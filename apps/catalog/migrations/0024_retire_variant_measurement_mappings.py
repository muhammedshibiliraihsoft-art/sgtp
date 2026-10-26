from django.db import migrations, models


def assert_no_variant_measurement_mappings(apps, schema_editor):
    Mapping = apps.get_model("catalog", "MeasurementDefinitionMapping")
    if Mapping._base_manager.filter(variant_id__isnull=False).exists():
        raise RuntimeError(
            "Variant retirement requires every measurement mapping to be family-level. "
            "Resolve variant-specific mappings before applying this migration."
        )


class Migration(migrations.Migration):
    dependencies = [("catalog", "0023_seed_abaya_darraa_measurement_defaults")]

    operations = [
        migrations.RunPython(
            assert_no_variant_measurement_mappings,
            migrations.RunPython.noop,
        ),
        migrations.RemoveConstraint(
            model_name="measurementdefinitionmapping",
            name="measure_map_variant_uniq",
        ),
        migrations.RemoveConstraint(
            model_name="measurementdefinitionmapping",
            name="measure_map_family_uniq",
        ),
        migrations.RemoveField(
            model_name="measurementdefinitionmapping",
            name="variant",
        ),
        migrations.AddConstraint(
            model_name="measurementdefinitionmapping",
            constraint=models.UniqueConstraint(
                fields=("definition", "family"),
                condition=models.Q(deleted__isnull=True),
                name="measure_map_family_uniq",
            ),
        ),
    ]
