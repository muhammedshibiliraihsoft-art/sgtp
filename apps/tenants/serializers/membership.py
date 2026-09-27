from rest_framework import serializers
from ..models import TenantMember

class TenantMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')
    tenant_name = serializers.ReadOnlyField(source='tenant.name')

    class Meta:
        model = TenantMember
        fields = [
            'id', 'tenant', 'tenant_name', 'user', 'user_email',
            'role', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """
        Ensure user and tenant are active upon membership creation/update.
        """
        user = data.get('user') or (self.instance.user if self.instance else None)
        tenant = data.get('tenant') or (self.instance.tenant if self.instance else None)

        if user and not user.is_active:
            raise serializers.ValidationError({"user": "Cannot assign an inactive user."})
        if tenant and not tenant.is_active:
            raise serializers.ValidationError({"tenant": "Cannot assign to an inactive shop."})

        return data
