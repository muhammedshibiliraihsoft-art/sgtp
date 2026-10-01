"""Secure, explicitly non-production settings for the shared staging API."""

import os
import re

from django.core.exceptions import ImproperlyConfigured

from .prod import *  # noqa: F403


ENVIRONMENT = "staging"
STAGING_FRONTEND_ORIGIN = "https://staging.birky.com"
STAGING_API_HOSTNAME = "api-staging.birky.com"

if get_env_var("DJANGO_DEBUG", "False").strip().lower() != "false":  # noqa: F405
    raise ImproperlyConfigured("Staging requires DJANGO_DEBUG=False.")
DEBUG = False

_hostname_pattern = re.compile(
    r"(?=.{1,253}\Z)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)"
    r"(?:\.(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?))*\Z"
)
_configured_hosts = [
    host.strip() for host in ALLOWED_HOSTS if host.strip()  # noqa: F405
]  # noqa: F405
if any(not _hostname_pattern.fullmatch(host) for host in _configured_hosts):
    raise ImproperlyConfigured(
        "Staging DJANGO_ALLOWED_HOSTS must be explicit hostnames."
    )
if any(host != STAGING_API_HOSTNAME for host in _configured_hosts):
    raise ImproperlyConfigured(
        "Staging DJANGO_ALLOWED_HOSTS may contain only api-staging.birky.com."
    )

_render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
if _render_hostname and not _hostname_pattern.fullmatch(_render_hostname):
    raise ImproperlyConfigured("RENDER_EXTERNAL_HOSTNAME is invalid.")
ALLOWED_HOSTS = list(
    dict.fromkeys(
        [
            STAGING_API_HOSTNAME,
            *_configured_hosts,
            *([_render_hostname] if _render_hostname else []),
        ]
    )
)


def _require_exact_origins(variable_name):
    raw_value = get_env_var(variable_name)  # noqa: F405
    origins = [origin.strip() for origin in raw_value.split(",") if origin.strip()]
    if origins != [STAGING_FRONTEND_ORIGIN]:
        raise ImproperlyConfigured(
            f"{variable_name} must contain only {STAGING_FRONTEND_ORIGIN}."
        )
    return origins


CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = _require_exact_origins("DJANGO_CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = _require_exact_origins("DJANGO_CSRF_TRUSTED_ORIGINS")

# Retain production-grade HTTPS, proxy and HSTS defaults while keeping browser
# cookies host-only and same-site across the approved sibling subdomains.
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False

# Shared staging must never write recovery links or tokens to provider logs.
EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"
if get_env_var("DJANGO_EMAIL_BACKEND", EMAIL_BACKEND) != EMAIL_BACKEND:  # noqa: F405
    raise ImproperlyConfigured("Staging password-reset email delivery is disabled.")
PASSWORD_RESET_URL = "https://staging.birky.com/reset-password"
