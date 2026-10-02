from django.db import migrations


FAMILIES = (
    ("kuwaiti-dishdasha", "Kuwaiti Dishdasha", "standard-kuwaiti-dishdasha", "Standard Kuwaiti Dishdasha"),
    ("mens-shirt", "Men’s Shirt", "standard-shirt", "Standard Shirt"),
    ("abaya", "Abaya", "standard-abaya", "Standard Abaya"),
    ("darraa-long-dress", "Darraa / Long Dress", "standard-darraa", "Standard Darraa"),
)


def seed_catalog(apps, schema_editor):
    GarmentFamily = apps.get_model("catalog", "GarmentFamily")
    FamilyTranslation = apps.get_model("catalog", "GarmentFamilyTranslation")
    GarmentVariant = apps.get_model("catalog", "GarmentVariant")
    VariantTranslation = apps.get_model("catalog", "GarmentVariantTranslation")
    OptionGroup = apps.get_model("catalog", "OptionGroup")
    GroupTranslation = apps.get_model("catalog", "OptionGroupTranslation")
    StyleOption = apps.get_model("catalog", "StyleOption")
    StyleTranslation = apps.get_model("catalog", "StyleOptionTranslation")

    for family_code, family_name, variant_code, variant_name in FAMILIES:
        family, _ = GarmentFamily.objects.get_or_create(code=family_code)
        FamilyTranslation.objects.get_or_create(
            family=family, locale="en", defaults={"name": family_name}
        )
        variant, _ = GarmentVariant.objects.get_or_create(
            family=family, tenant=None, code=variant_code,
            defaults={"is_default": True},
        )
        VariantTranslation.objects.get_or_create(
            variant=variant, locale="en", defaults={"name": variant_name}
        )

    groups = {
        "cuff": "Cuff",
        "collar": "Collar",
        "pocket": "Pocket",
        "placket": "Placket",
        "embroidery": "Embroidery",
        "color": "Color",
        "fabric": "Fabric",
    }
    for code, name in groups.items():
        group, _ = OptionGroup.objects.get_or_create(code=code)
        GroupTranslation.objects.get_or_create(
            option_group=group, locale="en", defaults={"name": name}
        )

    cuff = OptionGroup.objects.get(code="cuff")
    cuff_styles = (
        ("normal-cuff", "Normal Cuff"),
        ("open-cuff", "Open Cuff"),
        ("round-cuff", "Round Cuff"),
        ("square-cuff", "Square Cuff"),
        ("custom", "Custom"),
    )
    for code, name in cuff_styles:
        option, _ = StyleOption.objects.get_or_create(
            tenant=None, option_group=cuff, code=code
        )
        StyleTranslation.objects.get_or_create(
            style_option=option, locale="en", defaults={"name": name}
        )


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]
    operations = [migrations.RunPython(seed_catalog, migrations.RunPython.noop)]
