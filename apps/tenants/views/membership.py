from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.utils import timezone
from datetime import timedelta
from django.db import IntegrityError

from ..models import TenantMember, ShopRole
from ..serializers.membership import TenantMemberSerializer
from ..permissions import CanManageShopMembership
from ..policy import ShopRolePolicy
from ..services import membership as membership_service

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
        tenant_id = serializer.validated_data.get('tenant').id
        user_id = serializer.validated_data.get('user').id
        role = serializer.validated_data.get('role', ShopRole.VIEWER)

        membership = membership_service.create_membership(
            actor=self.request.user,
            tenant_id=tenant_id,
            user_id=user_id,
            role=role
        )
        serializer.instance = membership

    def perform_update(self, serializer):
        if 'role' in serializer.validated_data:
            new_role = serializer.validated_data.get('role')
            membership = membership_service.change_membership_role(
                actor=self.request.user,
                membership_id=serializer.instance.pk,
                new_role=new_role
            )
            serializer.instance = membership

    def perform_destroy(self, instance):
        membership_service.remove_membership(
            actor=self.request.user,
            membership_id=instance.pk
        )

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        membership = membership_service.deactivate_membership(
            actor=self.request.user,
            membership_id=pk
        )
        return Response({"detail": "Membership deactivated.", "status": "INACTIVE"})

    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        membership = membership_service.reactivate_membership(
            actor=self.request.user,
            membership_id=pk
        )
        return Response({"detail": "Membership reactivated.", "status": "ACTIVE"})

    @action(detail=True, methods=['post'])
    def undo_remove(self, request, pk=None):
        membership = membership_service.undo_remove_membership(
            actor=self.request.user,
            membership_id=pk
        )
        return Response(
            {"detail": "Membership restored to previous state.", "status": "INACTIVE" if not membership.is_active else "ACTIVE"}
        )
