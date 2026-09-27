from rest_framework import viewsets

class TenantScopedMixin:
    """
    Mixin to enforce tenant (shop) scoping on querysets.
    Extracts the tenant identifier from the URL kwargs and filters the queryset.
    """
    tenant_lookup_url_kwarg = 'shop_id'
    tenant_lookup_field = 'tenant_id'
    
    def get_queryset(self):
        """
        Filters the base queryset to ensure only objects belonging to the 
        tenant specified in the URL are returned.
        """
        # We must call super() if this mixin is used with GenericAPIView
        if hasattr(super(), 'get_queryset'):
            qs = super().get_queryset()
        else:
            # Fallback if super() doesn't have it, though DRF views always do
            qs = self.queryset

        # If queryset is None, we can't filter it
        if qs is None:
            return None

        shop_id = self.kwargs.get(self.tenant_lookup_url_kwarg)
        
        # Deny-by-default: if no shop_id is provided in the URL context,
        # we return an empty queryset to prevent cross-tenant data leakage.
        if not shop_id:
            return qs.none()
            
        return qs.filter(**{self.tenant_lookup_field: shop_id})
