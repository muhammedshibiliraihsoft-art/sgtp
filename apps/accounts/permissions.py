from rest_framework.permissions import BasePermission


class PasswordChangeGate(BasePermission):
    """Restrict generated-credential accounts to changing password or logout."""

    message = "Change the initial password before using this operation."
    code = "password_change_required"

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if (
            not user
            or not user.is_authenticated
            or not getattr(user, "must_change_password", False)
        ):
            return True
        if getattr(view, "allow_must_change_password", False):
            return True
        return getattr(view, "action", None) == "password_change"
