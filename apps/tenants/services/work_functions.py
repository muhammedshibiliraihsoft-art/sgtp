"""Transactional membership-scoped Work-Function management."""

from django.db import IntegrityError, transaction
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.accounts.models import User
from apps.tenants.models import (
    MembershipWorkFunction,
    ShopRole,
    Tenant,
    TenantMember,
    WorkFunctionCode,
)
from apps.tenants.policy import ShopRolePolicy


def _locked_membership_for_shop_admin(actor, shop_id, membership_id):
    """Lock Shop first so membership authority/lifecycle mutations serialize."""
    try:
        shop = Tenant.objects.select_for_update().get(pk=shop_id, is_active=True)
    except Tenant.DoesNotExist as exc:
        raise NotFound() from exc

    current_actor = User.objects.filter(
        pk=getattr(actor, "pk", None), is_active=True
    ).first()
    if current_actor is None:
        raise NotFound()
    if ShopRolePolicy.is_main_supplier_admin(current_actor):
        # Platform-wide Shop administration does not grant Shop-local
        # operational Work-Function management.
        raise PermissionDenied("Only this Shop's ADMIN can manage Work Functions.")
    if current_actor.owning_shop_id != shop.pk:
        raise NotFound()

    admin_membership = (
        TenantMember.objects.select_for_update()
        .filter(
            tenant=shop,
            user=current_actor,
            role=ShopRole.ADMIN,
            is_active=True,
            deleted__isnull=True,
            user__is_active=True,
        )
        .first()
    )
    if admin_membership is None:
        if ShopRolePolicy.get_active_membership(current_actor, shop.pk) is None:
            raise NotFound()
        raise PermissionDenied("Only this Shop's ADMIN can manage Work Functions.")

    try:
        membership = TenantMember.objects.select_for_update().get(
            pk=membership_id, tenant=shop
        )
    except (TenantMember.DoesNotExist, ValueError) as exc:
        # A foreign, removed, and nonexistent membership are indistinguishable.
        raise NotFound() from exc
    return current_actor, shop, membership


def _validate_function_codes(function_codes):
    allowed = {code for code, _label in WorkFunctionCode.choices}
    if len(function_codes) != len(set(function_codes)):
        raise ValidationError(
            {"functions": ["Duplicate Work Functions are not allowed."]}
        )
    invalid = [code for code in function_codes if code not in allowed]
    if invalid:
        raise ValidationError(
            {"functions": ["One or more Work Functions are invalid."]}
        )


def _ordered_codes(function_codes):
    order = {
        code: index for index, (code, _label) in enumerate(WorkFunctionCode.choices)
    }
    return sorted(function_codes, key=order.__getitem__)


@transaction.atomic
def get_membership_work_functions(*, actor, shop_id, membership_id):
    _current_actor, _shop, membership = _locked_membership_for_shop_admin(
        actor, shop_id, membership_id
    )
    rows = MembershipWorkFunction.objects.select_for_update().filter(
        membership=membership
    )
    return membership, _ordered_codes(
        list(rows.values_list("function_code", flat=True))
    )


@transaction.atomic
def set_membership_work_functions(*, actor, shop_id, membership_id, function_codes):
    """Atomically replace one membership's current set, retaining removed history."""
    _validate_function_codes(function_codes)
    current_actor, _shop, membership = _locked_membership_for_shop_admin(
        actor, shop_id, membership_id
    )
    desired = set(function_codes)
    current_rows = list(
        MembershipWorkFunction.objects.select_for_update()
        .filter(membership=membership)
        .order_by("function_code", "pk")
    )
    current_by_code = {row.function_code: row for row in current_rows}

    for code, row in current_by_code.items():
        if code not in desired:
            row.updated_by = current_actor
            row.save(update_fields=["updated_by", "updated_at"])
            row.delete()

    for code in _ordered_codes(desired - current_by_code.keys()):
        try:
            with transaction.atomic():
                MembershipWorkFunction.objects.create(
                    membership=membership,
                    function_code=code,
                    created_by=current_actor,
                    updated_by=current_actor,
                )
        except IntegrityError as exc:
            raise ValidationError(
                {"functions": ["The Work-Function set changed concurrently; retry."]}
            ) from exc

    return membership, _ordered_codes(desired)
