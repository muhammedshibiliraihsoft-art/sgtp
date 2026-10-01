import uuid

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view

from apps.clients.models import Client, RelatedPerson
from apps.clients.normalization import normalize_phone
from apps.clients.permissions import ClientAccessPermission
from apps.clients.serializers import (
    ClientSerializer,
    ContactWriteResponseSerializer,
    RelatedPersonSerializer,
    RelatedPersonWriteResponseSerializer,
)
from apps.clients.services import (
    create_contact,
    soft_delete_contact,
    update_contact,
)
from apps.common.views import TenantScopedMixin
from apps.tenants.context_views import ShopContextMixin
from core.permissions import IsTenantMember


class ClientQueryMixin:
    filter_backends = ()
    ordering = ("name", "id")

    def filter_queryset(self, queryset):
        term = self.request.query_params.get("search", "").strip()
        if not term:
            return queryset
        normalized_phone = normalize_phone(term)
        conditions = Q(name__icontains=term)
        if normalized_phone:
            conditions |= Q(phone_normalized__startswith=normalized_phone)
        try:
            client_id = uuid.UUID(term)
        except (ValueError, AttributeError):
            pass
        else:
            conditions |= Q(pk=client_id)
        return queryset.filter(conditions).order_by(*self.ordering)


@extend_schema_view(
    get=extend_schema(
        parameters=[
            OpenApiParameter(
                "search",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Unicode name, normalized phone prefix, or exact Client UUID.",
            )
        ]
    )
)
class ClientListCreateView(
    ShopContextMixin,
    TenantScopedMixin,
    ClientQueryMixin,
    generics.ListCreateAPIView,
):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = (IsAuthenticated, IsTenantMember, ClientAccessPermission)

    @extend_schema(
        request=ClientSerializer,
        responses={201: ContactWriteResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record, warnings = create_contact(
            model=Client,
            shop_id=request.shop_context.shop.pk,
            values=serializer.validated_data,
            actor=request.user,
        )
        return Response(
            {**self.get_serializer(record).data, "warnings": warnings},
            status=status.HTTP_201_CREATED,
        )


class ClientDetailView(
    ShopContextMixin, TenantScopedMixin, generics.RetrieveUpdateDestroyAPIView
):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = (IsAuthenticated, IsTenantMember, ClientAccessPermission)
    http_method_names = ("get", "put", "patch", "delete", "head", "options")

    @extend_schema(
        request=ClientSerializer,
        responses={200: ContactWriteResponseSerializer},
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @extend_schema(
        request=ClientSerializer,
        responses={200: ContactWriteResponseSerializer},
    )
    def patch(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        record, warnings = update_contact(
            model=Client,
            shop_id=request.shop_context.shop.pk,
            record_id=instance.pk,
            values=serializer.validated_data,
            actor=request.user,
        )
        return Response({**self.get_serializer(record).data, "warnings": warnings})

    def destroy(self, request, *args, **kwargs):
        record = self.get_object()
        soft_delete_contact(
            model=Client,
            shop_id=request.shop_context.shop.pk,
            record_id=record.pk,
            actor=request.user,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    get=extend_schema(
        parameters=[
            OpenApiParameter(
                "search",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Unicode name, normalized phone prefix, or exact RelatedPerson UUID.",
            )
        ]
    )
)
class RelatedPersonListCreateView(
    ShopContextMixin,
    TenantScopedMixin,
    ClientQueryMixin,
    generics.ListCreateAPIView,
):
    queryset = RelatedPerson.objects.select_related("primary_client")
    serializer_class = RelatedPersonSerializer
    permission_classes = (IsAuthenticated, IsTenantMember, ClientAccessPermission)

    def get_parent(self):
        return get_object_or_404(
            Client.objects.filter(tenant_id=self.request.shop_context.shop.pk),
            pk=self.kwargs["client_id"],
        )

    def get_queryset(self):
        self.get_parent()
        return super().get_queryset().filter(primary_client_id=self.kwargs["client_id"])

    @extend_schema(
        request=RelatedPersonSerializer,
        responses={201: RelatedPersonWriteResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        parent = self.get_parent()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record, warnings = create_contact(
            model=RelatedPerson,
            shop_id=request.shop_context.shop.pk,
            values=serializer.validated_data,
            actor=request.user,
            primary_client=parent.pk,
        )
        return Response(
            {**self.get_serializer(record).data, "warnings": warnings},
            status=status.HTTP_201_CREATED,
        )


class RelatedPersonDetailView(
    ShopContextMixin,
    TenantScopedMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    queryset = RelatedPerson.objects.select_related("primary_client")
    serializer_class = RelatedPersonSerializer
    permission_classes = (IsAuthenticated, IsTenantMember, ClientAccessPermission)
    http_method_names = ("get", "put", "patch", "delete", "head", "options")

    def get_queryset(self):
        parent = Client.objects.filter(
            tenant_id=self.request.shop_context.shop.pk
        ).filter(pk=self.kwargs["client_id"])
        if not parent.exists():
            raise NotFound()
        return super().get_queryset().filter(primary_client_id=self.kwargs["client_id"])

    @extend_schema(
        request=RelatedPersonSerializer,
        responses={200: RelatedPersonWriteResponseSerializer},
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @extend_schema(
        request=RelatedPersonSerializer,
        responses={200: RelatedPersonWriteResponseSerializer},
    )
    def patch(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        record, warnings = update_contact(
            model=RelatedPerson,
            shop_id=request.shop_context.shop.pk,
            record_id=instance.pk,
            values=serializer.validated_data,
            actor=request.user,
        )
        return Response({**self.get_serializer(record).data, "warnings": warnings})

    def destroy(self, request, *args, **kwargs):
        record = self.get_object()
        soft_delete_contact(
            model=RelatedPerson,
            shop_id=request.shop_context.shop.pk,
            record_id=record.pk,
            actor=request.user,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
