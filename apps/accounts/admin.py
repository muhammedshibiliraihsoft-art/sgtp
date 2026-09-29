from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models.users import User
from .forms import AccountChangeForm, AccountCreationForm


class UserAdmin(BaseUserAdmin):
    model = User
    form = AccountChangeForm
    add_form = AccountCreationForm
    list_display = ('user_code', 'full_name', 'email', 'phone', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('user_code', 'email')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Contact'), {'fields': ('phone',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone', 'password1', 'password2', 'is_staff', 'is_active')
        }),
    )
    readonly_fields = ('user_code',)
    search_fields = ('user_code', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('user_code',)
    actions = None

    @admin.display(description="Name")
    def full_name(self, obj):
        return obj.full_name

    def save_model(self, request, obj, form, change):
        if change and 'is_active' in form.changed_data and not obj.is_active:
            # We are deactivating. Ensure we don't bypass T3-04B invariant.
            from apps.accounts.services.user_lifecycle import deactivate_global_user
            from rest_framework.exceptions import ValidationError
            from django.contrib import messages

            # Revert the in-memory object temporarily to let the service act on DB state
            obj.is_active = True
            try:
                deactivate_global_user(actor=request.user, target_user=obj)
                # Success. The service saved is_active=False to DB.
                # Update our in-memory object so super().save_model persists it properly.
                obj.is_active = False
            except ValidationError as e:
                messages.set_level(request, messages.ERROR)
                messages.error(request, str(e.detail[0] if isinstance(e.detail, list) else e.detail))
                # Leave obj.is_active = True so the bad deactivation is not saved.

        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        # Django's built-in password editor lets an administrator set another
        # account's permanent password directly. T3-04A replaces that with the
        # explicit generated-credential reset action on the authorized API.
        return [
            url for url in super().get_urls()
            if url.name != "auth_user_password_change"
        ]


admin.site.register(User, UserAdmin)
