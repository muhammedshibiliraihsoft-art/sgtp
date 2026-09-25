import os
from pathlib import Path

# In test, we usually don't load .env but rely on environment variables injected by the test runner (e.g. pytest-env or tox).
# For convenience, if .env exists, we can load it, or just .env.test
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(BASE_DIR / ".env.test")

from .base import *

# Tests should run with DEBUG=False by default to catch template errors, etc.
DEBUG = get_env_var("DJANGO_DEBUG", "False") == "True"

# Use in-memory SQLite for fast testing if desired, or override to use PostgreSQL.
# Usually tests use the same engine but a different test DB name, handled by Django test runner automatically.
# We'll rely on the base DATABASES definition, which Django will clone for tests.

# Fast password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
