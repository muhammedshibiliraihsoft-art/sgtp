from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.exceptions import ValidationError
import threading
from django.db import connection
from apps.tenants.services.shop_accounts import create_shop_account
from apps.tenants.models import ShopRole

User = get_user_model()

class T302ConcurrencyTests(TransactionTestCase):
    def setUp(self):
        from apps.tenants.models import Tenant, Supplier
        supplier, _ = Supplier.objects.get_or_create(singleton_lock=True)
        self.shop = Tenant.objects.create(name="Test Shop", slug="test-shop", supplier=supplier, max_users=2)
        self.user = User.objects.create_superuser(email="admin@test.com", password="pw", first_name='Main', phone='+96550000000')

    def test_concurrent_capacity_race(self):
        """F-06: Real concurrency proof. Verify final membership count never exceeds max_users."""
        gate = threading.Barrier(3)

        def create_account(index, results_list):
            # Close connection so it uses a new one in the thread
            connection.close()
            gate.wait(timeout=10)
            try:
                create_shop_account(
                    actor=self.user,
                    shop_id=self.shop.pk,
                    role=ShopRole.STAFF,
                    account_data={
                        "email": f"capacity{index}@test.com",
                        "first_name": f"Staff{index}",
                        "login_id": f"staff{index}",
                    },
                )
                results_list[index] = status.HTTP_201_CREATED
            except ValidationError:
                results_list[index] = status.HTTP_400_BAD_REQUEST
            connection.close()

        threads = []
        results = [None, None, None]
        for i in range(3):
            t = threading.Thread(target=create_account, args=(i, results))
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
