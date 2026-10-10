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
from apps.accounts.tests.factories import create_test_user


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

    def user(self, email, *, shop=None, **kwargs):
        kwargs.setdefault("first_name", "Tailor")
        kwargs.setdefault("phone", f"+965500000{User.objects.count() + 2:02d}")
        return create_test_user(owning_shop=shop, email=email, password="pw", **kwargs)

    def shop(self, slug, **kwargs):
        return Tenant.objects.create(
            supplier=self.supplier, name=slug, slug=slug, max_users=5, **kwargs
        )

    def create_shop_payload(self, slug, first_admin=None, **kwargs):
        payload = {
            "name": slug,
            "slug": slug,
            "max_users": 3,
            "first_admin": first_admin or {
                "first_name": "First",
                "login_id": slug.replace("-", "_")[:32],
                "email": f"{slug}@example.test",
                "phone": f"+965500000{User.objects.count() + 2:02d}",
            },
        }
        payload.update(kwargs)
        return payload

    def test_shop_creation_commits_shop_and_first_admin_together(self):
        response = self.client.post(
            "/api/v1/tenants/", self.create_shop_payload("new-shop"), format="json"
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
        membership = TenantMember.objects.get(tenant=shop, role=ShopRole.ADMIN)
        self.assertEqual(membership.user.owning_shop_id, shop.pk)
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_created_first_admin_can_log_in_and_change_initial_password(self):
        payload = self.create_shop_payload("login-shop")
        payload["first_admin"]["login_id"] = "  MainTailor_01  "
        created = self.client.post(
            "/api/v1/tenants/",
            payload,
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)
        user = User.objects.get(user_code=created.data["first_admin_user_code"])
        self.assertEqual(created.data["first_admin_login_id"], "MainTailor_01")
        self.assertEqual(user.login_id, "MainTailor_01")
        self.assertTrue(user.login_enabled)
        initial_password = created.data["initial_password"]
        self.assertRegex(initial_password, r"^[0-9]{6}$")
        self.assertNotEqual(user.password, initial_password)
        self.assertTrue(user.check_password(initial_password))
        self.assertTrue(user.must_change_password)

        memberships = self.client.get(
            f"/api/v1/memberships/?tenant={created.data['id']}&role=ADMIN"
        )
        self.assertEqual(memberships.status_code, 200, memberships.data)
        self.assertEqual(memberships.data["results"][0]["login_id"], "MainTailor_01")

        shop_admin_client = APIClient()
        login = shop_admin_client.post(
            "/api/v1/auth/login/",
            {"identifier": "MainTailor_01", "password": initial_password},
            format="json",
        )
        self.assertEqual(login.status_code, 200, login.data)
        self.assertEqual(login.data["user"]["id"], str(user.pk))
        self.assertTrue(login.data["user"]["must_change_password"])
        shop_admin_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['access']}"
        )
        blocked = shop_admin_client.get("/api/v1/auth/users/me/")
        self.assertEqual(blocked.status_code, 403)

        changed = shop_admin_client.post(
            "/api/v1/auth/users/password/change/",
            {
                "current_password": initial_password,
                "new_password": "048731",
                "new_password_confirm": "048731",
            },
            format="json",
        )
        self.assertEqual(changed.status_code, 200, changed.data)
        user.refresh_from_db()
        self.assertFalse(user.must_change_password)
        self.assertTrue(user.check_password("048731"))

        old_password_login = shop_admin_client.post(
            "/api/v1/auth/login/",
            {"identifier": "MainTailor_01", "password": initial_password},
            format="json",
        )
        new_password_login = shop_admin_client.post(
            "/api/v1/auth/login/",
            {"identifier": "MainTailor_01", "password": "048731"},
            format="json",
        )
        self.assertEqual(old_password_login.status_code, 401)
        self.assertEqual(new_password_login.status_code, 200, new_password_login.data)

    def test_shop_creation_rejects_invalid_first_admin_without_orphan(self):
        first_admin = {
            "first_name": "No phone", "email": "no-phone@example.test", "phone": ""
        }
        response = self.client.post(
            "/api/v1/tenants/",
            self.create_shop_payload("invalid-shop", first_admin),
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(Tenant.objects.filter(slug="invalid-shop").exists())

    def test_shop_creation_rejects_missing_email_and_inactive_first_admin(self):
        no_email = {"first_name": "No email", "email": "", "phone": "+96550000029"}
        response = self.client.post(
            "/api/v1/tenants/",
            self.create_shop_payload("no-email-shop", no_email),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Tenant.objects.filter(slug="no-email-shop").exists())

        response = self.client.post(
            "/api/v1/tenants/",
            self.create_shop_payload("inactive-admin-shop", {
                "first_name": "Inactive", "email": "inactive-first-admin@example.test",
                "phone": "+96550000030", "is_active": False,
            }),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Tenant.objects.filter(slug="inactive-admin-shop").exists())

    def test_shop_creation_requires_first_admin_and_valid_capacity(self):
        payload = {"name": "missing-admin", "slug": "missing-admin", "max_users": 3}
        response = self.client.post("/api/v1/tenants/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        payload["first_admin"] = self.create_shop_payload("cap-shop")["first_admin"]
        payload["max_users"] = 0
        response = self.client.post("/api/v1/tenants/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Tenant.objects.filter(slug="missing-admin").exists())

    def test_inactive_shop_creation_rejected_and_admin_add_is_disabled(self):
        response = self.client.post(
            "/api/v1/tenants/",
            self.create_shop_payload("inactive-shop", is_active=False),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        tenant_admin = TenantAdmin(Tenant, admin.site)
        member_admin = TenantMemberAdmin(TenantMember, admin.site)
        self.assertFalse(tenant_admin.has_add_permission(None))
        self.assertFalse(member_admin.has_add_permission(None))
        self.assertFalse(member_admin.has_change_permission(None))
        self.assertFalse(member_admin.has_delete_permission(None))

    def test_global_deactivation_rejects_last_admin_even_in_inactive_shop(self):
        shop = self.shop("inactive-admin-shop")
        user = self.user("sole-admin@example.test", shop=shop)
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
        demoted_user = self.user("inactive-shop-demoted@example.test", shop=shop)
        remaining_user = self.user("inactive-shop-remaining@example.test", shop=shop)
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
        shop = self.shop("staff-shop")
        target = self.user("staff-target@example.test", shop=shop)
        actor = self.user("shop-admin@example.test", shop=shop)
        TenantMember.objects.create(tenant=shop, user=actor, role=ShopRole.ADMIN)
        with self.assertRaises(PermissionDenied):
            deactivate_global_user(actor, target)
        target.refresh_from_db()
        self.assertTrue(target.is_active)

    def test_different_shop_accounts_have_independent_admin_lifecycle(self):
        first = self.shop("multi-a")
        second = self.shop("multi-b")
        target = self.user("multi-admin-a@example.test", shop=first)
        other = self.user("multi-admin-b@example.test", shop=second)
        TenantMember.objects.create(tenant=first, user=target, role=ShopRole.ADMIN)
        TenantMember.objects.create(tenant=second, user=other, role=ShopRole.ADMIN)
        TenantMember.objects.create(
            tenant=first,
            user=self.user("other-admin@example.test", shop=first),
            role=ShopRole.ADMIN,
        )
        deactivate_global_user(self.main, target)
        target.refresh_from_db()
        other.refresh_from_db()
        self.assertFalse(target.is_active)
        self.assertTrue(other.is_active)

    def test_global_deactivation_allowed_for_second_admin_and_non_admin_user(self):
        shop = self.shop("two-admin-shop")
        target = self.user("second-admin@example.test", shop=shop)
        TenantMember.objects.create(tenant=shop, user=target, role=ShopRole.ADMIN)
        TenantMember.objects.create(
            tenant=shop,
            user=self.user("retained-admin@example.test", shop=shop),
            role=ShopRole.ADMIN,
        )
        deactivate_global_user(self.main, target)
        target.refresh_from_db()
        self.assertFalse(target.is_active)

        staff = self.user("staff-only@example.test", shop=shop)
        deactivate_global_user(self.main, staff)
        staff.refresh_from_db()
        self.assertFalse(staff.is_active)

    def test_user_admin_cannot_bypass_global_deactivation_invariant(self):
        from apps.accounts.admin import UserAdmin

        shop = self.shop("admin-ui-sole-shop")
        target = self.user("admin-ui-sole@example.test", shop=shop)
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
