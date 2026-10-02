"""Private media storage boundary for catalog reference images."""

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateReferenceStorage(FileSystemStorage):
    """Store references outside MEDIA_ROOT and never expose a public URL."""

    def __init__(self):
        super().__init__(location=settings.PRIVATE_MEDIA_ROOT, base_url="")

    def deconstruct(self):
        return ("apps.catalog.storage.PrivateReferenceStorage", (), {})

    def url(self, name):
        raise ValueError("Private reference files do not have public URLs.")
