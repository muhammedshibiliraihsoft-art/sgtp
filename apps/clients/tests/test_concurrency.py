from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.db import close_old_connections, connection
from django.test import TransactionTestCase, skipUnlessDBFeature

from apps.accounts.models import User
from apps.clients.models import Client
from apps.clients.services import create_contact, update_contact
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember


@skipUnlessDBFeature("has_select_for_update")
class ClientDuplicateConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.supplier, _ = Supplier.objects.get_or_create(
            singleton_lock=True, defaults={"name": "Main Supplier"}
        )
        self.shop = Tenant.objects.create(
            supplier=self.supplier,
            name="Concurrency Shop",
            slug="client-concurrency-shop",
            max_users=20,
        )
        self.user = User.objects.create_user(
            email="client-concurrency@example.test",
            password="Safe-Test-Password-293!",
            first_name="Concurrency",
            owning_shop=self.shop,
        )
        TenantMember.objects.create(
            user=self.user, tenant=self.shop, role=ShopRole.ADMIN
        )

    def run_parallel(self, operation):
        barrier = Barrier(2)

        def worker():
            close_old_connections()
            try:
                actor = User.objects.get(pk=self.user.pk)
                barrier.wait(timeout=10)
                return operation(actor)
            finally:
                connection.close()
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(worker) for _ in range(2)]
            return [future.result(timeout=30) for future in futures]

    def test_concurrent_identical_creates_serialize_duplicate_warning_check(self):
        results = self.run_parallel(
            lambda actor: create_contact(
                model=Client,
                shop_id=self.shop.pk,
                values={"name": "Concurrent", "phone": "+96550007777"},
                actor=actor,
            )
        )
        self.assertEqual(Client.objects.filter(tenant=self.shop).count(), 2)
        self.assertEqual(
            sorted(bool(warnings) for _, warnings in results), [False, True]
        )

    def test_concurrent_contact_updates_serialize_duplicate_warning_check(self):
        first = Client.objects.create(tenant=self.shop, name="First")
        second = Client.objects.create(tenant=self.shop, name="Second")

        def update_target(actor, target_id):
            return update_contact(
                model=Client,
                shop_id=self.shop.pk,
                record_id=target_id,
                values={"phone": "+96550008888"},
                actor=actor,
            )

        barrier = Barrier(2)

        def worker(target_id):
            close_old_connections()
            try:
                actor = User.objects.get(pk=self.user.pk)
                barrier.wait(timeout=10)
                return update_target(actor, target_id)
            finally:
                connection.close()
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(worker, first.pk),
                executor.submit(worker, second.pk),
            ]
            results = [future.result(timeout=30) for future in futures]
        self.assertEqual(
            sorted(bool(warnings) for _, warnings in results), [False, True]
        )
