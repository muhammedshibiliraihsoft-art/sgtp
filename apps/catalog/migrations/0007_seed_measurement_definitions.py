from django.db import migrations


APPROVED_DEFINITIONS = {
    "mens-shirt": (
        ("full-length", "Full Length"),
        ("shoulder-width", "Shoulder Width"),
        ("chest", "Chest"),
        ("waist", "Waist"),
        ("sleeve-length", "Sleeve Length"),
        ("neck", "Neck"),
        ("hip-seat", "Hip/Seat"),
        ("bicep", "Bicep"),
        ("armhole", "Armhole"),
        ("cuff-wrist", "Cuff/Wrist"),
    ),
    "kuwaiti-dishdasha": (
        ("full-length", "Full Length"),
        ("shoulder", "Shoulder"),
        ("chest", "Chest"),
        ("sleeve-length", "Sleeve Length"),
        ("neck", "Neck"),
        ("waist", "Waist"),
        ("hip-seat", "Hip/Seat"),
        ("upper-arm-bicep", "Upper Arm/Bicep"),
        ("cuff-sleeve-opening", "Cuff/Sleeve Opening"),
        ("armhole", "Armhole"),
        ("shoulder-slope-posture", "Shoulder Slope/Posture"),
        ("placket-length", "Placket Length"),
        ("side-slit-height", "Side Slit Height"),
    ),
}


def seed_measurements(apps, schema_editor):
    Family = apps.get_model("catalog", "GarmentFamily")
    Definition = apps.get_model("catalog", "MeasurementDefinition")
    Translation = apps.get_model("catalog", "MeasurementDefinitionTranslation")
    Mapping = apps.get_model("catalog", "MeasurementDefinitionMapping")

    for family_code, definitions in APPROVED_DEFINITIONS.items():
        family = Family.objects.get(code=family_code)
        for order, (code, label) in enumerate(definitions):
            definition, _ = Definition.objects.get_or_create(
                tenant=None,
                code=code,
                defaults={"sort_order": order},
            )
            definition.sort_order = order
            definition.save(update_fields=("sort_order", "updated_at"))
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
    dependencies = [("catalog", "0006_measurement_material_foundation")]
    operations = [migrations.RunPython(seed_measurements, migrations.RunPython.noop)]
