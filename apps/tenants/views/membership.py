from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from ..models import TenantMember
from ..permissions import CanManageShopMembership
from ..policy import ShopRolePolicy
from ..serializers.membership import TenantMemberSerializer
from ..services import membership as membership_service


class TenantMemberViewSet(viewsets.ModelViewSet):
    """Manage Shop memberships through the transactional domain service."""

    queryset = TenantMember.objects.none()
    serializer_class = TenantMemberSerializer
    permission_classes = [CanManageShopMembership]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["tenant", "user", "role", "is_active"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated or not user.is_active:
            return TenantMember.objects.none()
        if ShopRolePolicy.is_main_supplier_admin(user):
            return TenantMember.objects.select_related("user", "tenant").all()
        return (
            TenantMember.objects.select_related("user", "tenant")
            .filter(
                tenant__memberships__user=user,
                tenant__memberships__role="ADMIN",
                tenant__memberships__is_active=True,
                tenant__memberships__deleted__isnull=True,
            )
            .distinct()
        )

    def perform_create(self, serializer):
        serializer.instance = membership_service.create_membership(
            actor=self.request.user,
            shop_id=serializer.validated_data["tenant"].pk,
            user_id=serializer.validated_data["user"].pk,
            role=serializer.validated_data.get("role", "STAFF"),
        )

    def perform_update(self, serializer):
        if "role" in serializer.validated_data:
            role = serializer.validated_data.pop("role")
            serializer.instance = membership_service.change_membership_role(
                actor=self.request.user,
                membership_id=serializer.instance.pk,
                new_role=role,
            )
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        membership_service.remove_membership(
            actor=self.request.user, membership_id=instance.pk
        )

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        membership_service.deactivate_membership(actor=request.user, membership_id=pk)
        return Response({"detail": "Membership deactivated.", "status": "INACTIVE"})

    @action(detail=True, methods=["post"])
    def reactivate(self, request, pk=None):
        membership_service.reactivate_membership(actor=request.user, membership_id=pk)
        return Response({"detail": "Membership reactivated.", "status": "ACTIVE"})

    @action(detail=True, methods=["post"])
    def undo_remove(self, request, pk=None):
        try:
            membership = TenantMember.objects.all_with_deleted().get(pk=pk)
        except TenantMember.DoesNotExist as exc:
            raise NotFound() from exc
        self.check_object_permissions(request, membership)
        membership = membership_service.undo_remove_membership(
            actor=request.user, membership_id=pk
        )
        return Response(
            {
                "detail": "Membership restored to previous state.",
                "status": "ACTIVE" if membership.is_active else "INACTIVE",
            },
            status=status.HTTP_200_OK,
        )
