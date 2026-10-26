import uuid
from datetime import datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from apps.tenants.context_views import ShopContextMixin
from apps.works.models import WorkOrder
from apps.works.serializers import (
    DeletedWorkFiltersSerializer,
    DeletedWorkSerializer,
    WorkAssignmentSerializer,
    WorkAdvanceSerializer,
    WorkCreateSerializer,
    WorkSerializer,
    WorkUpdateSerializer,
)
from apps.works.services import (
    advance_work,
    assign_work,
    create_work,
    delete_work,
    require_admin,
    update_work,
)
from core.permissions import IsTenantMember


class WorkBase:
    permission_classes = (IsAuthenticated, IsTenantMember)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return WorkOrder.objects.none()
        return WorkOrder.objects.filter(
            tenant=self.request.shop_context.shop
        ).select_related(
            "tenant",
            "client",
            "related_person",
            "design_version__design",
            "measurement_set__profile",
            "material",
            "assigned_membership__user",
        )


class WorkListCreateView(ShopContextMixin, WorkBase, generics.ListCreateAPIView):
    serializer_class = WorkSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        term = self.request.query_params.get("search", "").strip()
        if term:
            condition = Q(work_number__icontains=term) | Q(client__name__icontains=term)
            try:
                condition |= Q(pk=uuid.UUID(term))
            except ValueError:
                pass
            queryset = queryset.filter(condition)
        for param in ("status", "priority"):
            value = self.request.query_params.get(param)
            if value:
                queryset = queryset.filter(**{param: value})
        return queryset.order_by("-created_at", "-id")

    @extend_schema(request=WorkCreateSerializer, responses={201: WorkSerializer})
    def post(self, request, *args, **kwargs):
        serializer = WorkCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        order = create_work(
            context=request.shop_context,
            actor=request.user,
            values=serializer.validated_data,
        )
        return Response(WorkSerializer(order).data, status=status.HTTP_201_CREATED)


class DeletedWorkListView(ShopContextMixin, WorkBase, generics.ListAPIView):
    """Read-only Shop archive; ordinary Work queries remain active-only."""

    serializer_class = DeletedWorkSerializer
    http_method_names = ("get", "head", "options")

    @extend_schema(
        parameters=[
            OpenApiParameter("deleted_from", OpenApiTypes.DATE),
            OpenApiParameter("deleted_to", OpenApiTypes.DATE),
            OpenApiParameter("search", OpenApiTypes.STR),
        ],
        responses={200: DeletedWorkSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return WorkOrder.all_objects.none()
        context = self.request.shop_context
        require_admin(context)
        params = {
            key: self.request.query_params[key]
            for key in ("deleted_from", "deleted_to")
            if key in self.request.query_params
        }
        filters = DeletedWorkFiltersSerializer(data=params)
        filters.is_valid(raise_exception=True)
        try:
            zone = ZoneInfo(context.shop.default_timezone or settings.TIME_ZONE)
        except ZoneInfoNotFoundError:
            zone = ZoneInfo(settings.TIME_ZONE)
        queryset = WorkOrder.all_objects.filter(
            tenant=context.shop, deleted__isnull=False
        ).select_related("tenant", "client", "design_version").prefetch_related(
            "design_version__translations"
        )
        if start_date := filters.validated_data.get("deleted_from"):
            queryset = queryset.filter(
                deleted__gte=timezone.make_aware(
                    datetime.combine(start_date, time.min), zone
                )
            )
        if end_date := filters.validated_data.get("deleted_to"):
            queryset = queryset.filter(
                deleted__lte=timezone.make_aware(
                    datetime.combine(end_date, time.max), zone
                )
            )
        term = self.request.query_params.get("search", "").strip()
        if term:
            queryset = queryset.filter(
                Q(work_number__icontains=term) | Q(client__name__icontains=term)
            )
        return queryset.order_by("-deleted", "-id")


class WorkDetailView(ShopContextMixin, WorkBase, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WorkSerializer
    http_method_names = ("get", "patch", "delete", "head", "options")

    @extend_schema(request=WorkUpdateSerializer, responses={200: WorkSerializer})
    def patch(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = WorkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = update_work(
            context=request.shop_context,
            actor=request.user,
            order_id=order.pk,
            values=serializer.validated_data,
        )
        return Response(WorkSerializer(order).data)

    def delete(self, request, *args, **kwargs):
        order = self.get_object()
        delete_work(context=request.shop_context, actor=request.user, order_id=order.pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkAdvanceView(ShopContextMixin, WorkBase, generics.GenericAPIView):
    serializer_class = WorkSerializer

    @extend_schema(
        request=WorkAdvanceSerializer,
        responses={200: WorkSerializer, 409: OpenApiTypes.OBJECT},
    )
    def post(self, request, shop_id, pk):
        order = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = WorkAdvanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = advance_work(
            context=request.shop_context,
            actor=request.user,
            order_id=order.pk,
            expected_status=serializer.validated_data["expected_status"],
        )
        return Response(WorkSerializer(order).data)


class WorkAssignView(ShopContextMixin, WorkBase, generics.GenericAPIView):
    serializer_class = WorkSerializer

    @extend_schema(request=WorkAssignmentSerializer, responses={200: WorkSerializer})
    def post(self, request, shop_id, pk):
        order = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = WorkAssignmentSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        order = assign_work(
            context=request.shop_context,
            actor=request.user,
            order_id=order.pk,
            membership=serializer.validated_data["membership"],
        )
        return Response(WorkSerializer(order).data)
