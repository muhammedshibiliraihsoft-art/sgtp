from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from ..models import TenantMember
from ..serializers import TenantMemberSerializer

class TenantMemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Shop (Tenant) Memberships.
    """
    queryset = TenantMember.objects.select_related('user', 'tenant').all()
    serializer_class = TenantMemberSerializer
    permission_classes = [permissions.IsAdminUser]  # Basic security: only admins can manage for now
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['tenant', 'user', 'role', 'is_active']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
