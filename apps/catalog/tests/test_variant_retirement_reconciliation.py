import importlib
from types import SimpleNamespace

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from safedelete.models import HARD_DELETE

from apps.accounts.models import User
from apps.catalog.models import (
    Design,
    DesignSelection,
    DesignVersion,
    DesignVersionTranslation,
    FamilyOptionGroup,
    GarmentFamily,
    GarmentVariant,
    StyleOption,
)
from apps.tenants.models import Supplier, Tenant


reconciliation = importlib.import_module(
    "apps.catalog.migrations.0025_reconcile_family_design_defaults"
)


def _migration_apps():
    executor = MigrationExecutor(connection)
    return executor.loader.project_state(
        [("catalog", "0025_reconcile_family_design_defaults")]
    ).apps


def _run_reconciliation():
    reconciliation.reconcile_family_design_defaults(
        _migration_apps(), SimpleNamespace(connection=connection)
    )


def _preset_design_ids(family, names):
    return list(
        Design.objects.filter(
            tenant__isnull=True,
            family=family,
            versions__translations__locale="en",
            versions__translations__name__in=names,
        )
        .distinct()
        .values_list("id", flat=True)
    )


@pytest.mark.django_db
def test_reconciliation_does_not_duplicate_normal_0018_defaults():
    family_codes = tuple(reconciliation.FAMILY_PRESETS)
    before = {
        "designs": Design.objects.filter(
            tenant__isnull=True, family__code__in=family_codes
        ).count(),
        "groups": FamilyOptionGroup.objects.filter(
            family__code__in=family_codes, family__tenant__isnull=True
        ).count(),
        "options": StyleOption.objects.filter(
            tenant__isnull=True,
            option_group__families__code__in=family_codes,
            option_group__families__tenant__isnull=True,
        )
        .distinct()
        .count(),
    }

    _run_reconciliation()

    after = {
        "designs": Design.objects.filter(
            tenant__isnull=True, family__code__in=family_codes
        ).count(),
        "groups": FamilyOptionGroup.objects.filter(
            family__code__in=family_codes, family__tenant__isnull=True
        ).count(),
        "options": StyleOption.objects.filter(
            tenant__isnull=True,
            option_group__families__code__in=family_codes,
            option_group__families__tenant__isnull=True,
        )
        .distinct()
        .count(),
    }
    assert after == before


@pytest.mark.django_db
def test_variant_absent_0018_outcome_is_repaired_and_bootstraps_shop():
    family_code = "abaya"
    config = reconciliation.FAMILY_PRESETS[family_code]
    family = GarmentFamily.objects.get(code=family_code, tenant__isnull=True)
    names = [name for name, _selected in config["presets"]]

    GarmentVariant.objects.filter(family=family, tenant__isnull=True).update(
        is_active=False, is_default=False
    )
    family_group_codes = [group_code for group_code, _label, _rows in config["groups"]]
    FamilyOptionGroup.objects.filter(
        family=family, option_group__code__in=family_group_codes
    ).delete(force_policy=HARD_DELETE)

    seed_ids = _preset_design_ids(family, names)
    seed_version_ids = list(
        DesignVersion.objects.filter(design_id__in=seed_ids).values_list(
            "id", flat=True
        )
    )
    DesignSelection.all_objects.filter(version_id__in=seed_version_ids).delete(
        force_policy=HARD_DELETE
    )
    DesignVersionTranslation.all_objects.filter(
        version_id__in=seed_version_ids
    ).delete(force_policy=HARD_DELETE)
    DesignVersion.all_objects.filter(id__in=seed_version_ids).delete(
        force_policy=HARD_DELETE
    )
    Design.all_objects.filter(id__in=seed_ids).delete(force_policy=HARD_DELETE)

    preserved = Design.objects.create(
        tenant=None, family=family, variant=GarmentVariant.objects.filter(
            family=family, tenant__isnull=True
        ).first()
    )
    preserved_version = DesignVersion.objects.create(
        design=preserved, number=1, status="DRAFT"
    )
    DesignVersionTranslation.objects.create(
        version=preserved_version, locale="en", name="Unrelated preserved draft"
    )

    _run_reconciliation()

    assert not GarmentVariant.objects.filter(
        family=family, tenant__isnull=True, is_active=True
    ).exists()
    assert FamilyOptionGroup.objects.filter(
        family=family,
        family__tenant__isnull=True,
        option_group__code__in=family_group_codes,
        deleted__isnull=True,
    ).count() == len(family_group_codes)
    for name, selected in config["presets"]:
        design = Design.objects.get(
            tenant__isnull=True,
            family=family,
            variant__isnull=True,
            versions__status="PUBLISHED",
            versions__translations__locale="en",
            versions__translations__name=name,
        )
        version = design.versions.get(status="PUBLISHED")
        assert version.selections.count() == len(selected)
        assert {
            (row.option_group.code, row.selected_code)
            for row in version.selections.select_related("option_group")
        } == set(selected.items())

    preserved.refresh_from_db()
    preserved_version.refresh_from_db()
    assert preserved.status == Design.Status.ACTIVE
    assert preserved_version.status == DesignVersion.Status.DRAFT
    assert preserved_version.translations.get(locale="en").name == (
        "Unrelated preserved draft"
    )

    before_rerun = (
        Design.objects.filter(tenant__isnull=True, family=family).count(),
        FamilyOptionGroup.objects.filter(
            family=family, deleted__isnull=True
        ).count(),
        StyleOption.objects.filter(
            tenant__isnull=True,
            option_group__families=family,
            option_group__families__tenant__isnull=True,
        )
        .distinct()
        .count(),
    )
    _run_reconciliation()
    assert (
        Design.objects.filter(tenant__isnull=True, family=family).count(),
        FamilyOptionGroup.objects.filter(
            family=family, deleted__isnull=True
        ).count(),
        StyleOption.objects.filter(
            tenant__isnull=True,
            option_group__families=family,
            option_group__families__tenant__isnull=True,
        )
        .distinct()
        .count(),
    ) == before_rerun

    supplier = Supplier.objects.get(singleton_lock=True)
    shop = Tenant.objects.create(
        supplier=supplier,
        name="Variant-free bootstrap",
        slug="variant-free-bootstrap",
        max_users=5,
    )
    actor = User.objects.create_superuser(
        email="variant-free-bootstrap@example.test",
        password="Safe-Test-Password-293!",
        first_name="Bootstrap",
        phone="+96550001991",
    )
    from apps.catalog.services import initialize_shop_default_catalog

    initialize_shop_default_catalog(
        shop=shop, actor=actor, family_ids=[family.pk]
    )
    local_family = GarmentFamily.objects.get(tenant=shop, template_source=family)
    local_defaults = Design.objects.filter(
        tenant=shop,
        family=local_family,
        is_default_seeded=True,
        source_design__family=family,
    )
    copied_names = set(
        local_defaults.filter(
            versions__status="PUBLISHED",
            versions__translations__locale="en",
        ).values_list("versions__translations__name", flat=True)
    )
    assert copied_names == set(names)
    assert all(
        design.versions.filter(status=DesignVersion.Status.PUBLISHED).count() == 1
        and design.versions.filter(status=DesignVersion.Status.DRAFT).count() == 1
        for design in local_defaults.distinct()
    )
    assert not GarmentVariant.objects.filter(tenant=shop, family=local_family).exists()
