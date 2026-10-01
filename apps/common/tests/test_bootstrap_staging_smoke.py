import io
import os
import secrets
from unittest.mock import patch

import pytest
from django.core.management import CommandError, call_command
from django.test import override_settings

from apps.accounts.models import User
from apps.tenants.models import (
    MembershipWorkFunction,
    ShopRole,
    Supplier,
    Tenant,
    TenantMember,
)


PASSWORD_ENV = {
    "STAGING_SMOKE_MAIN_PASSWORD": None,
    "STAGING_SMOKE_SHOP_A_ADMIN_PASSWORD": None,
    "STAGING_SMOKE_SHOP_B_ADMIN_PASSWORD": None,
}
SHOP_SLUGS = ("sgtp-smoke-shop-a", "sgtp-smoke-shop-b")
USER_EMAILS = (
    "sgtp-smoke-main@staging.invalid",
    "sgtp-smoke-shop-a-admin@staging.invalid",
    "sgtp-smoke-shop-b-admin@staging.invalid",
)
pytestmark = pytest.mark.django_db


def bootstrap_env(**overrides):
    values = {key: secrets.token_urlsafe(48) for key in PASSWORD_ENV}
    values["STAGING_SMOKE_BOOTSTRAP_ENABLED"] = "true"
    values.update(overrides)
    return values


def run_bootstrap(env, *, confirmed=True, database_name="sgtp_staging"):
    output = io.StringIO()
    with (
        patch.dict(os.environ, env, clear=False),
        override_settings(ENVIRONMENT="staging"),
        patch(
            "apps.common.management.commands.bootstrap_staging_smoke.Command._configured_database_name",
            return_value=database_name,
        ),
    ):
        call_command(
            "bootstrap_staging_smoke",
            confirm_staging_bootstrap=confirmed,
            stdout=output,
        )
    return output.getvalue()


def marker_counts():
    return (
        Tenant.objects.all_with_deleted().filter(slug__in=SHOP_SLUGS).count(),
        User.objects.filter(email__in=USER_EMAILS).count(),
        MembershipWorkFunction.objects.count(),
    )


@pytest.mark.parametrize("environment", ["dev", "prod", "production", "test", None])
def test_bootstrap_rejects_non_staging_environments_without_mutation(environment):
    before = marker_counts()
    with (
        patch.dict(os.environ, bootstrap_env(), clear=False),
        override_settings(ENVIRONMENT=environment),
        patch(
            "apps.common.management.commands.bootstrap_staging_smoke.Command._configured_database_name",
            return_value="sgtp_staging",
        ),
        pytest.raises(CommandError),
    ):
        call_command("bootstrap_staging_smoke", confirm_staging_bootstrap=True)
    assert marker_counts() == before


def test_bootstrap_rejects_wrong_database_without_mutation():
    before = marker_counts()
    with pytest.raises(CommandError, match="sgtp_staging"):
        run_bootstrap(bootstrap_env(), database_name="sgtp_production")
    assert marker_counts() == before


def test_bootstrap_requires_explicit_confirmation_without_mutation():
    before = marker_counts()
    with pytest.raises(CommandError, match="--confirm-staging-bootstrap"):
        run_bootstrap(bootstrap_env(), confirmed=False)
    assert marker_counts() == before


def test_bootstrap_requires_explicit_enable_switch_without_mutation():
    before = marker_counts()
    env = bootstrap_env(STAGING_SMOKE_BOOTSTRAP_ENABLED="false")
    with pytest.raises(CommandError, match="not explicitly enabled"):
        run_bootstrap(env)
    assert marker_counts() == before


def test_bootstrap_requires_all_credential_secrets_without_mutation():
    before = marker_counts()
    env = bootstrap_env()
    env["STAGING_SMOKE_SHOP_B_ADMIN_PASSWORD"] = ""
    with pytest.raises(CommandError, match="STAGING_SMOKE_SHOP_B_ADMIN_PASSWORD"):
        run_bootstrap(env)
    assert marker_counts() == before


def test_bootstrap_rejects_weak_secrets_without_mutation():
    before = marker_counts()
    env = bootstrap_env(STAGING_SMOKE_MAIN_PASSWORD="short")
    with pytest.raises(CommandError, match="at least 40 characters"):
        run_bootstrap(env)
    assert marker_counts() == before


def test_successful_bootstrap_creates_valid_fixture_without_printing_passwords():
    env = bootstrap_env()
    output = run_bootstrap(env)
    supplier = Supplier.objects.get(singleton_lock=True)
    main = User.objects.get(email=USER_EMAILS[0])

    assert supplier.is_active
    assert main.is_superuser and main.is_active and main.owning_shop_id is None
    assert main.check_password(env["STAGING_SMOKE_MAIN_PASSWORD"])
    assert "Synthetic Main Supplier created" in output
    for secret in env.values():
        assert secret not in output

    shops = list(Tenant.objects.filter(slug__in=SHOP_SLUGS).order_by("slug"))
    assert len(shops) == 2
    assert all(shop.supplier_id == supplier.pk and shop.is_active for shop in shops)
    assert [shop.user_count for shop in shops] == [1, 1]
    for index, shop in enumerate(shops, start=1):
        user = User.objects.get(email=USER_EMAILS[index])
        membership = TenantMember.objects.get(tenant=shop, user=user)
        assert user.owning_shop_id == shop.pk
        assert user.is_active and not user.is_superuser
        assert user.phone == f"+1202555010{index}"
        assert user.email == USER_EMAILS[index]
        assert not user.must_change_password
        assert user.check_password(
            env[f"STAGING_SMOKE_SHOP_{'A' if index == 1 else 'B'}_ADMIN_PASSWORD"]
        )
        assert membership.role == ShopRole.ADMIN and membership.is_active
        assert (
            TenantMember.objects.filter(
                tenant=shop,
                role=ShopRole.ADMIN,
                is_active=True,
                deleted__isnull=True,
                user__is_active=True,
            ).count()
            == 1
        )
        assert (
            MembershipWorkFunction.objects.filter(
                membership=membership, deleted__isnull=True
            ).count()
            == 1
        )


def test_bootstrap_is_idempotent_and_does_not_duplicate_fixture():
    env = bootstrap_env()
    run_bootstrap(env)
    before = marker_counts()
    output = run_bootstrap(env)
    assert marker_counts() == before
    assert "already exist and are valid; no changes made" in output
    for secret in env.values():
        assert secret not in output


def test_bootstrap_rejects_changed_secret_for_existing_fixture_without_mutation():
    env = bootstrap_env()
    run_bootstrap(env)
    before = marker_counts()
    env["STAGING_SMOKE_SHOP_A_ADMIN_PASSWORD"] = secrets.token_urlsafe(48)
    with pytest.raises(CommandError, match="fixture is inconsistent"):
        run_bootstrap(env)
    assert marker_counts() == before


def test_bootstrap_rejects_partial_fixture_without_creating_more_data():
    supplier = Supplier.objects.get(singleton_lock=True)
    Tenant.objects.create(
        supplier=supplier,
        name="SGTP Synthetic Smoke Shop A",
        slug=SHOP_SLUGS[0],
        max_users=5,
    )
    before = marker_counts()
    with pytest.raises(CommandError, match="partial synthetic fixture"):
        run_bootstrap(bootstrap_env())
    assert marker_counts() == before


def test_fixture_bootstrap_requires_existing_singleton_supplier_without_mutation():
    before = marker_counts()
    with patch(
        "apps.common.management.commands.bootstrap_staging_smoke.Supplier.objects"
    ) as manager:
        manager.select_for_update.return_value.get.side_effect = Supplier.DoesNotExist
        with (
            patch.dict(os.environ, bootstrap_env(), clear=False),
            override_settings(ENVIRONMENT="staging"),
            patch(
                "apps.common.management.commands.bootstrap_staging_smoke.Command._configured_database_name",
                return_value="sgtp_staging",
            ),
            pytest.raises(CommandError, match="DoesNotExist"),
        ):
            call_command("bootstrap_staging_smoke", confirm_staging_bootstrap=True)
    assert marker_counts() == before
