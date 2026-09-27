import pytest
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.tenants.models import Tenant, Supplier, TenantMember, ShopRole

User = get_user_model()

class TenantMemberAPITest(APITestCase):
    def setUp(self):
        self.supplier = Supplier.objects.get(singleton_lock=True)
        self.tenant = Tenant.objects.create(
            name="API Shop", slug="api-shop", supplier=self.supplier
        )
        self.admin_user = User.objects.create_superuser(
            email="admin@test.com", password="testpass"
        )
        self.regular_user = User.objects.create_user(
            email="user@test.com", password="testpass"
        )
        
    def test_admin_can_create_membership(self):
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/v1/memberships/'
        data = {
            'tenant': self.tenant.id,
            'user': self.regular_user.id,
            'role': ShopRole.STAFF
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(TenantMember.objects.filter(user=self.regular_user).exists())

    def test_regular_user_cannot_manage_memberships(self):
        self.client.force_authenticate(user=self.regular_user)
        url = '/api/v1/memberships/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_cannot_assign_inactive_user_via_api(self):
        self.client.force_authenticate(user=self.admin_user)
        inactive_user = User.objects.create_user(
            email="inactive@test.com", password="testpass", is_active=False
        )
        url = '/api/v1/memberships/'
        data = {
            'tenant': self.tenant.id,
            'user': inactive_user.id,
            'role': ShopRole.VIEWER
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        if 'errors' in response.data:
            self.assertIn('user', response.data['errors'])
        else:
            self.assertIn('user', response.data)
