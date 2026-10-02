from decimal import Decimal

from rest_framework import serializers

from apps.catalog.inventory_models import StockMovement
from apps.catalog.inventory_types import InventoryCategory, StockUnit
from apps.catalog.measurement_models import Material


class InventoryItemCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160)
    code = serializers.SlugField(max_length=64, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    category = serializers.ChoiceField(choices=InventoryCategory.choices)
    stock_unit = serializers.ChoiceField(choices=StockUnit.choices)


class InventoryItemUpdateSerializer(serializers.ModelSerializer):
    category = serializers.ChoiceField(
        source="inventory_category", choices=InventoryCategory.choices, required=False
    )
    stock_unit = serializers.ChoiceField(choices=StockUnit.choices, required=False)

    class Meta:
        model = Material
        fields = ("name", "code", "description", "category", "stock_unit")


class InventoryEnableSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=InventoryCategory.choices)
    stock_unit = serializers.ChoiceField(choices=StockUnit.choices)


class StockMutationSerializer(serializers.Serializer):
    quantity = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal("0.0000")
    )
    reason = serializers.CharField(max_length=300, trim_whitespace=True)


class InventoryAdjustmentSerializer(StockMutationSerializer):
    direction = serializers.ChoiceField(choices=("IN", "OUT"))


class InventoryBalanceSerializer(serializers.Serializer):
    material_id = serializers.UUIDField(source="pk", read_only=True)
    name = serializers.CharField(read_only=True)
    code = serializers.CharField(read_only=True)
    category = serializers.CharField(source="inventory_category", read_only=True)
    unit = serializers.CharField(source="stock_unit", read_only=True)
    status = serializers.CharField(read_only=True)
    on_hand = serializers.DecimalField(
        max_digits=18,
        decimal_places=4,
        read_only=True,
        source="inventory_balance.on_hand",
    )
    reserved = serializers.DecimalField(
        max_digits=18,
        decimal_places=4,
        read_only=True,
        source="inventory_balance.reserved",
    )
    available = serializers.DecimalField(
        max_digits=18,
        decimal_places=4,
        read_only=True,
        source="inventory_balance.available",
    )
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class StockMovementSerializer(serializers.ModelSerializer):
    material_id = serializers.UUIDField(read_only=True)
    shop_id = serializers.UUIDField(source="tenant_id", read_only=True)
    actor_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = StockMovement
        fields = (
            "id",
            "shop_id",
            "material_id",
            "movement_type",
            "quantity",
            "unit_snapshot",
            "on_hand_before",
            "on_hand_after",
            "reserved_before",
            "reserved_after",
            "actor_id",
            "reason",
            "created_at",
        )
        read_only_fields = fields
