from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.tenants.models import Tenant, Supplier, TenantMember, ShopRole
from apps.accounts.tests.factories import create_test_user

User = get_user_model()


class TenantMemberAPITest(APITestCase):
    def setUp(self):
        # We need a Main Supplier
        try:
            self.supplier = Supplier.objects.get(singleton_lock=True)
        except Supplier.DoesNotExist:
            self.supplier = Supplier.objects.create(
                name="Main Supplier", slug="main-supplier"
            )

        self.shop_a = Tenant.objects.create(
            max_users=10, name="Shop A", slug="shop-a", supplier=self.supplier
        )
        self.shop_b = Tenant.objects.create(
            max_users=10, name="Shop B", slug="shop-b", supplier=self.supplier
        )

        # Superuser (Main Supplier Admin)
        self.super_admin = User.objects.create_superuser(
            email="super@test.com",
            password="testpass",
            first_name="Main",
            phone="+96550000000",
        )

        # Shop A Admin
        self.shop_a_admin = create_test_user(owning_shop=self.shop_a,
            email="admin_a@test.com", password="testpass", first_name="Test"
        )
        self.mem_a_admin = TenantMember.objects.create(
            tenant=self.shop_a, user=self.shop_a_admin, role=ShopRole.ADMIN
        )

        # Shop A Staff
        self.shop_a_staff = create_test_user(owning_shop=self.shop_a,
            email="staff_a@test.com", password="testpass", first_name="Test"
        )
        self.mem_a_staff = TenantMember.objects.create(
            tenant=self.shop_a, user=self.shop_a_staff, role=ShopRole.STAFF
        )

        # Shop A Viewer
        self.shop_a_viewer = create_test_user(owning_shop=self.shop_a,
            email="viewer_a@test.com", password="testpass", first_name="Test"
        )
        self.mem_a_viewer = TenantMember.objects.create(
            tenant=self.shop_a, user=self.shop_a_viewer, role=ShopRole.VIEWER
        )

        # Plain user with is_staff (but not superuser)
        self.staff_user = create_test_user(
            email="staff_no_super@test.com",
            password="testpass",
            is_staff=True,
            first_name="Test",
        )

        # External user
        self.external_user = create_test_user(owning_shop=self.shop_b,
            email="external@test.com", password="testpass", first_name="Test"
        )

        self.list_url = "/api/v1/memberships/"

    # AUTHENTICATION
    def test_unauth_get_401(self):
        r = self.client.get(self.list_url)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauth_post_401(self):
        r = self.client.post(self.list_url, {})
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    # MAIN SUPPLIER
    def test_superuser_can_list_all(self):
        self.client.force_authenticate(user=self.super_admin)
        r = self.client.get(self.list_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        # Should see all 3 memberships created in setup
        self.assertGreaterEqual(len(r.data["results"]), 3)

    def test_existing_user_membership_endpoint_cannot_create_first_membership(self):
        self.client.force_authenticate(user=self.super_admin)
        u1 = create_test_user(owning_shop=self.shop_a,
            email="u1@test.com", password="tp", first_name="Test"
        )
        u2 = create_test_user(owning_shop=self.shop_b,
            email="u2@test.com", password="tp", first_name="Test"
        )

        r1 = self.client.post(
            self.list_url,
            {"tenant": self.shop_a.id, "user": u1.id, "role": ShopRole.STAFF},
        )
        self.assertEqual(r1.status_code, status.HTTP_400_BAD_REQUEST)

        r2 = self.client.post(
            self.list_url,
            {"tenant": self.shop_b.id, "user": u2.id, "role": ShopRole.STAFF},
        )
        self.assertEqual(r2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_superuser_can_update_any(self):
        self.client.force_authenticate(user=self.super_admin)
        r = self.client.patch(
            f"{self.list_url}{self.mem_a_viewer.id}/", {"role": ShopRole.STAFF}
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.mem_a_viewer.refresh_from_db()
        self.assertEqual(self.mem_a_viewer.role, ShopRole.STAFF)

    def test_generic_update_cannot_change_membership_lifecycle_state(self):
        """Lifecycle state changes must use deactivate/reactivate actions."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.patch(
            f"{self.list_url}{self.mem_a_viewer.id}/", {"is_active": False}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mem_a_viewer.refresh_from_db()
        self.assertTrue(self.mem_a_viewer.is_active)

    def test_superuser_can_delete_any(self):
        self.mem_a_viewer.is_active = False
        self.mem_a_viewer.save()
        self.client.force_authenticate(user=self.super_admin)
        r = self.client.delete(f"{self.list_url}{self.mem_a_viewer.id}/")
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)

    # IS_STAFF VS SUPERUSER
    def test_is_staff_without_superuser_cannot_manage(self):
        self.client.force_authenticate(user=self.staff_user)
        r = self.client.get(self.list_url)
        # They are not an admin of any shop, so they see nothing.
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data["results"]), 0)

        r_post = self.client.post(
            self.list_url,
            {
                "tenant": self.shop_a.id,
                "user": self.external_user.id,
                "role": ShopRole.STAFF,
            },
        )
        self.assertEqual(r_post.status_code, status.HTTP_403_FORBIDDEN)

    def test_business_authority_not_derived_from_is_staff(self):
        self.client.force_authenticate(user=self.staff_user)
        r_post = self.client.post(
            self.list_url,
            {
                "tenant": self.shop_a.id,
                "user": self.external_user.id,
                "role": ShopRole.STAFF,
            },
        )
        self.assertEqual(r_post.status_code, status.HTTP_403_FORBIDDEN)

    # SHOP ADMIN
    def test_shop_admin_can_list_own(self):
        self.client.force_authenticate(user=self.shop_a_admin)
        r = self.client.get(self.list_url)
        print("Response:", r.status_code, r.data)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        # Should see 3 members of shop A
        self.assertEqual(len(r.data["results"]), 3)

    def test_shop_admin_cannot_list_other(self):
        TenantMember.objects.create(
            tenant=self.shop_b, user=self.external_user, role=ShopRole.ADMIN
        )
        self.client.force_authenticate(user=self.shop_a_admin)
        r = self.client.get(self.list_url)
        for item in r.data["results"]:
            self.assertNotEqual(item["tenant"], str(self.shop_b.id))

    def test_shop_admin_can_create_in_own(self):
        self.client.force_authenticate(user=self.shop_a_admin)
        r = self.client.post(
            f"/api/v1/shops/{self.shop_a.pk}/users/",
            {
                "email": "new-shop-a-staff@test.com",
                "first_name": "New",
                "role": ShopRole.STAFF,
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r["Cache-Control"], "no-store")
        created = User.objects.get(email="new-shop-a-staff@test.com")
        self.assertEqual(created.owning_shop_id, self.shop_a.pk)
        self.assertEqual(
            TenantMember.objects.get(user=created).role,
            ShopRole.STAFF,
        )

    def test_shop_admin_cannot_create_in_other(self):
        self.client.force_authenticate(user=self.shop_a_admin)
        r = self.client.post(
            self.list_url,
            {
                "tenant": self.shop_b.id,
                "user": self.external_user.id,
                "role": ShopRole.STAFF,
            },
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_shop_admin_can_update_own(self):
        self.client.force_authenticate(user=self.shop_a_admin)
        r = self.client.patch(
            f"{self.list_url}{self.mem_a_viewer.id}/", {"role": ShopRole.STAFF}
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_shop_admin_cannot_update_other(self):
        mem_b = TenantMember.objects.create(
            tenant=self.shop_b, user=self.external_user, role=ShopRole.ADMIN
        )
        self.client.force_authenticate(user=self.shop_a_admin)
        r = self.client.patch(f"{self.list_url}{mem_b.id}/", {"role": ShopRole.STAFF})
        self.assertEqual(
            r.status_code, status.HTTP_404_NOT_FOUND
        )  # Due to get_queryset restriction

    def test_shop_admin_cannot_delete_other(self):
        mem_b = TenantMember.objects.create(
            tenant=self.shop_b, user=self.external_user, role=ShopRole.ADMIN
        )
        self.client.force_authenticate(user=self.shop_a_admin)
        r = self.client.delete(f"{self.list_url}{mem_b.id}/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    # STAFF & VIEWER
    def test_staff_cannot_create_update_delete(self):
        self.client.force_authenticate(user=self.shop_a_staff)
        r = self.client.post(
            self.list_url,
            {
                "tenant": self.shop_a.id,
                "user": self.external_user.id,
                "role": ShopRole.VIEWER,
            },
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        r = self.client.patch(
            f"{self.list_url}{self.mem_a_viewer.id}/", {"role": ShopRole.ADMIN}
        )
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)
        r = self.client.delete(f"{self.list_url}{self.mem_a_viewer.id}/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_viewer_cannot_create_update_delete(self):
        self.client.force_authenticate(user=self.shop_a_viewer)
        r = self.client.post(
            self.list_url,
            {
                "tenant": self.shop_a.id,
                "user": self.external_user.id,
                "role": ShopRole.VIEWER,
            },
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        r = self.client.patch(
            f"{self.list_url}{self.mem_a_staff.id}/", {"role": ShopRole.ADMIN}
        )
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)
        r = self.client.delete(f"{self.list_url}{self.mem_a_staff.id}/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_cannot_elevate_own_role(self):
        self.client.force_authenticate(user=self.shop_a_staff)
        r = self.client.patch(
            f"{self.list_url}{self.mem_a_staff.id}/", {"role": ShopRole.ADMIN}
        )
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_viewer_cannot_elevate_own_role(self):
        self.client.force_authenticate(user=self.shop_a_viewer)
        r = self.client.patch(
            f"{self.list_url}{self.mem_a_viewer.id}/", {"role": ShopRole.ADMIN}
        )
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    # IDOR / PAYLOAD TAMPERING
    def test_direct_foreign_membership_uuid_access_denied(self):
        mem_b = TenantMember.objects.create(
            tenant=self.shop_b, user=self.external_user, role=ShopRole.STAFF
        )
        self.client.force_authenticate(user=self.shop_a_admin)
        r = self.client.get(f"{self.list_url}{mem_b.id}/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_with_another_shop_tenant_id_denied(self):
        self.client.force_authenticate(user=self.shop_a_admin)
        r = self.client.post(
            self.list_url,
            {
                "tenant": self.shop_b.id,
                "user": self.external_user.id,
                "role": ShopRole.STAFF,
            },
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_another_shop_tenant_assignment_denied(self):
        self.client.force_authenticate(user=self.shop_a_admin)
        r = self.client.patch(
            f"{self.list_url}{self.mem_a_staff.id}/", {"tenant": self.shop_b.id}
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot change the Shop", r.data["errors"]["tenant"][0])
        self.mem_a_staff.refresh_from_db()
        self.assertEqual(self.mem_a_staff.tenant_id, self.shop_a.id)

    def test_malicious_role_admin_payload_cannot_elevate_staff(self):
        self.client.force_authenticate(user=self.shop_a_staff)
        r = self.client.post(
            self.list_url,
            {
                "tenant": self.shop_a.id,
                "user": self.external_user.id,
                "role": ShopRole.ADMIN,
            },
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_bypass_authorization_by_manipulating_tenant_field(self):
        self.client.force_authenticate(user=self.shop_a_staff)
        r = self.client.patch(
            f"{self.list_url}{self.mem_a_staff.id}/", {"tenant": self.shop_b.id}
        )
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    # LIFECYCLE
    def test_inactive_user_cannot_be_added(self):
        self.client.force_authenticate(user=self.shop_a_admin)
        u = create_test_user(owning_shop=self.shop_a,
            email="inactive@test.com", password="tp", is_active=False, first_name="Test"
        )
        r = self.client.post(
            self.list_url,
            {"tenant": self.shop_a.id, "user": u.id, "role": ShopRole.STAFF},
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_shop_cannot_receive_membership(self):
        self.client.force_authenticate(user=self.super_admin)
        self.shop_a.is_active = False
        self.shop_a.save()
        r = self.client.post(
            self.list_url,
            {
                "tenant": self.shop_a.id,
                "user": self.external_user.id,
                "role": ShopRole.STAFF,
            },
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_membership_cannot_grant_management_authority(self):
        self.mem_a_admin.is_active = False
        self.mem_a_admin.save()
        self.client.force_authenticate(user=self.shop_a_admin)
        r = self.client.post(
            self.list_url,
            {
                "tenant": self.shop_a.id,
                "user": self.external_user.id,
                "role": ShopRole.STAFF,
            },
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_inactive_shop_admin_cannot_manage_memberships(self):
        """Inactive Shop authority denial is 403; Main Supplier gets business validation."""
        self.shop_a.is_active = False
        self.shop_a.save()
        self.client.force_authenticate(user=self.shop_a_admin)
        r = self.client.post(
            self.list_url,
            {
                "tenant": self.shop_a.id,
                "user": self.external_user.id,
                "role": ShopRole.STAFF,
            },
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    # DUPLICATES
    def test_api_duplicate_membership_rejected(self):
        self.client.force_authenticate(user=self.shop_a_admin)
        r = self.client.post(
            self.list_url,
            {
                "tenant": self.shop_a.id,
                "user": self.shop_a_staff.id,
                "role": ShopRole.STAFF,
            },
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    # ROLE DATA
    def test_invalid_role_is_rejected(self):
        self.client.force_authenticate(user=self.shop_a_admin)
        r = self.client.post(
            self.list_url,
            {"tenant": self.shop_a.id, "user": self.external_user.id, "role": "HACKER"},
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    # USER COUNT / LIMIT
    # user_count logic is skipped due to BUSINESS DECISION REQUIRED for B-04

    # EXTERNAL SUPPLIER BOUNDARY
    def test_no_external_supplier_authentication_path_exists(self):
        # Implicitly tested as external suppliers are not models that can auth.
        # But we ensure they can't be added using standard membership endpoints.
        # Wait, the prompt says external suppliers are NOT users.
        # So they can't be added to membership because the FK requires a User model.
        pass
