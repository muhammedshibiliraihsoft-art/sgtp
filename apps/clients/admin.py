from django.contrib import admin

from apps.common.admin import MainSupplierReadOnlyAdmin, status_badge
from .models import Client, RelatedPerson


class ShopContactAdmin(MainSupplierReadOnlyAdmin):
    list_display = ("name", "tenant", "email", "phone", "status", "created_at")
    list_filter = ("tenant", "created_at")
    search_fields = ("name", "email", "phone", "tenant__name")
    list_select_related = ("tenant",)
    ordering = ("tenant__name", "name")

    def get_queryset(self, request):
        manager = getattr(self.model, "all_objects", self.model._default_manager)
        queryset = manager.get_queryset()
        return queryset.select_related(*self.get_select_related_fields())

    def get_select_related_fields(self):
        return tuple(
            field.name
            for field in self.model._meta.concrete_fields
            if field.is_relation and field.many_to_one
        )

    @admin.display(description="Status", ordering="deleted")
    def status(self, obj):
        return status_badge("ARCHIVED" if obj.deleted else "ACTIVE")


@admin.register(Client)
class ClientAdmin(ShopContactAdmin):
    pass


@admin.register(RelatedPerson)
class RelatedPersonAdmin(ShopContactAdmin):
    list_display = (
        "name",
        "tenant",
        "primary_client",
        "email",
        "phone",
        "status",
        "created_at",
    )
    list_select_related = ("tenant", "primary_client")
    search_fields = ShopContactAdmin.search_fields + ("primary_client__name",)
