from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.permissions import PasswordChangeGate
from apps.tenants.policy import ShopRolePolicy


class ClientAccessPermission(BasePermission):
    """Apply the approved Client access matrix after trusted Shop resolution."""

    def has_permission(self, request, view):
        if not PasswordChangeGate().has_permission(request, view):
            return False
        context = getattr(request, "shop_context", None)
        if not context or not context.shop:
            return False
        if ShopRolePolicy.is_main_supplier_admin(request.user):
            return True
        membership = context.membership
        if not membership or not membership.is_active:
            return False
        method = request.method.upper()
        if method in SAFE_METHODS:
            return True
        if method in {"POST", "PUT", "PATCH"}:
            return membership.role in {"ADMIN", "STAFF"}
        if method == "DELETE":
            return membership.role == "ADMIN"
        return False
