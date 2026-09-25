import os

DJANGO_ENV = os.getenv("DJANGO_ENV", "development")

if DJANGO_ENV == "production":
    from backend.config.settings.prod import *
elif DJANGO_ENV == "test":
    from backend.config.settings.test import *
else:
    from backend.config.settings.dev import *
