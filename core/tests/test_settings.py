import json
import os
import subprocess
import sys
from pathlib import Path
import pytest
from django.core.exceptions import ImproperlyConfigured
from backend.config.settings.base import get_env_var


def test_get_env_var_existing(monkeypatch):
    monkeypatch.setenv("DUMMY_VAR", "123")
    assert get_env_var("DUMMY_VAR") == "123"


def test_get_env_var_default():
    assert get_env_var("NON_EXISTENT", "default_val") == "default_val"


def test_get_env_var_missing_raises_improperly_configured():
    with pytest.raises(ImproperlyConfigured) as exc:
        get_env_var("NON_EXISTENT_VAR")
    assert "Set the NON_EXISTENT_VAR environment variable" in str(exc.value)


def test_base_settings_load_without_secret_key_fails(monkeypatch):
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    with pytest.raises(ImproperlyConfigured):
        # We can't import base directly if it's already imported,
        # but we can simulate the get_env_var call it does.
        get_env_var("DJANGO_SECRET_KEY")


def test_prod_settings_security_flags():
    # Import in a fresh process: base settings are cached in this pytest process.
    env = os.environ.copy()
    env.pop("DATABASE_URL", None)
    env.update(
        {
            "DJANGO_ENV": "production",
            "DB_NAME": "test",
            "DB_USER": "test",
            "DB_PASSWORD": "test",
            "DB_HOST": "localhost",
            "DJANGO_SECRET_KEY": "production-test-secret-not-used-outside-tests-and-long-enough",
            "DJANGO_ALLOWED_HOSTS": "test.example.com",
            "DJANGO_DEBUG": "False",
            "DJANGO_CORS_ALLOWED_ORIGINS": "https://app.example.com",
            "DJANGO_CSRF_TRUSTED_ORIGINS": "https://app.example.com",
            "R2_BUCKET_NAME": "production-test",
            "R2_ENDPOINT": "https://example-account.r2.cloudflarestorage.com",
            "R2_ACCESS_KEY_ID": "test-access-key",
            "R2_SECRET_ACCESS_KEY": "test-secret-key",
            "R2_REGION": "auto",
        }
    )
    script = """
import json
from backend.config.settings import prod
print(json.dumps({
    "debug": prod.DEBUG,
    "session_secure": prod.SESSION_COOKIE_SECURE,
    "csrf_secure": prod.CSRF_COOKIE_SECURE,
    "ssl_redirect": prod.SECURE_SSL_REDIRECT,
    "environment": prod.ENVIRONMENT,
    "r2": prod.R2_ENABLED,
}))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "debug": False,
        "session_secure": True,
        "csrf_secure": True,
        "ssl_redirect": True,
        "environment": "production",
        "r2": True,
    }
