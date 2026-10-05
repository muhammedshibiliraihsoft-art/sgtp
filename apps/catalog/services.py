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
    GarmentFamily,
    GarmentFamilyTranslation,
    GarmentVariant,
    GarmentVariantTranslation,
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
        family = GarmentFamily.objects.select_for_update().get(pk=family_id)
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


@transaction.atomic
def set_family_status(*, family_id, status, actor):
    _main_supplier(actor)
    try:
        family = GarmentFamily.objects.select_for_update().get(pk=family_id)
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
        .filter(pk=family_id, status=GarmentFamily.Status.ACTIVE)
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
        .filter(pk=family_id, status=GarmentFamily.Status.ACTIVE)
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
                    for image in option.reference_images.all():
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
    *, shop_id, actor, family, variant, name, source=None, translations=None
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
    design = Design.objects.create(
        tenant=shop,
        family=family,
        variant=variant,
        source_design=source,
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


def copy_design_version(
    *, shop_id, actor, family, variant, name, source, source_version, translations=None
):
    shop, _membership = _shop_actor(shop_id=shop_id, actor=actor, write=True)
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
    if (
        source_version.design_id != source.pk
        or source_version.status != DesignVersion.Status.PUBLISHED
    ):
        raise NotFound()
    if source.tenant_id not in (None, shop.pk):
        raise NotFound()
    design = Design.objects.create(
        tenant=shop,
        family=family,
        variant=variant,
        source_design=source,
        created_by=actor,
        updated_by=actor,
    )
    target = DesignVersion.objects.create(design=design, number=1, created_by=actor)
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
                for image in original.reference_images.all():
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
    if not family.option_groups.filter(pk=option.option_group_id).exists():
        raise ValidationError(
            {"style_option": "This option group is not available for the garment."}
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
                for image in option.reference_images.all()
            ]
        )
    return selection


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
def create_global_design(*, actor, family, variant, name, translations=None):
    _main_supplier(actor)
    try:
        family = GarmentFamily.objects.select_for_update().get(
            pk=family.pk, status=GarmentFamily.Status.ACTIVE
        )
    except GarmentFamily.DoesNotExist:
        raise ValidationError(
            {"family_id": "Select an active garment family."}
        ) from None
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
        raise ValidationError({"variant": "Select a global variant for this family."})
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
    if not uploads or len(uploads) > MAX_BATCH_FILES:
        raise ValidationError({"images": "Upload between 1 and 3 images per request."})
    processed = [optimize_reference(upload) for upload in uploads]
    records = []
    stored_names = []
    try:
        with transaction.atomic():
            for content, size, width, height in processed:
                record = StyleOptionImage(
                    style_option=style_option,
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
