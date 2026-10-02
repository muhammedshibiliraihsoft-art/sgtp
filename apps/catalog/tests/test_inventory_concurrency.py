from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

from django.db import close_old_connections, connection
from django.test import TransactionTestCase, skipUnlessDBFeature
from rest_framework.exceptions import NotFound, ValidationError as DRFValidationError

from apps.accounts.models import User
from apps.catalog.inventory_models import InventoryBalance, StockMovement
from apps.catalog.inventory_services import (
    adjust_inventory,
    create_inventory_item,
    enable_material_inventory,
    open_inventory_stock,
    stock_in,
)
from apps.catalog.measurement_models import Material
from apps.catalog.measurement_services import archive_material
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember


@skipUnlessDBFeature("has_select_for_update")
class InventoryConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.assertEqual(connection.vendor, "postgresql")
        supplier, _created = Supplier.objects.get_or_create(singleton_lock=True)
        self.shop = Tenant.objects.create(
            supplier=supplier,
            name="Inventory Race Shop",
            slug="inventory-race-shop",
            max_users=10,
        )
        self.actor = User.objects.create_user(
            email="inventory-race-admin@example.test",
            password="Safe-Test-Password-293!",
            first_name="Inventory Race",
            owning_shop=self.shop,
        )
        TenantMember.objects.create(
            tenant=self.shop, user=self.actor, role=ShopRole.ADMIN
        )
        self.material = create_inventory_item(
            shop_id=self.shop.pk,
            actor=self.actor,
            name="Race Cotton",
            code="race-cotton",
            category="FABRIC",
            stock_unit="METRE",
        )
        open_inventory_stock(
            shop_id=self.shop.pk,
            actor=self.actor,
            material_id=self.material.pk,
            quantity=Decimal("5.0000"),
            reason="Concurrent baseline",
        )

    def concurrently(self, operation, other_operation=None):
        barrier = Barrier(2)
        return_results = other_operation is not None

        def run(operation_to_run):
            close_old_connections()
            try:
                actor = User.objects.get(pk=self.actor.pk)
                barrier.wait(timeout=10)
                try:
                    result = operation_to_run(actor)
                    return result if return_results else "success"
                except (DRFValidationError, NotFound):
                    return "rejected"
            finally:
                connection.close()
                close_old_connections()

        operations = (operation, other_operation or operation)
        with ThreadPoolExecutor(max_workers=2) as pool:
            return [
                future.result(timeout=30)
                for future in (
                    pool.submit(run, operations[0]),
                    pool.submit(run, operations[1]),
                )
            ]

    def test_concurrent_stock_out_never_oversells(self):
        def deduct(actor):
            return adjust_inventory(
                shop_id=self.shop.pk,
                actor=actor,
                material_id=self.material.pk,
                direction="OUT",
                quantity=Decimal("4.0000"),
                reason="Concurrent deduction",
            )

        results = self.concurrently(deduct)
        self.assertEqual(results.count("success"), 1)
        self.assertEqual(results.count("rejected"), 1)
        balance = InventoryBalance.objects.get(material=self.material)
        self.assertEqual(balance.on_hand, Decimal("1.0000"))
        self.assertEqual(
            StockMovement.objects.filter(
                material=self.material, movement_type="ADJUSTMENT_OUT"
            ).count(),
            1,
        )

    def test_concurrent_stock_in_preserves_both_movements(self):
        def receive(actor):
            return stock_in(
                shop_id=self.shop.pk,
                actor=actor,
                material_id=self.material.pk,
                quantity=Decimal("2.2500"),
                reason="Concurrent delivery",
            )

        results = self.concurrently(receive)
        self.assertEqual(results, ["success", "success"])
        self.assertEqual(
            InventoryBalance.objects.get(material=self.material).on_hand,
            Decimal("9.5000"),
        )
        self.assertEqual(
            StockMovement.objects.filter(
                material=self.material, movement_type="STOCK_IN"
            ).count(),
            2,
        )

    def test_concurrent_adjustments_do_not_lose_updates(self):
        def adjust(actor):
            return adjust_inventory(
                shop_id=self.shop.pk,
                actor=actor,
                material_id=self.material.pk,
                direction="IN",
                quantity=Decimal("1.0000"),
                reason="Concurrent adjustment",
            )

        self.assertEqual(self.concurrently(adjust), ["success", "success"])
        self.assertEqual(
            InventoryBalance.objects.get(material=self.material).on_hand,
            Decimal("7.0000"),
        )
        self.assertEqual(
            StockMovement.objects.filter(
                material=self.material, movement_type="ADJUSTMENT_IN"
            ).count(),
            2,
        )

    def test_concurrent_inventory_enablement_creates_one_balance(self):
        reference = Material.objects.create(
            tenant=self.shop, name="Legacy Cotton", code="legacy-cotton"
        )

        def enable(actor):
            return enable_material_inventory(
                shop_id=self.shop.pk,
                actor=actor,
                material_id=reference.pk,
                category="FABRIC",
                stock_unit="METRE",
            )

        results = self.concurrently(enable)
        self.assertEqual(results.count("success"), 1)
        self.assertEqual(results.count("rejected"), 1)
        self.assertEqual(InventoryBalance.objects.filter(material=reference).count(), 1)
        self.assertFalse(StockMovement.objects.filter(material=reference).exists())

    def test_archive_and_stock_in_are_serialized_without_archived_stock(self):
        def archive(actor):
            archive_material(
                shop_id=self.shop.pk, actor=actor, material_id=self.material.pk
            )
            return "archived"

        def receive(actor):
            stock_in(
                shop_id=self.shop.pk,
                actor=actor,
                material_id=self.material.pk,
                quantity=Decimal("1.0000"),
                reason="Archive race delivery",
            )
            return "stocked"

        outcomes = self.concurrently(archive, receive)
        self.material.refresh_from_db()
        balance = InventoryBalance.objects.get(material=self.material)
        if self.material.status == Material.Status.ARCHIVED:
            self.assertIn("archived", outcomes)
            self.assertEqual(balance.on_hand, Decimal("5.0000"))
        else:
            self.assertIn("stocked", outcomes)
            self.assertEqual(balance.on_hand, Decimal("6.0000"))
