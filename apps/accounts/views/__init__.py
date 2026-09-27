from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter, OpenApiTypes
from rest_framework import serializers
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.middleware.csrf import get_token
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.decorators import throttle_classes

class AuthRateThrottle(ScopedRateThrottle):
    scope = 'auth'

from django.contrib.auth import logout
from ..models import User
from ..serializers import UserSerializer, UserCreateSerializer, LoginSerializer


def set_refresh_cookie(response, refresh_token):
    max_age = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())
    secure = getattr(settings, 'SESSION_COOKIE_SECURE', False)
    response.set_cookie(
        'refresh',
        refresh_token,
        max_age=max_age,
        httponly=True,
        samesite='Lax',
        secure=secure
    )

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """Update current user's profile"""
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view that returns user data, issues CSRF token, and sets HttpOnly refresh cookie"""
    throttle_classes = [AuthRateThrottle]

    @extend_schema(
        responses={
            200: inline_serializer(
                name='LoginResponse',
                fields={
                    'access': serializers.CharField(),
                    'user': UserSerializer()
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Issue the CSRF cookie so frontend has it for subsequent calls
            get_token(request)

            # Move refresh token from JSON payload to HttpOnly cookie
            refresh_token = response.data.pop('refresh', None)
            if refresh_token:
                set_refresh_cookie(response, refresh_token)

            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data['user']
                response.data['user'] = UserSerializer(user).data
        return response

@method_decorator(csrf_protect, name='dispatch')
class CustomTokenRefreshView(TokenRefreshView):
    """Refresh view that reads refresh token from HttpOnly cookie and requires CSRF"""
    throttle_classes = [AuthRateThrottle]

    @extend_schema(
        request=None,
        parameters=[
            OpenApiParameter(
                name='refresh',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.COOKIE,
                description='Refresh token in HttpOnly cookie',
                required=True,
            )
        ],
        responses={
            200: inline_serializer(
                name='RefreshResponse',
                fields={
                    'access': serializers.CharField(),
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh')
        if not refresh_token:
            return Response({"detail": "Refresh token missing from cookies."}, status=status.HTTP_401_UNAUTHORIZED)

        mutable_data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        mutable_data['refresh'] = refresh_token

        serializer = self.get_serializer(data=mutable_data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        response = Response(serializer.validated_data, status=status.HTTP_200_OK)

        # Move the new rotated refresh token to cookie
        refresh_token_rotated = response.data.pop('refresh', None)
        if refresh_token_rotated:
            set_refresh_cookie(response, refresh_token_rotated)

        return response


@extend_schema(request=None, responses={200: dict, 400: dict})
@api_view(['POST'])
@throttle_classes([AuthRateThrottle])
@permission_classes([IsAuthenticated])
@csrf_protect
def logout_view(request):
    """Logout view that blacklists the refresh token and clears cookies"""
    try:
        refresh_token = request.COOKIES.get("refresh")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()

        logout(request)
        response = Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        response.delete_cookie('refresh')
        response.delete_cookie('csrftoken')
        return response
    except Exception:
        response = Response(
            {"error": "Invalid or expired refresh token."},
            status=status.HTTP_400_BAD_REQUEST,
        )
        response.delete_cookie('refresh')
        response.delete_cookie('csrftoken')
        return response
