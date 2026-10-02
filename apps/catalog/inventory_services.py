from decimal import Decimal

from django.db import IntegrityError, transaction
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.fields import ErrorDetail

from apps.catalog.inventory_models import InventoryBalance, StockMovement
from apps.catalog.inventory_types import InventoryCategory, StockMovementType, StockUnit
from apps.catalog.measurement_models import Material
from apps.catalog.measurement_services import require_material_access


def _business_error(field, code, detail):
    return ValidationError({field: [ErrorDetail(detail, code=code)]})


def _validate_quantity(material, quantity):
    quantity = Decimal(quantity)
    if quantity <= 0:
        raise _business_error(
            "quantity", "invalid_quantity", "Quantity must be greater than zero."
        )
    if material.stock_unit in {StockUnit.PIECE, StockUnit.ROLL}:
        if quantity != quantity.to_integral_value():
            raise _business_error(
                "quantity",
                "whole_quantity_required",
                "Piece and roll quantities must be whole numbers.",
            )
    return quantity


def _lock_inventory_item(shop, material_id):
    material = (
        Material.objects.select_for_update()
        .filter(
            pk=material_id,
            tenant=shop,
            status=Material.Status.ACTIVE,
            deleted__isnull=True,
            inventory_category__in=InventoryCategory.values,
            stock_unit__in=StockUnit.values,
        )
        .first()
    )
    if material is None:
        raise NotFound()
    balance = (
        InventoryBalance.objects.select_for_update()
        .filter(material=material, tenant=shop, deleted__isnull=True)
        .first()
    )
    if balance is None:
        raise _business_error(
            "inventory",
            "inventory_balance_missing",
            "Inventory balance is unavailable; contact an administrator.",
        )
    return material, balance


def _assert_same_shop(material, shop):
    if material.tenant_id != shop.pk:
        raise NotFound()


def _record_movement(
    *,
    shop,
    material,
    balance,
    actor,
    movement_type,
    quantity,
    reason,
    on_hand_after,
    reserved_after=None,
):
    _assert_same_shop(material, shop)
    quantity = _validate_quantity(material, quantity)
    reserved_after = balance.reserved if reserved_after is None else reserved_after
    movement = StockMovement.objects.create(
        tenant=shop,
        material=material,
        movement_type=movement_type,
        quantity=quantity,
        unit_snapshot=material.stock_unit,
        on_hand_before=balance.on_hand,
        on_hand_after=on_hand_after,
        reserved_before=balance.reserved,
        reserved_after=reserved_after,
        actor=actor,
        created_by=actor,
        updated_by=actor,
        reason=reason.strip(),
    )
    balance.on_hand = on_hand_after
    balance.reserved = reserved_after
    balance.updated_by = actor
    balance.save(
        update_fields=("on_hand", "reserved", "updated_by", "updated_at"),
        _service_update=True,
    )
    return movement


@transaction.atomic
def create_inventory_item(
    *, shop_id, actor, name, code="", description="", category, stock_unit
):
    shop, _membership = require_material_access(shop_id, actor, write=True, lock=True)
    try:
        with transaction.atomic():
            material = Material.objects.create(
                tenant=shop,
                name=name,
                code=code,
                description=description,
                inventory_category=category,
                stock_unit=stock_unit,
                created_by=actor,
                updated_by=actor,
            )
            InventoryBalance.objects.create(
                tenant=shop,
                material=material,
                created_by=actor,
                updated_by=actor,
            )
            return material
    except IntegrityError as exc:
        raise _business_error(
            "code",
            "duplicate_item_code",
            "This Shop-local material code is already in use.",
        ) from exc


@transaction.atomic
def enable_material_inventory(*, shop_id, actor, material_id, category, stock_unit):
    shop, _membership = require_material_access(shop_id, actor, write=True, lock=True)
    material = (
        Material.objects.select_for_update()
        .filter(
            pk=material_id,
            tenant=shop,
            status=Material.Status.ACTIVE,
            deleted__isnull=True,
        )
        .first()
    )
    if material is None:
        raise NotFound()
    if material.inventory_category or material.stock_unit:
        raise _business_error(
            "material_id",
            "already_inventory_enabled",
            "Material is already inventory-enabled.",
        )
    try:
        with transaction.atomic():
            material.inventory_category = category
            material.stock_unit = stock_unit
            material.updated_by = actor
            material.save(
                update_fields=(
                    "inventory_category",
                    "stock_unit",
                    "updated_by",
                    "updated_at",
                )
            )
            InventoryBalance.objects.create(
                tenant=shop,
                material=material,
                created_by=actor,
                updated_by=actor,
            )
    except IntegrityError as exc:
        raise ValidationError(
            {"material_id": "Material inventory configuration is unavailable."}
        ) from exc
    return material


@transaction.atomic
def update_inventory_item(*, shop_id, actor, material_id, values):
    shop, _membership = require_material_access(shop_id, actor, write=True, lock=True)
    material, _balance = _lock_inventory_item(shop, material_id)
    if {"inventory_category", "stock_unit"}.intersection(values):
        if StockMovement.objects.filter(material=material).exists():
            for field in ("inventory_category", "stock_unit"):
                if field in values and values[field] != getattr(material, field):
                    raise _business_error(
                        field,
                        (
                            "unit_locked_by_history"
                            if field == "stock_unit"
                            else "category_locked_by_history"
                        ),
                        "Inventory classification cannot change after stock history exists.",
                    )
    try:
        with transaction.atomic():
            for field, value in values.items():
                setattr(material, field, value)
            material.updated_by = actor
            material.save()
    except IntegrityError as exc:
        raise _business_error(
            "code",
            "duplicate_item_code",
            "This Shop-local material code is already in use.",
        ) from exc
    return material


@transaction.atomic
def open_inventory_stock(*, shop_id, actor, material_id, quantity, reason):
    shop, _membership = require_material_access(shop_id, actor, write=True, lock=True)
    material, balance = _lock_inventory_item(shop, material_id)
    if StockMovement.objects.filter(material=material).exists() or balance.on_hand:
        raise _business_error(
            "quantity",
            "opening_stock_already_recorded",
            "Opening stock can only be recorded once.",
        )
    quantity = _validate_quantity(material, quantity)
    _record_movement(
        shop=shop,
        material=material,
        balance=balance,
        actor=actor,
        movement_type=StockMovementType.OPENING,
        quantity=quantity,
        reason=reason,
        on_hand_after=quantity,
    )
    return balance


@transaction.atomic
def stock_in(*, shop_id, actor, material_id, quantity, reason):
    shop, _membership = require_material_access(shop_id, actor, write=True, lock=True)
    material, balance = _lock_inventory_item(shop, material_id)
    quantity = _validate_quantity(material, quantity)
    _record_movement(
        shop=shop,
        material=material,
        balance=balance,
        actor=actor,
        movement_type=StockMovementType.STOCK_IN,
        quantity=quantity,
        reason=reason,
        on_hand_after=balance.on_hand + quantity,
    )
    return balance


@transaction.atomic
def adjust_inventory(*, shop_id, actor, material_id, direction, quantity, reason):
    shop, _membership = require_material_access(shop_id, actor, write=True, lock=True)
    material, balance = _lock_inventory_item(shop, material_id)
    quantity = _validate_quantity(material, quantity)
    direction = direction.upper()
    if direction == "IN":
        movement_type = StockMovementType.ADJUSTMENT_IN
        on_hand_after = balance.on_hand + quantity
    elif direction == "OUT":
        if quantity > balance.available:
            raise _business_error(
                "quantity",
                "insufficient_stock",
                "Requested quantity exceeds available stock.",
            )
        movement_type = StockMovementType.ADJUSTMENT_OUT
        on_hand_after = balance.on_hand - quantity
    else:
        raise _business_error(
            "direction", "invalid_adjustment_direction", "Direction must be IN or OUT."
        )
    _record_movement(
        shop=shop,
        material=material,
        balance=balance,
        actor=actor,
        movement_type=movement_type,
        quantity=quantity,
        reason=reason,
        on_hand_after=on_hand_after,
    )
    return balance
