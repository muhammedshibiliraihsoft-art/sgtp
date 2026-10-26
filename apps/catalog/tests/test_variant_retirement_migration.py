import importlib
from unittest.mock import Mock

from django.test import SimpleTestCase


migration = importlib.import_module(
    "apps.catalog.migrations.0024_retire_variant_measurement_mappings"
)


class VariantRetirementMigrationTests(SimpleTestCase):
    def _apps_with_mapping_result(self, exists):
        mapping = Mock()
        mapping._base_manager.filter.return_value.exists.return_value = exists
        apps = Mock()
        apps.get_model.return_value = mapping
        return apps, mapping

    def test_preflight_allows_family_only_measurement_mappings(self):
        apps, mapping = self._apps_with_mapping_result(False)

        migration.assert_no_variant_measurement_mappings(apps, None)

        apps.get_model.assert_called_once_with(
            "catalog", "MeasurementDefinitionMapping"
        )
        mapping._base_manager.filter.assert_called_once_with(
            variant_id__isnull=False
        )

    def test_preflight_blocks_variant_specific_measurement_mappings(self):
        apps, _mapping = self._apps_with_mapping_result(True)

        with self.assertRaisesMessage(
            RuntimeError,
            "Resolve variant-specific mappings before applying this migration.",
        ):
            migration.assert_no_variant_measurement_mappings(apps, None)
