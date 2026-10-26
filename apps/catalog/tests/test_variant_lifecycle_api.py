from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.catalog.models import Design, GarmentFamily, GarmentVariant, GarmentVariantTranslation
from apps.tenants.models import Supplier, Tenant, TenantMember


class VariantRetirementApiTests(APITestCase):
    def setUp(self):
        supplier = Supplier.objects.get(singleton_lock=True)
        self.shop = Tenant.objects.create(
            supplier=supplier,
            name="Variant Retirement Shop",
            slug="variant-retirement-shop",
            max_users=20,
        )
        self.admin = self._member("variant-retirement@example.test", self.shop)
        self.main = User.objects.create_superuser(
            email="variant-retirement-main@example.test",
            password="Safe-Test-Password-293!",
            first_name="Variant Main",
            phone="+96550001900",
        )
        self.family = GarmentFamily.objects.get(code="mens-shirt")
        self.global_variant = GarmentVariant.objects.get(
            tenant__isnull=True, family=self.family, is_default=True
        )
        self.shop_variant = self._variant(shop=self.shop, code="legacy-shop-shirt")
        self.initial_variant_count = GarmentVariant.objects.count()

    @staticmethod
    def _member(email, shop):
        user = User.objects.create_user(
            email=email,
            password="Safe-Test-Password-293!",
            first_name="Variant User",
            owning_shop=shop,
        )
        TenantMember.objects.create(tenant=shop, user=user, role="ADMIN")
        return user

    def _variant(self, *, shop=None, code):
        variant = GarmentVariant.objects.create(
            tenant=shop, family=self.family, code=code
        )
        GarmentVariantTranslation.objects.create(
            variant=variant, locale="en", name=f"Name {code}", description="Legacy"
        )
        return variant

    def test_legacy_variant_and_design_references_remain_readable(self):
        self.client.force_authenticate(self.admin)
        shop_variants = self.client.get(
            f"/api/v1/shops/{self.shop.pk}/catalog/variants/"
        )
        self.assertEqual(shop_variants.status_code, status.HTTP_200_OK)
        self.assertIn(
            str(self.shop_variant.pk),
            {row["id"] for row in shop_variants.data["results"]},
        )
        detail = self.client.get(
            f"/api/v1/shops/{self.shop.pk}/catalog/variants/{self.shop_variant.pk}/"
        )
        self.assertEqual(detail.status_code, status.HTTP_200_OK)

        legacy_design = Design.objects.create(
            tenant=self.shop, family=self.family, variant=self.shop_variant
        )
        design_response = self.client.get(
            f"/api/v1/shops/{self.shop.pk}/designs/{legacy_design.pk}/"
        )
        self.assertEqual(design_response.status_code, status.HTTP_200_OK)
        self.assertEqual(design_response.data["variant"], self.shop_variant.pk)

        self.client.force_authenticate(self.main)
        global_variants = self.client.get("/api/v1/catalog/variants/")
        self.assertEqual(global_variants.status_code, status.HTTP_200_OK)
        self.assertIn(
            str(self.global_variant.pk),
            {row["id"] for row in global_variants.data["results"]},
        )
        self.assertEqual(
            self.client.get(
                f"/api/v1/catalog/variants/{self.global_variant.pk}/"
            ).status_code,
            status.HTTP_200_OK,
        )

    def test_variant_mutations_are_retired_without_changing_legacy_rows(self):
        self.client.force_authenticate(self.admin)
        shop_base = f"/api/v1/shops/{self.shop.pk}/catalog/variants/"
        self.assertEqual(
            self.client.post(shop_base, {"family_id": str(self.family.pk)}).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client.patch(
                f"{shop_base}{self.shop_variant.pk}/", {"translations": []}
            ).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        for action in ("archive", "reactivate"):
            self.assertEqual(
                self.client.post(f"{shop_base}{self.shop_variant.pk}/{action}/").status_code,
                status.HTTP_405_METHOD_NOT_ALLOWED,
            )

        self.client.force_authenticate(self.main)
        global_base = "/api/v1/catalog/variants/"
        self.assertEqual(
            self.client.post(global_base, {"family_id": str(self.family.pk)}).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client.patch(
                f"{global_base}{self.global_variant.pk}/", {"translations": []}
            ).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        for action in ("archive", "reactivate", "set-default"):
            self.assertEqual(
                self.client.post(f"{global_base}{self.global_variant.pk}/{action}/").status_code,
                status.HTTP_405_METHOD_NOT_ALLOWED,
            )

        self.global_variant.refresh_from_db()
        self.shop_variant.refresh_from_db()
        self.assertTrue(self.global_variant.is_active)
        self.assertTrue(self.global_variant.is_default)
        self.assertTrue(self.shop_variant.is_active)
        self.assertEqual(GarmentVariant.objects.count(), self.initial_variant_count)
