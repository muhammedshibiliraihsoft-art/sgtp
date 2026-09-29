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
