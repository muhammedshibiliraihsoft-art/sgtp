"""Authorization and transactional operations for measurements and materials."""

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.fields import ErrorDetail

from apps.catalog.measurement_models import (
    Material,
    MeasurementDefinition,
    MeasurementDefinitionMapping,
    MeasurementDefinitionTranslation,
    MeasurementProfile,
    MeasurementSet,
    MeasurementValue,
    MeasurementValueTranslationSnapshot,
)
from apps.catalog.inventory_models import InventoryBalance
from apps.catalog.models import GarmentFamily, GarmentVariant
from apps.clients.models import Client
from apps.tenants.models import MembershipWorkFunction, Tenant, TenantMember
from apps.tenants.policy import ShopRolePolicy


def _actor_and_membership(shop_id, actor, *, lock=False):
    if not actor or not actor.is_authenticated or not actor.is_active:
        raise PermissionDenied()
    shops = Tenant.objects
    members = TenantMember.objects
    if lock:
        shops = shops.select_for_update()
        members = members.select_for_update()
    shop = shops.filter(pk=shop_id, is_active=True).first()
    if shop is None:
        raise NotFound()
    if ShopRolePolicy.is_main_supplier_admin(actor):
        return shop, None
    membership = members.filter(
        tenant=shop,
        user=actor,
        user__is_active=True,
        is_active=True,
        deleted__isnull=True,
    ).first()
    if membership is None:
        raise NotFound()
    return shop, membership


def require_measurement_access(
    shop_id, actor, *, write=False, archive=False, lock=False
):
    shop, membership = _actor_and_membership(shop_id, actor, lock=lock)
    if membership is None or membership.role == "ADMIN":
        return shop, membership
    if membership.role != "STAFF" or archive:
        raise PermissionDenied()
    assigned = MembershipWorkFunction.objects.filter(
        membership=membership,
        function_code="MEASUREMENT",
        deleted__isnull=True,
    ).exists()
    if not assigned:
        raise PermissionDenied()
    return shop, membership


def require_material_access(shop_id, actor, *, write=False, lock=False):
    shop, membership = _actor_and_membership(shop_id, actor, lock=lock)
    if membership is None or membership.role == "ADMIN":
        return shop, membership
    if write or membership.role not in {"STAFF", "VIEWER"}:
        raise PermissionDenied()
    return shop, membership


def _valid_profile_relations(*, shop, person_model, person_id, family_id, variant_id):
    person_qs = person_model.objects.select_for_update()
    person = person_qs.filter(pk=person_id, tenant=shop).first()
    if person is None:
        raise NotFound()
    family = get_object_or_404(
        GarmentFamily.objects.select_for_update().filter(
            status=GarmentFamily.Status.ACTIVE
        ),
        pk=family_id,
    )
    variant = None
    if variant_id:
        variant = (
            GarmentVariant.objects.select_for_update()
            .filter(pk=variant_id, family=family, is_active=True)
            .filter(Q(tenant__isnull=True) | Q(tenant=shop))
            .first()
        )
        if variant is None:
            raise ValidationError(
                {"variant_id": "Variant is unavailable for this Shop and family."}
            )
    return person, family, variant


@transaction.atomic
def create_measurement_profile(
    *, shop_id, actor, person_model, person_id, family_id, variant_id=None
):
    shop, _membership = require_measurement_access(
        shop_id, actor, write=True, lock=True
    )
    person, family, variant = _valid_profile_relations(
        shop=shop,
        person_model=person_model,
        person_id=person_id,
        family_id=family_id,
        variant_id=variant_id,
    )
    owner_field = "client" if person_model is Client else "related_person"
    profile_identity = {
        "tenant": shop,
        "family": family,
        "variant": variant,
        f"{owner_field}_id": person.pk,
        "deleted__isnull": True,
    }
    if MeasurementProfile.objects.filter(**profile_identity).exists():
        raise ValidationError(
            {"profile": "A profile already exists for this person and garment."}
        )
    try:
        with transaction.atomic():
            profile = MeasurementProfile.objects.create(
                tenant=shop,
                family=family,
                variant=variant,
                **{owner_field: person},
                created_by=actor,
                updated_by=actor,
            )
    except IntegrityError as exc:
        if MeasurementProfile.objects.filter(**profile_identity).exists():
            raise ValidationError(
                {"profile": "A profile already exists for this person and garment."}
            ) from exc
        raise
    except DjangoValidationError as exc:
        if MeasurementProfile.objects.filter(**profile_identity).exists():
            raise ValidationError(
                {"profile": "A profile already exists for this person and garment."}
            ) from exc
        raise ValidationError(
            exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        ) from exc
    return profile


def _allowed_definitions(*, shop, profile, definition_ids):
    if len(definition_ids) != len(set(definition_ids)):
        raise ValidationError({"values": "A definition may appear only once per set."})
    definitions = list(
        MeasurementDefinition.objects.filter(pk__in=definition_ids, is_active=True)
        .filter(Q(tenant__isnull=True) | Q(tenant=shop))
        .prefetch_related("translations", "mappings__variant")
    )
    if len(definitions) != len(definition_ids):
        raise NotFound()
    by_id = {item.pk: item for item in definitions}
    for definition_id in definition_ids:
        definition = by_id[definition_id]
        mappings = definition.mappings.filter(
            family=profile.family, deleted__isnull=True
        )
        applicable = mappings.filter(variant__isnull=True).exists()
        if profile.variant_id:
            applicable = (
                applicable or mappings.filter(variant_id=profile.variant_id).exists()
            )
        if not applicable:
            raise ValidationError(
                {"values": "Definition is not available for this garment."}
            )
    return by_id


def _create_value_snapshots(*, measurement_value, definition):
    translations = list(definition.translations.filter(deleted__isnull=True))
    english = next((item for item in translations if item.locale == "en"), None)
    label = (
        english.name
        if english
        else definition.code.replace("-", " ").replace("_", " ").title()
    )
    measurement_value.definition_code_snapshot = definition.code
    measurement_value.label_snapshot = label
    measurement_value.save()
    MeasurementValueTranslationSnapshot.objects.bulk_create(
        [
            MeasurementValueTranslationSnapshot(
                value_record=measurement_value,
                locale=item.locale,
                name=item.name,
                created_by=measurement_value.created_by,
                updated_by=measurement_value.created_by,
            )
            for item in translations
        ]
    )


def _next_version(profile):
    return (
        profile.sets.order_by("-version").values_list("version", flat=True).first() or 0
    ) + 1


@transaction.atomic
def create_measurement_set(*, shop_id, actor, profile_id, values):
    shop, _membership = require_measurement_access(
        shop_id, actor, write=True, lock=True
    )
    profile = (
        MeasurementProfile.objects.select_for_update()
        .filter(pk=profile_id, tenant=shop, deleted__isnull=True)
        .first()
    )
    if profile is None:
        raise NotFound()
    ids = [item["definition_id"] for item in values]
    if not values:
        raise ValidationError({"values": "Provide at least one measurement value."})
    definitions = _allowed_definitions(shop=shop, profile=profile, definition_ids=ids)
    measurement_set = MeasurementSet.objects.create(
        profile=profile,
        version=_next_version(profile),
        created_by=actor,
        updated_by=actor,
    )
    for item in values:
        definition = definitions[item["definition_id"]]
        record = MeasurementValue(
            measurement_set=measurement_set,
            definition=definition,
            value=item["value"],
            unit=item["unit"],
            created_by=actor,
            updated_by=actor,
        )
        _create_value_snapshots(measurement_value=record, definition=definition)
    return measurement_set


@transaction.atomic
def copy_measurement_set(*, shop_id, actor, profile_id, source_set_id):
    shop, _membership = require_measurement_access(
        shop_id, actor, write=True, lock=True
    )
    profile = (
        MeasurementProfile.objects.select_for_update()
        .filter(pk=profile_id, tenant=shop, deleted__isnull=True)
        .first()
    )
    if profile is None:
        raise NotFound()
    source = (
        MeasurementSet.objects.select_for_update()
        .filter(pk=source_set_id, profile=profile)
        .prefetch_related("values__label_translations")
        .first()
    )
    if source is None:
        raise NotFound()
    duplicate = MeasurementSet.objects.create(
        profile=profile,
        version=_next_version(profile),
        copied_from=source,
        created_by=actor,
        updated_by=actor,
    )
    for original in source.values.all():
        copied = MeasurementValue.objects.create(
            measurement_set=duplicate,
            definition=original.definition,
            definition_code_snapshot=original.definition_code_snapshot,
            label_snapshot=original.label_snapshot,
            value=original.value,
            unit=original.unit,
            created_by=actor,
            updated_by=actor,
        )
        MeasurementValueTranslationSnapshot.objects.bulk_create(
            [
                MeasurementValueTranslationSnapshot(
                    value_record=copied,
                    locale=translation.locale,
                    name=translation.name,
                    created_by=actor,
                    updated_by=actor,
                )
                for translation in original.label_translations.all()
            ]
        )
    return duplicate


@transaction.atomic
def create_measurement_definition(
    *, shop_id, actor, code, group_code, sort_order, translations, mappings
):
    shop, _membership = require_measurement_access(
        shop_id, actor, write=True, lock=True
    )
    if MeasurementDefinition.objects.filter(
        tenant=shop, code=code, deleted__isnull=True
    ).exists():
        raise ValidationError(
            {"code": "A definition with this Shop-local code already exists."}
        )
    definition = MeasurementDefinition.objects.create(
        tenant=shop,
        code=code,
        group_code=group_code,
        sort_order=sort_order,
        created_by=actor,
        updated_by=actor,
    )
    if not translations or not any(item["locale"] == "en" for item in translations):
        raise ValidationError({"translations": "English translation is required."})
    seen = set()
    for item in translations:
        if item["locale"] in seen:
            raise ValidationError({"translations": "Locales must be unique."})
        seen.add(item["locale"])
        MeasurementDefinitionTranslation.objects.create(
            definition=definition,
            **item,
            created_by=actor,
            updated_by=actor,
        )
    seen_mappings = set()
    for item in mappings:
        family = (
            GarmentFamily.objects.select_for_update()
            .filter(pk=item["family_id"], status=GarmentFamily.Status.ACTIVE)
            .first()
        )
        if family is None:
            raise ValidationError({"mappings": "Unknown garment family."})
        variant = None
        if item.get("variant_id"):
            variant = (
                GarmentVariant.objects.select_for_update()
                .filter(pk=item["variant_id"], family=family, is_active=True)
                .filter(Q(tenant__isnull=True) | Q(tenant=shop))
                .first()
            )
            if variant is None:
                raise ValidationError(
                    {"mappings": "Variant is unavailable for this Shop and family."}
                )
        key = (family.pk, variant.pk if variant else None)
        if key in seen_mappings:
            raise ValidationError({"mappings": "Mappings must be unique."})
        seen_mappings.add(key)
        MeasurementDefinitionMapping.objects.create(
            definition=definition,
            family=family,
            variant=variant,
            created_by=actor,
            updated_by=actor,
        )
    return definition


@transaction.atomic
def archive_measurement_definition(*, shop_id, actor, definition_id):
    shop, _membership = require_measurement_access(
        shop_id, actor, write=True, archive=True, lock=True
    )
    definition = (
        MeasurementDefinition.objects.select_for_update()
        .filter(pk=definition_id, tenant=shop, deleted__isnull=True)
        .first()
    )
    if definition is None:
        raise NotFound()
    definition.is_active = False
    definition.updated_by = actor
    definition.save(update_fields=("is_active", "updated_by", "updated_at"))
    return definition


@transaction.atomic
def create_material(*, shop_id, actor, **fields):
    shop, _membership = require_material_access(shop_id, actor, write=True, lock=True)
    try:
        with transaction.atomic():
            return Material.objects.create(
                tenant=shop, created_by=actor, updated_by=actor, **fields
            )
    except IntegrityError as exc:
        raise ValidationError(
            {"code": "This Shop-local material code is already in use."}
        ) from exc


@transaction.atomic
def update_material(*, shop_id, actor, material_id, values):
    shop, _membership = require_material_access(shop_id, actor, write=True, lock=True)
    material = (
        Material.objects.select_for_update()
        .filter(
            pk=material_id,
            tenant=shop,
            status=Material.Status.ACTIVE,
            deleted__isnull=True,
        )
        .first()
    )
    if material is None:
        raise NotFound()
    try:
        with transaction.atomic():
            for field, value in values.items():
                setattr(material, field, value)
            material.updated_by = actor
            material.save()
    except IntegrityError as exc:
        raise ValidationError(
            {"code": "This Shop-local material code is already in use."}
        ) from exc
    return material


@transaction.atomic
def archive_material(*, shop_id, actor, material_id):
    shop, _membership = require_material_access(shop_id, actor, write=True, lock=True)
    material = (
        Material.objects.select_for_update()
        .filter(pk=material_id, tenant=shop, deleted__isnull=True)
        .first()
    )
    if material is None:
        raise NotFound()
    balance = (
        InventoryBalance.objects.select_for_update()
        .filter(material=material, tenant=shop, deleted__isnull=True)
        .first()
    )
    if balance and (balance.on_hand != 0 or balance.reserved != 0):
        raise ValidationError(
            {
                "status": [
                    ErrorDetail(
                        "Stock must be zero before this item can be archived.",
                        code="inventory_stock_remaining",
                    )
                ]
            }
        )
    material.status = Material.Status.ARCHIVED
    material.updated_by = actor
    material.save(update_fields=("status", "updated_by", "updated_at"))
    return material
