from collections.abc import Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from apps.catalog.models import DesignVersion, Material, MeasurementSet
from apps.catalog.serializers import translated_name
from apps.clients.models import Client, RelatedPerson
from apps.tenants.models import TenantMember
from apps.works.constants import WorkPriority, WorkStatus
from apps.works.services import due_indicator


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, Mapping):
            return super().to_internal_value(data)
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError(
                {key: "Unknown field." for key in unknown}
            )
        return super().to_internal_value(data)


class WorkCreateSerializer(StrictSerializer):
    client_id = serializers.PrimaryKeyRelatedField(
        source="client", queryset=Client.objects.all()
    )
    related_person_id = serializers.PrimaryKeyRelatedField(
        source="related_person",
        queryset=RelatedPerson.objects.all(),
        required=False,
        allow_null=True,
    )
    design_version_id = serializers.PrimaryKeyRelatedField(
        source="design_version", queryset=DesignVersion.objects.all()
    )
    measurement_set_id = serializers.PrimaryKeyRelatedField(
        source="measurement_set", queryset=MeasurementSet.objects.all()
    )
    material_id = serializers.PrimaryKeyRelatedField(
        source="material",
        queryset=Material.objects.all(),
        required=False,
        allow_null=True,
    )
    priority = serializers.ChoiceField(choices=WorkPriority.choices, required=False)
    due_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=5000)

    def validate(self, attrs):
        shop_id = self.context["request"].shop_context.shop.pk
        linked = (
            ("client", lambda item: item.tenant_id == shop_id),
            ("related_person", lambda item: item.tenant_id == shop_id),
            ("design_version", lambda item: item.design.tenant_id in (None, shop_id)),
            ("measurement_set", lambda item: item.profile.tenant_id == shop_id),
            ("material", lambda item: item.tenant_id == shop_id),
        )
        for field, valid in linked:
            item = attrs.get(field)
            if item is not None and not valid(item):
                raise serializers.ValidationError(
                    {field: "Not available in this Shop."}
                )
        return attrs


class WorkUpdateSerializer(StrictSerializer):
    priority = serializers.ChoiceField(choices=WorkPriority.choices, required=False)
    due_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=5000)


class WorkAssignmentSerializer(StrictSerializer):
    membership_id = serializers.PrimaryKeyRelatedField(
        source="membership", queryset=TenantMember.objects.all(), allow_null=True
    )

    def validate_membership_id(self, membership):
        if (
            membership
            and membership.tenant_id != self.context["request"].shop_context.shop.pk
        ):
            raise serializers.ValidationError("Not available in this Shop.")
        return membership


class WorkAdvanceSerializer(StrictSerializer):
    expected_status = serializers.ChoiceField(choices=WorkStatus.choices)


class WorkSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    work_number = serializers.CharField(read_only=True)
    client_id = serializers.UUIDField(read_only=True)
    related_person_id = serializers.UUIDField(read_only=True, allow_null=True)
    design_version_id = serializers.UUIDField(read_only=True)
    measurement_set_id = serializers.UUIDField(read_only=True)
    material_id = serializers.UUIDField(read_only=True, allow_null=True)
    assigned_membership_id = serializers.UUIDField(read_only=True, allow_null=True)
    status = serializers.CharField(read_only=True)
    priority = serializers.CharField(read_only=True)
    due_date = serializers.DateField(read_only=True, allow_null=True)
    due_indicator = serializers.SerializerMethodField()
    notes = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def get_due_indicator(self, obj) -> str | None:
        return due_indicator(obj)


class DeletedWorkFiltersSerializer(serializers.Serializer):
    deleted_from = serializers.DateField(required=False)
    deleted_to = serializers.DateField(required=False)

    def validate(self, attrs):
        if attrs.get("deleted_from") and attrs.get("deleted_to"):
            if attrs["deleted_from"] > attrs["deleted_to"]:
                raise serializers.ValidationError(
                    {"deleted_to": "Must be on or after deleted_from."}
                )
        return attrs


class DeletedWorkSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    work_number = serializers.CharField(read_only=True)
    client_name = serializers.CharField(source="client.name", read_only=True)
    design_name = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    priority = serializers.CharField(read_only=True)
    due_date = serializers.DateField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    deleted = serializers.DateTimeField(read_only=True)
    deleted_date = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.STR)
    def get_design_name(self, obj):
        return translated_name(obj.design_version, "en")

    @extend_schema_field(OpenApiTypes.DATE)
    def get_deleted_date(self, obj):
        try:
            zone = ZoneInfo(obj.tenant.default_timezone or settings.TIME_ZONE)
        except ZoneInfoNotFoundError:
            zone = ZoneInfo(settings.TIME_ZONE)
        return timezone.localtime(obj.deleted, zone).date().isoformat()
