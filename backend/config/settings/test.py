import os
from pathlib import Path

# In test, we usually don't load .env but rely on environment variables injected by the test runner (e.g. pytest-env or tox).
# For convenience, if .env exists, we can load it, or just .env.test
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(BASE_DIR / ".env.test")

from .base import *

# The Windows development PostgreSQL cluster may use a legacy encoding. Keep
# the disposable test database Unicode-capable for the V1 localized catalog.
DATABASES["default"].setdefault("TEST", {}).update(CHARSET="UTF8", TEMPLATE="template0")
STORAGES["staticfiles"] = {
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
}
# Uploaded catalog reference images are private and test-generated files must
# never share the development storage location or enter source control.
PRIVATE_MEDIA_ROOT = os.path.join(BASE_DIR, ".test-private-assets")

# Tests should run with DEBUG=False by default to catch template errors, etc.
DEBUG = get_env_var("DJANGO_DEBUG", "False") == "True"

# Use in-memory SQLite for fast testing if desired, or override to use PostgreSQL.
# Usually tests use the same engine but a different test DB name, handled by Django test runner automatically.
# We'll rely on the base DATABASES definition, which Django will clone for tests.

# Fast password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
