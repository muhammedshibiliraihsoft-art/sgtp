from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from rest_framework.exceptions import ValidationError as DRFValidationError

from .models import Supplier, Tenant, TenantMember
from .policy import ShopRolePolicy
from .services.shop_management import set_shop_active, update_shop


class MainSupplierAdminMixin:
    def has_module_permission(self, request):
        return ShopRolePolicy.is_main_supplier_admin(request.user)


@admin.register(Supplier)
class SupplierAdmin(MainSupplierAdminMixin, admin.ModelAdmin):
    list_display = ["name", "is_active", "created_at"]
    readonly_fields = ["id", "singleton_lock", "created_at", "updated_at"]

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request) and not Supplier.objects.exists()

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def delete_queryset(self, request, queryset):
        raise ValidationError("The Main Supplier record cannot be deleted.")


@admin.register(Tenant)
class TenantAdmin(MainSupplierAdminMixin, admin.ModelAdmin):
    list_display = [
        "name",
        "slug",
        "supplier",
        "domain",
        "is_active_display",
        "user_count_display",
        "max_users",
        "created_at",
    ]
    list_filter = ["supplier", "is_active", "created_at", "max_users"]
    search_fields = ["name", "slug", "domain", "contact_email"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = [
        "id",
        "supplier",
        "created_at",
        "updated_at",
        "user_count_display",
        "is_active",
    ]
    actions = ["activate_selected_shops", "deactivate_selected_shops"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("supplier", "name", "slug", "domain", "is_active")},
        ),
        (
            "Limits & Settings",
            {
                "fields": (
                    "max_users",
                    "default_locale",
                    "default_timezone",
                    "default_currency",
                )
            },
        ),
        ("Contact Information", {"fields": ("contact_email", "contact_phone")}),
        (
            "Address",
            {
                "fields": (
                    "address_line1",
                    "address_line2",
                    "city",
                    "state",
                    "postal_code",
                    "country",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("id", "created_at", "updated_at", "user_count_display"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        # Shop creation must atomically create its first ADMIN through the API service.
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def delete_queryset(self, request, queryset):
        raise ValidationError("Shops cannot be deleted; deactivate them instead.")

    def save_model(self, request, obj, form, change):
        if not change or obj.pk is None:
            raise ValidationError("Shop creation must use the atomic first-ADMIN flow.")
        if {"is_active", "supplier"}.intersection(form.changed_data):
            raise ValidationError(
                "Shop lifecycle and Supplier ownership are service-controlled."
            )
        changes = {field: form.cleaned_data[field] for field in form.changed_data}
        try:
            saved = update_shop(request.user, obj.pk, changes)
        except DRFValidationError as exc:
            raise ValidationError(exc.detail) from exc
        obj.__dict__.update(saved.__dict__)

    @admin.action(description="Activate selected Shops (service-controlled)")
    def activate_selected_shops(self, request, queryset):
        for shop_id in queryset.values_list("pk", flat=True):
            set_shop_active(request.user, shop_id, active=True)

    @admin.action(description="Deactivate selected Shops (service-controlled)")
    def deactivate_selected_shops(self, request, queryset):
        for shop_id in queryset.values_list("pk", flat=True):
            set_shop_active(request.user, shop_id, active=False)

    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: red;">✗ Inactive</span>')

    is_active_display.short_description = "Status"

    def user_count_display(self, obj):
        count = obj.user_count
        max_users = obj.max_users
        color = (
            "red"
            if count >= max_users
            else "orange" if count >= max_users * 0.8 else "green"
        )
        return format_html(
            '<span style="color: {}">{}/{}</span>', color, count, max_users
        )

    user_count_display.short_description = "Users"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("supplier")


class TenantMemberInline(admin.TabularInline):
    model = TenantMember
    extra = 0
    readonly_fields = ["user", "tenant", "role", "is_active", "deleted"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


TenantAdmin.inlines = [TenantMemberInline]


@admin.register(TenantMember)
class TenantMemberAdmin(MainSupplierAdminMixin, admin.ModelAdmin):
    list_display = ["user", "tenant", "role", "is_active", "created_at"]
    list_filter = ["role", "is_active", "tenant"]
    search_fields = [
        "user__user_code",
        "user__first_name",
        "user__last_name",
        "tenant__name",
    ]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "role",
        "is_active",
        "deleted",
        "tenant",
        "user",
    ]

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def delete_queryset(self, request, queryset):
        raise ValidationError("Membership lifecycle must use the domain services.")
