"""Shop currency validation shared by catalog prices and billing."""

from decimal import Decimal, InvalidOperation

from babel.core import get_global
from babel.numbers import get_currency_precision


def normalize_currency(value):
    code = str(value or "").strip().upper()
    if len(code) != 3 or code not in get_global("all_currencies"):
        raise ValueError("A valid ISO 4217 currency code is required.")
    return code


def currency_minor_unit(currency):
    return get_currency_precision(normalize_currency(currency))


def validate_money_amount(value, currency, *, allow_zero=True):
    """Return a finite Decimal at the currency's scale; never round input."""
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError("Enter a valid decimal amount.") from error
    if not amount.is_finite() or amount < 0 or (not allow_zero and amount == 0):
        raise ValueError("Amount must be finite and non-negative.")
    scale = currency_minor_unit(currency)
    quantum = Decimal(1).scaleb(-scale)
    if amount != amount.quantize(quantum):
        raise ValueError(f"Amount supports at most {scale} decimal places for {currency}.")
    return amount
