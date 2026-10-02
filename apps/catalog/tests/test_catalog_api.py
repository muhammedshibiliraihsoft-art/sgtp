from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.test import APITestCase

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
    GarmentVariant,
    OptionGroup,
    StyleOption,
    StyleOptionImage,
    StyleOptionTranslation,
)
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
        FamilyOptionGroup.objects.create(family=self.family, option_group=self.group)
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

    def create_design(self, *, client=None, shop=None, name="Blue Shirt"):
        client = client or self.client
        shop = shop or self.shop_a
        response = client.post(
            self.shop_url(shop, "designs/"),
            {
                "family_id": str(self.family.pk),
                "variant_id": str(self.variant.pk),
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
            {"normal-cuff", "open-cuff", "round-cuff", "square-cuff", "custom"},
        )
        self.assertNotIn("french-cuff", cuff_codes)

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
        self.assertEqual(custom_response.status_code, status.HTTP_201_CREATED)
        rows = self.client.get("/api/v1/catalog/variants/").data["results"]
        self.assertFalse(any(row["id"] == custom_response.data["id"] for row in rows))

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
        response = self.client.get("/api/v1/catalog/style-options/?locale=ur")
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

    def test_shop_custom_variants_are_shop_owned_and_viewer_cannot_create(self):
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
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.admin)
        created = self.client.post(
            self.shop_url(self.shop_a, "catalog/variants/"), payload, format="json"
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        variant = GarmentVariant.objects.get(pk=created.data["id"])
        self.assertEqual(variant.tenant_id, self.shop_a.pk)
        self.assertFalse(variant.is_default)
        self.assertEqual(variant.translations.get(locale="ar-KW").name, "قميص مريح")
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
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
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
        rows_a = self.client.get(url).data
        self.assertTrue(
            any(row["id"] == created.data["id"] for row in rows_a["results"])
        )
        self.client.force_authenticate(self.main)
        rows_b = self.client.get(
            self.shop_url(self.shop_b, "catalog/style-options/")
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
        self.assertLessEqual(image.byte_size, 2 * 1024 * 1024)
        self.assertEqual(image.mime_type, "image/webp")
        self.assertFalse(
            Path(image.image.path).is_relative_to(Path(settings.MEDIA_ROOT))
        )
        content_url = response.data[0]["content_url"]
        body = self.client.get(content_url)
        self.assertEqual(body.status_code, status.HTTP_200_OK)
        self.assertEqual(body["Content-Type"], "image/webp")
        self.assertIn("no-store", body["Cache-Control"])
        self.client.force_authenticate(self.other_admin)
        foreign_url = self.shop_url(
            self.shop_b,
            f"catalog/style-options/{local_option.pk}/reference-images/{image.pk}/",
        )
        self.assertEqual(
            self.client.get(foreign_url).status_code, status.HTTP_404_NOT_FOUND
        )

    def test_upload_rejects_four_files_and_unsupported_content(self):
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
            {"images": [self.png_upload(f"{i}.png") for i in range(4)]},
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
