"""Shop-context APIs for measurement history and material references."""

from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from apps.accounts.permissions import PasswordChangeGate
from apps.catalog.measurement_models import (
    Material,
    MeasurementDefinition,
    MeasurementDefinitionMapping,
    MeasurementDefinitionTranslation,
    MeasurementProfile,
    MeasurementSet,
)
from apps.catalog.measurement_serializers import (
    MaterialCreateSerializer,
    MaterialPatchSerializer,
    MaterialSerializer,
    MeasurementDefinitionCreateSerializer,
    MeasurementDefinitionPatchSerializer,
    MeasurementDefinitionReadSerializer,
    MeasurementProfileCreateSerializer,
    MeasurementProfileSerializer,
    MeasurementSetCreateSerializer,
    MeasurementSetSerializer,
)
from apps.catalog.measurement_services import (
    archive_material,
    archive_measurement_definition,
    copy_measurement_set,
    create_material,
    create_measurement_definition,
    create_measurement_profile,
    create_measurement_set,
    require_material_access,
    require_measurement_access,
    update_material,
)
from apps.clients.models import Client, RelatedPerson
from apps.common.views import TenantScopedMixin
from apps.tenants.context_views import ShopContextMixin


class CatalogPagination(PageNumberPagination):
    page_size = 20


class MeasurementAccess(BasePermission):
    def has_permission(self, request, view):
        require_measurement_access(
            request.shop_context.shop.pk,
            request.user,
            write=request.method not in ("GET", "HEAD", "OPTIONS"),
            archive=getattr(view, "measurement_archive_action", False),
        )
        return True


class MaterialAccess(BasePermission):
    def has_permission(self, request, view):
        require_material_access(
            request.shop_context.shop.pk,
            request.user,
            write=request.method not in ("GET", "HEAD", "OPTIONS"),
        )
        return True


def _locale(request):
    locale = request.query_params.get("locale", "en")
    return locale if locale in {"en", "ar-KW", "bn", "ur"} else "en"


def _paginated(request, queryset, serializer_class, *, context=None):
    paginator = CatalogPagination()
    page = paginator.paginate_queryset(queryset, request)
    return paginator.get_paginated_response(
        serializer_class(page, many=True, context=context or {}).data
    )


def _page_schema(name, item_serializer):
    return inline_serializer(
        name=name,
        fields={
            "count": serializers.IntegerField(),
            "next": serializers.URLField(allow_null=True),
            "previous": serializers.URLField(allow_null=True),
            "results": item_serializer(many=True),
        },
    )


class PersonProfileMixin:
    person_model = None

    def get_person_model(self):
        return self.kwargs.get("person_model", self.person_model)

    def get_person(self):
        shop = self.request.shop_context.shop
        if self.get_person_model() is Client:
            person = Client.objects.filter(
                pk=self.kwargs["client_id"], tenant=shop, deleted__isnull=True
            ).first()
        else:
            parent = Client.objects.filter(
                pk=self.kwargs["client_id"], tenant=shop, deleted__isnull=True
            ).first()
            person = None
            if parent:
                person = RelatedPerson.objects.filter(
                    pk=self.kwargs["related_person_id"],
                    tenant=shop,
                    primary_client=parent,
                    deleted__isnull=True,
                ).first()
        if person is None:
            raise NotFound()
        return person

    def owner_filter(self, person):
        if self.get_person_model() is Client:
            return {"client": person, "related_person__isnull": True}
        return {"related_person": person, "client__isnull": True}


class MeasurementDefinitionListCreateView(ShopContextMixin, TenantScopedMixin, APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate, MeasurementAccess)

    @extend_schema(
        operation_id="measurement_definitions_list",
        parameters=[
            OpenApiParameter(
                "family_id",
                OpenApiTypes.UUID,
                OpenApiParameter.QUERY,
                description="Optional garment-family filter.",
            ),
            OpenApiParameter(
                "variant_id",
                OpenApiTypes.UUID,
                OpenApiParameter.QUERY,
                description="Optional variant filter; requires family_id.",
            ),
        ],
        responses=_page_schema(
            "MeasurementDefinitionPage", MeasurementDefinitionReadSerializer
        ),
        description=(
            "Lists global approved definitions and active definitions for the selected "
            "Shop. Only Shop ADMIN, Main Supplier in this explicit Shop context, or "
            "STAFF assigned MEASUREMENT may access measurement data."
        ),
    )
    def get(self, request, shop_id):
        rows = (
            MeasurementDefinition.objects.filter(is_active=True)
            .filter(Q(tenant__isnull=True) | Q(tenant=request.shop_context.shop))
            .prefetch_related("translations", "mappings")
            .order_by("sort_order", "code", "id")
        )
        family_raw = request.query_params.get("family_id")
        variant_raw = request.query_params.get("variant_id")
        if variant_raw and not family_raw:
            raise serializers.ValidationError(
                {"family_id": "Required when variant_id is supplied."}
            )
        family_id = (
            serializers.UUIDField().run_validation(family_raw) if family_raw else None
        )
        variant_id = (
            serializers.UUIDField().run_validation(variant_raw) if variant_raw else None
        )
        if family_id:
            applicable_mappings = MeasurementDefinitionMapping.objects.filter(
                definition_id=OuterRef("pk"),
                family_id=family_id,
                deleted__isnull=True,
            )
            if variant_id:
                applicable_mappings = applicable_mappings.filter(
                    Q(variant__isnull=True) | Q(variant_id=variant_id)
                )
            else:
                applicable_mappings = applicable_mappings.filter(variant__isnull=True)
            rows = rows.filter(Exists(applicable_mappings)).order_by(
                "sort_order", "code", "id"
            )
        return _paginated(
            request,
            rows,
            MeasurementDefinitionReadSerializer,
            context={"locale": _locale(request)},
        )

    @extend_schema(
        operation_id="measurement_definitions_create",
        request=MeasurementDefinitionCreateSerializer,
        responses={201: MeasurementDefinitionReadSerializer},
    )
    def post(self, request, shop_id):
        serializer = MeasurementDefinitionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        definition = create_measurement_definition(
            shop_id=request.shop_context.shop.pk,
            actor=request.user,
            code=data["code"],
            group_code=data.get("group_code", ""),
            sort_order=data.get("sort_order", 0),
            translations=data["translations"],
            mappings=data["mappings"],
        )
        definition = MeasurementDefinition.objects.prefetch_related(
            "translations", "mappings"
        ).get(pk=definition.pk)
        return Response(
            MeasurementDefinitionReadSerializer(definition).data,
            status=status.HTTP_201_CREATED,
        )


class MeasurementDefinitionDetailView(ShopContextMixin, TenantScopedMixin, APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate, MeasurementAccess)

    def _get(self, request, definition_id):
        return (
            MeasurementDefinition.objects.filter(
                pk=definition_id,
                is_active=True,
            )
            .filter(Q(tenant__isnull=True) | Q(tenant=request.shop_context.shop))
            .prefetch_related("translations", "mappings")
            .first()
        )

    @extend_schema(
        operation_id="measurement_definition_detail",
        responses=MeasurementDefinitionReadSerializer,
    )
    def get(self, request, shop_id, definition_id):
        definition = self._get(request, definition_id)
        if definition is None:
            raise NotFound()
        return Response(MeasurementDefinitionReadSerializer(definition).data)

    @extend_schema(
        operation_id="measurement_definition_update",
        request=MeasurementDefinitionPatchSerializer,
        responses=MeasurementDefinitionReadSerializer,
    )
    def patch(self, request, shop_id, definition_id):
        definition = self._get(request, definition_id)
        if definition is None or definition.tenant_id is None:
            raise NotFound()
        membership = request.shop_context.membership
        if (
            membership
            and membership.role == "STAFF"
            and definition.created_by_id != request.user.pk
        ):
            raise PermissionDenied()
        serializer = MeasurementDefinitionPatchSerializer(
            data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            definition = MeasurementDefinition.objects.select_for_update().get(
                pk=definition.pk
            )
            for key in ("group_code", "sort_order"):
                if key in serializer.validated_data:
                    setattr(definition, key, serializer.validated_data[key])
            definition.updated_by = request.user
            definition.save()
            for translation in serializer.validated_data.get("translations", []):
                existing = MeasurementDefinitionTranslation.objects.filter(
                    definition=definition, locale=translation["locale"]
                ).first()
                if existing:
                    existing.name = translation["name"]
                    existing.description = translation.get("description", "")
                    existing.updated_by = request.user
                    existing.save(
                        update_fields=(
                            "name",
                            "description",
                            "updated_by",
                            "updated_at",
                        )
                    )
                else:
                    MeasurementDefinitionTranslation.objects.create(
                        definition=definition,
                        created_by=request.user,
                        updated_by=request.user,
                        **translation,
                    )
        definition = MeasurementDefinition.objects.prefetch_related(
            "translations", "mappings"
        ).get(pk=definition.pk)
        return Response(MeasurementDefinitionReadSerializer(definition).data)


class MeasurementDefinitionArchiveView(ShopContextMixin, TenantScopedMixin, APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate, MeasurementAccess)
    measurement_archive_action = True

    @extend_schema(
        operation_id="measurement_definition_archive",
        request=None,
        responses=MeasurementDefinitionReadSerializer,
    )
    def post(self, request, shop_id, definition_id):
        definition = archive_measurement_definition(
            shop_id=request.shop_context.shop.pk,
            actor=request.user,
            definition_id=definition_id,
        )
        return Response(MeasurementDefinitionReadSerializer(definition).data)


class MeasurementProfileListCreateView(
    PersonProfileMixin, ShopContextMixin, TenantScopedMixin, APIView
):
    permission_classes = (IsAuthenticated, PasswordChangeGate, MeasurementAccess)

    @extend_schema(
        responses=_page_schema("MeasurementProfilePage", MeasurementProfileSerializer)
    )
    def get(self, request, shop_id, client_id, **kwargs):
        person = self.get_person()
        rows = (
            MeasurementProfile.objects.filter(
                tenant=request.shop_context.shop, **self.owner_filter(person)
            )
            .select_related("family", "variant")
            .order_by("family__code", "variant__code", "created_at", "id")
        )
        return _paginated(request, rows, MeasurementProfileSerializer)

    @extend_schema(
        request=MeasurementProfileCreateSerializer,
        responses={201: MeasurementProfileSerializer},
    )
    def post(self, request, shop_id, client_id, **kwargs):
        person = self.get_person()
        serializer = MeasurementProfileCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = create_measurement_profile(
            shop_id=request.shop_context.shop.pk,
            actor=request.user,
            person_model=self.get_person_model(),
            person_id=person.pk,
            **serializer.validated_data,
        )
        return Response(
            MeasurementProfileSerializer(profile).data, status=status.HTTP_201_CREATED
        )


class ClientMeasurementProfilesView(MeasurementProfileListCreateView):
    person_model = Client


class RelatedPersonMeasurementProfilesView(MeasurementProfileListCreateView):
    person_model = RelatedPerson


class MeasurementProfileDetailView(
    PersonProfileMixin, ShopContextMixin, TenantScopedMixin, APIView
):
    permission_classes = (IsAuthenticated, PasswordChangeGate, MeasurementAccess)

    def _profile(self, request, profile_id):
        person = self.get_person()
        profile = (
            MeasurementProfile.objects.filter(
                pk=profile_id,
                tenant=request.shop_context.shop,
                **self.owner_filter(person),
            )
            .select_related("family", "variant")
            .first()
        )
        if profile is None:
            raise NotFound()
        return profile

    @extend_schema(
        responses=MeasurementProfileSerializer,
    )
    def get(self, request, shop_id, client_id, profile_id, **kwargs):
        return Response(
            MeasurementProfileSerializer(self._profile(request, profile_id)).data
        )


class MeasurementSetListCreateView(
    PersonProfileMixin, ShopContextMixin, TenantScopedMixin, APIView
):
    permission_classes = (IsAuthenticated, PasswordChangeGate, MeasurementAccess)

    def _profile(self, request, profile_id):
        person = self.get_person()
        profile = MeasurementProfile.objects.filter(
            pk=profile_id, tenant=request.shop_context.shop, **self.owner_filter(person)
        ).first()
        if profile is None:
            raise NotFound()
        return profile

    @extend_schema(
        responses=_page_schema("MeasurementSetPage", MeasurementSetSerializer)
    )
    def get(self, request, shop_id, client_id, profile_id, **kwargs):
        profile = self._profile(request, profile_id)
        rows = (
            MeasurementSet.objects.filter(profile=profile)
            .prefetch_related("values__label_translations")
            .order_by("-version", "id")
        )
        return _paginated(
            request,
            rows,
            MeasurementSetSerializer,
            context={"locale": _locale(request)},
        )

    @extend_schema(
        request=MeasurementSetCreateSerializer,
        responses={201: MeasurementSetSerializer},
    )
    def post(self, request, shop_id, client_id, profile_id, **kwargs):
        profile = self._profile(request, profile_id)
        serializer = MeasurementSetCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        measurement_set = create_measurement_set(
            shop_id=request.shop_context.shop.pk,
            actor=request.user,
            profile_id=profile.pk,
            values=serializer.validated_data["values"],
        )
        measurement_set = MeasurementSet.objects.prefetch_related(
            "values__label_translations"
        ).get(pk=measurement_set.pk)
        return Response(
            MeasurementSetSerializer(
                measurement_set, context={"locale": _locale(request)}
            ).data,
            status=status.HTTP_201_CREATED,
        )


class MeasurementSetDetailView(
    PersonProfileMixin, ShopContextMixin, TenantScopedMixin, APIView
):
    permission_classes = (IsAuthenticated, PasswordChangeGate, MeasurementAccess)

    @extend_schema(
        responses=MeasurementSetSerializer,
    )
    def get(self, request, shop_id, client_id, profile_id, set_id, **kwargs):
        person = self.get_person()
        profile = MeasurementProfile.objects.filter(
            pk=profile_id, tenant=request.shop_context.shop, **self.owner_filter(person)
        ).first()
        if profile is None:
            raise NotFound()
        record = (
            MeasurementSet.objects.filter(profile=profile, pk=set_id)
            .prefetch_related("values__label_translations")
            .first()
        )
        if record is None:
            raise NotFound()
        return Response(
            MeasurementSetSerializer(record, context={"locale": _locale(request)}).data
        )


class MeasurementSetCopyView(
    PersonProfileMixin, ShopContextMixin, TenantScopedMixin, APIView
):
    permission_classes = (IsAuthenticated, PasswordChangeGate, MeasurementAccess)

    @extend_schema(
        request=None,
        responses={201: MeasurementSetSerializer},
    )
    def post(self, request, shop_id, client_id, profile_id, set_id, **kwargs):
        person = self.get_person()
        profile = MeasurementProfile.objects.filter(
            pk=profile_id, tenant=request.shop_context.shop, **self.owner_filter(person)
        ).first()
        if profile is None:
            raise NotFound()
        copied = copy_measurement_set(
            shop_id=request.shop_context.shop.pk,
            actor=request.user,
            profile_id=profile.pk,
            source_set_id=set_id,
        )
        copied = MeasurementSet.objects.prefetch_related(
            "values__label_translations"
        ).get(pk=copied.pk)
        return Response(
            MeasurementSetSerializer(copied, context={"locale": _locale(request)}).data,
            status=status.HTTP_201_CREATED,
        )


class MeasurementCompareView(
    PersonProfileMixin, ShopContextMixin, TenantScopedMixin, APIView
):
    permission_classes = (IsAuthenticated, PasswordChangeGate, MeasurementAccess)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "from_set_id", OpenApiTypes.UUID, OpenApiParameter.QUERY, required=True
            ),
            OpenApiParameter(
                "to_set_id", OpenApiTypes.UUID, OpenApiParameter.QUERY, required=True
            ),
        ],
        responses=inline_serializer(
            name="MeasurementComparison",
            fields={
                "from_set_id": serializers.UUIDField(),
                "to_set_id": serializers.UUIDField(),
                "results": serializers.ListField(
                    child=inline_serializer(
                        name="MeasurementComparisonItem",
                        fields={
                            "definition_id": serializers.UUIDField(),
                            "code": serializers.CharField(),
                            "label": serializers.CharField(),
                            "from_value": serializers.CharField(allow_null=True),
                            "from_unit": serializers.CharField(allow_null=True),
                            "to_value": serializers.CharField(allow_null=True),
                            "to_unit": serializers.CharField(allow_null=True),
                            "difference": serializers.CharField(allow_null=True),
                            "unit_mismatch": serializers.BooleanField(),
                        },
                    )
                ),
            },
        ),
        description="Compares immutable sets. Difference is numeric only when both values use the same explicit unit; values are never converted.",
    )
    def get(self, request, shop_id, client_id, profile_id, **kwargs):
        person = self.get_person()
        profile = MeasurementProfile.objects.filter(
            pk=profile_id, tenant=request.shop_context.shop, **self.owner_filter(person)
        ).first()
        if profile is None:
            raise NotFound()
        from_id = request.query_params.get("from_set_id")
        to_id = request.query_params.get("to_set_id")
        if not from_id or not to_id or from_id == to_id:
            raise serializers.ValidationError(
                {"from_set_id": "Provide two different set IDs."}
            )
        from_id = serializers.UUIDField().run_validation(from_id)
        to_id = serializers.UUIDField().run_validation(to_id)
        sets = list(
            MeasurementSet.objects.filter(
                profile=profile, pk__in=(from_id, to_id)
            ).prefetch_related("values__label_translations")
        )
        by_id = {item.pk: item for item in sets}
        if from_id not in by_id or to_id not in by_id:
            raise NotFound()
        older, newer = by_id[from_id], by_id[to_id]
        old_values = {str(item.definition_id): item for item in older.values.all()}
        new_values = {str(item.definition_id): item for item in newer.values.all()}
        results = []
        for key in sorted(old_values.keys() | new_values.keys()):
            before, after = old_values.get(key), new_values.get(key)
            same_unit = (
                before is not None and after is not None and before.unit == after.unit
            )
            results.append(
                {
                    "definition_id": key,
                    "code": (after or before).definition_code_snapshot,
                    "label": (after or before).label_snapshot,
                    "from_value": str(before.value) if before else None,
                    "from_unit": before.unit if before else None,
                    "to_value": str(after.value) if after else None,
                    "to_unit": after.unit if after else None,
                    "difference": (
                        str(after.value - before.value) if same_unit else None
                    ),
                    "unit_mismatch": before is not None
                    and after is not None
                    and before.unit != after.unit,
                }
            )
        return Response(
            {"from_set_id": older.pk, "to_set_id": newer.pk, "results": results}
        )


class MaterialListCreateView(ShopContextMixin, TenantScopedMixin, APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate, MaterialAccess)

    @extend_schema(
        operation_id="materials_list",
        responses=_page_schema("MaterialPage", MaterialSerializer),
    )
    def get(self, request, shop_id):
        rows = Material.objects.filter(
            tenant=request.shop_context.shop, deleted__isnull=True
        )
        include_archived = request.query_params.get("include_archived") == "true"
        if not include_archived or (
            request.shop_context.membership
            and request.shop_context.membership.role != "ADMIN"
        ):
            rows = rows.filter(status=Material.Status.ACTIVE)
        rows = rows.order_by("name", "id")
        return _paginated(request, rows, MaterialSerializer)

    @extend_schema(
        operation_id="materials_create",
        request=MaterialCreateSerializer,
        responses={201: MaterialSerializer},
    )
    def post(self, request, shop_id):
        serializer = MaterialCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        material = create_material(
            shop_id=request.shop_context.shop.pk,
            actor=request.user,
            **serializer.validated_data,
        )
        return Response(
            MaterialSerializer(material).data, status=status.HTTP_201_CREATED
        )


class MaterialDetailView(ShopContextMixin, TenantScopedMixin, APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate, MaterialAccess)

    def _get(self, request, material_id, *, include_archived=False):
        rows = Material.objects.filter(
            pk=material_id, tenant=request.shop_context.shop, deleted__isnull=True
        )
        if not include_archived:
            rows = rows.filter(status=Material.Status.ACTIVE)
        material = rows.first()
        if material is None:
            raise NotFound()
        return material

    @extend_schema(operation_id="material_detail", responses=MaterialSerializer)
    def get(self, request, shop_id, material_id):
        include_archived = bool(
            request.shop_context.is_main_supplier
            or request.shop_context.role == "ADMIN"
        )
        return Response(
            MaterialSerializer(
                self._get(request, material_id, include_archived=include_archived)
            ).data
        )

    @extend_schema(
        operation_id="material_update",
        request=MaterialPatchSerializer,
        responses=MaterialSerializer,
    )
    def patch(self, request, shop_id, material_id):
        material = self._get(request, material_id)
        serializer = MaterialPatchSerializer(material, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        material = update_material(
            shop_id=request.shop_context.shop.pk,
            actor=request.user,
            material_id=material.pk,
            values=serializer.validated_data,
        )
        return Response(MaterialSerializer(material).data)


class MaterialArchiveView(ShopContextMixin, TenantScopedMixin, APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate, MaterialAccess)

    @extend_schema(
        operation_id="material_archive", request=None, responses=MaterialSerializer
    )
    def post(self, request, shop_id, material_id):
        material = archive_material(
            shop_id=request.shop_context.shop.pk,
            actor=request.user,
            material_id=material_id,
        )
        return Response(MaterialSerializer(material).data)
