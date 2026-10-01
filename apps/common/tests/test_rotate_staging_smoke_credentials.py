import io
import os
import secrets
from unittest.mock import patch

import pytest
from django.core.management import CommandError, call_command
from django.test import override_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from apps.accounts.models import User
from apps.tenants.models import (
    MembershipWorkFunction,
    Supplier,
    Tenant,
    TenantMember,
)
from apps.common.management.commands.bootstrap_staging_smoke import (
    MAIN_EMAIL,
    PASSWORD_VARIABLES,
    SHOP_FIXTURES,
)


pytestmark = pytest.mark.django_db


def credential_set(prefix="new"):
    return {
        variable: f"{prefix}-{secrets.token_urlsafe(48)}"
        for variable in PASSWORD_VARIABLES.values()
    }


def configure_rotation(env, *, environment="staging", database_name="sgtp_staging"):
    env = {"STAGING_SMOKE_ROTATE_CREDENTIALS_ENABLED": "true", **env}
    return (
        patch.dict(os.environ, env, clear=False),
        override_settings(ENVIRONMENT=environment),
        patch(
            "apps.common.management.commands.rotate_staging_smoke_credentials.Command._configured_database_name",
            return_value=database_name,
        ),
    )


def bootstrap_fixture():
    old = credential_set("old")
    bootstrap_env = {**old, "STAGING_SMOKE_BOOTSTRAP_ENABLED": "true"}
    with (
        patch.dict(os.environ, bootstrap_env, clear=False),
        override_settings(ENVIRONMENT="staging"),
        patch(
            "apps.common.management.commands.bootstrap_staging_smoke.Command._configured_database_name",
            return_value="sgtp_staging",
        ),
    ):
        call_command("bootstrap_staging_smoke", confirm_staging_bootstrap=True)
    return old


def run_rotation(
    env, *, confirmed=True, environment="staging", database_name="sgtp_staging"
):
    output = io.StringIO()
    stderr = io.StringIO()
    contexts = configure_rotation(
        env, environment=environment, database_name=database_name
    )
    with contexts[0], contexts[1], contexts[2]:
        call_command(
            "rotate_staging_smoke_credentials",
            confirm_staging_credential_rotation=confirmed,
            stdout=output,
            stderr=stderr,
        )
    return output.getvalue(), stderr.getvalue()


def fixture_users():
    return [
        User.objects.get(email=MAIN_EMAIL),
        *[User.objects.get(email=fixture["email"]) for fixture in SHOP_FIXTURES],
    ]


def fixture_counts():
    return (
        Supplier.objects.count(),
        Tenant.objects.all_with_deleted()
        .filter(slug__startswith="sgtp-smoke-")
        .count(),
        User.objects.filter(email__startswith="sgtp-smoke-").count(),
        TenantMember.objects.all_with_deleted()
        .filter(tenant__slug__startswith="sgtp-smoke-")
        .count(),
        MembershipWorkFunction.objects.all_with_deleted()
        .filter(membership__tenant__slug__startswith="sgtp-smoke-")
        .count(),
    )


def assert_new_credentials(env):
    users = fixture_users()
    for user, role in zip(users, ("main", "shop_a", "shop_b"), strict=True):
        assert user.check_password(env[PASSWORD_VARIABLES[role]])


@pytest.mark.parametrize("environment", ["dev", "prod", "production", "test", None])
def test_rotation_rejects_non_staging_before_mutation(environment):
    before = fixture_counts()
    env = credential_set()
    with pytest.raises(CommandError, match="only in staging"):
        run_rotation(env, environment=environment)
    assert fixture_counts() == before


def test_rotation_rejects_wrong_database_before_mutation():
    before = fixture_counts()
    with pytest.raises(CommandError, match="sgtp_staging"):
        run_rotation(credential_set(), database_name="sgtp_production")
    assert fixture_counts() == before


def test_rotation_requires_explicit_cli_confirmation():
    old = bootstrap_fixture()
    before_hashes = [user.password for user in fixture_users()]
    with pytest.raises(CommandError, match="--confirm-staging-credential-rotation"):
        run_rotation(credential_set(), confirmed=False)
    assert [user.password for user in fixture_users()] == before_hashes
    assert_new_credentials(old)


@pytest.mark.parametrize("switch", ["false", "no", ""])
def test_rotation_requires_explicit_enable_switch(switch):
    old = bootstrap_fixture()
    before_hashes = [user.password for user in fixture_users()]
    env = credential_set()
    env["STAGING_SMOKE_ROTATE_CREDENTIALS_ENABLED"] = switch
    with pytest.raises(CommandError, match="not enabled"):
        run_rotation(env)
    assert [user.password for user in fixture_users()] == before_hashes
    assert_new_credentials(old)


@pytest.mark.parametrize("role", ["main", "shop_a", "shop_b"])
def test_rotation_requires_every_secret(role):
    old = bootstrap_fixture()
    before_hashes = [user.password for user in fixture_users()]
    env = credential_set()
    env[PASSWORD_VARIABLES[role]] = ""
    with pytest.raises(CommandError, match=PASSWORD_VARIABLES[role]):
        run_rotation(env)
    assert [user.password for user in fixture_users()] == before_hashes
    assert_new_credentials(old)


def test_rotation_rejects_weak_secret_before_mutation():
    old = bootstrap_fixture()
    before_hashes = [user.password for user in fixture_users()]
    env = credential_set()
    env[PASSWORD_VARIABLES["shop_b"]] = "weak-secret"
    with pytest.raises(CommandError, match="at least 40 characters"):
        run_rotation(env)
    assert [user.password for user in fixture_users()] == before_hashes
    assert_new_credentials(old)


def test_rotation_rejects_missing_fixture():
    before = fixture_counts()
    with pytest.raises(CommandError, match="fixture is missing"):
        run_rotation(credential_set())
    assert fixture_counts() == before


def test_rotation_rejects_partial_fixture_without_repair():
    old = bootstrap_fixture()
    Tenant.objects.filter(slug=SHOP_FIXTURES[1]["slug"]).update(
        slug="sgtp-smoke-shop-b-renamed"
    )
    before = fixture_counts()
    with pytest.raises(CommandError, match="fixture is missing, partial"):
        run_rotation(credential_set())
    assert fixture_counts() == before
    assert_new_credentials(old)


@pytest.mark.parametrize(
    "inconsistency",
    ["inactive_shop", "shop_metadata", "wrong_role", "missing_function"],
)
def test_rotation_rejects_inconsistent_fixture_without_mutation(inconsistency):
    old = bootstrap_fixture()
    fixture = SHOP_FIXTURES[0]
    shop = Tenant.objects.get(slug=fixture["slug"])
    membership = TenantMember.objects.get(tenant=shop)
    if inconsistency == "inactive_shop":
        Tenant.objects.filter(pk=shop.pk).update(is_active=False)
    elif inconsistency == "shop_metadata":
        Tenant.objects.filter(pk=shop.pk).update(contact_phone="+12025550999")
    elif inconsistency == "wrong_role":
        TenantMember.objects.filter(pk=membership.pk).update(role="STAFF")
    else:
        MembershipWorkFunction.objects.filter(membership=membership).delete()
    before_hashes = [user.password for user in fixture_users()]
    with pytest.raises(CommandError, match="inconsistent"):
        run_rotation(credential_set())
    assert [user.password for user in fixture_users()] == before_hashes
    assert_new_credentials(old)


def test_rotation_changes_only_existing_fixture_passwords_and_revokes_sessions():
    old = bootstrap_fixture()
    users = fixture_users()
    new = credential_set()
    before_counts = fixture_counts()
    before_identity = [
        (
            u.pk,
            u.user_code,
            u.email,
            u.phone,
            u.first_name,
            u.owning_shop_id,
            u.is_active,
            u.is_staff,
            u.is_superuser,
            u.must_change_password,
            u.auth_version,
        )
        for u in users
    ]
    refreshes = [RefreshToken.for_user(user) for user in users]
    output, stderr = run_rotation(new)

    assert "rotated" in output
    assert stderr == ""
    assert not any(secret in output + stderr for secret in new.values())
    assert fixture_counts() == before_counts
    users = fixture_users()
    after_identity = [
        (
            u.pk,
            u.user_code,
            u.email,
            u.phone,
            u.first_name,
            u.owning_shop_id,
            u.is_active,
            u.is_staff,
            u.is_superuser,
            u.must_change_password,
            u.auth_version,
        )
        for u in users
    ]
    for before, after in zip(before_identity, after_identity, strict=True):
        assert before[:-1] == after[:-1]
        assert after[-1] == before[-1] + 1
    for index, (user, role, old_refresh) in enumerate(
        zip(users, ("main", "shop_a", "shop_b"), refreshes, strict=True)
    ):
        assert user.check_password(new[PASSWORD_VARIABLES[role]])
        assert not user.check_password(old[PASSWORD_VARIABLES[role]])
        assert user.auth_version == before_identity[index][-1] + 1
        assert BlacklistedToken.objects.filter(token__jti=old_refresh["jti"]).exists()


def test_rotation_is_safe_on_restart_and_does_not_increment_auth_version_twice():
    bootstrap_fixture()
    new = credential_set()
    first_output, _ = run_rotation(new)
    versions = [user.auth_version for user in fixture_users()]
    counts = fixture_counts()
    second_output, _ = run_rotation(new)
    assert "already current" in second_output
    assert "rotated" in first_output
    assert [user.auth_version for user in fixture_users()] == versions
    assert fixture_counts() == counts


def test_partial_already_current_secret_set_fails_without_any_rotation():
    bootstrap_fixture()
    new = credential_set()
    users = fixture_users()
    users[0].set_password(new[PASSWORD_VARIABLES["main"]])
    users[0].save(update_fields=["password"])
    hashes = [user.password for user in fixture_users()]
    with pytest.raises(CommandError, match="Only part"):
        run_rotation(new)
    assert [user.password for user in fixture_users()] == hashes


def test_fixture_entities_and_assignments_are_never_duplicated_by_rotation():
    old = bootstrap_fixture()
    before = fixture_counts()
    new = credential_set()
    run_rotation(new)
    assert fixture_counts() == before
    assert_new_credentials(new)
    assert not any(
        user.check_password(old[PASSWORD_VARIABLES[role]])
        for user, role in zip(
            fixture_users(), ("main", "shop_a", "shop_b"), strict=True
        )
    )
