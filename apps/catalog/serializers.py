from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from apps.catalog.models import (
    Design,
    DesignReference,
    DesignSelection,
    DesignVersion,
    FamilyOptionGroup,
    GarmentFamily,
    GarmentFamilyTranslation,
    GarmentVariant,
    GarmentVariantTranslation,
    OptionGroup,
    StyleOption,
    StyleOptionImage,
)


def translated_name(record, locale):
    translations = {item.locale: item.name for item in record.translations.all()}
    return (
        translations.get(locale)
        or translations.get("en")
        or getattr(record, "code", "")
    )


class FamilySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    has_image = serializers.SerializerMethodField()
    image_content_url = serializers.SerializerMethodField()

    class Meta:
        model = GarmentFamily
        fields = (
            "id",
            "tenant",
            "template_source",
            "code",
            "name",
            "status",
            "has_image",
            "image_content_url",
        )
        read_only_fields = ("tenant", "template_source")

    @extend_schema_field(OpenApiTypes.STR)
    def get_name(self, obj):
        return translated_name(obj, self.context.get("locale", "en"))

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_has_image(self, obj):
        return bool(obj.image)

    @extend_schema_field(OpenApiTypes.STR)
    def get_image_content_url(self, obj):
        if not obj.image:
            return None
        from django.urls import reverse

        return reverse("v1:catalog-family-image", kwargs={"family_id": obj.pk})


class TranslationInputSerializer(serializers.Serializer):
    locale = serializers.ChoiceField(choices=("en", "ar-KW", "bn", "ur"))
    name = serializers.CharField(max_length=120, trim_whitespace=True)
    description = serializers.CharField(required=False, allow_blank=True)


class GlobalCatalogRecordInputSerializer(serializers.Serializer):
    """Shared input contract for Main Supplier-owned global catalog records."""

    code = serializers.SlugField(max_length=48)
    translations = TranslationInputSerializer(many=True)

    def validate_translations(self, value):
        locales = [item["locale"] for item in value]
        if len(locales) != len(set(locales)) or "en" not in locales:
            raise serializers.ValidationError(
                "Provide unique translations including English."
            )
        return value


class FamilyListQuerySerializer(serializers.Serializer):
    search = serializers.CharField(required=False, allow_blank=True, max_length=120)
    status = serializers.ChoiceField(
        choices=("ACTIVE", "ARCHIVED", "all"), required=False, default="ACTIVE"
    )


class FamilyUpdateSerializer(serializers.Serializer):
    translations = TranslationInputSerializer(many=True, required=False)
    option_group_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False
    )

    def validate(self, attrs):
        if set(self.initial_data) - {"translations", "option_group_ids"}:
            raise serializers.ValidationError(
                "Only family translations and option groups may be changed; the family code is immutable."
            )
        if not attrs:
            raise serializers.ValidationError(
                "Provide family translations or option groups to update."
            )
        translations = attrs.get("translations")
        if translations is not None:
            locales = [item["locale"] for item in translations]
            if len(locales) != len(set(locales)):
                raise serializers.ValidationError(
                    {"translations": "Each locale may appear only once."}
                )
        return attrs


class FamilyTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GarmentFamilyTranslation
        fields = ("locale", "name", "description")


class FamilyImageUploadSerializer(serializers.Serializer):
    image = serializers.FileField()


class FamilyImageMetadataSerializer(serializers.Serializer):
    has_image = serializers.BooleanField()
    image_content_url = serializers.CharField(allow_null=True)
    mime_type = serializers.CharField(allow_blank=True)
    byte_size = serializers.IntegerField(allow_null=True)
    width = serializers.IntegerField(allow_null=True)
    height = serializers.IntegerField(allow_null=True)


class GlobalVariantQuerySerializer(serializers.Serializer):
    family = serializers.UUIDField(required=False)
    search = serializers.CharField(required=False, allow_blank=True, max_length=120)
    status = serializers.ChoiceField(
        choices=("ACTIVE", "ARCHIVED", "all"), required=False, default="ACTIVE"
    )


class ShopVariantQuerySerializer(GlobalVariantQuerySerializer):
    source = serializers.ChoiceField(
        choices=("all", "global", "shop"), required=False, default="all"
    )


class DesignListQuerySerializer(serializers.Serializer):
    family = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(
        choices=("ACTIVE", "ARCHIVED", "all"), required=False, default="ACTIVE"
    )


class VariantSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    is_global = serializers.SerializerMethodField()

    class Meta:
        model = GarmentVariant
        fields = (
            "id",
            "family",
            "code",
            "name",
            "is_default",
            "is_global",
            "is_active",
        )

    @extend_schema_field(OpenApiTypes.STR)
    def get_name(self, obj):
        return translated_name(obj, self.context.get("locale", "en"))

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_global(self, obj):
        return obj.tenant_id is None


class VariantTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GarmentVariantTranslation
        fields = ("locale", "name", "description")


class VariantDetailSerializer(VariantSerializer):
    description = serializers.SerializerMethodField()
    translations = VariantTranslationSerializer(many=True, read_only=True)

    class Meta(VariantSerializer.Meta):
        fields = VariantSerializer.Meta.fields + (
            "description",
            "translations",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("tenant", "is_default_seeded")

    @extend_schema_field(OpenApiTypes.STR)
    def get_description(self, obj):
        locale = self.context.get("locale", "en")
        translations = {item.locale: item for item in obj.translations.all()}
        selected = translations.get(locale) or translations.get("en")
        return selected.description if selected else ""


class GlobalVariantInputSerializer(serializers.Serializer):
    family_id = serializers.UUIDField()
    code = serializers.SlugField(max_length=64)
    translations = TranslationInputSerializer(many=True)

    def validate_translations(self, value):
        locales = [item["locale"] for item in value]
        if len(locales) != len(set(locales)) or "en" not in locales:
            raise serializers.ValidationError(
                "Provide unique translations including English."
            )
        return value


class VariantUpdateSerializer(serializers.Serializer):
    translations = TranslationInputSerializer(many=True)

    def validate(self, attrs):
        if set(self.initial_data) != {"translations"}:
            raise serializers.ValidationError(
                "Only translations may be changed; variant code and family are immutable."
            )
        translations = attrs["translations"]
        locales = [item["locale"] for item in translations]
        if len(locales) != len(set(locales)) or "en" not in locales:
            raise serializers.ValidationError(
                {"translations": "Provide unique translations including English."}
            )
        return attrs


class ShopVariantInputSerializer(GlobalVariantInputSerializer):
    pass


class OptionGroupSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    families = serializers.SerializerMethodField()
    is_global = serializers.SerializerMethodField()

    class Meta:
        model = OptionGroup
        fields = ("id", "tenant", "code", "name", "families", "is_global")

    @extend_schema_field(OpenApiTypes.STR)
    def get_name(self, obj):
        return translated_name(obj, self.context.get("locale", "en"))

    @extend_schema_field(serializers.ListField(child=serializers.UUIDField()))
    def get_families(self, obj):
        rows = FamilyOptionGroup.objects.filter(option_group=obj).select_related(
            "family"
        )
        shop_id = self.context.get("shop_id")
        if shop_id:
            rows = rows.filter(family__tenant_id__in=(None, shop_id))
        else:
            rows = rows.filter(family__tenant__isnull=True)
        return [
            str(family_id) for family_id in rows.values_list("family_id", flat=True)
        ]

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_global(self, obj):
        return obj.tenant_id is None


class FamilyOptionGroupSerializer(serializers.ModelSerializer):
    option_group = OptionGroupSerializer(read_only=True)

    class Meta:
        model = FamilyOptionGroup
        fields = ("id", "option_group", "sort_order", "selection_mode", "is_required")


class FamilyDetailSerializer(FamilySerializer):
    translations = FamilyTranslationSerializer(many=True, read_only=True)
    option_groups = serializers.SerializerMethodField()

    class Meta(FamilySerializer.Meta):
        fields = FamilySerializer.Meta.fields + ("translations", "option_groups")

    @extend_schema_field(OptionGroupSerializer(many=True))
    def get_option_groups(self, obj):
        groups = [
            row.option_group
            for row in FamilyOptionGroup.objects.filter(family=obj)
            .select_related("option_group")
            .prefetch_related("option_group__translations")
        ]
        return OptionGroupSerializer(groups, many=True, context=self.context).data


class StyleImageSerializer(serializers.ModelSerializer):
    content_url = serializers.SerializerMethodField()

    class Meta:
        model = StyleOptionImage
        fields = (
            "id",
            "mime_type",
            "byte_size",
            "width",
            "height",
            "sort_order",
            "alt_text",
            "content_url",
        )

    @extend_schema_field(OpenApiTypes.STR)
    def get_content_url(self, obj):
        from django.urls import reverse

        if obj.style_option.tenant_id is None:
            return reverse(
                "v1:catalog-global-style-image",
                kwargs={"option_id": obj.style_option_id, "image_id": obj.pk},
            )
        return reverse(
            "v1:shop-style-image",
            kwargs={
                "shop_id": obj.style_option.tenant_id,
                "option_id": obj.style_option_id,
                "image_id": obj.pk,
            },
        )


class StyleOptionSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    reference_images = serializers.SerializerMethodField()
    is_global = serializers.SerializerMethodField()

    class Meta:
        model = StyleOption
        fields = (
            "id",
            "option_group",
            "tenant",
            "code",
            "name",
            "is_active",
            "is_global",
            "reference_images",
        )

    @extend_schema_field(OpenApiTypes.STR)
    def get_name(self, obj):
        return translated_name(obj, self.context.get("locale", "en"))

    @extend_schema_field(StyleImageSerializer(many=True))
    def get_reference_images(self, obj):
        images = list(obj.reference_images.all())
        current = next((image for image in images if image.is_primary), None)
        return StyleImageSerializer(
            [current] if current else [], many=True, context=self.context
        ).data

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_global(self, obj):
        return obj.tenant_id is None


class ShopStyleOptionInputSerializer(serializers.Serializer):
    option_group_id = serializers.UUIDField()
    code = serializers.SlugField(max_length=64)
    translations = TranslationInputSerializer(many=True)

    def validate_translations(self, value):
        locales = [item["locale"] for item in value]
        if len(locales) != len(set(locales)) or "en" not in locales:
            raise serializers.ValidationError(
                "Provide unique translations including English."
            )
        return value


class StyleOptionUpdateSerializer(serializers.Serializer):
    """Allow Shop-owned translation edits without changing immutable identity."""

    translations = TranslationInputSerializer(many=True, required=False)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if set(self.initial_data) != set(attrs):
            raise serializers.ValidationError(
                "Unknown or read-only fields were provided."
            )
        if set(attrs) == {"translations"}:
            if not attrs["translations"]:
                raise serializers.ValidationError(
                    {"translations": "Provide at least one translation to update."}
                )
            locales = [item["locale"] for item in attrs["translations"]]
            if len(locales) != len(set(locales)):
                raise serializers.ValidationError(
                    {"translations": "Each locale may appear only once."}
                )
            return attrs
        if set(attrs) == {"is_active"}:
            return attrs
        raise serializers.ValidationError(
            "Provide either translations or is_active; other fields are immutable."
        )


class DesignVersionSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    translations = serializers.SerializerMethodField()
    selections = serializers.SerializerMethodField()
    references = serializers.SerializerMethodField()

    class Meta:
        model = DesignVersion
        fields = (
            "id",
            "number",
            "name",
            "translations",
            "status",
            "published_at",
            "selections",
            "references",
        )

    @extend_schema_field(OpenApiTypes.STR)
    def get_name(self, obj):
        return translated_name(obj, self.context.get("locale", "en"))

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_translations(self, obj):
        return list(
            obj.translations.order_by("locale").values("locale", "name", "description")
        )

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_selections(self, obj):
        return SelectionSerializer(
            obj.selections.select_related("style_option", "option_group"), many=True
        ).data

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_references(self, obj):
        from django.urls import reverse

        shop_id = self.context.get("shop_id") or obj.design.tenant_id
        is_global = obj.design.tenant_id is None
        direct = [
            {
                "id": str(ref.pk),
                "source": "design",
                "mime_type": ref.mime_type,
                "byte_size": ref.byte_size,
                "width": ref.width,
                "height": ref.height,
                "alt_text": ref.alt_text,
                "content_url": (
                    reverse(
                        "v1:catalog-global-design-reference-image",
                        kwargs={"reference_id": ref.pk},
                    )
                    if is_global
                    else reverse(
                        "v1:shop-design-reference",
                        kwargs={"shop_id": shop_id, "reference_id": ref.pk},
                    )
                ),
            }
            for ref in obj.references.all()
        ]
        selected = [
            {
                "id": str(link.source_image_id),
                "source": "style_option",
                "style_option_id": str(link.selection.style_option_id),
                "style_option_image_id": str(link.source_image_id),
                "mime_type": link.source_image.mime_type,
                "byte_size": link.source_image.byte_size,
                "width": link.source_image.width,
                "height": link.source_image.height,
                "alt_text": link.source_image.alt_text,
                "content_url": (
                    reverse(
                        "v1:catalog-global-style-image",
                        kwargs={
                            "option_id": link.selection.style_option_id,
                            "image_id": link.source_image_id,
                        },
                    )
                    if link.source_image.style_option.tenant_id is None
                    else reverse(
                        "v1:shop-style-image",
                        kwargs={
                            "shop_id": shop_id,
                            "option_id": link.selection.style_option_id,
                            "image_id": link.source_image_id,
                        },
                    )
                ),
            }
            for selection in obj.selections.prefetch_related(
                "reference_images__source_image"
            )
            for link in selection.reference_images.all()
        ]
        return direct + selected


class SelectionSerializer(serializers.ModelSerializer):
    style_option_name = serializers.SerializerMethodField()
    style_option_images = serializers.SerializerMethodField()
    style_option_translations = serializers.SerializerMethodField()

    class Meta:
        model = DesignSelection
        fields = (
            "id",
            "option_group",
            "style_option",
            "selected_code",
            "selected_name_en",
            "style_option_name",
            "style_option_translations",
            "style_option_images",
        )

    @extend_schema_field(OpenApiTypes.STR)
    def get_style_option_name(self, obj):
        locale = self.context.get("locale", "en")
        return (
            obj.translations.filter(locale=locale)
            .values_list("name", flat=True)
            .first()
            or obj.translations.filter(locale="en")
            .values_list("name", flat=True)
            .first()
            or obj.selected_name_en
        )

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_style_option_translations(self, obj):
        return list(
            obj.translations.order_by("locale").values("locale", "name", "description")
        )

    @extend_schema_field(StyleImageSerializer(many=True))
    def get_style_option_images(self, obj):
        return StyleImageSerializer(
            [
                link.source_image
                for link in obj.reference_images.select_related("source_image")
            ],
            many=True,
        ).data


class DesignSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    family_status = serializers.CharField(source="family.status", read_only=True)
    latest_version = serializers.SerializerMethodField()
    latest_published_version = serializers.SerializerMethodField()

    class Meta:
        model = Design
        fields = (
            "id",
            "tenant",
            "family",
            "family_status",
            "variant",
            "name",
            "status",
            "is_default_seeded",
            "latest_version",
            "latest_published_version",
            "created_at",
            "updated_at",
        )

    @extend_schema_field(OpenApiTypes.STR)
    def get_name(self, obj):
        versions = list(obj.versions.all())
        if self.context.get("published_only"):
            versions = [
                version
                for version in versions
                if version.status == DesignVersion.Status.PUBLISHED
            ]
        version = max(versions, key=lambda item: item.number, default=None)
        return (
            translated_name(version, self.context.get("locale", "en"))
            if version
            else ""
        )

    @extend_schema_field(DesignVersionSerializer(allow_null=True))
    def get_latest_version(self, obj):
        versions = list(obj.versions.all())
        if self.context.get("published_only"):
            versions = [
                version
                for version in versions
                if version.status == DesignVersion.Status.PUBLISHED
            ]
        version = max(versions, key=lambda item: item.number, default=None)
        return (
            DesignVersionSerializer(version, context=self.context).data
            if version
            else None
        )

    @extend_schema_field(DesignVersionSerializer(allow_null=True))
    def get_latest_published_version(self, obj):
        versions = [
            version
            for version in obj.versions.all()
            if version.status == DesignVersion.Status.PUBLISHED
        ]
        version = max(versions, key=lambda item: item.number, default=None)
        return (
            DesignVersionSerializer(version, context=self.context).data
            if version
            else None
        )


class DesignPriceInputSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=4)


class DesignCreateSerializer(serializers.Serializer):
    family_id = serializers.UUIDField()
    name = serializers.CharField(max_length=160, trim_whitespace=True)
    translations = TranslationInputSerializer(many=True, required=False)
    source_design_id = serializers.UUIDField(required=False)
    source_version_id = serializers.UUIDField(required=False)
    selection_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True
    )
    idempotency_key = serializers.UUIDField(required=False)
    price = DesignPriceInputSerializer(required=False)

    def validate(self, attrs):
        if bool(attrs.get("source_design_id")) != bool(attrs.get("source_version_id")):
            raise serializers.ValidationError(
                "Copying requires both source design and version IDs."
            )
        if not attrs["name"]:
            raise serializers.ValidationError({"name": "Name must not be blank."})
        selection_ids = attrs.get("selection_ids", [])
        if len(selection_ids) != len(set(selection_ids)):
            raise serializers.ValidationError(
                {"selection_ids": "Each style option may be selected only once."}
            )
        if attrs.get("source_design_id") and selection_ids:
            raise serializers.ValidationError(
                {
                    "selection_ids": "Copied designs cannot add selections during creation."
                }
            )
        translations = attrs.get("translations")
        if translations is not None:
            locales = [item["locale"] for item in translations]
            if len(locales) != len(set(locales)):
                raise serializers.ValidationError(
                    {"translations": "Locales must be unique."}
                )
            english = next(
                (item for item in translations if item["locale"] == "en"), None
            )
            if english is None:
                translations.insert(
                    0, {"locale": "en", "name": attrs["name"], "description": ""}
                )
            else:
                attrs["name"] = english["name"]
        return attrs


class DesignDraftNameUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160, trim_whitespace=True, required=False)
    translations = TranslationInputSerializer(many=True, required=False)


class ShopDesignPriceSerializer(serializers.Serializer):
    design_id = serializers.UUIDField(read_only=True)
    amount = serializers.DecimalField(max_digits=18, decimal_places=4)
    currency = serializers.CharField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class SelectionCreateSerializer(serializers.Serializer):
    style_option_id = serializers.UUIDField()


class FamilyOptionGroupUpdateSerializer(serializers.Serializer):
    option_group_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False
    )
    option_groups = serializers.ListField(child=serializers.DictField(), required=False)

    def validate(self, attrs):
        if ("option_group_ids" in attrs) == ("option_groups" in attrs):
            raise serializers.ValidationError(
                "Provide either option_group_ids or option_groups."
            )
        if "option_group_ids" in attrs:
            ids = attrs["option_group_ids"]
            if len(ids) != len(set(ids)):
                raise serializers.ValidationError(
                    {"option_group_ids": "Provide a unique list."}
                )
            attrs["option_groups"] = [
                {
                    "option_group_id": group_id,
                    "selection_mode": "MULTI",
                    "is_required": False,
                    "sort_order": index,
                }
                for index, group_id in enumerate(ids)
            ]
        attrs["option_groups"] = self._normalize_option_groups(attrs["option_groups"])
        return attrs

    def _normalize_option_groups(self, value):
        normalized = []
        seen = set()
        for index, item in enumerate(value):
            if set(item) - {
                "option_group_id",
                "selection_mode",
                "is_required",
                "sort_order",
            }:
                raise serializers.ValidationError(
                    {index: "Unsupported option-group mapping fields."}
                )
            try:
                group_id = serializers.UUIDField().run_validation(
                    item.get("option_group_id")
                )
                mode = serializers.ChoiceField(
                    choices=("SINGLE", "MULTI")
                ).run_validation(item.get("selection_mode", "MULTI"))
                required = serializers.BooleanField().run_validation(
                    item.get("is_required", False)
                )
                sort_order = serializers.IntegerField(
                    min_value=0, max_value=32767
                ).run_validation(item.get("sort_order", index))
            except serializers.ValidationError as exc:
                raise serializers.ValidationError({index: exc.detail}) from exc
            if group_id in seen:
                raise serializers.ValidationError("Option groups must be unique.")
            seen.add(group_id)
            normalized.append(
                {
                    "option_group_id": group_id,
                    "selection_mode": mode,
                    "is_required": required,
                    "sort_order": sort_order,
                }
            )
        return normalized


class ShopGarmentRecordInputSerializer(GlobalCatalogRecordInputSerializer):
    """A Shop-owned family or option-group definition with localized names."""


class ShopFamilyOptionGroupCreateSerializer(ShopGarmentRecordInputSerializer):
    selection_mode = serializers.ChoiceField(
        choices=FamilyOptionGroup.SelectionMode.choices,
        default=FamilyOptionGroup.SelectionMode.MULTI,
    )
    is_required = serializers.BooleanField(default=False)


class ReferenceImageUploadSerializer(serializers.Serializer):
    images = serializers.ListField(child=serializers.FileField(), allow_empty=False)


class DesignReferenceGallerySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    source = serializers.ChoiceField(choices=("design", "style_option"))
    mime_type = serializers.CharField()
    byte_size = serializers.IntegerField()
    width = serializers.IntegerField()
    height = serializers.IntegerField()
    alt_text = serializers.CharField(allow_blank=True)
    content_url = serializers.CharField()
    style_option_id = serializers.UUIDField(required=False)
    style_option_image_id = serializers.UUIDField(required=False)


class PublishResponseSerializer(serializers.Serializer):
    published = DesignVersionSerializer()
    next_draft = DesignVersionSerializer()


class DesignReferenceSerializer(serializers.ModelSerializer):
    content_url = serializers.SerializerMethodField()

    class Meta:
        model = DesignReference
        fields = (
            "id",
            "mime_type",
            "byte_size",
            "width",
            "height",
            "sort_order",
            "alt_text",
            "content_url",
        )

    @extend_schema_field(OpenApiTypes.STR)
    def get_content_url(self, obj):
        from django.urls import reverse

        design = obj.version.design
        if design.tenant_id is None:
            return reverse(
                "v1:catalog-global-design-reference-image",
                kwargs={"reference_id": obj.pk},
            )
        return reverse(
            "v1:shop-design-reference",
            kwargs={"shop_id": design.tenant_id, "reference_id": obj.pk},
        )
