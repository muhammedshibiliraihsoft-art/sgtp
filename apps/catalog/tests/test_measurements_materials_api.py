from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from pypdf import PdfReader

from apps.accounts.models import User
from apps.catalog.measurement_models import (
    Material,
    MeasurementDefinition,
    MeasurementProfile,
    MeasurementSet,
    MeasurementValue,
)
from apps.catalog.models import DesignVersion, GarmentVariant
from apps.catalog.measurement_pdf import build_measurement_worksheet_pdf
from apps.clients.models import Client, RelatedPerson
from apps.tenants.models import (
    MembershipWorkFunction,
    ShopRole,
    Supplier,
    Tenant,
    TenantMember,
)


class MeasurementMaterialApiTests(APITestCase):
    def setUp(self):
        self.supplier = Supplier.objects.get(singleton_lock=True)
        self.shop_a = self.make_shop("Measurement Shop A", "measurement-shop-a")
        self.shop_b = self.make_shop("Measurement Shop B", "measurement-shop-b")
        self.admin = self.make_member("measure-admin-a", self.shop_a, ShopRole.ADMIN)
        self.staff = self.make_member("measure-staff-a", self.shop_a, ShopRole.STAFF)
        self.assigned_staff = self.make_member(
            "measure-assigned-a", self.shop_a, ShopRole.STAFF
        )
        self.viewer = self.make_member("measure-viewer-a", self.shop_a, ShopRole.VIEWER)
        self.other_admin = self.make_member(
            "measure-admin-b", self.shop_b, ShopRole.ADMIN
        )
        MembershipWorkFunction.objects.create(
            membership=self.assigned_staff.tenant_memberships.get(tenant=self.shop_a),
            function_code="MEASUREMENT",
        )
        self.main = User.objects.create_superuser(
            email="measure-main@example.test",
            password="Safe-Test-Password-293!",
            first_name="Measure Main",
            phone="+96550002200",
        )
        self.client_a = Client.objects.create(tenant=self.shop_a, name="Shop A Client")
        self.client_b = Client.objects.create(tenant=self.shop_b, name="Shop B Client")
        self.related = RelatedPerson.objects.create(
            tenant=self.shop_a,
            primary_client=self.client_a,
            name="Shop A Related Person",
        )
        self.family = self.catalog_family("mens-shirt")
        self.variant = self.family.variants.get(tenant__isnull=True, is_default=True)
        self.chest = MeasurementDefinition.objects.get(
            tenant__isnull=True, code="chest", is_active=True
        )

    def make_shop(self, name, slug):
        return Tenant.objects.create(
            supplier=self.supplier, name=name, slug=slug, max_users=20
        )

    def make_member(self, name, shop, role):
        user = User.objects.create_user(
            email=f"{name}@example.test",
            password="Safe-Test-Password-293!",
            first_name=name,
            owning_shop=shop,
        )
        TenantMember.objects.create(tenant=shop, user=user, role=role)
        return user

    @staticmethod
    def catalog_family(code):
        from apps.catalog.models import GarmentFamily

        return GarmentFamily.objects.get(code=code)

    def client_profiles_url(self, *, shop=None, client=None):
        return (
            f"/api/v1/shops/{(shop or self.shop_a).pk}/clients/"
            f"{(client or self.client_a).pk}/measurement-profiles/"
        )

    def related_profiles_url(self, *, shop=None, client=None, related=None):
        related_id = getattr(related or self.related, "pk", related or self.related.pk)
        return (
            f"/api/v1/shops/{(shop or self.shop_a).pk}/clients/"
            f"{(client or self.client_a).pk}/related-persons/"
            f"{related_id}/measurement-profiles/"
        )

    def definitions_url(self, shop=None):
        return f"/api/v1/shops/{(shop or self.shop_a).pk}/measurement-definitions/"

    def materials_url(self, shop=None):
        return f"/api/v1/shops/{(shop or self.shop_a).pk}/materials/"

    def create_profile(self, *, person="client", user=None):
        self.client.force_authenticate(user or self.admin)
        response = self.client.post(
            (
                self.client_profiles_url()
                if person == "client"
                else self.related_profiles_url()
            ),
            {"family_id": str(self.family.pk), "variant_id": str(self.variant.pk)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return response.data

    def create_set(
        self,
        profile,
        *,
        user=None,
        unit="CM",
        value="95.2500",
        shop=None,
        client=None,
    ):
        self.client.force_authenticate(user or self.admin)
        base_url = (
            self.related_profiles_url(
                shop=shop, client=client, related=profile.get("related_person")
            )
            if profile.get("related_person")
            else self.client_profiles_url(shop=shop, client=client)
        )
        response = self.client.post(
            f"{base_url}{profile['id']}/sets/",
            {
                "values": [
                    {
                        "definition_id": str(self.chest.pk),
                        "value": value,
                        "unit": unit,
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return response.data

    def test_measurement_snapshot_can_reference_exact_published_design_version(self):
        profile = self.create_profile()
        self.client.force_authenticate(self.admin)
        design = self.client.post(
            f"/api/v1/shops/{self.shop_a.pk}/designs/",
            {
                "family_id": str(self.family.pk),
                "variant_id": str(self.variant.pk),
                "name": "Measurement-linked Shirt",
            },
            format="json",
        )
        self.assertEqual(design.status_code, status.HTTP_201_CREATED, design.data)
        version_id = design.data["latest_version"]["id"]
        published = self.client.post(
            f"/api/v1/shops/{self.shop_a.pk}/design-versions/{version_id}/publish/",
            {},
            format="json",
        )
        self.assertEqual(published.status_code, status.HTTP_200_OK, published.data)
        self.assertEqual(
            DesignVersion.objects.get(pk=version_id).status,
            DesignVersion.Status.PUBLISHED,
        )

        response = self.client.post(
            f"{self.client_profiles_url()}{profile['id']}/sets/",
            {
                "design_version_id": version_id,
                "values": [
                    {
                        "definition_id": str(self.chest.pk),
                        "value": "42.0000",
                        "unit": "INCH",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(str(response.data["design_version"]), version_id)

        copied = self.client.post(
            f"{self.client_profiles_url()}{profile['id']}/sets/{response.data['id']}/copy/",
            {},
            format="json",
        )
        self.assertEqual(copied.status_code, status.HTTP_201_CREATED, copied.data)
        self.assertEqual(str(copied.data["design_version"]), version_id)

    def worksheet_url(self, profile, *, shop=None, client=None, related=False):
        if related:
            return (
                f"{self.related_profiles_url(shop=shop, client=client)}"
                f"{profile['id']}/worksheet.pdf"
            )
        return f"{self.client_profiles_url(shop=shop, client=client)}{profile['id']}/worksheet.pdf"

    def test_each_seeded_family_has_approved_family_level_measurements(self):
        expected = {
            "mens-shirt": [
                "full-length",
                "shoulder-width",
                "chest",
                "waist",
                "sleeve-length",
                "neck",
                "hip-seat",
                "bicep",
                "armhole",
                "cuff-wrist",
            ],
            "kuwaiti-dishdasha": [
                "full-length",
                "shoulder",
                "chest",
                "sleeve-length",
                "neck",
                "waist",
                "hip-seat",
                "upper-arm-bicep",
                "cuff-sleeve-opening",
                "armhole",
                "shoulder-slope-posture",
                "placket-length",
                "side-slit-height",
            ],
            "abaya": [
                "full-length",
                "shoulder-width",
                "bust-chest",
                "waist",
                "hip-seat",
                "sleeve-length",
                "upper-arm-bicep",
                "armhole",
                "sleeve-opening",
                "neck-opening",
            ],
            "darraa-long-dress": [
                "full-length",
                "shoulder-width",
                "bust-chest",
                "waist",
                "hip-seat",
                "sleeve-length",
                "upper-arm-bicep",
                "armhole",
                "sleeve-opening",
                "neck-opening",
                "hem-width",
            ],
        }
        from apps.catalog.measurement_models import MeasurementDefinitionMapping
        from apps.catalog.models import GarmentFamily, GarmentVariant

        self.client.force_authenticate(self.admin)
        for family_code, codes in expected.items():
            family = GarmentFamily.objects.get(code=family_code)
            actual = list(
                MeasurementDefinitionMapping.objects.filter(
                    family=family, definition__tenant__isnull=True, deleted__isnull=True
                )
                .order_by("sort_order")
                .values_list("definition__code", flat=True)
            )
            self.assertEqual(actual, codes)
            default_variant = GarmentVariant.objects.get(
                family=family,
                tenant__isnull=True,
                is_default=True,
                is_active=True,
            )
            response = self.client.get(
                self.definitions_url()
                + f"?family_id={family.pk}&variant_id={default_variant.pk}"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
            self.assertEqual(
                [row["code"] for row in response.data["results"]],
                codes,
            )

    def test_shop_can_add_a_measurement_to_the_garment_family_for_all_variants(self):
        from apps.catalog.models import GarmentVariant

        alternate_variant = GarmentVariant.objects.create(
            family=self.family,
            code="alternate-measurement-fit",
            created_by=self.main,
            updated_by=self.main,
        )
        self.client.force_authenticate(self.admin)

        created = self.client.post(
            self.definitions_url(),
            {
                "code": "variant-collar-drop",
                "group_code": "supplemental",
                "sort_order": 10,
                "translations": [
                    {"locale": "en", "name": "Variant Collar Drop"}
                ],
                "mappings": [
                    {
                        "family_id": str(self.family.pk),
                        "variant_id": None,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        selected = self.client.get(
            self.definitions_url()
            + f"?family_id={self.family.pk}&variant_id={self.variant.pk}"
        )
        alternate = self.client.get(
            self.definitions_url()
            + f"?family_id={self.family.pk}&variant_id={alternate_variant.pk}"
        )
        self.assertEqual(selected.status_code, status.HTTP_200_OK, selected.data)
        self.assertEqual(alternate.status_code, status.HTTP_200_OK, alternate.data)
        self.assertIn(
            "variant-collar-drop",
            [row["code"] for row in selected.data["results"]],
        )
        self.assertIn(
            "variant-collar-drop",
            [row["code"] for row in alternate.data["results"]],
        )

    def test_family_filter_returns_each_definition_once(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.definitions_url() + f"?family_id={self.family.pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        definition_ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(len(definition_ids), len(set(definition_ids)))
        self.assertEqual(sum(item["id"] == str(self.chest.pk) for item in response.data["results"]), 1)

    def test_materialized_shop_family_inherits_family_measurements(self):
        from apps.catalog.measurement_models import MeasurementDefinitionMapping
        from apps.catalog.models import GarmentFamily
        from apps.catalog.services import initialize_shop_default_catalog
        initialize_shop_default_catalog(shop=self.shop_a, actor=self.admin, family_ids=[self.family.pk])
        local_family = GarmentFamily.objects.get(tenant=self.shop_a, template_source=self.family)
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.definitions_url() + f"?family_id={local_family.pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        codes = [row["code"] for row in response.data["results"]]
        self.assertEqual(len(codes), 10)
        self.assertEqual(codes.count("chest"), 1)
        self.assertEqual(MeasurementDefinitionMapping.objects.filter(family=local_family).count(), 0)
        profile_response = self.client.post(self.client_profiles_url(), {"family_id": str(local_family.pk)}, format="json")
        self.assertEqual(profile_response.status_code, status.HTTP_201_CREATED, profile_response.data)
        self.assertIsNone(profile_response.data["variant"])

    def test_materialized_family_defaults_survive_shop_variant_and_custom_addition(
        self,
    ):
        from apps.catalog.measurement_models import MeasurementDefinitionMapping
        from apps.catalog.models import GarmentFamily, GarmentVariant
        from apps.catalog.services import initialize_shop_default_catalog

        initialize_shop_default_catalog(
            shop=self.shop_a, actor=self.admin, family_ids=[self.family.pk]
        )
        local_family = GarmentFamily.objects.get(
            tenant=self.shop_a, template_source=self.family
        )
        extra_variant = GarmentVariant.objects.create(
            tenant=self.shop_a,
            family=local_family,
            code="shop-fit-variant",
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.client.force_authenticate(self.admin)

        defaults_response = self.client.get(
            self.definitions_url()
            + f"?family_id={local_family.pk}&variant_id={extra_variant.pk}"
        )
        self.assertEqual(defaults_response.status_code, status.HTTP_200_OK)
        default_codes = [row["code"] for row in defaults_response.data["results"]]
        self.assertEqual(len(default_codes), 10)
        self.assertIn("chest", default_codes)

        custom = self.client.post(
            self.definitions_url(),
            {
                "code": "shop-extra-measurement",
                "group_code": "supplemental",
                "sort_order": 10,
                "translations": [{"locale": "en", "name": "Extra Measurement"}],
                "mappings": [{"family_id": str(local_family.pk), "variant_id": None}],
            },
            format="json",
        )
        self.assertEqual(custom.status_code, status.HTTP_201_CREATED, custom.data)

        after_add = self.client.get(
            self.definitions_url()
            + f"?family_id={local_family.pk}&variant_id={extra_variant.pk}"
        )
        self.assertEqual(after_add.status_code, status.HTTP_200_OK)
        codes = [row["code"] for row in after_add.data["results"]]
        self.assertEqual(len(codes), 11)
        self.assertEqual(codes.count("chest"), 1)
        self.assertIn("shop-extra-measurement", codes)
        self.assertEqual(codes[-1], "shop-extra-measurement")
        self.assertEqual(
            [row["sort_order"] for row in after_add.data["results"]], list(range(11))
        )
        self.assertEqual(
            MeasurementDefinitionMapping.objects.filter(family=local_family).count(), 1
        )

    def test_materialized_family_ignores_retired_variant_query_parameter(self):
        from apps.catalog.models import GarmentFamily
        from apps.catalog.services import initialize_shop_default_catalog
        initialize_shop_default_catalog(shop=self.shop_a, actor=self.admin, family_ids=[self.family.pk])
        local_family = GarmentFamily.objects.get(tenant=self.shop_a, template_source=self.family)
        self.client.force_authenticate(self.admin)
        plain = self.client.get(self.definitions_url() + f"?family_id={local_family.pk}")
        legacy_query = self.client.get(self.definitions_url() + f"?family_id={local_family.pk}&variant_id={self.variant.pk}")
        self.assertEqual(plain.status_code, status.HTTP_200_OK, plain.data)
        self.assertEqual(legacy_query.status_code, status.HTTP_200_OK, legacy_query.data)
        self.assertEqual(plain.data["results"], legacy_query.data["results"])

    def test_materialized_defaults_resolve_for_other_family_without_cross_shop_custom_fields(
        self,
    ):
        from apps.catalog.measurement_models import (
            MeasurementDefinition,
            MeasurementDefinitionMapping,
            MeasurementDefinitionTranslation,
        )
        from apps.catalog.models import GarmentFamily
        from apps.catalog.services import initialize_shop_default_catalog

        dishdasha = GarmentFamily.objects.get(code="kuwaiti-dishdasha")
        initialize_shop_default_catalog(
            shop=self.shop_a, actor=self.admin, family_ids=[dishdasha.pk]
        )
        initialize_shop_default_catalog(
            shop=self.shop_b, actor=self.other_admin, family_ids=[dishdasha.pk]
        )
        local_a = GarmentFamily.objects.get(
            tenant=self.shop_a, template_source=dishdasha
        )
        local_b = GarmentFamily.objects.get(
            tenant=self.shop_b, template_source=dishdasha
        )
        self.client.force_authenticate(self.admin)

        response_a = self.client.get(
            self.definitions_url() + f"?family_id={local_a.pk}"
        )
        self.assertEqual(response_a.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [row["code"] for row in response_a.data["results"]],
            [
                "full-length",
                "shoulder",
                "chest",
                "sleeve-length",
                "neck",
                "waist",
                "hip-seat",
                "upper-arm-bicep",
                "cuff-sleeve-opening",
                "armhole",
                "shoulder-slope-posture",
                "placket-length",
                "side-slit-height",
            ],
        )

        custom = MeasurementDefinition.objects.create(
            tenant=self.shop_a, code="shop-a-only-measurement", sort_order=20
        )
        MeasurementDefinitionTranslation.objects.create(
            definition=custom, locale="en", name="Shop A Only"
        )
        MeasurementDefinitionMapping.objects.create(
            definition=custom, family=local_a, sort_order=20
        )

        self.client.force_authenticate(self.other_admin)
        response_b = self.client.get(
            self.definitions_url(self.shop_b) + f"?family_id={local_b.pk}"
        )
        self.assertEqual(response_b.status_code, status.HTTP_200_OK)
        codes_b = [row["code"] for row in response_b.data["results"]]
        self.assertEqual(len(codes_b), 13)
        self.assertNotIn("shop-a-only-measurement", codes_b)

    def test_shop_profiles_are_independent_for_client_and_related_person(self):
        client_profile = self.create_profile()
        related_profile = self.create_profile(person="related")
        self.assertEqual(str(client_profile["client"]), str(self.client_a.pk))
        self.assertIsNone(client_profile["related_person"])
        self.assertEqual(str(related_profile["related_person"]), str(self.related.pk))
        self.assertIsNone(related_profile["client"])
        self.assertEqual(self.related.primary_client_id, self.client_a.pk)
        self.assertEqual(MeasurementProfile.objects.count(), 2)

    def test_profile_database_constraint_requires_exactly_one_owner(self):
        with self.assertRaises(ValidationError):
            MeasurementProfile(
                tenant=self.shop_a,
                family=self.family,
                client=self.client_a,
                related_person=self.related,
            ).full_clean()

    def test_duplicate_profile_is_rejected_without_creating_a_second_history(self):
        self.client.force_authenticate(self.admin)
        payload = {"family_id": str(self.family.pk), "variant_id": str(self.variant.pk)}
        endpoint = self.client_profiles_url()
        self.assertEqual(
            self.client.post(endpoint, payload, format="json").status_code, 201
        )
        duplicate = self.client.post(endpoint, payload, format="json")
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client_a.measurement_profiles.count(), 1)

        other_family = self.catalog_family("kuwaiti-dishdasha")
        other_variant = other_family.variants.get(tenant__isnull=True, is_default=True)
        other_garment = self.client.post(
            endpoint,
            {
                "family_id": str(other_family.pk),
                "variant_id": str(other_variant.pk),
            },
            format="json",
        )
        self.assertEqual(other_garment.status_code, status.HTTP_201_CREATED, other_garment.data)
        self.assertEqual(self.client_a.measurement_profiles.count(), 2)

    def test_measurement_values_require_explicit_unit_and_history_is_immutable(self):
        profile = self.create_profile()
        endpoint = f"{self.client_profiles_url()}{profile['id']}/sets/"
        self.client.force_authenticate(self.admin)
        missing_unit = self.client.post(
            endpoint,
            {"values": [{"definition_id": str(self.chest.pk), "value": "36"}]},
            format="json",
        )
        self.assertEqual(missing_unit.status_code, status.HTTP_400_BAD_REQUEST)
        first = self.create_set(profile, unit="INCH", value="36.1250")
        record = MeasurementValue.objects.get(measurement_set_id=first["id"])
        self.assertEqual(str(record.value), "36.1250")
        self.assertEqual(record.unit, "INCH")
        record.value = "40"
        with self.assertRaises(ValidationError):
            record.save()
        with self.assertRaises(ValidationError):
            MeasurementValue.objects.filter(pk=record.pk).update(value="40")
        self.assertEqual(
            self.client.patch(
                f"{endpoint}{first['id']}/", {"values": []}, format="json"
            ).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_version_delete_is_recoverable_and_protects_last_active_version(self):
        profile = self.create_profile()
        first = self.create_set(profile, value="36.0000")
        second = self.create_set(profile, value="37.0000")
        endpoint = f"{self.client_profiles_url()}{profile['id']}/sets/"

        removed = self.client.delete(f"{endpoint}{first['id']}/")
        self.assertEqual(removed.status_code, status.HTTP_204_NO_CONTENT)
        first_record = MeasurementSet.all_objects.get(pk=first["id"])
        self.assertFalse(first_record.is_active)
        self.assertEqual(first_record.values.count(), 1)
        self.assertEqual(
            self.client.get(f"{endpoint}{first['id']}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        remaining = self.client.get(endpoint)
        self.assertEqual(remaining.data["count"], 1)
        self.assertEqual(remaining.data["results"][0]["id"], second["id"])

        rejected = self.client.delete(f"{endpoint}{second['id']}/")
        self.assertEqual(rejected.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(MeasurementSet.objects.get(pk=second["id"]).is_active)

        third = self.create_set(profile, value="38.0000")
        self.assertEqual(third["version"], 3)

    def test_deleted_version_cannot_be_copied_compared_or_exported(self):
        profile = self.create_profile()
        first = self.create_set(profile, value="36.0000")
        second = self.create_set(profile, value="37.0000")
        base = f"{self.client_profiles_url()}{profile['id']}"
        self.assertEqual(
            self.client.delete(f"{base}/sets/{first['id']}/").status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertEqual(
            self.client.post(f"{base}/sets/{first['id']}/copy/", {}).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.get(
                f"{base}/compare/",
                {"from_set_id": first["id"], "to_set_id": second["id"]},
            ).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.get(
                f"{base}/worksheet.pdf", {"measurement_set_id": first["id"]}
            ).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_copy_is_independent_and_comparison_never_converts_units(self):
        profile = self.create_profile()
        original = self.create_set(profile, unit="INCH", value="36.1250")
        copy_url = (
            f"{self.client_profiles_url()}{profile['id']}/sets/{original['id']}/copy/"
        )
        copied_response = self.client.post(copy_url, {}, format="json")
        self.assertEqual(copied_response.status_code, status.HTTP_201_CREATED)
        copied = copied_response.data
        self.assertEqual(str(copied["copied_from"]), original["id"])
        self.assertEqual(copied["values"][0]["value"], "36.1250")
        self.assertNotEqual(copied["values"][0]["id"], original["values"][0]["id"])
        newer = self.create_set(profile, unit="CM", value="91.7600")
        compare = self.client.get(
            f"{self.client_profiles_url()}{profile['id']}/compare/",
            {"from_set_id": original["id"], "to_set_id": newer["id"]},
        )
        self.assertEqual(compare.status_code, status.HTTP_200_OK)
        result = compare.data["results"][0]
        self.assertIsNone(result["difference"])
        self.assertTrue(result["unit_mismatch"])
        self.assertEqual(result["from_value"], "36.1250")
        self.assertEqual(result["from_unit"], "INCH")
        self.assertEqual(result["to_value"], "91.7600")
        self.assertEqual(result["to_unit"], "CM")

    def test_measurement_worksheet_defaults_to_latest_and_accepts_selected_version(
        self,
    ):
        profile = self.create_profile()
        first = self.create_set(profile, value="95.2500", unit="CM")
        second = self.create_set(profile, value="40.0000", unit="INCH")
        endpoint = self.worksheet_url(profile)

        with patch(
            "apps.catalog.measurement_views.build_measurement_worksheet_pdf",
            return_value=b"%PDF-1.4 test worksheet",
        ) as render_pdf:
            latest = self.client.get(endpoint)
            self.assertEqual(latest.status_code, status.HTTP_200_OK)
            self.assertEqual(latest["Content-Type"], "application/pdf")
            self.assertEqual(latest["Cache-Control"], "private, no-store")
            self.assertEqual(latest["X-Content-Type-Options"], "nosniff")
            self.assertEqual(render_pdf.call_args.kwargs["measurement_set"].version, 2)

            selected = self.client.get(endpoint, {"measurement_set_id": first["id"]})
            self.assertEqual(selected.status_code, status.HTTP_200_OK)
            self.assertEqual(render_pdf.call_args.kwargs["measurement_set"].version, 1)
            self.assertEqual(selected.content, b"%PDF-1.4 test worksheet")

        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(
            MeasurementProfile.objects.get(pk=profile["id"]).sets.count(), 2
        )

    def test_measurement_worksheet_returns_real_pdf_with_demo_only_bill_placeholder(
        self,
    ):
        profile = self.create_profile()
        self.create_set(profile, unit="INCH", value="36.1250")
        response = self.client.get(self.worksheet_url(profile))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF-"))
        self.assertIn("measurement-worksheet-v1.pdf", response["Content-Disposition"])
        reader = PdfReader(BytesIO(response.content))
        self.assertGreaterEqual(len(reader.pages), 1)
        for page in reader.pages:
            self.assertAlmostEqual(float(page.mediabox.width), 419.53, delta=1)
            self.assertAlmostEqual(float(page.mediabox.height), 595.28, delta=1)
        extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("Measurement / Design Worksheet", extracted)
        self.assertIn("INCH", extracted)
        self.assertIn("36.1250", extracted)
        self.assertIn("Bill / Estimate", extracted)
        self.assertIn("No invoice", extracted)

    def test_measurement_worksheet_paginates_long_measurement_tables_on_a5(self):
        class WorksheetValue:
            def __init__(self, number):
                self.label_snapshot = f"Measurement {number:03d}"
                self.value = "123.4567"
                self.unit = "CM"

            def __str__(self):
                return self.label_snapshot

        client = SimpleNamespace(name="Amina Client")
        profile = SimpleNamespace(
            client=client,
            client_id="client-id",
            related_person=None,
            family=SimpleNamespace(name="Shirt"),
            variant=SimpleNamespace(name="Standard"),
        )
        measurement_set = SimpleNamespace(
            version=1,
            values=SimpleNamespace(all=lambda: [WorksheetValue(i) for i in range(120)]),
        )

        pdf = build_measurement_worksheet_pdf(
            shop=SimpleNamespace(name="Test Shop"),
            profile=profile,
            measurement_set=measurement_set,
        )
        reader = PdfReader(BytesIO(pdf))
        self.assertGreater(len(reader.pages), 1)
        for page in reader.pages:
            self.assertAlmostEqual(float(page.mediabox.width), 419.53, delta=1)
            self.assertAlmostEqual(float(page.mediabox.height), 595.28, delta=1)
        extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("Measurement 000", extracted)
        self.assertIn("Measurement 119", extracted)

    def test_measurement_worksheet_embeds_supported_localized_name_glyphs(self):
        samples = (
            "مرحبا عميل",  # Arabic / Urdu script
            "বাংলা নাম",  # Bangla
            "മലയാളം പേര്",  # Malayalam
        )
        for name in samples:
            with self.subTest(name=ascii(name)):
                profile = SimpleNamespace(
                    client=SimpleNamespace(name=name),
                    client_id="client-id",
                    related_person=None,
                    family=SimpleNamespace(name="Shirt"),
                    variant=SimpleNamespace(name="Standard"),
                )
                measurement_set = SimpleNamespace(
                    version=1,
                    values=SimpleNamespace(all=lambda: []),
                )
                pdf = build_measurement_worksheet_pdf(
                    shop=SimpleNamespace(name="Test Shop"),
                    profile=profile,
                    measurement_set=measurement_set,
                )
                extracted = "\n".join(
                    page.extract_text() or "" for page in PdfReader(BytesIO(pdf)).pages
                )
                self.assertNotIn("\u25a0", extracted)
                self.assertTrue(any(ord(character) > 127 for character in extracted))

    def test_measurement_worksheet_scopes_person_shop_and_design_non_disclosing(self):
        profile_a = self.create_profile()
        set_a = self.create_set(profile_a)
        self.client.force_authenticate(self.other_admin)
        denied_shop = self.client.get(self.worksheet_url(profile_a))
        self.assertEqual(denied_shop.status_code, status.HTTP_404_NOT_FOUND)

        profile_b_response = self.client.post(
            self.client_profiles_url(shop=self.shop_b, client=self.client_b),
            {"family_id": str(self.family.pk), "variant_id": str(self.variant.pk)},
            format="json",
        )
        self.assertEqual(profile_b_response.status_code, status.HTTP_201_CREATED)
        set_b = self.create_set(
            profile_b_response.data,
            user=self.other_admin,
            shop=self.shop_b,
            client=self.client_b,
        )

        self.client.force_authenticate(self.admin)
        foreign_version = self.client.get(
            self.worksheet_url(profile_a), {"measurement_set_id": set_b["id"]}
        )
        self.assertEqual(foreign_version.status_code, status.HTTP_404_NOT_FOUND)

        unavailable_design = self.client.get(
            self.worksheet_url(profile_a),
            {"design_id": "00000000-0000-0000-0000-000000000001"},
        )
        self.assertEqual(unavailable_design.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            str(MeasurementSet.objects.get(pk=set_a["id"]).profile_id), profile_a["id"]
        )

    def test_related_person_measurement_worksheet_keeps_primary_client_identity(self):
        profile = self.create_profile(person="related")
        self.create_set(profile)
        response = self.client.get(self.worksheet_url(profile, related=True))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.content.startswith(b"%PDF-"))
        extracted = "\n".join(
            page.extract_text() or ""
            for page in PdfReader(BytesIO(response.content)).pages
        )
        self.assertIn("Primary Client", extracted)
        self.assertIn("Shop A Client", extracted)
        self.assertIn("Shop A Related Person", extracted)

    def test_same_unit_comparison_returns_decimal_difference(self):
        profile = self.create_profile()
        old = self.create_set(profile, unit="CM", value="90.0000")
        new = self.create_set(profile, unit="CM", value="94.2500")
        response = self.client.get(
            f"{self.client_profiles_url()}{profile['id']}/compare/",
            {"from_set_id": old["id"], "to_set_id": new["id"]},
        )
        self.assertEqual(response.data["results"][0]["difference"], "4.2500")
        self.assertFalse(response.data["results"][0]["unit_mismatch"])

    def test_staff_requires_measurement_function_and_viewer_has_no_pii_access(self):
        self.client.force_authenticate(self.staff)
        denied = self.client.get(self.definitions_url())
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.viewer)
        denied = self.client.get(self.client_profiles_url())
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.assigned_staff)
        allowed = self.client.get(self.definitions_url())
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)

    def test_main_supplier_cannot_read_client_measurements_but_configuration_remains_available(self):
        self.create_profile()
        self.client.force_authenticate(self.main)
        response = self.client.get(self.client_profiles_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        definitions = self.client.get(self.definitions_url(self.shop_a))
        self.assertEqual(definitions.status_code, status.HTTP_200_OK)

    def test_measurement_function_does_not_authorize_inactive_membership(self):
        membership = self.assigned_staff.tenant_memberships.get(tenant=self.shop_a)
        membership.is_active = False
        membership.save(update_fields=("is_active", "updated_at"))
        self.client.force_authenticate(self.assigned_staff)
        response = self.client.get(self.definitions_url())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_measurement_staff_can_create_custom_definition_but_not_archive(self):
        self.client.force_authenticate(self.assigned_staff)
        create = self.client.post(
            self.definitions_url(),
            {
                "code": "shop-sleeve-opening",
                "translations": [{"locale": "en", "name": "Sleeve Opening"}],
                "mappings": [{"family_id": str(self.family.pk)}],
            },
            format="json",
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED, create.data)
        archive = self.client.post(
            f"{self.definitions_url()}{create.data['id']}/archive/", {}, format="json"
        )
        self.assertEqual(archive.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            MeasurementDefinition.objects.filter(
                pk=create.data["id"], is_active=True
            ).exists()
        )

    def test_shop_can_attach_existing_definition_to_family(self):
        from apps.catalog.measurement_models import MeasurementDefinitionMapping
        from apps.catalog.models import GarmentFamily
        family = GarmentFamily.objects.create(tenant=self.shop_a, code="custom-garment", created_by=self.admin, updated_by=self.admin)
        self.client.force_authenticate(self.admin)
        created = self.client.post(self.definitions_url(), {"code": "custom-garment-chest", "sort_order": 3, "translations": [{"locale": "en", "name": "Chest"}], "mappings": [{"family_id": str(family.pk)}]}, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        definition_id = created.data["id"]
        mapping = self.client.post(f"{self.definitions_url()}{definition_id}/mappings/", {"family_id": str(family.pk), "sort_order": 4}, format="json")
        self.assertEqual(mapping.status_code, status.HTTP_201_CREATED, mapping.data)
        self.assertEqual(mapping.data["mappings"], [{"family_id": str(family.pk), "sort_order": 4}])
        self.assertEqual(MeasurementDefinitionMapping.objects.filter(definition_id=definition_id, family=family, deleted__isnull=True).count(), 1)

    def test_definition_mapping_obeys_measurement_scope_and_permissions(self):
        from apps.catalog.models import GarmentFamily

        family = GarmentFamily.objects.create(
            tenant=self.shop_a,
            code="mapping-permission-garment",
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.client.force_authenticate(self.admin)
        definition = self.client.post(
            self.definitions_url(),
            {
                "code": "mapping-permission-measurement",
                "translations": [{"locale": "en", "name": "Fit"}],
                "mappings": [{"family_id": str(family.pk)}],
            },
            format="json",
        )
        self.assertEqual(definition.status_code, status.HTTP_201_CREATED)
        mapping_url = f"{self.definitions_url()}{definition.data['id']}/mappings/"
        payload = {"family_id": str(family.pk)}

        self.client.force_authenticate(self.staff)
        self.assertEqual(
            self.client.post(mapping_url, payload, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.client.force_authenticate(self.viewer)
        self.assertEqual(
            self.client.post(mapping_url, payload, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.client.force_authenticate(self.assigned_staff)
        self.assertEqual(
            self.client.post(mapping_url, payload, format="json").status_code,
            status.HTTP_201_CREATED,
        )

        self.client.force_authenticate(self.other_admin)
        cross_shop = self.client.post(
            f"{self.definitions_url(self.shop_b)}{definition.data['id']}/mappings/",
            {"family_id": str(family.pk)},
            format="json",
        )
        self.assertEqual(cross_shop.status_code, status.HTTP_404_NOT_FOUND)
        global_mapping = self.client.post(
            f"{self.definitions_url(self.shop_b)}{self.chest.pk}/mappings/",
            {"family_id": str(family.pk)},
            format="json",
        )
        self.assertEqual(global_mapping.status_code, status.HTTP_404_NOT_FOUND)

    def test_archived_family_preserves_measurements_but_rejects_new_use(self):
        profile = self.create_profile()
        self.client.force_authenticate(self.main)
        archived = self.client.post(
            f"/api/v1/catalog/families/{self.family.pk}/archive/", {}, format="json"
        )
        self.assertEqual(archived.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(self.admin)
        historical_profile = self.client.get(
            f"{self.client_profiles_url()}{profile['id']}/"
        )
        self.assertEqual(historical_profile.status_code, status.HTTP_200_OK)
        new_profile = self.client.post(
            self.client_profiles_url(),
            {"family_id": str(self.family.pk), "variant_id": str(self.variant.pk)},
            format="json",
        )
        self.assertEqual(new_profile.status_code, status.HTTP_404_NOT_FOUND)

        new_definition = self.client.post(
            self.definitions_url(),
            {
                "code": "archived-family-check",
                "translations": [{"locale": "en", "name": "Archived Family"}],
                "mappings": [{"family_id": str(self.family.pk)}],
            },
            format="json",
        )
        self.assertEqual(new_definition.status_code, status.HTTP_400_BAD_REQUEST)

    def test_legacy_variant_profile_is_readable_and_new_records_remain_family_level(
        self,
    ):
        from apps.catalog.measurement_models import MeasurementProfile

        profile = MeasurementProfile.objects.create(
            tenant=self.shop_a,
            client=self.client_a,
            family=self.family,
            variant=self.variant,
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.client.force_authenticate(self.main)
        archived = self.client.post(
            f"/api/v1/catalog/variants/{self.variant.pk}/archive/",
            {},
            format="json",
        )
        self.assertEqual(archived.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        GarmentVariant.objects.filter(pk=self.variant.pk).update(
            is_active=False, is_default=False
        )
        self.client.force_authenticate(self.admin)
        historical_profile = self.client.get(
            f"{self.client_profiles_url()}{profile.pk}/"
        )
        self.assertEqual(historical_profile.status_code, status.HTTP_200_OK)
        self.assertEqual(str(historical_profile.data["variant"]), str(self.variant.pk))
        new_profile = self.client.post(
            self.client_profiles_url(),
            {"family_id": str(self.family.pk)},
            format="json",
        )
        self.assertEqual(new_profile.status_code, status.HTTP_201_CREATED, new_profile.data)
        self.assertIsNone(new_profile.data["variant"])
        new_definition = self.client.post(
            self.definitions_url(),
            {
                "code": "family-level-after-variant-archive",
                "translations": [{"locale": "en", "name": "Family Level"}],
                "mappings": [{"family_id": str(self.family.pk)}],
            },
            format="json",
        )
        self.assertEqual(new_definition.status_code, status.HTTP_201_CREATED, new_definition.data)

    def test_custom_definition_is_not_visible_or_usable_in_another_shop(self):
        self.client.force_authenticate(self.main)
        created = self.client.post(
            self.definitions_url(self.shop_b),
            {
                "code": "shop-b-only",
                "translations": [{"locale": "en", "name": "Shop B only"}],
                "mappings": [{"family_id": str(self.family.pk)}],
            },
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)

        foreign_detail = self.client.get(
            f"{self.definitions_url(self.shop_a)}{created.data['id']}/"
        )
        self.assertEqual(foreign_detail.status_code, status.HTTP_404_NOT_FOUND)

        profile = self.create_profile()
        rejected_set = self.client.post(
            f"{self.client_profiles_url()}{profile['id']}/sets/",
            {
                "values": [
                    {
                        "definition_id": created.data["id"],
                        "value": "12",
                        "unit": "CM",
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(rejected_set.status_code, status.HTTP_404_NOT_FOUND)

    def test_definition_label_change_does_not_rewrite_history(self):
        self.client.force_authenticate(self.admin)
        created = self.client.post(
            self.definitions_url(),
            {
                "code": "custom-chest-width",
                "translations": [
                    {"locale": "en", "name": "Old Label"},
                    {"locale": "bn", "name": "Bangla Label"},
                ],
                "mappings": [{"family_id": str(self.family.pk)}],
            },
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        profile = self.create_profile()
        self.client.force_authenticate(self.admin)
        saved = self.client.post(
            f"{self.client_profiles_url()}{profile['id']}/sets/",
            {
                "values": [
                    {"definition_id": created.data["id"], "value": "5", "unit": "CM"}
                ]
            },
            format="json",
        )
        self.assertEqual(saved.status_code, status.HTTP_201_CREATED, saved.data)
        patch = self.client.patch(
            f"{self.definitions_url()}{created.data['id']}/",
            {"translations": [{"locale": "en", "name": "New Label"}]},
            format="json",
        )
        self.assertEqual(patch.status_code, status.HTTP_200_OK, patch.data)
        history = self.client.get(
            f"{self.client_profiles_url()}{profile['id']}/sets/{saved.data['id']}/?locale=bn"
        )
        self.assertEqual(history.data["values"][0]["label"], "Bangla Label")

    def test_system_definitions_cannot_be_mutated_and_archive_preserves_history(self):
        self.client.force_authenticate(self.admin)
        forbidden = self.client.patch(
            f"{self.definitions_url()}{self.chest.pk}/",
            {"group_code": "changed"},
            format="json",
        )
        self.assertEqual(forbidden.status_code, status.HTTP_404_NOT_FOUND)
        created = self.client.post(
            self.definitions_url(),
            {
                "code": "custom-neck-width",
                "translations": [{"locale": "en", "name": "Neck Width"}],
                "mappings": [{"family_id": str(self.family.pk)}],
            },
            format="json",
        )
        profile = self.create_profile()
        self.client.force_authenticate(self.admin)
        saved = self.client.post(
            f"{self.client_profiles_url()}{profile['id']}/sets/",
            {
                "values": [
                    {"definition_id": created.data["id"], "value": "5", "unit": "CM"}
                ]
            },
            format="json",
        )
        archived = self.client.post(
            f"{self.definitions_url()}{created.data['id']}/archive/", {}, format="json"
        )
        self.assertEqual(archived.status_code, status.HTTP_200_OK)
        history = self.client.get(
            f"{self.client_profiles_url()}{profile['id']}/sets/{saved.data['id']}/"
        )
        self.assertEqual(history.status_code, status.HTTP_200_OK)
        self.assertEqual(history.data["values"][0]["label_snapshot"], "Neck Width")

    def test_related_person_history_is_nested_and_shop_isolated(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            self.related_profiles_url(),
            {"family_id": str(self.family.pk)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(str(response.data["related_person"]), str(self.related.pk))
        self.assertEqual(response.data["client"], None)
        foreign_route = self.client.get(
            self.client_profiles_url(shop=self.shop_b, client=self.client_b)
        )
        self.assertEqual(foreign_route.status_code, status.HTTP_404_NOT_FOUND)

    def test_material_role_matrix_archive_and_shop_non_disclosure(self):
        self.client.force_authenticate(self.admin)
        created = self.client.post(
            self.materials_url(),
            {"name": "Cotton", "code": "cotton", "description": "Reference only"},
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        self.client.force_authenticate(self.staff)
        self.assertEqual(
            self.client.get(self.materials_url()).status_code, status.HTTP_200_OK
        )
        self.assertEqual(
            self.client.post(
                self.materials_url(), {"name": "Silk"}, format="json"
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.client.force_authenticate(self.viewer)
        self.assertEqual(
            self.client.get(self.materials_url()).status_code, status.HTTP_200_OK
        )
        self.client.force_authenticate(self.other_admin)
        self.assertEqual(
            self.client.get(
                f"{self.materials_url(self.shop_b)}{created.data['id']}/"
            ).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.client.force_authenticate(self.admin)
        archived = self.client.post(
            f"{self.materials_url()}{created.data['id']}/archive/", {}, format="json"
        )
        self.assertEqual(archived.status_code, status.HTTP_200_OK)
        material = Material.objects.get(pk=created.data["id"])
        self.assertEqual(material.status, Material.Status.ARCHIVED)
        with self.assertRaises(ValidationError):
            material.delete()

    def test_main_supplier_must_select_shop_context_and_can_manage_materials(self):
        self.client.force_authenticate(self.main)
        self.assertEqual(
            self.client.get("/api/v1/materials/").status_code, status.HTTP_404_NOT_FOUND
        )
        created = self.client.post(
            self.materials_url(self.shop_b), {"name": "Linen"}, format="json"
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
