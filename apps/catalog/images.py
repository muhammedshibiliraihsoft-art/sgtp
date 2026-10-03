"""Validate and optimize uploaded reference images before persistence."""

from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError
from rest_framework.exceptions import ValidationError


MAX_BATCH_FILES = 3
MAX_STORED_BYTES = 2 * 1024 * 1024
ACCEPTED_FORMATS = {"JPEG", "PNG", "WEBP"}


def optimize_reference(upload, *, error_field="images"):
    try:
        upload.seek(0)
        with Image.open(upload) as opened:
            if opened.format not in ACCEPTED_FORMATS:
                raise ValidationError(
                    {error_field: "Only JPG, PNG, and WebP images are supported."}
                )
            image = ImageOps.exif_transpose(opened)
            image.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise ValidationError(
            {error_field: "The uploaded file is not a valid supported image."}
        ) from error
    finally:
        upload.seek(0)

    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA" if "transparency" in image.info else "RGB")

    for _attempt in range(24):
        buffer = BytesIO()
        image.save(buffer, format="WEBP", quality=82, method=6)
        payload = buffer.getvalue()
        if len(payload) <= MAX_STORED_BYTES:
            return (
                ContentFile(payload, name="reference.webp"),
                len(payload),
                image.width,
                image.height,
            )
        if image.width <= 256 or image.height <= 256:
            break
        image.thumbnail(
            (int(image.width * 0.82), int(image.height * 0.82)),
            Image.Resampling.LANCZOS,
        )

    raise ValidationError(
        {error_field: "Image could not be optimized below the 2 MB limit."}
    )
