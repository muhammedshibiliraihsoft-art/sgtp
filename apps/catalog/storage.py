"""Private reference storage with local and Cloudflare R2 backends."""

import posixpath

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage, Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateReferenceStorage(Storage):
    """Keep the private storage alias stable while selecting its provider by env."""

    def __init__(self):
        if settings.R2_ENABLED:
            from storages.backends.s3 import S3Storage

            self.backend = S3Storage(
                bucket_name=settings.R2_BUCKET_NAME,
                endpoint_url=settings.R2_ENDPOINT,
                access_key=settings.R2_ACCESS_KEY_ID,
                secret_key=settings.R2_SECRET_ACCESS_KEY,
                region_name=settings.R2_REGION,
                addressing_style="path",
                signature_version="s3v4",
                default_acl=None,
                querystring_auth=True,
                querystring_expire=300,
                file_overwrite=False,
                object_parameters={"CacheControl": "private, no-store"},
                max_memory_size=2 * 1024 * 1024,
            )
        else:
            self.backend = FileSystemStorage(
                location=settings.PRIVATE_MEDIA_ROOT, base_url=""
            )

    def deconstruct(self):
        return ("apps.catalog.storage.PrivateReferenceStorage", (), {})

    def _open(self, name, mode="rb"):
        return self.backend.open(name, mode)

    def _save(self, name, content):
        saved_name = self.backend._save(name.replace("\\", "/"), content)
        return saved_name.replace("\\", "/")

    def get_available_name(self, name, max_length=None):
        normalized_name = posixpath.normpath(name.replace("\\", "/"))
        available_name = self.backend.get_available_name(
            normalized_name, max_length=max_length
        )
        return available_name.replace("\\", "/")

    def delete(self, name):
        return self.backend.delete(name)

    def exists(self, name):
        return self.backend.exists(name)

    def size(self, name):
        return self.backend.size(name)

    def listdir(self, path):
        return self.backend.listdir(path)

    def path(self, name):
        if settings.R2_ENABLED:
            raise NotImplementedError("Private R2 objects do not have local paths.")
        return self.backend.path(name)

    def get_accessed_time(self, name):
        return self.backend.get_accessed_time(name)

    def get_created_time(self, name):
        return self.backend.get_created_time(name)

    def get_modified_time(self, name):
        return self.backend.get_modified_time(name)

    def url(self, name):
        raise ValueError("Private reference files do not have public URLs.")

    def presigned_upload(self, name, content_type, *, expires=300):
        if not settings.R2_ENABLED:
            raise ImproperlyConfigured("Direct uploads require private R2 storage.")
        return self.backend.connection.meta.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.R2_BUCKET_NAME,
                "Key": name,
                "ContentType": content_type,
            },
            ExpiresIn=expires,
            HttpMethod="PUT",
        )

    def object_metadata(self, name):
        if not settings.R2_ENABLED:
            raise ImproperlyConfigured("Direct uploads require private R2 storage.")
        return self.backend.connection.meta.client.head_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=name,
        )

    def delete_object(self, name):
        if settings.R2_ENABLED:
            self.backend.connection.meta.client.delete_object(
                Bucket=settings.R2_BUCKET_NAME,
                Key=name,
            )
        else:
            self.backend.delete(name)
