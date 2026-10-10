from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from rest_framework import serializers

from apps.accounts.permissions import PasswordChangeGate
from apps.accounts.serializers import ShopUserCreateSerializer, UserAdminSerializer
from apps.tenants.context import resolve_shop_context


class ShopUserCreatedSerializer(UserAdminSerializer):
    initial_password = serializers.CharField(required=False, allow_null=True)

    class Meta(UserAdminSerializer.Meta):
        fields = UserAdminSerializer.Meta.fields + ("initial_password",)


class ShopUserCreateView(APIView):
    """Create a Shop account using the URL-resolved Shop as trusted context."""

    permission_classes = [IsAuthenticated, PasswordChangeGate]

    @extend_schema(
        request=ShopUserCreateSerializer,
        responses={201: ShopUserCreatedSerializer},
    )
    def post(self, request, shop_id):
        shop_context = resolve_shop_context(request.user, shop_id)
        serializer = ShopUserCreateSerializer(
            data=request.data,
            context={"request": request, "shop_context": shop_context},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = UserAdminSerializer(user).data
        if serializer.initial_password:
            data["initial_password"] = serializer.initial_password
        response = Response(data, status=status.HTTP_201_CREATED)
        response["Cache-Control"] = "no-store"
        response["Pragma"] = "no-cache"
        return response
