from typing import Any
from django.contrib.auth import get_user_model

User = get_user_model()


class ShopRolePolicy:
    """
    Explicit Role Policy for the SGTP V1 Shop Workspace.

    This policy formally defines the relationship between the Main Supplier Admin
    and individual Shop workspaces, as well as the roles within a Shop.

    1. Main Supplier Authority:
       A user with `is_superuser=True` (Main Supplier Admin) has explicit cross-Shop
       authority. They do not require a TenantMember record to manage or view Shops.

    2. Shop Roles:
       Users assigned to a Shop via `TenantMember` receive one of three roles:
       - ADMIN: Can manage permitted same-Shop non-ADMIN memberships and accounts.
       - STAFF: Standard operational access to shop records (clients, measurements, etc.).
       - VIEWER: Read-only access to shop records.
       Shop configuration/settings and lifecycle remain Main Supplier-only.

    3. External Suppliers:
       External suppliers are business records owned by a Shop. They are NOT users,
       cannot authenticate, and hold no roles or permissions in the system.
    """

    @staticmethod
    def is_main_supplier_admin(user: Any) -> bool:
        """
        Resolve Main Supplier authority from current persisted User state.
        """
        if not user or not user.is_authenticated or not user.is_active:
            return False
        user_id = getattr(user, "pk", None)
        if not user_id:
            return False
        return User.objects.filter(
            pk=user_id, is_active=True, is_superuser=True
        ).exists()

    @staticmethod
    def is_shop_member(user: Any, tenant_id: Any) -> bool:
        """
        Check if a user is an active member of an active shop.
        Main Supplier Admins are considered authorized for all shops.
        """
        if ShopRolePolicy.is_main_supplier_admin(user):
            return True

        if not user or not user.is_authenticated or not user.is_active:
            return False

        return ShopRolePolicy.get_active_membership(user, tenant_id) is not None

    @staticmethod
    def get_active_membership(user: Any, tenant_id: Any):
        """Return the selected Shop membership used to authorize request context."""
        if not user or not user.is_authenticated or not user.is_active:
            return None
        if not User.objects.filter(
            pk=getattr(user, "pk", None), is_active=True
        ).exists():
            return None

        from apps.tenants.models import TenantMember

        return TenantMember.objects.filter(
            user=user,
            user__is_active=True,
            tenant_id=tenant_id,
            is_active=True,
            tenant__is_active=True,
            deleted__isnull=True,
        ).first()

    @staticmethod
    def can_manage_memberships(user: Any, tenant_id: Any) -> bool:
        """
        Check if a user can manage memberships for a specific shop.
        Main Supplier Admins can manage memberships for all shops.
        Shop ADMINs can manage memberships for their authorized shop.
        """
        if ShopRolePolicy.is_main_supplier_admin(user):
            return True

        if not user or not user.is_authenticated or not user.is_active:
            return False

        membership = ShopRolePolicy.get_active_membership(user, tenant_id)
        return membership is not None and membership.role == "ADMIN"
