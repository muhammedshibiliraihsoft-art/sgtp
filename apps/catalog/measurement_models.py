"""Shop-scoped measurement history and minimal material reference records."""

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from safedelete.managers import SafeDeleteManager
from safedelete.queryset import SafeDeleteQueryset

from backend.core.models import BaseModel
from apps.catalog.models import GarmentFamily, GarmentVariant, ShopScopedCatalogModel
from apps.clients.models import Client, RelatedPerson
from apps.tenants.models import Tenant


LOCALES = (
    ("en", "English"),
    ("ar-KW", "Arabic (Kuwait)"),
    ("bn", "Bangla"),
    ("ur", "Urdu"),
)


class MeasurementUnit(models.TextChoices):
    INCH = "INCH", "Inch"
    CM = "CM", "Centimetre"


class ImmutableHistoryQuerySet(SafeDeleteQueryset):
    def update(self, **kwargs):
        raise ValidationError("Measurement history is immutable.")

    def delete(self, *args, **kwargs):
        raise ValidationError("Measurement history cannot be deleted.")


class ImmutableHistoryManager(SafeDeleteManager):
    _queryset_class = ImmutableHistoryQuerySet


class MeasurementDefinition(ShopScopedCatalogModel):
    """A global system definition or reusable Shop-owned measurement label."""

    code = models.SlugField(max_length=64)
    group_code = models.CharField(max_length=48, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    families = models.ManyToManyField(
        GarmentFamily,
        through="MeasurementDefinitionMapping",
        related_name="measurement_definitions",
    )

    class Meta:
        ordering = ("sort_order", "code", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("code",),
                condition=Q(tenant__isnull=True, deleted__isnull=True),
                name="measurement_global_code_uniq",
            ),
            models.UniqueConstraint(
                fields=("tenant", "code"),
                condition=Q(tenant__isnull=False, deleted__isnull=True),
                name="measurement_shop_code_uniq",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            previous = (
                type(self)
                .all_objects.filter(pk=self.pk)
                .values("tenant_id", "code", "is_active")
                .first()
            )
            if previous and previous["tenant_id"] is None:
                raise ValidationError("System measurement definitions are immutable.")
            if previous and previous["code"] != self.code:
                raise ValidationError("Measurement definition codes are immutable.")
            if previous and not previous["is_active"] and self.is_active:
                raise ValidationError(
                    "Archived measurement definitions cannot be restored."
                )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "Measurement definitions are archived rather than deleted."
        )


class MeasurementDefinitionTranslation(BaseModel):
    definition = models.ForeignKey(
        MeasurementDefinition, on_delete=models.CASCADE, related_name="translations"
    )
    locale = models.CharField(max_length=5, choices=LOCALES)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("definition", "locale"), name="measurement_def_locale_uniq"
            )
        ]


class MeasurementDefinitionMapping(BaseModel):
    """Family applicability, optionally restricted to one garment variant."""

    definition = models.ForeignKey(
        MeasurementDefinition, on_delete=models.PROTECT, related_name="mappings"
    )
    family = models.ForeignKey(
        GarmentFamily, on_delete=models.PROTECT, related_name="measurement_mappings"
    )
    variant = models.ForeignKey(
        GarmentVariant,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="measurement_mappings",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("definition", "family"),
                condition=Q(variant__isnull=True, deleted__isnull=True),
                name="measure_map_family_uniq",
            ),
            models.UniqueConstraint(
                fields=("definition", "family", "variant"),
                condition=Q(variant__isnull=False, deleted__isnull=True),
                name="measure_map_variant_uniq",
            ),
        ]

    def clean(self):
        super().clean()
        if (
            self.variant_id
            and self.family_id
            and self.variant.family_id != self.family_id
        ):
            raise ValidationError(
                {"variant": "Variant must belong to the selected family."}
            )
        if self.definition_id and self.variant_id:
            if (
                self.definition.tenant_id != self.variant.tenant_id
                and self.variant.tenant_id
            ):
                raise ValidationError(
                    {"variant": "Variant must be global or belong to this Shop."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class MeasurementProfile(BaseModel):
    """Independent measurement history for exactly one person and garment."""

    tenant = models.ForeignKey(
        Tenant, on_delete=models.PROTECT, related_name="measurement_profiles"
    )
    client = models.ForeignKey(
        Client,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="measurement_profiles",
    )
    related_person = models.ForeignKey(
        RelatedPerson,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="measurement_profiles",
    )
    family = models.ForeignKey(
        GarmentFamily, on_delete=models.PROTECT, related_name="measurement_profiles"
    )
    variant = models.ForeignKey(
        GarmentVariant,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="measurement_profiles",
    )
    objects = ImmutableHistoryManager()

    class Meta:
        ordering = ("-created_at", "id")
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(client__isnull=False, related_person__isnull=True)
                    | Q(client__isnull=True, related_person__isnull=False)
                ),
                name="measurement_profile_one_owner",
            ),
            models.UniqueConstraint(
                fields=("tenant", "client", "family"),
                condition=Q(
                    client__isnull=False, variant__isnull=True, deleted__isnull=True
                ),
                name="measure_profile_client_base_uniq",
            ),
            models.UniqueConstraint(
                fields=("tenant", "client", "family", "variant"),
                condition=Q(
                    client__isnull=False, variant__isnull=False, deleted__isnull=True
                ),
                name="measure_profile_client_variant_uniq",
            ),
            models.UniqueConstraint(
                fields=("tenant", "related_person", "family"),
                condition=Q(
                    related_person__isnull=False,
                    variant__isnull=True,
                    deleted__isnull=True,
                ),
                name="measure_profile_person_base_uniq",
            ),
            models.UniqueConstraint(
                fields=("tenant", "related_person", "family", "variant"),
                condition=Q(
                    related_person__isnull=False,
                    variant__isnull=False,
                    deleted__isnull=True,
                ),
                name="measure_profile_person_variant_uniq",
            ),
        ]

    def clean(self):
        super().clean()
        if bool(self.client_id) == bool(self.related_person_id):
            raise ValidationError("A profile must belong to exactly one person.")
        person_shop_id = (
            self.client.tenant_id if self.client_id else self.related_person.tenant_id
        )
        if self.tenant_id and person_shop_id != self.tenant_id:
            raise ValidationError("Measured person must belong to the same Shop.")
        if self.related_person_id and self.client_id:
            if self.related_person.primary_client_id != self.client_id:
                raise ValidationError(
                    "Related Person billing owner must remain its Primary Client."
                )
        if (
            self.variant_id
            and self.family_id
            and self.variant.family_id != self.family_id
        ):
            raise ValidationError(
                {"variant": "Variant must belong to the selected family."}
            )
        if self.variant_id and self.variant.tenant_id not in (None, self.tenant_id):
            raise ValidationError(
                {"variant": "Variant must be global or belong to this Shop."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self._state.adding:
            original = (
                type(self)
                .all_objects.filter(pk=self.pk)
                .values(
                    "tenant_id",
                    "client_id",
                    "related_person_id",
                    "family_id",
                    "variant_id",
                )
                .first()
            )
            if original and any(
                original[field] != getattr(self, field) for field in original
            ):
                raise ValidationError(
                    "Measurement profile ownership and garment are immutable."
                )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Measurement profiles cannot be hard-deleted.")


class MeasurementSet(BaseModel):
    """Immutable, versioned snapshot of one person's recorded measurements."""

    Unit = MeasurementUnit

    profile = models.ForeignKey(
        MeasurementProfile, on_delete=models.PROTECT, related_name="sets"
    )
    version = models.PositiveIntegerField()
    copied_from = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="copies"
    )
    objects = ImmutableHistoryManager()

    class Meta:
        ordering = ("-version", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("profile", "version"), name="measurement_set_version_uniq"
            ),
            models.CheckConstraint(
                condition=Q(version__gte=1), name="measurement_set_version_positive"
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "Measurement sets are immutable; create a new version."
            )
        if self.copied_from_id and self.copied_from.profile_id != self.profile_id:
            raise ValidationError("A copied set must come from the same profile.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Measurement history cannot be deleted.")


class MeasurementValue(BaseModel):
    Unit = MeasurementUnit

    measurement_set = models.ForeignKey(
        MeasurementSet, on_delete=models.PROTECT, related_name="values"
    )
    definition = models.ForeignKey(
        MeasurementDefinition, on_delete=models.PROTECT, related_name="values"
    )
    definition_code_snapshot = models.CharField(max_length=64)
    label_snapshot = models.CharField(max_length=120)
    value = models.DecimalField(max_digits=12, decimal_places=4)
    unit = models.CharField(max_length=4, choices=MeasurementUnit.choices)
    objects = ImmutableHistoryManager()

    class Meta:
        ordering = ("definition_code_snapshot", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("measurement_set", "definition"),
                name="measurement_value_def_uniq",
            ),
            models.CheckConstraint(
                condition=Q(unit__in=("INCH", "CM")),
                name="measurement_value_unit_valid",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Saved measurement values are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Measurement history cannot be deleted.")


class MeasurementValueTranslationSnapshot(BaseModel):
    """Historical localized label captured with a value, not read live later."""

    value_record = models.ForeignKey(
        MeasurementValue, on_delete=models.PROTECT, related_name="label_translations"
    )
    locale = models.CharField(max_length=5, choices=LOCALES)
    name = models.CharField(max_length=120)
    objects = ImmutableHistoryManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("value_record", "locale"), name="measure_value_locale_uniq"
            )
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Measurement history labels are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Measurement history labels cannot be deleted.")


class Material(BaseModel):
    """Minimal Shop-owned fabric/material reference; contains no inventory data."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ARCHIVED = "ARCHIVED", "Archived"

    tenant = models.ForeignKey(
        Tenant, on_delete=models.PROTECT, related_name="materials"
    )
    name = models.CharField(max_length=160)
    code = models.SlugField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=8, choices=Status.choices, default=Status.ACTIVE
    )

    class Meta:
        ordering = ("name", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "code"),
                condition=Q(code__gt="", deleted__isnull=True),
                name="material_shop_code_uniq",
            ),
            models.CheckConstraint(
                condition=Q(status__in=("ACTIVE", "ARCHIVED")),
                name="material_status_valid",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            previous = (
                type(self).all_objects.filter(pk=self.pk).values("status").first()
            )
            if previous and previous["status"] == self.Status.ARCHIVED:
                if self.status != self.Status.ARCHIVED:
                    raise ValidationError("Archived Materials cannot be restored.")
                original = (
                    type(self)
                    .all_objects.filter(pk=self.pk)
                    .values("tenant_id", "name", "code", "description")
                    .first()
                )
                if original and any(
                    original[field] != getattr(self, field)
                    for field in ("tenant_id", "name", "code", "description")
                ):
                    raise ValidationError("Archived Materials cannot be edited.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Materials are archived rather than deleted.")
