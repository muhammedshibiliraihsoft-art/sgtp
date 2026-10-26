from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from apps.tenants.models import MembershipWorkFunction, ShopRole, TenantMember


def has_financial_access(membership):
    if not membership or membership.deleted is not None or not membership.is_active:
        return False
    if membership.role == ShopRole.ADMIN:
        return True
    return bool(
        membership.role == ShopRole.STAFF
        and MembershipWorkFunction.objects.filter(
            membership=membership,
            function_code="CASHIER",
            deleted__isnull=True,
        ).exists()
    )


def require_financial_access(*, context, actor, lock=False):
    membership = context.membership
    if membership is None:
        raise PermissionDenied("Shop ADMIN or CASHIER STAFF access required.")
    queryset = TenantMember.objects
    if lock:
        queryset = queryset.select_for_update()
    membership = queryset.filter(
        pk=membership.pk,
        tenant=context.shop,
        user=actor,
        is_active=True,
        user__is_active=True,
        deleted__isnull=True,
    ).first()
    if not has_financial_access(membership):
        raise PermissionDenied("Shop ADMIN or CASHIER STAFF access required.")
    return membership


class IsShopFinancialUser(BasePermission):
    message = "Shop ADMIN or CASHIER STAFF access required."

    def has_permission(self, request, view):
        context = getattr(request, "shop_context", None)
        return bool(context and has_financial_access(context.membership))
