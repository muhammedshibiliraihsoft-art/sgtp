"""Transactional membership and Shop-ADMIN business operations."""

from datetime import timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.accounts.models import User
from apps.accounts.identity import normalize_login_id
from apps.accounts.security import (
    generate_initial_password,
    revoke_user_sessions,
    set_password_and_revoke_sessions,
)
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember
from apps.tenants.policy import ShopRolePolicy


def get_effective_admins(shop_id=None):
    """The single canonical effective-ADMIN definition for all Shops."""
    queryset = TenantMember.objects.filter(
        role=ShopRole.ADMIN,
        is_active=True,
        deleted__isnull=True,
        user__is_active=True,
    )
    if shop_id is not None:
        queryset = queryset.filter(tenant_id=shop_id)
    return queryset


def count_effective_admins(shop_id):
    return get_effective_admins(shop_id).count()


def validate_admin_grade_user(user):
    if not user.is_active:
        raise ValidationError({"user": "ADMIN user must be active."})
    if not (user.first_name or "").strip():
        raise ValidationError({"user": "ADMIN user must have a valid first name."})
    if not (user.email or "").strip():
        raise ValidationError({"user": "ADMIN user must have an email."})
    if not (user.phone or "").strip():
        raise ValidationError({"user": "ADMIN user must have a valid phone number."})


def _locked_user(user_id):
    try:
        return User.objects.select_for_update().get(pk=user_id)
    except User.DoesNotExist as exc:
        raise ValidationError({"user": "User does not exist."}) from exc


def _actor_authority(actor, shop_id):
    """Read authority from current database state; fail closed for stale actors."""
    current_actor = User.objects.filter(
        pk=getattr(actor, "pk", None), is_active=True
    ).first()
    if current_actor is None:
        raise PermissionDenied("Active global administration is required.")
    if ShopRolePolicy.is_main_supplier_admin(current_actor):
        return True
    if ShopRolePolicy.can_manage_memberships(current_actor, shop_id):
        return False
    raise PermissionDenied(
        "You do not have permission to manage memberships for this Shop."
    )


def _locked_shop(shop_id):
    try:
        return Tenant.objects.select_for_update().get(pk=shop_id)
    except Tenant.DoesNotExist as exc:
        raise NotFound() from exc


def _locked_membership(membership_id, *, include_removed=False):
    manager = (
        TenantMember.objects.all_with_deleted()
        if include_removed
        else TenantMember.objects
    )
    try:
        return manager.select_for_update().get(pk=membership_id)
    except TenantMember.DoesNotExist as exc:
        raise NotFound() from exc


def _check_admin_upper_bound(shop_id):
    if count_effective_admins(shop_id) >= 2:
        raise ValidationError("Shop cannot have more than 2 active ADMINs.")


def create_membership(actor, shop_id, user_id, role):
    """Create membership under Shop→User locks and enforce role/capacity rules."""
    with transaction.atomic():
        shop = _locked_shop(shop_id)
        is_main_supplier = _actor_authority(actor, shop.id)
        if role == ShopRole.ADMIN and not is_main_supplier:
            raise PermissionDenied("Only Main Supplier can create ADMIN memberships.")
        if not shop.is_active:
            raise ValidationError({"tenant": "Cannot assign to an inactive Shop."})

        user = _locked_user(user_id)
        if user.owning_shop_id != shop.pk:
            raise ValidationError(
                {"user": "This account is not owned by the selected Shop."}
            )
        if not user.is_active:
            raise ValidationError({"user": "Cannot assign an inactive user."})
        if not TenantMember.objects.all_with_deleted().filter(
            user_id=user.pk, tenant_id=shop.pk
        ).exists():
            raise ValidationError(
                "Create the account and its first membership atomically through the Shop account flow."
            )
        if TenantMember.objects.filter(
            user_id=user.pk, tenant_id=shop.pk, deleted__isnull=True
        ).exists():
            raise ValidationError("This user is already a member of the Shop.")
        if shop.is_at_user_limit:
            raise ValidationError(
                {"tenant": "Shop has reached its maximum user limit."}
            )
        if role == ShopRole.ADMIN:
            validate_admin_grade_user(user)
            _check_admin_upper_bound(shop.pk)
        return TenantMember.objects.create(
            tenant=shop, user=user, role=role, is_active=True, created_by=actor
        )


def change_membership_role(actor, membership_id, new_role, *, new_login_id=None):
    with transaction.atomic():
        try:
            initial = TenantMember.objects.only("tenant_id").get(pk=membership_id)
        except TenantMember.DoesNotExist as exc:
            raise NotFound() from exc
        shop = _locked_shop(initial.tenant_id)
        membership = _locked_membership(membership_id)
        user = _locked_user(membership.user_id)
        membership.user = user
        if membership.deleted:
            raise ValidationError("Cannot change role of a removed membership.")
        is_main_supplier = _actor_authority(actor, shop.pk)
        if not is_main_supplier and not shop.is_active:
            raise PermissionDenied("Inactive Shops are not operational.")
        old_role = membership.role
        if old_role == new_role:
            return membership
        if (
            old_role == ShopRole.ADMIN or new_role == ShopRole.ADMIN
        ) and not is_main_supplier:
            raise PermissionDenied("Only Main Supplier can manage ADMIN roles.")

        effective_before = membership.is_active and user.is_active
        effective_after = effective_before and new_role == ShopRole.ADMIN
        if new_role == ShopRole.ADMIN and effective_after:
            validate_admin_grade_user(user)
            _check_admin_upper_bound(shop.pk)
        if old_role == ShopRole.ADMIN and effective_before and not effective_after:
            if count_effective_admins(shop.pk) <= 1:
                raise ValidationError("Shop must have at least 1 active ADMIN.")

        promotion_credentials = None
        if old_role == ShopRole.VIEWER and new_role == ShopRole.STAFF:
            login_id = user.login_id
            if login_id is None:
                try:
                    login_id = normalize_login_id(new_login_id)
                except ValueError as exc:
                    raise ValidationError({"new_login_id": str(exc)}) from exc
                if User.objects.filter(login_id__iexact=login_id).exclude(pk=user.pk).exists():
                    raise ValidationError({"new_login_id": "This Login ID is unavailable."})
                user.login_id = login_id
                user.save(update_fields=["login_id", "updated_at"])
            elif new_login_id:
                try:
                    requested_login_id = normalize_login_id(new_login_id)
                except ValueError as exc:
                    raise ValidationError({"new_login_id": str(exc)}) from exc
                if requested_login_id != login_id:
                    raise ValidationError({"new_login_id": "This account's Login ID cannot be changed."})
            temporary_pin = generate_initial_password(user)
            set_password_and_revoke_sessions(user, temporary_pin, must_change=True)
            promotion_credentials = {
                "login_id": login_id,
                "temporary_password": temporary_pin,
            }
        elif new_role == ShopRole.VIEWER:
            revoke_user_sessions(user)

        membership.role = new_role
        membership.updated_by = actor
        membership.save(update_fields=["role", "updated_by", "updated_at"])
        if user.login_enabled != (new_role != ShopRole.VIEWER):
            user.login_enabled = new_role != ShopRole.VIEWER
            user.save(update_fields=["login_enabled", "updated_at"])
        membership.promotion_credentials = promotion_credentials
        return membership


def deactivate_membership(actor, membership_id):
    with transaction.atomic():
        try:
            initial = TenantMember.objects.only("tenant_id").get(pk=membership_id)
        except TenantMember.DoesNotExist as exc:
            raise NotFound() from exc
        shop = _locked_shop(initial.tenant_id)
        membership = _locked_membership(membership_id)
        user = _locked_user(membership.user_id)
        membership.user = user
        is_main_supplier = _actor_authority(actor, shop.pk)
        if not is_main_supplier and not shop.is_active:
            raise PermissionDenied("Inactive Shops are not operational.")
        if membership.deleted:
            raise ValidationError("Cannot deactivate a removed membership.")
        if not membership.is_active:
            raise ValidationError("Membership is already inactive.")
        if membership.role == ShopRole.ADMIN:
            if not is_main_supplier:
                raise PermissionDenied("Only Main Supplier can deactivate an ADMIN.")
            if user.is_active and count_effective_admins(shop.pk) <= 1:
                raise ValidationError("Shop must have at least 1 active ADMIN.")
        membership.is_active = False
        membership.updated_by = actor
        membership.save(update_fields=["is_active", "updated_by", "updated_at"])
        return membership


def reactivate_membership(actor, membership_id):
    with transaction.atomic():
        try:
            initial = TenantMember.objects.only("tenant_id").get(pk=membership_id)
        except TenantMember.DoesNotExist as exc:
            raise NotFound() from exc
        shop = _locked_shop(initial.tenant_id)
        membership = _locked_membership(membership_id)
        user = _locked_user(membership.user_id)
        membership.user = user
        is_main_supplier = _actor_authority(actor, shop.pk)
        if not shop.is_active:
            raise ValidationError(
                {"tenant": "Cannot reactivate membership in an inactive Shop."}
            )
        if membership.deleted:
            raise ValidationError("Cannot reactivate a removed membership.")
        if membership.is_active:
            raise ValidationError("Membership is already active.")
        if not user.is_active:
            raise ValidationError(
                {"user": "Cannot reactivate membership for an inactive User."}
            )
        if membership.role == ShopRole.ADMIN:
            if not is_main_supplier:
                raise PermissionDenied("Only Main Supplier can reactivate an ADMIN.")
            validate_admin_grade_user(user)
            _check_admin_upper_bound(shop.pk)
        # INACTIVE memberships already consume capacity; no additional slot is used.
        membership.is_active = True
        membership.updated_by = actor
        membership.save(update_fields=["is_active", "updated_by", "updated_at"])
        return membership


def remove_membership(actor, membership_id):
    with transaction.atomic():
        try:
            initial = TenantMember.objects.only("tenant_id").get(pk=membership_id)
        except TenantMember.DoesNotExist as exc:
            raise NotFound() from exc
        shop = _locked_shop(initial.tenant_id)
        membership = _locked_membership(membership_id)
        _locked_user(membership.user_id)
        is_main_supplier = _actor_authority(actor, shop.pk)
        if not is_main_supplier and not shop.is_active:
            raise PermissionDenied("Inactive Shops are not operational.")
        if membership.deleted:
            raise ValidationError("Membership is already removed.")
        if membership.is_active:
            raise ValidationError(
                "Cannot remove an active membership. Deactivate it first."
            )
        if membership.role == ShopRole.ADMIN and not is_main_supplier:
            raise PermissionDenied("Only Main Supplier can remove an ADMIN membership.")
        membership.updated_by = actor
        membership.save(update_fields=["updated_by", "updated_at"])
        membership.delete()
        return membership


def undo_remove_membership(actor, membership_id):
    # Candidate lookup obtains only the Shop key; state is re-read under locks.
    try:
        initial = (
            TenantMember.objects.all_with_deleted()
            .only("tenant_id")
            .get(pk=membership_id)
        )
    except TenantMember.DoesNotExist as exc:
        raise NotFound() from exc
    with transaction.atomic():
        shop = _locked_shop(initial.tenant_id)
        membership = _locked_membership(membership_id, include_removed=True)
        user = _locked_user(membership.user_id)
        membership.user = user
        is_main_supplier = _actor_authority(actor, shop.pk)
        is_shop_admin = not is_main_supplier and ShopRolePolicy.can_manage_memberships(
            actor, shop.pk
        )
        if not is_main_supplier and not is_shop_admin:
            raise PermissionDenied(
                "You do not have permission to manage memberships for this Shop."
            )
        if not membership.deleted:
            raise ValidationError("Membership is not removed.")
        if membership.role == ShopRole.ADMIN and not is_main_supplier:
            raise PermissionDenied(
                "Only Main Supplier can undo removal of an ADMIN membership."
            )
        if shop.is_at_user_limit:
            raise ValidationError(
                "Shop has reached its maximum user limit. Cannot restore."
            )
        if membership.role == ShopRole.ADMIN and membership.is_active:
            validate_admin_grade_user(user)
            _check_admin_upper_bound(shop.pk)
        # Decisive check is after locking and immediately before the restore path.
        if timezone.now() > membership.deleted + timedelta(seconds=5):
            raise ValidationError("Undo window expired.")
        try:
            with transaction.atomic():
                membership.undelete()
        except IntegrityError as exc:
            raise ValidationError(
                "Cannot restore: a membership for this user already exists in this Shop."
            ) from exc
        except DjangoValidationError as exc:
            details = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            raise ValidationError(details) from exc
        return membership


def create_shop_with_first_admin(actor, shop_data, first_admin_data):
    """Atomically create an active Shop and a new, Shop-owned first ADMIN."""
    with transaction.atomic():
        current_actor = User.objects.filter(
            pk=getattr(actor, "pk", None), is_active=True
        ).first()
        if not ShopRolePolicy.is_main_supplier_admin(current_actor):
            raise PermissionDenied("Only Main Supplier can create a Shop.")
        data = dict(shop_data)
        if data.pop("is_active", True) is False:
            raise ValidationError(
                {
                    "is_active": "A Shop must be active when created with its first ADMIN."
                }
            )
        if data.get("max_users", 0) < 1:
            raise ValidationError({"max_users": "Shop capacity must be at least 1."})
        supplier = Supplier.objects.get(singleton_lock=True)
        shop = Tenant(supplier=supplier, created_by=actor, is_active=True, **data)
        shop.save()
        from .shop_accounts import create_shop_account

        user, initial_password = create_shop_account(
            actor=actor,
            shop_id=shop.pk,
            role=ShopRole.ADMIN,
            account_data=first_admin_data,
        )
        return shop, user, initial_password
