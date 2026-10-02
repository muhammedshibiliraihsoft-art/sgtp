from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.catalog.inventory_models import InventoryBalance, StockMovement
from apps.catalog.measurement_models import Material
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember


class InventoryApiTests(APITestCase):
    def setUp(self):
        self.supplier = Supplier.objects.get(singleton_lock=True)
        self.shop_a = self.make_shop("Inventory Shop A", "inventory-shop-a")
        self.shop_b = self.make_shop("Inventory Shop B", "inventory-shop-b")
        self.admin = self.make_user("inventory-admin-a", self.shop_a, ShopRole.ADMIN)
        self.staff = self.make_user("inventory-staff-a", self.shop_a, ShopRole.STAFF)
        self.viewer = self.make_user("inventory-viewer-a", self.shop_a, ShopRole.VIEWER)
        self.other_admin = self.make_user(
            "inventory-admin-b", self.shop_b, ShopRole.ADMIN
        )
        self.main = User.objects.create_superuser(
            email="inventory-main@example.test",
            password="Safe-Test-Password-293!",
            first_name="Inventory Main",
            phone="+96550003300",
        )

    def make_shop(self, name, slug):
        return Tenant.objects.create(
            supplier=self.supplier, name=name, slug=slug, max_users=20
        )

    def make_user(self, name, shop, role):
        user = User.objects.create_user(
            email=f"{name}@example.test",
            password="Safe-Test-Password-293!",
            first_name=name,
            owning_shop=shop,
        )
        TenantMember.objects.create(tenant=shop, user=user, role=role)
        return user

    def items_url(self, shop=None):
        return f"/api/v1/shops/{(shop or self.shop_a).pk}/inventory/items/"

    def create_item(self, *, user=None, name="White Cotton", unit="METRE"):
        actor = user or self.admin
        shop = self.shop_b if actor == self.other_admin else self.shop_a
        self.client.force_authenticate(actor)
        response = self.client.post(
            self.items_url(shop),
            {
                "name": name,
                "code": name.lower().replace(" ", "-"),
                "category": "FABRIC",
                "stock_unit": unit,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return response.data

    def mutation_url(self, material_id, action, shop=None):
        return f"{self.items_url(shop)}{material_id}/{action}/"

    def test_admin_creates_decimal_inventory_item_and_opening_ledger(self):
        item = self.create_item()
        material = Material.objects.get(pk=item["material_id"])
        self.assertEqual(material.inventory_category, "FABRIC")
        self.assertEqual(material.stock_unit, "METRE")
        self.assertEqual(item["on_hand"], "0.0000")
        self.assertEqual(InventoryBalance.objects.get(material=material).available, 0)

        opened = self.client.post(
            self.mutation_url(material.pk, "opening"),
            {"quantity": "3.5000", "reason": "Initial counted stock"},
            format="json",
        )
        self.assertEqual(opened.status_code, status.HTTP_200_OK, opened.data)
        self.assertEqual(opened.data["on_hand"], "3.5000")
        movement = StockMovement.objects.get(material=material)
        self.assertEqual(movement.movement_type, "OPENING")
        self.assertEqual(movement.quantity, Decimal("3.5000"))
        self.assertEqual(movement.unit_snapshot, "METRE")
        self.assertEqual(movement.tenant_id, self.shop_a.pk)
        self.assertEqual(movement.actor_id, self.admin.pk)

    def test_main_supplier_must_use_selected_shop_and_can_manage(self):
        self.client.force_authenticate(self.main)
        no_shop = self.client.post(
            "/api/v1/inventory/items/",
            {"name": "Linen", "category": "FABRIC", "stock_unit": "METRE"},
            format="json",
        )
        self.assertEqual(no_shop.status_code, status.HTTP_404_NOT_FOUND)
        created = self.client.post(
            self.items_url(self.shop_b),
            {"name": "Linen", "category": "FABRIC", "stock_unit": "METRE"},
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        self.assertEqual(
            str(Material.objects.get(pk=created.data["material_id"]).tenant_id),
            str(self.shop_b.pk),
        )

    def test_staff_and_viewer_read_active_inventory_but_cannot_mutate(self):
        item = self.create_item()
        self.client.force_authenticate(self.staff)
        self.assertEqual(
            self.client.get(self.items_url()).status_code, status.HTTP_200_OK
        )
        denied = self.client.post(
            self.mutation_url(item["material_id"], "stock-in"),
            {"quantity": "1", "reason": "not allowed"},
            format="json",
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            self.client.get(
                self.mutation_url(item["material_id"], "movements")
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.client.force_authenticate(self.viewer)
        self.assertEqual(
            self.client.get(self.items_url()).status_code, status.HTTP_200_OK
        )
        self.assertEqual(
            self.client.post(
                self.mutation_url(item["material_id"], "stock-in"),
                {"quantity": "1", "reason": "not allowed"},
                format="json",
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_existing_material_requires_explicit_inventory_enablement(self):
        material = Material.objects.create(
            tenant=self.shop_a, name="Old Reference Fabric", code="old-reference"
        )
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(self.items_url()).data["count"], 0)
        enabled = self.client.post(
            f"/api/v1/shops/{self.shop_a.pk}/materials/{material.pk}/enable-inventory/",
            {"category": "FABRIC", "stock_unit": "YARD"},
            format="json",
        )
        self.assertEqual(enabled.status_code, status.HTTP_201_CREATED, enabled.data)
        self.assertEqual(enabled.data["material_id"], str(material.pk))
        self.assertEqual(enabled.data["on_hand"], "0.0000")
        self.assertFalse(StockMovement.objects.filter(material=material).exists())

    def test_invalid_categories_and_units_are_rejected(self):
        self.client.force_authenticate(self.admin)
        for payload in (
            {"name": "Unknown category", "category": "GARMENT", "stock_unit": "PIECE"},
            {"name": "Unknown unit", "category": "BUTTON", "stock_unit": "BOX"},
        ):
            response = self.client.post(self.items_url(), payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            self.client.get(self.items_url() + "?category=GARMENT").status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(Material.objects.filter(tenant=self.shop_a).count(), 0)

    def test_duplicate_item_code_is_a_shop_local_machine_readable_warning(self):
        self.create_item(name="First Material", unit="METRE")
        self.client.force_authenticate(self.admin)
        duplicate = self.client.post(
            self.items_url(),
            {
                "name": "Duplicate Code",
                "code": "first-material",
                "category": "FABRIC",
                "stock_unit": "METRE",
            },
            format="json",
        )
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            duplicate.data["errors"]["code"][0].code, "duplicate_item_code"
        )
        self.client.force_authenticate(self.other_admin)
        other_shop = self.client.post(
            self.items_url(self.shop_b),
            {
                "name": "Same Code Other Shop",
                "code": "first-material",
                "category": "FABRIC",
                "stock_unit": "METRE",
            },
            format="json",
        )
        self.assertEqual(other_shop.status_code, status.HTTP_201_CREATED)

    def test_stock_in_and_adjustment_are_atomic_and_never_negative(self):
        item = self.create_item()
        material_id = item["material_id"]
        self.client.post(
            self.mutation_url(material_id, "opening"),
            {"quantity": "5.0000", "reason": "Counted"},
            format="json",
        )
        duplicate_opening = self.client.post(
            self.mutation_url(material_id, "opening"),
            {"quantity": "2", "reason": "Must be rejected"},
            format="json",
        )
        self.assertEqual(duplicate_opening.status_code, status.HTTP_400_BAD_REQUEST)

        added = self.client.post(
            self.mutation_url(material_id, "stock-in"),
            {"quantity": "1.2500", "reason": "Delivery"},
            format="json",
        )
        self.assertEqual(added.status_code, status.HTTP_200_OK, added.data)
        self.assertEqual(added.data["on_hand"], "6.2500")

        reduced = self.client.post(
            self.mutation_url(material_id, "adjust"),
            {"direction": "OUT", "quantity": "2.2500", "reason": "Count correction"},
            format="json",
        )
        self.assertEqual(reduced.status_code, status.HTTP_200_OK, reduced.data)
        self.assertEqual(reduced.data["on_hand"], "4.0000")
        too_much = self.client.post(
            self.mutation_url(material_id, "adjust"),
            {"direction": "OUT", "quantity": "4.0001", "reason": "Overdraw"},
            format="json",
        )
        self.assertEqual(too_much.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            too_much.data["errors"]["quantity"][0].code, "insufficient_stock"
        )
        self.assertEqual(
            InventoryBalance.objects.get(material_id=material_id).on_hand,
            Decimal("4.0000"),
        )

    def test_piece_and_roll_quantities_must_be_whole(self):
        item = self.create_item(name="Metal Button", unit="PIECE")
        response = self.client.post(
            self.mutation_url(item["material_id"], "stock-in"),
            {"quantity": "1.5000", "reason": "Fractional piece"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["errors"]["quantity"][0].code, "whole_quantity_required"
        )
        self.assertEqual(
            InventoryBalance.objects.get(material_id=item["material_id"]).on_hand,
            Decimal("0.0000"),
        )

    def test_piece_and_roll_model_records_reject_fractional_values(self):
        item = self.create_item(name="Metal Hook", unit="PIECE")
        material = Material.objects.get(pk=item["material_id"])
        balance = InventoryBalance.objects.get(material=material)
        balance.on_hand = Decimal("1.5000")
        with self.assertRaises(DjangoValidationError):
            balance.save(update_fields=("on_hand", "updated_at"), _service_update=True)
        movement = StockMovement(
            tenant=self.shop_a,
            material=material,
            movement_type="OPENING",
            quantity=Decimal("1.5000"),
            unit_snapshot="PIECE",
            on_hand_before=Decimal("0.0000"),
            on_hand_after=Decimal("1.5000"),
            reserved_before=Decimal("0.0000"),
            reserved_after=Decimal("0.0000"),
            actor=self.admin,
            reason="Fractional pieces are invalid",
        )
        with self.assertRaises(DjangoValidationError):
            movement.save()

    def test_shop_isolation_for_list_detail_movement_and_mutation(self):
        item = self.create_item()
        other_item = self.create_item(user=self.other_admin, name="Foreign Blue Fabric")
        self.client.force_authenticate(self.other_admin)
        other_list = self.client.get(self.items_url(self.shop_b))
        self.assertEqual(other_list.status_code, status.HTTP_200_OK)
        self.assertEqual(other_list.data["count"], 1)
        self.client.force_authenticate(self.admin)
        for query in ("?search=Foreign%20Blue%20Fabric", "?search=foreign-blue-fabric"):
            local_list = self.client.get(self.items_url() + query)
            self.assertEqual(local_list.status_code, status.HTTP_200_OK)
            self.assertEqual(local_list.data["count"], 0)
            self.assertEqual(local_list.data["results"], [])
        local_list = self.client.get(self.items_url() + "?category=FABRIC&page=1")
        self.assertEqual(local_list.status_code, status.HTTP_200_OK)
        self.assertEqual(local_list.data["count"], 1)
        self.assertEqual(
            {row["material_id"] for row in local_list.data["results"]},
            {item["material_id"]},
        )
        self.assertEqual(
            self.client.get(self.items_url() + "?page=2").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.client.force_authenticate(self.other_admin)
        for method, url, payload in (
            ("get", f"{self.items_url(self.shop_b)}{item['material_id']}/", None),
            (
                "get",
                self.mutation_url(item["material_id"], "movements", self.shop_b),
                None,
            ),
            (
                "post",
                self.mutation_url(item["material_id"], "stock-in", self.shop_b),
                {"quantity": "1", "reason": "foreign"},
            ),
            (
                "post",
                self.mutation_url(item["material_id"], "archive", self.shop_b),
                {},
            ),
        ):
            response = (
                getattr(self.client, method)(url, payload, format="json")
                if payload
                else getattr(self.client, method)(url)
            )
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(StockMovement.objects.count(), 0)
        self.assertEqual(
            Material.objects.get(pk=other_item["material_id"]).status,
            Material.Status.ACTIVE,
        )

    def test_archive_is_blocked_with_stock_and_history_survives_zero_balance_archive(
        self,
    ):
        item = self.create_item()
        material_id = item["material_id"]
        archive_url = self.mutation_url(material_id, "archive")
        self.client.post(
            self.mutation_url(material_id, "opening"),
            {"quantity": "2", "reason": "Opening"},
            format="json",
        )
        blocked = self.client.post(archive_url, {}, format="json")
        self.assertEqual(blocked.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            Material.objects.get(pk=material_id).status, Material.Status.ACTIVE
        )
        self.client.post(
            self.mutation_url(material_id, "adjust"),
            {"direction": "OUT", "quantity": "2", "reason": "Zero stock"},
            format="json",
        )
        archived = self.client.post(archive_url, {}, format="json")
        self.assertEqual(archived.status_code, status.HTTP_200_OK, archived.data)
        self.assertEqual(
            StockMovement.objects.filter(material_id=material_id).count(), 2
        )
        self.assertEqual(self.client.get(self.items_url()).data["count"], 0)
        history = self.client.get(self.mutation_url(material_id, "movements"))
        self.assertEqual(history.status_code, status.HTTP_200_OK)
        self.assertEqual(history.data["count"], 2)

    def test_model_cannot_archive_inventory_with_nonzero_balance(self):
        item = self.create_item()
        material = Material.objects.get(pk=item["material_id"])
        balance = InventoryBalance.objects.get(material=material)
        balance.on_hand = Decimal("1.0000")
        balance.save(update_fields=("on_hand", "updated_at"), _service_update=True)
        material.status = Material.Status.ARCHIVED
        with self.assertRaises(DjangoValidationError):
            material.save(update_fields=("status", "updated_at"))

    def test_archive_is_blocked_when_only_reserved_stock_remains(self):
        item = self.create_item()
        material = Material.objects.get(pk=item["material_id"])
        balance = InventoryBalance.objects.get(material=material)
        balance.on_hand = Decimal("2.0000")
        balance.reserved = Decimal("1.0000")
        balance.save(
            update_fields=("on_hand", "reserved", "updated_at"),
            _service_update=True,
        )
        response = self.client.post(
            self.mutation_url(material.pk, "archive"), {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["errors"]["status"][0].code,
            "inventory_stock_remaining",
        )
        self.assertEqual(
            Material.objects.get(pk=material.pk).status, Material.Status.ACTIVE
        )

    def test_inactive_membership_cannot_access_inventory(self):
        item = self.create_item()
        membership = TenantMember.objects.get(tenant=self.shop_a, user=self.admin)
        membership.is_active = False
        membership.save(update_fields=("is_active", "updated_at"))
        self.client.force_authenticate(self.admin)
        self.assertEqual(
            self.client.get(self.items_url()).status_code, status.HTTP_404_NOT_FOUND
        )
        self.assertEqual(
            self.client.post(
                self.mutation_url(item["material_id"], "stock-in"),
                {"quantity": "1", "reason": "Inactive user"},
                format="json",
            ).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_balance_and_movement_rows_are_not_directly_mutable(self):
        item = self.create_item()
        balance = InventoryBalance.objects.get(material_id=item["material_id"])
        with self.assertRaises(DjangoValidationError):
            InventoryBalance.all_objects.filter(pk=balance.pk).update(on_hand=4)
        with self.assertRaises(DjangoValidationError):
            InventoryBalance.objects.create(
                tenant=self.shop_a,
                material=balance.material,
                on_hand=Decimal("2"),
            )
        balance.on_hand = Decimal("4")
        with self.assertRaises(DjangoValidationError):
            balance.save()
        with self.assertRaises(DjangoValidationError):
            InventoryBalance.objects.filter(pk=balance.pk).update(on_hand=4)

        self.client.post(
            self.mutation_url(item["material_id"], "opening"),
            {"quantity": "1", "reason": "Opening"},
            format="json",
        )
        movement = StockMovement.objects.get(material_id=item["material_id"])
        movement.reason = "rewritten"
        with self.assertRaises(DjangoValidationError):
            movement.save()
        with self.assertRaises(DjangoValidationError):
            StockMovement.objects.filter(pk=movement.pk).update(reason="rewritten")
        with self.assertRaises(DjangoValidationError):
            StockMovement.objects.filter(pk=movement.pk).delete()
        with self.assertRaises(DjangoValidationError):
            StockMovement.all_objects.filter(pk=movement.pk).update(reason="rewritten")
        with self.assertRaises(DjangoValidationError):
            StockMovement.deleted_objects.filter(pk=movement.pk).delete()

    def test_category_and_unit_cannot_change_after_stock_history(self):
        item = self.create_item()
        self.client.post(
            self.mutation_url(item["material_id"], "opening"),
            {"quantity": "2", "reason": "Opening"},
            format="json",
        )
        response = self.client.patch(
            f"{self.items_url()}{item['material_id']}/",
            {"stock_unit": "YARD", "category": "OTHER"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        material = Material.objects.get(pk=item["material_id"])
        self.assertEqual(material.stock_unit, "METRE")
        self.assertEqual(material.inventory_category, "FABRIC")
