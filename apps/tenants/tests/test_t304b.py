from django.contrib import admin
from django.test import RequestFactory
from django.test import TestCase
from types import SimpleNamespace
from unittest.mock import patch
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.accounts.services.user_lifecycle import deactivate_global_user
from apps.tenants.admin import TenantAdmin, TenantMemberAdmin
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember
from apps.tenants.services.membership import change_membership_role


class T304BRemediationTests(TestCase):
    def setUp(self):
        self.main = User.objects.create_superuser(
            email="main@example.test",
            password="pw",
            first_name="Main",
            phone="+96550000001",
        )
        self.supplier = Supplier.objects.get(singleton_lock=True)
        self.client = APIClient()
        self.client.force_authenticate(self.main)

    def user(self, email, **kwargs):
        kwargs.setdefault("first_name", "Tailor")
        kwargs.setdefault("phone", f"+965500000{User.objects.count() + 2:02d}")
        return User.objects.create_user(email=email, password="pw", **kwargs)

    def shop(self, slug, **kwargs):
        return Tenant.objects.create(
            supplier=self.supplier, name=slug, slug=slug, max_users=5, **kwargs
        )

    def create_shop_payload(self, slug, first_admin, **kwargs):
        payload = {
            "name": slug,
            "slug": slug,
            "max_users": 3,
            "first_admin_user": str(first_admin.pk),
        }
        payload.update(kwargs)
        return payload

    def test_shop_creation_commits_shop_and_first_admin_together(self):
        user = self.user("first@example.test")
        response = self.client.post(
            "/api/v1/tenants/", self.create_shop_payload("new-shop", user)
        )
        self.assertEqual(response.status_code, 201, response.data)
        shop = Tenant.objects.get(slug="new-shop")
        self.assertTrue(shop.is_active)
        self.assertEqual(
            TenantMember.objects.filter(
                tenant=shop, role=ShopRole.ADMIN, is_active=True, deleted__isnull=True
            ).count(),
            1,
        )
        self.assertNotIn("first_admin_user", response.data)

    def test_shop_creation_rejects_invalid_first_admin_without_orphan(self):
        user = self.user("no-phone@example.test", phone="")
        response = self.client.post(
            "/api/v1/tenants/", self.create_shop_payload("invalid-shop", user)
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(Tenant.objects.filter(slug="invalid-shop").exists())

    def test_shop_creation_rejects_missing_email_and_inactive_first_admin(self):
        no_email = self.user(None)
        response = self.client.post(
            "/api/v1/tenants/", self.create_shop_payload("no-email-shop", no_email)
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Tenant.objects.filter(slug="no-email-shop").exists())

        inactive = self.user("inactive-first-admin@example.test", is_active=False)
        response = self.client.post(
            "/api/v1/tenants/",
            self.create_shop_payload("inactive-admin-shop", inactive),
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Tenant.objects.filter(slug="inactive-admin-shop").exists())

    def test_shop_creation_requires_first_admin_and_valid_capacity(self):
        payload = {"name": "missing-admin", "slug": "missing-admin", "max_users": 3}
        response = self.client.post("/api/v1/tenants/", payload)
        self.assertEqual(response.status_code, 400)
        payload["first_admin_user"] = str(self.user("cap@example.test").pk)
        payload["max_users"] = 0
        response = self.client.post("/api/v1/tenants/", payload)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Tenant.objects.filter(slug="missing-admin").exists())

    def test_inactive_shop_creation_rejected_and_admin_add_is_disabled(self):
        user = self.user("inactive-shop@example.test")
        response = self.client.post(
            "/api/v1/tenants/",
            self.create_shop_payload("inactive-shop", user, is_active=False),
        )
        self.assertEqual(response.status_code, 400)
        tenant_admin = TenantAdmin(Tenant, admin.site)
        member_admin = TenantMemberAdmin(TenantMember, admin.site)
        self.assertFalse(tenant_admin.has_add_permission(None))
        self.assertFalse(member_admin.has_add_permission(None))
        self.assertFalse(member_admin.has_change_permission(None))
        self.assertFalse(member_admin.has_delete_permission(None))

    def test_global_deactivation_rejects_last_admin_even_in_inactive_shop(self):
        user = self.user("sole-admin@example.test")
        shop = self.shop("inactive-admin-shop")
        TenantMember.objects.create(tenant=shop, user=user, role=ShopRole.ADMIN)
        shop.is_active = False
        shop.save(update_fields=["is_active"])
        with self.assertRaises(ValidationError):
            deactivate_global_user(self.main, user)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_main_supplier_can_demote_admin_in_inactive_shop_without_losing_last_admin(
        self,
    ):
        shop = self.shop("inactive-shop-admin-management")
        demoted_user = self.user("inactive-shop-demoted@example.test")
        remaining_user = self.user("inactive-shop-remaining@example.test")
        demoted = TenantMember.objects.create(
            tenant=shop, user=demoted_user, role=ShopRole.ADMIN
        )
        TenantMember.objects.create(
            tenant=shop, user=remaining_user, role=ShopRole.ADMIN
        )
        shop.is_active = False
        shop.save(update_fields=["is_active"])

        updated = change_membership_role(self.main, demoted.pk, ShopRole.STAFF)

        self.assertEqual(updated.role, ShopRole.STAFF)
        self.assertEqual(
            TenantMember.objects.filter(
                tenant=shop,
                role=ShopRole.ADMIN,
                is_active=True,
                deleted__isnull=True,
                user__is_active=True,
            ).count(),
            1,
        )

    def test_global_deactivation_requires_main_supplier_authority(self):
        target = self.user("staff-target@example.test")
        shop = self.shop("staff-shop")
        actor = self.user("shop-admin@example.test")
        TenantMember.objects.create(tenant=shop, user=actor, role=ShopRole.ADMIN)
        with self.assertRaises(PermissionDenied):
            deactivate_global_user(actor, target)
        target.refresh_from_db()
        self.assertTrue(target.is_active)

    def test_global_deactivation_of_admin_in_multiple_shops_is_atomic(self):
        target = self.user("multi-admin@example.test")
        first = self.shop("multi-a")
        second = self.shop("multi-b")
        TenantMember.objects.create(tenant=first, user=target, role=ShopRole.ADMIN)
        TenantMember.objects.create(tenant=second, user=target, role=ShopRole.ADMIN)
        # A second effective ADMIN protects only the first Shop; the second has a sole ADMIN.
        TenantMember.objects.create(
            tenant=first,
            user=self.user("other-admin@example.test"),
            role=ShopRole.ADMIN,
        )
        with self.assertRaises(ValidationError):
            deactivate_global_user(self.main, target)
        target.refresh_from_db()
        self.assertTrue(target.is_active)

    def test_global_deactivation_allowed_for_second_admin_and_non_admin_user(self):
        target = self.user("second-admin@example.test")
        shop = self.shop("two-admin-shop")
        TenantMember.objects.create(tenant=shop, user=target, role=ShopRole.ADMIN)
        TenantMember.objects.create(
            tenant=shop,
            user=self.user("retained-admin@example.test"),
            role=ShopRole.ADMIN,
        )
        deactivate_global_user(self.main, target)
        target.refresh_from_db()
        self.assertFalse(target.is_active)

        staff = self.user("staff-only@example.test")
        deactivate_global_user(self.main, staff)
        staff.refresh_from_db()
        self.assertFalse(staff.is_active)

    def test_user_admin_cannot_bypass_global_deactivation_invariant(self):
        from apps.accounts.admin import UserAdmin

        target = self.user("admin-ui-sole@example.test")
        shop = self.shop("admin-ui-sole-shop")
        TenantMember.objects.create(tenant=shop, user=target, role=ShopRole.ADMIN)
        target.is_active = False
        request = RequestFactory().post("/admin/accounts/user/")
        request.user = self.main
        form = SimpleNamespace(changed_data=["is_active"], instance=target)
        user_admin = UserAdmin(User, admin.site)
        with patch("apps.accounts.admin.messages.error") as error_message:
            user_admin.save_model(request, target, form, change=True)
            user_admin.save_related(request, form, [], change=True)
        target.refresh_from_db()
        self.assertTrue(target.is_active)
        error_message.assert_called_once()

    def test_user_admin_reports_denied_global_deactivation_without_saving(self):
        from apps.accounts.admin import UserAdmin

        target = self.user("admin-ui-unauthorized@example.test")
        actor = self.user("admin-ui-staff@example.test", is_staff=True)
        target.is_active = False
        request = RequestFactory().post("/admin/accounts/user/")
        request.user = actor
        form = SimpleNamespace(changed_data=["is_active"], instance=target)
        user_admin = UserAdmin(User, admin.site)
        with patch("apps.accounts.admin.messages.error") as error_message:
            user_admin.save_model(request, target, form, change=True)
            user_admin.save_related(request, form, [], change=True)
        target.refresh_from_db()
        self.assertTrue(target.is_active)
        error_message.assert_called_once()

    def test_admin_contact_validation_uses_trimmed_first_name_and_phone(self):
        from apps.tenants.services.membership import validate_admin_grade_user

        with self.assertRaises(ValidationError):
            validate_admin_grade_user(
                SimpleNamespace(
                    is_active=True,
                    first_name="   ",
                    email="valid@example.test",
                    phone="+96550000099",
                )
            )
