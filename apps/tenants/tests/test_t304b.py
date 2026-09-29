from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant, Supplier, TenantMember, ShopRole

User = get_user_model()

class T304BTests(APITestCase):
    def setUp(self):
        self.supplier, _ = Supplier.objects.get_or_create(singleton_lock=True)
        self.main_supplier = User.objects.create_superuser(
            email="main@sgtp.com", password="pw", first_name="Main", phone="+12125550001"
        )
        self.shop_admin_user = User.objects.create_user(
            email="admin@shop.com", password="pw", first_name="Admin", phone="+12125550002"
        )
        self.staff_user = User.objects.create_user(
            email="staff@shop.com", password="pw", first_name="Staff", phone="+12125550003"
        )
        self.viewer_user = User.objects.create_user(
            email="viewer@shop.com", password="pw", first_name="Viewer", phone="+12125550004"
        )
        self.shop = Tenant.objects.create(name="Test Shop", slug="test-shop", max_users=10, supplier=self.supplier)
        
        self.admin_member = TenantMember.objects.create(
            tenant=self.shop, user=self.shop_admin_user, role=ShopRole.ADMIN, is_active=True
        )
        self.staff_member = TenantMember.objects.create(
            tenant=self.shop, user=self.staff_user, role=ShopRole.STAFF, is_active=True
        )
        self.viewer_member = TenantMember.objects.create(
            tenant=self.shop, user=self.viewer_user, role=ShopRole.VIEWER, is_active=True
        )

    def test_shop_admin_create_staff_viewer(self):
        self.client.force_authenticate(user=self.shop_admin_user)
        new_u = User.objects.create_user(email="new1@test.com", password="pw", first_name="N1")
        resp = self.client.post("/api/v1/memberships/", {'tenant': self.shop.id, 'user': new_u.id, 'role': ShopRole.STAFF})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        
        new_u2 = User.objects.create_user(email="new2@test.com", password="pw", first_name="N2")
        resp = self.client.post("/api/v1/memberships/", {'tenant': self.shop.id, 'user': new_u2.id, 'role': ShopRole.VIEWER})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_shop_admin_create_admin_denied(self):
        self.client.force_authenticate(user=self.shop_admin_user)
        new_u = User.objects.create_user(email="new1@test.com", password="pw", first_name="N1")
        resp = self.client.post("/api/v1/memberships/", {'tenant': self.shop.id, 'user': new_u.id, 'role': ShopRole.ADMIN})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_shop_admin_role_mutations(self):
        self.client.force_authenticate(user=self.shop_admin_user)
        # STAFF -> VIEWER allowed
        resp = self.client.patch(f"/api/v1/memberships/{self.staff_member.id}/", {'role': ShopRole.VIEWER})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # VIEWER -> ADMIN denied
        resp = self.client.patch(f"/api/v1/memberships/{self.viewer_member.id}/", {'role': ShopRole.ADMIN})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_main_supplier_admin_cardinality(self):
        self.client.force_authenticate(user=self.main_supplier)
        # Demote sole admin -> rejected
        resp = self.client.patch(f"/api/v1/memberships/{self.admin_member.id}/", {'role': ShopRole.STAFF})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Promote staff to admin -> allowed (now 2 admins)
        resp = self.client.patch(f"/api/v1/memberships/{self.staff_member.id}/", {'role': ShopRole.ADMIN})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        
        # Promote viewer to admin -> rejected (would be 3 admins)
        resp = self.client.patch(f"/api/v1/memberships/{self.viewer_member.id}/", {'role': ShopRole.ADMIN})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Demote one admin -> allowed (now 1 admin)
        resp = self.client.patch(f"/api/v1/memberships/{self.staff_member.id}/", {'role': ShopRole.STAFF})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_shop_creation_atomic(self):
        self.client.force_authenticate(user=self.main_supplier)
        valid_u = User.objects.create_user(email="first@test.com", password="pw", first_name="First", phone="+12125550005")
        resp = self.client.post("/api/v1/tenants/", {
            'name': 'New', 'slug': 'new', 'first_admin_user': valid_u.id, 'max_users': 5
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        t = Tenant.objects.get(slug='new')
        self.assertTrue(TenantMember.objects.filter(tenant=t, role=ShopRole.ADMIN).exists())

    def test_global_user_deactivation_guard(self):
        # Admin is sole admin, deactivation should fail
        from apps.accounts.services.user_lifecycle import deactivate_global_user
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            deactivate_global_user(self.main_supplier, self.shop_admin_user)
            
        # Add a second admin
        self.client.force_authenticate(user=self.main_supplier)
        self.client.patch(f"/api/v1/memberships/{self.staff_member.id}/", {'role': ShopRole.ADMIN})
        
        # Now deactivation should succeed
        deactivate_global_user(self.main_supplier, self.shop_admin_user)
        self.shop_admin_user.refresh_from_db()
        self.assertFalse(self.shop_admin_user.is_active)
