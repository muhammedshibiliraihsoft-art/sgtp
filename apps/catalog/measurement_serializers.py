"""OpenAPI-backed request and response serializers for T4-03 resources."""

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from apps.catalog.measurement_models import (
    Material,
    MeasurementDefinition,
    MeasurementProfile,
    MeasurementSet,
    MeasurementValue,
)


class MeasurementTranslationSerializer(serializers.Serializer):
    locale = serializers.ChoiceField(choices=("en", "ar-KW", "bn", "ur"))
    name = serializers.CharField(max_length=120, trim_whitespace=True)
    description = serializers.CharField(required=False, allow_blank=True)


class MeasurementMappingInputSerializer(serializers.Serializer):
    family_id = serializers.UUIDField()
    variant_id = serializers.UUIDField(required=False, allow_null=True)


class MeasurementDefinitionCreateSerializer(serializers.Serializer):
    code = serializers.SlugField(max_length=64)
    group_code = serializers.CharField(max_length=48, required=False, allow_blank=True)
    sort_order = serializers.IntegerField(min_value=0, max_value=32767, required=False)
    translations = MeasurementTranslationSerializer(many=True)
    mappings = MeasurementMappingInputSerializer(many=True, allow_empty=False)

    def validate_translations(self, value):
        locales = [item["locale"] for item in value]
        if len(locales) != len(set(locales)) or "en" not in locales:
            raise serializers.ValidationError(
                "Provide unique translations including English."
            )
        return value

    def validate_mappings(self, value):
        keys = [(item["family_id"], item.get("variant_id")) for item in value]
        if len(keys) != len(set(keys)):
            raise serializers.ValidationError("Mappings must be unique.")
        return value


class MeasurementDefinitionPatchSerializer(serializers.Serializer):
    group_code = serializers.CharField(max_length=48, required=False, allow_blank=True)
    sort_order = serializers.IntegerField(min_value=0, max_value=32767, required=False)
    translations = MeasurementTranslationSerializer(many=True, required=False)

    def validate_translations(self, value):
        locales = [item["locale"] for item in value]
        if len(locales) != len(set(locales)):
            raise serializers.ValidationError("Locales must be unique.")
        return value


class MeasurementDefinitionTranslationReadSerializer(serializers.Serializer):
    locale = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()


class MeasurementDefinitionReadSerializer(serializers.ModelSerializer):
    is_global = serializers.SerializerMethodField()
    translations = MeasurementDefinitionTranslationReadSerializer(
        many=True, read_only=True
    )
    mappings = serializers.SerializerMethodField()

    class Meta:
        model = MeasurementDefinition
        fields = (
            "id",
            "code",
            "group_code",
            "sort_order",
            "is_active",
            "is_global",
            "translations",
            "mappings",
        )

    @extend_schema_field(serializers.BooleanField())
    def get_is_global(self, obj):
        return obj.tenant_id is None

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_mappings(self, obj):
        return [
            {
                "family_id": str(item.family_id),
                "variant_id": str(item.variant_id) if item.variant_id else None,
                "sort_order": item.sort_order,
            }
            for item in obj.mappings.filter(deleted__isnull=True).order_by(
                "family__code", "sort_order", "variant_id"
            )
        ]


class MeasurementProfileCreateSerializer(serializers.Serializer):
    family_id = serializers.UUIDField()
    variant_id = serializers.UUIDField(required=False, allow_null=True)


class MeasurementProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementProfile
        fields = ("id", "client", "related_person", "family", "variant", "created_at")
        read_only_fields = fields


class MeasurementValueInputSerializer(serializers.Serializer):
    definition_id = serializers.UUIDField()
    value = serializers.DecimalField(max_digits=12, decimal_places=4)
    unit = serializers.ChoiceField(choices=MeasurementSet.Unit.choices)


class MeasurementSetCreateSerializer(serializers.Serializer):
    values = MeasurementValueInputSerializer(many=True, allow_empty=False)

    def validate_values(self, value):
        ids = [item["definition_id"] for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                "A definition may appear only once per set."
            )
        return value


class MeasurementValueSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    translations = serializers.SerializerMethodField()

    class Meta:
        model = MeasurementValue
        fields = (
            "id",
            "definition",
            "definition_code_snapshot",
            "label_snapshot",
            "label",
            "translations",
            "value",
            "unit",
        )

    def _translation(self, obj, locale):
        rows = {item.locale: item.name for item in obj.label_translations.all()}
        return rows.get(locale) or rows.get("en") or obj.label_snapshot

    @extend_schema_field(serializers.CharField())
    def get_label(self, obj):
        return self._translation(obj, self.context.get("locale", "en"))

    @extend_schema_field(serializers.DictField(child=serializers.CharField()))
    def get_translations(self, obj):
        return {item.locale: item.name for item in obj.label_translations.all()}


class MeasurementSetSerializer(serializers.ModelSerializer):
    values = MeasurementValueSerializer(many=True, read_only=True)

    class Meta:
        model = MeasurementSet
        fields = ("id", "profile", "version", "copied_from", "created_at", "values")


class MaterialCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ("name", "code", "description")


class MaterialPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ("name", "code", "description")


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = (
            "id",
            "name",
            "code",
            "description",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
