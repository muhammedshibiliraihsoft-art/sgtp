from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import threading
from django.db import connection

User = get_user_model()

class T302ConcurrencyTests(TransactionTestCase):
    def setUp(self):
        from apps.tenants.models import Tenant, Supplier
        supplier, _ = Supplier.objects.get_or_create(singleton_lock=True)
        self.shop = Tenant.objects.create(name="Test Shop", slug="test-shop", supplier=supplier, max_users=2)
        self.user = User.objects.create_superuser(email="admin@test.com", password="pw", first_name='Main', phone='+96550000000')

    def test_concurrent_capacity_race(self):
        """F-06: Real concurrency proof. Verify final membership count never exceeds max_users."""
        # Create users to be added concurrently
        u1 = User.objects.create_user(email="u1@test.com", password="pw", first_name='Test')
        u2 = User.objects.create_user(email="u2@test.com", password="pw", first_name='Test')
        u3 = User.objects.create_user(email="u3@test.com", password="pw", first_name='Test')
        users = [u1, u2, u3]
        
        def create_membership(user, results_list, idx):
            # Close connection so it uses a new one in the thread
            connection.close()
            client = APIClient()
            client.force_authenticate(user=self.user)
            r = client.post("/api/v1/memberships/", {'tenant': self.shop.id, 'user': user.id})
            results_list[idx] = r.status_code
            connection.close()

        threads = []
        results = [None, None, None]
        for i, u in enumerate(users):
            t = threading.Thread(target=create_membership, args=(u, results, i))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        # 2 should succeed, 1 should fail
        successes = [r for r in results if r == status.HTTP_201_CREATED]
        fails = [r for r in results if r == status.HTTP_400_BAD_REQUEST]
        
        from apps.tenants.models import TenantMember
        # Ensure only 2 created
        self.assertEqual(TenantMember.objects.filter(tenant=self.shop).count(), 2)
        self.assertEqual(len(successes), 2)
        self.assertEqual(len(fails), 1)
