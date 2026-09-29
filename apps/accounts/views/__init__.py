from base64 import urlsafe_b64decode
from binascii import Error as Base64DecodeError

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import (
    action,
    api_view,
    permission_classes,
    throttle_classes,
)
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.tenants.permissions import IsMainSupplierAdmin
from ..models import User
from ..identity import normalize_email
from ..permissions import PasswordChangeGate
from ..security import set_password_and_revoke_sessions
from ..serializers import (
    EmailOrPhoneTokenObtainPairSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    VersionedTokenRefreshSerializer,
    UserAdminSerializer,
    UserCreateSerializer,
    ShopUserCreateSerializer,
    UserSerializer,
)


class AuthRateThrottle(ScopedRateThrottle):
    scope = "auth"


def set_refresh_cookie(response, refresh_token):
    max_age = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())
    response.set_cookie(
        "refresh",
        refresh_token,
        max_age=max_age,
        httponly=True,
        samesite="Lax",
        secure=getattr(settings, "SESSION_COOKIE_SECURE", False),
    )


def clear_refresh_cookie(response):
    response.delete_cookie("refresh")


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        """Limit user enumeration to the Main Supplier Admin and self."""
        if IsMainSupplierAdmin().has_permission(self.request, self):
            return User.objects.all()
        if self.action == "reset_credentials" and self.request.user.owning_shop_id:
            return User.objects.filter(owning_shop_id=self.request.user.owning_shop_id)
        return User.objects.filter(pk=self.request.user.pk)

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in (
            "list",
            "retrieve",
            "update",
            "partial_update",
        ) and IsMainSupplierAdmin().has_permission(self.request, self):
            return UserAdminSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == "create":
            classes = [IsMainSupplierAdmin, PasswordChangeGate]
        elif self.action == "list":
            classes = [IsAuthenticated, PasswordChangeGate]
        elif self.action == "destroy":
            classes = [IsAuthenticated, PasswordChangeGate]
        elif self.action == "password_change":
            classes = [IsAuthenticated]
        elif self.action == "reset_credentials":
            classes = [IsAuthenticated, PasswordChangeGate]
        else:
            classes = [IsAuthenticated, PasswordChangeGate]
        return [permission() for permission in classes]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = UserAdminSerializer(user).data
        data["initial_password"] = serializer.initial_password
        response = Response(data, status=status.HTTP_201_CREATED)
        response["Cache-Control"] = "no-store"
        response["Pragma"] = "no-cache"
        return response

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Global User deletion is not available."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @extend_schema(
        request=None,
        responses={
            200: inline_serializer(
                name="AdminCredentialResetResponse",
                fields={
                    "user_code": serializers.CharField(),
                    "temporary_password": serializers.CharField(),
                },
            )
        },
        description="Main Supplier only. Returns one temporary credential with no-store headers.",
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="reset-credentials",
        permission_classes=[IsMainSupplierAdmin, PasswordChangeGate],
        throttle_classes=[AuthRateThrottle],
    )
    def reset_credentials(self, request, pk=None):
        user = self.get_object()
        from ..services.user_lifecycle import reset_user_credentials

        temporary_password = reset_user_credentials(request.user, user)
        response = Response(
            {"user_code": user.user_code, "temporary_password": temporary_password},
            status=status.HTTP_200_OK,
        )
        response["Cache-Control"] = "no-store"
        response["Pragma"] = "no-cache"
        return response

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated, PasswordChangeGate],
    )
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(
        detail=False,
        methods=["put", "patch"],
        permission_classes=[IsAuthenticated, PasswordChangeGate],
    )
    def update_profile(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=request.method == "PATCH",
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="password/change",
    )
    def password_change(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        set_password_and_revoke_sessions(
            request.user,
            serializer.validated_data["new_password"],
            must_change=False,
        )
        response = Response(
            {"detail": "Password changed. Sign in again."}, status=status.HTTP_200_OK
        )
        clear_refresh_cookie(response)
        return response


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailOrPhoneTokenObtainPairSerializer
    throttle_classes = [AuthRateThrottle]
    throttle_scope = "auth"

    @extend_schema(
        responses={
            200: inline_serializer(
                name="LoginResponse",
                fields={"access": serializers.CharField(), "user": UserSerializer()},
            )
        }
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            get_token(request)
            refresh_token = response.data.pop("refresh", None)
            if refresh_token:
                set_refresh_cookie(response, refresh_token)
            try:
                access = AccessToken(response.data["access"])
                user = User.objects.get(pk=access[api_settings.USER_ID_CLAIM])
                response.data["user"] = UserSerializer(user).data
            except (TokenError, User.DoesNotExist, KeyError):
                response.data["user"] = None
        return response


@method_decorator(csrf_protect, name="dispatch")
class CustomTokenRefreshView(TokenRefreshView):
    """Refresh only from the HttpOnly cookie and require CSRF validation."""

    serializer_class = VersionedTokenRefreshSerializer
    throttle_classes = [AuthRateThrottle]
    throttle_scope = "auth"

    @extend_schema(
        request=None,
        parameters=[
            OpenApiParameter(
                name="refresh",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.COOKIE,
                description="Refresh token in HttpOnly cookie",
                required=True,
            )
        ],
        responses={
            200: inline_serializer(
                name="RefreshResponse", fields={"access": serializers.CharField()}
            )
        },
    )
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "Refresh token missing from cookies."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise ValidationError({"detail": "Token is invalid or revoked."}) from exc
        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        rotated = response.data.pop("refresh", None)
        if rotated:
            set_refresh_cookie(response, rotated)
        return response


@extend_schema(
    request=PasswordResetRequestSerializer,
    responses={
        200: inline_serializer(
            name="PasswordResetRequestResponse",
            fields={"detail": serializers.CharField()},
        )
    },
)
@api_view(["POST"])
@throttle_classes([AuthRateThrottle])
@permission_classes([AllowAny])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = normalize_email(serializer.validated_data.get("email"))
    user = User.objects.filter(email=email, is_active=True).first() if email else None
    if user and getattr(settings, "PASSWORD_RESET_URL", ""):
        uid = urlsafe_base64_encode(str(user.pk).encode())
        token = PasswordResetTokenGenerator().make_token(user)
        reset_url = f"{settings.PASSWORD_RESET_URL}?uid={uid}&token={token}"
        send_mail(
            subject="Reset your SGTP password",
            message=f"Use this link to reset your password: {reset_url}",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[user.email],
            fail_silently=True,
        )
    response = Response(
        {
            "detail": "If the account is eligible, password reset instructions will be sent."
        },
        status=status.HTTP_200_OK,
    )
    response["Cache-Control"] = "no-store"
    response["Pragma"] = "no-cache"
    return response


@extend_schema(
    request=PasswordResetConfirmSerializer,
    responses={
        200: inline_serializer(
            name="PasswordResetConfirmResponse",
            fields={"detail": serializers.CharField()},
        )
    },
)
@api_view(["POST"])
@throttle_classes([AuthRateThrottle])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    uid = request.data.get("uid", "")
    token = request.data.get("token", "")
    try:
        user_id = force_str(urlsafe_b64decode(uid.encode()))
        user = User.objects.get(pk=user_id, is_active=True, email__isnull=False)
    except (
        ValueError,
        TypeError,
        UnicodeDecodeError,
        Base64DecodeError,
        User.DoesNotExist,
    ):
        user = None
    if not user or not PasswordResetTokenGenerator().check_token(user, token):
        raise ValidationError({"detail": "Reset token is invalid or expired."})
    serializer = PasswordResetConfirmSerializer(
        data=request.data, context={"reset_user": user}
    )
    serializer.is_valid(raise_exception=True)
    set_password_and_revoke_sessions(
        user, serializer.validated_data["new_password"], must_change=False
    )
    response = Response(
        {"detail": "Password reset. Sign in with your new password."},
        status=status.HTTP_200_OK,
    )
    response["Cache-Control"] = "no-store"
    return response


@extend_schema(
    request=None,
    responses={
        200: inline_serializer(
            name="LogoutResponse",
            fields={"message": serializers.CharField()},
        )
    },
)
@api_view(["POST"])
@throttle_classes([AuthRateThrottle])
@permission_classes([IsAuthenticated, PasswordChangeGate])
@csrf_protect
def logout_view(request):
    """Blacklist the refresh token and clear its cookie."""
    try:
        token_value = request.COOKIES.get("refresh")
        if token_value:
            RefreshToken(token_value).blacklist()
    except TokenError:
        pass
    logout(request)
    response = Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
    response.delete_cookie("refresh")
    response.delete_cookie("csrftoken")
    return response


logout_view.throttle_scope = "auth"
logout_view.allow_must_change_password = True
