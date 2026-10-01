"""Transactional domain operations for Clients and Related Persons."""

from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotAuthenticated, NotFound, PermissionDenied

from apps.clients.models import Client
from apps.clients.normalization import normalize_email, normalize_phone
from apps.tenants.policy import ShopRolePolicy
from apps.tenants.models import Tenant


def _prepare_contact(values):
    values = dict(values)
    values["name"] = values["name"].strip()
    values["phone"] = values.get("phone", "").strip()
    values["email"] = values.get("email", "").strip()
    values["phone_normalized"] = normalize_phone(values["phone"])
    values["email_normalized"] = normalize_email(values["email"])
    return values


def _duplicate_warnings(model, shop_id, contact, *, exclude_id=None):
    base = model.objects.filter(tenant_id=shop_id)
    if exclude_id is not None:
        base = base.exclude(pk=exclude_id)
    warnings = []
    for field, key in (
        ("phone", "phone_normalized"),
        ("email", "email_normalized"),
    ):
        normalized = contact[key]
        if not normalized:
            continue
        matches = list(
            base.filter(**{key: normalized})
            .order_by("name", "id")
            .values("id", "name")[:10]
        )
        if matches:
            warnings.append(
                {
                    "code": "possible_duplicate",
                    "field": field,
                    "matches": [
                        {"id": str(match["id"]), "name": match["name"]}
                        for match in matches
                    ],
                }
            )
    return warnings


def _authorize_locked_shop(*, shop, actor, deleting=False):
    """Recheck active Shop membership under the Shop write lock."""
    if not shop.is_active:
        raise NotFound()
    user_model = get_user_model()
    if (
        not actor
        or not getattr(actor, "is_authenticated", False)
        or not user_model.objects.filter(pk=actor.pk, is_active=True).exists()
    ):
        raise NotAuthenticated()
    if ShopRolePolicy.is_main_supplier_admin(actor):
        return
    membership = ShopRolePolicy.get_active_membership(actor, shop.pk)
    if membership is None:
        raise NotFound()
    if deleting:
        if membership.role != "ADMIN":
            raise PermissionDenied()
    elif membership.role not in {"ADMIN", "STAFF"}:
        raise PermissionDenied()


@transaction.atomic
def create_contact(*, model, shop_id, values, actor, primary_client=None):
    shop = get_object_or_404(Tenant.objects.select_for_update(), pk=shop_id)
    _authorize_locked_shop(shop=shop, actor=actor)
    contact = _prepare_contact(values)
    if primary_client is not None:
        parent = get_object_or_404(
            Client.objects.select_for_update().filter(tenant_id=shop.pk),
            pk=primary_client,
        )
        contact["primary_client"] = parent
    warnings = _duplicate_warnings(model, shop.pk, contact)
    record = model.objects.create(
        tenant=shop,
        created_by=actor,
        updated_by=actor,
        **contact,
    )
    return record, warnings


@transaction.atomic
def update_contact(*, model, shop_id, record_id, values, actor):
    shop = get_object_or_404(Tenant.objects.select_for_update(), pk=shop_id)
    _authorize_locked_shop(shop=shop, actor=actor)
    record = get_object_or_404(
        model.objects.select_for_update().filter(tenant_id=shop.pk), pk=record_id
    )
    changes_contact = bool({"phone", "email"} & set(values))
    merged = {
        "name": values.get("name", record.name),
        "phone": values.get("phone", record.phone),
        "email": values.get("email", record.email),
    }
    normalized = _prepare_contact(merged)
    warnings = (
        _duplicate_warnings(model, shop.pk, normalized, exclude_id=record.pk)
        if changes_contact
        else []
    )
    for key in ("name", "phone", "email", "phone_normalized", "email_normalized"):
        setattr(record, key, normalized[key])
    record.updated_by = actor
    record.save()
    return record, warnings


@transaction.atomic
def soft_delete_contact(*, model, shop_id, record_id, actor):
    shop = get_object_or_404(Tenant.objects.select_for_update(), pk=shop_id)
    _authorize_locked_shop(shop=shop, actor=actor, deleting=True)
    record = get_object_or_404(
        model.objects.select_for_update().filter(tenant_id=shop.pk), pk=record_id
    )
    record.updated_by = actor
    record.save(update_fields=("updated_by", "updated_at"))
    record.delete()
    return record
