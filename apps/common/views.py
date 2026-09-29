"""Reusable fail-closed scoping for Shop-owned DRF resources."""

from django.core.exceptions import ImproperlyConfigured
from rest_framework.exceptions import NotAuthenticated, NotFound


class TenantScopedMixin:
    """Scope queryset reads and writes to the authorized T3-03 Shop context.

    This mixin is for Shop-owned resources only. Platform-wide endpoints must
    use a separate, explicitly authorized view instead.
    """

    tenant_lookup_url_kwarg = "shop_id"
    tenant_lookup_field = "tenant_id"
    tenant_model_field = "tenant"

    def _get_authorized_shop_context(self):
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            raise NotAuthenticated()
        if not getattr(user, "is_active", False):
            raise NotAuthenticated()

        context = getattr(request, "shop_context", None)
        if not context or not getattr(context, "shop", None):
            raise ImproperlyConfigured(
                "TenantScopedMixin requires an authorized request.shop_context."
            )
        if context.actor_user_id != user.pk:
            raise NotFound()

        url_shop_id = getattr(self, "kwargs", {}).get(self.tenant_lookup_url_kwarg)
        if url_shop_id is None:
            raise ImproperlyConfigured(
                "TenantScopedMixin requires its Shop URL parameter."
            )
        if str(url_shop_id) != str(context.shop.pk):
            raise NotFound()

        # T3-03 defines this as a compatibility alias, not a second selector.
        if str(getattr(request, "tenant_id", "")) != str(context.shop.pk):
            raise NotFound()
        return context

    def get_queryset(self):
        """Return only rows owned by the Shop authorized for this request."""
        context = self._get_authorized_shop_context()
        parent_get_queryset = getattr(super(), "get_queryset", None)
        if parent_get_queryset:
            queryset = parent_get_queryset()
        else:
            queryset = getattr(self, "queryset", None)

        if queryset is None or not hasattr(queryset, "filter"):
            raise ImproperlyConfigured(
                "TenantScopedMixin requires a configured Django queryset."
            )

        return queryset.filter(**{self.tenant_lookup_field: context.shop.pk})

    def perform_create(self, serializer):
        """Ignore client ownership as authority; assign the resolved Shop."""
        context = self._get_authorized_shop_context()
        serializer.save(**{self.tenant_model_field: context.shop})

    def perform_update(self, serializer):
        """Keep updates in the selected Shop, even if input supplies another."""
        context = self._get_authorized_shop_context()
        instance_shop_id = getattr(
            serializer.instance,
            f"{self.tenant_model_field}_id",
            None,
        )
        if str(instance_shop_id) != str(context.shop.pk):
            raise NotFound()
        serializer.save(**{self.tenant_model_field: context.shop})
