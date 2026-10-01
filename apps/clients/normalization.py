"""Deterministic contact normalization without regional phone inference."""

import unicodedata


def normalize_phone(value: str) -> str:
    """Map Unicode decimal digits to ASCII and retain only an initial plus."""
    normalized = unicodedata.normalize("NFKC", value or "").strip()
    digits = []
    for character in normalized:
        try:
            digits.append(str(unicodedata.decimal(character)))
        except (TypeError, ValueError):
            continue
    prefix = "+" if normalized.startswith("+") else ""
    return prefix + "".join(digits)


def normalize_email(value: str) -> str:
    """Trim and case-fold for local duplicate checks and search."""
    return (value or "").strip().casefold()
