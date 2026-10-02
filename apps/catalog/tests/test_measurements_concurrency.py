from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import close_old_connections, connection
from django.test import TransactionTestCase, skipUnlessDBFeature
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.accounts.models import User
from apps.catalog.measurement_models import (
    MeasurementDefinition,
    MeasurementDefinitionMapping,
    MeasurementDefinitionTranslation,
)
from apps.catalog.measurement_services import (
    copy_measurement_set,
    create_measurement_definition,
    create_measurement_profile,
    create_measurement_set,
)
from apps.catalog.models import GarmentFamily, GarmentVariant
from apps.clients.models import Client
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember


@skipUnlessDBFeature("has_select_for_update")
class MeasurementConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.assertEqual(connection.vendor, "postgresql")
        supplier, _created = Supplier.objects.get_or_create(singleton_lock=True)
        self.shop = Tenant.objects.create(
            supplier=supplier,
            name="Measurement Race Shop",
            slug="measurement-race-shop",
            max_users=10,
        )
        self.actor = User.objects.create_user(
            email="measurement-race-admin@example.test",
            password="safe-test-password",
            first_name="Measure Race",
            owning_shop=self.shop,
        )
        TenantMember.objects.create(
            tenant=self.shop, user=self.actor, role=ShopRole.ADMIN
        )
        self.client_record = Client.objects.create(tenant=self.shop, name="Race Client")
        self.family, _created = GarmentFamily.objects.get_or_create(code="mens-shirt")
        self.variant, _created = GarmentVariant.objects.get_or_create(
            family=self.family,
            tenant=None,
            code="standard-shirt",
            defaults={"is_default": True},
        )
        self.chest, _created = MeasurementDefinition.objects.get_or_create(
            tenant=None, code="chest", defaults={"sort_order": 0}
        )
        MeasurementDefinitionTranslation.objects.get_or_create(
            definition=self.chest, locale="en", defaults={"name": "Chest"}
        )
        MeasurementDefinitionMapping.objects.get_or_create(
            definition=self.chest, family=self.family, variant=None
        )

    def concurrently(self, operation):
        barrier = Barrier(2)

        def run():
            close_old_connections()
            try:
                actor = User.objects.get(pk=self.actor.pk)
                barrier.wait(timeout=10)
                try:
                    return operation(actor)
                except (DjangoValidationError, DRFValidationError):
                    return "rejected"
            finally:
                connection.close()
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            return [
                future.result(timeout=30)
                for future in (pool.submit(run), pool.submit(run))
            ]

    def profile_operation(self, actor):
        return create_measurement_profile(
            shop_id=self.shop.pk,
            actor=actor,
            person_model=Client,
            person_id=self.client_record.pk,
            family_id=self.family.pk,
            variant_id=self.variant.pk,
        )

    def test_profile_creation_race_keeps_one_profile(self):
        results = self.concurrently(self.profile_operation)
        self.assertEqual(sum(result != "rejected" for result in results), 1)
        self.assertEqual(self.client_record.measurement_profiles.count(), 1)

    def test_concurrent_set_creation_gets_distinct_ordered_versions(self):
        profile = self.profile_operation(self.actor)

        def create(actor):
            return create_measurement_set(
                shop_id=self.shop.pk,
                actor=actor,
                profile_id=profile.pk,
                values=[
                    {"definition_id": self.chest.pk, "value": "38.0000", "unit": "CM"}
                ],
            )

        results = self.concurrently(create)
        self.assertTrue(all(result != "rejected" for result in results))
        self.assertEqual(
            list(profile.sets.order_by("version").values_list("version", flat=True)),
            [1, 2],
        )

    def test_concurrent_copies_get_distinct_versions_and_preserve_provenance(self):
        profile = self.profile_operation(self.actor)
        original = create_measurement_set(
            shop_id=self.shop.pk,
            actor=self.actor,
            profile_id=profile.pk,
            values=[{"definition_id": self.chest.pk, "value": "38.0000", "unit": "CM"}],
        )

        def copy(actor):
            return copy_measurement_set(
                shop_id=self.shop.pk,
                actor=actor,
                profile_id=profile.pk,
                source_set_id=original.pk,
            )

        results = self.concurrently(copy)
        self.assertTrue(all(result != "rejected" for result in results))
        self.assertEqual(
            list(profile.sets.order_by("version").values_list("version", flat=True)),
            [1, 2, 3],
        )
        self.assertEqual(profile.sets.filter(copied_from=original).count(), 2)

    def test_concurrent_custom_definition_code_creation_keeps_one_code(self):
        def create(actor):
            return create_measurement_definition(
                shop_id=self.shop.pk,
                actor=actor,
                code="race-custom-measurement",
                group_code="",
                sort_order=0,
                translations=[
                    {"locale": "en", "name": "Race Measurement", "description": ""}
                ],
                mappings=[{"family_id": self.family.pk}],
            )

        results = self.concurrently(create)
        self.assertEqual(sum(result != "rejected" for result in results), 1)
        self.assertEqual(
            MeasurementDefinition.objects.filter(
                tenant=self.shop, code="race-custom-measurement", deleted__isnull=True
            ).count(),
            1,
        )
