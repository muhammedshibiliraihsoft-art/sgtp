import secrets

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from .models import User


def generate_initial_password(user):
    """Create an unpersisted temporary secret that is returned once by the view."""
    while True:
        value = secrets.token_urlsafe(32)
        try:
            validate_password(value, user=user)
        except ValidationError:
            continue
        return value


def set_password_and_revoke_sessions(user, raw_password, *, must_change=False):
    """Change credentials and invalidate all refresh and access tokens atomically."""
    with transaction.atomic():
        locked_user = User.objects.select_for_update().get(pk=user.pk)
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
