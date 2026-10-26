"""Canonical account identifiers and human User ID generation."""

import secrets
import re

USER_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
USER_CODE_PATTERN = re.compile(r"^U-[23456789ABCDEFGHJKMNPQRSTUVWXYZ]{16}$")
LOGIN_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{2,31}$")


def normalize_login_id(value):
    value = (value or "").strip()
    if not LOGIN_ID_PATTERN.fullmatch(value):
        raise ValueError("User ID must be 3-32 letters, digits or underscores and start with a letter.")
    return value


def normalize_email(value):
    """Canonicalize optional email consistently for writes and lookups."""
    if value is None:
        return None
    value = value.strip()
    return value.lower() or None


def generate_user_code():
    return "U-" + "".join(secrets.choice(USER_CODE_ALPHABET) for _ in range(16))
