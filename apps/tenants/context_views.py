"""Reusable DRF contract for endpoints that require an explicit Shop URL."""

from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

from apps.accounts.permissions import PasswordChangeGate
from apps.tenants.context import resolve_shop_context
from apps.tenants.models import ShopRole


class ShopContextMixin:
    """Resolve and attach Shop context after DRF authentication, before permissions."""

    shop_context_url_kwarg = "shop_id"

    def perform_authentication(self, request):
        super().perform_authentication(request)

        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            raise NotAuthenticated()

        password_gate = PasswordChangeGate()
        if not password_gate.has_permission(request, self):
            raise PermissionDenied(
                detail=password_gate.message,
                code=password_gate.code,
            )

        shop_id = self.kwargs.get(self.shop_context_url_kwarg)
        context = resolve_shop_context(user, shop_id)
        request.shop_context = context
        # Transitional compatibility for B2-03 callers; always derived from
        # the canonical resolved object and never read as an input selector.
        request.tenant_id = context.shop.pk


class ShopContextView(ShopContextMixin, APIView):
    """Small authenticated endpoint proving the selected request context."""

    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(
        responses=inline_serializer(
            name="ShopRequestContext",
            fields={
                "shop_id": serializers.UUIDField(),
                "role": serializers.ChoiceField(
                    choices=ShopRole.choices, allow_null=True
                ),
                "is_main_supplier": serializers.BooleanField(),
            },
        ),
    )
    def get(self, request, shop_id):
        context = request.shop_context
        return Response(
            {
                "shop_id": str(context.shop.pk),
                "role": context.role,
                "is_main_supplier": context.is_main_supplier,
            }
        )
