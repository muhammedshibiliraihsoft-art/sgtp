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
    Must be implemented to validate user-shop membership.
    Currently returns False (secure-by-default) until Phase 3 implementation.
    """
    def has_permission(self, request, view):
        return False
        
    def has_object_permission(self, request, view, obj):
        return False

class DenyAll(BasePermission):
    """
    Explicit denial primitive.
    """
    def has_permission(self, request, view):
        return False
        
    def has_object_permission(self, request, view, obj):
        return False
