import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.db import models
from django.db.models import Q

from backend.core.models import BaseModel
from backend.core.models import TimeStampedUUIDModel


LOCALES = ("en", "ar-KW", "bn", "ur")


class ShopScopedCatalogModel(BaseModel):
    """Global defaults have no Shop; operational custom records require one."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="%(class)s_records",
    )

    class Meta:
        abstract = True


def family_image_upload_path(instance, filename):
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else "webp"
    return f"catalog/global/families/{instance.pk}/{uuid.uuid4().hex}.{suffix}"


class GarmentFamily(BaseModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ARCHIVED = "ARCHIVED", "Archived"

    code = models.SlugField(max_length=48, unique=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.ACTIVE
    )
    image = models.FileField(
        upload_to=family_image_upload_path,
        storage=storages["private_media"],
        blank=True,
    )
    image_mime_type = models.CharField(max_length=32, blank=True)
    image_byte_size = models.PositiveIntegerField(null=True, blank=True)
    image_width = models.PositiveIntegerField(null=True, blank=True)
    image_height = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ("code",)

    def __str__(self):
        return self.code


class GarmentFamilyTranslation(BaseModel):
    family = models.ForeignKey(
        GarmentFamily, on_delete=models.CASCADE, related_name="translations"
    )
    locale = models.CharField(max_length=5, choices=[(x, x) for x in LOCALES])
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("family", "locale"), name="catalog_family_locale_uniq"
            )
        ]


class GarmentVariant(ShopScopedCatalogModel):
    family = models.ForeignKey(
        GarmentFamily, on_delete=models.PROTECT, related_name="variants"
    )
    code = models.SlugField(max_length=64)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("family__code", "code")
        constraints = [
            models.UniqueConstraint(
                fields=("family", "code"),
                condition=Q(tenant__isnull=True, deleted__isnull=True),
                name="catalog_global_variant_code_uniq",
            ),
            models.UniqueConstraint(
                fields=("tenant", "family", "code"),
                condition=Q(tenant__isnull=False, deleted__isnull=True),
                name="catalog_shop_variant_code_uniq",
            ),
            models.UniqueConstraint(
                fields=("family",),
                condition=Q(tenant__isnull=True, is_default=True, deleted__isnull=True),
                name="catalog_one_global_default_variant",
            ),
        ]


class GarmentVariantTranslation(BaseModel):
    variant = models.ForeignKey(
        GarmentVariant, on_delete=models.CASCADE, related_name="translations"
    )
    locale = models.CharField(max_length=5, choices=[(x, x) for x in LOCALES])
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("variant", "locale"), name="catalog_variant_locale_uniq"
            )
        ]


class OptionGroup(BaseModel):
    code = models.SlugField(max_length=48, unique=True)
    families = models.ManyToManyField(
        GarmentFamily, through="FamilyOptionGroup", related_name="option_groups"
    )

    class Meta:
        ordering = ("code",)


class FamilyOptionGroup(BaseModel):
    family = models.ForeignKey(GarmentFamily, on_delete=models.CASCADE)
    option_group = models.ForeignKey(OptionGroup, on_delete=models.CASCADE)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "option_group__code")
        constraints = [
            models.UniqueConstraint(
                fields=("family", "option_group"),
                condition=Q(deleted__isnull=True),
                name="catalog_family_option_group_uniq",
            )
        ]


class OptionGroupTranslation(BaseModel):
    option_group = models.ForeignKey(
        OptionGroup, on_delete=models.CASCADE, related_name="translations"
    )
    locale = models.CharField(max_length=5, choices=[(x, x) for x in LOCALES])
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("option_group", "locale"),
                name="catalog_group_locale_uniq",
            )
        ]


class StyleOption(ShopScopedCatalogModel):
    option_group = models.ForeignKey(
        OptionGroup, on_delete=models.PROTECT, related_name="style_options"
    )
    code = models.SlugField(max_length=64)
    is_active = models.BooleanField(default=True)
    source_style_option = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="copied_style_options",
    )

    class Meta:
        ordering = ("option_group__code", "code")
        constraints = [
            models.UniqueConstraint(
                fields=("option_group", "code"),
                condition=Q(tenant__isnull=True, deleted__isnull=True),
                name="catalog_global_style_code_uniq",
            ),
            models.UniqueConstraint(
                fields=("tenant", "option_group", "code"),
                condition=Q(tenant__isnull=False, deleted__isnull=True),
                name="catalog_shop_style_code_uniq",
            ),
        ]

    def clean(self):
        super().clean()


class StyleOptionTranslation(BaseModel):
    style_option = models.ForeignKey(
        StyleOption, on_delete=models.CASCADE, related_name="translations"
    )
    locale = models.CharField(max_length=5, choices=[(x, x) for x in LOCALES])
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("style_option", "locale"),
                name="catalog_style_locale_uniq",
            )
        ]


def reference_upload_path(instance, filename):
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    if hasattr(instance, "style_option_id"):
        option = instance.style_option
        scope = f"shops/{option.tenant_id}" if option.tenant_id else "catalog/global"
        parent = f"style-options/{option.pk}"
    elif hasattr(instance, "version_id"):
        design = instance.version.design
        scope = f"shops/{design.tenant_id}" if design.tenant_id else "catalog/global"
        parent = f"design-versions/{instance.version_id}"
    else:
        scope, parent = "catalog/global", "references"
    return f"{scope}/{parent}/references/{uuid.uuid4().hex}.{suffix}"


class StyleOptionImage(BaseModel):
    style_option = models.ForeignKey(
        StyleOption, on_delete=models.PROTECT, related_name="reference_images"
    )
    image = models.FileField(
        upload_to=reference_upload_path,
        storage=storages["private_media"],
        max_length=512,
    )
    mime_type = models.CharField(max_length=32)
    byte_size = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    sort_order = models.PositiveSmallIntegerField(default=0)
    alt_text = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ("sort_order", "created_at", "id")

    def save(self, *args, **kwargs):
        if not self._state.adding:
            previous = (
                type(self)
                .objects.filter(pk=self.pk)
                .values(
                    "style_option_id",
                    "image",
                    "mime_type",
                    "byte_size",
                    "width",
                    "height",
                )
                .first()
            )
            if previous and any(
                previous[field]
                != (
                    getattr(self, attr).name if attr == "image" else getattr(self, attr)
                )
                for field, attr in (
                    ("style_option_id", "style_option_id"),
                    ("image", "image"),
                    ("mime_type", "mime_type"),
                    ("byte_size", "byte_size"),
                    ("width", "width"),
                    ("height", "height"),
                )
            ):
                raise ValidationError("Stored style references are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if DesignSelectionImage.objects.filter(
            source_image=self, selection__version__status=DesignVersion.Status.PUBLISHED
        ).exists():
            raise ValidationError(
                "Reference images used by published versions cannot be deleted."
            )
        return super().delete(*args, **kwargs)


class Design(ShopScopedCatalogModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ARCHIVED = "ARCHIVED", "Archived"

    family = models.ForeignKey(
        GarmentFamily, on_delete=models.PROTECT, related_name="designs"
    )
    variant = models.ForeignKey(
        GarmentVariant, on_delete=models.PROTECT, related_name="designs"
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.ACTIVE
    )
    source_design = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="derived_designs",
    )

    class Meta:
        ordering = ("-created_at", "id")
        indexes = [models.Index(fields=("tenant", "status", "family"))]

    def clean(self):
        super().clean()
        if (
            self.variant_id
            and self.family_id
            and self.variant.family_id != self.family_id
        ):
            raise ValidationError(
                {"variant": "Variant must belong to this garment family."}
            )
        if self.variant_id and self.variant.tenant_id not in (None, self.tenant_id):
            raise ValidationError(
                {"variant": "Variant must be global or Shop-owned here."}
            )


class DesignVersion(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"

    design = models.ForeignKey(
        Design, on_delete=models.PROTECT, related_name="versions"
    )
    number = models.PositiveIntegerField()
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.DRAFT
    )
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="published_design_versions",
    )

    class Meta:
        ordering = ("design_id", "number")
        constraints = [
            models.UniqueConstraint(
                fields=("design", "number"), name="catalog_design_version_number_uniq"
            ),
            models.UniqueConstraint(
                fields=("design",),
                condition=Q(status="DRAFT", deleted__isnull=True),
                name="catalog_one_draft_per_design",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            previous = (
                type(self)
                .objects.filter(pk=self.pk)
                .values(
                    "design_id", "number", "status", "published_at", "published_by_id"
                )
                .first()
            )
            if previous and previous["status"] == self.Status.PUBLISHED:
                changed = any(
                    previous[key] != getattr(self, attr)
                    for key, attr in (
                        ("design_id", "design_id"),
                        ("number", "number"),
                        ("status", "status"),
                        ("published_at", "published_at"),
                        ("published_by_id", "published_by_id"),
                    )
                )
                if changed:
                    raise ValidationError("Published DesignVersions are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status == self.Status.PUBLISHED:
            raise ValidationError("Published DesignVersions cannot be deleted.")
        return super().delete(*args, **kwargs)


class DesignVersionTranslation(BaseModel):
    version = models.ForeignKey(
        DesignVersion, on_delete=models.CASCADE, related_name="translations"
    )
    locale = models.CharField(max_length=5, choices=[(x, x) for x in LOCALES])
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("version", "locale"), name="catalog_design_locale_uniq"
            )
        ]

    def clean(self):
        super().clean()
        if self.version_id and self.version.status == DesignVersion.Status.PUBLISHED:
            raise ValidationError("Published DesignVersion translations are immutable.")

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.version.status == DesignVersion.Status.PUBLISHED:
            raise ValidationError(
                "Published DesignVersion translations cannot be deleted."
            )
        return super().delete(*args, **kwargs)


class DesignSelection(BaseModel):
    version = models.ForeignKey(
        DesignVersion, on_delete=models.CASCADE, related_name="selections"
    )
    option_group = models.ForeignKey(OptionGroup, on_delete=models.PROTECT)
    style_option = models.ForeignKey(StyleOption, on_delete=models.PROTECT)
    selected_code = models.CharField(max_length=64)
    selected_name_en = models.CharField(max_length=120)

    class Meta:
        ordering = ("option_group__code", "selected_code", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("version", "option_group", "style_option"),
                name="catalog_selection_unique_option",
            )
        ]

    def clean(self):
        super().clean()
        if self.style_option_id and self.option_group_id:
            if self.style_option.option_group_id != self.option_group_id:
                raise ValidationError({"style_option": "Option must match its group."})
        design = self.version.design if self.version_id else None
        if self.version_id and self.version.status != DesignVersion.Status.DRAFT:
            raise ValidationError({"version": "Published versions are immutable."})
        if design and self.style_option.tenant_id not in (None, design.tenant_id):
            raise ValidationError(
                {"style_option": "Option is not available in this Shop."}
            )

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.version.status == DesignVersion.Status.PUBLISHED:
            raise ValidationError("Published DesignSelections cannot be deleted.")
        return super().delete(*args, **kwargs)


class DesignSelectionTranslation(BaseModel):
    """Localized style-option label captured as part of a DesignVersion snapshot."""

    selection = models.ForeignKey(
        DesignSelection, on_delete=models.CASCADE, related_name="translations"
    )
    locale = models.CharField(max_length=5, choices=[(x, x) for x in LOCALES])
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("selection", "locale"), name="catalog_selection_locale_uniq"
            )
        ]

    def save(self, *args, **kwargs):
        if self.selection.version.status != DesignVersion.Status.DRAFT:
            raise ValidationError("Published versions are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.selection.version.status == DesignVersion.Status.PUBLISHED:
            raise ValidationError(
                "Published DesignSelection translations cannot be deleted."
            )
        return super().delete(*args, **kwargs)


class DesignSelectionImage(BaseModel):
    """Immutable image references captured when an option is selected."""

    selection = models.ForeignKey(
        DesignSelection, on_delete=models.CASCADE, related_name="reference_images"
    )
    source_image = models.ForeignKey(StyleOptionImage, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("selection", "source_image"),
                name="catalog_selection_image_uniq",
            )
        ]

    def clean(self):
        super().clean()
        if self.selection_id and self.source_image_id:
            selection = self.selection
            image = self.source_image
            if selection.version.status != DesignVersion.Status.DRAFT:
                raise ValidationError("Published versions are immutable.")
            if image.style_option_id != selection.style_option_id:
                raise ValidationError(
                    "Reference image must belong to selected StyleOption."
                )

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.selection.version.status == DesignVersion.Status.PUBLISHED:
            raise ValidationError("Published DesignSelection images cannot be deleted.")
        return super().delete(*args, **kwargs)


class DesignReference(BaseModel):
    """Private image uploaded directly to a particular DesignVersion."""

    version = models.ForeignKey(
        DesignVersion, on_delete=models.PROTECT, related_name="references"
    )
    image = models.FileField(
        upload_to=reference_upload_path,
        storage=storages["private_media"],
        max_length=512,
    )
    mime_type = models.CharField(max_length=32)
    byte_size = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    sort_order = models.PositiveSmallIntegerField(default=0)
    alt_text = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ("sort_order", "created_at", "id")

    def save(self, *args, **kwargs):
        if self.version.status != DesignVersion.Status.DRAFT:
            raise ValidationError("Published versions are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.version.status == DesignVersion.Status.PUBLISHED:
            raise ValidationError(
                "Published DesignVersion references cannot be deleted."
            )
        return super().delete(*args, **kwargs)


class PrivateMediaUpload(TimeStampedUUIDModel):
    """One-time Shop-bound ticket for validating a direct private object upload."""

    class Kind(models.TextChoices):
        FAMILY = "family", "Global garment-family image"
        STYLE_OPTION = "style_option", "Style option reference"
        DESIGN_VERSION = "design_version", "Design version reference"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="private_media_uploads",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="private_media_uploads",
    )
    kind = models.CharField(max_length=24, choices=Kind.choices)
    target_id = models.UUIDField()
    object_key = models.CharField(max_length=512, unique=True)
    content_type = models.CharField(max_length=32)
    byte_size = models.PositiveIntegerField()
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ("-created_at",)


# Keep the existing Catalog app as the runtime owner while keeping its
# measurement/material domain models separate from the Design model definitions.
from apps.catalog.measurement_models import (  # noqa: E402, F401
    Material,
    MeasurementDefinition,
    MeasurementDefinitionMapping,
    MeasurementDefinitionTranslation,
    MeasurementProfile,
    MeasurementSet,
    MeasurementValue,
    MeasurementValueTranslationSnapshot,
)
from apps.catalog.inventory_models import (  # noqa: E402, F401
    InventoryBalance,
    StockMovement,
)
