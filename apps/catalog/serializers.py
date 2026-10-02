from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from apps.catalog.models import (
    Design,
    DesignReference,
    DesignSelection,
    DesignVersion,
    GarmentFamily,
    GarmentVariant,
    OptionGroup,
    StyleOption,
    StyleOptionImage,
)


def translated_name(record, locale):
    translations = record.translations.all()
    return (
        translations.filter(locale=locale).values_list("name", flat=True).first()
        or translations.filter(locale="en").values_list("name", flat=True).first()
        or getattr(record, "code", "")
    )


class FamilySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = GarmentFamily
        fields = ("id", "code", "name")

    @extend_schema_field(OpenApiTypes.STR)
    def get_name(self, obj):
        return translated_name(obj, self.context.get("locale", "en"))


class TranslationInputSerializer(serializers.Serializer):
    locale = serializers.ChoiceField(choices=("en", "ar-KW", "bn", "ur"))
    name = serializers.CharField(max_length=120, trim_whitespace=True)
    description = serializers.CharField(required=False, allow_blank=True)


class VariantSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = GarmentVariant
        fields = ("id", "family", "code", "name", "is_default")

    @extend_schema_field(OpenApiTypes.STR)
    def get_name(self, obj):
        return translated_name(obj, self.context.get("locale", "en"))


class ShopVariantInputSerializer(serializers.Serializer):
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


class OptionGroupSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    families = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = OptionGroup
        fields = ("id", "code", "name", "families")

    @extend_schema_field(OpenApiTypes.STR)
    def get_name(self, obj):
        return translated_name(obj, self.context.get("locale", "en"))


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
    reference_images = StyleImageSerializer(many=True, read_only=True)
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
    latest_version = serializers.SerializerMethodField()

    class Meta:
        model = Design
        fields = (
            "id",
            "tenant",
            "family",
            "variant",
            "name",
            "status",
            "latest_version",
            "created_at",
            "updated_at",
        )

    @extend_schema_field(OpenApiTypes.STR)
    def get_name(self, obj):
        versions = obj.versions.all()
        if self.context.get("published_only"):
            versions = versions.filter(status=DesignVersion.Status.PUBLISHED)
        version = versions.order_by("-number").first()
        return (
            translated_name(version, self.context.get("locale", "en"))
            if version
            else ""
        )

    @extend_schema_field(DesignVersionSerializer(allow_null=True))
    def get_latest_version(self, obj):
        versions = obj.versions.all()
        if self.context.get("published_only"):
            versions = versions.filter(status=DesignVersion.Status.PUBLISHED)
        version = versions.order_by("-number").first()
        return (
            DesignVersionSerializer(version, context=self.context).data
            if version
            else None
        )


class DesignCreateSerializer(serializers.Serializer):
    family_id = serializers.UUIDField()
    variant_id = serializers.UUIDField()
    name = serializers.CharField(max_length=160, trim_whitespace=True)
    translations = TranslationInputSerializer(many=True, required=False)
    source_design_id = serializers.UUIDField(required=False)
    source_version_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if bool(attrs.get("source_design_id")) != bool(attrs.get("source_version_id")):
            raise serializers.ValidationError(
                "Copying requires both source design and version IDs."
            )
        if not attrs["name"]:
            raise serializers.ValidationError({"name": "Name must not be blank."})
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


class SelectionCreateSerializer(serializers.Serializer):
    style_option_id = serializers.UUIDField()


class FamilyOptionGroupUpdateSerializer(serializers.Serializer):
    option_group_ids = serializers.ListField(child=serializers.UUIDField())


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
