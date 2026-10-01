from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.tests.factories import create_test_user
from apps.tenants.admin import SupplierAdmin, TenantAdmin
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember
from apps.tenants.services.shop_management import update_shop

User = get_user_model()


class T305ShopManagementAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.supplier = Supplier.objects.get(singleton_lock=True)
        self.main = User.objects.create_superuser(
            email="t305-main@example.test",
            password="Strong-Password-993!",
            first_name="Main",
            phone="+96551110001",
        )
        self.shop_a = self.shop("t305-shop-a")
        self.shop_b = self.shop("t305-shop-b")
        self.admin_a = self.member(
            self.shop_a, "t305-admin-a@example.test", ShopRole.ADMIN
        )
        self.staff_a = self.member(
            self.shop_a, "t305-staff-a@example.test", ShopRole.STAFF
        )
        self.viewer_b = self.member(
            self.shop_b, "t305-viewer-b@example.test", ShopRole.VIEWER
        )

    def shop(self, slug, **values):
        values.setdefault("default_locale", "ar-KW")
        return Tenant.objects.create(
            supplier=self.supplier,
            name=slug.replace("-", " ").title(),
            slug=slug,
            max_users=10,
            contact_email=f"{slug}@example.test",
            address_line1="1 Main Street",
            **values,
        )

    def member(self, shop, email, role, *, active=True):
        user = create_test_user(
            owning_shop=shop,
            email=email,
            password="Strong-Password-993!",
            first_name="Test",
            last_name=role.title(),
            phone=f"+965{50000000 + User.objects.count():08d}",
        )
        return TenantMember.objects.create(
            tenant=shop, user=user, role=role, is_active=active
        )

    def shop_url(self, shop):
        return f"/api/v1/tenants/{shop.pk}/"

    def test_main_supplier_sees_all_shops_and_management_fields(self):
        self.client.force_authenticate(self.main)
        response = self.client.get("/api/v1/tenants/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertIn("user_count", response.data["results"][0])
        self.assertIn("max_users", response.data["results"][0])
        self.assertIn("default_locale", response.data["results"][0])
        self.assertTrue(all(item["is_active"] for item in response.data["results"]))

    def test_ordinary_list_search_filters_and_pagination_are_shop_scoped(self):
        self.client.force_authenticate(self.admin_a.user)
        response = self.client.get("/api/v1/tenants/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        row = response.data["results"][0]
        self.assertEqual(row["id"], str(self.shop_a.pk))
        self.assertNotIn("user_count", row)
        self.assertNotIn("max_users", row)
        self.assertNotIn("default_locale", row)

        search = self.client.get("/api/v1/tenants/?search=t305-shop-b")
        self.assertEqual(search.data["count"], 0)
        filtered_active = self.client.get("/api/v1/tenants/?is_active=false")
        filtered_inactive = self.client.get("/api/v1/tenants/?is_active=true")
        self.assertEqual(filtered_active.data["count"], 1)
        self.assertEqual(filtered_inactive.data["count"], 1)
        direct = self.client.get(self.shop_url(self.shop_b))
        self.assertEqual(direct.status_code, status.HTTP_404_NOT_FOUND)

    def test_inactive_membership_sees_only_disabled_historical_profile(self):
        self.admin_a.is_active = False
        self.admin_a.save(update_fields=["is_active"])
        self.client.force_authenticate(self.admin_a.user)
        response = self.client.get("/api/v1/tenants/")
        self.assertEqual(response.data["count"], 1)
        self.assertFalse(response.data["results"][0]["is_active"])
        detail = self.client.get(self.shop_url(self.shop_a))
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertFalse(detail.data["is_active"])
        self.assertNotIn("user_count", detail.data)
        stats = self.client.get(f"{self.shop_url(self.shop_a)}stats/")
        self.assertEqual(stats.status_code, status.HTTP_403_FORBIDDEN)
        context = self.client.get(f"/api/v1/shops/{self.shop_a.pk}/context/")
        self.assertEqual(context.status_code, status.HTTP_404_NOT_FOUND)

    def test_removed_membership_does_not_grant_shop_discovery(self):
        self.staff_a.is_active = False
        self.staff_a.save(update_fields=["is_active"])
        self.staff_a.delete()
        self.client.force_authenticate(self.staff_a.user)
        response = self.client.get("/api/v1/tenants/")
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(
            self.client.get(self.shop_url(self.shop_a)).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_staff_and_viewer_profiles_hide_management_and_settings(self):
        self.client.force_authenticate(self.staff_a.user)
        staff = self.client.get(self.shop_url(self.shop_a))
        self.assertEqual(staff.status_code, status.HTTP_200_OK)
        for field in (
            "user_count",
            "max_users",
            "is_at_user_limit",
            "default_locale",
            "slug",
            "domain",
        ):
            self.assertNotIn(field, staff.data)
        self.client.force_authenticate(self.viewer_b.user)
        viewer = self.client.get(self.shop_url(self.shop_b))
        self.assertEqual(viewer.status_code, status.HTTP_200_OK)
        self.assertNotIn("max_users", viewer.data)
        self.assertNotIn("default_currency", viewer.data)

    def test_shop_admin_profile_has_own_stats_but_not_settings(self):
        self.client.force_authenticate(self.admin_a.user)
        response = self.client.get(self.shop_url(self.shop_a))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user_count"], 2)
        self.assertEqual(response.data["max_users"], 10)
        self.assertNotIn("default_locale", response.data)
        self.assertNotIn("slug", response.data)
        self.assertNotIn("domain", response.data)

    def test_stats_authority_and_foreign_non_disclosure(self):
        self.client.force_authenticate(self.main)
        self.assertEqual(
            self.client.get(f"{self.shop_url(self.shop_b)}stats/").status_code,
            status.HTTP_200_OK,
        )
        self.client.force_authenticate(self.admin_a.user)
        self.assertEqual(
            self.client.get(f"{self.shop_url(self.shop_a)}stats/").status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self.client.get(f"{self.shop_url(self.shop_b)}stats/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.client.force_authenticate(self.staff_a.user)
        self.assertEqual(
            self.client.get(f"{self.shop_url(self.shop_a)}stats/").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.client.force_authenticate(self.viewer_b.user)
        self.assertEqual(
            self.client.get(f"{self.shop_url(self.shop_b)}stats/").status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_only_main_supplier_can_update_profile_settings_and_capacity(self):
        self.client.force_authenticate(self.admin_a.user)
        denied = self.client.patch(self.shop_url(self.shop_a), {"name": "Changed"})
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.main)
        response = self.client.patch(
            self.shop_url(self.shop_a),
            {"name": "Updated Shop", "default_locale": "bn", "max_users": 8},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.shop_a.refresh_from_db()
        self.assertEqual(self.shop_a.name, "Updated Shop")
        self.assertEqual(self.shop_a.default_locale, "bn")
        self.assertEqual(self.shop_a.updated_by_id, self.main.pk)

    def test_capacity_cannot_be_reduced_below_current_count(self):
        self.client.force_authenticate(self.main)
        response = self.client.patch(
            self.shop_url(self.shop_a), {"max_users": 1}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("max_users", response.data["errors"])
        self.shop_a.refresh_from_db()
        self.assertEqual(self.shop_a.max_users, 10)

    def test_generic_lifecycle_patch_and_delete_are_unavailable(self):
        self.client.force_authenticate(self.main)
        patch = self.client.patch(
            self.shop_url(self.shop_a), {"is_active": False}, format="json"
        )
        self.assertEqual(patch.status_code, status.HTTP_400_BAD_REQUEST)
        delete = self.client.delete(self.shop_url(self.shop_a))
        self.assertEqual(delete.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.shop_a.refresh_from_db()
        self.assertTrue(self.shop_a.is_active)

    def test_lifecycle_actions_are_main_supplier_only_and_preserve_memberships(self):
        self.client.force_authenticate(self.admin_a.user)
        denied = self.client.post(f"{self.shop_url(self.shop_a)}deactivate/")
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.main)
        response = self.client.post(f"{self.shop_url(self.shop_a)}deactivate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.shop_a.refresh_from_db()
        self.assertFalse(self.shop_a.is_active)
        self.assertEqual(self.shop_a.memberships.count(), 2)
        self.assertEqual(self.shop_a.updated_by_id, self.main.pk)

    def test_exact_user_code_lookup_is_shop_scoped_and_never_attaches(self):
        self.client.force_authenticate(self.admin_a.user)
        url = f"{self.shop_url(self.shop_a)}member-lookup/?user_code={self.staff_a.user.user_code}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user_code"], self.staff_a.user.user_code)
        self.assertEqual(response.data["display_name"], "Test Staff")
        self.assertNotIn("id", response.data)
        for code in (
            self.viewer_b.user.user_code,
            self.main.user_code,
            "U-2345678923456789",
        ):
            result = self.client.get(
                f"{self.shop_url(self.shop_a)}member-lookup/?user_code={code}"
            )
            self.assertEqual(result.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(
            TenantMember.objects.filter(
                user=self.viewer_b.user, tenant=self.shop_a
            ).exists()
        )

    def test_main_supplier_can_lookup_member_inside_selected_shop(self):
        self.client.force_authenticate(self.main)
        response = self.client.get(
            f"{self.shop_url(self.shop_b)}member-lookup/?user_code={self.viewer_b.user.user_code}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["membership_status"], "ACTIVE")

    def test_membership_list_prefers_permanent_user_id(self):
        self.client.force_authenticate(self.admin_a.user)
        response = self.client.get("/api/v1/memberships/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = next(
            item
            for item in response.data["results"]
            if item["id"] == str(self.staff_a.pk)
        )
        self.assertEqual(row["user_code"], self.staff_a.user.user_code)
        self.assertEqual(row["display_name"], "Test Staff")
        self.assertNotIn("user", row)


class T305ShopAdminParityTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.get(singleton_lock=True)
        self.main = User.objects.create_superuser(
            email="t305-admin-main@example.test",
            password="Strong-Password-993!",
            first_name="Main",
            phone="+96551112222",
        )
        self.shop = Tenant.objects.create(
            supplier=self.supplier,
            name="Admin Shop",
            slug="t305-admin-shop",
            max_users=2,
        )
        self.account = create_test_user(
            owning_shop=self.shop,
            email="t305-admin-member@example.test",
            password="pw",
            first_name="Member",
            phone=f"+965{50000000 + User.objects.count():08d}",
        )
        TenantMember.objects.create(
            tenant=self.shop, user=self.account, role=ShopRole.STAFF
        )
        self.shop_admin = TenantAdmin(Tenant, admin.site)
        self.supplier_admin = SupplierAdmin(Supplier, admin.site)

    def test_admin_scope_and_unsafe_operations_are_denied(self):
        self.assertFalse(
            self.shop_admin.has_add_permission(type("R", (), {"user": self.main})())
        )
        self.assertFalse(
            self.shop_admin.has_delete_permission(
                type("R", (), {"user": self.main})(), self.shop
            )
        )
        self.assertFalse(
            self.supplier_admin.has_delete_permission(
                type("R", (), {"user": self.main})()
            )
        )
        self.assertFalse(
            self.supplier_admin.has_change_permission(
                type("R", (), {"user": self.main})()
            )
        )
        non_main = create_test_user(
            email="t305-admin-staff@example.test", first_name="Staff"
        )
        request = type("R", (), {"user": non_main})()
        self.assertFalse(self.shop_admin.has_module_permission(request))

    def test_admin_max_users_update_uses_locked_shared_service(self):
        from django.core.exceptions import ValidationError

        form = type(
            "F", (), {"changed_data": ["max_users"], "cleaned_data": {"max_users": 0}}
        )()
        with self.assertRaises(ValidationError):
            self.shop_admin.save_model(
                type("R", (), {"user": self.main})(), self.shop, form, change=True
            )
        self.shop.refresh_from_db()
        self.assertEqual(self.shop.max_users, 2)

    def test_admin_lifecycle_actions_use_the_same_safe_service(self):
        request = type("R", (), {"user": self.main, "_messages": []})()
        self.shop_admin.deactivate_selected_shops(
            request, Tenant.objects.filter(pk=self.shop.pk)
        )
        self.shop.refresh_from_db()
        self.assertFalse(self.shop.is_active)
        self.assertEqual(self.shop.updated_by_id, self.main.pk)
        self.shop_admin.activate_selected_shops(
            request, Tenant.objects.filter(pk=self.shop.pk)
        )
        self.shop.refresh_from_db()
        self.assertTrue(self.shop.is_active)

    def test_shared_service_rechecks_current_main_supplier_authority(self):
        self.main.is_active = False
        self.main.save(update_fields=["is_active"])
        with self.assertRaises(Exception):
            update_shop(self.main, self.shop.pk, {"name": "Unauthorized"})
        self.shop.refresh_from_db()
        self.assertEqual(self.shop.name, "Admin Shop")
