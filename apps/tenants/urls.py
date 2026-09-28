from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenantViewSet, TenantMemberViewSet
from .context_views import ShopContextView

router = DefaultRouter()
router.register(r"tenants", TenantViewSet)
router.register(r"memberships", TenantMemberViewSet)

urlpatterns = [
    path(
        "shops/<uuid:shop_id>/context/", ShopContextView.as_view(), name="shop_context"
    ),
    path("", include(router.urls)),
]
