"""One-time, Shop-authorized direct uploads for private catalog images."""

import uuid
from datetime import timedelta

from django.core import signing
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from apps.catalog.models import (
    DesignVersion,
    GarmentFamily,
    PrivateMediaUpload,
    StyleOption,
)
from apps.catalog.services import (
    upload_design_references,
    upload_family_image,
    upload_style_images,
)
from apps.tenants.policy import ShopRolePolicy


MAX_UPLOAD_BYTES = 10 * 1024 * 1024
UPLOAD_URL_TTL_SECONDS = 300
UPLOAD_TOKEN_SALT = "catalog.private-media-upload.v1"
MIME_FORMATS = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}


def validate_upload_metadata(content_type, byte_size):
    if content_type not in MIME_FORMATS:
        raise ValidationError(
            {"content_type": "Only JPG, PNG, and WebP are supported."}
        )
    if not isinstance(byte_size, int) or not 1 <= byte_size <= MAX_UPLOAD_BYTES:
        raise ValidationError(
            {"byte_size": "Image size must be between 1 byte and 10 MB."}
        )


def resolve_upload_target(*, kind, target_id, shop, actor):
    try:
        if kind == PrivateMediaUpload.Kind.FAMILY:
            if shop is not None or not ShopRolePolicy.is_main_supplier_admin(actor):
                raise NotFound()
            return GarmentFamily.objects.get(pk=target_id)
        if kind == PrivateMediaUpload.Kind.STYLE_OPTION:
            options = StyleOption.objects.all()
            if shop is None:
                if not ShopRolePolicy.is_main_supplier_admin(actor):
                    raise NotFound()
                options = options.filter(tenant__isnull=True)
            else:
                options = options.filter(Q(tenant__isnull=True) | Q(tenant=shop))
                if not ShopRolePolicy.is_main_supplier_admin(actor):
                    options = options.filter(tenant=shop)
            return options.get(pk=target_id)
        if kind == PrivateMediaUpload.Kind.DESIGN_VERSION:
            versions = DesignVersion.objects.select_related("design").filter(
                status=DesignVersion.Status.DRAFT
            )
            if shop is None:
                if not ShopRolePolicy.is_main_supplier_admin(actor):
                    raise NotFound()
                versions = versions.filter(design__tenant__isnull=True)
            else:
                versions = versions.filter(design__tenant=shop)
            return versions.get(pk=target_id)
        raise ValidationError({"kind": "Unsupported private media target."})
    except (
        GarmentFamily.DoesNotExist,
        StyleOption.DoesNotExist,
        DesignVersion.DoesNotExist,
        ValueError,
    ):
        raise NotFound() from None


def issue_upload(*, kind, target_id, content_type, byte_size, actor, shop):
    from django.conf import settings
    from django.core.files.storage import storages

    if not settings.R2_ENABLED:
        raise RuntimeError(
            "Direct uploads are unavailable until private R2 is configured."
        )
    validate_upload_metadata(content_type, byte_size)
    target = resolve_upload_target(
        kind=kind, target_id=target_id, shop=shop, actor=actor
    )
    storage = storages["private_media"]
    scope = f"shops/{shop.pk}" if shop is not None else "catalog/global"
    object_key = f"pending/{scope}/{kind}/{target.pk}/{uuid.uuid4().hex}.upload"
    expires_at = timezone.now() + timedelta(seconds=UPLOAD_URL_TTL_SECONDS)
    upload_url = storage.presigned_upload(
        object_key, content_type, expires=UPLOAD_URL_TTL_SECONDS
    )
    ticket = PrivateMediaUpload.objects.create(
        tenant=shop,
        actor=actor,
        kind=kind,
        target_id=target.pk,
        object_key=object_key,
        content_type=content_type,
        byte_size=byte_size,
        expires_at=expires_at,
    )
    token = signing.dumps({"upload_id": str(ticket.pk)}, salt=UPLOAD_TOKEN_SALT)
    return {
        "upload_url": upload_url,
        "upload_token": token,
        "headers": {"Content-Type": content_type},
        "expires_in": UPLOAD_URL_TTL_SECONDS,
    }


@transaction.atomic
def complete_upload(*, token, actor, shop):
    from django.conf import settings
    from django.core.files.storage import storages

    if not settings.R2_ENABLED:
        raise ValidationError({"detail": "Private direct upload is not configured."})
    try:
        data = signing.loads(
            token, salt=UPLOAD_TOKEN_SALT, max_age=UPLOAD_URL_TTL_SECONDS
        )
        ticket = PrivateMediaUpload.objects.select_for_update().get(
            pk=data["upload_id"]
        )
    except (
        signing.BadSignature,
        KeyError,
        PrivateMediaUpload.DoesNotExist,
        ValueError,
    ):
        raise ValidationError(
            {"upload_token": "Upload authorization is invalid or expired."}
        ) from None

    now = timezone.now()
    if (
        ticket.actor_id != actor.pk
        or ticket.tenant_id != (shop.pk if shop else None)
        or ticket.expires_at <= now
    ):
        raise ValidationError(
            {"upload_token": "Upload authorization is invalid or expired."}
        )

    target = resolve_upload_target(
        kind=ticket.kind,
        target_id=ticket.target_id,
        shop=shop,
        actor=actor,
    )
    storage = storages["private_media"]
    try:
        metadata = storage.object_metadata(ticket.object_key)
        if (
            metadata.get("ContentLength") != ticket.byte_size
            or metadata.get("ContentType") != ticket.content_type
            or metadata.get("ContentLength", MAX_UPLOAD_BYTES + 1) > MAX_UPLOAD_BYTES
        ):
            raise ValidationError(
                {"file": "Uploaded image metadata does not match its authorization."}
            )
        with storage.open(ticket.object_key, "rb") as uploaded:
            payload = uploaded.read(MAX_UPLOAD_BYTES + 1)
        if len(payload) != ticket.byte_size or len(payload) > MAX_UPLOAD_BYTES:
            raise ValidationError(
                {"file": "Uploaded image size does not match its authorization."}
            )
        file = ContentFile(payload, name="authorized-upload")

        if ticket.kind == PrivateMediaUpload.Kind.FAMILY:
            result = upload_family_image(family_id=target.pk, upload=file, actor=actor)
            from apps.catalog.views import FamilyImageView

            response_data = FamilyImageView._metadata(result)
        elif ticket.kind == PrivateMediaUpload.Kind.STYLE_OPTION:
            result = upload_style_images(
                style_option=target,
                uploads=[file],
                actor=actor,
                shop=shop,
            )
            from apps.catalog.serializers import StyleImageSerializer

            response_data = StyleImageSerializer(result, many=True).data
        else:
            result = upload_design_references(
                version=target, uploads=[file], actor=actor
            )
            from apps.catalog.serializers import DesignReferenceSerializer

            response_data = DesignReferenceSerializer(
                result, many=True, context={"shop_id": shop.pk if shop else None}
            ).data
    except ValidationError:
        raise
    except Exception as error:
        # Do not expose provider errors, signed URLs, or credentials to clients.
        raise ValidationError(
            {"file": "Uploaded image could not be verified."}
        ) from error

    ticket.delete()
    transaction.on_commit(lambda: storage.delete_object(ticket.object_key))
    return response_data
