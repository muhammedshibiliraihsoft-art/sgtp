from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.admin.sites import NotRegistered
from django.db import models
from django.utils.html import format_html

from apps.tenants.policy import ShopRolePolicy


class MainSupplierAdminMixin:
    """Gate every Admin surface and direct object URL to Main Supplier users."""

    @staticmethod
    def _is_main_supplier(request):
        return ShopRolePolicy.is_main_supplier_admin(
            getattr(request, "user", None) if request else None
        )

    def has_module_permission(self, request):
        return self._is_main_supplier(request)

    def has_view_permission(self, request, obj=None):
        return self._is_main_supplier(request)

    def has_add_permission(self, request):
        return self._is_main_supplier(request) and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return self._is_main_supplier(request) and super().has_change_permission(
            request, obj
        )

    def has_delete_permission(self, request, obj=None):
        return self._is_main_supplier(request) and super().has_delete_permission(
            request, obj
        )


class MainSupplierReadOnlyAdmin(MainSupplierAdminMixin, admin.ModelAdmin):
    """Inspection-only Admin; mutations stay behind domain services."""

    actions = None
    list_per_page = 50
    view_on_site = False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_exclude(self, request, obj=None):
        excluded = set(super().get_exclude(request, obj) or ())
        excluded.update(
            field.name
            for field in self.model._meta.concrete_fields
            if isinstance(field, models.FileField)
        )
        return tuple(sorted(excluded))

    def get_readonly_fields(self, request, obj=None):
        concrete_fields = (
            field.name
            for field in self.model._meta.concrete_fields
            if not isinstance(field, models.FileField)
        )
        return tuple(
            dict.fromkeys(
                (*concrete_fields, *super().get_readonly_fields(request, obj))
            )
        )


def status_badge(value, label=None):
    """Render a small accessible badge using a controlled CSS status class."""
    raw_value = str(value or "unknown").strip()
    status = raw_value.lower()
    allowed_statuses = {"active", "inactive", "archived", "draft", "published"}
    css_status = status if status in allowed_statuses else "neutral"
    display_label = label or raw_value.replace("_", " ").title()
    return format_html(
        '<span class="admin-status-badge admin-status-badge--{}">{}</span>',
        css_status,
        display_label,
    )


admin.site.site_header = "BiRKy Administration"
admin.site.site_title = "BiRKy Admin"
admin.site.index_title = "Internal Management"
admin.site.index_template = "admin/index.html"

# Django's built-in Group editor would create a separate permission-management
# surface for staff accounts. Main Supplier user and access views remain the
# only supported place for internal account inspection.
try:
    admin.site.unregister(Group)
except NotRegistered:
    pass
