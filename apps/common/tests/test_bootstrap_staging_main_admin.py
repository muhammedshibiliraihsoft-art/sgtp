import io
import os
import secrets
from unittest.mock import patch

import pytest
from django.core.management import CommandError, call_command
from django.test import override_settings

from apps.accounts.models import User


BOOTSTRAP_ENV = {
    "DJANGO_ENV": "staging",
    "STAGING_MAIN_ADMIN_BOOTSTRAP_ENABLED": "true",
    "STAGING_MAIN_ADMIN_EMAIL": "shibili.test@example.com",
    "STAGING_MAIN_ADMIN_FIRST_NAME": "Shibili",
    "STAGING_MAIN_ADMIN_PHONE": "+916282911854",
    "STAGING_MAIN_ADMIN_PASSWORD": secrets.token_urlsafe(48),
}
pytestmark = pytest.mark.django_db


def run_bootstrap(env=None, *, confirmed=True, database_name="sgtp_staging"):
    output = io.StringIO()
    values = {**BOOTSTRAP_ENV, **(env or {})}
    with (
        patch.dict(os.environ, values, clear=False),
        override_settings(ENVIRONMENT="staging"),
        patch(
            "apps.common.management.commands.bootstrap_staging_main_admin.Command._configured_database_name",
            return_value=database_name,
        ),
    ):
        call_command(
            "bootstrap_staging_main_admin",
            confirm_staging_main_admin_bootstrap=confirmed,
            stdout=output,
        )
    return output.getvalue()


def test_creates_one_main_admin_and_requires_password_change():
    password = BOOTSTRAP_ENV["STAGING_MAIN_ADMIN_PASSWORD"]
    output = run_bootstrap()

    user = User.objects.get(email="shibili.test@example.com")
    assert user.first_name == "Shibili"
    assert user.phone == "+916282911854"
    assert user.is_active and user.is_staff and user.is_superuser
    assert user.owning_shop_id is None
    assert user.must_change_password
    assert user.check_password(password)
    assert User.objects.filter(is_superuser=True).count() == 1
    assert "created" in output
    assert password not in output


def test_existing_contact_collision_is_a_noop():
    existing = User.objects.create_superuser(
        email="different@example.com",
        password=secrets.token_urlsafe(48),
        first_name="Existing",
        phone="+916282911854",
    )

    output = run_bootstrap()

    existing.refresh_from_db()
    assert existing.email == "different@example.com"
    assert User.objects.filter(email="shibili.test@example.com").count() == 0
    assert "no account changes were made" in output


@pytest.mark.parametrize(
    ("env", "database_name", "environment", "confirmed"),
    [
        (
            {"STAGING_MAIN_ADMIN_BOOTSTRAP_ENABLED": "false"},
            "sgtp_staging",
            "staging",
            True,
        ),
        ({}, "sgtp_production", "staging", True),
        ({"DJANGO_ENV": "production"}, "sgtp_staging", "staging", True),
        ({}, "sgtp_staging", "production", True),
        ({}, "sgtp_staging", "staging", False),
    ],
)
def test_guards_refuse_creation_without_mutation(
    env, database_name, environment, confirmed
):
    before = User.objects.count()
    with (
        patch.dict(os.environ, {**BOOTSTRAP_ENV, **env}, clear=False),
        override_settings(ENVIRONMENT=environment),
        patch(
            "apps.common.management.commands.bootstrap_staging_main_admin.Command._configured_database_name",
            return_value=database_name,
        ),
        pytest.raises(CommandError),
    ):
        call_command(
            "bootstrap_staging_main_admin",
            confirm_staging_main_admin_bootstrap=confirmed,
        )
    assert User.objects.count() == before


def test_weak_password_is_rejected_without_mutation():
    before = User.objects.count()
    with pytest.raises(CommandError, match="at least 40 characters"):
        run_bootstrap({"STAGING_MAIN_ADMIN_PASSWORD": "weak"})
    assert User.objects.count() == before


def test_repeated_run_never_resets_or_promotes_existing_user():
    run_bootstrap()
    user = User.objects.get(email="shibili.test@example.com")
    original_password = BOOTSTRAP_ENV["STAGING_MAIN_ADMIN_PASSWORD"]
    changed_config = {
        "STAGING_MAIN_ADMIN_PASSWORD": secrets.token_urlsafe(48),
        "STAGING_MAIN_ADMIN_FIRST_NAME": "Changed Name",
    }

    output = run_bootstrap(changed_config)

    user.refresh_from_db()
    assert user.first_name == "Shibili"
    assert user.check_password(original_password)
    assert not user.check_password(changed_config["STAGING_MAIN_ADMIN_PASSWORD"])
    assert "no account changes were made" in output
