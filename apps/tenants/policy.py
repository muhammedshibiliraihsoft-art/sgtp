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
       - ADMIN: Can manage shop settings and other memberships.
       - STAFF: Standard operational access to shop records (clients, measurements, etc.).
       - VIEWER: Read-only access to shop records.
       
    3. External Suppliers:
       External suppliers are business records owned by a Shop. They are NOT users,
       cannot authenticate, and hold no roles or permissions in the system.
    """

    @staticmethod
    def is_main_supplier_admin(user: Any) -> bool:
        """
        Main Supplier Admins implicitly have cross-shop authority.
        In V1, this is mapped to the Django superuser flag.
        """
        if not user or not user.is_authenticated:
            return False
        return getattr(user, 'is_superuser', False)

    @staticmethod
    def is_shop_member(user: Any, tenant_id: Any) -> bool:
        """
        Check if a user is an active member of an active shop.
        Main Supplier Admins are considered authorized for all shops.
        """
        if ShopRolePolicy.is_main_supplier_admin(user):
            return True
            
        if not user or not user.is_authenticated:
            return False
            
        from apps.tenants.models import TenantMember
        return TenantMember.objects.filter(
            user=user, 
            tenant_id=tenant_id, 
            is_active=True,
            tenant__is_active=True
        ).exists()
