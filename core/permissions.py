from rest_framework.permissions import BasePermission

class IsOwner(BasePermission):
    """
    Object-level permission to only allow owners of an object to access it.
    Assumes the model instance has an `owner_id` attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Allow access if the object's owner matches the requesting user.
        return getattr(obj, 'owner_id', None) == request.user.id

class IsTenantMember(BasePermission):
    """
    Contract interface for Phase 3 tenant membership validation.
    Validates user-shop membership using the explicit ShopRolePolicy.
    """
    def has_permission(self, request, view):
        # The view must establish the tenant context first (T3-03)
        # For now, if there's no tenant context attached, we fail securely unless they are a main admin.
        from apps.tenants.policy import ShopRolePolicy
        user = getattr(request, 'user', None)
        if ShopRolePolicy.is_main_supplier_admin(user):
            return True
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            return False
        return ShopRolePolicy.is_shop_member(user, tenant_id)
        
    def has_object_permission(self, request, view, obj):
        from apps.tenants.policy import ShopRolePolicy
        user = getattr(request, 'user', None)
        if ShopRolePolicy.is_main_supplier_admin(user):
            return True
        
        # If the object is a tenant, check membership against its ID
        tenant_id = getattr(obj, 'tenant_id', None)
        if tenant_id is None:
            # Maybe the object IS the tenant itself
            if hasattr(obj, 'supplier') and hasattr(obj, 'domain'):
                tenant_id = obj.id
                
        if not tenant_id:
            return False
            
        return ShopRolePolicy.is_shop_member(user, tenant_id)

class DenyAll(BasePermission):
    """
    Explicit denial primitive.
    """
    def has_permission(self, request, view):
        return False
        
    def has_object_permission(self, request, view, obj):
        return False
