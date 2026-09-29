"""Transactional global User lifecycle operations."""

from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.accounts.models import User
from apps.tenants.models import ShopRole, Tenant, TenantMember
from apps.tenants.policy import ShopRolePolicy
from apps.tenants.services.membership import get_effective_admins
from apps.accounts.security import generate_initial_password, set_password_and_revoke_sessions


def reset_user_credentials(actor, target_user):
    """Use global authority or same-Shop ADMIN authority for normal members."""
    current_actor = User.objects.filter(
        pk=getattr(actor, "pk", None), is_active=True
    ).first()
    if ShopRolePolicy.is_main_supplier_admin(current_actor):
        with transaction.atomic():
            target = User.objects.select_for_update().get(pk=target_user.pk)
            password = generate_initial_password(target)
            set_password_and_revoke_sessions(target, password, must_change=True)
            return password

    shop_id = getattr(current_actor, "owning_shop_id", None)
    if not shop_id:
        raise NotFound()
    with transaction.atomic():
        try:
            shop = Tenant.objects.select_for_update().get(pk=shop_id, is_active=True)
        except Tenant.DoesNotExist as exc:
            raise NotFound() from exc
        current_actor = User.objects.filter(
            pk=getattr(actor, "pk", None), is_active=True, owning_shop_id=shop.pk
        ).first()
        if not ShopRolePolicy.can_manage_memberships(current_actor, shop.pk):
            raise NotFound()
        membership = (
            TenantMember.objects.select_for_update()
            .filter(
                tenant=shop,
                user_id=target_user.pk,
                role__in=[ShopRole.STAFF, ShopRole.VIEWER],
                is_active=True,
                deleted__isnull=True,
            )
            .first()
        )
        target = User.objects.select_for_update().filter(
            pk=target_user.pk, owning_shop_id=shop.pk, is_active=True
        ).first()
        if membership is None or target is None:
            raise NotFound()
        password = generate_initial_password(target)
        set_password_and_revoke_sessions(target, password, must_change=True)
        return password


def deactivate_global_user(actor, target_user, *, update_fields=None):
    """Deactivate a User while preserving their owning Shop's ADMIN invariant."""
    user_id = target_user.pk
    concrete_fields = {
        field.name
        for field in User._meta.concrete_fields
        if not field.primary_key and not field.auto_created
    }
    requested_fields = set(update_fields or ()) & concrete_fields

    shop_id = target_user.owning_shop_id
    with transaction.atomic():
        if shop_id and not target_user.is_superuser:
            try:
                Tenant.objects.select_for_update().get(pk=shop_id)
            except Tenant.DoesNotExist as exc:
                raise ValidationError("User owning Shop is unavailable.") from exc
        locked_user = User.objects.select_for_update().get(pk=user_id)
        current_actor = User.objects.filter(
            pk=getattr(actor, "pk", None), is_active=True
        ).first()
        if not ShopRolePolicy.is_main_supplier_admin(current_actor):
            raise PermissionDenied("Only Main Supplier may deactivate a User.")
        if not locked_user.is_active:
            target_user.__dict__.update(locked_user.__dict__)
            return locked_user
        if shop_id and get_effective_admins(shop_id).filter(user_id=user_id).exists():
            if get_effective_admins(shop_id).count() <= 1:
                raise ValidationError(
                    "Cannot deactivate User: the owning Shop would have no active ADMIN."
                )
        for field_name in requested_fields:
            setattr(locked_user, field_name, getattr(target_user, field_name))
        locked_user.is_active = False
        locked_user.save(update_fields=requested_fields | {"is_active"})
        target_user.__dict__.update(locked_user.__dict__)
        return locked_user
