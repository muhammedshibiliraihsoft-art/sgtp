from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.contrib.auth import get_user_model
from django.db import close_old_connections
from django.test import TransactionTestCase, skipUnlessDBFeature
from rest_framework.exceptions import ValidationError

from apps.accounts.tests.factories import create_test_user
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember
from apps.tenants.services.shop_accounts import create_shop_account
from apps.tenants.services.shop_management import set_shop_active, update_shop

User = get_user_model()


@skipUnlessDBFeature("has_select_for_update")
class T305ShopManagementConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.supplier, _ = Supplier.objects.get_or_create(
            singleton_lock=True, defaults={"name": "Main Supplier"}
        )
        self.main = User.objects.create_superuser(
            email="t305-race-main@example.test",
            password="Strong-Password-993!",
            first_name="Main",
            phone="+96550000001",
        )
        self.shop = Tenant.objects.create(
            supplier=self.supplier,
            name="Race Shop",
            slug="t305-race-shop",
            max_users=2,
        )
        first_admin = create_test_user(
            owning_shop=self.shop,
            email="t305-race-admin@example.test",
            password="pw",
            first_name="First",
            phone="+96550000002",
        )
        TenantMember.objects.create(
            tenant=self.shop, user=first_admin, role=ShopRole.ADMIN
        )

    def _concurrently(self, *operations):
        barrier = Barrier(len(operations))

        def run(operation):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return operation()
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=len(operations)) as executor:
            futures = [executor.submit(run, operation) for operation in operations]
            return [future.result(timeout=30) for future in futures]

    def _create_staff(self):
        try:
            create_shop_account(
                actor=self.main,
                shop_id=self.shop.pk,
                role=ShopRole.STAFF,
                account_data={
                    "first_name": "Staff",
                    "login_id": "race_staff",
                    "email": "t305-race-staff@example.test",
                    "phone": "+96550000003",
                },
            )
            return "created"
        except ValidationError:
            return "rejected"

    def test_capacity_lowering_races_safely_with_account_creation(self):
        def lower_capacity():
            try:
                update_shop(self.main, self.shop.pk, {"max_users": 1})
                return "lowered"
            except ValidationError:
                return "rejected"

        results = self._concurrently(self._create_staff, lower_capacity)
        self.shop.refresh_from_db()
        self.assertLessEqual(self.shop.user_count, self.shop.max_users)
        self.assertEqual(results.count("rejected"), 1)
        if "created" in results:
            self.assertEqual(self.shop.max_users, 2)
            self.assertEqual(self.shop.user_count, 2)
        else:
            self.assertEqual(self.shop.max_users, 1)
            self.assertEqual(self.shop.user_count, 1)

    def test_shop_deactivation_races_safely_with_account_creation(self):
        def deactivate():
            set_shop_active(self.main, self.shop.pk, active=False)
            return "deactivated"

        results = self._concurrently(self._create_staff, deactivate)
        self.shop.refresh_from_db()
        self.assertFalse(self.shop.is_active)
        self.assertIn(results[0], {"created", "rejected"})
        self.assertEqual(
            TenantMember.objects.filter(tenant=self.shop, role=ShopRole.STAFF).count(),
            1 if "created" in results else 0,
        )
