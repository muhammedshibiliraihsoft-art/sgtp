from django.contrib.auth import get_user_model
from rest_framework import serializers
from ..models import TenantMember

User = get_user_model()


class TenantMemberSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, required=True
    )
    user_code = serializers.CharField(source="user.user_code", read_only=True)
    display_name = serializers.SerializerMethodField()
    user_email = serializers.ReadOnlyField(source="user.email")
    tenant_name = serializers.ReadOnlyField(source="tenant.name")

    class Meta:
        model = TenantMember
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "user",
            "user_code",
            "display_name",
            "user_email",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_active"]

    def get_display_name(self, obj):
        return " ".join(
            part
            for part in (obj.user.first_name.strip(), obj.user.last_name.strip())
            if part
        )

    def validate(self, data):
        """Membership identity is immutable after creation."""
        if self.instance:
            if "user" in data and data["user"] != self.instance.user:
                raise serializers.ValidationError(
                    {"user": ["Cannot change the user of an existing membership."]}
                )
            if "tenant" in data and data["tenant"] != self.instance.tenant:
                raise serializers.ValidationError(
                    {"tenant": ["Cannot change the Shop of an existing membership."]}
                )
        if self.instance:
            return data

        user = data.get("user")
        tenant = data.get("tenant")

        if user and not user.is_active:
            raise serializers.ValidationError(
                {"user": ["Cannot assign an inactive User."]}
            )
        # Check for duplicates on create
        if not self.instance and user and tenant:
            if TenantMember.objects.filter(
                user=user, tenant=tenant, deleted__isnull=True
            ).exists():
                raise serializers.ValidationError(
                    {"user": ["This user is already a member of the Shop."]}
                )

        return data
