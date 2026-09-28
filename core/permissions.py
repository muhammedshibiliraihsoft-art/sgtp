from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Object-level permission to only allow owners of an object to access it.
    Assumes the model instance has an `owner_id` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Allow access if the object's owner matches the requesting user.
        return getattr(obj, "owner_id", None) == request.user.id


class IsTenantMember(BasePermission):
    """
    Requires the authorized T3-03 request context for Shop entry.
    Endpoint action/object rules remain separate from context establishment.
    """

    def has_permission(self, request, view):
        from apps.tenants.policy import ShopRolePolicy
        from apps.accounts.permissions import PasswordChangeGate

        user = getattr(request, "user", None)
        context = getattr(request, "shop_context", None)
        if not context or not getattr(context, "shop", None):
            return False

        if not PasswordChangeGate().has_permission(request, view):
            return False
        if not user or not user.is_authenticated or not user.is_active:
            return False
        if context.actor_user_id != user.pk:
            return False
        if context.shop.pk != getattr(request, "tenant_id", None):
            return False
        if ShopRolePolicy.is_main_supplier_admin(user):
            return context.is_main_supplier and context.membership is None

        membership = context.membership
        return bool(
            membership
            and membership.user_id == user.pk
            and membership.tenant_id == context.shop.pk
            and membership.is_active
            and membership.deleted is None
            and not context.is_main_supplier
        )

    def has_object_permission(self, request, view, obj):
        from apps.tenants.policy import ShopRolePolicy

        user = getattr(request, "user", None)
        if ShopRolePolicy.is_main_supplier_admin(user):
            return True

        # If the object is a tenant, check membership against its ID
        tenant_id = getattr(obj, "tenant_id", None)
        if tenant_id is None:
            # Maybe the object IS the tenant itself
            if hasattr(obj, "supplier") and hasattr(obj, "domain"):
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
