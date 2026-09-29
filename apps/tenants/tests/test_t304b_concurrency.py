import threading
from django.test import TransactionTestCase
from django.db import connection
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant, Supplier, TenantMember, ShopRole

User = get_user_model()

class T304BConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.supplier, _ = Supplier.objects.get_or_create(singleton_lock=True)
        self.shop = Tenant.objects.create(name="Test Shop", slug="test-shop", supplier=self.supplier, max_users=10)
        self.main_supplier = User.objects.create_superuser(
            email="main@sgtp.com", password="pw", first_name="Main", phone="+12125550006"
        )
        self.admin1 = User.objects.create_user(email="admin1@test.com", password="pw", first_name="A1", phone="+12125550007")
        self.u1 = User.objects.create_user(email="u1@test.com", password="pw", first_name="U1", phone="+12125550008")
        self.u2 = User.objects.create_user(email="u2@test.com", password="pw", first_name="U2", phone="+12125550009")
        
        self.m_admin1 = TenantMember.objects.create(tenant=self.shop, user=self.admin1, role=ShopRole.ADMIN, is_active=True)
        self.m_u1 = TenantMember.objects.create(tenant=self.shop, user=self.u1, role=ShopRole.STAFF, is_active=True)
        self.m_u2 = TenantMember.objects.create(tenant=self.shop, user=self.u2, role=ShopRole.STAFF, is_active=True)

    def test_concurrent_admin_promotion_limit(self):
        # We have 1 admin. Concurrently promoting u1 and u2 to admin.
        # Only one should succeed because max is 2.
        
        def promote(member, results, idx):
            connection.close()
            client = APIClient()
            client.force_authenticate(user=self.main_supplier)
            r = client.patch(f"/api/v1/memberships/{member.id}/", {'role': ShopRole.ADMIN})
            results[idx] = r.status_code
            connection.close()
            
        threads = []
        results = [None, None]
        for i, m in enumerate([self.m_u1, self.m_u2]):
            t = threading.Thread(target=promote, args=(m, results, i))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        successes = [r for r in results if r == status.HTTP_200_OK]
        fails = [r for r in results if r == status.HTTP_400_BAD_REQUEST]
        
        # 1 success, 1 failure
        self.assertEqual(len(successes), 1)
        self.assertEqual(len(fails), 1)
        self.assertEqual(TenantMember.objects.filter(tenant=self.shop, role=ShopRole.ADMIN).count(), 2)
