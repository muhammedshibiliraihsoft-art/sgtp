from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException
from .models.users import User
from .forms import AccountChangeForm, AccountCreationForm


class UserAdmin(BaseUserAdmin):
    model = User
    form = AccountChangeForm
    add_form = AccountCreationForm
    list_display = ("user_code", "full_name", "email", "phone", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")
    fieldsets = (
        (None, {"fields": ("user_code", "email", "owning_shop")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (_("Contact"), {"fields": ("phone",)}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "phone",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
    readonly_fields = ("user_code", "owning_shop", "is_superuser")
    search_fields = ("user_code", "email", "first_name", "last_name", "phone")
    ordering = ("user_code",)
    actions = None

    def has_add_permission(self, request):
        # Account creation must atomically set immutable Shop ownership and membership.
        return False

    @admin.display(description="Name")
    def full_name(self, obj):
        return obj.full_name

    def save_model(self, request, obj, form, change):
        if change and "is_active" in form.changed_data and not obj.is_active:
            from .services.user_lifecycle import deactivate_global_user

            persisted_active = (
                User.objects.filter(pk=obj.pk)
                .values_list("is_active", flat=True)
                .first()
            )
            if persisted_active:
                try:
                    deactivate_global_user(
                        actor=request.user,
                        target_user=obj,
                        update_fields=form.changed_data,
                    )
                except (APIException, DjangoValidationError) as exc:
                    detail = getattr(exc, "detail", None)
                    if detail is None:
                        detail = getattr(exc, "message_dict", None)
                    if detail is None:
                        detail = getattr(exc, "messages", [str(exc)])
                    messages.error(request, str(detail))
                    obj._t304b_deactivation_rejected = True
                return
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        if getattr(form.instance, "_t304b_deactivation_rejected", False):
            return
        super().save_related(request, form, formsets, change)

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        # Django's built-in password editor lets an administrator set another
        # account's permanent password directly. T3-04A replaces that with the
        # explicit generated-credential reset action on the authorized API.
        return [
            url for url in super().get_urls() if url.name != "auth_user_password_change"
        ]


admin.site.register(User, UserAdmin)
