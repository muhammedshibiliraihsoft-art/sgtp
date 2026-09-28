from rest_framework.permissions import BasePermission
from apps.tenants.policy import ShopRolePolicy


class IsMainSupplierAdmin(BasePermission):
    """Allow Shop administration only to the approved Main Supplier authority."""

    def has_permission(self, request, view):
        return ShopRolePolicy.is_main_supplier_admin(request.user)

class CanManageShopMembership(BasePermission):
    """
    Permission to manage memberships. 
    Main Supplier Admins can manage any membership.
    Shop Admins can only manage memberships within their authorized shops.
    """
    
    def has_permission(self, request, view):
        # Allow if authenticated; scoping is handled by get_queryset() for LIST
        # For CREATE, we validate the target tenant in serializer or view.
        if not request.user or not request.user.is_authenticated or not request.user.is_active:
            return False
            
        # We allow authenticated users to hit the view, but get_queryset will scope
        # and has_object_permission will check individual objects.
        # For creation, they must be able to manage the specific tenant.
        # This is handled dynamically in the view or serializer.
        return True

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated or not request.user.is_active:
            return False
        
        # obj is a TenantMember instance
        # Ensure the user has membership-management rights over the target membership's shop
        return ShopRolePolicy.can_manage_memberships(request.user, obj.tenant_id)
