from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.db import close_old_connections, connection
from django.test import TransactionTestCase, skipUnlessDBFeature
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User
from apps.catalog.models import (
    Design,
    DesignSelection,
    DesignVersion,
    FamilyOptionGroup,
    GarmentFamily,
    GarmentVariant,
    OptionGroup,
    StyleOption,
)
from apps.catalog.services import add_selection, publish_version
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember


@skipUnlessDBFeature("has_select_for_update")
class CatalogConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.assertEqual(connection.vendor, "postgresql")
        supplier, _ = Supplier.objects.get_or_create(singleton_lock=True)
        self.shop = Tenant.objects.create(
            supplier=supplier,
            name="Catalog Race Shop",
            slug="catalog-race-shop",
            max_users=10,
        )
        self.actor = User.objects.create_user(
            email="catalog-race-admin@example.test",
            password="safe-test-password",
            first_name="Catalog Race",
            owning_shop=self.shop,
        )
        TenantMember.objects.create(
            tenant=self.shop, user=self.actor, role=ShopRole.ADMIN
        )
        family, _ = GarmentFamily.objects.get_or_create(code="mens-shirt")
        variant, _ = GarmentVariant.objects.get_or_create(
            family=family,
            tenant=None,
            code="standard-shirt",
            defaults={"is_default": True},
        )
        group, _ = OptionGroup.objects.get_or_create(code="cuff")
        FamilyOptionGroup.objects.get_or_create(family=family, option_group=group)
        self.option, _ = StyleOption.objects.get_or_create(
            tenant=None, option_group=group, code="normal-cuff"
        )
        self.design = Design.objects.create(
            tenant=self.shop, family=family, variant=variant
        )
        self.version = DesignVersion.objects.create(design=self.design, number=1)

    def concurrently(self, operation):
        barrier = Barrier(2)

        def worker(run_operation):
            close_old_connections()
            try:
                actor = User.objects.get(pk=self.actor.pk)
                barrier.wait(timeout=10)
                try:
                    run_operation(actor)
                    return "ok"
                except ValidationError:
                    return "rejected"
            finally:
                connection.close()
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(worker, operation) for _ in range(2)]
            return [future.result(timeout=30) for future in futures]

    def test_only_one_concurrent_publish_creates_the_next_version(self):
        results = self.concurrently(
            lambda actor: publish_version(
                shop_id=self.shop.pk, actor=actor, version_id=self.version.pk
            )
        )
        self.assertCountEqual(results, ["ok", "rejected"])
        self.assertEqual(self.design.versions.count(), 2)
        self.assertEqual(
            self.design.versions.filter(status=DesignVersion.Status.PUBLISHED).count(),
            1,
        )
        self.assertEqual(
            self.design.versions.filter(status=DesignVersion.Status.DRAFT).count(), 1
        )

    def test_selection_racing_publish_never_mutates_published_version(self):
        def select(actor):
            add_selection(
                shop_id=self.shop.pk,
                actor=actor,
                version_id=self.version.pk,
                option=self.option,
            )

        def publish(actor):
            publish_version(
                shop_id=self.shop.pk, actor=actor, version_id=self.version.pk
            )

        # Run the actual conflicting operations under independent connections.
        barrier = Barrier(2)

        def run(operation):
            close_old_connections()
            try:
                actor = User.objects.get(pk=self.actor.pk)
                barrier.wait(timeout=10)
                try:
                    operation(actor)
                    return operation.__name__, "ok"
                except ValidationError:
                    return operation.__name__, "rejected"
            finally:
                connection.close()
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(run, (select, publish)))

        self.assertIn(("publish", "ok"), outcomes)
        self.assertIn(
            outcomes,
            [
                [("select", "ok"), ("publish", "ok")],
                [("publish", "ok"), ("select", "ok")],
                [("select", "rejected"), ("publish", "ok")],
                [("publish", "ok"), ("select", "rejected")],
            ],
        )
        published = self.design.versions.get(status=DesignVersion.Status.PUBLISHED)
        self.assertLessEqual(published.selections.count(), 1)
        self.assertEqual(
            DesignSelection.objects.filter(version=published).count(),
            published.selections.count(),
        )
