"""Canonical international phone handling for User login identifiers."""

import phonenumbers


class InvalidUserPhone(ValueError):
    pass


def normalize_user_phone(value):
    """Return a valid E.164 number; never infer a region for national input."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if not isinstance(value, str) or not value.strip().startswith("+"):
        raise InvalidUserPhone("Enter an international phone number with country code.")
    try:
        parsed = phonenumbers.parse(value.strip(), None)
    except phonenumbers.NumberParseException as exc:
        raise InvalidUserPhone("Enter a valid international phone number.") from exc
    if parsed.extension or not phonenumbers.is_valid_number(parsed):
        raise InvalidUserPhone("Enter a valid international phone number.")
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
