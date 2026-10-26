"""Main Supplier-reviewed Shop ADMIN PIN recovery."""

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.tenants.models import ShopRole, TenantMember
from apps.tenants.policy import ShopRolePolicy
from apps.accounts.models import ShopAdminPinResetRequest, User
from apps.accounts.security import (
    generate_initial_password,
    set_password_and_revoke_sessions,
)


def eligible_admin(user, shop_id, phone):
    return bool(
        user
        and user.is_active
        and not user.is_superuser
        and user.owning_shop_id == shop_id
        and user.phone == phone
        and TenantMember.objects.filter(
            user_id=user.pk,
            tenant_id=shop_id,
            tenant__is_active=True,
            role=ShopRole.ADMIN,
            is_active=True,
            deleted__isnull=True,
        ).exists()
    )


def find_eligible_admin(phone):
    user = User.objects.filter(phone=phone, is_active=True).first()
    if (
        not user
        or not user.owning_shop_id
        or not eligible_admin(user, user.owning_shop_id, phone)
    ):
        return None
    return user


def submit_request(user, phone):
    try:
        with transaction.atomic():
            user = User.objects.filter(pk=user.pk, is_active=True).first()
            if (
                not user
                or not user.owning_shop_id
                or not eligible_admin(user, user.owning_shop_id, phone)
            ):
                return
            ShopAdminPinResetRequest.objects.get_or_create(
                user=user,
                status=ShopAdminPinResetRequest.Status.PENDING,
                defaults={"shop_id": user.owning_shop_id, "phone": phone},
            )
    except IntegrityError:
        # Concurrent duplicate requests are intentionally indistinguishable.
        pass


def _main_supplier(actor):
    current = User.objects.filter(pk=getattr(actor, "pk", None), is_active=True).first()
    if not ShopRolePolicy.is_main_supplier_admin(current):
        raise PermissionDenied("Main Supplier authority required.")
    return current


def resolve_request(actor, request_id, *, approve):
    current = _main_supplier(actor)
    with transaction.atomic():
        reset = (
            ShopAdminPinResetRequest.objects.select_for_update()
            .filter(pk=request_id)
            .first()
        )
        if not reset:
            raise NotFound()
        if reset.status != ShopAdminPinResetRequest.Status.PENDING:
            raise ValidationError("Reset request is already resolved.")
        if approve:
            user = User.objects.select_for_update().filter(pk=reset.user_id).first()
            if not eligible_admin(user, reset.shop_id, reset.phone):
                raise ValidationError(
                    "This request is no longer eligible; reject it instead."
                )
            pin = generate_initial_password(user)
            set_password_and_revoke_sessions(user, pin, must_change=True)
            reset.status = ShopAdminPinResetRequest.Status.APPROVED
        else:
            pin = None
            reset.status = ShopAdminPinResetRequest.Status.REJECTED
        reset.resolved_by = current
        reset.resolved_at = timezone.now()
        reset.save(update_fields=["status", "resolved_by", "resolved_at"])
        return reset, pin
