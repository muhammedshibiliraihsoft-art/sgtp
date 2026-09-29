from rest_framework import serializers
from ..models import Tenant


class TenantSerializer(serializers.ModelSerializer):
    user_count = serializers.ReadOnlyField()
    is_at_user_limit = serializers.ReadOnlyField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'domain', 'is_active',
            'max_users', 'user_count', 'is_at_user_limit',
            'contact_email', 'contact_phone',
            'address_line1', 'address_line2', 'city', 'state',
            'postal_code', 'country', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_slug(self, value):
        """Ensure slug is lowercase and valid."""
        if value != value.lower():
            raise serializers.ValidationError("Slug must be lowercase.")
        return value


class TenantAdminSerializer(TenantSerializer):
    """Shop settings are serialized only on Main Supplier Admin paths."""

    class Meta(TenantSerializer.Meta):
        fields = TenantSerializer.Meta.fields + [
            'default_locale', 'default_timezone', 'default_currency'
        ]


class TenantCreateSerializer(TenantAdminSerializer):
    """Serializer for creating tenants with required fields."""
    from apps.accounts.models import User
    first_admin_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )

    class Meta(TenantAdminSerializer.Meta):
        fields = TenantAdminSerializer.Meta.fields + ['first_admin_user']
        extra_kwargs = {
            'name': {'required': True},
            'slug': {'required': True},
        }


class TenantSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for tenant lists and references."""
    user_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'slug', 'is_active', 'user_count']


class TenantAdminSummarySerializer(TenantSummarySerializer):
    class Meta(TenantSummarySerializer.Meta):
        fields = TenantSummarySerializer.Meta.fields + [
            'default_locale', 'default_timezone', 'default_currency'
        ]
from .membership import TenantMemberSerializer
