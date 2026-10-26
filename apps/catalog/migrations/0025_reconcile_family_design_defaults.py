import importlib
import uuid

from django.db import migrations


_seed_0018 = importlib.import_module(
    "apps.catalog.migrations.0018_seed_remaining_family_design_defaults"
)
FAMILY_PRESETS = _seed_0018.FAMILY_PRESETS
STYLE_ONLY_DESCRIPTION = _seed_0018.STYLE_ONLY_DESCRIPTION


def _seed_design_id(family_code, name):
    return uuid.uuid5(
        uuid.NAMESPACE_URL, f"sgtp:catalog:seed-0025:{family_code}:{name}"
    )


def reconcile_family_design_defaults(apps, schema_editor):
    """Repair missing 0018 global defaults without relying on Variants."""
    db_alias = schema_editor.connection.alias
    GarmentFamily = apps.get_model("catalog", "GarmentFamily")
    OptionGroup = apps.get_model("catalog", "OptionGroup")
    OptionGroupTranslation = apps.get_model("catalog", "OptionGroupTranslation")
    FamilyOptionGroup = apps.get_model("catalog", "FamilyOptionGroup")
    StyleOption = apps.get_model("catalog", "StyleOption")
    StyleOptionTranslation = apps.get_model("catalog", "StyleOptionTranslation")
    Design = apps.get_model("catalog", "Design")
    DesignVersion = apps.get_model("catalog", "DesignVersion")
    DesignVersionTranslation = apps.get_model("catalog", "DesignVersionTranslation")
    DesignSelection = apps.get_model("catalog", "DesignSelection")

    for family_code, config in FAMILY_PRESETS.items():
        family = (
            GarmentFamily.objects.using(db_alias)
            .filter(code=family_code, tenant__isnull=True)
            .first()
        )
        if family is None:
            continue

        groups = {}
        options = {}
        for sort_order, (group_code, group_name, option_rows) in enumerate(
            config["groups"], start=1
        ):
            group, _created = OptionGroup.objects.using(db_alias).get_or_create(
                tenant_id=None,
                code=group_code,
            )
            OptionGroupTranslation.objects.using(db_alias).get_or_create(
                option_group=group,
                locale="en",
                defaults={"name": group_name, "description": ""},
            )
            FamilyOptionGroup.objects.using(db_alias).get_or_create(
                family=family,
                option_group=group,
                defaults={"sort_order": sort_order},
            )
            groups[group_code] = group

            for option_code, option_name in option_rows:
                option, _created = StyleOption.objects.using(db_alias).get_or_create(
                    tenant_id=None,
                    option_group=group,
                    code=option_code,
                    defaults={"is_active": True},
                )
                StyleOptionTranslation.objects.using(db_alias).get_or_create(
                    style_option=option,
                    locale="en",
                    defaults={"name": option_name, "description": ""},
                )
                options[(group_code, option_code)] = option

        for name, selected in config["presets"]:
            existing_name = DesignVersionTranslation._base_manager.using(
                db_alias
            ).filter(
                locale="en",
                name=name,
                version__design__tenant__isnull=True,
                version__design__family_id=family.pk,
            ).exists()
            if existing_name:
                continue

            design_id = _seed_design_id(family_code, name)
            if Design._base_manager.using(db_alias).filter(pk=design_id).exists():
                raise RuntimeError(
                    "Family default Design seed ID already exists without its "
                    "expected English name; refusing to overwrite it."
                )

            design = Design.objects.using(db_alias).create(
                id=design_id,
                tenant_id=None,
                family_id=family.pk,
                variant_id=None,
                status="ACTIVE",
                is_default_seeded=False,
            )
            version = DesignVersion.objects.using(db_alias).create(
                design=design,
                number=1,
                status="PUBLISHED",
            )
            DesignVersionTranslation.objects.using(db_alias).create(
                version=version,
                locale="en",
                name=name,
                description=STYLE_ONLY_DESCRIPTION,
            )
            for group_code, option_code in selected.items():
                option = options[(group_code, option_code)]
                option_name = StyleOptionTranslation._base_manager.using(
                    db_alias
                ).get(style_option_id=option.pk, locale="en").name
                DesignSelection.objects.using(db_alias).create(
                    version=version,
                    option_group=groups[group_code],
                    style_option=option,
                    selected_code=option_code,
                    selected_name_en=option_name,
                )


class Migration(migrations.Migration):
    dependencies = [("catalog", "0024_retire_variant_measurement_mappings")]

    operations = [
        migrations.RunPython(
            reconcile_family_design_defaults,
            migrations.RunPython.noop,
        )
    ]
