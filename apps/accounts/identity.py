"""Canonical account identifiers and human User ID generation."""

import secrets
import re

USER_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
USER_CODE_PATTERN = re.compile(r"^U-[23456789ABCDEFGHJKMNPQRSTUVWXYZ]{16}$")


def normalize_email(value):
    """Canonicalize optional email consistently for writes and lookups."""
    if value is None:
        return None
    value = value.strip()
    return value.lower() or None


def generate_user_code():
    return "U-" + "".join(secrets.choice(USER_CODE_ALPHABET) for _ in range(16))
