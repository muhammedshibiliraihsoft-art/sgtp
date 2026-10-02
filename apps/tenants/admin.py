from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.common.admin import MainSupplierAdminMixin, status_badge
from .models import MembershipWorkFunction, Supplier, Tenant, TenantMember
from .services.shop_management import set_shop_active, update_shop


@admin.register(Supplier)
class SupplierAdmin(MainSupplierAdminMixin, admin.ModelAdmin):
    list_display = ("name", "status", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 50
    readonly_fields = ("id", "singleton_lock", "created_at", "updated_at")

    @admin.display(description="Status", ordering="is_active")
    def status(self, obj):
        return status_badge("ACTIVE" if obj.is_active else "INACTIVE")

    def has_add_permission(self, request):
        return super().has_add_permission(request) and not Supplier.objects.exists()

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def delete_queryset(self, request, queryset):
        raise ValidationError("The Main Supplier record cannot be deleted.")


class TenantMemberInline(admin.TabularInline):
    model = TenantMember
    extra = 0
    can_delete = False
    show_change_link = True
    fields = ("user", "role", "is_active", "deleted", "created_at")
    readonly_fields = fields

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Tenant)
class TenantAdmin(MainSupplierAdminMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "supplier",
        "domain",
        "status",
        "user_count_display",
        "max_users",
        "created_at",
    )
    list_filter = ("supplier", "is_active", "created_at", "max_users")
    search_fields = ("name", "slug", "domain", "contact_email")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = (
        "id",
        "supplier",
        "created_at",
        "updated_at",
        "user_count_display",
        "is_active",
    )
    actions = ("activate_selected_shops", "deactivate_selected_shops")
    inlines = (TenantMemberInline,)
    list_per_page = 50
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

    def has_add_permission(self, request):
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

    @admin.display(description="Status", ordering="is_active")
    def status(self, obj):
        return status_badge("ACTIVE" if obj.is_active else "INACTIVE")

    @admin.display(description="Users", ordering="_admin_user_count")
    def user_count_display(self, obj):
        count = getattr(obj, "_admin_user_count", 0)
        label = f"{count}/{obj.max_users}"
        state = (
            "INACTIVE"
            if not obj.is_active
            else "AT_LIMIT" if count >= obj.max_users else "ACTIVE"
        )
        return status_badge(state, label)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("supplier")
            .annotate(
                _admin_user_count=Count(
                    "memberships",
                    filter=Q(memberships__deleted__isnull=True),
                    distinct=True,
                )
            )
        )


@admin.register(TenantMember)
class TenantMemberAdmin(MainSupplierAdminMixin, admin.ModelAdmin):
    list_display = ("user", "tenant", "role", "status", "created_at")
    list_filter = ("role", "is_active", "tenant")
    search_fields = (
        "user__user_code",
        "user__first_name",
        "user__last_name",
        "tenant__name",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "role",
        "is_active",
        "deleted",
        "tenant",
        "user",
    )
    list_select_related = ("user", "tenant")
    list_per_page = 50

    @admin.display(description="Status", ordering="is_active")
    def status(self, obj):
        if obj.deleted:
            return status_badge("ARCHIVED")
        return status_badge("ACTIVE" if obj.is_active else "INACTIVE")

    def get_queryset(self, request):
        return TenantMember.all_objects.select_related("user", "tenant")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def delete_queryset(self, request, queryset):
        raise ValidationError("Membership lifecycle must use the domain services.")


@admin.register(MembershipWorkFunction)
class MembershipWorkFunctionAdmin(MainSupplierAdminMixin, admin.ModelAdmin):
    list_display = ("membership", "function_code", "created_at")
    list_filter = ("function_code",)
    search_fields = ("membership__user__user_code", "membership__tenant__name")
    readonly_fields = (
        "id",
        "membership",
        "function_code",
        "created_at",
        "updated_at",
        "deleted",
    )
    list_select_related = ("membership__user", "membership__tenant")
    actions = None

    def has_view_permission(self, request, obj=None):
        return self._is_main_supplier(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
