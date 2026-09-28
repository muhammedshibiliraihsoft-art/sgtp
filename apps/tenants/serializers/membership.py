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
        Prevent changing user or tenant on update.
        """
        if self.instance:
            if 'user' in data and data['user'] != self.instance.user:
                raise serializers.ValidationError({"user": "Cannot change the user of an existing membership."})
            if 'tenant' in data and data['tenant'] != self.instance.tenant:
                raise serializers.ValidationError({"tenant": "Cannot change the shop of an existing membership."})
                
        user = data.get('user') or (self.instance.user if self.instance else None)
        tenant = data.get('tenant') or (self.instance.tenant if self.instance else None)

        if user and not user.is_active:
            raise serializers.ValidationError({"user": "Cannot assign an inactive user."})
        if tenant and not tenant.is_active:
            raise serializers.ValidationError({"tenant": "Cannot assign to an inactive shop."})

        # Check for duplicates on create
        if not self.instance and user and tenant:
            if TenantMember.objects.filter(user=user, tenant=tenant, deleted__isnull=True).exists():
                raise serializers.ValidationError("This user is already a member of the shop.")

        return data
