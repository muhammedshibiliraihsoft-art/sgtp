from importlib import import_module

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.exceptions import IrreversibleError

from apps.catalog.models import (
    Design,
    DesignSelection,
    DesignVersion,
    DesignVersionTranslation,
    OptionGroup,
    StyleOption,
)


seed_migration = import_module(
    "apps.catalog.migrations.0018_seed_remaining_family_design_defaults"
)


def _migration_apps():
    return (
        MigrationExecutor(connection)
        .loader.project_state(
            [("catalog", "0018_seed_remaining_family_design_defaults")]
        )
        .apps
    )


@pytest.mark.django_db
def test_seed_reverse_preserves_another_design_with_the_same_name():
    family_code = "kuwaiti-dishdasha"
    name = "Everyday White Dishdasha"
    seeded = Design.objects.get(id=seed_migration._seed_design_id(family_code, name))
    another = Design.objects.create(family=seeded.family, variant=seeded.variant)
    another_version = DesignVersion.objects.create(
        design=another, number=1, status="DRAFT"
    )
    DesignVersionTranslation.objects.create(
        version=another_version, locale="en", name=name
    )

    seed_migration.unseed_remaining_design_defaults(_migration_apps(), None)

    assert not Design.objects.filter(id=seeded.id).exists()
    assert Design.objects.filter(id=another.id).exists()
    assert DesignVersionTranslation.objects.filter(version=another_version).exists()


@pytest.mark.django_db
def test_seed_reverse_refuses_to_delete_an_edited_design():
    family_code = "kuwaiti-dishdasha"
    name = "Everyday White Dishdasha"
    seeded = Design.objects.get(id=seed_migration._seed_design_id(family_code, name))
    DesignVersion.objects.create(design=seeded, number=2, status="DRAFT")

    with pytest.raises(IrreversibleError, match="Seeded design has changed"):
        seed_migration.unseed_remaining_design_defaults(_migration_apps(), None)

    assert Design.objects.filter(id=seeded.id).exists()


@pytest.mark.django_db
def test_seed_reverse_refuses_an_extra_selection_in_an_existing_group():
    family_code = "kuwaiti-dishdasha"
    name = "Everyday White Dishdasha"
    seeded = Design.objects.get(id=seed_migration._seed_design_id(family_code, name))
    version = DesignVersion.objects.get(design=seeded, number=1)
    neckline = OptionGroup.objects.get(code="neckline")
    alternate = StyleOption.objects.get(
        tenant__isnull=True,
        option_group=neckline,
        code="collarless-round-neck",
    )
    DesignSelection.objects.bulk_create(
        [
            DesignSelection(
                version=version,
                option_group=neckline,
                style_option=alternate,
                selected_code=alternate.code,
                selected_name_en="Collarless Round Neck",
            )
        ]
    )

    with pytest.raises(
        IrreversibleError, match="Seeded design selections have changed"
    ):
        seed_migration.unseed_remaining_design_defaults(_migration_apps(), None)

    assert Design.objects.filter(id=seeded.id).exists()
    assert DesignSelection.objects.filter(version=version).count() == 8
