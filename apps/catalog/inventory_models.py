from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.functions import Floor
from safedelete.managers import SafeDeleteDeletedManager, SafeDeleteManager
from safedelete.queryset import SafeDeleteQueryset

from backend.core.models import BaseModel
from apps.catalog.inventory_types import StockMovementType, StockUnit
from apps.catalog.measurement_models import Material
from apps.tenants.models import Tenant


class ImmutableStockQuerySet(SafeDeleteQueryset):
    def update(self, **kwargs):
        raise ValidationError("Stock movement history is immutable.")

    def delete(self, *args, **kwargs):
        raise ValidationError("Stock movement history cannot be deleted.")


class ImmutableStockManager(SafeDeleteManager):
    _queryset_class = ImmutableStockQuerySet


class ImmutableDeletedStockManager(SafeDeleteDeletedManager):
    _queryset_class = ImmutableStockQuerySet


class InventoryBalanceQuerySet(SafeDeleteQueryset):
    def update(self, **kwargs):
        raise ValidationError(
            "Inventory balances may only be changed by stock services."
        )

    def delete(self, *args, **kwargs):
        raise ValidationError("Inventory balances cannot be deleted.")


class InventoryBalanceManager(SafeDeleteManager):
    _queryset_class = InventoryBalanceQuerySet


class InventoryBalanceDeletedManager(SafeDeleteDeletedManager):
    _queryset_class = InventoryBalanceQuerySet


class InventoryBalance(BaseModel):
    """Service-maintained balance; every change must have a ledger movement."""

    tenant = models.ForeignKey(
        Tenant, on_delete=models.PROTECT, related_name="inventory_balances"
    )
    material = models.OneToOneField(
        Material,
        on_delete=models.PROTECT,
        related_name="inventory_balance",
    )
    on_hand = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    reserved = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    objects = InventoryBalanceManager()
    all_objects = InventoryBalanceManager()
    deleted_objects = InventoryBalanceDeletedManager()

    class Meta:
        ordering = ("material_id",)
        constraints = [
            models.CheckConstraint(
                condition=Q(on_hand__gte=0),
                name="inventory_balance_on_hand_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(reserved__gte=0),
                name="inventory_balance_reserved_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(reserved__lte=models.F("on_hand")),
                name="inventory_balance_reserved_lte_on_hand",
            ),
        ]
        indexes = [models.Index(fields=("tenant", "on_hand"))]

    @property
    def available(self):
        return self.on_hand - self.reserved

    def save(self, *args, **kwargs):
        service_update = kwargs.pop("_service_update", False)
        if self._state.adding and (self.on_hand != 0 or self.reserved != 0):
            raise ValidationError(
                "Inventory balances must start at zero; use a stock service."
            )
        if not self._state.adding and not service_update:
            raise ValidationError(
                "Inventory balances may only be changed by stock services."
            )
        if self.material_id and self.material.tenant_id != self.tenant_id:
            raise ValidationError(
                "Inventory balance Shop must match its Material Shop."
            )
        if self.material_id and self.material.stock_unit in {
            StockUnit.PIECE,
            StockUnit.ROLL,
        }:
            if any(
                Decimal(str(value)) != Decimal(str(value)).to_integral_value()
                for value in (self.on_hand, self.reserved)
            ):
                raise ValidationError(
                    "Piece and roll inventory balances must be whole numbers."
                )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Inventory balances cannot be deleted.")


class StockMovement(BaseModel):
    """Append-only record of one Shop Material stock change."""

    tenant = models.ForeignKey(
        Tenant, on_delete=models.PROTECT, related_name="stock_movements"
    )
    material = models.ForeignKey(
        Material, on_delete=models.PROTECT, related_name="stock_movements"
    )
    movement_type = models.CharField(max_length=16, choices=StockMovementType.choices)
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    unit_snapshot = models.CharField(max_length=8, choices=StockUnit.choices)
    on_hand_before = models.DecimalField(max_digits=18, decimal_places=4)
    on_hand_after = models.DecimalField(max_digits=18, decimal_places=4)
    reserved_before = models.DecimalField(max_digits=18, decimal_places=4)
    reserved_after = models.DecimalField(max_digits=18, decimal_places=4)
    actor = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    reason = models.CharField(max_length=300)

    objects = ImmutableStockManager()
    all_objects = ImmutableStockManager()
    deleted_objects = ImmutableDeletedStockManager()

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.CheckConstraint(
                condition=Q(movement_type__in=StockMovementType.values),
                name="stock_movement_type_valid",
            ),
            models.CheckConstraint(
                condition=Q(unit_snapshot__in=StockUnit.values),
                name="stock_movement_unit_valid",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gt=0), name="stock_movement_quantity_positive"
            ),
            models.CheckConstraint(
                condition=Q(unit_snapshot__in=(StockUnit.METRE, StockUnit.YARD))
                | Q(quantity=Floor("quantity")),
                name="stock_movement_piece_roll_whole",
            ),
            models.CheckConstraint(
                condition=Q(on_hand_before__gte=0)
                & Q(on_hand_after__gte=0)
                & Q(reserved_before__gte=0)
                & Q(reserved_after__gte=0),
                name="stock_movement_snapshots_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(reserved_before__lte=models.F("on_hand_before"))
                & Q(reserved_after__lte=models.F("on_hand_after")),
                name="stock_movement_reserved_lte_on_hand",
            ),
        ]
        indexes = [
            models.Index(fields=("tenant", "material", "created_at")),
            models.Index(fields=("material", "movement_type", "created_at")),
        ]

    def clean(self):
        super().clean()
        if self.material_id and self.tenant_id:
            if self.material.tenant_id != self.tenant_id:
                raise ValidationError("Movement Shop must match its Material Shop.")
        if self.material_id and self.unit_snapshot != self.material.stock_unit:
            raise ValidationError("Movement unit must match the Material stock unit.")
        if (
            self.unit_snapshot in {StockUnit.PIECE, StockUnit.ROLL}
            and self.quantity is not None
            and self.quantity != self.quantity.to_integral_value()
        ):
            raise ValidationError(
                {
                    "quantity": "Piece and roll movement quantities must be whole numbers."
                }
            )

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Stock movements are immutable.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Stock movements cannot be deleted.")
