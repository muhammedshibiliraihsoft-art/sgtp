from django.db.models import Count, Exists, OuterRef, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import PasswordChangeGate
from ..models import ShopRole, Tenant, TenantMember
from ..policy import ShopRolePolicy
from ..serializers import (
    TenantAdminManagementSerializer,
    TenantAdminSerializer,
    TenantAdminSummarySerializer,
    TenantCreateSerializer,
    TenantMemberProfileSerializer,
    TenantSerializer,
    TenantSummarySerializer,
)
from ..services.membership import create_shop_with_first_admin
from ..services.shop_management import set_shop_active, update_shop
from .membership import TenantMemberViewSet


class MemberLookupSerializer(serializers.Serializer):
    user_code = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    role = serializers.ChoiceField(choices=ShopRole.choices, read_only=True)
    membership_status = serializers.ChoiceField(
        choices=("ACTIVE", "INACTIVE", "REMOVED"), read_only=True
    )


class TenantViewSet(viewsets.ModelViewSet):
    """Compatibility Shop API with authorization applied before all query filters."""

    queryset = Tenant.objects.none()
    permission_classes = [IsAuthenticated, PasswordChangeGate]
    http_method_names = ["get", "post", "put", "patch", "head", "options"]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_active"]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]

    def _is_main_supplier(self):
        return ShopRolePolicy.is_main_supplier_admin(self.request.user)

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated or not user.is_active:
            return Tenant.objects.none()

        queryset = Tenant.objects.select_related("supplier").annotate(
            _user_count=Count(
                "memberships",
                filter=Q(memberships__deleted__isnull=True),
                distinct=True,
            )
        )
        if self._is_main_supplier():
            self.filterset_fields = ["is_active", "max_users"]
            self.search_fields = ["name", "slug", "contact_email", "domain"]
            self.ordering_fields = ["name", "created_at"]
            return queryset

        active_membership = TenantMember.objects.filter(
            tenant_id=OuterRef("pk"),
            user_id=user.pk,
            is_active=True,
            deleted__isnull=True,
            user__is_active=True,
            tenant__is_active=True,
        )
        self.search_fields = ["name"]
        self.ordering_fields = ["name"]
        # This field reflects actual Shop state; inactive memberships must not
        # infer operational state through a result-count side channel.
        self.filterset_fields = []
        return (
            queryset.filter(
                memberships__user_id=user.pk,
                memberships__user__is_active=True,
                memberships__deleted__isnull=True,
            )
            .annotate(_actor_has_active_membership=Exists(active_membership))
            .distinct()
        )

    def get_serializer_class(self):
        if self.action == "create":
            return TenantCreateSerializer
        if self._is_main_supplier():
            if self.action == "list":
                return TenantAdminSummarySerializer
            return TenantAdminSerializer
        membership = (
            ShopRolePolicy.get_active_membership(
                self.request.user, getattr(self, "kwargs", {}).get("pk")
            )
            if getattr(self, "kwargs", {}).get("pk")
            else None
        )
        if self.action == "list":
            return TenantSummarySerializer
        if membership and membership.role == ShopRole.ADMIN:
            return TenantAdminManagementSerializer
        return TenantMemberProfileSerializer

    def get_permissions(self):
        if self.action in {
            "create",
            "update",
            "partial_update",
            "activate",
            "deactivate",
        }:
            from ..permissions import IsMainSupplierAdmin

            classes = [IsMainSupplierAdmin, PasswordChangeGate]
        else:
            classes = [IsAuthenticated, PasswordChangeGate]
        return [permission() for permission in classes]

    def perform_create(self, serializer):
        values = dict(serializer.validated_data)
        first_admin = values.pop("first_admin")
        shop, user, password = create_shop_with_first_admin(
            actor=self.request.user,
            shop_data=values,
            first_admin_data=first_admin,
        )
        self._created_shop = shop
        self._created_first_admin = user
        self._initial_password = password

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = TenantAdminSerializer(self._created_shop).data
        data["first_admin_user_code"] = self._created_first_admin.user_code
        data["initial_password"] = self._initial_password
        response = Response(data, status=status.HTTP_201_CREATED)
        response["Cache-Control"] = "no-store"
        response["Pragma"] = "no-cache"
        return response

    def perform_update(self, serializer):
        serializer.instance = update_shop(
            actor=self.request.user,
            shop_id=serializer.instance.pk,
            changes=serializer.validated_data,
        )

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        shop = set_shop_active(request.user, self.get_object().pk, active=True)
        return Response({"status": "Shop activated", "is_active": shop.is_active})

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        shop = set_shop_active(request.user, self.get_object().pk, active=False)
        return Response({"status": "Shop deactivated", "is_active": shop.is_active})

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        shop = self.get_object()
        if not self._is_main_supplier():
            membership = ShopRolePolicy.get_active_membership(request.user, shop.pk)
            if (
                not shop.is_active
                or membership is None
                or membership.role != ShopRole.ADMIN
            ):
                raise PermissionDenied("Shop management statistics are unavailable.")
        return Response(
            {
                "user_count": shop._user_count,
                "max_users": shop.max_users,
                "is_at_user_limit": shop._user_count >= shop.max_users,
            }
        )

    @action(detail=True, methods=["get"], url_path="member-lookup")
    def member_lookup(self, request, pk=None):
        shop = self.get_object()
        if not self._is_main_supplier():
            membership = ShopRolePolicy.get_active_membership(request.user, shop.pk)
            if (
                not shop.is_active
                or membership is None
                or membership.role != ShopRole.ADMIN
            ):
                raise PermissionDenied("Shop membership management is unavailable.")

        user_code = request.query_params.get("user_code", "").strip().upper()
        if not user_code:
            raise ValidationError({"user_code": "This query parameter is required."})
        membership = (
            TenantMember.objects.all_with_deleted()
            .select_related("user")
            .filter(tenant_id=shop.pk, user__user_code=user_code)
            .first()
        )
        if membership is None:
            raise NotFound()
        user = membership.user
        display_name = " ".join(
            part for part in (user.first_name.strip(), user.last_name.strip()) if part
        )
        result = {
            "user_code": user.user_code,
            "display_name": display_name,
            "role": membership.role,
            "membership_status": (
                "REMOVED"
                if membership.deleted
                else (
                    "ACTIVE"
                    if membership.is_active and user.is_active and shop.is_active
                    else "INACTIVE"
                )
            ),
        }
        return Response(MemberLookupSerializer(result).data)
