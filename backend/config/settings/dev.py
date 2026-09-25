import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(BASE_DIR / ".env")

from .base import *

# Override any base settings for development
# Ensure debug is true if not overridden
DEBUG = get_env_var("DJANGO_DEBUG", "True") == "True"

# In development, you might want LocMemCache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-cache",
    }
}
