from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenantViewSet, TenantMemberViewSet
from .context_views import ShopContextView
from .views.shop_users import ShopUserCreateView
from .views.work_functions import MembershipWorkFunctionView

router = DefaultRouter()
router.register(r"tenants", TenantViewSet)
router.register(r"memberships", TenantMemberViewSet)

urlpatterns = [
    path(
        "shops/<uuid:shop_id>/memberships/<uuid:membership_id>/functions/",
        MembershipWorkFunctionView.as_view(),
        name="membership_work_functions",
    ),
    path(
        "shops/<uuid:shop_id>/users/",
        ShopUserCreateView.as_view(),
        name="shop_user_create",
    ),
    path(
        "shops/<uuid:shop_id>/context/", ShopContextView.as_view(), name="shop_context"
    ),
    path("", include(router.urls)),
]
