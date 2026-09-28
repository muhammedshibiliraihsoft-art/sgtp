from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    logout_view,
    password_reset_confirm,
    password_reset_request,
)

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('password/reset/', password_reset_request, name='password_reset_request'),
    path('password/reset/confirm/', password_reset_confirm, name='password_reset_confirm'),
    path('', include(router.urls)),
]
