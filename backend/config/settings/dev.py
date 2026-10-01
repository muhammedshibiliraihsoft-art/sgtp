from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(BASE_DIR / ".env")

from .base import *  # noqa: E402, F401, F403

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Override any base settings for development
# Ensure debug is true if not overridden
DEBUG = get_env_var("DJANGO_DEBUG", "True") == "True"  # noqa: F405

# Explicitly disable production security for local dev
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# In development, you might want LocMemCache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-cache",
    }
}

# Development DRF overrides
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}
