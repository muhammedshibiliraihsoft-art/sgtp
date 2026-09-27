from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CustomTokenObtainPairView, CustomTokenRefreshView, logout_view

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]