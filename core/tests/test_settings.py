import os
import pytest
from importlib import import_module
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
    # If we load prod settings, verify security flags are True
    # We must mock os.environ before importing
    old_env = dict(os.environ)
    os.environ["DJANGO_ENV"] = "production"
    os.environ["DB_NAME"] = "test"
    os.environ["DB_USER"] = "test"
    os.environ["DB_PASSWORD"] = "test"
    os.environ["DB_HOST"] = "test"
    os.environ["DJANGO_SECRET_KEY"] = "test"
    os.environ["DJANGO_ALLOWED_HOSTS"] = "test"
    os.environ["DJANGO_DEBUG"] = "False"
    
    try:
        import sys
        if "backend.config.settings.prod" in sys.modules:
            del sys.modules["backend.config.settings.prod"]
        prod_settings = import_module("backend.config.settings.prod")
        assert prod_settings.DEBUG is False
        assert prod_settings.SESSION_COOKIE_SECURE is True
        assert prod_settings.CSRF_COOKIE_SECURE is True
        assert prod_settings.SECURE_SSL_REDIRECT is True
    finally:
        os.environ.clear()
        os.environ.update(old_env)
