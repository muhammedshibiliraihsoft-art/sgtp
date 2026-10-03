from django.db import migrations


SHIRT_GROUPS = (
    (
        "sleeve",
        "Sleeve",
        (
            ("full-sleeve", "Full Sleeve"),
            ("short-sleeve", "Short Sleeve"),
        ),
    ),
    (
        "collar",
        "Collar",
        (
            ("spread-collar", "Spread Collar"),
            ("button-down-collar", "Button-Down Collar"),
            ("band-collar", "Band Collar"),
        ),
    ),
    (
        "cuff",
        "Cuff",
        (
            ("normal-cuff", "Normal Cuff"),
            ("round-cuff", "Round Cuff"),
        ),
    ),
    (
        "pocket",
        "Pocket",
        (
            ("no-pocket", "No Pocket"),
            ("left-chest-pocket", "Left Chest Pocket"),
        ),
    ),
    (
        "placket",
        "Placket",
        (
            ("standard-placket", "Standard Placket"),
            ("hidden-placket", "Hidden Placket"),
        ),
    ),
    (
        "embroidery",
        "Embroidery",
        (
            ("no-embroidery", "No Embroidery"),
            ("monogram", "Monogram"),
        ),
    ),
    (
        "color",
        "Color",
        (
            ("classic-white", "Classic White"),
            ("sky-blue", "Sky Blue"),
            ("navy", "Navy"),
        ),
    ),
)


SHIRT_PRESETS = (
    (
        "Classic Formal Shirt",
        {
            "sleeve": "full-sleeve",
            "collar": "spread-collar",
            "cuff": "normal-cuff",
            "pocket": "no-pocket",
            "placket": "standard-placket",
            "embroidery": "no-embroidery",
            "color": "classic-white",
        },
    ),
    (
        "Smart Casual Shirt",
        {
            "sleeve": "full-sleeve",
            "collar": "button-down-collar",
            "cuff": "round-cuff",
            "pocket": "left-chest-pocket",
            "placket": "standard-placket",
            "embroidery": "monogram",
            "color": "sky-blue",
        },
    ),
    (
        "Modern Evening Shirt",
        {
            "sleeve": "full-sleeve",
            "collar": "band-collar",
            "cuff": "normal-cuff",
            "pocket": "no-pocket",
            "placket": "hidden-placket",
            "embroidery": "no-embroidery",
            "color": "navy",
        },
    ),
)


def seed_mens_shirt_design_defaults(apps, schema_editor):
    GarmentFamily = apps.get_model("catalog", "GarmentFamily")
    GarmentVariant = apps.get_model("catalog", "GarmentVariant")
    OptionGroup = apps.get_model("catalog", "OptionGroup")
    OptionGroupTranslation = apps.get_model("catalog", "OptionGroupTranslation")
    FamilyOptionGroup = apps.get_model("catalog", "FamilyOptionGroup")
    StyleOption = apps.get_model("catalog", "StyleOption")
    StyleOptionTranslation = apps.get_model("catalog", "StyleOptionTranslation")
    Design = apps.get_model("catalog", "Design")
    DesignVersion = apps.get_model("catalog", "DesignVersion")
    DesignVersionTranslation = apps.get_model("catalog", "DesignVersionTranslation")
    DesignSelection = apps.get_model("catalog", "DesignSelection")

    family = GarmentFamily.objects.get(code="mens-shirt")
    variant = GarmentVariant.objects.get(
        family=family,
        tenant__isnull=True,
        code="standard-shirt",
    )
    groups_by_code = {}
    options_by_code = {}

    for sort_order, (group_code, group_name, option_rows) in enumerate(
        SHIRT_GROUPS, start=1
    ):
        group, _ = OptionGroup.objects.get_or_create(code=group_code)
        OptionGroupTranslation.objects.get_or_create(
            option_group=group,
            locale="en",
            defaults={"name": group_name, "description": ""},
        )
        FamilyOptionGroup.objects.get_or_create(
            family=family,
            option_group=group,
            defaults={"sort_order": sort_order},
        )
        groups_by_code[group_code] = group
        for option_code, option_name in option_rows:
            option, _ = StyleOption.objects.get_or_create(
                tenant=None,
                option_group=group,
                code=option_code,
                defaults={"is_active": True},
            )
            StyleOptionTranslation.objects.get_or_create(
                style_option=option,
                locale="en",
                defaults={"name": option_name, "description": ""},
            )
            options_by_code[(group_code, option_code)] = option

    for name, selected_options in SHIRT_PRESETS:
        existing = (
            Design.objects.filter(
                tenant__isnull=True,
                family=family,
                variant=variant,
                versions__translations__locale="en",
                versions__translations__name=name,
            )
            .order_by("id")
            .first()
        )
        if existing is not None:
            continue
        design = Design.objects.create(tenant=None, family=family, variant=variant)
        version = DesignVersion.objects.create(
            design=design,
            number=1,
            status="PUBLISHED",
        )
        DesignVersionTranslation.objects.create(
            version=version,
            locale="en",
            name=name,
            description="",
        )
        for group_code, option_code in selected_options.items():
            option = options_by_code[(group_code, option_code)]
            DesignSelection.objects.create(
                version=version,
                option_group=groups_by_code[group_code],
                style_option=option,
                selected_code=option_code,
                selected_name_en=option.translations.get(locale="en").name,
            )


def unseed_mens_shirt_design_defaults(apps, schema_editor):
    """Remove only the published template rows introduced by this migration.

    The project migration tests temporarily move the accounts and tenant
    schemas backwards.  Catalog migrations are consequently unapplied too,
    so leaving template Design rows behind would make an earlier non-null
    Design.name column impossible to restore.
    """
    GarmentFamily = apps.get_model("catalog", "GarmentFamily")
    GarmentVariant = apps.get_model("catalog", "GarmentVariant")
    Design = apps.get_model("catalog", "Design")
    DesignVersion = apps.get_model("catalog", "DesignVersion")
    DesignVersionTranslation = apps.get_model("catalog", "DesignVersionTranslation")
    DesignSelection = apps.get_model("catalog", "DesignSelection")

    family = GarmentFamily.objects.filter(code="mens-shirt").first()
    if family is None:
        return
    variant = GarmentVariant.objects.filter(
        family=family, tenant__isnull=True, code="standard-shirt"
    ).first()
    if variant is None:
        return

    names = [name for name, _selected_options in SHIRT_PRESETS]
    versions = DesignVersion.objects.filter(
        design__tenant__isnull=True,
        design__family=family,
        design__variant=variant,
        translations__locale="en",
        translations__name__in=names,
    ).distinct()
    design_ids = list(versions.values_list("design_id", flat=True))
    version_ids = list(versions.values_list("id", flat=True))
    if not version_ids:
        return

    # These seed rows have no external user-owned relations.  Hard deletion is
    # required for migration reversal because the earlier schema restores a
    # non-null Design.name column.
    # Historical migration models use Django's regular queryset deletion, so
    # this removes rows rather than invoking the runtime soft-delete policy.
    DesignSelection.objects.filter(version_id__in=version_ids).delete()
    DesignVersionTranslation.objects.filter(version_id__in=version_ids).delete()
    DesignVersion.objects.filter(id__in=version_ids).delete()
    Design.objects.filter(id__in=design_ids).delete()


class Migration(migrations.Migration):
    dependencies = [("catalog", "0011_garmentvariant_is_active")]

    operations = [
        migrations.RunPython(
            seed_mens_shirt_design_defaults,
            unseed_mens_shirt_design_defaults,
        )
    ]
