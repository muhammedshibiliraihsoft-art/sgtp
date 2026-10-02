"""Main Supplier, inspection-only views for catalog and measurement records."""

from django.contrib import admin

from apps.common.admin import MainSupplierReadOnlyAdmin
from . import measurement_models as measurements
from . import models as catalog


class CatalogRecordAdmin(MainSupplierReadOnlyAdmin):
    list_per_page = 50
    ordering = ("-created_at",)

    def get_queryset(self, request):
        manager = getattr(self.model, "all_objects", self.model._default_manager)
        queryset = manager.get_queryset()
        relations = tuple(
            field.name
            for field in self.model._meta.concrete_fields
            if field.is_relation and field.many_to_one
        )
        return queryset.select_related(*relations)

    def get_exclude(self, request, obj=None):
        excluded = set(super().get_exclude(request, obj) or ())
        excluded.update(
            field.name
            for field in self.model._meta.concrete_fields
            if getattr(field, "get_internal_type", lambda: "")()
            in {"FileField", "ImageField"}
        )
        return tuple(sorted(excluded))

    def get_list_display(self, request):
        available = {field.name for field in self.model._meta.concrete_fields}
        fields = [
            name
            for name in (
                "code",
                "name",
                "tenant",
                "family",
                "option_group",
                "status",
                "is_active",
                "version",
                "locale",
                "function_code",
                "created_at",
            )
            if name in available
        ]
        return tuple(fields or ("__str__",))

    def get_list_filter(self, request):
        return tuple(
            name
            for name in ("tenant", "status", "is_active", "locale", "family")
            if name in {field.name for field in self.model._meta.concrete_fields}
        )

    def get_search_fields(self, request):
        return tuple(
            name
            for name in ("code", "name", "group_code", "description", "alt_text")
            if name in {field.name for field in self.model._meta.concrete_fields}
        )


CATALOG_MODELS = (
    catalog.GarmentFamily,
    catalog.GarmentFamilyTranslation,
    catalog.GarmentVariant,
    catalog.GarmentVariantTranslation,
    catalog.OptionGroup,
    catalog.FamilyOptionGroup,
    catalog.OptionGroupTranslation,
    catalog.StyleOption,
    catalog.StyleOptionTranslation,
    catalog.StyleOptionImage,
    catalog.Design,
    catalog.DesignVersion,
    catalog.DesignVersionTranslation,
    catalog.DesignSelection,
    catalog.DesignSelectionTranslation,
    catalog.DesignSelectionImage,
    catalog.DesignReference,
    measurements.MeasurementDefinition,
    measurements.MeasurementDefinitionTranslation,
    measurements.MeasurementDefinitionMapping,
    measurements.MeasurementProfile,
    measurements.MeasurementSet,
    measurements.MeasurementValue,
    measurements.MeasurementValueTranslationSnapshot,
    measurements.Material,
    catalog.InventoryBalance,
    catalog.StockMovement,
)

for model in CATALOG_MODELS:
    admin.site.register(model, CatalogRecordAdmin)
