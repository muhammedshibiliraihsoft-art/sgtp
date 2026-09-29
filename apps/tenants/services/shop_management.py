"""Locked Shop lifecycle and configuration operations for Main Supplier."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.tenants.models import Tenant

User = get_user_model()


def _locked_shop(shop_id):
    try:
        return Tenant.objects.select_for_update().get(pk=shop_id)
    except (Tenant.DoesNotExist, ValueError, TypeError) as exc:
        raise NotFound() from exc


def _current_main_supplier(actor):
    current = User.objects.filter(
        pk=getattr(actor, "pk", None), is_active=True, is_superuser=True
    ).first()
    if current is None:
        raise PermissionDenied("Only Main Supplier may manage Shop configuration.")
    return current


def update_shop(actor, shop_id, changes):
    """Update approved Shop profile/settings fields under the Shop capacity lock."""
    allowed = {
        "name",
        "slug",
        "domain",
        "max_users",
        "contact_email",
        "contact_phone",
        "address_line1",
        "address_line2",
        "city",
        "state",
        "postal_code",
        "country",
        "default_locale",
        "default_timezone",
        "default_currency",
    }
    unexpected = set(changes) - allowed
    if unexpected:
        raise ValidationError(
            {key: "This field cannot be changed here." for key in unexpected}
        )

    with transaction.atomic():
        shop = _locked_shop(shop_id)
        current_actor = _current_main_supplier(actor)
        for name, value in changes.items():
            setattr(shop, name, value)
        if shop.max_users < shop.user_count:
            raise ValidationError(
                {"max_users": "Cannot be lower than the current Shop user count."}
            )
        try:
            shop.full_clean()
        except DjangoValidationError as exc:
            details = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            raise ValidationError(details) from exc
        shop.updated_by = current_actor
        update_fields = [*changes, "updated_by", "updated_at"]
        shop.save(update_fields=update_fields)
        return shop


def set_shop_active(actor, shop_id, *, active):
    """Activate/deactivate a Shop without deleting memberships or history."""
    with transaction.atomic():
        shop = _locked_shop(shop_id)
        current_actor = _current_main_supplier(actor)
        shop.is_active = active
        shop.updated_by = current_actor
        shop.save(update_fields=["is_active", "updated_by", "updated_at"])
        return shop
