from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from ..models import TenantMember
from ..serializers.membership import TenantMemberSerializer
from ..permissions import CanManageShopMembership
from ..policy import ShopRolePolicy

class TenantMemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Shop (Tenant) Memberships.
    """
    queryset = TenantMember.objects.none()
    serializer_class = TenantMemberSerializer
    permission_classes = [CanManageShopMembership]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['tenant', 'user', 'role', 'is_active']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated or not user.is_active:
            return TenantMember.objects.none()
            
        if ShopRolePolicy.is_main_supplier_admin(user):
            return TenantMember.objects.select_related('user', 'tenant').all()
            
        # Normal shop admins only see memberships for shops where they are ADMIN
        return TenantMember.objects.select_related('user', 'tenant').filter(
            tenant__memberships__user=user,
            tenant__memberships__role='ADMIN',
            tenant__memberships__is_active=True,
            tenant__memberships__deleted__isnull=True
        ).distinct()

    def perform_create(self, serializer):
        tenant = serializer.validated_data.get('tenant')
        if not ShopRolePolicy.can_manage_memberships(self.request.user, tenant.id):
            raise PermissionDenied("You do not have permission to manage memberships for this Shop.")
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
