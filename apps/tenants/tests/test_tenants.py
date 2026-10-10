from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from ..models import Tenant, Supplier, TenantMember
from apps.accounts.tests.factories import create_test_user

User = get_user_model()


class TenantModelTest(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.get(singleton_lock=True)
        self.owner_shop = Tenant.objects.create(
            name="Owner Shop",
            slug="owner-shop-model-test",
            max_users=10,
            supplier=self.supplier,
        )
        self.user = create_test_user(
            owning_shop=self.owner_shop,
            email="test@example.com",
            password="testpass123",
            first_name="Test",
        )

    def test_create_tenant(self):
        """Test creating a tenant"""
        tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            contact_email="admin@test-tenant.com",
            max_users=10,
            created_by=self.user,
            supplier=self.supplier,
        )

        self.assertEqual(tenant.name, "Test Tenant")
        self.assertEqual(tenant.slug, "test-tenant")
        self.assertTrue(tenant.is_active)
        self.assertEqual(tenant.max_users, 10)
        self.assertEqual(tenant.user_count, 0)
        self.assertFalse(tenant.is_at_user_limit)

    def test_tenant_string_representation(self):
        """Test tenant string representation"""
        tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            max_users=10,
            created_by=self.user,
            supplier=self.supplier,
        )
        self.assertEqual(str(tenant), "Test Tenant")

    def test_tenant_user_count(self):
        """ACTIVE and INACTIVE memberships consume capacity; REMOVED does not."""
        tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            max_users=2,
            created_by=self.user,
            supplier=self.supplier,
        )
        active_user = create_test_user(
            owning_shop=tenant, email="tenant-active@example.test", first_name="Active"
        )
        inactive_user = create_test_user(
            owning_shop=tenant,
            email="tenant-inactive@example.test",
            first_name="Inactive",
        )
        removed_user = create_test_user(
            owning_shop=tenant,
            email="tenant-removed@example.test",
            first_name="Removed",
        )
        TenantMember.objects.create(tenant=tenant, user=active_user, role="STAFF")
        TenantMember.objects.create(
            tenant=tenant, user=inactive_user, role="STAFF", is_active=False
        )
        removed = TenantMember.objects.create(
            tenant=tenant, user=removed_user, role="STAFF", is_active=False
        )
        removed.delete()

        self.assertEqual(tenant.user_count, 2)
        self.assertTrue(tenant.is_at_user_limit)


class TenantAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
        )
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
            first_name="Main",
            phone="+96550000000",
        )
        self.supplier = Supplier.objects.get(singleton_lock=True)
        self.tenant_data = {
            "name": "Test Tenant",
            "slug": "test-tenant",
            "first_admin": {
                "first_name": "First",
                "login_id": "first_admin",
                "email": "first-admin@example.test",
                "phone": "+96550000019",
            },
            "contact_email": "admin@test-tenant.com",
            "max_users": 20,
        }

    def test_list_tenants_authenticated(self):
        """Authenticated users do not receive a global Shop directory."""
        self.client.force_authenticate(user=self.user)
        Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            max_users=10,
            created_by=self.user,
            supplier=self.supplier,
        )

        response = self.client.get("/api/v1/tenants/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_list_tenants_unauthenticated(self):
        """Test listing tenants without authentication"""
        response = self.client.get("/api/v1/tenants/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_tenant_as_admin(self):
        """Test creating tenant as admin user"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post("/api/v1/tenants/", self.tenant_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(Tenant.objects.filter(slug="test-tenant").exists())
        tenant = Tenant.objects.get(slug="test-tenant")
        self.assertEqual(
            TenantMember.objects.filter(
                tenant=tenant, role="ADMIN", is_active=True, deleted__isnull=True
            ).count(),
            1,
        )

    def test_create_tenant_as_regular_user(self):
        """Test creating tenant as regular user (should fail)"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/v1/tenants/", self.tenant_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_foreign_tenant_stats_are_non_disclosing(self):
        """Unrelated authenticated users cannot discover a Shop through stats."""
        self.client.force_authenticate(user=self.user)
        tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            max_users=10,
            created_by=self.user,
            supplier=self.supplier,
        )

        response = self.client.get(f"/api/v1/tenants/{tenant.id}/stats/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_activate_tenant(self):
        """Test activating a tenant"""
        self.client.force_authenticate(user=self.admin_user)
        tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            max_users=10,
            is_active=False,
            created_by=self.user,
            supplier=self.supplier,
        )

        response = self.client.post(f"/api/v1/tenants/{tenant.id}/activate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tenant.refresh_from_db()
        self.assertTrue(tenant.is_active)

    def test_staff_without_superuser_cannot_manage_tenants(self):
        """Shop administration follows Main Supplier policy, not is_staff."""
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        self.client.force_authenticate(user=self.user)
        tenant = Tenant.objects.create(
            name="Protected Shop",
            slug="protected-shop",
            max_users=10,
            created_by=self.user,
            supplier=self.supplier,
        )

        create_response = self.client.post(
            "/api/v1/tenants/",
            {
                "name": "Another Shop",
                "slug": "another-shop",
                "max_users": 10,
            },
        )
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)

        update_response = self.client.patch(
            f"/api/v1/tenants/{tenant.id}/", {"name": "Changed"}
        )
        self.assertEqual(update_response.status_code, status.HTTP_403_FORBIDDEN)

        deactivate_response = self.client.post(
            f"/api/v1/tenants/{tenant.id}/deactivate/"
        )
        self.assertEqual(deactivate_response.status_code, status.HTTP_403_FORBIDDEN)
