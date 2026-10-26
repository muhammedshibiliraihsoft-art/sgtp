"""PostgreSQL-backed atomic limits shared by all application workers."""

import hashlib
import hmac
import ipaddress
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Subquery
from django.utils import timezone

from .models import AuthAttemptBucket


def _key(kind, value):
    material = f"{kind}:{value}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), material, hashlib.sha256).hexdigest()


def _prune_expired(now):
    expired_keys = (
        AuthAttemptBucket.objects.filter(window_ends_at__lte=now - timedelta(hours=1))
        .order_by("window_ends_at")
        .values("key")[:250]
    )
    AuthAttemptBucket.objects.filter(key__in=Subquery(expired_keys)).delete()


def consume(kind, value, *, limit, minutes=15):
    """Return False during a bounded lockout; no local-memory throttle dependency."""
    key = _key(kind, value)
    now = timezone.now()
    if secrets.randbelow(256) == 0:
        _prune_expired(now)
    for _ in range(2):
        with transaction.atomic():
            try:
                with transaction.atomic():
                    AuthAttemptBucket.objects.get_or_create(
                        key=key,
                        defaults={"window_ends_at": now + timedelta(minutes=minutes)},
                    )
            except IntegrityError:
                pass
            bucket = (
                AuthAttemptBucket.objects.select_for_update().filter(key=key).first()
            )
            if bucket is None:
                # A concurrent bounded cleanup may have deleted this stale row.
                continue
            if bucket.blocked_until and bucket.blocked_until > now:
                return False
            if bucket.window_ends_at <= now:
                bucket.count = 0
                bucket.window_ends_at = now + timedelta(minutes=minutes)
                bucket.blocked_until = None
            bucket.count += 1
            if bucket.count > limit:
                bucket.blocked_until = bucket.window_ends_at
            bucket.save(update_fields=["count", "window_ends_at", "blocked_until"])
            return bucket.count <= limit
    raise RuntimeError("Could not reserve an authentication attempt bucket.")


def release(kind, value, *, limit):
    """Undo a reserved attempt after successful authentication."""
    key = _key(kind, value)
    now = timezone.now()
    with transaction.atomic():
        bucket = AuthAttemptBucket.objects.select_for_update().filter(key=key).first()
        if not bucket or bucket.window_ends_at <= now:
            return
        bucket.count = max(0, bucket.count - 1)
        if bucket.count <= limit:
            bucket.blocked_until = None
        bucket.save(update_fields=["count", "blocked_until"])


def source(request):
    # Only use a forwarding header when deployment configuration explicitly
    # declares the trusted proxy boundary. REMOTE_ADDR is the safe default.
    header = getattr(settings, "AUTH_TRUSTED_CLIENT_IP_HEADER", "REMOTE_ADDR")
    if header not in {
        "REMOTE_ADDR",
        "HTTP_X_REAL_IP",
        "HTTP_CF_CONNECTING_IP",
    }:
        header = "REMOTE_ADDR"
    candidates = (request.META.get(header), request.META.get("REMOTE_ADDR"))
    for candidate in candidates:
        try:
            return ipaddress.ip_address(candidate.strip()).compressed
        except (AttributeError, ValueError):
            continue
    return "unknown"
