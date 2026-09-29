"""Atomic creation and credential-reset operations for Shop-scoped accounts."""

from django.db import IntegrityError, transaction
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.accounts.models import User
from apps.accounts.security import generate_initial_password
from apps.tenants.models import ShopRole, Tenant, TenantMember
from apps.tenants.policy import ShopRolePolicy


def _locked_shop(shop_id):
    try:
        return Tenant.objects.select_for_update().get(pk=shop_id)
    except (Tenant.DoesNotExist, ValueError) as exc:
        raise NotFound() from exc


def create_shop_account(actor, shop_id, role, account_data):
    """Create one immutable Shop-owned User and membership in one transaction."""
    with transaction.atomic():
        shop = _locked_shop(shop_id)
        current_actor = User.objects.filter(
            pk=getattr(actor, "pk", None), is_active=True
        ).first()
        if current_actor is None:
            raise PermissionDenied("Active account administration is required.")
        is_main_supplier = ShopRolePolicy.is_main_supplier_admin(current_actor)
        if not is_main_supplier and not ShopRolePolicy.can_manage_memberships(
            current_actor, shop.pk
        ):
            raise NotFound()
        if not shop.is_active:
            raise ValidationError(
                {"shop": "Cannot create accounts in an inactive Shop."}
            )
        if role not in ShopRole.values:
            raise ValidationError({"role": "Unsupported Shop role."})
        if not is_main_supplier and role == ShopRole.ADMIN:
            raise PermissionDenied("Shop ADMINs cannot create ADMIN accounts.")
        if shop.is_at_user_limit:
            raise ValidationError({"shop": "Shop has reached its user limit."})

        data = dict(account_data)
        for key in ("email", "phone"):
            if data.get(key) == "":
                data[key] = None
        if role == ShopRole.ADMIN:
            if not (data.get("email") or "").strip():
                raise ValidationError({"email": "ADMIN accounts require email."})
            if not (data.get("phone") or "").strip():
                raise ValidationError({"phone": "ADMIN accounts require phone."})
            if (
                TenantMember.objects.filter(
                    tenant=shop,
                    role=ShopRole.ADMIN,
                    is_active=True,
                    deleted__isnull=True,
                    user__is_active=True,
                ).count()
                >= 2
            ):
                raise ValidationError("Shop cannot have more than 2 active ADMINs.")

        candidate = User(
            owning_shop=shop,
            email=data.get("email"),
            phone=data.get("phone"),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
        )
        initial_password = generate_initial_password(candidate)
        try:
            user = User.objects.create_user(
                password=initial_password,
                owning_shop=shop,
                must_change_password=True,
                **data,
            )
        except IntegrityError as exc:
            constraint = getattr(
                getattr(getattr(exc, "__cause__", None), "diag", None),
                "constraint_name",
                "",
            )
            if constraint in {"unique_user_login_phone", "accounts_user_phone_key"}:
                raise ValidationError(
                    {"phone": "This login phone is unavailable."}
                ) from exc
            if constraint in {"unique_user_email_casefold", "accounts_user_email_key"}:
                raise ValidationError({"email": "This email is unavailable."}) from exc
            raise

        TenantMember.objects.create(
            tenant=shop,
            user=user,
            role=role,
            is_active=True,
            created_by=current_actor,
        )
        return user, initial_password
