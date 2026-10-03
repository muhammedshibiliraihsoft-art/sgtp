from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.catalog.models import (
    DesignVersion,
    FamilyOptionGroup,
    GarmentFamily,
    GarmentVariant,
)
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember


class MensShirtDefaultCatalogTests(APITestCase):
    def test_mens_shirt_has_scoped_style_sections_and_published_presets(self):
        family = GarmentFamily.objects.get(code="mens-shirt")
        variant = GarmentVariant.objects.get(
            family=family,
            tenant__isnull=True,
            code="standard-shirt",
        )

        group_codes = set(
            FamilyOptionGroup.objects.filter(family=family).values_list(
                "option_group__code", flat=True
            )
        )
        self.assertEqual(
            group_codes,
            {
                "sleeve",
                "collar",
                "cuff",
                "pocket",
                "placket",
                "embroidery",
                "color",
            },
        )

        expected_names = (
            "Classic Formal Shirt",
            "Smart Casual Shirt",
            "Modern Evening Shirt",
        )
        for name in expected_names:
            version = DesignVersion.objects.get(
                design__tenant__isnull=True,
                design__family=family,
                design__variant=variant,
                status=DesignVersion.Status.PUBLISHED,
                translations__locale="en",
                translations__name=name,
            )
            self.assertEqual(version.selections.count(), 7)

    def test_same_shop_measurement_user_can_load_published_shirt_presets(self):
        supplier = Supplier.objects.get(singleton_lock=True)
        shop = Tenant.objects.create(
            supplier=supplier,
            name="Shirt Preset Shop",
            slug="shirt-preset-shop",
            max_users=5,
        )
        user = User.objects.create_user(
            email="shirt-preset@example.test",
            password="Safe-Test-Password-293!",
            first_name="Shirt Preset",
            owning_shop=shop,
        )
        membership = TenantMember.objects.create(
            tenant=shop, user=user, role=ShopRole.STAFF
        )
        from apps.tenants.models import MembershipWorkFunction

        MembershipWorkFunction.objects.create(
            membership=membership, function_code="MEASUREMENT"
        )
        family = GarmentFamily.objects.get(code="mens-shirt")
        variant = GarmentVariant.objects.get(
            family=family, tenant__isnull=True, code="standard-shirt"
        )

        self.client.force_authenticate(user)
        response = self.client.get(
            "/api/v1/catalog/design-templates/",
            {"family": str(family.pk), "variant": str(variant.pk)},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {row["name"] for row in response.data["results"]},
            {"Classic Formal Shirt", "Smart Casual Shirt", "Modern Evening Shirt"},
        )
        self.assertTrue(
            all(
                len(row["latest_version"]["selections"]) == 7
                for row in response.data["results"]
            )
        )
