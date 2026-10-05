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

    def worksheet_url(self, profile, *, shop=None, client=None, related=False):
        if related:
            return (
                f"{self.related_profiles_url(shop=shop, client=client)}"
                f"{profile['id']}/worksheet.pdf"
            )
        return f"{self.client_profiles_url(shop=shop, client=client)}{profile['id']}/worksheet.pdf"

    def test_exact_approved_system_templates_and_no_guessed_abaya_darraa_sets(self):
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
        }
        from apps.catalog.measurement_models import MeasurementDefinitionMapping
        from apps.catalog.models import GarmentFamily

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
        self.assertFalse(
            MeasurementDefinitionMapping.objects.filter(
                family__code__in=("abaya", "darraa-long-dress"),
                definition__tenant__isnull=True,
            ).exists()
        )

    def test_variant_filter_returns_definition_once_for_family_and_variant_mappings(
        self,
    ):
        from apps.catalog.measurement_models import MeasurementDefinitionMapping

        MeasurementDefinitionMapping.objects.get_or_create(
            definition=self.chest,
            family=self.family,
            variant=self.variant,
            defaults={"sort_order": 99},
        )
        self.client.force_authenticate(self.admin)

        response = self.client.get(
            self.definitions_url()
            + f"?family_id={self.family.pk}&variant_id={self.variant.pk}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        definition_ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(len(definition_ids), len(set(definition_ids)))
        self.assertEqual(
            sum(item["id"] == str(self.chest.pk) for item in response.data["results"]),
            1,
        )

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
        extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("Measurement / Design Worksheet", extracted)
        self.assertIn("INCH", extracted)
        self.assertIn("36.1250", extracted)
        self.assertIn("Bill / Estimate", extracted)
        self.assertIn("No invoice", extracted)

    def test_measurement_worksheet_paginates_long_measurement_tables_on_a4(self):
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
        self.assertAlmostEqual(float(reader.pages[0].mediabox.width), 595.28, delta=1)
        self.assertAlmostEqual(float(reader.pages[0].mediabox.height), 841.89, delta=1)
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

    def test_archived_variant_preserves_measurement_history_but_rejects_new_records(
        self,
    ):
        profile = self.create_profile()
        self.client.force_authenticate(self.main)
        archived = self.client.post(
            f"/api/v1/catalog/variants/{self.variant.pk}/archive/", {}, format="json"
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
        self.assertEqual(new_profile.status_code, status.HTTP_400_BAD_REQUEST)

        new_definition = self.client.post(
            self.definitions_url(),
            {
                "code": "archived-variant-check",
                "translations": [{"locale": "en", "name": "Archived Variant"}],
                "mappings": [
                    {
                        "family_id": str(self.family.pk),
                        "variant_id": str(self.variant.pk),
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(new_definition.status_code, status.HTTP_400_BAD_REQUEST)

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
