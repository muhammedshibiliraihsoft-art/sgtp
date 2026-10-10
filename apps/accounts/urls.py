from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    csrf_bootstrap,
    logout_view,
    shop_admin_pin_reset_request,
    shop_admin_pin_reset_list,
    shop_admin_pin_reset_approve,
    shop_admin_pin_reset_reject,
)

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('csrf/', csrf_bootstrap, name='csrf_bootstrap'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('pin-reset-requests/', shop_admin_pin_reset_request, name='shop_admin_pin_reset_request'),
    path('pin-reset-requests/pending/', shop_admin_pin_reset_list, name='shop_admin_pin_reset_list'),
    path('pin-reset-requests/<uuid:request_id>/approve/', shop_admin_pin_reset_approve, name='shop_admin_pin_reset_approve'),
    path('pin-reset-requests/<uuid:request_id>/reject/', shop_admin_pin_reset_reject, name='shop_admin_pin_reset_reject'),
    path('', include(router.urls)),
]
