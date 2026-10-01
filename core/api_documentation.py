"""Access control for the internal Swagger and OpenAPI views."""

from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseNotFound
from django.urls import reverse
from django.utils.cache import patch_cache_control

from apps.tenants.policy import ShopRolePolicy


def internal_api_documentation(view):
    """Require an active, password-change-complete Main Supplier session."""

    @wraps(view)
    def wrapped(request, *args, **kwargs):
        response = None
        user = request.user
        if not user.is_authenticated:
            response = redirect_to_login(
                request.get_full_path(), login_url=reverse("admin:login")
            )
        elif (
            not user.is_active
            or getattr(user, "must_change_password", False)
            or not ShopRolePolicy.is_main_supplier_admin(user)
        ):
            # Use the same generic response for every authenticated non-admin.
            response = HttpResponseNotFound("Not found.")
        else:
            response = view(request, *args, **kwargs)

        patch_cache_control(response, private=True, no_store=True)
        response["Pragma"] = "no-cache"
        response["X-Robots-Tag"] = "noindex, nofollow"
        return response

    return wrapped
