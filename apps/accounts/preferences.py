"""Presentation preference fallback helpers; callers authorize Shop first."""

SUPPORTED_LOCALES = frozenset({"en", "ar-KW", "bn", "ur"})


def resolve_locale(user_locale=None, *, authorized_shop_locale=None):
    """Resolve User preference → already-authorized Shop default → English.

    This helper intentionally does not query for a Shop or authorize one. A caller
    may pass a Shop default only after the applicable Shop access check succeeds.
    """
    if user_locale in SUPPORTED_LOCALES:
        return user_locale
    if authorized_shop_locale in SUPPORTED_LOCALES:
        return authorized_shop_locale
    return "en"
