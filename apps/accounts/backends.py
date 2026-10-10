"""Authenticate the same global User through approved identity aliases."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import make_password
import secrets

from .identity import USER_CODE_PATTERN, LOGIN_ID_PATTERN, normalize_email
from .phone_numbers import InvalidUserPhone, normalize_user_phone

User = get_user_model()
_DUMMY_PASSWORD_HASH = make_password(secrets.token_urlsafe(32))


class UserIdentifierBackend(BaseBackend):
    def authenticate(
        self,
        request,
        username=None,
        password=None,
        email=None,
        identifier=None,
        identifier_kind=None,
        **kwargs,
    ):
        raw = identifier if identifier is not None else (email or username)
        if not raw or not password:
            from django.contrib.auth.hashers import check_password

            check_password(password or "", _DUMMY_PASSWORD_HASH)
            return None
        value = raw.strip()
        kind = identifier_kind
        if kind is None:
            if USER_CODE_PATTERN.fullmatch(value.upper()):
                kind, value = "user_code", value.upper()
            elif "@" in value:
                kind, value = "email", normalize_email(value)
            elif value.startswith("+"):
                try:
                    kind, value = "phone", normalize_user_phone(value)
                except InvalidUserPhone:
                    kind = None
            elif LOGIN_ID_PATTERN.fullmatch(value):
                kind, value = "login_id", value
        user = None
        if kind in {"user_code", "email", "phone", "login_id"} and value:
            lookup = {f"{kind}__iexact" if kind == "login_id" else kind: value}
            user = User.objects.filter(**lookup).first()
        if user is None:
            # Perform a password hash operation on misses to reduce timing-based
            # account discovery. The dummy hash is never associated with a User.
            from django.contrib.auth.hashers import check_password

            check_password(password, _DUMMY_PASSWORD_HASH)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    @staticmethod
    def user_can_authenticate(user):
        return bool(
            getattr(user, "is_active", True)
            and getattr(user, "login_enabled", True)
        )

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return None
        return user if self.user_can_authenticate(user) else None
