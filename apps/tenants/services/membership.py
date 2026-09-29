from typing import Any
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError, PermissionDenied

from apps.accounts.models import User
from apps.tenants.models import Tenant, TenantMember, ShopRole
from apps.tenants.policy import ShopRolePolicy


def validate_admin_grade_user(user: User):
    """Ensure the user meets ADMIN requirements."""
    if not user.is_active:
        raise ValidationError("ADMIN user must be active.")
    if not user.first_name or not user.first_name.strip():
        raise ValidationError("ADMIN user must have a valid first name.")
    if not user.email:
        raise ValidationError("ADMIN user must have an email.")
    if not getattr(user, 'phone', None):
        raise ValidationError("ADMIN user must have a valid phone number.")


def get_effective_admins(tenant_id):
    """Queryset of effective active ADMINs for a shop."""
    return TenantMember.objects.filter(
        tenant_id=tenant_id,
        role=ShopRole.ADMIN,
        is_active=True,
        deleted__isnull=True,
        user__is_active=True
    )


def count_effective_admins(tenant_id) -> int:
    """Count effective active ADMINs. Must be called under Shop lock for cardinality invariant."""
    return get_effective_admins(tenant_id).count()


def create_membership(actor: User, tenant_id, user_id, role: str) -> TenantMember:
    """Create a new membership, checking authority, capacity, and ADMIN cardinality."""
    with transaction.atomic():
        tenant = Tenant.objects.select_for_update().get(pk=tenant_id)
        
        # 1. Authority
        is_main_supplier = ShopRolePolicy.is_main_supplier_admin(actor)
        is_shop_admin = ShopRolePolicy.can_manage_memberships(actor, tenant_id)
        
        if not is_main_supplier and not is_shop_admin:
            raise PermissionDenied("You do not have permission to manage memberships for this Shop.")
        
        if role == ShopRole.ADMIN and not is_main_supplier:
            raise PermissionDenied("Only Main Supplier can create ADMIN memberships.")
            
        # 2. Validation
        if not tenant.is_active:
            raise ValidationError({"tenant": "Cannot assign to an inactive shop."})
            
        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise ValidationError({"user": "User does not exist."})
            
        if not target_user.is_active:
            raise ValidationError({"user": "Cannot assign an inactive user."})
            
        if TenantMember.objects.filter(user_id=user_id, tenant_id=tenant_id, deleted__isnull=True).exists():
            raise ValidationError("This user is already a member of the shop.")
            
        if tenant.is_at_user_limit:
            raise ValidationError({"tenant": "Shop has reached its maximum user limit."})
            
        if role == ShopRole.ADMIN:
            validate_admin_grade_user(target_user)
            current_admins = count_effective_admins(tenant_id)
            if current_admins >= 2:
                raise ValidationError("Shop cannot have more than 2 active ADMINs.")
                
        # 3. Create
        return TenantMember.objects.create(
            tenant=tenant,
            user=target_user,
            role=role,
            created_by=actor
        )


def change_membership_role(actor: User, membership_id, new_role: str) -> TenantMember:
    """Change the role of an existing membership."""
    with transaction.atomic():
        membership = TenantMember.objects.select_related('tenant').get(pk=membership_id)
        tenant_id = membership.tenant_id
        
        tenant = Tenant.objects.select_for_update().get(pk=tenant_id)
        membership.refresh_from_db()
        
        if membership.deleted:
            raise ValidationError("Cannot change role of a removed membership.")
            
        is_main_supplier = ShopRolePolicy.is_main_supplier_admin(actor)
        is_shop_admin = ShopRolePolicy.can_manage_memberships(actor, tenant_id)
        
        if not is_main_supplier and not is_shop_admin:
            raise PermissionDenied("You do not have permission to manage memberships for this Shop.")
            
        old_role = membership.role
        if old_role == new_role:
            return membership
            
        # Any transition involving ADMIN requires Main Supplier
        if (old_role == ShopRole.ADMIN or new_role == ShopRole.ADMIN) and not is_main_supplier:
            raise PermissionDenied("Only Main Supplier can manage ADMIN roles.")
            
        if new_role == ShopRole.ADMIN:
            validate_admin_grade_user(membership.user)
            if membership.is_active and membership.user.is_active:
                if count_effective_admins(tenant_id) >= 2:
                    raise ValidationError("Shop cannot have more than 2 active ADMINs.")
                    
        elif old_role == ShopRole.ADMIN:
            if membership.is_active and membership.user.is_active:
                if count_effective_admins(tenant_id) <= 1:
                    raise ValidationError("Shop must have at least 1 active ADMIN.")
                    
        membership.role = new_role
        membership.updated_by = actor
        membership.save(update_fields=['role', 'updated_by', 'updated_at'])
        return membership


def deactivate_membership(actor: User, membership_id) -> TenantMember:
    """Deactivate a membership."""
    with transaction.atomic():
        membership = TenantMember.objects.get(pk=membership_id)
        tenant = Tenant.objects.select_for_update().get(pk=membership.tenant_id)
        membership.refresh_from_db()
        
        if membership.deleted:
            raise ValidationError("Cannot deactivate a removed membership.")
        if not membership.is_active:
            raise ValidationError("Membership is already inactive.")
            
        is_main_supplier = ShopRolePolicy.is_main_supplier_admin(actor)
        is_shop_admin = ShopRolePolicy.can_manage_memberships(actor, tenant.id)
        
        if not is_main_supplier and not is_shop_admin:
            raise PermissionDenied("You do not have permission to manage memberships for this Shop.")
            
        if membership.role == ShopRole.ADMIN:
            if not is_main_supplier:
                raise PermissionDenied("Only Main Supplier can deactivate an ADMIN.")
            if membership.user.is_active:
                if count_effective_admins(tenant.id) <= 1:
                    raise ValidationError("Shop must have at least 1 active ADMIN.")
                    
        membership.is_active = False
        membership.updated_by = actor
        membership.save(update_fields=['is_active', 'updated_by', 'updated_at'])
        return membership


def reactivate_membership(actor: User, membership_id) -> TenantMember:
    """Reactivate a membership."""
    with transaction.atomic():
        membership = TenantMember.objects.get(pk=membership_id)
        tenant = Tenant.objects.select_for_update().get(pk=membership.tenant_id)
        membership.refresh_from_db()
        
        if membership.deleted:
            raise ValidationError("Cannot reactivate a removed membership.")
        if membership.is_active:
            raise ValidationError("Membership is already active.")
            
        is_main_supplier = ShopRolePolicy.is_main_supplier_admin(actor)
        is_shop_admin = ShopRolePolicy.can_manage_memberships(actor, tenant.id)
        
        if not is_main_supplier and not is_shop_admin:
            raise PermissionDenied("You do not have permission to manage memberships for this Shop.")
            
        if membership.role == ShopRole.ADMIN:
            if not is_main_supplier:
                raise PermissionDenied("Only Main Supplier can reactivate an ADMIN.")
            validate_admin_grade_user(membership.user)
            if membership.user.is_active:
                if count_effective_admins(tenant.id) >= 2:
                    raise ValidationError("Shop cannot have more than 2 active ADMINs.")
                    
        # Note: Do not check capacity because INACTIVE membership already consumes a slot.
        membership.is_active = True
        membership.updated_by = actor
        membership.save(update_fields=['is_active', 'updated_by', 'updated_at'])
        return membership


def remove_membership(actor: User, membership_id) -> TenantMember:
    """Soft remove an inactive membership."""
    with transaction.atomic():
        membership = TenantMember.objects.get(pk=membership_id)
        tenant = Tenant.objects.select_for_update().get(pk=membership.tenant_id)
        membership.refresh_from_db()
        
        if membership.deleted:
            raise ValidationError("Membership is already removed.")
        if membership.is_active:
            raise ValidationError("Cannot remove an active membership. Deactivate it first.")
            
        is_main_supplier = ShopRolePolicy.is_main_supplier_admin(actor)
        is_shop_admin = ShopRolePolicy.can_manage_memberships(actor, tenant.id)
        
        if not is_main_supplier and not is_shop_admin:
            raise PermissionDenied("You do not have permission to manage memberships for this Shop.")
            
        if membership.role == ShopRole.ADMIN and not is_main_supplier:
            raise PermissionDenied("Only Main Supplier can remove an ADMIN membership.")
            
        # Already inactive, so it doesn't affect active ADMIN count.
        membership.delete()
        return membership


def undo_remove_membership(actor: User, membership_id) -> TenantMember:
    """Restore a recently removed membership."""
    with transaction.atomic():
        try:
            membership = TenantMember.objects.all_with_deleted().get(pk=membership_id)
        except TenantMember.DoesNotExist:
            raise ValidationError("Membership not found.")
            
        if not membership.deleted:
            raise ValidationError("Membership is not removed.")
            
        if timezone.now() - membership.deleted > timedelta(seconds=5):
            raise ValidationError("Undo window expired.")
            
        tenant = Tenant.objects.select_for_update().get(pk=membership.tenant_id)
        
        is_main_supplier = ShopRolePolicy.is_main_supplier_admin(actor)
        is_shop_admin = ShopRolePolicy.can_manage_memberships(actor, tenant.id)
        
        if not is_main_supplier and not is_shop_admin:
            raise PermissionDenied("You do not have permission to manage memberships for this Shop.")
            
        if membership.role == ShopRole.ADMIN and not is_main_supplier:
            raise PermissionDenied("Only Main Supplier can undo removal of an ADMIN membership.")
            
        if tenant.is_at_user_limit:
            raise ValidationError("Shop has reached its maximum user limit. Cannot restore.")
            
        if membership.role == ShopRole.ADMIN and membership.is_active and membership.user.is_active:
            if count_effective_admins(tenant.id) >= 2:
                raise ValidationError("Shop cannot have more than 2 active ADMINs.")
                
        try:
            membership.undelete()
        except IntegrityError:
            raise ValidationError("Cannot restore: a membership for this user already exists in this Shop.")
            
        return membership


def create_shop_with_first_admin(actor: User, tenant_data: dict, first_admin_user_id) -> Tenant:
    """Create a shop and its first ADMIN membership atomically."""
    if not ShopRolePolicy.is_main_supplier_admin(actor):
        raise PermissionDenied("Only Main Supplier can create a Shop.")
        
    try:
        first_admin = User.objects.get(pk=first_admin_user_id)
    except User.DoesNotExist:
        raise ValidationError({"first_admin_user": "User does not exist."})
        
    validate_admin_grade_user(first_admin)
    
    max_users = tenant_data.get('max_users', 0)
    if max_users < 1:
        raise ValidationError({"max_users": "Shop capacity must be at least 1."})
        
    from apps.tenants.models import Supplier
    
    with transaction.atomic():
        supplier = Supplier.objects.get(singleton_lock=True)
        tenant = Tenant(supplier=supplier, created_by=actor, **tenant_data)
        tenant.save()
        
        TenantMember.objects.create(
            tenant=tenant,
            user=first_admin,
            role=ShopRole.ADMIN,
            is_active=True,
            created_by=actor
        )
        
        return tenant
