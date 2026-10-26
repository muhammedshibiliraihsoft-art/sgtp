from io import BytesIO
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from apps.accounts.models import User
from apps.catalog.models import (
    Design,
    DesignReference,
    DesignSelection,
    DesignSelectionImage,
    DesignVersion,
    DesignVersionTranslation,
    FamilyOptionGroup,
    GarmentFamily,
    GarmentFamilyTranslation,
    GarmentVariant,
    OptionGroup,
    PrivateMediaUpload,
    StyleOption,
    StyleOptionImage,
    StyleOptionTranslation,
    ShopDesignPrice,
)
from apps.catalog.views import FamilyImageView
from apps.catalog.storage import PrivateReferenceStorage
from apps.tenants.models import (
    MembershipWorkFunction,
    ShopRole,
    Supplier,
    Tenant,
    TenantMember,
)


class CatalogDesignApiTests(APITestCase):
    def setUp(self):
        self.supplier = Supplier.objects.get(singleton_lock=True)
        self.shop_a = self.make_shop("Catalog Shop A", "catalog-shop-a")
        self.shop_b = self.make_shop("Catalog Shop B", "catalog-shop-b")
        self.admin, self.admin_membership = self.make_member(
            "catalog-admin-a@example.test", self.shop_a, ShopRole.ADMIN
        )
        self.staff, self.staff_membership = self.make_member(
            "catalog-tailor-a@example.test", self.shop_a, ShopRole.STAFF
        )
        self.viewer, _ = self.make_member(
            "catalog-viewer-a@example.test", self.shop_a, ShopRole.VIEWER
        )
        self.other_admin, _ = self.make_member(
            "catalog-admin-b@example.test", self.shop_b, ShopRole.ADMIN
        )
        self.main = User.objects.create_superuser(
            email="catalog-main@example.test",
            password="Safe-Test-Password-293!",
            first_name="Catalog Main",
            phone="+96550001100",
        )
        self.family = GarmentFamily.objects.get(code="mens-shirt")
        self.variant = GarmentVariant.objects.get(family=self.family, is_default=True)
        self.group = OptionGroup.objects.get(code="cuff")
        # The Men’s Shirt defaults now map Cuff during migrations.  The API
        # scenarios below require the mapping, whether it came from the
        # production seed or a minimal isolated fixture.
        FamilyOptionGroup.objects.get_or_create(
            family=self.family, option_group=self.group
        )
        self.global_option = StyleOption.objects.get(
            tenant__isnull=True, option_group=self.group, code="normal-cuff"
        )

    def make_shop(self, name, slug):
        return Tenant.objects.create(
            supplier=self.supplier, name=name, slug=slug, max_users=20
        )

    def make_member(self, email, shop, role):
        user = User.objects.create_user(
            email=email,
            password="Safe-Test-Password-293!",
            first_name="Catalog",
            owning_shop=shop,
        )
        membership = TenantMember.objects.create(tenant=shop, user=user, role=role)
        return user, membership

    @staticmethod
    def shop_url(shop, suffix=""):
        return f"/api/v1/shops/{shop.pk}/{suffix}"

    @staticmethod
    def make_option(*, tenant, code, label):
        group = OptionGroup.objects.get(code="cuff")
        option = StyleOption.objects.create(
            tenant=tenant, option_group=group, code=code
        )
        StyleOptionTranslation.objects.create(
            style_option=option, locale="en", name=label
        )
        return option

    @staticmethod
    def png_upload(name="reference.png", color=(20, 90, 160)):
        buffer = BytesIO()
        Image.new("RGB", (640, 480), color).save(buffer, format="PNG")
        return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")

    @staticmethod
    def family_image_upload(image_format="PNG", name=None, color=(30, 100, 170)):
        buffer = BytesIO()
        Image.new("RGB", (320, 240), color).save(buffer, format=image_format)
        extension = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}[image_format]
        content_type = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}[
            image_format
        ]
        return SimpleUploadedFile(
            name or f"family.{extension}", buffer.getvalue(), content_type=content_type
        )

    def create_design(self, *, client=None, shop=None, name="Blue Shirt"):
        client = client or self.client
        shop = shop or self.shop_a
        response = client.post(
            self.shop_url(shop, "designs/"),
            {
                "family_id": str(self.family.pk),
                "name": name,
            },
            format="json",
        )
        return response

    def test_migration_seeds_only_approved_families_variants_and_cuff_styles(self):
        self.assertEqual(
            set(GarmentFamily.objects.values_list("code", flat=True)),
            {"kuwaiti-dishdasha", "mens-shirt", "abaya", "darraa-long-dress"},
        )
        self.assertEqual(
            GarmentVariant.objects.filter(tenant__isnull=True, is_default=True).count(),
            4,
        )
        cuff_codes = set(
            StyleOption.objects.filter(
                tenant__isnull=True, option_group=self.group
            ).values_list("code", flat=True)
        )
        self.assertEqual(
            cuff_codes,
            {
                "normal-cuff",
                "open-cuff",
                "round-cuff",
                "square-cuff",
                "button-cuff",
                "custom",
            },
        )
        self.assertNotIn("french-cuff", cuff_codes)

    def test_measurement_family_list_excludes_shop_copy_of_global_template(self):
        from apps.catalog.services import initialize_shop_default_catalog

        initialize_shop_default_catalog(shop=self.shop_a, actor=self.admin)
        local_copy = GarmentFamily.objects.get(
            tenant=self.shop_a, template_source=self.family
        )
        self.assertEqual(local_copy.code, self.family.code)
        self.assertEqual(
            local_copy.translations.get(locale="en").name,
            self.family.translations.get(locale="en").name,
        )

        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/v1/catalog/families/?locale=en")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {row["id"] for row in response.data["results"]}
        self.assertIn(str(self.family.pk), returned_ids)
        self.assertNotIn(str(local_copy.pk), returned_ids)
        self.assertTrue(
            Design.objects.filter(family=local_copy, variant__isnull=True).exists()
        )

    def test_main_supplier_can_create_global_family_with_translations(self):
        payload = {
            "code": "mens-jacket",
            "translations": [
                {"locale": "en", "name": "Men's Jacket"},
            ],
        }
        self.client.force_authenticate(self.admin)
        denied = self.client.post("/api/v1/catalog/families/", payload, format="json")
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.main)
        created = self.client.post("/api/v1/catalog/families/", payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        family = GarmentFamily.objects.get(pk=created.data["id"])
        self.assertIsNone(family.variants.filter(is_default=True).first())
        self.assertEqual(
            set(family.translations.values_list("locale", flat=True)),
            {"en"},
        )
        self.assertEqual(created.data["name"], "Men's Jacket")
        duplicate = self.client.post(
            "/api/v1/catalog/families/", payload, format="json"
        )
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)

    def test_global_family_creation_requires_unique_english_translations(self):
        self.client.force_authenticate(self.main)
        response = self.client.post(
            "/api/v1/catalog/families/",
            {
                "code": "mens-coat",
                "translations": [
                    {"locale": "ar-KW", "name": "معطف"},
                    {"locale": "ar-KW", "name": "معطف آخر"},
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(GarmentFamily.objects.filter(code="mens-coat").exists())

    def test_shop_can_create_owned_garment_system_and_family_level_design(self):
        self.client.force_authenticate(self.admin)
        root = self.shop_url(self.shop_a, "catalog/")
        family_response = self.client.post(
            f"{root}garment-families/",
            {
                "code": "custom-coat",
                "translations": [{"locale": "en", "name": "Custom Coat"}],
            },
            format="json",
        )
        self.assertEqual(family_response.status_code, status.HTTP_201_CREATED)
        family = GarmentFamily.objects.get(pk=family_response.data["id"])
        self.assertEqual(family.tenant_id, self.shop_a.pk)
        family_list = self.client.get(f"{root}garment-families/?locale=en")
        self.assertEqual(family_list.status_code, status.HTTP_200_OK)
        self.assertIn(
            str(family.pk),
            {item["id"] for item in family_list.data["results"]},
        )

        group_response = self.client.post(
            f"{root}option-groups/",
            {
                "code": "custom-fastening",
                "translations": [{"locale": "en", "name": "Fastening"}],
            },
            format="json",
        )
        self.assertEqual(group_response.status_code, status.HTTP_201_CREATED)
        group = OptionGroup.objects.get(pk=group_response.data["id"])
        self.assertEqual(group.tenant_id, self.shop_a.pk)

        config_response = self.client.put(
            f"{root}garment-families/{family.pk}/option-groups/",
            {
                "option_groups": [
                    {
                        "option_group_id": str(group.pk),
                        "selection_mode": "SINGLE",
                        "is_required": True,
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(config_response.status_code, status.HTTP_200_OK)
        mapping = FamilyOptionGroup.objects.get(family=family, option_group=group)
        self.assertEqual(mapping.selection_mode, FamilyOptionGroup.SelectionMode.SINGLE)
        self.assertTrue(mapping.is_required)

        option_response = self.client.post(
            f"{root}style-options/",
            {
                "option_group_id": str(group.pk),
                "code": "hidden-buttons",
                "translations": [{"locale": "en", "name": "Hidden Buttons"}],
            },
            format="json",
        )
        self.assertEqual(option_response.status_code, status.HTTP_201_CREATED)
        design_response = self.client.post(
            self.shop_url(self.shop_a, "designs/"),
            {"family_id": str(family.pk), "name": "Everyday Coat"},
            format="json",
        )
        self.assertEqual(design_response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(design_response.data["variant"])
        version_id = design_response.data["latest_version"]["id"]
        publish_url = self.shop_url(
            self.shop_a, f"design-versions/{version_id}/publish/"
        )
        missing_required = self.client.post(publish_url, {}, format="json")
        self.assertEqual(missing_required.status_code, status.HTTP_400_BAD_REQUEST)

        selected = self.client.post(
            self.shop_url(self.shop_a, f"design-versions/{version_id}/selections/"),
            {"style_option_id": option_response.data["id"]},
            format="json",
        )
        self.assertEqual(selected.status_code, status.HTTP_201_CREATED, selected.data)
        published = self.client.post(publish_url, {}, format="json")
        self.assertEqual(published.status_code, status.HTTP_200_OK, published.data)

        second_design = self.client.post(
            self.shop_url(self.shop_a, "designs/"),
            {"family_id": str(family.pk), "name": "Ceremonial Coat"},
            format="json",
        )
        self.assertEqual(second_design.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(second_design.data["variant"])
        self.assertNotEqual(second_design.data["id"], design_response.data["id"])
        self.assertEqual(
            Design.objects.filter(tenant=self.shop_a, family=family).count(), 2
        )

    def test_shop_family_creation_uses_authorized_shop_and_preserves_existing_staff_access(self):
        path = self.shop_url(self.shop_a, "catalog/garment-families/")
        payload = {
            "tenant": str(self.shop_b.pk),
            "code": "shop-owned-coat",
            "translations": [{"locale": "en", "name": "Shop-owned Coat"}],
        }

        created_codes = []
        for actor, code in (
            (self.admin, "shop-owned-coat-admin"),
            (self.staff, "shop-owned-coat-staff"),
        ):
            self.client.force_authenticate(actor)
            response = self.client.post(
                path,
                {**payload, "code": code},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
            created = GarmentFamily.objects.get(pk=response.data["id"])
            self.assertEqual(created.tenant_id, self.shop_a.pk)
            self.assertNotEqual(created.tenant_id, self.shop_b.pk)
            created_codes.append(created.code)

        self.client.force_authenticate(self.other_admin)
        other_shop_rows = self.client.get(
            self.shop_url(self.shop_b, "catalog/garment-families/")
        )
        self.assertEqual(other_shop_rows.status_code, status.HTTP_200_OK)
        self.assertTrue(set(created_codes).isdisjoint(
            {row["code"] for row in other_shop_rows.data["results"]}
        ))

        self.client.force_authenticate(self.viewer)
        denied = self.client.post(
            self.shop_url(self.shop_a, "catalog/garment-families/"),
            {"code": "viewer-garment", "translations": [{"locale": "en", "name": "Viewer Garment"}]},
            format="json",
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            GarmentFamily.objects.filter(tenant=self.shop_a, code="viewer-garment").exists()
        )

    def test_shop_local_group_can_be_created_and_attached_to_one_owned_family_atomically(self):
        self.client.force_authenticate(self.admin)
        family_response = self.client.post(
            self.shop_url(self.shop_a, "catalog/garment-families/"),
            {
                "code": "local-dress-system",
                "translations": [{"locale": "en", "name": "Local Dress System"}],
            },
            format="json",
        )
        self.assertEqual(family_response.status_code, status.HTTP_201_CREATED)
        family_id = family_response.data["id"]
        path = self.shop_url(
            self.shop_a,
            f"catalog/garment-families/{family_id}/option-groups/create/",
        )
        response = self.client.post(
            path,
            {
                "code": "dress-fastening-detail",
                "translations": [{"locale": "en", "name": "Fastening detail"}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        group = OptionGroup.objects.get(pk=response.data["option_group"]["id"])
        self.assertEqual(group.tenant_id, self.shop_a.pk)
        self.assertEqual(group.families.count(), 1)
        self.assertEqual(str(group.families.get().pk), family_id)
        mapping = FamilyOptionGroup.objects.get(family_id=family_id, option_group=group)
        self.assertEqual(mapping.selection_mode, FamilyOptionGroup.SelectionMode.MULTI)
        self.assertFalse(mapping.is_required)
        self.assertFalse(
            FamilyOptionGroup.objects.filter(
                family__tenant=self.shop_b, option_group=group
            ).exists()
        )

    def test_shop_local_group_create_rejects_global_or_another_shops_family(self):
        self.client.force_authenticate(self.admin)
        payload = {
            "code": "shop-only-detail",
            "translations": [{"locale": "en", "name": "Shop-only detail"}],
        }
        global_response = self.client.post(
            self.shop_url(
                self.shop_a,
                f"catalog/garment-families/{self.family.pk}/option-groups/create/",
            ),
            payload,
            format="json",
        )
        self.assertEqual(global_response.status_code, status.HTTP_404_NOT_FOUND)
        other_family = GarmentFamily.objects.create(
            tenant=self.shop_b, code="another-shop-family"
        )
        foreign_response = self.client.post(
            self.shop_url(
                self.shop_a,
                f"catalog/garment-families/{other_family.pk}/option-groups/create/",
            ),
            payload,
            format="json",
        )
        self.assertEqual(foreign_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(OptionGroup.objects.filter(code="shop-only-detail").exists())

    def test_new_shop_default_catalog_is_materialized_and_designs_are_shop_owned(self):
        from apps.catalog.services import initialize_shop_default_catalog

        initialize_shop_default_catalog(shop=self.shop_a, actor=self.admin)
        initialize_shop_default_catalog(shop=self.shop_b, actor=self.other_admin)
        local = GarmentFamily.objects.get(tenant=self.shop_a, template_source=self.family)
        other = GarmentFamily.objects.get(tenant=self.shop_b, template_source=self.family)
        self.assertNotEqual(local.pk, self.family.pk)
        self.assertNotEqual(local.pk, other.pk)
        self.assertEqual(
            list(FamilyOptionGroup.objects.filter(family=local).values_list(
                "option_group_id", "sort_order", "selection_mode", "is_required"
            )),
            list(FamilyOptionGroup.objects.filter(family=self.family).values_list(
                "option_group_id", "sort_order", "selection_mode", "is_required"
            )),
        )
        design = Design.objects.filter(
            tenant=self.shop_a, family=local, is_default_seeded=True
        ).first()
        self.assertIsNotNone(design)
        self.assertIsNone(design.source_design.tenant_id)
        self.assertGreater(design.versions.count(), 0)

    def test_staff_can_edit_archive_and_restore_only_shop_default_family(self):
        from apps.catalog.services import initialize_shop_default_catalog

        initialize_shop_default_catalog(shop=self.shop_a, actor=self.admin)
        initialize_shop_default_catalog(shop=self.shop_b, actor=self.other_admin)
        local = GarmentFamily.objects.get(tenant=self.shop_a, template_source=self.family)
        other = GarmentFamily.objects.get(tenant=self.shop_b, template_source=self.family)
        source_mapping = FamilyOptionGroup.objects.get(
            family=self.family, option_group=self.group
        )
        self.client.force_authenticate(self.staff)
        path = self.shop_url(self.shop_a, f"catalog/garment-families/{local.pk}/option-groups/")
        response = self.client.put(path, {"option_groups": []}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(FamilyOptionGroup.objects.filter(family=self.family, option_group=self.group).exists())
        self.assertTrue(FamilyOptionGroup.objects.filter(family=other, option_group=self.group).exists())

        FamilyOptionGroup.objects.filter(pk=source_mapping.pk).update(is_required=True)
        archived = self.client.post(self.shop_url(self.shop_a, f"catalog/garment-families/{local.pk}/archive/"), {}, format="json")
        self.assertEqual(archived.status_code, status.HTTP_200_OK)
        restored = self.client.post(self.shop_url(self.shop_a, f"catalog/garment-families/{local.pk}/restore/"), {}, format="json")
        self.assertEqual(restored.status_code, status.HTTP_200_OK)
        self.assertTrue(FamilyOptionGroup.objects.get(family=local, option_group=self.group).is_required)
        self.assertFalse(FamilyOptionGroup.objects.get(family=other, option_group=self.group).is_required)

    def test_restoring_seeded_design_uses_latest_global_published_version(self):
        from apps.catalog.services import initialize_shop_default_catalog, publish_global_version

        initialize_shop_default_catalog(shop=self.shop_a, actor=self.admin)
        design = Design.objects.filter(tenant=self.shop_a, is_default_seeded=True).first()
        self.assertIsNotNone(design)
        source = design.source_design
        from apps.catalog.services import _clone_version_content

        source_published = source.versions.filter(
            status=DesignVersion.Status.PUBLISHED
        ).order_by("-number").first()
        source_draft = DesignVersion.objects.create(
            design=source,
            number=source_published.number + 1,
            created_by=self.main,
            updated_by=self.main,
        )
        _clone_version_content(source_published, source_draft, self.main, clone_options=False)
        translation = source_draft.translations.get(locale="en")
        latest_name = f"{translation.name} restored latest"
        translation.name = latest_name
        translation.save(update_fields=("name", "updated_at"))
        publish_global_version(actor=self.main, design_id=source.pk, version_id=source_draft.pk)

        self.client.force_authenticate(self.admin)
        archived = self.client.delete(self.shop_url(self.shop_a, f"designs/{design.pk}/"))
        self.assertEqual(archived.status_code, status.HTTP_200_OK)
        restored = self.client.post(self.shop_url(self.shop_a, f"designs/{design.pk}/restore-default/"), {}, format="json")
        self.assertEqual(restored.status_code, status.HTTP_200_OK)
        design.refresh_from_db()
        latest = design.versions.order_by("-number").first()
        self.assertEqual(design.status, Design.Status.ACTIVE)
        # Default materialization now keeps published version 1 and creates
        # draft 2; restoring replaces that draft without reusing its number.
        self.assertEqual(latest.number, 3)
        self.assertEqual(latest.translations.get(locale="en").name, latest_name)

    def test_shop_garment_system_endpoints_do_not_expose_another_shop_records(self):
        family = GarmentFamily.objects.create(
            tenant=self.shop_b, code="other-shop-garment"
        )
        self.client.force_authenticate(self.admin)
        response = self.client.get(
            self.shop_url(self.shop_a, "catalog/garment-families/")
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        visible_ids = {item["id"] for item in response.data["results"]}
        self.assertNotIn(str(family.pk), visible_ids)

        detail = self.client.put(
            self.shop_url(
                self.shop_a,
                f"catalog/garment-families/{family.pk}/option-groups/",
            ),
            {"option_groups": []},
            format="json",
        )
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_family_search_is_case_insensitive_and_runs_before_pagination(self):
        GarmentFamilyTranslation.objects.create(
            family=self.family, locale="ur", name="School Shirt"
        )
        for index in range(24):
            family = GarmentFamily.objects.create(code=f"search-family-{index:02d}")
            GarmentFamilyTranslation.objects.create(
                family=family, locale="en", name=f"Search Family {index:02d}"
            )
        self.client.force_authenticate(self.admin)

        code_result = self.client.get("/api/v1/catalog/families/?search=MENs-SHIRT")
        self.assertEqual(code_result.status_code, status.HTTP_200_OK)
        self.assertEqual(code_result.data["count"], 1)
        self.assertEqual(code_result.data["results"][0]["id"], str(self.family.pk))

        localized_result = self.client.get("/api/v1/catalog/families/?search=school")
        self.assertEqual(localized_result.data["count"], 1)
        self.assertEqual(localized_result.data["results"][0]["id"], str(self.family.pk))

        late_result = self.client.get(
            "/api/v1/catalog/families/?search=Search%20Family%2023"
        )
        self.assertEqual(late_result.status_code, status.HTTP_200_OK)
        self.assertEqual(late_result.data["count"], 1)
        self.assertEqual(late_result.data["results"][0]["code"], "search-family-23")

    def test_family_detail_update_archive_and_reactivate_permissions(self):
        detail_url = f"/api/v1/catalog/families/{self.family.pk}/"
        archive_url = f"/api/v1/catalog/families/{self.family.pk}/archive/"
        reactivate_url = f"/api/v1/catalog/families/{self.family.pk}/reactivate/"
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.patch(detail_url, {"translations": []}).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.patch(
                detail_url,
                {
                    "translations": [{"locale": "en", "name": "Denied"}],
                    "option_group_ids": [str(self.group.pk)],
                },
                format="json",
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.post(archive_url).status_code, status.HTTP_403_FORBIDDEN
        )
        self.assertEqual(
            self.client.post(reactivate_url).status_code, status.HTTP_403_FORBIDDEN
        )

        self.client.force_authenticate(self.main)
        detail = self.client.get(detail_url)
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["code"], "mens-shirt")
        self.assertIn("cuff", {group["code"] for group in detail.data["option_groups"]})
        original_english_name = self.family.translations.get(locale="en").name
        self.assertEqual(
            self.client.patch(detail_url, {"code": "renamed-shirt"}).status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        duplicate_locale = self.client.patch(
            detail_url,
            {
                "translations": [
                    {"locale": "bn", "name": "Shirt"},
                    {"locale": "bn", "name": "Shirts"},
                ]
            },
            format="json",
        )
        self.assertEqual(duplicate_locale.status_code, status.HTTP_400_BAD_REQUEST)
        updated = self.client.patch(
            detail_url,
            {"translations": [{"locale": "bn", "name": "Shirt"}]},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["code"], "mens-shirt")
        self.assertEqual(
            self.family.translations.get(locale="en").name, original_english_name
        )
        self.assertEqual(self.family.translations.get(locale="bn").name, "Shirt")

        archived = self.client.post(archive_url)
        self.assertEqual(archived.status_code, status.HTTP_200_OK)
        self.assertEqual(archived.data["status"], GarmentFamily.Status.ARCHIVED)
        self.assertEqual(
            GarmentFamily.objects.get(pk=self.family.pk).status,
            GarmentFamily.Status.ARCHIVED,
        )
        self.client.force_authenticate(self.admin)
        self.assertEqual(
            self.client.get(detail_url).status_code, status.HTTP_404_NOT_FOUND
        )
        self.assertEqual(
            self.client.get(
                f"/api/v1/catalog/families/{self.family.pk}/option-groups/"
            ).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.client.force_authenticate(self.main)
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_200_OK)
        archived_list = self.client.get("/api/v1/catalog/families/?status=ARCHIVED")
        self.assertEqual(archived_list.data["count"], 1)
        active_list = self.client.get("/api/v1/catalog/families/")
        self.assertFalse(
            any(row["id"] == str(self.family.pk) for row in active_list.data["results"])
        )
        self.client.force_authenticate(self.admin)
        self.assertEqual(
            self.client.get("/api/v1/catalog/families/?status=ARCHIVED").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.client.force_authenticate(self.main)
        reactivated = self.client.post(reactivate_url)
        self.assertEqual(reactivated.status_code, status.HTTP_200_OK)
        self.assertEqual(reactivated.data["status"], GarmentFamily.Status.ACTIVE)
        self.assertTrue(GarmentFamily.objects.filter(pk=self.family.pk).exists())

    def test_global_family_metadata_and_groups_save_in_one_request(self):
        self.client.force_authenticate(self.main)
        group = OptionGroup.objects.create(tenant=None, code="atomic-save-collar")
        detail_url = f"/api/v1/catalog/families/{self.family.pk}/"

        response = self.client.patch(
            detail_url,
            {
                "translations": [
                    {"locale": "en", "name": "Atomic Shirt", "description": "Saved together"}
                ],
                "option_group_ids": [str(group.pk)],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.family.translations.get(locale="en").name, "Atomic Shirt"
        )
        self.assertEqual(
            list(
                FamilyOptionGroup.objects.filter(family=self.family).values_list(
                    "option_group_id", flat=True
                )
            ),
            [group.pk],
        )
        self.assertEqual(
            [item["id"] for item in response.data["option_groups"]], [str(group.pk)]
        )

    def test_failed_atomic_global_family_save_rolls_back_metadata_and_groups(self):
        self.client.force_authenticate(self.main)
        old_name = self.family.translations.get(locale="en").name
        old_group_ids = list(
            FamilyOptionGroup.objects.filter(family=self.family)
            .order_by("option_group_id")
            .values_list("option_group_id", flat=True)
        )
        group = OptionGroup.objects.create(tenant=None, code="atomic-failure-collar")

        with patch(
            "apps.catalog.services.replace_global_family_option_groups",
            side_effect=DRFValidationError({"option_groups": "Controlled failure."}),
        ):
            response = self.client.patch(
                f"/api/v1/catalog/families/{self.family.pk}/",
                {
                    "translations": [
                        {"locale": "en", "name": "Must Roll Back"}
                    ],
                    "option_group_ids": [str(group.pk)],
                },
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.family.translations.get(locale="en").name, old_name)
        self.assertEqual(
            list(
                FamilyOptionGroup.objects.filter(family=self.family)
                .order_by("option_group_id")
                .values_list("option_group_id", flat=True)
            ),
            old_group_ids,
        )

    def test_legacy_split_global_save_reproduces_partial_state_on_second_request_failure(self):
        self.client.force_authenticate(self.main)
        old_group_ids = set(
            FamilyOptionGroup.objects.filter(family=self.family).values_list(
                "option_group_id", flat=True
            )
        )
        group = OptionGroup.objects.create(tenant=None, code="split-failure-collar")
        detail_url = f"/api/v1/catalog/families/{self.family.pk}/"
        metadata_response = self.client.patch(
            detail_url,
            {"translations": [{"locale": "en", "name": "First Request Saved"}]},
            format="json",
        )
        self.assertEqual(metadata_response.status_code, status.HTTP_200_OK)

        with patch(
            "apps.catalog.views.replace_global_family_option_groups",
            side_effect=DRFValidationError({"option_groups": "Controlled failure."}),
        ):
            groups_response = self.client.put(
                f"{detail_url}option-groups/",
                {"option_group_ids": [str(group.pk)]},
                format="json",
            )

        self.assertEqual(groups_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            self.family.translations.get(locale="en").name, "First Request Saved"
        )
        self.assertEqual(
            set(
                FamilyOptionGroup.objects.filter(family=self.family).values_list(
                    "option_group_id", flat=True
                )
            ),
            old_group_ids,
        )
    def test_archived_family_cannot_be_used_for_new_shop_or_global_records(self):
        self.client.force_authenticate(self.admin)
        existing = self.create_design(name="Historical archived-family design")
        self.assertEqual(existing.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(self.main)
        self.assertEqual(
            self.client.post(
                f"/api/v1/catalog/families/{self.family.pk}/archive/"
            ).status_code,
            status.HTTP_200_OK,
        )

        self.client.force_authenticate(self.admin)
        variant = self.client.post(
            self.shop_url(self.shop_a, "catalog/variants/"),
            {
                "family_id": str(self.family.pk),
                "code": "after-archive",
                "translations": [{"locale": "en", "name": "After Archive"}],
            },
            format="json",
        )
        self.assertEqual(variant.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        design = self.create_design(name="Rejected archived-family design")
        self.assertEqual(design.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            self.client.get(self.shop_url(self.shop_a, "designs/")).data["count"], 1
        )
        self.client.force_authenticate(self.main)
        global_variant = self.client.post(
            "/api/v1/catalog/variants/",
            {
                "family_id": str(self.family.pk),
                "code": "global-after-family-archive",
                "translations": [{"locale": "en", "name": "After Archive"}],
            },
            format="json",
        )
        self.assertEqual(global_variant.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        global_design = self.client.post(
            "/api/v1/catalog/design-templates/",
            {
                "family_id": str(self.family.pk),
                "variant_id": str(self.variant.pk),
                "name": "Rejected Archived Template",
            },
            format="json",
        )
        self.assertEqual(global_design.status_code, status.HTTP_404_NOT_FOUND)

    def test_family_thumbnail_upload_replace_read_remove_and_validation(self):
        endpoint = f"/api/v1/catalog/families/{self.family.pk}/image/"
        storage = GarmentFamily._meta.get_field("image").storage
        self.client.force_authenticate(self.admin)
        denied = self.client.post(endpoint, {"image": self.family_image_upload()})
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.main)
        for image_format in ("JPEG", "PNG", "WEBP"):
            with self.captureOnCommitCallbacks(execute=True):
                uploaded = self.client.post(
                    endpoint,
                    {"image": self.family_image_upload(image_format)},
                    format="multipart",
                )
            self.assertEqual(uploaded.status_code, status.HTTP_200_OK)
            self.assertTrue(uploaded.data["has_image"])
            self.assertEqual(uploaded.data["mime_type"], "image/webp")
            self.assertTrue(
                storage.exists(GarmentFamily.objects.get(pk=self.family.pk).image.name)
            )

        family = GarmentFamily.objects.get(pk=self.family.pk)
        old_name = family.image.name
        with self.captureOnCommitCallbacks(execute=True):
            replaced = self.client.post(
                endpoint,
                {"image": self.family_image_upload("PNG", color=(190, 35, 80))},
                format="multipart",
            )
        self.assertEqual(replaced.status_code, status.HTTP_200_OK)
        self.assertFalse(storage.exists(old_name))

        self.client.force_authenticate(self.admin)
        image_request = APIRequestFactory().get(endpoint)
        force_authenticate(image_request, user=self.admin)
        image_response = FamilyImageView.as_view()(
            image_request, family_id=self.family.pk
        )
        self.assertEqual(image_response.status_code, status.HTTP_200_OK)
        self.assertEqual(image_response["Content-Type"], "image/webp")
        self.assertEqual(image_response["Cache-Control"], "private, no-store")
        image_response.file_to_stream.close()
        invalid = self.client.post(
            endpoint,
            {
                "image": SimpleUploadedFile(
                    "broken.png", b"not an image", content_type="image/png"
                )
            },
            format="multipart",
        )
        self.assertEqual(invalid.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.main)
        invalid = self.client.post(
            endpoint,
            {
                "image": SimpleUploadedFile(
                    "broken.png", b"not an image", content_type="image/png"
                )
            },
            format="multipart",
        )
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        multiple = self.client.post(
            endpoint,
            {"image": [self.family_image_upload(), self.family_image_upload()]},
            format="multipart",
        )
        self.assertEqual(multiple.status_code, status.HTTP_400_BAD_REQUEST)

        old_name = GarmentFamily.objects.get(pk=self.family.pk).image.name
        with self.captureOnCommitCallbacks(execute=True):
            removed = self.client.delete(endpoint)
        self.assertEqual(removed.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(storage.exists(old_name))
        family = GarmentFamily.objects.get(pk=self.family.pk)
        self.assertFalse(family.image)
        self.assertIsNone(family.image_byte_size)
        self.assertEqual(
            self.client.get(endpoint).status_code, status.HTTP_404_NOT_FOUND
        )

    def test_main_supplier_can_create_global_option_group(self):
        payload = {
            "code": "collar-style",
            "translations": [
                {"locale": "en", "name": "Collar Style"},
            ],
        }
        self.client.force_authenticate(self.staff)
        denied = self.client.post(
            "/api/v1/catalog/option-groups/", payload, format="json"
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.main)
        created = self.client.post(
            "/api/v1/catalog/option-groups/", payload, format="json"
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        group = OptionGroup.objects.get(pk=created.data["id"])
        self.assertEqual(
            set(group.translations.values_list("locale", flat=True)), {"en"}
        )
        self.assertEqual(created.data["families"], [])
        self.assertEqual(created.data["name"], "Collar Style")

    def test_global_variants_are_main_supplier_only_and_exclude_shop_variants(self):
        self.client.force_authenticate(self.admin)
        denied = self.client.get("/api/v1/catalog/variants/")
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.main)
        response = self.client.get("/api/v1/catalog/variants/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            any(
                str(row["id"]) == str(self.variant.pk)
                for row in response.data["results"]
            )
        )
        filtered = self.client.get(f"/api/v1/catalog/variants/?family={self.family.pk}")
        self.assertTrue(
            all(
                str(row["family"]) == str(self.family.pk)
                for row in filtered.data["results"]
            )
        )
        invalid_filter = self.client.get("/api/v1/catalog/variants/?family=invalid")
        self.assertEqual(invalid_filter.status_code, status.HTTP_400_BAD_REQUEST)
        custom_response = self.client.post(
            self.shop_url(self.shop_a, "catalog/variants/"),
            {
                "family_id": str(self.family.pk),
                "code": "global-list-test-custom",
                "translations": [{"locale": "en", "name": "Custom"}],
            },
            format="json",
        )
        self.assertEqual(
            custom_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )
        rows = self.client.get("/api/v1/catalog/variants/").data["results"]
        self.assertFalse(any(row["code"] == "global-list-test-custom" for row in rows))

    def test_global_design_template_detail_hides_drafts_from_shop_members(self):
        self.client.force_authenticate(self.main)
        created = self.client.post(
            "/api/v1/catalog/design-templates/",
            {
                "family_id": str(self.family.pk),
                "variant_id": str(self.variant.pk),
                "name": "Global Template Detail",
            },
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        detail_url = f"/api/v1/catalog/design-templates/{created.data['id']}/"
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_200_OK)

        self.client.force_authenticate(self.admin)
        self.assertEqual(
            self.client.get(detail_url).status_code, status.HTTP_404_NOT_FOUND
        )

        self.client.force_authenticate(self.main)
        version_id = created.data["latest_version"]["id"]
        published = self.client.post(
            f"/api/v1/catalog/design-templates/{created.data['id']}/versions/{version_id}/publish/",
            {},
            format="json",
        )
        self.assertEqual(published.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(self.admin)
        visible = self.client.get(detail_url)
        self.assertEqual(visible.status_code, status.HTTP_200_OK)
        self.assertEqual(visible.data["latest_version"]["status"], "PUBLISHED")

    def test_global_catalog_falls_back_to_english_and_shop_cannot_change_defaults(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get(
            f"/api/v1/catalog/style-options/?locale=ur&option_group={self.group.pk}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), {"count", "next", "previous", "results"})
        normal = next(
            item
            for item in response.data["results"]
            if str(item["id"]) == str(self.global_option.pk)
        )
        self.assertEqual(normal["name"], "Normal Cuff")
        denied = self.client.patch(
            f"/api/v1/catalog/style-options/{self.global_option.pk}/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

    def test_main_supplier_configures_family_option_groups_and_shop_cannot(self):
        self.client.force_authenticate(self.staff)
        path = f"/api/v1/catalog/families/{self.family.pk}/option-groups/"
        self.assertEqual(
            self.client.put(path, {"option_group_ids": []}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.client.force_authenticate(self.main)
        response = self.client.put(
            path, {"option_group_ids": [str(self.group.pk)]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["code"] for item in response.data], ["cuff"])

    def test_shop_catalog_cannot_mutate_global_family_configuration(self):
        def path(shop):
            return self.shop_url(
                shop, f"catalog/garment-families/{self.family.pk}/option-groups/"
            )
        global_mappings = list(
            FamilyOptionGroup.objects.filter(family=self.family)
            .order_by("option_group_id")
            .values_list(
                "option_group_id", "sort_order", "selection_mode", "is_required"
            )
        )

        self.client.force_authenticate(self.admin)
        shop_a_before = self.client.get(path(self.shop_a))
        self.assertEqual(shop_a_before.status_code, status.HTTP_200_OK)
        self.assertTrue(shop_a_before.data)
        denied = self.client.put(path(self.shop_a), {"option_groups": []}, format="json")
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            list(
                FamilyOptionGroup.objects.filter(family=self.family)
                .order_by("option_group_id")
                .values_list(
                    "option_group_id", "sort_order", "selection_mode", "is_required"
                )
            ),
            global_mappings,
        )

        self.client.force_authenticate(self.other_admin)
        shop_b_after = self.client.get(path(self.shop_b))
        self.assertEqual(shop_b_after.status_code, status.HTTP_200_OK)
        self.assertEqual(shop_b_after.data, shop_a_before.data)

        new_shop = self.make_shop("Catalog Shop C", "catalog-shop-c")
        new_shop_admin, _ = self.make_member(
            "catalog-admin-c@example.test", new_shop, ShopRole.ADMIN
        )
        self.client.force_authenticate(new_shop_admin)
        new_shop_defaults = self.client.get(path(new_shop))
        self.assertEqual(new_shop_defaults.status_code, status.HTTP_200_OK)
        self.assertEqual(new_shop_defaults.data, shop_a_before.data)

    def test_shop_admin_and_staff_edit_an_isolated_copy_of_a_global_default(self):
        source_config = list(
            FamilyOptionGroup.objects.filter(family=self.family)
            .order_by("option_group_id")
            .values_list(
                "option_group_id", "sort_order", "selection_mode", "is_required"
            )
        )
        materialize_url = self.shop_url(
            self.shop_a,
            f"catalog/garment-families/{self.family.pk}/materialize-default/",
        )

        self.client.force_authenticate(self.admin)
        materialized = self.client.post(materialize_url, {}, format="json")
        self.assertEqual(materialized.status_code, status.HTTP_200_OK, materialized.data)
        local_family = GarmentFamily.objects.get(pk=materialized.data["id"])
        self.assertEqual(local_family.tenant_id, self.shop_a.pk)
        self.assertEqual(local_family.template_source_id, self.family.pk)
        self.assertEqual(
            list(
                FamilyOptionGroup.objects.filter(family=local_family)
                .order_by("option_group_id")
                .values_list(
                    "option_group_id", "sort_order", "selection_mode", "is_required"
                )
            ),
            source_config,
        )

        local_config_url = self.shop_url(
            self.shop_a, f"catalog/garment-families/{local_family.pk}/option-groups/"
        )
        self.client.force_authenticate(self.staff)
        edited = self.client.put(
            local_config_url,
            {
                "option_groups": [
                    {
                        "option_group_id": str(self.group.pk),
                        "selection_mode": "SINGLE",
                        "is_required": True,
                        "sort_order": 0,
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(edited.status_code, status.HTTP_200_OK, edited.data)
        self.assertTrue(
            FamilyOptionGroup.objects.get(
                family=local_family, option_group=self.group
            ).is_required
        )

        self.assertEqual(
            list(
                FamilyOptionGroup.objects.filter(family=self.family)
                .order_by("option_group_id")
                .values_list(
                    "option_group_id", "sort_order", "selection_mode", "is_required"
                )
            ),
            source_config,
        )
        self.client.force_authenticate(self.other_admin)
        shop_b_config = self.client.get(
            self.shop_url(
                self.shop_b,
                f"catalog/garment-families/{self.family.pk}/option-groups/",
            )
        )
        self.assertEqual(shop_b_config.status_code, status.HTTP_200_OK)
        shop_b_mappings = sorted(
            (
                row["option_group"]["id"],
                row["sort_order"],
                row["selection_mode"],
                row["is_required"],
            )
            for row in shop_b_config.data
        )
        self.assertEqual(
            shop_b_mappings,
            sorted(
                (str(group_id), order, mode, required)
                for group_id, order, mode, required in source_config
            ),
        )

        # Materialization is idempotent and never creates duplicate copies.
        self.client.force_authenticate(self.admin)
        repeated = self.client.post(materialize_url, {}, format="json")
        self.assertEqual(repeated.status_code, status.HTTP_200_OK)
        self.assertEqual(repeated.data["id"], str(local_family.pk))
        self.assertEqual(
            GarmentFamily.objects.filter(
                tenant=self.shop_a, template_source=self.family
            ).count(),
            1,
        )

    def test_shop_owned_family_config_isolated_and_used_by_design_validation(self):
        family = GarmentFamily.objects.create(
            tenant=self.shop_a, code="shop-a-custom-shirt"
        )
        multi_group = OptionGroup.objects.create(
            tenant=None, code="shop-isolation-multi"
        )
        config_path = self.shop_url(
            self.shop_a, f"catalog/garment-families/{family.pk}/option-groups/"
        )
        global_mappings = list(
            FamilyOptionGroup.objects.filter(family=self.family)
            .order_by("option_group_id")
            .values_list(
                "option_group_id", "sort_order", "selection_mode", "is_required"
            )
        )

        self.client.force_authenticate(self.admin)
        saved = self.client.put(
            config_path,
            {
                "option_groups": [
                    {
                        "option_group_id": str(self.group.pk),
                        "selection_mode": "SINGLE",
                        "is_required": True,
                        "sort_order": 0,
                    },
                    {
                        "option_group_id": str(multi_group.pk),
                        "selection_mode": "MULTI",
                        "is_required": False,
                        "sort_order": 1,
                    },
                ]
            },
            format="json",
        )
        self.assertEqual(saved.status_code, status.HTTP_200_OK, saved.data)
        saved_by_code = {row["option_group"]["code"]: row for row in saved.data}
        self.assertEqual(len(saved_by_code), 2)
        self.assertEqual(saved_by_code[self.group.code]["selection_mode"], "SINGLE")
        self.assertTrue(saved_by_code[self.group.code]["is_required"])
        self.assertEqual(saved_by_code[multi_group.code]["selection_mode"], "MULTI")
        self.assertFalse(saved_by_code[multi_group.code]["is_required"])

        design = self.client.post(
            self.shop_url(self.shop_a, "designs/"),
            {"family_id": str(family.pk), "name": "Shop A Custom Shirt"},
            format="json",
        )
        self.assertEqual(design.status_code, status.HTTP_201_CREATED, design.data)
        version_id = design.data["latest_version"]["id"]
        publish_url = self.shop_url(
            self.shop_a, f"design-versions/{version_id}/publish/"
        )
        missing_required = self.client.post(publish_url, {}, format="json")
        self.assertEqual(missing_required.status_code, status.HTTP_400_BAD_REQUEST)

        selected = self.client.post(
            self.shop_url(self.shop_a, f"design-versions/{version_id}/selections/"),
            {"style_option_id": str(self.global_option.pk)},
            format="json",
        )
        self.assertEqual(selected.status_code, status.HTTP_201_CREATED, selected.data)
        second_option = self.make_option(
            tenant=None, code="shop-isolation-second-cuff", label="Second Cuff"
        )
        single_violation = self.client.post(
            self.shop_url(self.shop_a, f"design-versions/{version_id}/selections/"),
            {"style_option_id": str(second_option.pk)},
            format="json",
        )
        self.assertEqual(
            single_violation.status_code, status.HTTP_400_BAD_REQUEST
        )
        multi_options = []
        for code, label in (
            ("shop-isolation-multi-a", "Multi Option A"),
            ("shop-isolation-multi-b", "Multi Option B"),
        ):
            option = StyleOption.objects.create(
                tenant=None, option_group=multi_group, code=code
            )
            StyleOptionTranslation.objects.create(
                style_option=option, locale="en", name=label
            )
            multi_options.append(option)
        for option in multi_options:
            accepted = self.client.post(
                self.shop_url(
                    self.shop_a, f"design-versions/{version_id}/selections/"
                ),
                {"style_option_id": str(option.pk)},
                format="json",
            )
            self.assertEqual(accepted.status_code, status.HTTP_201_CREATED)
        published = self.client.post(publish_url, {}, format="json")
        self.assertEqual(published.status_code, status.HTTP_200_OK, published.data)

        self.assertEqual(
            list(
                FamilyOptionGroup.objects.filter(family=self.family)
                .order_by("option_group_id")
                .values_list(
                    "option_group_id", "sort_order", "selection_mode", "is_required"
                )
            ),
            global_mappings,
        )
        self.client.force_authenticate(self.other_admin)
        foreign_family = self.client.get(
            self.shop_url(
                self.shop_b, f"catalog/garment-families/{family.pk}/option-groups/"
            )
        )
        self.assertEqual(foreign_family.status_code, status.HTTP_404_NOT_FOUND)
        shop_b_defaults = self.client.get(
            self.shop_url(
                self.shop_b,
                f"catalog/garment-families/{self.family.pk}/option-groups/",
            )
        )
        self.assertEqual(shop_b_defaults.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(self.admin)
        shop_a_defaults = self.client.get(
            self.shop_url(
                self.shop_a,
                f"catalog/garment-families/{self.family.pk}/option-groups/",
            )
        )
        self.assertEqual(shop_a_defaults.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [
                (
                    row["option_group"]["id"],
                    row["sort_order"],
                    row["selection_mode"],
                    row["is_required"],
                )
                for row in shop_b_defaults.data
            ],
            [
                (
                    row["option_group"]["id"],
                    row["sort_order"],
                    row["selection_mode"],
                    row["is_required"],
                )
                for row in shop_a_defaults.data
            ],
        )

    def test_shop_variant_writes_are_retired_and_legacy_rows_remain_shop_scoped(self):
        payload = {
            "family_id": str(self.family.pk),
            "code": "relaxed-shirt",
            "translations": [
                {"locale": "en", "name": "Relaxed Shirt"},
                {"locale": "ar-KW", "name": "قميص مريح"},
            ],
        }
        self.client.force_authenticate(self.viewer)
        denied = self.client.post(
            self.shop_url(self.shop_a, "catalog/variants/"), payload, format="json"
        )
        self.assertEqual(denied.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.client.force_authenticate(self.admin)
        created = self.client.post(
            self.shop_url(self.shop_a, "catalog/variants/"), payload, format="json"
        )
        self.assertEqual(created.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        variant = GarmentVariant.objects.create(
            tenant=self.shop_a, family=self.family, code="legacy-relaxed-shirt"
        )
        self.assertEqual(
            self.client.get(
                self.shop_url(self.shop_a, "catalog/variants/")
            ).status_code,
            status.HTTP_200_OK,
        )
        self.client.force_authenticate(self.other_admin)
        hidden = self.client.get(self.shop_url(self.shop_b, "catalog/variants/"))
        self.assertEqual(hidden.status_code, status.HTTP_200_OK)
        self.assertFalse(
            any(str(item["id"]) == str(variant.pk) for item in hidden.data["results"])
        )
        self.client.force_authenticate(self.admin)
        duplicate = self.client.post(
            self.shop_url(self.shop_a, "catalog/variants/"), payload, format="json"
        )
        self.assertEqual(duplicate.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.client.force_authenticate(self.other_admin)
        foreign_design = self.create_design(shop=self.shop_b)
        self.assertEqual(foreign_design.status_code, status.HTTP_201_CREATED)
        foreign_selection = self.client.post(
            self.shop_url(
                self.shop_b,
                f"design-versions/{foreign_design.data['latest_version']['id']}/selections/",
            ),
            {"style_option_id": str(variant.pk)},
            format="json",
        )
        self.assertEqual(foreign_selection.status_code, status.HTTP_404_NOT_FOUND)

    def test_custom_styles_are_shop_scoped_and_global_defaults_are_read_only(self):
        self.client.force_authenticate(self.admin)
        url = self.shop_url(self.shop_a, "catalog/style-options/")
        payload = {
            "option_group_id": str(self.group.pk),
            "code": "shop-round-cuff",
            "translations": [{"locale": "en", "name": "Shop Round"}],
        }
        created = self.client.post(url, payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(created.data["tenant"]), str(self.shop_a.pk))
        rows_a = self.client.get(f"{url}?option_group={self.group.pk}").data
        self.assertTrue(
            any(row["id"] == created.data["id"] for row in rows_a["results"])
        )
        self.client.force_authenticate(self.main)
        rows_b = self.client.get(
            self.shop_url(
                self.shop_b,
                f"catalog/style-options/?option_group={self.group.pk}",
            )
        ).data
        self.assertFalse(
            any(row["id"] == created.data["id"] for row in rows_b["results"])
        )
        self.assertTrue(
            any(
                str(row["id"]) == str(self.global_option.pk)
                for row in rows_b["results"]
            )
        )

    def test_design_snapshot_style_copies_are_not_selectable_catalog_options(self):
        snapshot_copy = StyleOption.objects.create(
            tenant=self.shop_a,
            option_group=self.group,
            code="normal-cuff-copy-design-snapshot",
            source_style_option=self.global_option,
        )
        StyleOptionTranslation.objects.create(
            style_option=snapshot_copy, locale="en", name="Normal Cuff"
        )
        self.client.force_authenticate(self.admin)

        catalog_url = self.shop_url(
            self.shop_a, f"catalog/style-options/?option_group={self.group.pk}"
        )
        listed = self.client.get(catalog_url)
        listed_ids = {row["id"] for row in listed.data["results"]}
        self.assertIn(str(self.global_option.pk), listed_ids)
        self.assertNotIn(str(snapshot_copy.pk), listed_ids)

        before = Design.objects.filter(tenant=self.shop_a).count()
        invalid_design = self.client.post(
            self.shop_url(self.shop_a, "designs/"),
            {
                "family_id": str(self.family.pk),
                "variant_id": str(self.variant.pk),
                "name": "Cannot Select Snapshot Copy",
                "selection_ids": [str(snapshot_copy.pk)],
            },
            format="json",
        )
        self.assertEqual(invalid_design.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Design.objects.filter(tenant=self.shop_a).count(), before)

        created = self.create_design()
        version_id = created.data["latest_version"]["id"]
        invalid_add = self.client.post(
            self.shop_url(self.shop_a, f"design-versions/{version_id}/selections/"),
            {"style_option_id": str(snapshot_copy.pk)},
            format="json",
        )
        self.assertEqual(invalid_add.status_code, status.HTTP_404_NOT_FOUND)

        valid_add = self.client.post(
            self.shop_url(self.shop_a, f"design-versions/{version_id}/selections/"),
            {"style_option_id": str(self.global_option.pk)},
            format="json",
        )
        self.assertEqual(valid_add.status_code, status.HTTP_201_CREATED)
        invalid_replace = self.client.patch(
            self.shop_url(
                self.shop_a,
                f"design-versions/{version_id}/selections/{valid_add.data['id']}/",
            ),
            {"style_option_id": str(snapshot_copy.pk)},
            format="json",
        )
        self.assertEqual(invalid_replace.status_code, status.HTTP_404_NOT_FOUND)

    def test_shop_style_option_translation_edit_is_scoped_and_preserves_identity(self):
        option = self.make_option(
            tenant=self.shop_a, code="editable-cuff", label="Original Cuff"
        )
        StyleOptionTranslation.objects.create(
            style_option=option,
            locale="ar-KW",
            name="كفة أصلية",
            description="Existing localized description",
        )
        endpoint = self.shop_url(self.shop_a, f"catalog/style-options/{option.pk}/")
        self.client.force_authenticate(self.admin)
        updated = self.client.patch(
            endpoint,
            {"translations": [{"locale": "en", "name": "Updated Cuff"}]},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["name"], "Updated Cuff")
        option.refresh_from_db()
        self.assertEqual(option.code, "editable-cuff")
        self.assertEqual(option.tenant_id, self.shop_a.pk)
        self.assertEqual(option.option_group_id, self.group.pk)
        self.assertEqual(option.translations.get(locale="en").name, "Updated Cuff")
        arabic = option.translations.get(locale="ar-KW")
        self.assertEqual(arabic.name, "كفة أصلية")
        self.assertEqual(arabic.description, "Existing localized description")

        self.client.force_authenticate(self.staff)
        staff_update = self.client.patch(
            endpoint,
            {"translations": [{"locale": "en", "name": "Staff Updated Cuff"}]},
            format="json",
        )
        self.assertEqual(staff_update.status_code, status.HTTP_200_OK)

        archived = self.client.patch(endpoint, {"is_active": False}, format="json")
        self.assertEqual(archived.status_code, status.HTTP_200_OK)
        self.assertFalse(archived.data["is_active"])

    def test_shop_style_option_edit_denies_viewer_and_hides_foreign_or_global_options(
        self,
    ):
        local_option = self.make_option(
            tenant=self.shop_a, code="private-edit-cuff", label="Private Cuff"
        )
        payload = {"translations": [{"locale": "en", "name": "Changed"}]}
        self.client.force_authenticate(self.viewer)
        denied = self.client.patch(
            self.shop_url(self.shop_a, f"catalog/style-options/{local_option.pk}/"),
            payload,
            format="json",
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.other_admin)
        foreign = self.client.patch(
            self.shop_url(self.shop_b, f"catalog/style-options/{local_option.pk}/"),
            payload,
            format="json",
        )
        self.assertEqual(foreign.status_code, status.HTTP_404_NOT_FOUND)
        global_option = self.client.patch(
            self.shop_url(
                self.shop_b, f"catalog/style-options/{self.global_option.pk}/"
            ),
            payload,
            format="json",
        )
        self.assertEqual(global_option.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            self.global_option.translations.get(locale="en").name, "Normal Cuff"
        )

    def test_shop_style_option_edit_rejects_identity_changes_and_bad_translation_sets(
        self,
    ):
        option = self.make_option(
            tenant=self.shop_a, code="immutable-edit-cuff", label="Original"
        )
        endpoint = self.shop_url(self.shop_a, f"catalog/style-options/{option.pk}/")
        self.client.force_authenticate(self.admin)
        invalid_payloads = (
            {"translations": []},
            {
                "translations": [
                    {"locale": "en", "name": "First"},
                    {"locale": "en", "name": "Second"},
                ]
            },
            {"translations": [{"locale": "en", "name": "Changed"}], "code": "new"},
            {"name": "Changed"},
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.patch(endpoint, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(option.translations.get(locale="en").name, "Original")

    def test_viewer_cannot_create_design_and_admin_can_create_blank_draft(self):
        self.client.force_authenticate(self.viewer)
        denied = self.create_design()
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.admin)
        response = self.create_design()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        design = Design.objects.get(pk=response.data["id"])
        self.assertEqual(design.tenant_id, self.shop_a.pk)
        version = design.versions.get()
        self.assertEqual(version.status, DesignVersion.Status.DRAFT)
        self.assertEqual(version.translations.get(locale="en").name, "Blue Shirt")

    def test_design_create_can_set_shop_price_atomically_with_admin_or_cashier(self):
        self.shop_a.default_currency = "KWD"
        self.shop_a.save(update_fields=["default_currency"])
        MembershipWorkFunction.objects.create(
            membership=self.staff_membership, function_code="CASHIER"
        )
        self.client.force_authenticate(self.staff)
        response = self.client.post(
            self.shop_url(self.shop_a, "designs/"),
            {
                "family_id": str(self.family.pk),
                "name": "Priced design",
                "idempotency_key": "62345678-1234-5678-1234-567812345678",
                "price": {"amount": "18.750"},
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        price = ShopDesignPrice.objects.get(
            tenant=self.shop_a, design_id=response.data["id"]
        )
        self.assertEqual(price.amount, Decimal("18.750"))
        self.assertEqual(price.currency, "KWD")

        self.client.force_authenticate(self.staff)
        MembershipWorkFunction.objects.filter(
            membership=self.staff_membership, function_code="CASHIER"
        ).delete()
        denied = self.client.post(
            self.shop_url(self.shop_a, "designs/"),
            {
                "family_id": str(self.family.pk),
                "name": "No price access",
                "price": {"amount": "20.000"},
            },
            format="json",
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        no_currency_shop = self.make_shop("No Currency Shop", "no-currency-shop")
        no_currency_admin, _ = self.make_member(
            "catalog-no-currency@example.test", no_currency_shop, ShopRole.ADMIN
        )
        self.client.force_authenticate(no_currency_admin)
        before = Design.objects.filter(tenant=no_currency_shop).count()
        blocked = self.client.post(
            self.shop_url(no_currency_shop, "designs/"),
            {
                "family_id": str(self.family.pk),
                "name": "Blocked price",
                "price": {"amount": "20.000"},
            },
            format="json",
        )
        self.assertEqual(blocked.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Design.objects.filter(tenant=no_currency_shop).count(), before)
        self.assertFalse(ShopDesignPrice.objects.filter(tenant=no_currency_shop).exists())

    def test_design_create_saves_selections_atomically_and_retry_is_idempotent(self):
        self.client.force_authenticate(self.admin)
        payload = {
            "family_id": str(self.family.pk),
            "variant_id": str(self.variant.pk),
            "name": "Retry-safe Shirt",
            "selection_ids": [str(self.global_option.pk)],
            "idempotency_key": "12345678-1234-5678-1234-567812345678",
        }
        first = self.client.post(
            self.shop_url(self.shop_a, "designs/"), payload, format="json"
        )
        retry = self.client.post(
            self.shop_url(self.shop_a, "designs/"), payload, format="json"
        )

        self.assertEqual(first.status_code, status.HTTP_201_CREATED, first.data)
        self.assertEqual(retry.status_code, status.HTTP_201_CREATED, retry.data)
        self.assertEqual(first.data["id"], retry.data["id"])
        self.assertEqual(len(first.data["latest_version"]["selections"]), 1)
        self.assertEqual(
            Design.objects.filter(
                tenant=self.shop_a,
                client_request_id=payload["idempotency_key"],
            ).count(),
            1,
        )

    def test_design_create_rolls_back_when_a_selection_is_not_mapped_to_family(self):
        fabric_group = OptionGroup.objects.get(code="fabric")
        invalid_option = StyleOption.objects.create(
            tenant=self.shop_a, option_group=fabric_group, code="unmapped-fabric"
        )
        StyleOptionTranslation.objects.create(
            style_option=invalid_option, locale="en", name="Unmapped Fabric"
        )
        self.client.force_authenticate(self.admin)
        before = Design.objects.filter(tenant=self.shop_a).count()
        response = self.client.post(
            self.shop_url(self.shop_a, "designs/"),
            {
                "family_id": str(self.family.pk),
                "variant_id": str(self.variant.pk),
                "name": "Must Roll Back",
                "selection_ids": [str(invalid_option.pk)],
                "idempotency_key": "22345678-1234-5678-1234-567812345678",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Design.objects.filter(tenant=self.shop_a).count(), before)

    def test_design_create_supports_shop_variant_with_no_style_groups(self):
        family = GarmentFamily.objects.create(code="shop-empty-style-family")
        GarmentFamilyTranslation.objects.create(
            family=family, locale="en", name="Shop Empty Style Family"
        )
        variant = GarmentVariant.objects.create(
            family=family,
            tenant=self.shop_a,
            code="shop-first-variant",
            is_default=False,
        )
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            self.shop_url(self.shop_a, "designs/"),
            {
                "family_id": str(family.pk),
                "variant_id": str(variant.pk),
                "name": "No Groups Design",
                "selection_ids": [],
                "idempotency_key": "32345678-1234-5678-1234-567812345678",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["latest_version"]["selections"], [])

    def test_design_foreign_shop_is_non_disclosing(self):
        self.client.force_authenticate(self.admin)
        created = self.create_design()
        self.client.force_authenticate(self.other_admin)
        foreign = self.client.get(
            self.shop_url(self.shop_b, f"designs/{created.data['id']}/")
        )
        self.assertEqual(foreign.status_code, status.HTTP_404_NOT_FOUND)

    def test_shop_design_list_uses_standard_page_number_pagination(self):
        self.client.force_authenticate(self.admin)
        self.create_design(name="First Paginated Shirt")
        response = self.client.get(self.shop_url(self.shop_a, "designs/?page=1"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

    def test_selection_keeps_source_style_and_captures_its_image_references(self):
        self.client.force_authenticate(self.admin)
        self.client.force_authenticate(self.main)
        uploaded = self.client.post(
            self.shop_url(
                self.shop_a,
                f"catalog/style-options/{self.global_option.pk}/reference-images/",
            ),
            {"images": [self.png_upload()]},
            format="multipart",
        )
        self.assertEqual(uploaded.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(self.admin)
        created = self.create_design()
        version_id = created.data["latest_version"]["id"]
        selected = self.client.post(
            self.shop_url(self.shop_a, f"design-versions/{version_id}/selections/"),
            {"style_option_id": str(self.global_option.pk)},
            format="json",
        )
        self.assertEqual(selected.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(selected.data["style_option"]), str(self.global_option.pk))
        self.assertEqual(len(selected.data["style_option_images"]), 1)
        self.assertEqual(DesignSelectionImage.objects.count(), 1)
        gallery = self.client.get(
            self.shop_url(self.shop_a, f"design-versions/{version_id}/references/")
        )
        self.assertEqual(gallery.status_code, status.HTTP_200_OK)
        self.assertEqual(gallery.data[0]["source"], "style_option")
        self.assertEqual(gallery.data[0]["style_option_id"], str(self.global_option.pk))
        selected_name = selected.data["style_option_name"]
        StyleOptionTranslation.objects.filter(
            style_option=self.global_option, locale="en"
        ).update(name="Changed After Selection")
        design = self.client.get(
            self.shop_url(self.shop_a, f"designs/{created.data['id']}/")
        )
        self.assertEqual(
            design.data["latest_version"]["selections"][0]["style_option_name"],
            selected_name,
        )

    def test_draft_selection_can_be_replaced_from_the_same_catalog_group(self):
        self.client.force_authenticate(self.admin)
        created = self.create_design()
        version_id = created.data["latest_version"]["id"]
        selected = self.client.post(
            self.shop_url(self.shop_a, f"design-versions/{version_id}/selections/"),
            {"style_option_id": str(self.global_option.pk)},
            format="json",
        )
        self.assertEqual(selected.status_code, status.HTTP_201_CREATED)

        replacement = self.make_option(
            tenant=None, code="edited-cuff-choice", label="Edited Cuff"
        )
        response = self.client.patch(
            self.shop_url(
                self.shop_a,
                f"design-versions/{version_id}/selections/{selected.data['id']}/",
            ),
            {"style_option_id": str(replacement.pk)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(str(response.data["style_option"]), str(replacement.pk))
        self.assertEqual(response.data["selected_code"], "edited-cuff-choice")
        self.assertEqual(response.data["style_option_name"], "Edited Cuff")
        selection = DesignSelection.objects.get(pk=selected.data["id"])
        self.assertEqual(selection.translations.get(locale="en").name, "Edited Cuff")

        unrelated_group = OptionGroup.objects.create(
            tenant=None, code="unmapped-design-part"
        )
        unrelated_option = StyleOption.objects.create(
            tenant=None, option_group=unrelated_group, code="unmapped-choice"
        )
        wrong_group = self.client.patch(
            self.shop_url(
                self.shop_a,
                f"design-versions/{version_id}/selections/{selected.data['id']}/",
            ),
            {"style_option_id": str(unrelated_option.pk)},
            format="json",
        )
        self.assertEqual(wrong_group.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.force_authenticate(self.staff)
        replacement_again = self.make_option(
            tenant=None, code="staff-edited-cuff", label="Staff Edited Cuff"
        )
        staff_response = self.client.patch(
            self.shop_url(
                self.shop_a,
                f"design-versions/{version_id}/selections/{selected.data['id']}/",
            ),
            {"style_option_id": str(replacement_again.pk)},
            format="json",
        )
        self.assertEqual(staff_response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(self.admin)
        published = self.client.post(
            self.shop_url(self.shop_a, f"design-versions/{version_id}/publish/"),
            {},
            format="json",
        )
        self.assertEqual(published.status_code, status.HTTP_200_OK)
        immutable = self.client.patch(
            self.shop_url(
                self.shop_a,
                f"design-versions/{version_id}/selections/{selected.data['id']}/",
            ),
            {"style_option_id": str(self.global_option.pk)},
            format="json",
        )
        self.assertEqual(immutable.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.force_authenticate(self.other_admin)
        foreign_response = self.client.patch(
            self.shop_url(
                self.shop_b,
                f"design-versions/{version_id}/selections/{selected.data['id']}/",
            ),
            {"style_option_id": str(self.global_option.pk)},
            format="json",
        )
        self.assertEqual(foreign_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_published_version_children_are_immutable_and_new_draft_is_a_snapshot(self):
        self.client.force_authenticate(self.admin)
        created = self.create_design()
        version_id = created.data["latest_version"]["id"]
        selected = self.client.post(
            self.shop_url(self.shop_a, f"design-versions/{version_id}/selections/"),
            {"style_option_id": str(self.global_option.pk)},
            format="json",
        )
        self.assertEqual(selected.status_code, status.HTTP_201_CREATED)
        published = self.client.post(
            self.shop_url(self.shop_a, f"design-versions/{version_id}/publish/"),
            {},
            format="json",
        )
        self.assertEqual(published.status_code, status.HTTP_200_OK)
        snapshot = DesignVersion.objects.get(pk=published.data["next_draft"]["id"])
        self.assertEqual(snapshot.selections.count(), 1)
        self.assertEqual(
            snapshot.selections.get().translations.get(locale="en").name,
            "Normal Cuff",
        )
        edited = self.client.patch(
            self.shop_url(self.shop_a, f"designs/{created.data['id']}/"),
            {"name": "Updated Draft Shirt"},
            format="json",
        )
        self.assertEqual(edited.status_code, status.HTTP_200_OK)
        self.assertEqual(
            DesignVersionTranslation.objects.get(
                version_id=published.data["published"]["id"], locale="en"
            ).name,
            "Blue Shirt",
        )
        self.assertEqual(
            DesignVersionTranslation.objects.get(
                version_id=published.data["next_draft"]["id"], locale="en"
            ).name,
            "Updated Draft Shirt",
        )
        selection = DesignSelection.objects.get(pk=selected.data["id"])
        selection.selected_name_en = "Tampered"
        with self.assertRaises(ValidationError):
            selection.save()
        with self.assertRaises(ValidationError):
            selection.delete()

    def test_image_upload_is_optimized_private_and_shop_isolated(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post(
            self.shop_url(
                self.shop_a,
                f"catalog/style-options/{self.global_option.pk}/reference-images/",
            ),
            {"images": [self.png_upload()]},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Staff can add references to its own Shop option, but cannot mutate a global option.
        local_option = self.make_option(
            tenant=self.shop_a, code="staff-cuff", label="Staff Cuff"
        )
        response = self.client.post(
            self.shop_url(
                self.shop_a,
                f"catalog/style-options/{local_option.pk}/reference-images/",
            ),
            {"images": [self.png_upload()]},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        image = StyleOptionImage.objects.get(pk=response.data[0]["id"])
        self.assertNotIn("\\", image.image.name)
        self.assertLessEqual(len(image.image.name), 512)
        self.assertLessEqual(image.byte_size, 2 * 1024 * 1024)
        self.assertEqual(image.mime_type, "image/webp")
        if settings.R2_ENABLED:
            with self.assertRaises(NotImplementedError):
                image.image.path
        else:
            self.assertFalse(
                Path(image.image.path).is_relative_to(Path(settings.MEDIA_ROOT))
            )
        content_url = response.data[0]["content_url"]
        body = self.client.get(content_url)
        self.assertEqual(body.status_code, status.HTTP_200_OK)
        self.assertEqual(body["Content-Type"], "image/webp")
        self.assertIn("no-store", body["Cache-Control"])
        with patch.object(image.image.storage, "open", side_effect=FileNotFoundError):
            missing_object = self.client.get(content_url)
        self.assertEqual(missing_object.status_code, status.HTTP_404_NOT_FOUND)
        listed = self.client.get(
            self.shop_url(
                self.shop_a,
                f"catalog/style-options/?option_group={self.group.pk}",
            )
        )
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        persisted = next(
            row for row in listed.data["results"] if row["id"] == str(local_option.pk)
        )
        self.assertEqual(
            [reference["id"] for reference in persisted["reference_images"]],
            [str(image.pk)],
        )
        self.assertEqual(persisted["reference_images"][0]["content_url"], content_url)
        old_image_name = image.image.name
        replacement = self.client.post(
            self.shop_url(
                self.shop_a,
                f"catalog/style-options/{local_option.pk}/reference-images/",
            ),
            {"images": [self.png_upload("replacement.png")]},
            format="multipart",
        )
        self.assertEqual(replacement.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            StyleOptionImage.objects.filter(style_option=local_option).count(), 2
        )
        image.refresh_from_db()
        self.assertFalse(image.is_primary)
        current_image = StyleOptionImage.objects.get(
            style_option=local_option, is_primary=True
        )
        self.assertEqual(str(current_image.pk), replacement.data[0]["id"])
        self.assertTrue(image.image.storage.exists(old_image_name))
        self.assertEqual(self.client.get(content_url).status_code, status.HTTP_200_OK)
        persisted_again = self.client.get(
            self.shop_url(
                self.shop_a,
                f"catalog/style-options/?option_group={self.group.pk}",
            )
        )
        current_option = next(
            row
            for row in persisted_again.data["results"]
            if row["id"] == str(local_option.pk)
        )
        self.assertEqual(
            [row["id"] for row in current_option["reference_images"]],
            [str(current_image.pk)],
        )
        self.client.force_authenticate(self.other_admin)
        foreign_url = self.shop_url(
            self.shop_b,
            f"catalog/style-options/{local_option.pk}/reference-images/{image.pk}/",
        )
        self.assertEqual(
            self.client.get(foreign_url).status_code, status.HTTP_404_NOT_FOUND
        )

    def test_upload_rejects_multiple_files_and_unsupported_content(self):
        self.client.force_authenticate(self.admin)
        local_option = self.make_option(
            tenant=self.shop_a, code="invalid-upload-check", label="Upload Check"
        )
        endpoint = self.shop_url(
            self.shop_a,
            f"catalog/style-options/{local_option.pk}/reference-images/",
        )
        too_many = self.client.post(
            endpoint,
            {"images": [self.png_upload(f"{i}.png") for i in range(2)]},
            format="multipart",
        )
        self.assertEqual(too_many.status_code, status.HTTP_400_BAD_REQUEST)
        invalid = SimpleUploadedFile(
            "notes.txt", b"not an image", content_type="text/plain"
        )
        rejected = self.client.post(endpoint, {"images": [invalid]}, format="multipart")
        self.assertEqual(rejected.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(StyleOptionImage.objects.count(), 0)

    def test_image_processing_failure_is_a_validation_response(self):
        self.client.force_authenticate(self.admin)
        option = self.make_option(
            tenant=self.shop_a, code="compression-failure", label="Compression Failure"
        )
        endpoint = self.shop_url(
            self.shop_a, f"catalog/style-options/{option.pk}/reference-images/"
        )
        with patch(
            "apps.catalog.services.optimize_reference",
            side_effect=DRFValidationError(
                {"images": "Image could not be optimized below the 2 MB limit."}
            ),
        ):
            response = self.client.post(
                endpoint, {"images": [self.png_upload()]}, format="multipart"
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(StyleOptionImage.objects.count(), 0)

    def test_shop_admin_and_assigned_tailor_can_publish_only_shop_version(self):
        self.client.force_authenticate(self.staff)
        created = self.create_design()
        version_id = created.data["latest_version"]["id"]
        self.client.force_authenticate(self.staff)
        denied = self.client.post(
            self.shop_url(self.shop_a, f"design-versions/{version_id}/publish/"),
            {},
            format="json",
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        MembershipWorkFunction.objects.create(
            membership=self.staff_membership, function_code="STITCHING"
        )
        allowed = self.client.post(
            self.shop_url(self.shop_a, f"design-versions/{version_id}/publish/"),
            {},
            format="json",
        )
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)
        self.assertEqual(allowed.data["published"]["status"], "PUBLISHED")
        self.assertEqual(allowed.data["next_draft"]["status"], "DRAFT")
        self.assertEqual(
            allowed.data["next_draft"]["selections"],
            [],
        )
        self.client.force_authenticate(self.admin)
        admin_design = self.create_design(name="Admin Published Shirt")
        admin_publish = self.client.post(
            self.shop_url(
                self.shop_a,
                f"design-versions/{admin_design.data['latest_version']['id']}/publish/",
            ),
            {},
            format="json",
        )
        self.assertEqual(admin_publish.status_code, status.HTTP_200_OK)

    def test_main_supplier_cannot_publish_shop_design(self):
        self.client.force_authenticate(self.admin)
        created = self.create_design()
        self.client.force_authenticate(self.main)
        response = self.client.post(
            self.shop_url(
                self.shop_a,
                f"design-versions/{created.data['latest_version']['id']}/publish/",
            ),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_global_design_publication_is_main_supplier_only_and_templates_are_copyable(
        self,
    ):
        self.client.force_authenticate(self.main)
        create = self.client.post(
            "/api/v1/catalog/design-templates/",
            {
                "family_id": str(self.family.pk),
                "variant_id": str(self.variant.pk),
                "name": "Default Shirt",
            },
            format="json",
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        design_id = create.data["id"]
        version_id = create.data["latest_version"]["id"]
        publish = self.client.post(
            f"/api/v1/catalog/design-templates/{design_id}/versions/{version_id}/publish/",
            {},
            format="json",
        )
        self.assertEqual(publish.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(self.admin)
        templates = self.client.get("/api/v1/catalog/design-templates/")
        self.assertTrue(
            any(str(item["id"]) == str(design_id) for item in templates.data["results"])
        )
        copy = self.client.post(
            self.shop_url(self.shop_a, "designs/"),
            {
                "family_id": str(self.family.pk),
                "variant_id": str(self.variant.pk),
                "name": "My Shirt",
                "source_design_id": design_id,
                "source_version_id": publish.data["published"]["id"],
            },
            format="json",
        )
        self.assertEqual(copy.status_code, status.HTTP_201_CREATED)
        copied = Design.objects.get(pk=copy.data["id"])
        self.assertEqual(copied.tenant_id, self.shop_a.pk)
        self.assertEqual(str(copied.source_design_id), design_id)

    def test_copy_from_published_shop_design_is_independent_and_survives_source_archive(
        self,
    ):
        self.client.force_authenticate(self.admin)
        source = self.create_design(name="Source Design")
        source_version = source.data["latest_version"]["id"]
        style = self.make_option(
            tenant=self.shop_a, code="copy-source-cuff", label="Source Cuff"
        )
        uploaded = self.client.post(
            self.shop_url(
                self.shop_a, f"catalog/style-options/{style.pk}/reference-images/"
            ),
            {"images": [self.png_upload("source-style.png")]},
            format="multipart",
        )
        self.assertEqual(uploaded.status_code, status.HTTP_201_CREATED)
        selected = self.client.post(
            self.shop_url(self.shop_a, f"design-versions/{source_version}/selections/"),
            {"style_option_id": str(style.pk)},
            format="json",
        )
        self.assertEqual(selected.status_code, status.HTTP_201_CREATED)
        direct_reference = self.client.post(
            self.shop_url(self.shop_a, f"design-versions/{source_version}/references/"),
            {"images": [self.png_upload("direct-reference.png", color=(160, 70, 30))]},
            format="multipart",
        )
        self.assertEqual(direct_reference.status_code, status.HTTP_201_CREATED)
        self.client.post(
            self.shop_url(self.shop_a, f"design-versions/{source_version}/publish/"),
            {},
            format="json",
        )
        source_version_record = DesignVersion.objects.get(pk=source_version)
        copied_response = self.client.post(
            self.shop_url(self.shop_a, "designs/"),
            {
                "family_id": str(self.family.pk),
                "variant_id": str(self.variant.pk),
                "name": "Independent Copy",
                "source_design_id": str(source.data["id"]),
                "source_version_id": str(source_version),
            },
            format="json",
        )
        self.assertEqual(copied_response.status_code, status.HTTP_201_CREATED)
        copied = Design.objects.get(pk=copied_response.data["id"])
        copied_selection = copied.versions.get().selections.get()
        self.assertNotEqual(copied_selection.style_option_id, style.pk)
        self.assertEqual(copied_selection.style_option.tenant_id, self.shop_a.pk)
        copied_image = copied_selection.reference_images.get().source_image
        self.assertNotEqual(
            copied_image.pk, StyleOptionImage.objects.get(pk=uploaded.data[0]["id"]).pk
        )
        self.assertEqual(copied_image.style_option_id, copied_selection.style_option_id)
        copied_reference = copied.versions.get().references.get()
        self.assertNotEqual(
            copied_reference.pk,
            DesignReference.objects.get(pk=direct_reference.data[0]["id"]).pk,
        )
        archive = self.client.delete(
            self.shop_url(self.shop_a, f"designs/{source.data['id']}/")
        )
        self.assertEqual(archive.status_code, status.HTTP_200_OK)
        self.assertEqual(copied.versions.get().selections.count(), 1)
        self.assertEqual(source_version_record.status, DesignVersion.Status.PUBLISHED)

    def test_staff_without_stitching_cannot_archive_or_publish_as_tailor(self):
        self.client.force_authenticate(self.admin)
        created = self.create_design()
        version_id = created.data["latest_version"]["id"]
        self.client.force_authenticate(self.staff)
        response = self.client.post(
            self.shop_url(self.shop_a, f"design-versions/{version_id}/publish/"),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(
        R2_ENABLED=True,
        R2_BUCKET_NAME="birkos-staging-private",
        R2_ENDPOINT="https://example-account.r2.cloudflarestorage.com",
        R2_ACCESS_KEY_ID="test-access-key",
        R2_SECRET_ACCESS_KEY="test-secret-key",
        R2_REGION="auto",
    )
    @patch.object(
        PrivateReferenceStorage,
        "presigned_upload",
        return_value="https://r2.example.invalid/signed-put",
    )
    def test_shop_private_upload_authorization_is_scoped_and_non_cacheable(
        self, _presigned
    ):
        shop_option = self.make_option(
            tenant=self.shop_a, code="upload-cuff-a", label="Shop A Cuff"
        )
        foreign_option = self.make_option(
            tenant=self.shop_b, code="upload-cuff-b", label="Shop B Cuff"
        )
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            self.shop_url(self.shop_a, "catalog/media/uploads/"),
            {
                "action": "authorize",
                "kind": "style_option",
                "target_id": str(shop_option.pk),
                "content_type": "image/png",
                "byte_size": 128,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(
            response.data["upload_url"], "https://r2.example.invalid/signed-put"
        )
        ticket = PrivateMediaUpload.objects.get()
        self.assertEqual(ticket.tenant_id, self.shop_a.pk)
        self.assertEqual(ticket.actor_id, self.admin.pk)
        self.assertEqual(ticket.target_id, shop_option.pk)
        self.assertTrue(
            ticket.object_key.startswith(f"pending/shops/{self.shop_a.pk}/")
        )
        self.assertNotIn("Shop A", ticket.object_key)

        denied = self.client.post(
            self.shop_url(self.shop_a, "catalog/media/uploads/"),
            {
                "action": "authorize",
                "kind": "style_option",
                "target_id": str(foreign_option.pk),
                "content_type": "image/png",
                "byte_size": 128,
            },
            format="json",
        )
        self.assertEqual(denied.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(PrivateMediaUpload.objects.count(), 1)

    @override_settings(
        R2_ENABLED=True,
        R2_BUCKET_NAME="birkos-staging-private",
        R2_ENDPOINT="https://example-account.r2.cloudflarestorage.com",
        R2_ACCESS_KEY_ID="test-access-key",
        R2_SECRET_ACCESS_KEY="test-secret-key",
        R2_REGION="auto",
    )
    @patch.object(
        PrivateReferenceStorage,
        "presigned_upload",
        return_value="https://r2.example.invalid/signed-put",
    )
    def test_private_upload_rejects_invalid_mime_and_oversized_files(self, _presigned):
        option = self.make_option(
            tenant=self.shop_a, code="upload-validation-cuff", label="Validation Cuff"
        )
        self.client.force_authenticate(self.admin)
        for content_type, byte_size in (
            ("image/svg+xml", 32),
            ("image/png", 10 * 1024 * 1024 + 1),
        ):
            response = self.client.post(
                self.shop_url(self.shop_a, "catalog/media/uploads/"),
                {
                    "action": "authorize",
                    "kind": "style_option",
                    "target_id": str(option.pk),
                    "content_type": content_type,
                    "byte_size": byte_size,
                },
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PrivateMediaUpload.objects.exists())
