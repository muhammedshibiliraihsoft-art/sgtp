from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from ..models import Tenant
from ..serializers import (
    TenantSerializer,
    TenantCreateSerializer,
    TenantSummarySerializer,
    TenantAdminSerializer,
    TenantAdminSummarySerializer,
)
from ..permissions import IsMainSupplierAdmin
from apps.accounts.permissions import PasswordChangeGate
from ..policy import ShopRolePolicy
from .membership import TenantMemberViewSet


class TenantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tenants.
    Provides CRUD operations for tenant management.
    """

    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_active", "max_users"]
    search_fields = ["name", "slug", "contact_email", "domain"]
    ordering_fields = ["name", "created_at", "user_count"]
    ordering = ["name"]

    def get_serializer_class(self):
        is_main_supplier_admin = ShopRolePolicy.is_main_supplier_admin(
            self.request.user
        )
        if self.action == "create":
            return TenantCreateSerializer
        elif self.action == "list":
            if is_main_supplier_admin:
                return TenantAdminSummarySerializer
            return TenantSummarySerializer
        if is_main_supplier_admin:
            return TenantAdminSerializer
        return TenantSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions.
        Admins can do everything, regular users can only view.
        """
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
            "activate",
            "deactivate",
        ]:
            permission_classes = [IsMainSupplierAdmin, PasswordChangeGate]
        else:
            permission_classes = [IsAuthenticated, PasswordChangeGate]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Create the Shop and its first ADMIN atomically."""
        from ..services.membership import create_shop_with_first_admin

        validated_data = dict(serializer.validated_data)
        first_admin = validated_data.pop("first_admin_user")
        serializer.instance = create_shop_with_first_admin(
            actor=self.request.user,
            shop_data=validated_data,
            first_admin_user_id=first_admin.pk,
        )

    def perform_update(self, serializer):
        """Set the updater when updating a tenant."""
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsMainSupplierAdmin])
    def activate(self, request, pk=None):
        """Activate a tenant."""
        tenant = self.get_object()
        tenant.is_active = True
        tenant.updated_by = request.user
        tenant.save()
        return Response({"status": "Tenant activated"})

    @action(detail=True, methods=["post"], permission_classes=[IsMainSupplierAdmin])
    def deactivate(self, request, pk=None):
        """Deactivate a tenant."""
        tenant = self.get_object()
        tenant.is_active = False
        tenant.updated_by = request.user
        tenant.save()
        return Response({"status": "Tenant deactivated"})

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        """Get tenant statistics."""
        tenant = self.get_object()
        return Response(
            {
                "user_count": tenant.user_count,
                "max_users": tenant.max_users,
                "is_at_user_limit": tenant.is_at_user_limit,
                "is_active": tenant.is_active,
            }
        )
