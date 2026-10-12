import uuid

from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


STYLE_ONLY_DESCRIPTION = (
    "Style preset only. Body measurements and finished-garment ease are "
    "intentionally not included."
)


FAMILY_PRESETS = {
    "kuwaiti-dishdasha": {
        "groups": (
            (
                "neckline",
                "Neckline",
                (
                    ("stand-collar", "Stand Collar"),
                    ("collarless-round-neck", "Collarless Round Neck"),
                ),
            ),
            ("sleeve", "Sleeve", (("full-sleeve", "Full Sleeve"),)),
            (
                "cuff",
                "Cuff",
                (("button-cuff", "Button Cuff"), ("open-cuff", "Open Cuff")),
            ),
            (
                "pocket",
                "Pocket",
                (
                    ("chest-and-side-pockets", "Chest and Side Pockets"),
                    ("side-pockets", "Side Pockets"),
                ),
            ),
            (
                "placket",
                "Placket",
                (
                    ("exposed-button-placket", "Exposed Button Placket"),
                    ("concealed-placket", "Concealed Placket"),
                ),
            ),
            (
                "embellishment",
                "Embellishment",
                (
                    ("no-embellishment", "No Embellishment"),
                    ("tonal-detail", "Tonal Detail"),
                ),
            ),
            (
                "color",
                "Color",
                (
                    ("white", "White"),
                    ("ivory", "Ivory"),
                    ("neutral-grey", "Neutral Grey"),
                ),
            ),
        ),
        "presets": (
            (
                "Everyday White Dishdasha",
                {
                    "neckline": "stand-collar",
                    "sleeve": "full-sleeve",
                    "cuff": "button-cuff",
                    "pocket": "chest-and-side-pockets",
                    "placket": "exposed-button-placket",
                    "embellishment": "no-embellishment",
                    "color": "white",
                },
            ),
            (
                "Minimal Ivory Dishdasha",
                {
                    "neckline": "collarless-round-neck",
                    "sleeve": "full-sleeve",
                    "cuff": "open-cuff",
                    "pocket": "side-pockets",
                    "placket": "concealed-placket",
                    "embellishment": "no-embellishment",
                    "color": "ivory",
                },
            ),
            (
                "Tonal Detail Dishdasha",
                {
                    "neckline": "stand-collar",
                    "sleeve": "full-sleeve",
                    "cuff": "button-cuff",
                    "pocket": "chest-and-side-pockets",
                    "placket": "concealed-placket",
                    "embellishment": "tonal-detail",
                    "color": "neutral-grey",
                },
            ),
        ),
    },
    "abaya": {
        "groups": (
            (
                "silhouette",
                "Silhouette",
                (
                    ("straight-silhouette", "Straight Silhouette"),
                    ("a-line-silhouette", "A-Line Silhouette"),
                    ("wide-flowing-silhouette", "Wide Flowing Silhouette"),
                ),
            ),
            (
                "closure",
                "Closure",
                (("closed-front", "Closed Front"), ("open-front", "Open Front")),
            ),
            (
                "sleeve",
                "Sleeve",
                (
                    ("straight-long-sleeve", "Straight Long Sleeve"),
                    ("bell-sleeve", "Bell Sleeve"),
                ),
            ),
            (
                "neckline",
                "Neckline",
                (("round-neck", "Round Neck"), ("v-neck", "V-Neck")),
            ),
            (
                "embellishment",
                "Embellishment",
                (
                    ("no-embellishment", "No Embellishment"),
                    ("tonal-embroidery", "Tonal Embroidery"),
                    ("contrast-trim", "Contrast Trim"),
                ),
            ),
            (
                "color",
                "Color",
                (("black", "Black"), ("navy", "Navy"), ("taupe", "Taupe")),
            ),
        ),
        "presets": (
            (
                "Classic Closed Abaya",
                {
                    "silhouette": "straight-silhouette",
                    "closure": "closed-front",
                    "sleeve": "straight-long-sleeve",
                    "neckline": "round-neck",
                    "embellishment": "no-embellishment",
                    "color": "black",
                },
            ),
            (
                "Everyday Open Abaya",
                {
                    "silhouette": "a-line-silhouette",
                    "closure": "open-front",
                    "sleeve": "straight-long-sleeve",
                    "neckline": "v-neck",
                    "embellishment": "contrast-trim",
                    "color": "navy",
                },
            ),
            (
                "Embroidered Occasion Abaya",
                {
                    "silhouette": "wide-flowing-silhouette",
                    "closure": "closed-front",
                    "sleeve": "bell-sleeve",
                    "neckline": "round-neck",
                    "embellishment": "tonal-embroidery",
                    "color": "taupe",
                },
            ),
        ),
    },
    "darraa-long-dress": {
        "groups": (
            (
                "silhouette",
                "Silhouette",
                (
                    ("straight-silhouette", "Straight Silhouette"),
                    ("a-line-silhouette", "A-Line Silhouette"),
                    ("relaxed-silhouette", "Relaxed Silhouette"),
                ),
            ),
            (
                "neckline",
                "Neckline",
                (("round-neck", "Round Neck"), ("v-neck", "V-Neck")),
            ),
            (
                "sleeve",
                "Sleeve",
                (
                    ("straight-long-sleeve", "Straight Long Sleeve"),
                    ("bell-sleeve", "Bell Sleeve"),
                ),
            ),
            (
                "closure",
                "Closure",
                (("pullover", "Pullover"), ("front-button", "Front Button")),
            ),
            (
                "embellishment",
                "Embellishment",
                (
                    ("no-embellishment", "No Embellishment"),
                    ("neckline-embroidery", "Neckline Embroidery"),
                    ("all-over-embroidery", "All-Over Embroidery"),
                ),
            ),
            (
                "color",
                "Color",
                (
                    ("jewel-tone", "Jewel Tone"),
                    ("neutral", "Neutral"),
                    ("pastel", "Pastel"),
                ),
            ),
        ),
        "presets": (
            (
                "Everyday Darraa",
                {
                    "silhouette": "relaxed-silhouette",
                    "neckline": "round-neck",
                    "sleeve": "straight-long-sleeve",
                    "closure": "pullover",
                    "embellishment": "no-embellishment",
                    "color": "neutral",
                },
            ),
            (
                "Neckline Embroidered Darraa",
                {
                    "silhouette": "a-line-silhouette",
                    "neckline": "v-neck",
                    "sleeve": "straight-long-sleeve",
                    "closure": "front-button",
                    "embellishment": "neckline-embroidery",
                    "color": "jewel-tone",
                },
            ),
            (
                "Flowing Occasion Long Dress",
                {
                    "silhouette": "a-line-silhouette",
                    "neckline": "round-neck",
                    "sleeve": "bell-sleeve",
                    "closure": "pullover",
                    "embellishment": "all-over-embroidery",
                    "color": "pastel",
                },
            ),
        ),
    },
}


def _default_variant(GarmentVariant, family):
    candidates = GarmentVariant.objects.filter(
        family=family, tenant__isnull=True, is_active=True
    )
    return (
        candidates.filter(is_default=True).order_by("created_at", "id").first()
        or candidates.order_by("created_at", "id").first()
    )


def _seed_design_id(family_code, name):
    return uuid.uuid5(
        uuid.NAMESPACE_URL, f"sgtp:catalog:seed-0018:{family_code}:{name}"
    )


def seed_remaining_design_defaults(apps, schema_editor):
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

    for family_code, config in FAMILY_PRESETS.items():
        family = GarmentFamily.objects.filter(code=family_code).first()
        if family is None:
            continue
        variant = _default_variant(GarmentVariant, family)
        if variant is None:
            continue
        groups = {}
        options = {}
        for sort_order, (group_code, group_name, option_rows) in enumerate(
            config["groups"], start=1
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
            groups[group_code] = group
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
                options[(group_code, option_code)] = option

        for name, selected in config["presets"]:
            exists = DesignVersionTranslation.objects.filter(
                locale="en",
                name=name,
                version__design__tenant__isnull=True,
                version__design__family=family,
                version__design__variant=variant,
            ).exists()
            if exists:
                continue
            design = Design.objects.create(
                id=_seed_design_id(family_code, name),
                tenant=None,
                family=family,
                variant=variant,
            )
            version = DesignVersion.objects.create(
                design=design, number=1, status="PUBLISHED"
            )
            DesignVersionTranslation.objects.create(
                version=version,
                locale="en",
                name=name,
                description=STYLE_ONLY_DESCRIPTION,
            )
            for group_code, option_code in selected.items():
                option = options[(group_code, option_code)]
                DesignSelection.objects.create(
                    version=version,
                    option_group=groups[group_code],
                    style_option=option,
                    selected_code=option_code,
                    selected_name_en=option.translations.get(locale="en").name,
                )


def unseed_remaining_design_defaults(apps, schema_editor):
    Design = apps.get_model("catalog", "Design")
    DesignVersion = apps.get_model("catalog", "DesignVersion")
    DesignVersionTranslation = apps.get_model("catalog", "DesignVersionTranslation")
    DesignSelection = apps.get_model("catalog", "DesignSelection")

    for family_code, config in FAMILY_PRESETS.items():
        for name, selected in config["presets"]:
            design = Design.objects.filter(
                id=_seed_design_id(family_code, name),
                tenant__isnull=True,
                family__code=family_code,
            ).first()
            if design is None:
                continue
            versions = list(DesignVersion.objects.filter(design=design))
            if (
                len(versions) != 1
                or versions[0].number != 1
                or versions[0].status != "PUBLISHED"
                or design.status != "ACTIVE"
                or design.source_design_id is not None
            ):
                raise IrreversibleError("Seeded design has changed; preserve it.")
            version = versions[0]
            translations = list(
                DesignVersionTranslation.objects.filter(version=version)
            )
            if len(translations) != 1 or not any(
                row.locale == "en"
                and row.name == name
                and row.description == STYLE_ONLY_DESCRIPTION
                for row in translations
            ):
                raise IrreversibleError("Seeded design translation has changed.")
            actual_selections = sorted(
                DesignSelection.objects.filter(version=version).values_list(
                    "option_group__code", "selected_code"
                )
            )
            expected_selections = sorted(selected.items())
            if actual_selections != expected_selections:
                raise IrreversibleError("Seeded design selections have changed.")
            DesignSelection.objects.filter(version=version).delete()
            DesignVersionTranslation.objects.filter(version=version).delete()
            DesignVersion.objects.filter(id=version.id).delete()
            Design.objects.filter(id=design.id).delete()


class Migration(migrations.Migration):
    dependencies = [("catalog", "0017_measurement_version_deactivation_design_retry")]
    operations = [
        migrations.RunPython(
            seed_remaining_design_defaults,
            unseed_remaining_design_defaults,
        )
    ]
