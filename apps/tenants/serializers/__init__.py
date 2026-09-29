from rest_framework import serializers
from ..models import Tenant
from .membership import TenantMemberSerializer


class TenantSerializer(serializers.ModelSerializer):
    user_count = serializers.ReadOnlyField()
    is_at_user_limit = serializers.ReadOnlyField()

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "slug",
            "domain",
            "is_active",
            "max_users",
            "user_count",
            "is_at_user_limit",
            "contact_email",
            "contact_phone",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_slug(self, value):
        """Ensure slug is lowercase and valid."""
        if value != value.lower():
            raise serializers.ValidationError("Slug must be lowercase.")
        return value


class TenantAdminSerializer(TenantSerializer):
    """Shop settings are serialized only on Main Supplier Admin paths."""

    class Meta(TenantSerializer.Meta):
        fields = TenantSerializer.Meta.fields + [
            "default_locale",
            "default_timezone",
            "default_currency",
        ]


class FirstShopAdminSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True, allow_blank=False, max_length=30)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=30)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=True, allow_blank=False)

    def to_internal_value(self, data):
        if "is_active" in data or "owning_shop" in data or "shop" in data:
            raise serializers.ValidationError(
                {"detail": "Account state and Shop ownership are server-controlled."}
            )
        return super().to_internal_value(data)


class TenantCreateSerializer(TenantAdminSerializer):
    """Serializer for creating tenants with required fields."""

    first_admin = FirstShopAdminSerializer(write_only=True, required=True)
    is_active = serializers.BooleanField(required=False, default=True)

    class Meta(TenantAdminSerializer.Meta):
        fields = TenantAdminSerializer.Meta.fields + ["first_admin"]
        extra_kwargs = {
            "name": {"required": True},
            "slug": {"required": True},
        }


class TenantSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for tenant lists and references."""

    user_count = serializers.ReadOnlyField()

    class Meta:
        model = Tenant
        fields = ["id", "name", "slug", "is_active", "user_count"]


class TenantAdminSummarySerializer(TenantSummarySerializer):
    class Meta(TenantSummarySerializer.Meta):
        fields = TenantSummarySerializer.Meta.fields + [
            "default_locale",
            "default_timezone",
            "default_currency",
        ]
