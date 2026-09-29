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
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_active']
