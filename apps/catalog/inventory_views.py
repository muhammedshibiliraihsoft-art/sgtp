from django.db.models import Q
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from apps.accounts.permissions import PasswordChangeGate
from apps.catalog.inventory_models import StockMovement
from apps.catalog.inventory_serializers import (
    InventoryAdjustmentSerializer,
    InventoryBalanceSerializer,
    InventoryEnableSerializer,
    InventoryItemCreateSerializer,
    InventoryItemUpdateSerializer,
    StockMovementSerializer,
    StockMutationSerializer,
)
from apps.catalog.inventory_services import (
    adjust_inventory,
    create_inventory_item,
    enable_material_inventory,
    open_inventory_stock,
    stock_in,
    update_inventory_item,
)
from apps.catalog.inventory_types import InventoryCategory
from apps.catalog.measurement_models import Material
from apps.catalog.measurement_services import archive_material, require_material_access
from apps.common.views import TenantScopedMixin
from apps.tenants.context_views import ShopContextMixin


class InventoryPagination(PageNumberPagination):
    page_size = 20


class InventoryAccess:
    """Apply the existing Material role policy to inventory operations."""

    @staticmethod
    def check(request, *, write=False):
        require_material_access(request.shop_context.shop.pk, request.user, write=write)


def _inventory_rows(request, *, include_archived=False):
    rows = Material.objects.filter(
        tenant=request.shop_context.shop,
        deleted__isnull=True,
        inventory_category__in=InventoryCategory.values,
        inventory_balance__isnull=False,
        inventory_balance__deleted__isnull=True,
    ).select_related("inventory_balance")
    include_archived = include_archived or (
        request.query_params.get("include_archived") == "true"
    )
    membership = request.shop_context.membership
    can_manage = request.shop_context.is_main_supplier or (
        membership is not None and membership.role == "ADMIN"
    )
    if not include_archived or not can_manage:
        rows = rows.filter(status=Material.Status.ACTIVE)
    return rows


class InventoryItemListCreateView(ShopContextMixin, TenantScopedMixin, APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(
        operation_id="inventory_items_list",
        parameters=[
            OpenApiParameter(
                "category",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                enum=InventoryCategory.values,
            ),
            OpenApiParameter("search", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter(
                "include_archived", OpenApiTypes.BOOL, OpenApiParameter.QUERY
            ),
        ],
        responses=inline_serializer(
            name="InventoryItemPage",
            fields={
                "count": serializers.IntegerField(),
                "next": serializers.URLField(allow_null=True),
                "previous": serializers.URLField(allow_null=True),
                "results": InventoryBalanceSerializer(many=True),
            },
        ),
    )
    def get(self, request, shop_id):
        InventoryAccess.check(request)
        rows = _inventory_rows(request)
        category = request.query_params.get("category")
        if category:
            category = serializers.ChoiceField(
                choices=InventoryCategory.choices
            ).run_validation(category.upper())
            rows = rows.filter(inventory_category=category)
        search = request.query_params.get("search", "").strip()
        if search:
            rows = rows.filter(Q(name__icontains=search) | Q(code__icontains=search))
        paginator = InventoryPagination()
        page = paginator.paginate_queryset(rows.order_by("name", "id"), request)
        return paginator.get_paginated_response(
            InventoryBalanceSerializer(page, many=True).data
        )

    @extend_schema(
        operation_id="inventory_items_create",
        request=InventoryItemCreateSerializer,
        responses={201: InventoryBalanceSerializer},
    )
    def post(self, request, shop_id):
        InventoryAccess.check(request, write=True)
        serializer = InventoryItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        material = create_inventory_item(
            shop_id=request.shop_context.shop.pk,
            actor=request.user,
            name=values["name"],
            code=values.get("code", ""),
            description=values.get("description", ""),
            category=values["category"],
            stock_unit=values["stock_unit"],
        )
        material = Material.objects.select_related("inventory_balance").get(
            pk=material.pk
        )
        return Response(
            InventoryBalanceSerializer(material).data, status=status.HTTP_201_CREATED
        )


class InventoryItemDetailView(ShopContextMixin, TenantScopedMixin, APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    def _get_item(self, request, material_id, *, include_archived=False):
        rows = _inventory_rows(request, include_archived=include_archived).filter(
            pk=material_id
        )
        material = rows.first()
        if material is None:
            raise NotFound()
        return material

    @extend_schema(
        operation_id="inventory_item_detail",
        responses=InventoryBalanceSerializer,
    )
    def get(self, request, shop_id, material_id):
        InventoryAccess.check(request)
        return Response(
            InventoryBalanceSerializer(self._get_item(request, material_id)).data
        )

    @extend_schema(
        operation_id="inventory_item_update",
        request=InventoryItemUpdateSerializer,
        responses=InventoryBalanceSerializer,
    )
    def patch(self, request, shop_id, material_id):
        InventoryAccess.check(request, write=True)
        material = self._get_item(request, material_id)
        serializer = InventoryItemUpdateSerializer(
            material, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        material = update_inventory_item(
            shop_id=request.shop_context.shop.pk,
            actor=request.user,
            material_id=material.pk,
            values=serializer.validated_data,
        )
        material = Material.objects.select_related("inventory_balance").get(
            pk=material.pk
        )
        return Response(InventoryBalanceSerializer(material).data)


class EnableMaterialInventoryView(ShopContextMixin, TenantScopedMixin, APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(
        operation_id="inventory_enable_legacy_material",
        request=InventoryEnableSerializer,
        responses={201: InventoryBalanceSerializer},
    )
    def post(self, request, shop_id, material_id):
        InventoryAccess.check(request, write=True)
        serializer = InventoryEnableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        material = enable_material_inventory(
            shop_id=request.shop_context.shop.pk,
            actor=request.user,
            material_id=material_id,
            **serializer.validated_data,
        )
        material = Material.objects.select_related("inventory_balance").get(
            pk=material.pk
        )
        return Response(
            InventoryBalanceSerializer(material).data, status=status.HTTP_201_CREATED
        )


class StockMutationView(ShopContextMixin, TenantScopedMixin, APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)
    mutation_service = None
    input_serializer = StockMutationSerializer

    @extend_schema(
        request=StockMutationSerializer, responses=InventoryBalanceSerializer
    )
    def post(self, request, shop_id, material_id):
        InventoryAccess.check(request, write=True)
        material = InventoryItemDetailView()._get_item(
            request, material_id, include_archived=True
        )
        serializer = self.input_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        self.mutation_service(
            shop_id=request.shop_context.shop.pk,
            actor=request.user,
            material_id=material.pk,
            **values,
        )
        material = Material.objects.select_related("inventory_balance").get(
            pk=material.pk
        )
        return Response(InventoryBalanceSerializer(material).data)


class OpeningStockView(StockMutationView):
    mutation_service = staticmethod(open_inventory_stock)


class StockInView(StockMutationView):
    mutation_service = staticmethod(stock_in)


class InventoryAdjustmentView(StockMutationView):
    mutation_service = staticmethod(adjust_inventory)
    input_serializer = InventoryAdjustmentSerializer

    @extend_schema(
        operation_id="inventory_adjust_stock",
        request=InventoryAdjustmentSerializer,
        responses=InventoryBalanceSerializer,
    )
    def post(self, request, shop_id, material_id):
        return super().post(request, shop_id, material_id)


class StockMovementListView(ShopContextMixin, TenantScopedMixin, APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(
        operation_id="inventory_movement_history",
        responses=inline_serializer(
            name="StockMovementPage",
            fields={
                "count": serializers.IntegerField(),
                "next": serializers.URLField(allow_null=True),
                "previous": serializers.URLField(allow_null=True),
                "results": StockMovementSerializer(many=True),
            },
        ),
    )
    def get(self, request, shop_id, material_id):
        InventoryAccess.check(request)
        membership = request.shop_context.membership
        if not request.shop_context.is_main_supplier and (
            membership is None or membership.role != "ADMIN"
        ):
            raise PermissionDenied()
        # Inventory is hidden from normal active-item selectors after archive,
        # but ADMIN/Main Supplier must retain read-only access to its ledger.
        material = InventoryItemDetailView()._get_item(
            request, material_id, include_archived=True
        )
        rows = StockMovement.objects.filter(
            tenant=request.shop_context.shop, material=material
        ).select_related("actor")
        paginator = InventoryPagination()
        page = paginator.paginate_queryset(rows, request)
        return paginator.get_paginated_response(
            StockMovementSerializer(page, many=True).data
        )


class MaterialInventoryArchiveView(ShopContextMixin, TenantScopedMixin, APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(
        operation_id="inventory_item_archive",
        request=None,
        responses=InventoryBalanceSerializer,
    )
    def post(self, request, shop_id, material_id):
        InventoryAccess.check(request, write=True)
        material = archive_material(
            shop_id=request.shop_context.shop.pk,
            actor=request.user,
            material_id=material_id,
        )
        material = Material.objects.select_related("inventory_balance").get(
            pk=material.pk
        )
        return Response(InventoryBalanceSerializer(material).data)
