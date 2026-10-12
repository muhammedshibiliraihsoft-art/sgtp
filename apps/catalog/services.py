"""Transactional catalog/design operations and publication policy."""

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
import uuid
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.catalog.images import MAX_BATCH_FILES, optimize_reference
from apps.catalog.models import (
    Design,
    DesignReference,
    DesignSelection,
    DesignSelectionImage,
    DesignSelectionTranslation,
    DesignVersion,
    DesignVersionTranslation,
    FamilyOptionGroup,
    GarmentFamily,
    GarmentFamilyTranslation,
    GarmentVariant,
    GarmentVariantTranslation,
    OptionGroup,
    StyleOption,
    StyleOptionImage,
    StyleOptionTranslation,
)
from apps.tenants.models import MembershipWorkFunction, Tenant, TenantMember
from apps.tenants.policy import ShopRolePolicy


def _main_supplier(actor):
    if not ShopRolePolicy.is_main_supplier_admin(actor):
        raise PermissionDenied()


@transaction.atomic
def update_family_translations(*, family_id, translations, actor):
    _main_supplier(actor)
    try:
        family = GarmentFamily.objects.select_for_update().get(
            pk=family_id, tenant__isnull=True
        )
    except (GarmentFamily.DoesNotExist, ValueError):
        raise NotFound() from None

    existing = {
        row.locale: row
        for row in GarmentFamilyTranslation.objects.select_for_update().filter(
            family=family
        )
    }
    for item in translations:
        values = dict(item)
        current = existing.get(values["locale"])
        if current:
            current.name = values["name"]
            current.description = values.get("description", current.description)
            current.updated_by = actor
            current.save(
                update_fields=("name", "description", "updated_by", "updated_at")
            )
        else:
            GarmentFamilyTranslation.objects.create(
                family=family,
                created_by=actor,
                updated_by=actor,
                description=values.get("description", ""),
                **{key: value for key, value in values.items() if key != "description"},
            )

    if not family.translations.filter(locale="en").exists():
        raise ValidationError({"translations": "An English family name is required."})
    family.updated_by = actor
    family.save(update_fields=("updated_by", "updated_at"))
    return family


def replace_global_family_option_groups(*, family, option_group_mappings, actor):
    """Replace one global family's ordered group mappings; caller owns transaction/lock."""
    mappings = list(option_group_mappings)
    ids = [item["option_group_id"] for item in mappings]
    groups = list(OptionGroup.objects.filter(pk__in=ids, tenant__isnull=True))
    groups_by_id = {group.pk: group for group in groups}
    if len(groups_by_id) != len(ids):
        raise ValidationError({"option_groups": "Unknown global option group."})

    FamilyOptionGroup.objects.filter(family=family).delete()
    FamilyOptionGroup.objects.bulk_create(
        [
            FamilyOptionGroup(
                family=family,
                option_group=groups_by_id[item["option_group_id"]],
                sort_order=item["sort_order"],
                selection_mode=item["selection_mode"],
                is_required=item["is_required"],
                created_by=actor,
                updated_by=actor,
            )
            for item in mappings
        ]
    )


@transaction.atomic
def update_global_family_configuration(
    *, family_id, translations=None, option_group_mappings=None, actor
):
    """Apply the editable Global Catalog family fields in one locked transaction."""
    _main_supplier(actor)
    try:
        family = GarmentFamily.objects.select_for_update().get(
            pk=family_id, tenant__isnull=True
        )
    except (GarmentFamily.DoesNotExist, ValueError):
        raise NotFound() from None

    if translations is not None:
        update_family_translations(
            family_id=family.pk, translations=translations, actor=actor
        )
    if option_group_mappings is not None:
        replace_global_family_option_groups(
            family=family, option_group_mappings=option_group_mappings, actor=actor
        )
    return family


@transaction.atomic
def set_family_status(*, family_id, status, actor):
    _main_supplier(actor)
    try:
        family = GarmentFamily.objects.select_for_update().get(
            pk=family_id, tenant__isnull=True
        )
    except (GarmentFamily.DoesNotExist, ValueError):
        raise NotFound() from None
    if status not in GarmentFamily.Status.values:
        raise ValidationError({"status": "Invalid family status."})
    family.status = status
    family.updated_by = actor
    family.save(update_fields=("status", "updated_by", "updated_at"))
    return family


def _replace_variant_translations(*, variant, translations, actor):
    values_by_locale = {item["locale"]: item for item in translations}
    if "en" not in values_by_locale:
        raise ValidationError({"translations": "An English variant name is required."})

    current = {
        row.locale: row
        for row in GarmentVariantTranslation.objects.select_for_update().filter(
            variant=variant
        )
    }
    for locale, values in values_by_locale.items():
        translation = current.get(locale)
        if translation:
            translation.name = values["name"]
            translation.description = values.get("description", "")
            translation.updated_by = actor
            translation.save(
                update_fields=("name", "description", "updated_by", "updated_at")
            )
        else:
            GarmentVariantTranslation.objects.create(
                variant=variant,
                locale=locale,
                name=values["name"],
                description=values.get("description", ""),
                created_by=actor,
                updated_by=actor,
            )
    for locale, translation in current.items():
        if locale not in values_by_locale:
            translation.delete()


@transaction.atomic
def create_shop_variant(*, shop_id, actor, family_id, code, translations):
    shop, _membership = _shop_actor(shop_id=shop_id, actor=actor, write=True)
    family = (
        GarmentFamily.objects.select_for_update()
        .filter(
            pk=family_id,
            status=GarmentFamily.Status.ACTIVE,
        )
        .filter(Q(tenant__isnull=True) | Q(tenant=shop))
        .first()
    )
    if family is None:
        raise NotFound()
    variant = GarmentVariant.objects.create(
        tenant=shop,
        family=family,
        code=code,
        is_default=False,
        is_active=True,
        created_by=actor,
        updated_by=actor,
    )
    _replace_variant_translations(
        variant=variant, translations=translations, actor=actor
    )
    return variant


def _locked_shop_variant(*, shop, variant_id):
    initial = (
        GarmentVariant.objects.filter(tenant=shop, pk=variant_id)
        .values("family_id")
        .first()
    )
    if initial is None:
        raise NotFound()
    GarmentFamily.objects.select_for_update().get(pk=initial["family_id"])
    variant = (
        GarmentVariant.objects.select_for_update()
        .filter(tenant=shop, pk=variant_id)
        .select_related("family")
        .first()
    )
    if variant is None:
        raise NotFound()
    return variant


@transaction.atomic
def update_shop_variant(*, shop_id, actor, variant_id, translations):
    shop, _membership = _shop_actor(shop_id=shop_id, actor=actor, write=True)
    variant = _locked_shop_variant(shop=shop, variant_id=variant_id)
    _replace_variant_translations(
        variant=variant, translations=translations, actor=actor
    )
    variant.updated_by = actor
    variant.save(update_fields=("updated_by", "updated_at"))
    return variant


@transaction.atomic
def set_shop_variant_active(*, shop_id, actor, variant_id, is_active):
    shop, _membership = _shop_actor(shop_id=shop_id, actor=actor, write=True)
    variant = _locked_shop_variant(shop=shop, variant_id=variant_id)
    if is_active and variant.family.status != GarmentFamily.Status.ACTIVE:
        raise ValidationError(
            {"variant": "A variant under an archived family cannot be reactivated."}
        )
    variant.is_active = is_active
    variant.updated_by = actor
    variant.save(update_fields=("is_active", "updated_by", "updated_at"))
    return variant


@transaction.atomic
def create_global_variant(*, actor, family_id, code, translations):
    _main_supplier(actor)
    family = (
        GarmentFamily.objects.select_for_update()
        .filter(
            pk=family_id,
            status=GarmentFamily.Status.ACTIVE,
            tenant__isnull=True,
        )
        .first()
    )
    if family is None:
        raise NotFound()
    variant = GarmentVariant.objects.create(
        tenant=None,
        family=family,
        code=code,
        is_default=False,
        is_active=True,
        created_by=actor,
        updated_by=actor,
    )
    _replace_variant_translations(
        variant=variant, translations=translations, actor=actor
    )
    return variant


@transaction.atomic
def update_global_variant(*, actor, variant_id, translations):
    _main_supplier(actor)
    initial = (
        GarmentVariant.objects.filter(tenant__isnull=True, pk=variant_id)
        .values("family_id")
        .first()
    )
    if initial is None:
        raise NotFound()
    GarmentFamily.objects.select_for_update().get(pk=initial["family_id"])
    variant = (
        GarmentVariant.objects.select_for_update()
        .filter(tenant__isnull=True, pk=variant_id)
        .select_related("family")
        .first()
    )
    if variant is None:
        raise NotFound()
    _replace_variant_translations(
        variant=variant, translations=translations, actor=actor
    )
    variant.updated_by = actor
    variant.save(update_fields=("updated_by", "updated_at"))
    return variant


@transaction.atomic
def set_global_variant_active(*, actor, variant_id, is_active):
    _main_supplier(actor)
    initial = (
        GarmentVariant.objects.filter(tenant__isnull=True, pk=variant_id)
        .values("family_id")
        .first()
    )
    if initial is None:
        raise NotFound()
    family = GarmentFamily.objects.select_for_update().get(pk=initial["family_id"])
    variant = (
        GarmentVariant.objects.select_for_update()
        .filter(tenant__isnull=True, pk=variant_id)
        .select_related("family")
        .first()
    )
    if variant is None:
        raise NotFound()
    if is_active and family.status != GarmentFamily.Status.ACTIVE:
        raise ValidationError(
            {"variant": "A variant under an archived family cannot be reactivated."}
        )
    variant.is_active = is_active
    if not is_active and variant.is_default:
        variant.is_default = False
    variant.updated_by = actor
    variant.save(update_fields=("is_active", "is_default", "updated_by", "updated_at"))
    return variant


@transaction.atomic
def set_global_variant_default(*, actor, variant_id):
    _main_supplier(actor)
    initial = (
        GarmentVariant.objects.filter(tenant__isnull=True, pk=variant_id)
        .values("family_id")
        .first()
    )
    if initial is None:
        raise NotFound()
    family = GarmentFamily.objects.select_for_update().get(pk=initial["family_id"])
    if family.status != GarmentFamily.Status.ACTIVE:
        raise ValidationError({"variant": "The variant family must be active."})
    variant = (
        GarmentVariant.objects.select_for_update()
        .filter(tenant__isnull=True, pk=variant_id)
        .select_related("family")
        .first()
    )
    if variant is None:
        raise NotFound()
    if not variant.is_active:
        raise ValidationError({"variant": "Only active variants can be default."})
    previous_defaults = (
        GarmentVariant.objects.select_for_update()
        .filter(tenant__isnull=True, family=family, is_default=True)
        .exclude(pk=variant.pk)
    )
    for previous in previous_defaults:
        previous.is_default = False
        previous.updated_by = actor
        previous.save(update_fields=("is_default", "updated_by", "updated_at"))
    variant.is_default = True
    variant.updated_by = actor
    variant.save(update_fields=("is_default", "updated_by", "updated_at"))
    return variant


@transaction.atomic
def upload_family_image(*, family_id, upload, actor):
    _main_supplier(actor)
    try:
        family = GarmentFamily.objects.select_for_update().get(pk=family_id)
    except (GarmentFamily.DoesNotExist, ValueError):
        raise NotFound() from None

    optimized, byte_size, width, height = optimize_reference(
        upload, error_field="image"
    )
    storage = GarmentFamily._meta.get_field("image").storage
    previous_name = family.image.name if family.image else ""
    try:
        family.image.save(optimized.name, optimized, save=False)
        new_name = family.image.name
        family.image_mime_type = "image/webp"
        family.image_byte_size = byte_size
        family.image_width = width
        family.image_height = height
        family.updated_by = actor
        family.save(
            update_fields=(
                "image",
                "image_mime_type",
                "image_byte_size",
                "image_width",
                "image_height",
                "updated_by",
                "updated_at",
            )
        )
    except Exception:
        if family.image and family.image.name and family.image.name != previous_name:
            storage.delete(family.image.name)
        raise

    if previous_name and previous_name != new_name:
        transaction.on_commit(lambda: storage.delete(previous_name))
    return family


@transaction.atomic
def remove_family_image(*, family_id, actor):
    _main_supplier(actor)
    try:
        family = GarmentFamily.objects.select_for_update().get(pk=family_id)
    except (GarmentFamily.DoesNotExist, ValueError):
        raise NotFound() from None
    previous_name = family.image.name if family.image else ""
    family.image = ""
    family.image_mime_type = ""
    family.image_byte_size = None
    family.image_width = None
    family.image_height = None
    family.updated_by = actor
    family.save(
        update_fields=(
            "image",
            "image_mime_type",
            "image_byte_size",
            "image_width",
            "image_height",
            "updated_by",
            "updated_at",
        )
    )
    if previous_name:
        transaction.on_commit(
            lambda: GarmentFamily._meta.get_field("image").storage.delete(previous_name)
        )
    return family


def _actor_active(actor):
    return bool(actor and actor.is_authenticated and actor.is_active)


def _shop_actor(*, shop_id, actor, write=False):
    if not _actor_active(actor):
        raise PermissionDenied()
    try:
        shop = Tenant.objects.select_for_update().get(pk=shop_id, is_active=True)
    except (Tenant.DoesNotExist, ValueError):
        raise NotFound() from None
    if ShopRolePolicy.is_main_supplier_admin(actor):
        return shop, None
    membership = (
        TenantMember.objects.select_for_update()
        .filter(tenant=shop, user=actor, is_active=True, deleted__isnull=True)
        .first()
    )
    if membership is None:
        raise NotFound()
    if write and membership.role == "VIEWER":
        raise PermissionDenied()
    return shop, membership


def _can_publish_shop_design(membership):
    if membership is None:
        return False
    if membership.role == "ADMIN":
        return True
    return (
        membership.role == "STAFF"
        and MembershipWorkFunction.objects.filter(
            membership=membership,
            function_code="STITCHING",
            deleted__isnull=True,
        ).exists()
    )


def _clone_version_content(source_version, target_version, actor, *, clone_options):
    storage = DesignReference._meta.get_field("image").storage
    created_names = []
    option_map = {}
    try:
        for translation in source_version.translations.all():
            DesignVersionTranslation.objects.create(
                version=target_version,
                locale=translation.locale,
                name=translation.name,
                description=translation.description,
                created_by=actor,
                updated_by=actor,
            )
        selections = source_version.selections.prefetch_related(
            "reference_images__source_image",
            "style_option__translations",
            "style_option__reference_images",
        )
        for selection in selections:
            option = selection.style_option
            target_option = option
            image_map = {}
            if clone_options:
                if option.pk not in option_map:
                    copied_option = StyleOption.objects.create(
                        tenant=target_version.design.tenant,
                        option_group=option.option_group,
                        code=f"{option.code[:42]}-copy-{uuid.uuid4().hex[:16]}",
                        source_style_option=option,
                        is_active=option.is_active,
                        created_by=actor,
                        updated_by=actor,
                    )
                    for translation in option.translations.all():
                        copied_option.translations.create(
                            locale=translation.locale,
                            name=translation.name,
                            description=translation.description,
                            created_by=actor,
                            updated_by=actor,
                        )
                    for image in option.reference_images.filter(is_primary=True):
                        with image.image.storage.open(image.image.name, "rb") as handle:
                            payload = handle.read()
                        copied_image = StyleOptionImage(
                            style_option=copied_option,
                            image=ContentFile(
                                payload, name=image.image.name.rsplit("/", 1)[-1]
                            ),
                            mime_type=image.mime_type,
                            byte_size=image.byte_size,
                            width=image.width,
                            height=image.height,
                            is_primary=True,
                            sort_order=image.sort_order,
                            alt_text=image.alt_text,
                            created_by=actor,
                            updated_by=actor,
                        )
                        copied_image.save()
                        created_names.append(copied_image.image.name)
                        image_map[image.pk] = copied_image
                    option_map[option.pk] = (copied_option, image_map)
                target_option, image_map = option_map[option.pk]
            copied_selection = DesignSelection.objects.create(
                version=target_version,
                option_group=selection.option_group,
                style_option=target_option,
                selected_code=selection.selected_code,
                selected_name_en=selection.selected_name_en,
                created_by=actor,
                updated_by=actor,
            )
            for link in selection.reference_images.all():
                DesignSelectionImage.objects.create(
                    selection=copied_selection,
                    source_image=image_map.get(link.source_image_id, link.source_image),
                    created_by=actor,
                    updated_by=actor,
                )
            for translation in selection.translations.all():
                DesignSelectionTranslation.objects.create(
                    selection=copied_selection,
                    locale=translation.locale,
                    name=translation.name,
                    description=translation.description,
                    created_by=actor,
                    updated_by=actor,
                )
        for reference in source_version.references.all():
            with reference.image.storage.open(reference.image.name, "rb") as handle:
                payload = handle.read()
            copied_reference = DesignReference(
                version=target_version,
                image=ContentFile(
                    payload, name=reference.image.name.rsplit("/", 1)[-1]
                ),
                mime_type=reference.mime_type,
                byte_size=reference.byte_size,
                width=reference.width,
                height=reference.height,
                sort_order=reference.sort_order,
                alt_text=reference.alt_text,
                created_by=actor,
                updated_by=actor,
            )
            copied_reference.save()
            created_names.append(copied_reference.image.name)
    except Exception:
        for name in created_names:
            storage.delete(name)
        raise


@transaction.atomic
def create_design(
    *,
    shop_id,
    actor,
    family,
    variant=None,
    name,
    source=None,
    translations=None,
    selection_options=(),
    idempotency_key=None,
):
    shop, _membership = _shop_actor(shop_id=shop_id, actor=actor, write=True)
    try:
        family = GarmentFamily.objects.select_for_update().get(
            pk=family.pk, status=GarmentFamily.Status.ACTIVE
        )
    except GarmentFamily.DoesNotExist:
        raise ValidationError(
            {"family_id": "Select an active garment family."}
        ) from None
    if family.tenant_id not in (None, shop.pk):
        raise ValidationError({"family_id": "Family is not available to this Shop."})
    if variant is not None:
        variant = (
            GarmentVariant.objects.select_for_update()
            .filter(pk=variant.pk, family=family, is_active=True)
            .filter(Q(tenant__isnull=True) | Q(tenant=shop))
            .first()
        )
        if variant is None:
            raise ValidationError(
                {
                    "variant_id": "Select an active variant available to this Shop and family."
                }
            )
    if idempotency_key:
        existing = (
            Design.objects.select_for_update()
            .filter(tenant=shop, client_request_id=idempotency_key)
            .first()
        )
        if existing is not None:
            draft = existing.versions.filter(status=DesignVersion.Status.DRAFT).first()
            existing_name = (
                draft.translations.filter(locale="en")
                .values_list("name", flat=True)
                .first()
                if draft
                else None
            )
            existing_options = set(
                draft.selections.values_list("style_option_id", flat=True)
                if draft
                else ()
            )
            requested_options = {option.pk for option in selection_options}
            if (
                existing.family_id != family.pk
                or existing.variant_id != getattr(variant, "pk", None)
                or existing_name != name.strip()
                or existing_options != requested_options
            ):
                raise ValidationError(
                    {
                        "idempotency_key": "This retry key was already used for a different design request."
                    }
                )
            return existing
    design = Design.objects.create(
        tenant=shop,
        family=family,
        variant=variant,
        source_design=source,
        client_request_id=idempotency_key,
        created_by=actor,
        updated_by=actor,
    )
    version = DesignVersion.objects.create(design=design, number=1, created_by=actor)
    items = translations or [{"locale": "en", "name": name.strip(), "description": ""}]
    for item in items:
        DesignVersionTranslation.objects.create(
            version=version, created_by=actor, updated_by=actor, **item
        )
    for option in selection_options:
        add_selection(
            shop_id=shop.pk,
            actor=actor,
            version_id=version.pk,
            option=option,
        )
    return design


@transaction.atomic
def initialize_shop_default_catalog(*, shop, actor, family_ids=None):
    """Materialize current Back Office defaults, optionally for selected families."""
    families_query = GarmentFamily.objects.filter(
        tenant__isnull=True, status=GarmentFamily.Status.ACTIVE
    )
    if family_ids is not None:
        families_query = families_query.filter(pk__in=family_ids)
    families = list(
        families_query.prefetch_related(
            "translations", "familyoptiongroup_set__option_group"
        )
    )
    if family_ids is not None and len(families) != len(set(family_ids)):
        raise NotFound()
    family_map = {}
    for source in families:
        family = GarmentFamily.objects.create(
            tenant=shop,
            template_source=source,
            code=source.code,
            status=source.status,
            created_by=actor,
            updated_by=actor,
        )
        GarmentFamilyTranslation.objects.bulk_create(
            [
                GarmentFamilyTranslation(
                    family=family,
                    locale=item.locale,
                    name=item.name,
                    description=item.description,
                    created_by=actor,
                    updated_by=actor,
                )
                for item in source.translations.all()
            ]
        )
        family_map[source.pk] = family

    variant_map = {}
    for source in GarmentVariant.objects.filter(
        tenant__isnull=True,
        is_active=True,
        family_id__in=family_map,
    ).select_related("family").prefetch_related("translations"):
        variant = GarmentVariant.objects.create(
            tenant=shop,
            family=family_map[source.family_id],
            template_source=source,
            code=source.code,
            is_default=source.is_default,
            is_active=source.is_active,
            created_by=actor,
            updated_by=actor,
        )
        GarmentVariantTranslation.objects.bulk_create(
            [
                GarmentVariantTranslation(
                    variant=variant,
                    locale=item.locale,
                    name=item.name,
                    description=item.description,
                    created_by=actor,
                    updated_by=actor,
                )
                for item in source.translations.all()
            ]
        )
        variant_map[source.pk] = variant

    FamilyOptionGroup.objects.bulk_create(
        [
            FamilyOptionGroup(
                family=family_map[row.family_id],
                option_group_id=row.option_group_id,
                sort_order=row.sort_order,
                selection_mode=row.selection_mode,
                is_required=row.is_required,
                created_by=actor,
                updated_by=actor,
            )
            for row in FamilyOptionGroup.objects.filter(
                family_id__in=family_map
            ).select_related("family")
            if row.family_id in family_map
        ]
    )

    from apps.catalog.models import DesignVersion

    source_designs = (
        Design.objects.filter(
            tenant__isnull=True,
            status=Design.Status.ACTIVE,
            family_id__in=family_map,
            versions__status=DesignVersion.Status.PUBLISHED,
        )
        .distinct()
        .prefetch_related("versions__translations", "versions__selections")
    )
    for source in source_designs:
        source_version = (
            source.versions.filter(status=DesignVersion.Status.PUBLISHED)
            .order_by("-number")
            .first()
        )
        if source_version is None:
            continue
        target_variant = (
            variant_map.get(source.variant_id) if source.variant_id else None
        )
        copy_design_version(
            shop_id=shop.pk,
            actor=actor,
            family=family_map[source.family_id],
            variant=target_variant,
            name=(
                source_version.translations.filter(locale="en")
                .values_list("name", flat=True)
                .first()
                or source.family.code
            ),
            source=source,
            source_version=source_version,
            is_default_seeded=True,
        )
    return len(family_map)


@transaction.atomic
def materialize_shop_default_family(*, shop_id, actor, family_id):
    """Create one Shop-local working copy when a legacy Shop chooses to edit a default."""
    shop, _membership = _shop_actor(shop_id=shop_id, actor=actor, write=True)
    try:
        source = GarmentFamily.objects.select_for_update().get(
            pk=family_id,
            tenant__isnull=True,
            status=GarmentFamily.Status.ACTIVE,
        )
    except (GarmentFamily.DoesNotExist, ValueError):
        raise NotFound() from None

    existing = GarmentFamily.objects.filter(
        tenant=shop, template_source=source
    ).first()
    if existing:
        if existing.status != GarmentFamily.Status.ACTIVE:
            raise ValidationError(
                {"family": "This default is archived in the Shop; restore it first."}
            )
        return existing

    initialize_shop_default_catalog(shop=shop, actor=actor, family_ids=[source.pk])
    return GarmentFamily.objects.get(tenant=shop, template_source=source)


@transaction.atomic
def set_shop_default_family_status(*, shop_id, actor, family_id, is_active):
    """Archive or restore one Shop-local default family, never its source."""
    shop, _membership = _shop_actor(shop_id=shop_id, actor=actor, write=True)
    try:
        family = GarmentFamily.objects.select_for_update().get(
            pk=family_id, tenant=shop, template_source__isnull=False
        )
    except (GarmentFamily.DoesNotExist, ValueError):
        raise NotFound() from None

    if not is_active:
        family.status = GarmentFamily.Status.ARCHIVED
        family.updated_by = actor
        family.save(update_fields=("status", "updated_by", "updated_at"))
        Design.objects.filter(
            tenant=shop,
            family=family,
            is_default_seeded=True,
            status=Design.Status.ACTIVE,
        ).update(
            status=Design.Status.ARCHIVED,
            updated_by=actor,
            updated_at=timezone.now(),
        )
        return family

    try:
        source = GarmentFamily.objects.get(
            pk=family.template_source_id,
            tenant__isnull=True,
            status=GarmentFamily.Status.ACTIVE,
        )
    except GarmentFamily.DoesNotExist:
        raise ValidationError(
            {"family": "The current Back Office default is not active."}
        ) from None

    source_translations = {row.locale: row for row in source.translations.all()}
    local_translations = {row.locale: row for row in family.translations.all()}
    for locale, row in source_translations.items():
        local = local_translations.pop(locale, None)
        if local:
            local.name = row.name
            local.description = row.description
            local.updated_by = actor
            local.save(update_fields=("name", "description", "updated_by", "updated_at"))
        else:
            GarmentFamilyTranslation.objects.create(
                family=family,
                locale=locale,
                name=row.name,
                description=row.description,
                created_by=actor,
                updated_by=actor,
            )
    for obsolete in local_translations.values():
        obsolete.delete()

    FamilyOptionGroup.objects.filter(family=family).delete()
    FamilyOptionGroup.objects.bulk_create(
        [
            FamilyOptionGroup(
                family=family,
                option_group=row.option_group,
                sort_order=row.sort_order,
                selection_mode=row.selection_mode,
                is_required=row.is_required,
                created_by=actor,
                updated_by=actor,
            )
            for row in FamilyOptionGroup.objects.filter(family=source).select_related(
                "option_group"
            )
        ]
    )

    source_variants = {
        row.pk: row
        for row in GarmentVariant.objects.filter(family=source, tenant__isnull=True)
    }
    local_variants = {
        row.template_source_id: row
        for row in GarmentVariant.objects.filter(
            family=family, tenant=shop, template_source__isnull=False
        ).prefetch_related("translations")
    }
    for source_id, source_variant in source_variants.items():
        local = local_variants.pop(source_id, None)
        if not source_variant.is_active:
            if local:
                local.is_active = False
                local.updated_by = actor
                local.save(update_fields=("is_active", "updated_by", "updated_at"))
            continue
        if local is None:
            local = GarmentVariant.objects.create(
                tenant=shop,
                family=family,
                template_source=source_variant,
                code=source_variant.code,
                is_default=source_variant.is_default,
                is_active=True,
                created_by=actor,
                updated_by=actor,
            )
        else:
            local.is_active = True
            local.is_default = source_variant.is_default
            local.updated_by = actor
            local.save(update_fields=("is_active", "is_default", "updated_by", "updated_at"))
        current = {row.locale: row for row in local.translations.all()}
        for row in source_variant.translations.all():
            translation = current.pop(row.locale, None)
            if translation:
                translation.name = row.name
                translation.description = row.description
                translation.updated_by = actor
                translation.save(update_fields=("name", "description", "updated_by", "updated_at"))
            else:
                GarmentVariantTranslation.objects.create(
                    variant=local,
                    locale=row.locale,
                    name=row.name,
                    description=row.description,
                    created_by=actor,
                    updated_by=actor,
                )
        for obsolete in current.values():
            obsolete.delete()
    for obsolete in local_variants.values():
        obsolete.is_active = False
        obsolete.updated_by = actor
        obsolete.save(update_fields=("is_active", "updated_by", "updated_at"))

    family.status = GarmentFamily.Status.ACTIVE
    family.updated_by = actor
    family.save(update_fields=("status", "updated_by", "updated_at"))
    return family


def copy_design_version(
    *,
    shop_id,
    actor,
    family,
    variant,
    name,
    source,
    source_version,
    translations=None,
    is_default_seeded=False,
    target_design=None,
):
    shop, _membership = _shop_actor(shop_id=shop_id, actor=actor, write=True)
    if variant is not None:
        variant = (
            GarmentVariant.objects.select_for_update()
            .filter(pk=variant.pk, family=family, is_active=True)
            .filter(Q(tenant__isnull=True) | Q(tenant=shop))
            .first()
        )
    family_matches = source.family_id == family.pk or (
        family.tenant_id == shop.pk and family.template_source_id == source.family_id
    )
    variant_matches = source.variant_id == getattr(variant, "pk", None) or (
        source.variant_id is not None
        and variant is not None
        and variant.tenant_id == shop.pk
        and variant.template_source_id == source.variant_id
    )
    if not family_matches or not variant_matches:
        raise ValidationError(
            {"variant_id": "Copying must retain the source design's garment scope."}
        )
    if (
        source_version.design_id != source.pk
        or source_version.status != DesignVersion.Status.PUBLISHED
    ):
        raise NotFound()
    if source.tenant_id not in (None, shop.pk):
        raise NotFound()
    if target_design is None:
        design = Design.objects.create(
            tenant=shop,
            family=family,
            variant=variant,
            source_design=source,
            is_default_seeded=is_default_seeded,
            created_by=actor,
            updated_by=actor,
        )
        number = 1
    else:
        design = Design.objects.select_for_update().get(
            pk=target_design.pk, tenant=shop, source_design=source
        )
        target = design.versions.select_for_update().filter(
            status=DesignVersion.Status.DRAFT
        ).first()
        number = (
            target.number
            if target is not None
            else max(
                DesignVersion.all_objects.filter(design=design).values_list(
                    "number", flat=True
                ),
                default=0,
            )
            + 1
        )
    if target_design is None or target is None:
        target = DesignVersion.objects.create(
            design=design, number=number, created_by=actor, updated_by=actor
        )
    else:
        target.selections.all().delete()
        target.references.all().delete()
        target.translations.all().delete()
        target.updated_by = actor
        target.save(update_fields=("updated_by", "updated_at"))
    source_translations = list(source_version.translations.all())
    items = translations or [
        {
            "locale": row.locale,
            "name": name.strip() if row.locale == "en" else row.name,
            "description": row.description,
        }
        for row in source_translations
    ]
    if not any(item["locale"] == "en" for item in items):
        items.append({"locale": "en", "name": name.strip(), "description": ""})
    for item in items:
        DesignVersionTranslation.objects.create(
            version=target, created_by=actor, updated_by=actor, **item
        )
    style_map = {}
    storage = StyleOptionImage._meta.get_field("image").storage
    created_names = []
    try:
        for selection in source_version.selections.prefetch_related(
            "style_option__translations", "reference_images__source_image"
        ):
            original = selection.style_option
            if original.pk not in style_map:
                cloned = StyleOption.objects.create(
                    tenant=shop,
                    option_group=original.option_group,
                    code=f"{original.code[:42]}-copy-{uuid.uuid4().hex[:16]}",
                    source_style_option=original,
                    is_active=original.is_active,
                    created_by=actor,
                    updated_by=actor,
                )
                for translation in original.translations.all():
                    cloned.translations.create(
                        locale=translation.locale,
                        name=translation.name,
                        description=translation.description,
                        created_by=actor,
                        updated_by=actor,
                    )
                image_map = {}
                for image in original.reference_images.filter(is_primary=True):
                    with image.image.storage.open(image.image.name, "rb") as handle:
                        payload = handle.read()
                    cloned_image = StyleOptionImage(
                        style_option=cloned,
                        image=ContentFile(
                            payload, name=image.image.name.rsplit("/", 1)[-1]
                        ),
                        mime_type=image.mime_type,
                        byte_size=image.byte_size,
                        width=image.width,
                        height=image.height,
                        is_primary=True,
                        sort_order=image.sort_order,
                        alt_text=image.alt_text,
                        created_by=actor,
                        updated_by=actor,
                    )
                    cloned_image.save()
                    created_names.append(cloned_image.image.name)
                    image_map[image.pk] = cloned_image
                style_map[original.pk] = (cloned, image_map)
            cloned, image_map = style_map[original.pk]
            copied_selection = DesignSelection.objects.create(
                version=target,
                option_group=selection.option_group,
                style_option=cloned,
                selected_code=selection.selected_code,
                selected_name_en=selection.selected_name_en,
                created_by=actor,
                updated_by=actor,
            )
            for link in selection.reference_images.all():
                if link.source_image_id in image_map:
                    DesignSelectionImage.objects.create(
                        selection=copied_selection,
                        source_image=image_map[link.source_image_id],
                        created_by=actor,
                        updated_by=actor,
                    )
            for translation in selection.translations.all():
                DesignSelectionTranslation.objects.create(
                    selection=copied_selection,
                    locale=translation.locale,
                    name=translation.name,
                    description=translation.description,
                    created_by=actor,
                    updated_by=actor,
                )
        for reference in source_version.references.all():
            with reference.image.storage.open(reference.image.name, "rb") as handle:
                payload = handle.read()
            copied_reference = DesignReference(
                version=target,
                image=ContentFile(
                    payload, name=reference.image.name.rsplit("/", 1)[-1]
                ),
                mime_type=reference.mime_type,
                byte_size=reference.byte_size,
                width=reference.width,
                height=reference.height,
                sort_order=reference.sort_order,
                alt_text=reference.alt_text,
                created_by=actor,
                updated_by=actor,
            )
            copied_reference.save()
            created_names.append(copied_reference.image.name)
    except Exception:
        for name in created_names:
            storage.delete(name)
        raise
    return design


@transaction.atomic
def add_selection(*, shop_id, actor, version_id, option):
    shop, _membership = _shop_actor(shop_id=shop_id, actor=actor, write=True)
    try:
        version = (
            DesignVersion.objects.select_for_update()
            .select_related("design", "design__family")
            .get(
                pk=version_id, design__tenant=shop, design__status=Design.Status.ACTIVE
            )
        )
    except (DesignVersion.DoesNotExist, ValueError):
        raise NotFound() from None
    if version.status != DesignVersion.Status.DRAFT:
        raise ValidationError({"version": "Published versions are immutable."})
    if option.tenant_id not in (None, shop.pk):
        raise NotFound()
    family = GarmentFamily.objects.select_for_update().get(pk=version.design.family_id)
    mapping = FamilyOptionGroup.objects.filter(
        family=family, option_group_id=option.option_group_id
    ).first()
    if mapping is None:
        raise ValidationError(
            {"style_option": "This option group is not available for the garment."}
        )
    if (
        mapping.selection_mode == FamilyOptionGroup.SelectionMode.SINGLE
        and version.selections.filter(option_group_id=option.option_group_id)
        .exclude(style_option=option)
        .exists()
    ):
        raise ValidationError(
            {"style_option": "Only one option may be selected for this group."}
        )
    label = (
        option.translations.filter(locale="en").values_list("name", flat=True).first()
    )
    selection, created = DesignSelection.objects.get_or_create(
        version=version,
        option_group=option.option_group,
        style_option=option,
        defaults={
            "selected_code": option.code,
            "selected_name_en": label or option.code,
            "created_by": actor,
            "updated_by": actor,
        },
    )
    if created:
        DesignSelectionTranslation.objects.bulk_create(
            [
                DesignSelectionTranslation(
                    selection=selection,
                    locale=translation.locale,
                    name=translation.name,
                    description=translation.description,
                    created_by=actor,
                    updated_by=actor,
                )
                for translation in option.translations.all()
            ]
        )
        DesignSelectionImage.objects.bulk_create(
            [
                DesignSelectionImage(
                    selection=selection,
                    source_image=image,
                    created_by=actor,
                    updated_by=actor,
                )
                for image in option.reference_images.filter(is_primary=True)
            ]
        )
    return selection


@transaction.atomic
def update_selection(*, shop_id, actor, version_id, selection_id, option):
    """Replace a Draft selection while keeping its option group and Shop scope."""
    shop, _membership = _shop_actor(shop_id=shop_id, actor=actor, write=True)
    try:
        version = (
            DesignVersion.objects.select_for_update()
            .select_related("design")
            .get(
                pk=version_id,
                design__tenant=shop,
                design__status=Design.Status.ACTIVE,
            )
        )
        selection = DesignSelection.objects.select_for_update().get(
            pk=selection_id, version=version
        )
    except (DesignVersion.DoesNotExist, DesignSelection.DoesNotExist, ValueError):
        raise NotFound() from None
    if version.status != DesignVersion.Status.DRAFT:
        raise ValidationError({"version": "Published versions are immutable."})
    if option.tenant_id not in (None, shop.pk):
        raise NotFound()
    if option.option_group_id != selection.option_group_id:
        raise ValidationError(
            {"style_option": "Choose an option from the same configured garment part."}
        )
    if not FamilyOptionGroup.objects.filter(
        family=version.design.family, option_group_id=selection.option_group_id
    ).exists():
        raise ValidationError(
            {"style_option": "This option group is no longer configured for the garment."}
        )

    translations = list(option.translations.all())
    label = next((row.name for row in translations if row.locale == "en"), None)
    selection.style_option = option
    selection.selected_code = option.code
    selection.selected_name_en = label or option.code
    selection.updated_by = actor
    selection.save(
        update_fields=(
            "style_option",
            "selected_code",
            "selected_name_en",
            "updated_by",
            "updated_at",
        )
    )

    # Keep soft-deleted snapshot rows for recovery, reusing matching unique
    # rows where possible instead of hard-deleting or violating constraints.
    current_translations = {
        row.locale: row
        for row in DesignSelectionTranslation.all_objects.filter(selection=selection)
    }
    desired_translations = {row.locale: row for row in translations}
    for locale, row in current_translations.items():
        source = desired_translations.pop(locale, None)
        if source:
            row.name = source.name
            row.description = source.description
            row.updated_by = actor
            row.deleted = None
            row.deleted_by_cascade = False
            row.save()
        elif row.deleted is None:
            row.delete()
    for source in desired_translations.values():
        DesignSelectionTranslation.objects.create(
            selection=selection,
            locale=source.locale,
            name=source.name,
            description=source.description,
            created_by=actor,
            updated_by=actor,
        )

    current_images = {
        row.source_image_id: row
        for row in DesignSelectionImage.all_objects.filter(selection=selection)
    }
    desired_images = {
        image.pk: image
        for image in option.reference_images.filter(is_primary=True)
    }
    for image_id, row in current_images.items():
        image = desired_images.pop(image_id, None)
        if image:
            row.deleted = None
            row.deleted_by_cascade = False
            row.updated_by = actor
            row.save()
        elif row.deleted is None:
            row.delete()
    for image in desired_images.values():
        DesignSelectionImage.objects.create(
            selection=selection,
            source_image=image,
            created_by=actor,
            updated_by=actor,
        )
    return selection


def _validate_design_version_configuration(version):
    mappings = list(
        FamilyOptionGroup.objects.filter(family=version.design.family)
        .select_related("option_group")
        .order_by("sort_order", "id")
    )
    configured_group_ids = {mapping.option_group_id for mapping in mappings}
    selected_group_ids = set(
        version.selections.values_list("option_group_id", flat=True).distinct()
    )
    invalid_group_ids = selected_group_ids - configured_group_ids
    if invalid_group_ids:
        raise ValidationError(
            {
                "selections": "Selections must belong to a group configured for the family."
            }
        )
    for mapping in mappings:
        count = version.selections.filter(
            option_group_id=mapping.option_group_id
        ).count()
        if mapping.is_required and count == 0:
            raise ValidationError(
                {
                    "selections": f"Choose an option for required group '{mapping.option_group.code}'."
                }
            )
        if (
            mapping.selection_mode == FamilyOptionGroup.SelectionMode.SINGLE
            and count > 1
        ):
            raise ValidationError(
                {
                    "selections": f"Group '{mapping.option_group.code}' allows one option only."
                }
            )


@transaction.atomic
def publish_version(*, shop_id, actor, version_id):
    shop, membership = _shop_actor(shop_id=shop_id, actor=actor, write=True)
    if not _can_publish_shop_design(membership):
        raise PermissionDenied(
            "Only Shop ADMIN or a STAFF Tailor may publish a design."
        )
    try:
        version = (
            DesignVersion.objects.select_for_update()
            .select_related("design")
            .get(
                pk=version_id, design__tenant=shop, design__status=Design.Status.ACTIVE
            )
        )
    except (DesignVersion.DoesNotExist, ValueError):
        raise NotFound() from None
    if version.status != DesignVersion.Status.DRAFT:
        raise ValidationError({"version": "Only a Draft version can be published."})
    _validate_design_version_configuration(version)
    version.status = DesignVersion.Status.PUBLISHED
    version.published_at = timezone.now()
    version.published_by = actor
    version.updated_by = actor
    version.save()
    draft = DesignVersion.objects.create(
        design=version.design,
        number=version.number + 1,
        created_by=actor,
        updated_by=actor,
    )
    _clone_version_content(version, draft, actor, clone_options=False)
    return version, draft


@transaction.atomic
def create_global_design(*, actor, family, variant=None, name, translations=None):
    _main_supplier(actor)
    try:
        family = GarmentFamily.objects.select_for_update().get(
            pk=family.pk, status=GarmentFamily.Status.ACTIVE
        )
    except GarmentFamily.DoesNotExist:
        raise ValidationError(
            {"family_id": "Select an active garment family."}
        ) from None
    if variant is not None:
        variant = (
            GarmentVariant.objects.select_for_update()
            .filter(
                pk=variant.pk,
                tenant__isnull=True,
                family=family,
                is_active=True,
            )
            .first()
        )
        if variant is None:
            raise ValidationError(
                {"variant": "Select a global variant for this family."}
            )
    design = Design.objects.create(
        tenant=None,
        family=family,
        variant=variant,
        created_by=actor,
        updated_by=actor,
    )
    version = DesignVersion.objects.create(design=design, number=1, created_by=actor)
    items = translations or [{"locale": "en", "name": name.strip(), "description": ""}]
    for item in items:
        DesignVersionTranslation.objects.create(
            version=version, created_by=actor, updated_by=actor, **item
        )
    return design


@transaction.atomic
def publish_global_version(*, actor, design_id, version_id):
    if not ShopRolePolicy.is_main_supplier_admin(actor):
        raise PermissionDenied()
    try:
        version = (
            DesignVersion.objects.select_for_update()
            .select_related("design")
            .get(
                pk=version_id,
                design_id=design_id,
                design__tenant__isnull=True,
                design__status=Design.Status.ACTIVE,
            )
        )
    except (DesignVersion.DoesNotExist, ValueError):
        raise NotFound() from None
    if version.status != DesignVersion.Status.DRAFT:
        raise ValidationError({"version": "Only a Draft version can be published."})
    _validate_design_version_configuration(version)
    version.status = DesignVersion.Status.PUBLISHED
    version.published_at = timezone.now()
    version.published_by = actor
    version.updated_by = actor
    version.save()
    draft = DesignVersion.objects.create(
        design=version.design,
        number=version.number + 1,
        created_by=actor,
        updated_by=actor,
    )
    _clone_version_content(version, draft, actor, clone_options=False)
    return version, draft


@transaction.atomic
def archive_design(*, shop_id, actor, design_id):
    shop, _membership = _shop_actor(shop_id=shop_id, actor=actor, write=True)
    try:
        design = Design.objects.select_for_update().get(pk=design_id, tenant=shop)
    except (Design.DoesNotExist, ValueError):
        raise NotFound() from None
    design.status = Design.Status.ARCHIVED
    design.updated_by = actor
    design.save(update_fields=("status", "updated_by", "updated_at"))
    return design


@transaction.atomic
def restore_shop_default_design(*, shop_id, actor, design_id):
    shop, _membership = _shop_actor(shop_id=shop_id, actor=actor, write=True)
    try:
        design = (
            Design.objects.select_for_update(of=("self",))
            .select_related("family", "variant", "source_design")
            .get(
                pk=design_id,
                tenant=shop,
                is_default_seeded=True,
                status=Design.Status.ARCHIVED,
                source_design__tenant__isnull=True,
            )
        )
    except (Design.DoesNotExist, ValueError):
        raise NotFound() from None
    if design.family.status != GarmentFamily.Status.ACTIVE:
        raise ValidationError({"family": "Restore the garment family first."})
    try:
        source_version = design.source_design.versions.filter(
            status=DesignVersion.Status.PUBLISHED
        ).order_by("-number").first()
    except Design.DoesNotExist:
        source_version = None
    if source_version is None or design.source_design.status != Design.Status.ACTIVE:
        raise ValidationError({"design": "The current Back Office default is unavailable."})
    if design.variant_id and not design.variant.is_active:
        raise ValidationError({"variant": "Restore the garment variant first."})
    design.status = Design.Status.ACTIVE
    design.updated_by = actor
    design.save(update_fields=("status", "updated_by", "updated_at"))
    current_draft = design.versions.select_for_update().filter(
        status=DesignVersion.Status.DRAFT
    ).first()
    if current_draft:
        current_draft.delete()
    return copy_design_version(
        shop_id=shop.pk,
        actor=actor,
        family=design.family,
        variant=design.variant,
        name=source_version.translations.filter(locale="en").values_list("name", flat=True).first() or design.family.code,
        source=design.source_design,
        source_version=source_version,
        is_default_seeded=True,
        target_design=design,
    )


@transaction.atomic
def archive_global_design(*, actor, design_id):
    if not ShopRolePolicy.is_main_supplier_admin(actor):
        raise PermissionDenied()
    try:
        design = Design.objects.select_for_update().get(
            pk=design_id, tenant__isnull=True
        )
    except (Design.DoesNotExist, ValueError):
        raise NotFound() from None
    design.status = Design.Status.ARCHIVED
    design.updated_by = actor
    design.save(update_fields=("status", "updated_by", "updated_at"))
    return design


def upload_style_images(*, style_option, uploads, actor, shop=None):
    if len(uploads) != 1:
        raise ValidationError({"images": "Upload exactly one image per style option."})
    processed = [optimize_reference(uploads[0])]
    records = []
    stored_names = []
    try:
        with transaction.atomic():
            style_option = StyleOption.objects.select_for_update().get(
                pk=style_option.pk
            )
            style_option.reference_images.filter(is_primary=True).update(
                is_primary=False
            )
            for content, size, width, height in processed:
                record = StyleOptionImage(
                    style_option=style_option,
                    image=content,
                    mime_type="image/webp",
                    byte_size=size,
                    width=width,
                    height=height,
                    is_primary=True,
                    created_by=actor,
                    updated_by=actor,
                )
                record.save()
                stored_names.append(record.image.name)
                records.append(record)
    except Exception:
        for name in stored_names:
            style_option.reference_images.model._meta.get_field("image").storage.delete(
                name
            )
        raise
    return records


@transaction.atomic
def update_shop_style_option(*, shop, option_id, translations, actor):
    """Update supplied translations on one Shop-owned style option only."""
    try:
        option = StyleOption.objects.select_for_update().get(
            pk=option_id, tenant=shop, deleted__isnull=True
        )
    except (StyleOption.DoesNotExist, ValueError):
        raise NotFound() from None

    existing = {
        row.locale: row
        for row in StyleOptionTranslation.objects.select_for_update().filter(
            style_option=option
        )
    }
    if "en" not in existing:
        raise ValidationError(
            {"translations": "A Shop style option must retain its English name."}
        )

    for item in translations:
        values = dict(item)
        translation = existing.get(values["locale"])
        if translation is None:
            translation = StyleOptionTranslation(
                style_option=option,
                locale=values["locale"],
                name=values["name"],
                description=values.get("description", ""),
                created_by=actor,
            )
        else:
            translation.name = values["name"]
            if "description" in values:
                translation.description = values["description"]
        translation.updated_by = actor
        translation.save()

    option.updated_by = actor
    option.save(update_fields=("updated_by", "updated_at"))
    return option


@transaction.atomic
def upload_design_references(*, version, uploads, actor):
    if not uploads or len(uploads) > MAX_BATCH_FILES:
        raise ValidationError({"images": "Upload between 1 and 3 images per request."})
    try:
        version = DesignVersion.objects.select_for_update().get(pk=version.pk)
    except DesignVersion.DoesNotExist:
        raise NotFound() from None
    if version.status != DesignVersion.Status.DRAFT:
        raise ValidationError({"version": "Published versions are immutable."})
    processed = [optimize_reference(upload) for upload in uploads]
    records = []
    stored_names = []
    storage = DesignReference._meta.get_field("image").storage
    try:
        with transaction.atomic():
            for content, size, width, height in processed:
                record = DesignReference(
                    version=version,
                    image=content,
                    mime_type="image/webp",
                    byte_size=size,
                    width=width,
                    height=height,
                    created_by=actor,
                    updated_by=actor,
                )
                record.save()
                stored_names.append(record.image.name)
                records.append(record)
    except Exception:
        for name in stored_names:
            storage.delete(name)
        raise
    return records
