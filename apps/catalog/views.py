from django.http import FileResponse, Http404
from django.conf import settings
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Prefetch, Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer

from apps.catalog.models import (
    Design,
    DesignReference,
    DesignSelection,
    DesignSelectionTranslation,
    DesignVersion,
    DesignVersionTranslation,
    FamilyOptionGroup,
    GarmentFamily,
    GarmentFamilyTranslation,
    GarmentVariant,
    OptionGroup,
    OptionGroupTranslation,
    StyleOption,
    StyleOptionImage,
    StyleOptionTranslation,
)
from apps.catalog.serializers import (
    DesignListQuerySerializer,
    DesignCreateSerializer,
    DesignDraftNameUpdateSerializer,
    DesignReferenceSerializer,
    DesignSerializer,
    DesignVersionSerializer,
    DesignReferenceGallerySerializer,
    FamilyOptionGroupUpdateSerializer,
    FamilyDetailSerializer,
    FamilyImageMetadataSerializer,
    FamilyImageUploadSerializer,
    FamilyListQuerySerializer,
    FamilySerializer,
    FamilyUpdateSerializer,
    GlobalCatalogRecordInputSerializer,
    GlobalVariantInputSerializer,
    GlobalVariantQuerySerializer,
    OptionGroupSerializer,
    PublishResponseSerializer,
    ReferenceImageUploadSerializer,
    SelectionCreateSerializer,
    ShopStyleOptionInputSerializer,
    ShopVariantInputSerializer,
    ShopVariantQuerySerializer,
    SelectionSerializer,
    StyleImageSerializer,
    StyleOptionSerializer,
    StyleOptionUpdateSerializer,
    VariantDetailSerializer,
    VariantUpdateSerializer,
    VariantSerializer,
)
from apps.catalog.services import (
    _shop_actor,
    add_selection,
    archive_design,
    archive_global_design,
    copy_design_version,
    create_design,
    create_global_design,
    create_global_variant,
    create_shop_variant,
    publish_global_version,
    publish_version,
    remove_family_image,
    set_family_status,
    set_global_variant_active,
    set_global_variant_default,
    set_shop_variant_active,
    upload_design_references,
    upload_family_image,
    upload_style_images,
    update_family_translations,
    update_global_variant,
    update_shop_style_option,
    update_shop_variant,
)
from apps.catalog.private_uploads import complete_upload, issue_upload
from apps.catalog.models import PrivateMediaUpload
from apps.accounts.permissions import PasswordChangeGate
from apps.tenants.context_views import ShopContextMixin
from apps.tenants.policy import ShopRolePolicy
from apps.common.views import TenantScopedMixin


class MainSupplierOnly(BasePermission):
    def has_permission(self, request, view):
        return ShopRolePolicy.is_main_supplier_admin(request.user)


def _locale(request):
    locale = request.query_params.get("locale", "en")
    return locale if locale in {"en", "ar-KW", "bn", "ur"} else "en"


def _shop_write_allowed(context):
    if context.is_main_supplier:
        return True
    return bool(context.membership and context.membership.role in {"ADMIN", "STAFF"})


def _lock_shop_write_context(request, shop_id):
    shop, membership = _shop_actor(shop_id=shop_id, actor=request.user, write=True)
    if str(shop.pk) != str(request.shop_context.shop.pk):
        raise NotFound()
    return shop, membership


class CatalogPagination(PageNumberPagination):
    page_size = 20


class PrivateMediaUploadInputSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=("authorize", "complete"))
    kind = serializers.ChoiceField(
        choices=PrivateMediaUpload.Kind.choices, required=False
    )
    target_id = serializers.UUIDField(required=False)
    content_type = serializers.CharField(max_length=32, required=False)
    byte_size = serializers.IntegerField(min_value=1, required=False)
    upload_token = serializers.CharField(max_length=2048, required=False)

    def validate(self, attrs):
        required = (
            ("kind", "target_id", "content_type", "byte_size")
            if attrs["action"] == "authorize"
            else ("upload_token",)
        )
        missing = [name for name in required if name not in attrs]
        if missing:
            raise serializers.ValidationError(
                {name: "This field is required." for name in missing}
            )
        return attrs


class _PrivateMediaUploadAction:
    def perform_upload_action(self, request, *, shop=None):
        data = PrivateMediaUploadInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        if values["action"] == "authorize":
            if not settings.R2_ENABLED:
                return Response(
                    {"detail": "Private direct upload is not configured."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            result = issue_upload(
                kind=values["kind"],
                target_id=values["target_id"],
                content_type=values["content_type"],
                byte_size=values["byte_size"],
                actor=request.user,
                shop=shop,
            )
            response = Response(result, status=status.HTTP_201_CREATED)
            response["Cache-Control"] = "no-store"
            return response
        result = complete_upload(
            token=values["upload_token"], actor=request.user, shop=shop
        )
        response = Response(result, status=status.HTTP_201_CREATED)
        response["Cache-Control"] = "no-store"
        return response


PRIVATE_MEDIA_UPLOAD_RESPONSE_SCHEMA = {
    "oneOf": [
        {
            "type": "object",
            "required": ["upload_url", "upload_token", "headers", "expires_in"],
            "properties": {
                "upload_url": {"type": "string", "format": "uri"},
                "upload_token": {"type": "string"},
                "headers": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
                "expires_in": {"type": "integer"},
            },
        },
        {
            "type": "array",
            "items": {
                "type": "object",
                "description": "Created private image metadata.",
            },
        },
        {
            "type": "object",
            "description": "Created global family image metadata.",
            "additionalProperties": True,
        },
    ]
}


class GlobalPrivateMediaUploadView(_PrivateMediaUploadAction, APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(
        request=PrivateMediaUploadInputSerializer,
        responses={
            201: OpenApiResponse(
                response=PRIVATE_MEDIA_UPLOAD_RESPONSE_SCHEMA,
                description="Upload authorization or completed image metadata, based on action.",
            )
        },
        operation_id="catalog_global_private_media_upload",
    )
    def post(self, request):
        if not ShopRolePolicy.is_main_supplier_admin(request.user):
            raise PermissionDenied()
        return self.perform_upload_action(request)


class ShopPrivateMediaUploadView(_PrivateMediaUploadAction, ShopContextMixin, APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=PrivateMediaUploadInputSerializer,
        responses={
            201: OpenApiResponse(
                response=PRIVATE_MEDIA_UPLOAD_RESPONSE_SCHEMA,
                description="Upload authorization or completed image metadata, based on action.",
            )
        },
        operation_id="shop_private_media_upload",
    )
    @transaction.atomic
    def post(self, request, shop_id):
        # _lock_shop_write_context() uses select_for_update() to serialize
        # Shop-scoped writes, so this view must own the surrounding transaction.
        _lock_shop_write_context(request, shop_id)
        if not _shop_write_allowed(request.shop_context):
            raise PermissionDenied()
        return self.perform_upload_action(request, shop=request.shop_context.shop)


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


def _page_response(request, queryset, item_serializer, *, context=None):
    paginator = CatalogPagination()
    page = paginator.paginate_queryset(queryset, request)
    return paginator.get_paginated_response(
        item_serializer(page, many=True, context=context or {}).data
    )


class FamilyListView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(
        parameters=[FamilyListQuerySerializer],
        responses=_page_schema("CatalogFamilyPage", FamilySerializer),
        operation_id="catalog_families_list",
    )
    def get(self, request):
        query = FamilyListQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        is_main_supplier = ShopRolePolicy.is_main_supplier_admin(request.user)
        family_status = query.validated_data["status"]
        if not is_main_supplier and family_status != GarmentFamily.Status.ACTIVE:
            raise PermissionDenied()
        families = GarmentFamily.objects.all()
        if family_status != "all":
            families = families.filter(status=family_status)
        search = query.validated_data.get("search", "").strip()
        if search:
            families = families.filter(
                Q(code__icontains=search) | Q(translations__name__icontains=search)
            ).distinct()
        return _page_response(
            request,
            families.prefetch_related("translations"),
            FamilySerializer,
            context={"locale": _locale(request)},
        )

    @extend_schema(
        request=GlobalCatalogRecordInputSerializer,
        responses=FamilySerializer,
        operation_id="catalog_families_create",
    )
    def post(self, request):
        if not ShopRolePolicy.is_main_supplier_admin(request.user):
            raise PermissionDenied()
        data = GlobalCatalogRecordInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        try:
            with transaction.atomic():
                family = GarmentFamily.objects.create(
                    code=values["code"],
                    created_by=request.user,
                    updated_by=request.user,
                )
                GarmentFamilyTranslation.objects.bulk_create(
                    [
                        GarmentFamilyTranslation(
                            family=family,
                            created_by=request.user,
                            updated_by=request.user,
                            **translation,
                        )
                        for translation in values["translations"]
                    ]
                )
        except IntegrityError:
            raise serializers.ValidationError(
                {"code": "This global garment family code is already in use."}
            ) from None
        return Response(
            FamilySerializer(family, context={"locale": _locale(request)}).data,
            status=status.HTTP_201_CREATED,
        )


class FamilyDetailView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    def _family(self, request, family_id):
        family = get_object_or_404(
            GarmentFamily.objects.prefetch_related("translations"), pk=family_id
        )
        if (
            family.status != GarmentFamily.Status.ACTIVE
            and not ShopRolePolicy.is_main_supplier_admin(request.user)
        ):
            raise NotFound()
        return family

    @extend_schema(
        responses=FamilyDetailSerializer,
        operation_id="catalog_family_retrieve",
    )
    def get(self, request, family_id):
        family = self._family(request, family_id)
        return Response(
            FamilyDetailSerializer(family, context={"locale": _locale(request)}).data
        )

    @extend_schema(
        request=FamilyUpdateSerializer,
        responses=FamilyDetailSerializer,
        operation_id="catalog_family_update",
    )
    def patch(self, request, family_id):
        if not ShopRolePolicy.is_main_supplier_admin(request.user):
            raise PermissionDenied()
        data = FamilyUpdateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        family = update_family_translations(
            family_id=family_id,
            translations=data.validated_data.get("translations", []),
            actor=request.user,
        )
        family = self._family(request, family_id)
        return Response(
            FamilyDetailSerializer(family, context={"locale": _locale(request)}).data
        )


class FamilyArchiveView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(
        request=None,
        responses=FamilySerializer,
        operation_id="catalog_family_archive",
    )
    def post(self, request, family_id):
        family = set_family_status(
            family_id=family_id,
            status=GarmentFamily.Status.ARCHIVED,
            actor=request.user,
        )
        return Response(
            FamilySerializer(family, context={"locale": _locale(request)}).data
        )


class FamilyReactivateView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(
        request=None,
        responses=FamilySerializer,
        operation_id="catalog_family_reactivate",
    )
    def post(self, request, family_id):
        family = set_family_status(
            family_id=family_id,
            status=GarmentFamily.Status.ACTIVE,
            actor=request.user,
        )
        return Response(
            FamilySerializer(family, context={"locale": _locale(request)}).data
        )


class FamilyImageView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    def _family(self, request, family_id):
        family = get_object_or_404(GarmentFamily.objects.all(), pk=family_id)
        if (
            family.status != GarmentFamily.Status.ACTIVE
            and not ShopRolePolicy.is_main_supplier_admin(request.user)
        ):
            raise NotFound()
        return family

    @extend_schema(
        responses=OpenApiTypes.BINARY,
        operation_id="catalog_family_image_retrieve",
    )
    def get(self, request, family_id):
        family = self._family(request, family_id)
        if not family.image:
            raise NotFound()
        return _private_file_response(family.image, family.image_mime_type)

    @extend_schema(
        request=FamilyImageUploadSerializer,
        responses=FamilyImageMetadataSerializer,
        operation_id="catalog_family_image_upload",
    )
    def post(self, request, family_id):
        if not ShopRolePolicy.is_main_supplier_admin(request.user):
            raise PermissionDenied()
        if (
            set(request.FILES.keys()) != {"image"}
            or len(request.FILES.getlist("image")) != 1
        ):
            raise serializers.ValidationError(
                {"image": "Upload exactly one image file."}
            )
        data = FamilyImageUploadSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        family = upload_family_image(
            family_id=family_id, upload=data.validated_data["image"], actor=request.user
        )
        return Response(self._metadata(family), status=status.HTTP_200_OK)

    @extend_schema(responses={204: None}, operation_id="catalog_family_image_remove")
    def delete(self, request, family_id):
        if not ShopRolePolicy.is_main_supplier_admin(request.user):
            raise PermissionDenied()
        remove_family_image(family_id=family_id, actor=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _metadata(family):
        return FamilyImageMetadataSerializer(
            {
                "has_image": bool(family.image),
                "image_content_url": (
                    reverse("v1:catalog-family-image", kwargs={"family_id": family.pk})
                    if family.image
                    else None
                ),
                "mime_type": family.image_mime_type,
                "byte_size": family.image_byte_size,
                "width": family.image_width,
                "height": family.image_height,
            }
        ).data


class OptionGroupListView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(
        responses=_page_schema("CatalogOptionGroupPage", OptionGroupSerializer)
    )
    def get(self, request):
        return _page_response(
            request,
            OptionGroup.objects.all().prefetch_related("families", "translations"),
            OptionGroupSerializer,
            context={"locale": _locale(request)},
        )

    @extend_schema(
        request=GlobalCatalogRecordInputSerializer,
        responses=OptionGroupSerializer,
        operation_id="catalog_option_groups_create",
    )
    def post(self, request):
        if not ShopRolePolicy.is_main_supplier_admin(request.user):
            raise PermissionDenied()
        data = GlobalCatalogRecordInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        try:
            with transaction.atomic():
                group = OptionGroup.objects.create(
                    code=values["code"],
                    created_by=request.user,
                    updated_by=request.user,
                )
                OptionGroupTranslation.objects.bulk_create(
                    [
                        OptionGroupTranslation(
                            option_group=group,
                            created_by=request.user,
                            updated_by=request.user,
                            **translation,
                        )
                        for translation in values["translations"]
                    ]
                )
        except IntegrityError:
            raise serializers.ValidationError(
                {"code": "This global option group code is already in use."}
            ) from None
        return Response(
            OptionGroupSerializer(group, context={"locale": _locale(request)}).data,
            status=status.HTTP_201_CREATED,
        )


class GlobalVariantsView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate, MainSupplierOnly)

    @extend_schema(
        parameters=[GlobalVariantQuerySerializer],
        responses=_page_schema("GlobalVariantPage", VariantSerializer),
        operation_id="catalog_global_variants_list",
    )
    def get(self, request):
        query = GlobalVariantQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        variants = (
            GarmentVariant.objects.filter(tenant__isnull=True)
            .select_related("family")
            .prefetch_related("translations")
        )
        values = query.validated_data
        family_id = values.get("family")
        if family_id:
            variants = variants.filter(family_id=family_id)
        if values["status"] != "all":
            variants = variants.filter(is_active=values["status"] == "ACTIVE")
        search = values.get("search", "").strip()
        if search:
            variants = variants.filter(
                Q(code__icontains=search) | Q(translations__name__icontains=search)
            ).distinct()
        return _page_response(
            request,
            variants,
            VariantSerializer,
            context={"locale": _locale(request)},
        )

    @extend_schema(
        request=GlobalVariantInputSerializer,
        responses={201: VariantDetailSerializer},
        operation_id="catalog_global_variant_create",
    )
    def post(self, request):
        data = GlobalVariantInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            variant = create_global_variant(actor=request.user, **data.validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                {"code": "This global variant code is already in use for this family."}
            ) from None
        variant = GarmentVariant.objects.prefetch_related("translations").get(
            pk=variant.pk
        )
        return Response(
            VariantDetailSerializer(variant, context={"locale": _locale(request)}).data,
            status=status.HTTP_201_CREATED,
        )


class GlobalVariantDetailView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate, MainSupplierOnly)

    def _variant(self, variant_id):
        return get_object_or_404(
            GarmentVariant.objects.filter(tenant__isnull=True)
            .select_related("family")
            .prefetch_related("translations"),
            pk=variant_id,
        )

    @extend_schema(
        responses=VariantDetailSerializer,
        operation_id="catalog_global_variant_retrieve",
    )
    def get(self, request, variant_id):
        return Response(
            VariantDetailSerializer(
                self._variant(variant_id), context={"locale": _locale(request)}
            ).data
        )

    @extend_schema(
        request=VariantUpdateSerializer,
        responses=VariantDetailSerializer,
        operation_id="catalog_global_variant_update",
    )
    def patch(self, request, variant_id):
        data = VariantUpdateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        variant = update_global_variant(
            actor=request.user,
            variant_id=variant_id,
            **data.validated_data,
        )
        variant = GarmentVariant.objects.prefetch_related("translations").get(
            pk=variant.pk
        )
        return Response(
            VariantDetailSerializer(variant, context={"locale": _locale(request)}).data
        )


class GlobalVariantLifecycleView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate, MainSupplierOnly)

    @extend_schema(request=None, responses=VariantDetailSerializer)
    def post(self, request, variant_id, action):
        if action == "set-default":
            variant = set_global_variant_default(
                actor=request.user, variant_id=variant_id
            )
        else:
            variant = set_global_variant_active(
                actor=request.user,
                variant_id=variant_id,
                is_active=action == "reactivate",
            )
        variant = (
            GarmentVariant.objects.select_related("family")
            .prefetch_related("translations")
            .get(pk=variant.pk)
        )
        return Response(
            VariantDetailSerializer(variant, context={"locale": _locale(request)}).data
        )


class FamilyOptionGroupsView(APIView):
    """Read or configure which global option groups apply to a family."""

    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(
        responses=OptionGroupSerializer(many=True),
        operation_id="catalog_family_option_groups_list",
    )
    def get(self, request, family_id):
        family = get_object_or_404(GarmentFamily.objects.all(), pk=family_id)
        if (
            family.status != GarmentFamily.Status.ACTIVE
            and not ShopRolePolicy.is_main_supplier_admin(request.user)
        ):
            raise NotFound()
        rows = (
            FamilyOptionGroup.objects.filter(family=family)
            .select_related("option_group")
            .prefetch_related("option_group__translations")
        )
        return Response(
            OptionGroupSerializer(
                [row.option_group for row in rows],
                many=True,
                context={"locale": _locale(request)},
            ).data
        )

    @transaction.atomic
    @extend_schema(
        request=FamilyOptionGroupUpdateSerializer,
        responses=OptionGroupSerializer(many=True),
        operation_id="catalog_family_option_groups_update",
    )
    def put(self, request, family_id):
        if not ShopRolePolicy.is_main_supplier_admin(request.user):
            raise PermissionDenied()
        family = get_object_or_404(
            GarmentFamily.objects.select_for_update(), pk=family_id
        )
        ids = request.data.get("option_group_ids")
        if not isinstance(ids, list) or len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                {"option_group_ids": "Provide a unique list."}
            )
        groups = list(OptionGroup.objects.filter(pk__in=ids))
        if len(groups) != len(ids):
            raise serializers.ValidationError(
                {"option_group_ids": "Unknown option group."}
            )
        FamilyOptionGroup.objects.filter(family=family).delete()
        FamilyOptionGroup.objects.bulk_create(
            [
                FamilyOptionGroup(
                    family=family,
                    option_group=group,
                    sort_order=index,
                    created_by=request.user,
                    updated_by=request.user,
                )
                for index, group in enumerate(groups)
            ]
        )
        return self.get(request, family_id)


class GlobalStyleOptionsView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(
        responses=_page_schema("GlobalStyleOptionPage", StyleOptionSerializer),
        operation_id="catalog_global_style_options_list",
    )
    def get(self, request):
        group_id = request.query_params.get("option_group")
        queryset = StyleOption.objects.filter(tenant__isnull=True, is_active=True)
        if group_id:
            queryset = queryset.filter(option_group_id=group_id)
        return _page_response(
            request,
            queryset.select_related("option_group").prefetch_related(
                "translations",
                Prefetch(
                    "reference_images",
                    queryset=StyleOptionImage.objects.filter(is_primary=True),
                ),
            ),
            StyleOptionSerializer,
            context={"locale": _locale(request)},
        )

    @extend_schema(
        request=ShopStyleOptionInputSerializer,
        responses=StyleOptionSerializer,
        operation_id="catalog_global_style_options_create",
    )
    def post(self, request):
        if not ShopRolePolicy.is_main_supplier_admin(request.user):
            raise PermissionDenied()
        data = ShopStyleOptionInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        group = get_object_or_404(
            OptionGroup.objects.all(), pk=values["option_group_id"]
        )
        try:
            with transaction.atomic():
                option = StyleOption.objects.create(
                    option_group=group,
                    tenant=None,
                    code=values["code"],
                    created_by=request.user,
                    updated_by=request.user,
                )
                for translation in values["translations"]:
                    StyleOptionTranslation.objects.create(
                        style_option=option,
                        created_by=request.user,
                        updated_by=request.user,
                        **translation,
                    )
        except IntegrityError:
            raise serializers.ValidationError(
                {"code": "This global style code is already in use."}
            ) from None
        return Response(
            StyleOptionSerializer(option, context={"locale": _locale(request)}).data,
            status=status.HTTP_201_CREATED,
        )


class GlobalStyleOptionDetailView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(
        request=inline_serializer(
            name="StyleOptionActiveUpdate",
            fields={"is_active": serializers.BooleanField()},
        ),
        responses=StyleOptionSerializer,
    )
    def patch(self, request, option_id):
        if not ShopRolePolicy.is_main_supplier_admin(request.user):
            raise PermissionDenied()
        if set(request.data) != {"is_active"} or not isinstance(
            request.data["is_active"], bool
        ):
            raise serializers.ValidationError(
                "Only the active/archive state may be changed."
            )
        option = get_object_or_404(
            StyleOption.objects.filter(tenant__isnull=True), pk=option_id
        )
        option.is_active = request.data["is_active"]
        option.updated_by = request.user
        option.save(update_fields=("is_active", "updated_by", "updated_at"))
        return Response(
            StyleOptionSerializer(option, context={"locale": _locale(request)}).data
        )


class ShopVariantsView(ShopContextMixin, APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[ShopVariantQuerySerializer],
        responses=_page_schema("ShopVariantPage", VariantSerializer),
        operation_id="shop_variant_list",
    )
    def get(self, request, shop_id):
        query = ShopVariantQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        values = query.validated_data
        if values["status"] != "ACTIVE" and not _shop_write_allowed(
            request.shop_context
        ):
            raise PermissionDenied()
        variants = (
            GarmentVariant.objects.filter(
                Q(tenant__isnull=True) | Q(tenant=request.shop_context.shop)
            )
            .filter(family__status=GarmentFamily.Status.ACTIVE)
            .select_related("family")
            .prefetch_related("translations")
        )
        family_id = values.get("family")
        if family_id:
            variants = variants.filter(family_id=family_id)
        if values["status"] != "all":
            variants = variants.filter(is_active=values["status"] == "ACTIVE")
        if values["source"] == "global":
            variants = variants.filter(tenant__isnull=True)
        elif values["source"] == "shop":
            variants = variants.filter(tenant=request.shop_context.shop)
        search = values.get("search", "").strip()
        if search:
            variants = variants.filter(
                Q(code__icontains=search) | Q(translations__name__icontains=search)
            ).distinct()
        return _page_response(
            request, variants, VariantSerializer, context={"locale": _locale(request)}
        )

    @extend_schema(
        request=ShopVariantInputSerializer,
        responses=VariantSerializer,
        operation_id="shop_variant_create",
    )
    def post(self, request, shop_id):
        _lock_shop_write_context(request, shop_id)
        if not _shop_write_allowed(request.shop_context):
            raise PermissionDenied()
        data = ShopVariantInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        try:
            variant = create_shop_variant(shop_id=shop_id, actor=request.user, **values)
        except IntegrityError:
            raise serializers.ValidationError(
                {"code": "This Shop variant code is already in use."}
            ) from None
        variant = (
            GarmentVariant.objects.select_related("family")
            .prefetch_related("translations")
            .get(pk=variant.pk)
        )
        return Response(
            VariantDetailSerializer(variant, context={"locale": _locale(request)}).data,
            status=status.HTTP_201_CREATED,
        )


class ShopVariantDetailView(ShopContextMixin, APIView):
    permission_classes = (IsAuthenticated,)

    def _variant(self, request, variant_id):
        visible = GarmentVariant.objects.filter(
            Q(tenant__isnull=True, is_active=True) | Q(tenant=request.shop_context.shop)
        )
        return get_object_or_404(
            visible.select_related("family").prefetch_related("translations"),
            pk=variant_id,
        )

    @extend_schema(
        responses=VariantDetailSerializer, operation_id="shop_variant_retrieve"
    )
    def get(self, request, shop_id, variant_id):
        return Response(
            VariantDetailSerializer(
                self._variant(request, variant_id),
                context={"locale": _locale(request)},
            ).data
        )

    @extend_schema(
        request=VariantUpdateSerializer,
        responses=VariantDetailSerializer,
        operation_id="shop_variant_update",
    )
    def patch(self, request, shop_id, variant_id):
        _lock_shop_write_context(request, shop_id)
        if not _shop_write_allowed(request.shop_context):
            raise PermissionDenied()
        variant = self._variant(request, variant_id)
        if variant.tenant_id is None:
            raise PermissionDenied("Shop users cannot change global variants.")
        data = VariantUpdateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        variant = update_shop_variant(
            shop_id=shop_id,
            actor=request.user,
            variant_id=variant_id,
            **data.validated_data,
        )
        variant = (
            GarmentVariant.objects.select_related("family")
            .prefetch_related("translations")
            .get(pk=variant.pk)
        )
        return Response(
            VariantDetailSerializer(variant, context={"locale": _locale(request)}).data
        )


class ShopVariantLifecycleView(ShopContextMixin, APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=None, responses=VariantDetailSerializer)
    def post(self, request, shop_id, variant_id, action):
        _lock_shop_write_context(request, shop_id)
        if not _shop_write_allowed(request.shop_context):
            raise PermissionDenied()
        variant = get_object_or_404(
            GarmentVariant.objects.filter(tenant=request.shop_context.shop),
            pk=variant_id,
        )
        try:
            variant = set_shop_variant_active(
                shop_id=shop_id,
                actor=request.user,
                variant_id=variant_id,
                is_active=action == "reactivate",
            )
        except IntegrityError:
            raise serializers.ValidationError(
                {"variant": "This variant cannot be reactivated."}
            ) from None
        variant = (
            GarmentVariant.objects.select_related("family")
            .prefetch_related("translations")
            .get(pk=variant.pk)
        )
        return Response(
            VariantDetailSerializer(variant, context={"locale": _locale(request)}).data
        )


class ShopStyleOptionsView(ShopContextMixin, APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        responses=_page_schema("ShopStyleOptionPage", StyleOptionSerializer),
        operation_id="shop_style_options_list",
    )
    def get(self, request, shop_id):
        shop = request.shop_context.shop
        options = (
            StyleOption.objects.filter(
                Q(tenant__isnull=True) | Q(tenant=shop), is_active=True
            )
            .select_related("option_group")
            .prefetch_related(
                "translations",
                Prefetch(
                    "reference_images",
                    queryset=StyleOptionImage.objects.filter(is_primary=True),
                ),
            )
        )
        group_id = request.query_params.get("option_group")
        if group_id:
            options = options.filter(option_group_id=group_id)
        return _page_response(
            request,
            options,
            StyleOptionSerializer,
            context={"locale": _locale(request)},
        )

    @extend_schema(
        request=ShopStyleOptionInputSerializer,
        responses=StyleOptionSerializer,
        operation_id="shop_style_options_create",
    )
    @transaction.atomic
    def post(self, request, shop_id):
        _lock_shop_write_context(request, shop_id)
        if not _shop_write_allowed(request.shop_context):
            raise PermissionDenied()
        data = ShopStyleOptionInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        group = get_object_or_404(
            OptionGroup.objects.all(), pk=values["option_group_id"]
        )
        try:
            with transaction.atomic():
                option = StyleOption.objects.create(
                    tenant=request.shop_context.shop,
                    option_group=group,
                    code=values["code"],
                    created_by=request.user,
                    updated_by=request.user,
                )
                for translation in values["translations"]:
                    StyleOptionTranslation.objects.create(
                        style_option=option,
                        created_by=request.user,
                        updated_by=request.user,
                        **translation,
                    )
        except IntegrityError:
            raise serializers.ValidationError(
                {"code": "This Shop style code is already in use."}
            ) from None
        return Response(
            StyleOptionSerializer(option, context={"locale": _locale(request)}).data,
            status=status.HTTP_201_CREATED,
        )


class ShopStyleOptionDetailView(ShopContextMixin, APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=StyleOptionUpdateSerializer,
        responses=StyleOptionSerializer,
        operation_id="shop_style_option_update",
    )
    @transaction.atomic
    def patch(self, request, shop_id, option_id):
        _lock_shop_write_context(request, shop_id)
        if not _shop_write_allowed(request.shop_context):
            raise PermissionDenied()
        option = get_object_or_404(
            StyleOption.objects.filter(tenant=request.shop_context.shop), pk=option_id
        )
        data = StyleOptionUpdateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        if "translations" in data.validated_data:
            option = update_shop_style_option(
                shop=request.shop_context.shop,
                option_id=option_id,
                translations=data.validated_data["translations"],
                actor=request.user,
            )
        else:
            option.is_active = data.validated_data["is_active"]
            option.updated_by = request.user
            option.save(update_fields=("is_active", "updated_by", "updated_at"))
        return Response(
            StyleOptionSerializer(option, context={"locale": _locale(request)}).data
        )


class GlobalStyleImageUploadView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(
        request=ReferenceImageUploadSerializer,
        responses=StyleImageSerializer(many=True),
        operation_id="catalog_global_style_images_upload",
    )
    def post(self, request, option_id):
        if not ShopRolePolicy.is_main_supplier_admin(request.user):
            raise PermissionDenied()
        option = get_object_or_404(
            StyleOption.objects.filter(tenant__isnull=True), pk=option_id
        )
        return _upload_style_response(request, option)


class GlobalStyleImageView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(
        responses=OpenApiTypes.BINARY,
        operation_id="catalog_global_style_image_retrieve",
    )
    def get(self, request, option_id, image_id):
        image = get_object_or_404(
            StyleOptionImage.objects.select_related("style_option").filter(
                style_option__tenant__isnull=True
            ),
            pk=image_id,
            style_option_id=option_id,
        )
        return _private_file_response(image.image, image.mime_type)


class ShopStyleImageUploadView(ShopContextMixin, APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=ReferenceImageUploadSerializer,
        responses=StyleImageSerializer(many=True),
        operation_id="shop_style_images_upload",
    )
    @transaction.atomic
    def post(self, request, shop_id, option_id):
        _lock_shop_write_context(request, shop_id)
        if not _shop_write_allowed(request.shop_context):
            raise PermissionDenied()
        option = get_object_or_404(
            StyleOption.objects.filter(
                Q(tenant__isnull=True) | Q(tenant=request.shop_context.shop)
            ),
            pk=option_id,
        )
        if option.tenant_id is None and not request.shop_context.is_main_supplier:
            raise PermissionDenied("Shop users cannot change global defaults.")
        return _upload_style_response(request, option)


class ShopStyleImageView(ShopContextMixin, APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        responses=OpenApiTypes.BINARY, operation_id="shop_style_image_retrieve"
    )
    def get(self, request, shop_id, option_id, image_id):
        image = get_object_or_404(
            StyleOptionImage.objects.select_related("style_option").filter(
                Q(style_option__tenant__isnull=True)
                | Q(style_option__tenant=request.shop_context.shop)
            ),
            pk=image_id,
            style_option_id=option_id,
        )
        return _private_file_response(image.image, image.mime_type)


def _upload_style_response(request, option):
    uploads = request.FILES.getlist("images")
    images = upload_style_images(
        style_option=option, uploads=uploads, actor=request.user
    )
    from apps.catalog.serializers import StyleImageSerializer

    return Response(
        StyleImageSerializer(images, many=True).data, status=status.HTTP_201_CREATED
    )


def _private_file_response(field_file, mime_type):
    try:
        file_handle = field_file.open("rb")
    except FileNotFoundError:
        # Metadata can outlive a private object if it is removed out of band.
        # Return a normal not-found response rather than leaking a storage 500.
        raise Http404("Reference image not found.") from None
    response = FileResponse(file_handle, content_type=mime_type)
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Disposition"] = 'inline; filename="reference.webp"'
    return response


class DesignListCreateView(ShopContextMixin, TenantScopedMixin, APIView):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        context = self._get_authorized_shop_context()
        return Design.objects.filter(tenant=context.shop)

    @extend_schema(
        parameters=[DesignListQuerySerializer],
        responses=_page_schema("ShopDesignPage", DesignSerializer),
        operation_id="shop_design_list",
    )
    def get(self, request, shop_id):
        query = DesignListQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        designs = (
            self.get_queryset()
            .filter(status=Design.Status.ACTIVE)
            .prefetch_related("versions")
        )
        family_id = query.validated_data.get("family")
        if family_id:
            designs = designs.filter(family_id=family_id)
        variant_id = query.validated_data.get("variant")
        if variant_id:
            designs = designs.filter(variant_id=variant_id)
        return _page_response(
            request,
            designs,
            DesignSerializer,
            context={"shop_id": shop_id, "locale": _locale(request)},
        )

    @extend_schema(
        request=DesignCreateSerializer,
        responses=DesignSerializer,
        operation_id="shop_design_create",
    )
    def post(self, request, shop_id):
        if not _shop_write_allowed(request.shop_context):
            raise PermissionDenied()
        data = DesignCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        family = get_object_or_404(
            GarmentFamily.objects.filter(status=GarmentFamily.Status.ACTIVE),
            pk=values["family_id"],
        )
        variant = get_object_or_404(
            GarmentVariant.objects.filter(
                (Q(tenant__isnull=True) | Q(tenant=request.shop_context.shop)),
                is_active=True,
            ),
            pk=values["variant_id"],
            family=family,
        )
        source = source_version = None
        if values.get("source_design_id"):
            source_qs = Design.objects.filter(
                Q(tenant__isnull=True) | Q(tenant=request.shop_context.shop),
                status=Design.Status.ACTIVE,
            )
            source = get_object_or_404(source_qs, pk=values["source_design_id"])
            if source.family_id != family.pk or source.variant_id != variant.pk:
                raise serializers.ValidationError(
                    "A copied design must keep its source garment family and variant."
                )
            source_version = get_object_or_404(
                DesignVersion.objects.filter(
                    design=source, status=DesignVersion.Status.PUBLISHED
                ),
                pk=values["source_version_id"],
            )
            design = copy_design_version(
                shop_id=shop_id,
                actor=request.user,
                family=family,
                variant=variant,
                name=values["name"],
                source=source,
                source_version=source_version,
                translations=values.get("translations"),
            )
        else:
            design = create_design(
                shop_id=shop_id,
                actor=request.user,
                family=family,
                variant=variant,
                name=values["name"],
                translations=values.get("translations"),
            )
        design.refresh_from_db()
        return Response(
            DesignSerializer(
                design, context={"shop_id": shop_id, "locale": _locale(request)}
            ).data,
            status=status.HTTP_201_CREATED,
        )


class DesignDetailView(ShopContextMixin, APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses=DesignSerializer, operation_id="shop_design_retrieve")
    def get(self, request, shop_id, design_id):
        design = get_object_or_404(
            Design.objects.filter(tenant=request.shop_context.shop), pk=design_id
        )
        return Response(
            DesignSerializer(
                design, context={"shop_id": shop_id, "locale": _locale(request)}
            ).data
        )

    @extend_schema(
        request=DesignDraftNameUpdateSerializer,
        responses=DesignSerializer,
        operation_id="shop_design_update_draft_name",
    )
    @transaction.atomic
    def patch(self, request, shop_id, design_id):
        _lock_shop_write_context(request, shop_id)
        if not _shop_write_allowed(request.shop_context):
            raise PermissionDenied()
        design = get_object_or_404(
            Design.objects.filter(tenant=request.shop_context.shop), pk=design_id
        )
        if set(request.data) - {"name", "translations"}:
            raise serializers.ValidationError(
                "Only Draft version display names may be changed here."
            )
        draft = (
            design.versions.select_for_update()
            .filter(status=DesignVersion.Status.DRAFT)
            .order_by("-number")
            .first()
        )
        if draft is None:
            raise serializers.ValidationError("No editable Draft version exists.")
        if "translations" in request.data:
            from apps.catalog.serializers import TranslationInputSerializer

            validator = TranslationInputSerializer(
                data=request.data["translations"], many=True
            )
            validator.is_valid(raise_exception=True)
            items = validator.validated_data
            locales = [item["locale"] for item in items]
            if len(locales) != len(set(locales)) or "en" not in locales:
                raise serializers.ValidationError(
                    "Draft name translations need unique locales and English."
                )
            DesignVersionTranslation.objects.filter(version=draft).exclude(
                locale__in=locales
            ).delete()
            for item in items:
                DesignVersionTranslation.objects.update_or_create(
                    version=draft,
                    locale=item["locale"],
                    defaults={
                        "name": item["name"],
                        "description": item.get("description", ""),
                        "updated_by": request.user,
                    },
                )
        elif "name" in request.data:
            name = request.data["name"].strip()
            if not name:
                raise serializers.ValidationError({"name": "Name must not be blank."})
            translation, created = DesignVersionTranslation.objects.get_or_create(
                version=draft,
                locale="en",
                defaults={
                    "name": name,
                    "created_by": request.user,
                    "updated_by": request.user,
                },
            )
            if not created:
                translation.name = name
                translation.updated_by = request.user
                translation.save(update_fields=["name", "updated_by", "updated_at"])
        return Response(
            DesignSerializer(
                design, context={"shop_id": shop_id, "locale": _locale(request)}
            ).data
        )

    @extend_schema(
        request=None, responses=DesignSerializer, operation_id="shop_design_archive"
    )
    def delete(self, request, shop_id, design_id):
        design = archive_design(
            shop_id=shop_id, actor=request.user, design_id=design_id
        )
        return Response(DesignSerializer(design, context={"shop_id": shop_id}).data)


class DesignSelectionView(ShopContextMixin, APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=SelectionCreateSerializer,
        responses=SelectionSerializer,
        operation_id="shop_design_selection_create",
    )
    def post(self, request, shop_id, version_id):
        data = SelectionCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        option = get_object_or_404(
            StyleOption.objects.filter(
                Q(tenant__isnull=True) | Q(tenant=request.shop_context.shop),
                is_active=True,
            ),
            pk=data.validated_data["style_option_id"],
        )
        selection = add_selection(
            shop_id=shop_id, actor=request.user, version_id=version_id, option=option
        )
        from apps.catalog.serializers import SelectionSerializer

        return Response(
            SelectionSerializer(selection, context={"locale": _locale(request)}).data,
            status=status.HTTP_201_CREATED,
        )


class PublishDesignVersionView(ShopContextMixin, APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=None,
        responses=PublishResponseSerializer,
        operation_id="shop_design_version_publish",
    )
    def post(self, request, shop_id, version_id):
        published, draft = publish_version(
            shop_id=shop_id, actor=request.user, version_id=version_id
        )
        return Response(
            {
                "published": DesignVersionSerializer(
                    published, context={"shop_id": shop_id}
                ).data,
                "next_draft": DesignVersionSerializer(
                    draft, context={"shop_id": shop_id}
                ).data,
            }
        )


class DesignReferenceView(ShopContextMixin, APIView):
    permission_classes = (IsAuthenticated,)

    def _get_version(self, shop_id, version_id):
        return get_object_or_404(
            DesignVersion.objects.select_related("design").filter(
                design__tenant=request_shop(self, shop_id)
            ),
            pk=version_id,
        )

    @extend_schema(
        responses=DesignReferenceGallerySerializer(many=True),
        operation_id="shop_design_reference_gallery",
    )
    def get(self, request, shop_id, version_id):
        version = self._get_version(shop_id, version_id)
        return Response(
            DesignVersionSerializer(
                version, context={"shop_id": shop_id, "locale": _locale(request)}
            ).data["references"]
        )

    @extend_schema(
        request=ReferenceImageUploadSerializer,
        responses=DesignReferenceSerializer(many=True),
        operation_id="shop_design_reference_upload",
    )
    @transaction.atomic
    def post(self, request, shop_id, version_id):
        _lock_shop_write_context(request, shop_id)
        if not _shop_write_allowed(request.shop_context):
            raise PermissionDenied()
        version = self._get_version(shop_id, version_id)
        images = upload_design_references(
            version=version, uploads=request.FILES.getlist("images"), actor=request.user
        )
        return Response(
            DesignReferenceSerializer(images, many=True).data,
            status=status.HTTP_201_CREATED,
        )


def request_shop(view, shop_id):
    if str(view.request.shop_context.shop.pk) != str(shop_id):
        raise NotFound()
    return view.request.shop_context.shop


class DesignReferenceImageView(ShopContextMixin, APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        responses=OpenApiTypes.BINARY, operation_id="shop_design_reference_download"
    )
    def get(self, request, shop_id, reference_id):
        reference = get_object_or_404(
            DesignReference.objects.select_related("version__design").filter(
                version__design__tenant=request.shop_context.shop
            ),
            pk=reference_id,
        )
        return _private_file_response(reference.image, reference.mime_type)


class GlobalDesignTemplatesView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(
        parameters=[DesignListQuerySerializer],
        responses=_page_schema("GlobalDesignTemplatePage", DesignSerializer),
        operation_id="catalog_global_design_templates_list",
    )
    def get(self, request):
        query = DesignListQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        designs = Design.objects.filter(
            tenant__isnull=True, status=Design.Status.ACTIVE
        )
        main_supplier = ShopRolePolicy.is_main_supplier_admin(request.user)
        if not main_supplier:
            designs = designs.filter(
                versions__status=DesignVersion.Status.PUBLISHED
            ).distinct()
        family_id = query.validated_data.get("family")
        if family_id:
            designs = designs.filter(family_id=family_id)
        variant_id = query.validated_data.get("variant")
        if variant_id:
            designs = designs.filter(variant_id=variant_id)
        return _page_response(
            request,
            designs,
            DesignSerializer,
            context={"locale": _locale(request), "published_only": not main_supplier},
        )

    @extend_schema(
        request=DesignCreateSerializer,
        responses=DesignSerializer,
        operation_id="catalog_global_design_template_create",
    )
    def post(self, request):
        if not ShopRolePolicy.is_main_supplier_admin(request.user):
            raise PermissionDenied()
        data = DesignCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        if values.get("source_design_id") or values.get("source_version_id"):
            raise serializers.ValidationError(
                "Global defaults cannot be copied from Shop designs."
            )
        family = get_object_or_404(
            GarmentFamily.objects.filter(status=GarmentFamily.Status.ACTIVE),
            pk=values["family_id"],
        )
        variant = get_object_or_404(
            GarmentVariant.objects.filter(tenant__isnull=True, is_active=True),
            pk=values["variant_id"],
            family=family,
        )
        design = create_global_design(
            actor=request.user,
            family=family,
            variant=variant,
            name=values["name"],
            translations=values.get("translations"),
        )
        return Response(DesignSerializer(design).data, status=status.HTTP_201_CREATED)


class GlobalDesignTemplateDetailView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(
        responses=DesignSerializer,
        operation_id="catalog_global_design_template_retrieve",
    )
    def get(self, request, design_id):
        main_supplier = ShopRolePolicy.is_main_supplier_admin(request.user)
        designs = Design.objects.filter(
            tenant__isnull=True,
            status=Design.Status.ACTIVE,
        )
        if not main_supplier:
            designs = designs.filter(
                versions__status=DesignVersion.Status.PUBLISHED
            ).distinct()
        design = get_object_or_404(designs, pk=design_id)
        return Response(
            DesignSerializer(
                design,
                context={
                    "locale": _locale(request),
                    "published_only": not main_supplier,
                },
            ).data
        )


class GlobalDesignSelectionView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate, MainSupplierOnly)

    @extend_schema(
        request=SelectionCreateSerializer,
        responses=SelectionSerializer,
        operation_id="catalog_global_design_selection_create",
    )
    @transaction.atomic
    def post(self, request, design_id, version_id):
        data = SelectionCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        design = get_object_or_404(
            Design.objects.filter(tenant__isnull=True), pk=design_id
        )
        version = get_object_or_404(
            DesignVersion.objects.select_for_update().filter(
                design=design, status=DesignVersion.Status.DRAFT
            ),
            pk=version_id,
        )
        option = get_object_or_404(
            StyleOption.objects.filter(tenant__isnull=True, is_active=True),
            pk=data.validated_data["style_option_id"],
        )
        family = get_object_or_404(
            GarmentFamily.objects.select_for_update(), pk=design.family_id
        )
        if not family.option_groups.filter(pk=option.option_group_id).exists():
            raise serializers.ValidationError(
                "Option group is not available for this garment."
            )
        selection, created = DesignSelection.objects.get_or_create(
            version=version,
            option_group=option.option_group,
            style_option=option,
            defaults={
                "selected_code": option.code,
                "selected_name_en": option.translations.filter(locale="en")
                .values_list("name", flat=True)
                .first()
                or option.code,
                "created_by": request.user,
                "updated_by": request.user,
            },
        )
        if created:
            from apps.catalog.models import DesignSelectionImage

            DesignSelectionTranslation.objects.bulk_create(
                [
                    DesignSelectionTranslation(
                        selection=selection,
                        locale=translation.locale,
                        name=translation.name,
                        description=translation.description,
                        created_by=request.user,
                        updated_by=request.user,
                    )
                    for translation in option.translations.all()
                ]
            )

            DesignSelectionImage.objects.bulk_create(
                [
                    DesignSelectionImage(
                        selection=selection,
                        source_image=image,
                        created_by=request.user,
                        updated_by=request.user,
                    )
                    for image in option.reference_images.all()
                ]
            )
        from apps.catalog.serializers import SelectionSerializer

        return Response(
            SelectionSerializer(selection, context={"locale": _locale(request)}).data,
            status=status.HTTP_201_CREATED,
        )


class GlobalDesignPublishView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate, MainSupplierOnly)

    @extend_schema(
        request=None,
        responses=PublishResponseSerializer,
        operation_id="catalog_global_design_publish",
    )
    def post(self, request, design_id, version_id):
        published, draft = publish_global_version(
            actor=request.user, design_id=design_id, version_id=version_id
        )
        return Response(
            {
                "published": DesignVersionSerializer(published).data,
                "next_draft": DesignVersionSerializer(draft).data,
            }
        )


class GlobalDesignArchiveView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate, MainSupplierOnly)

    @extend_schema(
        request=None,
        responses=DesignSerializer,
        operation_id="catalog_global_design_archive",
    )
    def post(self, request, design_id):
        design = archive_global_design(actor=request.user, design_id=design_id)
        return Response(DesignSerializer(design).data)


class GlobalDesignReferenceView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    def _version(self, design_id, version_id):
        return get_object_or_404(
            DesignVersion.objects.select_related("design").filter(
                design__tenant__isnull=True, design__status=Design.Status.ACTIVE
            ),
            pk=version_id,
            design_id=design_id,
        )

    @extend_schema(
        responses=DesignReferenceGallerySerializer(many=True),
        operation_id="catalog_global_design_reference_gallery",
    )
    def get(self, request, design_id, version_id):
        version = self._version(design_id, version_id)
        return Response(
            DesignVersionSerializer(version, context={"locale": _locale(request)}).data[
                "references"
            ]
        )

    @extend_schema(
        request=ReferenceImageUploadSerializer,
        responses=DesignReferenceSerializer(many=True),
        operation_id="catalog_global_design_reference_upload",
    )
    def post(self, request, design_id, version_id):
        if not ShopRolePolicy.is_main_supplier_admin(request.user):
            raise PermissionDenied()
        version = self._version(design_id, version_id)
        images = upload_design_references(
            version=version, uploads=request.FILES.getlist("images"), actor=request.user
        )
        return Response(
            DesignReferenceSerializer(images, many=True).data,
            status=status.HTTP_201_CREATED,
        )


class GlobalDesignReferenceImageView(APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    @extend_schema(
        responses=OpenApiTypes.BINARY,
        operation_id="catalog_global_design_reference_download",
    )
    def get(self, request, reference_id):
        reference = get_object_or_404(
            DesignReference.objects.select_related("version__design").filter(
                version__design__tenant__isnull=True
            ),
            pk=reference_id,
        )
        return _private_file_response(reference.image, reference.mime_type)
