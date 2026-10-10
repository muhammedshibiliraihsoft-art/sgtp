import secrets
import re

from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from .models import User


def generate_initial_password(user):
    """Create an unpersisted, non-weak six-digit temporary PIN."""
    while True:
        value = f"{secrets.randbelow(1_000_000):06d}"
        try:
            validate_pin(value)
        except ValidationError:
            continue
        return value


def validate_pin(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{6}", value):
        raise ValidationError("PIN must contain exactly six ASCII digits.")
    if len(set(value)) == 1 or value in {"123456", "654321", "121212"}:
        raise ValidationError("Choose a less predictable PIN.")
    digits = [ord(character) - 48 for character in value]
    if all((digits[i + 1] - digits[i]) % 10 == 1 for i in range(5)) or all(
        (digits[i] - digits[i + 1]) % 10 == 1 for i in range(5)
    ) or value[:2] * 3 == value or value[:3] * 2 == value:
        raise ValidationError("Choose a less predictable PIN.")


def set_password_and_revoke_sessions(
    user, raw_password, *, must_change=False, validate_locked_user=None
):
    """Change credentials and invalidate all refresh and access tokens atomically."""
    with transaction.atomic():
        locked_user = User.objects.select_for_update().get(pk=user.pk)
        if validate_locked_user:
            validate_locked_user(locked_user)
        locked_user.set_password(raw_password)
        locked_user.must_change_password = must_change
        locked_user.auth_version += 1
        locked_user.save(
            update_fields=[
                "password",
                "must_change_password",
                "auth_version",
                "updated_at",
            ]
        )
        outstanding = OutstandingToken.objects.select_for_update().filter(
            user=locked_user
        )
        for token in outstanding.iterator():
            BlacklistedToken.objects.get_or_create(token=token)
    return locked_user


def revoke_user_sessions(user):
    """Invalidate a user's existing sessions without changing their credential."""
    with transaction.atomic():
        locked_user = User.objects.select_for_update().get(pk=user.pk)
        locked_user.auth_version += 1
        locked_user.save(update_fields=["auth_version", "updated_at"])
        outstanding = OutstandingToken.objects.select_for_update().filter(
            user=locked_user
        )
        for token in outstanding.iterator():
            BlacklistedToken.objects.get_or_create(token=token)
    return locked_user
