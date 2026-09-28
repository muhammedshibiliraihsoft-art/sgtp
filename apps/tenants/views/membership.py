from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.utils import timezone
from datetime import timedelta
from django.db import IntegrityError

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
        from django.db import transaction
        tenant_id = serializer.validated_data.get('tenant').id

        with transaction.atomic():
            from ..models import Tenant
            # Lock the tenant row to prevent capacity race conditions
            tenant = Tenant.objects.select_for_update().get(pk=tenant_id)

            if not ShopRolePolicy.can_manage_memberships(self.request.user, tenant.id):
                raise PermissionDenied("You do not have permission to manage memberships for this Shop.")

            if tenant.is_at_user_limit:
                raise ValidationError({"tenant": "Shop has reached its maximum user limit."})

            serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        from django.db import transaction
        if instance.is_active:
            raise ValidationError({"detail": "Cannot remove an active membership. Deactivate it first."})

        with transaction.atomic():
            from ..models import Tenant
            # Lock the tenant row to serialize capacity-changing operations
            tenant = Tenant.objects.select_for_update().get(pk=instance.tenant_id)
            instance.delete()


    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        membership = self.get_object()
        if not membership.is_active:
            return Response({"detail": "Membership is already inactive."}, status=status.HTTP_400_BAD_REQUEST)
        membership.is_active = False
        membership.save(update_fields=['is_active'])
        return Response({"detail": "Membership deactivated.", "status": "INACTIVE"})

    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        from django.db import transaction
        membership = self.get_object()
        if membership.is_active:
            return Response({"detail": "Membership is already active."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            from ..models import Tenant
            # Lock the tenant row to align with the authoritative capacity model
            tenant = Tenant.objects.select_for_update().get(pk=membership.tenant_id)

            if tenant.is_at_user_limit:
                return Response({"detail": "Shop has reached its maximum user limit."}, status=status.HTTP_400_BAD_REQUEST)

            membership.is_active = True
            membership.save(update_fields=['is_active'])

        return Response({"detail": "Membership reactivated.", "status": "ACTIVE"})

    @action(detail=True, methods=['post'])
    def undo_remove(self, request, pk=None):
        from django.db import transaction

        try:
            membership = TenantMember.objects.all_with_deleted().get(pk=pk)
        except TenantMember.DoesNotExist:
            raise NotFound()

        # Manually check permissions since we bypassed get_object()
        self.check_object_permissions(request, membership)

        if not membership.deleted:
            return Response({"detail": "Membership is not removed."}, status=status.HTTP_400_BAD_REQUEST)

        if timezone.now() - membership.deleted > timedelta(seconds=5):
            return Response({"detail": "Undo window expired."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            from ..models import Tenant
            # Lock the tenant row to prevent capacity race conditions during restoration
            tenant = Tenant.objects.select_for_update().get(pk=membership.tenant_id)

            if tenant.is_at_user_limit:
                return Response({"detail": "Shop has reached its maximum user limit. Cannot restore."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                membership.undelete()
            except IntegrityError:
                return Response({"detail": "Cannot restore: a membership for this user already exists in this Shop."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Membership restored to previous state.", "status": "INACTIVE" if not membership.is_active else "ACTIVE"})
