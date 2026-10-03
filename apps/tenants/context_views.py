"""Reusable DRF contract for endpoints that require an explicit Shop URL."""

from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

from apps.accounts.permissions import PasswordChangeGate
from apps.tenants.context import resolve_shop_context
from apps.tenants.models import MembershipWorkFunction, ShopRole, WorkFunctionCode


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
                "work_functions": serializers.ListField(
                    child=serializers.ChoiceField(choices=WorkFunctionCode.choices)
                ),
            },
        ),
    )
    def get(self, request, shop_id):
        context = request.shop_context
        work_functions = []
        if context.membership is not None:
            assigned = set(
                MembershipWorkFunction.objects.filter(
                    membership=context.membership,
                    deleted__isnull=True,
                ).values_list("function_code", flat=True)
            )
            work_functions = [
                code for code, _label in WorkFunctionCode.choices if code in assigned
            ]
        return Response(
            {
                "shop_id": str(context.shop.pk),
                "role": context.role,
                "is_main_supplier": context.is_main_supplier,
                "work_functions": work_functions,
            }
        )
