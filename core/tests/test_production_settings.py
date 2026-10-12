import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BASE_ENV = {
    "DJANGO_SETTINGS_MODULE": "backend.config.settings.prod",
    "DJANGO_ENV": "production",
    "DJANGO_SECRET_KEY": "production-test-secret-not-used-outside-tests-and-long-enough",
    "DJANGO_DEBUG": "False",
    "DJANGO_ALLOWED_HOSTS": "api.example.com",
    "DJANGO_CORS_ALLOWED_ORIGINS": "https://app.example.com",
    "DJANGO_CSRF_TRUSTED_ORIGINS": "https://app.example.com",
    "DB_NAME": "sgtp_production_test",
    "DB_USER": "production_test_user",
    "DB_PASSWORD": "test-only-password",
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DJANGO_DB_SSLMODE": "",
    "DJANGO_DB_SSLROOTCERT": "",
    "R2_BUCKET_NAME": "birkos-production-test",
    "R2_ENDPOINT": "https://example-account.r2.cloudflarestorage.com",
    "R2_ACCESS_KEY_ID": "test-r2-access-key",
    "R2_SECRET_ACCESS_KEY": "test-r2-secret-key",
    "R2_REGION": "auto",
}
SETTINGS_JSON = """
import json
from django.conf import settings
print(json.dumps({
    "environment": settings.ENVIRONMENT,
    "debug": settings.DEBUG,
    "hosts": settings.ALLOWED_HOSTS,
    "cors": settings.CORS_ALLOWED_ORIGINS,
    "cors_all": settings.CORS_ALLOW_ALL_ORIGINS,
    "cors_credentials": settings.CORS_ALLOW_CREDENTIALS,
    "csrf": settings.CSRF_TRUSTED_ORIGINS,
    "r2": settings.R2_ENABLED,
    "db_engine": settings.DATABASES["default"]["ENGINE"],
    "db_name": settings.DATABASES["default"]["NAME"],
    "db_host": settings.DATABASES["default"]["HOST"],
    "db_sslmode": settings.DATABASES["default"].get("OPTIONS", {}).get("sslmode"),
    "db_sslrootcert": settings.DATABASES["default"].get("OPTIONS", {}).get("sslrootcert"),
    "storage_endpoint": settings.R2_ENDPOINT,
    "storage_bucket": settings.R2_BUCKET_NAME,
    "private_media_backend": settings.STORAGES["private_media"]["BACKEND"],
    "secret_key_configured": bool(settings.SECRET_KEY),
    "proxy_ssl_header": settings.SECURE_PROXY_SSL_HEADER,
    "ssl_redirect": settings.SECURE_SSL_REDIRECT,
    "session_secure": settings.SESSION_COOKIE_SECURE,
    "csrf_secure": settings.CSRF_COOKIE_SECURE,
    "session_samesite": settings.SESSION_COOKIE_SAMESITE,
    "csrf_samesite": settings.CSRF_COOKIE_SAMESITE,
    "hsts_seconds": settings.SECURE_HSTS_SECONDS,
    "hsts_subdomains": settings.SECURE_HSTS_INCLUDE_SUBDOMAINS,
    "hsts_preload": settings.SECURE_HSTS_PRELOAD,
}))
"""


def run_settings(extra=None):
    env = os.environ.copy()
    env.update(BASE_ENV)
    env.pop("DATABASE_URL", None)
    env["RENDER_EXTERNAL_HOSTNAME"] = ""
    env.update(extra or {})
    return subprocess.run(
        [sys.executable, "-c", SETTINGS_JSON],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_production_settings_are_secure_and_use_explicit_storage_and_origins():
    result = run_settings({"RENDER_EXTERNAL_HOSTNAME": "birky-prod-api.onrender.com"})

    assert result.returncode == 0, result.stderr
    settings = json.loads(result.stdout)
    assert settings["environment"] == "production"
    assert settings["debug"] is False
    assert settings["hosts"] == ["api.example.com"]
    assert settings["cors"] == ["https://app.example.com"]
    assert settings["cors_all"] is False
    assert settings["cors_credentials"] is True
    assert settings["csrf"] == ["https://app.example.com"]
    assert settings["r2"] is True
    assert settings["db_engine"] == "django.db.backends.postgresql"
    assert (
        settings["private_media_backend"]
        == "apps.catalog.storage.PrivateReferenceStorage"
    )
    assert settings["secret_key_configured"] is True
    assert settings["proxy_ssl_header"] == ["HTTP_X_FORWARDED_PROTO", "https"]
    assert settings["ssl_redirect"] is True
    assert settings["session_secure"] is True
    assert settings["csrf_secure"] is True
    assert settings["session_samesite"] == "Lax"
    assert settings["csrf_samesite"] == "Lax"
    assert settings["hsts_seconds"] == 31536000
    assert settings["hsts_subdomains"] is True
    assert settings["hsts_preload"] is True


@pytest.mark.parametrize(
    "extra,expected_error",
    [
        ({"DJANGO_DEBUG": "True"}, "Production requires DJANGO_DEBUG=False"),
        ({"DJANGO_ALLOWED_HOSTS": "*"}, "explicit hostnames"),
        ({"DJANGO_ALLOWED_HOSTS": ""}, "explicit hostnames"),
        ({"DJANGO_CORS_ALLOWED_ORIGINS": "http://app.example.com"}, "HTTPS origins"),
        ({"DJANGO_CSRF_TRUSTED_ORIGINS": "https://*.example.com"}, "HTTPS origins"),
        ({"DJANGO_SECRET_KEY": ""}, "strong DJANGO_SECRET_KEY"),
        ({"DJANGO_SECRET_KEY": "too-short"}, "strong DJANGO_SECRET_KEY"),
        ({"DB_HOST": ""}, "Production requires complete PostgreSQL configuration"),
        ({"DB_PASSWORD": ""}, "Production requires complete PostgreSQL configuration"),
        (
            {"DB_HOST": "managed-db.example.com"},
            "Remote production PostgreSQL requires DJANGO_DB_SSLMODE",
        ),
        ({"DJANGO_DB_SSLMODE": "disable"}, "DJANGO_DB_SSLMODE must be"),
        (
            {"DJANGO_DB_SSLROOTCERT": "/certs/ca.pem"},
            "Database SSL root certificate requires",
        ),
        (
            {
                "DATABASE_URL": "postgresql://user:password@remote.example.com:5432/db?sslmode=disable",
            },
            "DATABASE_URL has an unsafe sslmode",
        ),
        (
            {
                "DATABASE_URL": "postgresql://user:password@remote.example.com:5432/db?connect_timeout=0",
            },
            "DATABASE_URL has unsupported options",
        ),
        (
            {
                "DATABASE_URL": "postgresql://user:password@remote.example.com:5432/db?sslmode=require&sslmode=verify-full",
            },
            "DATABASE_URL has unsupported options",
        ),
        (
            {
                "DATABASE_URL": "postgresql://user:password@remote.example.com:5432/db?sslmode=require&sslrootcert=%2Fcerts%2Fca.pem",
            },
            "Database SSL root certificate requires",
        ),
        (
            {
                "DJANGO_SETTINGS_MODULE": "backend.config.settings.prod",
                "DJANGO_ENV": "staging",
                "R2_BUCKET_NAME": "",
                "R2_ENDPOINT": "",
                "R2_ACCESS_KEY_ID": "",
                "R2_SECRET_ACCESS_KEY": "",
            },
            "Production requires private R2 storage",
        ),
        (
            {
                "R2_BUCKET_NAME": "",
                "R2_ENDPOINT": "",
                "R2_ACCESS_KEY_ID": "",
                "R2_SECRET_ACCESS_KEY": "",
            },
            "Production requires private R2 storage",
        ),
        (
            {
                "DJANGO_ENV": "development",
                "R2_BUCKET_NAME": "",
                "R2_ENDPOINT": "",
                "R2_ACCESS_KEY_ID": "",
                "R2_SECRET_ACCESS_KEY": "",
            },
            "Production requires private R2 storage",
        ),
        (
            {"R2_SECRET_ACCESS_KEY": ""},
            "R2_BUCKET_NAME, R2_ENDPOINT, R2_ACCESS_KEY_ID, and R2_SECRET_ACCESS_KEY must be configured together",
        ),
    ],
)
def test_production_settings_fail_closed_on_unsafe_or_missing_values(
    extra, expected_error
):
    result = run_settings(extra)

    assert result.returncode != 0
    assert expected_error in result.stderr
    assert "test-only-password" not in result.stderr
    assert "test-r2-secret-key" not in result.stderr


@pytest.mark.parametrize(
    "variable",
    ["DJANGO_CORS_ALLOWED_ORIGINS", "DJANGO_CSRF_TRUSTED_ORIGINS"],
)
def test_production_settings_require_both_browser_origin_lists(variable):
    # A local .env.prod may supply values when a variable is absent, so pass an
    # explicit empty value to verify the fail-closed behavior deterministically.
    result = run_settings({variable: ""})

    assert result.returncode != 0
    assert variable in result.stderr


@pytest.mark.parametrize(
    "query,expected_mode,expected_cert",
    [
        ("sslmode=require", "require", None),
        (
            "sslmode=verify-full&sslrootcert=%2Fcerts%2Fca.pem",
            "verify-full",
            "/certs/ca.pem",
        ),
    ],
)
def test_postgresql_url_tls_options_are_used_without_an_environment_override(
    query, expected_mode, expected_cert
):
    result = run_settings(
        {
            "DATABASE_URL": f"postgresql://user:password@managed-db.example.com:25060/db?{query}",
        }
    )

    assert result.returncode == 0, result.stderr
    configured = json.loads(result.stdout)
    assert configured["db_host"] == "managed-db.example.com"
    assert configured["db_sslmode"] == expected_mode
    assert configured["db_sslrootcert"] == expected_cert


def test_explicit_database_tls_environment_overrides_url_sslmode():
    result = run_settings(
        {
            "DATABASE_URL": "postgresql://user:password@managed-db.example.com:25060/db?sslmode=require",
            "DJANGO_DB_SSLMODE": "verify-full",
            "DJANGO_DB_SSLROOTCERT": "/certs/managed-ca.pem",
        }
    )

    assert result.returncode == 0, result.stderr
    configured = json.loads(result.stdout)
    assert configured["db_sslmode"] == "verify-full"
    assert configured["db_sslrootcert"] == "/certs/managed-ca.pem"


@pytest.mark.parametrize(
    "scenario,configuration,expected",
    [
        (
            "digitalocean_app_platform",
            {
                "DJANGO_ALLOWED_HOSTS": "api.managed.example.com",
                "DJANGO_CORS_ALLOWED_ORIGINS": "https://app.managed.example.com",
                "DJANGO_CSRF_TRUSTED_ORIGINS": "https://app.managed.example.com",
                "DATABASE_URL": "postgresql://managed_user:test-password@managed-db.example.com:25060/managed_db?sslmode=verify-full&sslrootcert=%2Fcerts%2Fmanaged-ca.pem",
                "R2_BUCKET_NAME": "managed-private",
            },
            {
                "hosts": ["api.managed.example.com"],
                "cors": ["https://app.managed.example.com"],
                "csrf": ["https://app.managed.example.com"],
                "db_name": "managed_db",
                "db_host": "managed-db.example.com",
                "db_sslmode": "verify-full",
                "db_sslrootcert": "/certs/managed-ca.pem",
                "storage_bucket": "managed-private",
                "storage_endpoint": "https://example-account.r2.cloudflarestorage.com",
            },
        ),
        (
            "digitalocean_droplet_nginx_gunicorn",
            {
                "DJANGO_ALLOWED_HOSTS": "api.droplet.example.com",
                "DJANGO_CORS_ALLOWED_ORIGINS": "https://app.droplet.example.com",
                "DJANGO_CSRF_TRUSTED_ORIGINS": "https://app.droplet.example.com",
                "DB_NAME": "droplet_db",
                "DB_HOST": "127.0.0.1",
                "R2_BUCKET_NAME": "droplet-private",
            },
            {
                "hosts": ["api.droplet.example.com"],
                "cors": ["https://app.droplet.example.com"],
                "csrf": ["https://app.droplet.example.com"],
                "db_name": "droplet_db",
                "db_host": "127.0.0.1",
                "db_sslmode": None,
                "db_sslrootcert": None,
                "storage_bucket": "droplet-private",
                "storage_endpoint": "https://example-account.r2.cloudflarestorage.com",
            },
        ),
        (
            "other_linux_vps",
            {
                "DJANGO_ALLOWED_HOSTS": "api.other.example.com",
                "DJANGO_CORS_ALLOWED_ORIGINS": "https://app.other.example.com",
                "DJANGO_CSRF_TRUSTED_ORIGINS": "https://app.other.example.com",
                "DB_NAME": "other_db",
                "DB_HOST": "postgres.other.example.com",
                "DJANGO_DB_SSLMODE": "require",
                "R2_BUCKET_NAME": "other-private",
                "R2_ENDPOINT": "https://other-account.r2.cloudflarestorage.com",
            },
            {
                "hosts": ["api.other.example.com"],
                "cors": ["https://app.other.example.com"],
                "csrf": ["https://app.other.example.com"],
                "db_name": "other_db",
                "db_host": "postgres.other.example.com",
                "db_sslmode": "require",
                "db_sslrootcert": None,
                "storage_bucket": "other-private",
                "storage_endpoint": "https://other-account.r2.cloudflarestorage.com",
            },
        ),
    ],
)
def test_production_contract_supports_provider_switch_with_environment_only(
    scenario, configuration, expected
):
    result = run_settings(configuration)

    assert result.returncode == 0, f"{scenario}: {result.stderr}"
    configured = json.loads(result.stdout)
    for key, value in expected.items():
        assert configured[key] == value, f"{scenario}: {key}"
    assert configured["db_engine"] == "django.db.backends.postgresql"
    assert (
        configured["private_media_backend"]
        == "apps.catalog.storage.PrivateReferenceStorage"
    )
    assert configured["proxy_ssl_header"] == ["HTTP_X_FORWARDED_PROTO", "https"]
    assert configured["ssl_redirect"] is True
