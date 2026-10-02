from rest_framework import serializers
from ..models import Tenant
from .membership import TenantMemberSerializer


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "slug",
            "domain",
            "is_active",
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
        read_only_fields = ["id", "supplier", "is_active", "created_at", "updated_at"]

    def validate_slug(self, value):
        """Ensure slug is lowercase and valid."""
        if value != value.lower():
            raise serializers.ValidationError("Slug must be lowercase.")
        return value


class TenantAdminSerializer(TenantSerializer):
    """Full Shop management representation for Main Supplier only."""

    max_users = serializers.IntegerField()
    user_count = serializers.SerializerMethodField()
    is_at_user_limit = serializers.SerializerMethodField()

    def to_internal_value(self, data):
        blocked = {"supplier", "user_count", "is_at_user_limit"}
        if not isinstance(self, TenantCreateSerializer):
            blocked.add("is_active")
        submitted = blocked.intersection(data)
        if submitted:
            raise serializers.ValidationError(
                {
                    field: "Use the dedicated Shop management action."
                    for field in submitted
                }
            )
        return super().to_internal_value(data)

    class Meta(TenantSerializer.Meta):
        fields = TenantSerializer.Meta.fields + [
            "max_users",
            "user_count",
            "is_at_user_limit",
            "default_locale",
            "default_timezone",
            "default_currency",
        ]

    def get_user_count(self, obj):
        return obj._user_count if hasattr(obj, "_user_count") else obj.user_count

    def get_is_at_user_limit(self, obj):
        count = obj._user_count if hasattr(obj, "_user_count") else obj.user_count
        return count >= obj.max_users


class TenantMemberProfileSerializer(serializers.ModelSerializer):
    """Minimal profile visible to a member of that Shop."""

    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "is_active",
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
        read_only_fields = fields

    def get_is_active(self, obj):
        if hasattr(obj, "_actor_has_active_membership"):
            return obj.is_active and obj._actor_has_active_membership
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        from ..models import TenantMember

        return (
            obj.is_active
            and TenantMember.objects.filter(
                tenant_id=obj.pk,
                user_id=request.user.pk,
                is_active=True,
                deleted__isnull=True,
                user__is_active=True,
            ).exists()
        )


class TenantAdminManagementSerializer(TenantMemberProfileSerializer):
    """Shop ADMIN profile plus same-Shop management statistics; no settings."""

    max_users = serializers.IntegerField(read_only=True)
    user_count = serializers.SerializerMethodField()
    is_at_user_limit = serializers.SerializerMethodField()

    class Meta(TenantMemberProfileSerializer.Meta):
        fields = TenantMemberProfileSerializer.Meta.fields + [
            "max_users",
            "user_count",
            "is_at_user_limit",
        ]

    def get_user_count(self, obj):
        return obj._user_count if hasattr(obj, "_user_count") else obj.user_count

    def get_is_at_user_limit(self, obj):
        count = obj._user_count if hasattr(obj, "_user_count") else obj.user_count
        return count >= obj.max_users


class FirstShopAdminSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True, allow_blank=False, max_length=30)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=30)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=True, allow_blank=False)

    def validate_phone(self, value):
        """Reject invalid phone numbers as request validation, not server errors."""
        from apps.accounts.phone_numbers import InvalidUserPhone, normalize_user_phone

        try:
            normalized = normalize_user_phone(value)
        except InvalidUserPhone as exc:
            raise serializers.ValidationError(str(exc)) from exc
        if not normalized:
            raise serializers.ValidationError("Enter an international phone number with country code.")
        return normalized

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
    """Small list representation for an authorized ordinary member."""

    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = ["id", "name", "is_active"]

    def get_is_active(self, obj):
        return TenantMemberProfileSerializer(context=self.context).get_is_active(obj)


class TenantAdminSummarySerializer(TenantSummarySerializer):
    max_users = serializers.IntegerField(read_only=True)
    user_count = serializers.SerializerMethodField()
    is_at_user_limit = serializers.SerializerMethodField()

    class Meta(TenantSummarySerializer.Meta):
        fields = TenantSummarySerializer.Meta.fields + [
            "max_users",
            "user_count",
            "is_at_user_limit",
            "default_locale",
            "default_timezone",
            "default_currency",
        ]

    def get_is_active(self, obj):
        return obj.is_active

    def get_user_count(self, obj):
        return obj._user_count if hasattr(obj, "_user_count") else obj.user_count

    def get_is_at_user_limit(self, obj):
        count = obj._user_count if hasattr(obj, "_user_count") else obj.user_count
        return count >= obj.max_users
