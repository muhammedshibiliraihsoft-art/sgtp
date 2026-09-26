import os
from django.core.exceptions import ImproperlyConfigured

DJANGO_ENV = os.getenv("DJANGO_ENV", "dev").lower()

if DJANGO_ENV in ("production", "prod"):
    from backend.config.settings.prod import *
elif DJANGO_ENV == "test":
    from backend.config.settings.test import *
elif DJANGO_ENV in ("development", "dev"):
    from backend.config.settings.dev import *
else:
    raise ImproperlyConfigured(f"Unknown DJANGO_ENV: {DJANGO_ENV}")
