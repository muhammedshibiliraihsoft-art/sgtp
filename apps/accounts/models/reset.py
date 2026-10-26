"""Durable auth-abuse counters and Shop ADMIN recovery requests."""

import uuid

from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class AuthAttemptBucket(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    count = models.PositiveIntegerField(default=0)
    window_ends_at = models.DateTimeField(db_index=True)
    blocked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(key__regex=r"^[a-f0-9]{64}$"),
                name="auth_attempt_key_sha256_hex",
            ),
            models.CheckConstraint(
                condition=Q(blocked_until__isnull=True)
                | Q(blocked_until__lte=F("window_ends_at")),
                name="auth_attempt_blocked_within_window",
            ),
        ]


class ShopAdminPinResetRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="pin_reset_requests"
    )
    shop = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT)
    phone = models.CharField(max_length=16)
    status = models.CharField(
        max_length=8, choices=Status.choices, default=Status.PENDING
    )
    requested_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="resolved_pin_reset_requests",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status="PENDING"),
                name="unique_pending_shop_admin_pin_reset",
            ),
            models.CheckConstraint(
                condition=Q(status__in=["PENDING", "APPROVED", "REJECTED"]),
                name="shop_pin_reset_status_valid",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        status="PENDING",
                        resolved_at__isnull=True,
                        resolved_by__isnull=True,
                    )
                    | Q(
                        status__in=["APPROVED", "REJECTED"],
                        resolved_at__isnull=False,
                        resolved_by__isnull=False,
                    )
                ),
                name="shop_pin_reset_resolution_state",
            ),
            models.CheckConstraint(
                condition=Q(phone__regex=r"^\+[1-9][0-9]{1,14}$"),
                name="shop_pin_reset_phone_e164",
            ),
        ]
