from django.db import migrations


FAMILY_MEASUREMENTS = {
    "abaya": (
        ("full-length", "Full Length"),
        ("shoulder-width", "Shoulder Width"),
        ("bust-chest", "Bust/Chest"),
        ("waist", "Waist"),
        ("hip-seat", "Hip/Seat"),
        ("sleeve-length", "Sleeve Length"),
        ("upper-arm-bicep", "Upper Arm/Bicep"),
        ("armhole", "Armhole"),
        ("sleeve-opening", "Sleeve Opening"),
        ("neck-opening", "Neck Opening"),
    ),
    "darraa-long-dress": (
        ("full-length", "Full Length"),
        ("shoulder-width", "Shoulder Width"),
        ("bust-chest", "Bust/Chest"),
        ("waist", "Waist"),
        ("hip-seat", "Hip/Seat"),
        ("sleeve-length", "Sleeve Length"),
        ("upper-arm-bicep", "Upper Arm/Bicep"),
        ("armhole", "Armhole"),
        ("sleeve-opening", "Sleeve Opening"),
        ("neck-opening", "Neck Opening"),
        ("hem-width", "Hem Width"),
    ),
}


def seed_remaining_family_measurements(apps, schema_editor):
    Family = apps.get_model("catalog", "GarmentFamily")
    Definition = apps.get_model("catalog", "MeasurementDefinition")
    Translation = apps.get_model("catalog", "MeasurementDefinitionTranslation")
    Mapping = apps.get_model("catalog", "MeasurementDefinitionMapping")

    for family_code, measurements in FAMILY_MEASUREMENTS.items():
        family = Family.objects.filter(
            tenant__isnull=True,
            code=family_code,
        ).first()
        if family is None:
            continue

        for order, (code, label) in enumerate(measurements):
            definition, _ = Definition.objects.get_or_create(
                tenant=None,
                code=code,
                defaults={"sort_order": order},
            )
            Translation.objects.get_or_create(
                definition=definition,
                locale="en",
                defaults={"name": label, "description": ""},
            )
            Mapping.objects.get_or_create(
                definition=definition,
                family=family,
                variant=None,
                defaults={"sort_order": order},
            )


class Migration(migrations.Migration):
    dependencies = [("catalog", "0022_unique_tenant_template_variant")]
    operations = [
        migrations.RunPython(
            seed_remaining_family_measurements,
            migrations.RunPython.noop,
        )
    ]
