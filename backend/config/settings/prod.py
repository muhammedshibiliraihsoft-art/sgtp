import os
from pathlib import Path
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(BASE_DIR / ".env.prod")

from .base import *

ENVIRONMENT = "production"

if get_env_var("DJANGO_DEBUG", "False").strip().lower() != "false":
    raise ImproperlyConfigured("Production requires DJANGO_DEBUG=False.")
DEBUG = False

_imported_by_staging = os.getenv(
    "DJANGO_ENV", ""
).strip().lower() == "staging" and os.getenv("DJANGO_SETTINGS_MODULE", "").strip() in {
    "core.settings",
    "backend.config.settings.staging",
}
if not _imported_by_staging and not R2_ENABLED:
    raise ImproperlyConfigured(
        "Production requires private R2 storage; filesystem media is not durable."
    )

if not _imported_by_staging and (
    len(SECRET_KEY) < 50 or SECRET_KEY.startswith("django-insecure-")
):
    raise ImproperlyConfigured("Production requires a strong DJANGO_SECRET_KEY.")

_database = DATABASES["default"]
if not all(str(_database[key]).strip() for key in ("NAME", "USER", "PASSWORD", "HOST")):
    raise ImproperlyConfigured("Production requires complete PostgreSQL configuration.")
if "DATABASE_URL" not in os.environ and not os.getenv("DB_HOST", "").strip():
    raise ImproperlyConfigured("Production requires DB_HOST or DATABASE_URL.")

_explicit_db_sslmode = os.getenv("DJANGO_DB_SSLMODE", "").strip().lower()
if _explicit_db_sslmode and _explicit_db_sslmode not in {
    "require",
    "verify-ca",
    "verify-full",
}:
    raise ImproperlyConfigured(
        "DJANGO_DB_SSLMODE must be require, verify-ca, or verify-full."
    )
_db_sslmode = _explicit_db_sslmode or _database.get("OPTIONS", {}).get("sslmode", "")
_db_sslrootcert = os.getenv("DJANGO_DB_SSLROOTCERT", "").strip() or _database.get(
    "OPTIONS", {}
).get("sslrootcert", "")
if _db_sslrootcert and _db_sslmode not in {"verify-ca", "verify-full"}:
    raise ImproperlyConfigured(
        "Database SSL root certificate requires verify-ca or verify-full."
    )
if (
    not _imported_by_staging
    and _database["HOST"] not in {"localhost", "127.0.0.1", "::1"}
    and not _database["HOST"].startswith("/")
    and not _db_sslmode
):
    raise ImproperlyConfigured(
        "Remote production PostgreSQL requires DJANGO_DB_SSLMODE."
    )
if _db_sslmode:
    _database.setdefault("OPTIONS", {})["sslmode"] = _db_sslmode
if _db_sslrootcert:
    _database.setdefault("OPTIONS", {})["sslrootcert"] = _db_sslrootcert

_configured_hosts = [host.strip() for host in ALLOWED_HOSTS if host.strip()]
if not _configured_hosts or any(
    host == "*" or "*" in host for host in _configured_hosts
):
    raise ImproperlyConfigured(
        "Production DJANGO_ALLOWED_HOSTS must contain explicit hostnames."
    )


def _require_https_origins(variable_name):
    raw_value = get_env_var(variable_name).strip()
    origins = [origin.strip() for origin in raw_value.split(",") if origin.strip()]
    if not origins:
        raise ImproperlyConfigured(f"{variable_name} must contain HTTPS origins.")
    for origin in origins:
        parsed = urlsplit(origin)
        if (
            parsed.scheme != "https"
            or not parsed.netloc
            or parsed.path
            or parsed.query
            or parsed.fragment
            or parsed.username
            or parsed.password
            or "*" in parsed.netloc
        ):
            raise ImproperlyConfigured(
                f"{variable_name} must contain explicit HTTPS origins only."
            )
    return list(dict.fromkeys(origins))


CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = _require_https_origins("DJANGO_CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = _require_https_origins("DJANGO_CSRF_TRUSTED_ORIGINS")

# Security settings (production only)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
