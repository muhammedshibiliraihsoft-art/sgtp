from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from apps.catalog.models import OptionGroup, StyleOption, StyleOptionImage


class StyleOptionImagePrimaryMigrationTests(TransactionTestCase):
    migrate_from = ("catalog", "0014_private_reference_path_length")
    migrate_to = ("catalog", "0016_styleoptionimage_one_primary")

    def setUp(self):
        super().setUp()
        group = OptionGroup.objects.create(code="migration-image-group")
        option = StyleOption.objects.create(
            option_group=group,
            code="migration-image-option",
        )
        self.image_ids = [
            StyleOptionImage.objects.create(
                style_option=option,
                image=f"catalog/global/migration-{sort_order}.png",
                mime_type="image/png",
                byte_size=128,
                width=16,
                height=16,
                sort_order=sort_order,
            ).pk
            for sort_order in (2, 1)
        ]

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_existing_images_are_backfilled_before_unique_constraint(self):
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])

        images = list(
            StyleOptionImage.objects.filter(pk__in=self.image_ids)
            .order_by("sort_order")
            .values_list("sort_order", "is_primary")
        )

        self.assertEqual(images, [(1, True), (2, False)])
