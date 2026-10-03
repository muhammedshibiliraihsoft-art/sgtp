from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.catalog.models import (
    Design,
    GarmentFamily,
    GarmentVariant,
    GarmentVariantTranslation,
)
from apps.tenants.models import Supplier, Tenant, TenantMember


class VariantLifecycleApiTests(APITestCase):
    def setUp(self):
        supplier = Supplier.objects.get(singleton_lock=True)
        self.shop_a = Tenant.objects.create(
            supplier=supplier,
            name="Variant Shop A",
            slug="variant-shop-a",
            max_users=20,
        )
        self.shop_b = Tenant.objects.create(
            supplier=supplier,
            name="Variant Shop B",
            slug="variant-shop-b",
            max_users=20,
        )
        self.admin = self._member("variant-admin-a@example.test", self.shop_a, "ADMIN")
        self.staff = self._member("variant-staff-a@example.test", self.shop_a, "STAFF")
        self.viewer = self._member(
            "variant-viewer-a@example.test", self.shop_a, "VIEWER"
        )
        self.other_admin = self._member(
            "variant-admin-b@example.test", self.shop_b, "ADMIN"
        )
        self.main = User.objects.create_superuser(
            email="variant-main@example.test",
            password="Safe-Test-Password-293!",
            first_name="Variant Main",
            phone="+96550001900",
        )
        self.family = GarmentFamily.objects.get(code="mens-shirt")
        self.default_variant = GarmentVariant.objects.get(
            tenant__isnull=True, family=self.family, is_default=True
        )

    @staticmethod
    def _member(email, shop, role):
        user = User.objects.create_user(
            email=email,
            password="Safe-Test-Password-293!",
            first_name="Variant User",
            owning_shop=shop,
        )
        TenantMember.objects.create(tenant=shop, user=user, role=role)
        return user

    def _variant(self, *, shop=None, code="variant-standard", family=None):
        variant = GarmentVariant.objects.create(
            tenant=shop,
            family=family or self.family,
            code=code,
        )
        GarmentVariantTranslation.objects.create(
            variant=variant, locale="en", name=f"Name {code}", description="Old"
        )
        return variant

    def _shop_url(self, shop, suffix=""):
        return f"/api/v1/shops/{shop.pk}/{suffix}"

    def _global_url(self, suffix=""):
        return f"/api/v1/catalog/variants/{suffix}"

    def _create_payload(self, code="new-variant"):
        return {
            "family_id": str(self.family.pk),
            "code": code,
            "translations": [
                {"locale": "en", "name": "New Variant", "description": "Details"},
                {"locale": "bn", "name": "Bangla Variant", "description": "Bangla"},
            ],
        }

    def test_shop_list_supports_search_family_source_status_and_shop_isolation(self):
        shop_variant = self._variant(shop=self.shop_a, code="needle-shop")
        foreign_variant = self._variant(shop=self.shop_b, code="needle-foreign")
        self.client.force_authenticate(self.admin)
        base = self._shop_url(self.shop_a, "catalog/variants/")

        all_rows = self.client.get(base).data["results"]
        ids = {row["id"] for row in all_rows}
        self.assertIn(str(self.default_variant.pk), ids)
        self.assertIn(str(shop_variant.pk), ids)
        self.assertNotIn(str(foreign_variant.pk), ids)
        self.assertTrue(
            next(row for row in all_rows if row["id"] == str(self.default_variant.pk))[
                "is_global"
            ]
        )
        self.assertFalse(
            next(row for row in all_rows if row["id"] == str(shop_variant.pk))[
                "is_global"
            ]
        )

        global_rows = self.client.get(base + "?source=global").data["results"]
        self.assertTrue(all(row["is_global"] for row in global_rows))
        localized = self.client.get(base + "?locale=bn").data["results"]
        localized_default = next(
            row for row in localized if row["id"] == str(self.default_variant.pk)
        )
        self.assertEqual(localized_default["name"], "Standard Shirt")
        shop_rows = self.client.get(base + "?source=shop").data["results"]
        self.assertEqual({row["id"] for row in shop_rows}, {str(shop_variant.pk)})
        found = self.client.get(base + "?search=NEEDLE&family=" + str(self.family.pk))
        self.assertEqual(
            {row["id"] for row in found.data["results"]}, {str(shop_variant.pk)}
        )

        archived = self._variant(shop=self.shop_a, code="archived-needle")
        archived.is_active = False
        archived.save(update_fields=("is_active",))
        archived_rows = self.client.get(base + "?status=ARCHIVED").data["results"]
        self.assertEqual({row["id"] for row in archived_rows}, {str(archived.pk)})
        self.assertEqual(
            self.client.get(base + "?status=ACTIVE").data["count"], len(all_rows)
        )

    def test_shop_create_staff_write_viewer_denial_and_detail_edit_immutability(self):
        base = self._shop_url(self.shop_a, "catalog/variants/")
        self.client.force_authenticate(self.staff)
        created = self.client.post(base, self._create_payload(), format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        variant_id = created.data["id"]
        self.assertFalse(created.data["is_global"])
        self.assertEqual(len(created.data["translations"]), 2)

        detail_url = base + f"{variant_id}/"
        updated = self.client.patch(
            detail_url,
            {
                "translations": [
                    {"locale": "en", "name": "Corrected", "description": ""}
                ]
            },
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["name"], "Corrected")
        self.assertEqual(updated.data["code"], "new-variant")
        self.assertEqual(len(updated.data["translations"]), 1)

        immutable = self.client.patch(
            detail_url,
            {"code": "changed", "translations": [{"locale": "en", "name": "x"}]},
            format="json",
        )
        self.assertEqual(immutable.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.force_authenticate(self.viewer)
        denied = self.client.post(
            base, self._create_payload("viewer-variant"), format="json"
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            self.client.patch(
                detail_url,
                {"translations": [{"locale": "en", "name": "x"}]},
                format="json",
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_shop_variant_lifecycle_global_read_only_and_foreign_non_disclosure(self):
        own = self._variant(shop=self.shop_a, code="own-lifecycle")
        foreign = self._variant(shop=self.shop_b, code="foreign-lifecycle")
        base = self._shop_url(self.shop_a, "catalog/variants/")
        self.client.force_authenticate(self.admin)

        detail = self.client.get(base + f"{self.default_variant.pk}/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        forbidden_global = self.client.patch(
            base + f"{self.default_variant.pk}/",
            {"translations": [{"locale": "en", "name": "Changed"}]},
            format="json",
        )
        self.assertEqual(forbidden_global.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(base + f"{foreign.pk}/").status_code, 404)

        archived = self.client.post(base + f"{own.pk}/archive/")
        self.assertEqual(archived.status_code, status.HTTP_200_OK)
        self.assertFalse(archived.data["is_active"])
        self.assertEqual(
            self.client.get(base + f"{own.pk}/").status_code, status.HTTP_200_OK
        )
        self.assertNotIn(
            str(own.pk),
            {row["id"] for row in self.client.get(base).data["results"]},
        )
        self.assertIn(
            str(own.pk),
            {
                row["id"]
                for row in self.client.get(base + "?status=ARCHIVED").data["results"]
            },
        )
        reactivated = self.client.post(base + f"{own.pk}/reactivate/")
        self.assertEqual(reactivated.status_code, status.HTTP_200_OK)
        self.assertTrue(reactivated.data["is_active"])

    def test_global_variant_create_edit_archive_reactivate_and_default_lifecycle(self):
        self.client.force_authenticate(self.main)
        base = self._global_url()
        created = self.client.post(
            base, self._create_payload("global-unique"), format="json"
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        variant_id = created.data["id"]
        self.assertTrue(created.data["is_global"])
        self.assertFalse(created.data["is_default"])

        detail_url = base + f"{variant_id}/"
        edited = self.client.patch(
            detail_url,
            {"translations": [{"locale": "en", "name": "Global Corrected"}]},
            format="json",
        )
        self.assertEqual(edited.status_code, status.HTTP_200_OK)
        self.assertEqual(edited.data["name"], "Global Corrected")

        selected = self.client.post(detail_url + "set-default/")
        self.assertEqual(selected.status_code, status.HTTP_200_OK)
        self.assertTrue(selected.data["is_default"])
        self.default_variant.refresh_from_db()
        self.assertFalse(self.default_variant.is_default)

        archived = self.client.post(detail_url + "archive/")
        self.assertEqual(archived.status_code, status.HTTP_200_OK)
        self.assertFalse(archived.data["is_active"])
        self.assertFalse(archived.data["is_default"])
        self.assertEqual(
            self.client.post(detail_url + "set-default/").status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertNotIn(
            variant_id,
            {row["id"] for row in self.client.get(base).data["results"]},
        )
        self.assertIn(
            variant_id,
            {
                row["id"]
                for row in self.client.get(base + "?status=ARCHIVED").data["results"]
            },
        )
        reactivated = self.client.post(detail_url + "reactivate/")
        self.assertEqual(reactivated.status_code, status.HTTP_200_OK)
        self.assertTrue(reactivated.data["is_active"])
        self.assertFalse(reactivated.data["is_default"])

        self.client.post(f"/api/v1/catalog/families/{self.family.pk}/archive/")
        self.assertEqual(
            self.client.post(detail_url + "set-default/").status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            self.client.post(detail_url + "reactivate/").status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_global_variant_management_search_family_status_and_shop_default_denial(
        self,
    ):
        variant = self._variant(code="global-search-target")
        self.client.force_authenticate(self.main)
        base = self._global_url()

        active = self.client.get(base + f"?family={self.family.pk}&search=TARGET")
        self.assertEqual(active.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {row["id"] for row in active.data["results"]}, {str(variant.pk)}
        )
        self.assertEqual(active.data["count"], 1)
        self.assertEqual(
            self.client.get(base + f"?family={self.family.pk}&status=all").status_code,
            status.HTTP_200_OK,
        )

        self.client.force_authenticate(self.admin)
        denied = self.client.post(base + f"{variant.pk}/set-default/")
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.main)
        shop_variant = self._variant(shop=self.shop_a, code="shop-default-forbidden")
        self.assertEqual(
            self.client.post(base + f"{shop_variant.pk}/set-default/").status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_non_main_supplier_cannot_use_global_management_writes(self):
        self.client.force_authenticate(self.admin)
        base = self._global_url()
        self.assertEqual(
            self.client.post(base, self._create_payload(), format="json").status_code,
            403,
        )

    def test_variant_filter_returns_exact_shop_designs_and_keeps_archived_history(self):
        variant = self._variant(shop=self.shop_a, code="design-filter-variant")
        design = Design.objects.create(
            tenant=self.shop_a, family=self.family, variant=variant
        )
        other_design = Design.objects.create(
            tenant=self.shop_a, family=self.family, variant=self.default_variant
        )
        self.client.force_authenticate(self.admin)
        base = self._shop_url(self.shop_a, "designs/")
        response = self.client.get(
            base + f"?variant={variant.pk}&family={self.family.pk}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {row["id"] for row in response.data["results"]}, {str(design.pk)}
        )

        archived = self.client.post(
            self._shop_url(self.shop_a, f"catalog/variants/{variant.pk}/archive/")
        )
        self.assertEqual(archived.status_code, status.HTTP_200_OK)
        history = self.client.get(base + f"?variant={variant.pk}")
        self.assertEqual(
            {row["id"] for row in history.data["results"]}, {str(design.pk)}
        )
        self.assertNotEqual(design.pk, other_design.pk)

        rejected_new_design = self.client.post(
            self._shop_url(self.shop_a, "designs/"),
            {
                "family_id": str(self.family.pk),
                "variant_id": str(variant.pk),
                "name": "Should be rejected",
            },
            format="json",
        )
        self.assertEqual(rejected_new_design.status_code, status.HTTP_404_NOT_FOUND)
