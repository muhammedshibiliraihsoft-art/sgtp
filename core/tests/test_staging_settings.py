import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.management import CommandError, call_command
from django.test import override_settings


ROOT = Path(__file__).resolve().parents[2]
BASE_ENV = {
    "DJANGO_ENV": "staging",
    "DJANGO_SECRET_KEY": "staging-test-secret-not-used-outside-tests-and-long-enough",
    "DJANGO_DEBUG": "False",
    "DJANGO_ALLOWED_HOSTS": "api-staging.birky.com",
    "DJANGO_CORS_ALLOWED_ORIGINS": "https://staging.birky.com",
    "DJANGO_CSRF_TRUSTED_ORIGINS": "https://staging.birky.com",
    "DB_NAME": "sgtp_staging",
    "DB_USER": "staging_user",
    "DB_PASSWORD": "test-only-password",
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "R2_BUCKET_NAME": "birkos-staging-private",
    "R2_ENDPOINT": "https://example-account.r2.cloudflarestorage.com",
    "R2_ACCESS_KEY_ID": "test-r2-access-key",
    "R2_SECRET_ACCESS_KEY": "test-r2-secret-key",
    "R2_REGION": "auto",
}
SETTINGS_JSON = """
import json
from django.conf import settings
print(json.dumps({
    "debug": settings.DEBUG,
    "hosts": settings.ALLOWED_HOSTS,
    "cors": settings.CORS_ALLOWED_ORIGINS,
    "cors_all": settings.CORS_ALLOW_ALL_ORIGINS,
    "credentials": settings.CORS_ALLOW_CREDENTIALS,
    "csrf": settings.CSRF_TRUSTED_ORIGINS,
    "session_secure": settings.SESSION_COOKIE_SECURE,
    "csrf_secure": settings.CSRF_COOKIE_SECURE,
    "csrf_httponly": settings.CSRF_COOKIE_HTTPONLY,
    "session_samesite": settings.SESSION_COOKIE_SAMESITE,
    "csrf_samesite": settings.CSRF_COOKIE_SAMESITE,
    "email_backend": settings.EMAIL_BACKEND,
    "environment": settings.ENVIRONMENT,
    "database": settings.DATABASES["default"],
}))
"""


def run_settings(extra=None, remove=()):
    env = os.environ.copy()
    env.update(BASE_ENV)
    env.pop("DATABASE_URL", None)
    env.update(extra or {})
    for name in remove:
        env.pop(name, None)
    return subprocess.run(
        [sys.executable, "-c", SETTINGS_JSON],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_staging_settings_are_secure_and_accept_only_approved_origins():
    result = run_settings(
        {"RENDER_EXTERNAL_HOSTNAME": "birky-staging-api.onrender.com"}
    )

    assert result.returncode == 0, result.stderr
    settings = json.loads(result.stdout)
    assert settings["environment"] == "staging"
    assert settings["debug"] is False
    assert settings["hosts"] == [
        "api-staging.birky.com",
        "birky-staging-api.onrender.com",
    ]
    assert settings["cors"] == ["https://staging.birky.com"]
    assert settings["cors_all"] is False
    assert settings["credentials"] is True
    assert settings["csrf"] == ["https://staging.birky.com"]
    assert settings["session_secure"] is True
    assert settings["csrf_secure"] is True
    assert settings["csrf_httponly"] is False
    assert settings["session_samesite"] == "Lax"
    assert settings["csrf_samesite"] == "Lax"
    assert settings["email_backend"] == "django.core.mail.backends.dummy.EmailBackend"


@pytest.mark.parametrize(
    "extra",
    [
        {"DJANGO_DEBUG": "True"},
        {"DJANGO_CORS_ALLOWED_ORIGINS": "*"},
        {
            "DJANGO_CORS_ALLOWED_ORIGINS": "https://staging.birky.com,http://localhost:3000"
        },
        {"DJANGO_CSRF_TRUSTED_ORIGINS": "https://*.birky.com"},
        {"RENDER_EXTERNAL_HOSTNAME": "*.onrender.com"},
        {"DJANGO_ALLOWED_HOSTS": "api.birky.com"},
        {"DJANGO_EMAIL_BACKEND": "django.core.mail.backends.console.EmailBackend"},
    ],
)
def test_staging_settings_fail_closed_on_insecure_values(extra):
    result = run_settings(extra)

    assert result.returncode != 0
    assert "Traceback" in result.stderr
    assert "ImproperlyConfigured" in result.stderr
    assert "test-only-password" not in result.stderr


def test_staging_settings_require_csrf_origin_configuration():
    result = run_settings(remove=("DJANGO_CSRF_TRUSTED_ORIGINS",))

    assert result.returncode != 0
    assert "DJANGO_CSRF_TRUSTED_ORIGINS" in result.stderr


def test_staging_settings_require_private_r2_storage():
    result = run_settings(
        remove=(
            "R2_BUCKET_NAME",
            "R2_ENDPOINT",
            "R2_ACCESS_KEY_ID",
            "R2_SECRET_ACCESS_KEY",
        )
    )

    assert result.returncode != 0
    assert "Staging requires private R2 storage" in result.stderr
    assert "test-r2-secret-key" not in result.stderr


def test_settings_selector_accepts_staging_database_connection_url():
    result = run_settings(
        {
            "DATABASE_URL": "postgresql://stage%40user:p%40ss@private-db:5432/sgtp_staging",
        }
    )

    assert result.returncode == 0, result.stderr
    database = json.loads(result.stdout)["database"]
    assert database == {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "sgtp_staging",
        "USER": "stage@user",
        "PASSWORD": "p@ss",
        "HOST": "private-db",
        "PORT": "5432",
    }


@pytest.mark.parametrize(
    "database_url",
    [
        "",
        "sqlite:///tmp/db.sqlite3",
        "postgresql://user@host:5432/db",
        "postgresql://user:pass@host/db?sslmode=require",
        "postgresql://user:pass@host/db#fragment",
    ],
)
def test_invalid_database_url_fails_without_echoing_credentials(database_url):
    result = run_settings({"DATABASE_URL": database_url})

    assert result.returncode != 0
    assert "ImproperlyConfigured" in result.stderr
    assert "pass" not in result.stderr


def test_staging_reset_requires_explicit_flag_and_exact_staging_database():
    with (
        override_settings(
            ENVIRONMENT="staging",
            DATABASES={"default": {"NAME": "sgtp_staging"}},
        ),
        patch("apps.common.management.commands.reset_staging.call_command") as flush,
    ):
        with pytest.raises(CommandError, match="--confirm-staging-reset"):
            call_command("reset_staging")
        flush.assert_not_called()

        call_command("reset_staging", confirm_staging_reset=True)

    flush.assert_called_once_with(
        "flush", interactive=False, database="default", verbosity=1
    )


@pytest.mark.parametrize(
    ("environment", "database_name"),
    [("dev", "sgtp_staging"), ("staging", "production"), ("prod", "production")],
)
def test_staging_reset_refuses_non_staging_or_wrong_database(
    environment, database_name
):
    with (
        override_settings(
            ENVIRONMENT=environment,
            DATABASES={"default": {"NAME": database_name}},
        ),
        patch("apps.common.management.commands.reset_staging.call_command") as flush,
    ):
        with pytest.raises(CommandError):
            call_command("reset_staging", confirm_staging_reset=True)
        flush.assert_not_called()
