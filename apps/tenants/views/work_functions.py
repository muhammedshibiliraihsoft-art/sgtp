from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import PasswordChangeGate
from apps.tenants.context_views import ShopContextMixin
from apps.tenants.models import WorkFunctionCode
from apps.tenants.serializers.work_functions import (
    MembershipWorkFunctionSetSerializer,
)
from apps.tenants.services import work_functions as work_function_service


WorkFunctionSetResponseSerializer = inline_serializer(
    name="MembershipWorkFunctionSetResponse",
    fields={
        "membership_id": serializers.UUIDField(read_only=True),
        "shop_id": serializers.UUIDField(read_only=True),
        "functions": serializers.ListField(
            child=serializers.ChoiceField(choices=WorkFunctionCode.choices),
            read_only=True,
        ),
    },
)


class MembershipWorkFunctionView(ShopContextMixin, APIView):
    """Read/replace the current Work-Function set for one Shop membership."""

    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(responses=WorkFunctionSetResponseSerializer)
    def get(self, request, shop_id, membership_id):
        membership, functions = work_function_service.get_membership_work_functions(
            actor=request.user,
            shop_id=request.shop_context.shop.pk,
            membership_id=membership_id,
        )
        return Response(
            {
                "membership_id": membership.pk,
                "shop_id": request.shop_context.shop.pk,
                "functions": functions,
            }
        )

    @extend_schema(
        request=MembershipWorkFunctionSetSerializer,
        responses={status.HTTP_200_OK: WorkFunctionSetResponseSerializer},
    )
    def put(self, request, shop_id, membership_id):
        serializer = MembershipWorkFunctionSetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership, functions = work_function_service.set_membership_work_functions(
            actor=request.user,
            shop_id=request.shop_context.shop.pk,
            membership_id=membership_id,
            function_codes=serializer.validated_data["functions"],
        )
        return Response(
            {
                "membership_id": membership.pk,
                "shop_id": request.shop_context.shop.pk,
                "functions": functions,
            }
        )
