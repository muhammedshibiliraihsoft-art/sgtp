import threading
from concurrent.futures import ThreadPoolExecutor

from django.contrib.auth import get_user_model
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.test import TransactionTestCase

from apps.accounts.tests.factories import create_test_user
from apps.tenants.models import (
    MembershipWorkFunction,
    ShopRole,
    Supplier,
    Tenant,
    TenantMember,
)
from apps.tenants.services.work_functions import set_membership_work_functions

User = get_user_model()


class WorkFunctionConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.assertEqual(
            connection.vendor,
            "postgresql",
            "Work-Function row-lock tests require PostgreSQL.",
        )
        supplier, _created = Supplier.objects.get_or_create(singleton_lock=True)
        self.shop = Tenant.objects.create(
            supplier=supplier,
            name="Concurrent functions Shop",
            slug="concurrent-functions-shop",
            max_users=10,
        )
        self.admin = create_test_user(
            owning_shop=self.shop,
            email="concurrent-functions-admin@example.test",
            first_name="Concurrent",
        )
        TenantMember.objects.create(
            tenant=self.shop, user=self.admin, role=ShopRole.ADMIN
        )
        self.worker = create_test_user(
            owning_shop=self.shop,
            email="concurrent-functions-worker@example.test",
            first_name="Concurrent",
        )
        self.membership = TenantMember.objects.create(
            tenant=self.shop, user=self.worker, role=ShopRole.STAFF
        )

    @staticmethod
    def run_concurrently(*operations):
        gate = threading.Barrier(len(operations))

        def run(operation):
            close_old_connections()
            try:
                gate.wait(timeout=10)
                try:
                    operation()
                    return "ok"
                except IntegrityError:
                    return "integrity-error"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=len(operations)) as pool:
            return list(pool.map(run, operations))

    def test_concurrent_set_replacements_leave_one_complete_valid_set(self):
        results = self.run_concurrently(
            lambda: set_membership_work_functions(
                actor=self.admin,
                shop_id=self.shop.pk,
                membership_id=self.membership.pk,
                function_codes=["CUTTING"],
            ),
            lambda: set_membership_work_functions(
                actor=self.admin,
                shop_id=self.shop.pk,
                membership_id=self.membership.pk,
                function_codes=["STITCHING"],
            ),
        )
        self.assertCountEqual(results, ["ok", "ok"])
        current = list(
            MembershipWorkFunction.objects.filter(
                membership=self.membership
            ).values_list("function_code", flat=True)
        )
        self.assertIn(current, [["CUTTING"], ["STITCHING"]])
        self.assertEqual(
            MembershipWorkFunction.objects.all_with_deleted()
            .filter(membership=self.membership)
            .count(),
            2,
        )

    def test_concurrent_duplicate_direct_inserts_are_stopped_by_database(self):
        def insert_duplicate():
            with transaction.atomic():
                MembershipWorkFunction.objects.create(
                    membership_id=self.membership.pk,
                    function_code="QC",
                )

        results = self.run_concurrently(insert_duplicate, insert_duplicate)
        self.assertCountEqual(results, ["ok", "integrity-error"])
        self.assertEqual(
            MembershipWorkFunction.objects.filter(
                membership=self.membership, function_code="QC"
            ).count(),
            1,
        )
