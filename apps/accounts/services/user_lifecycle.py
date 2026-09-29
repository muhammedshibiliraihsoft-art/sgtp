"""Transactional global User lifecycle operations."""

from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.accounts.models import User
from apps.tenants.models import Tenant, TenantMember
from apps.tenants.policy import ShopRolePolicy
from apps.tenants.services.membership import get_effective_admins


class _RetryShopLocks(Exception):
    pass


def deactivate_global_user(actor, target_user, *, update_fields=None):
    """Deactivate a User only when every Shop retains an effective ADMIN.

    Lock order is Shop rows in UUID order, followed by the target User. If a
    membership appears in a new Shop before the User lock is acquired, retry
    with the expanded Shop lock set rather than reversing lock order.
    """
    user_id = target_user.pk
    concrete_fields = {
        field.name
        for field in User._meta.concrete_fields
        if not field.primary_key and not field.auto_created
    }
    requested_fields = set(update_fields or ()) & concrete_fields

    while True:
        try:
            with transaction.atomic():
                candidate_shop_ids = set(
                    TenantMember.objects.filter(
                        user_id=user_id, deleted__isnull=True
                    ).values_list("tenant_id", flat=True)
                )
                locked_shop_ids = set(
                    Tenant.objects.filter(pk__in=candidate_shop_ids)
                    .select_for_update()
                    .order_by("pk")
                    .values_list("pk", flat=True)
                )
                locked_user = User.objects.select_for_update().get(pk=user_id)

                fresh_shop_ids = set(
                    TenantMember.objects.filter(
                        user_id=user_id, deleted__isnull=True
                    ).values_list("tenant_id", flat=True)
                )
                if fresh_shop_ids - locked_shop_ids:
                    raise _RetryShopLocks

                current_actor = User.objects.filter(
                    pk=getattr(actor, "pk", None), is_active=True
                ).first()
                if not ShopRolePolicy.is_main_supplier_admin(current_actor):
                    raise PermissionDenied(
                        "Only Main Supplier may deactivate a global User."
                    )
                if not locked_user.is_active:
                    target_user.__dict__.update(locked_user.__dict__)
                    return locked_user

                affected_shop_ids = set(
                    get_effective_admins()
                    .filter(user_id=user_id)
                    .values_list("tenant_id", flat=True)
                )
                for shop_id in affected_shop_ids:
                    if get_effective_admins(shop_id).count() <= 1:
                        raise ValidationError(
                            "Cannot deactivate User: it would leave one or more Shops without an active ADMIN."
                        )

                for field_name in requested_fields:
                    setattr(locked_user, field_name, getattr(target_user, field_name))
                locked_user.is_active = False
                locked_user.save(update_fields=requested_fields | {"is_active"})
                target_user.__dict__.update(locked_user.__dict__)
                return locked_user
        except _RetryShopLocks:
            continue
