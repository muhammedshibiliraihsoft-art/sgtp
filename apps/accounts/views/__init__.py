from django.conf import settings
from django.contrib.auth import logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
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
from rest_framework.exceptions import ValidationError, Throttled
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.tenants.permissions import IsMainSupplierAdmin
from ..models import User, ShopAdminPinResetRequest
from ..abuse import consume, source
from ..phone_numbers import InvalidUserPhone, normalize_user_phone
from ..services.shop_admin_pin_reset import (
    find_eligible_admin,
    resolve_request,
    submit_request,
)
from ..permissions import PasswordChangeGate
from ..security import set_password_and_revoke_sessions
from ..serializers import (
    EmailOrPhoneTokenObtainPairSerializer,
    PasswordChangeSerializer,
    VersionedTokenRefreshSerializer,
    UserAdminSerializer,
    UserCreateSerializer,
    ShopUserCreateSerializer,
    UserSerializer,
)


class AuthRateThrottle(ScopedRateThrottle):
    scope = "auth"

    def get_ident(self, request):
        return source(request)


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


LoginRequestSerializer = inline_serializer(
    name="EmailOrIdentifierLoginRequest",
    fields={
        "email": serializers.EmailField(required=False),
        "identifier": serializers.CharField(required=False, max_length=254),
        "password": serializers.CharField(write_only=True, required=True, max_length=256),
    },
)


@extend_schema(
    responses={
        200: inline_serializer(
            name="CsrfBootstrapResponse",
            fields={"csrf_token": serializers.CharField()},
        )
    },
    description=(
        "Returns only a CSRF token for credentialed browser clients on an "
        "explicitly trusted origin; it does not authenticate the caller."
    ),
)
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_bootstrap(request):
    """Issue a CSRF cookie and return its masked token for sibling-origin clients."""
    response = Response({"csrf_token": get_token(request)}, status=status.HTTP_200_OK)
    response["Cache-Control"] = "no-store"
    response["Pragma"] = "no-cache"
    return response


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
        if serializer.initial_password:
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
                    "login_id": serializers.CharField(allow_null=True),
                    "temporary_password": serializers.CharField(),
                },
            )
        },
        description="Main Supplier authority remains unchanged. A Shop ADMIN may reset only an active STAFF account in the same Shop. Returns a one-time temporary PIN.",
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
        if not consume("credential-reset-source", source(request), limit=10, minutes=60) or not consume(
            "credential-reset-target", str(user.pk), limit=3, minutes=60
        ):
            raise Throttled(detail="Credential reset temporarily unavailable.")
        from ..services.user_lifecycle import reset_user_credentials

        temporary_password = reset_user_credentials(request.user, user)
        response = Response(
            {"user_code": user.user_code, "login_id": user.login_id, "temporary_password": temporary_password},
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

        def validate_current_password(locked_user):
            if not locked_user.check_password(
                serializer.validated_data["current_password"]
            ):
                raise ValidationError(
                    {"current_password": "Current password is incorrect."}
                )

        set_password_and_revoke_sessions(
            request.user,
            serializer.validated_data["new_password"],
            must_change=False,
            validate_locked_user=validate_current_password,
        )
        response = Response(
            {"detail": "PIN changed. Sign in again."}, status=status.HTTP_200_OK
        )
        clear_refresh_cookie(response)
        return response


@method_decorator(csrf_protect, name="dispatch")
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailOrPhoneTokenObtainPairSerializer
    throttle_classes = [AuthRateThrottle]
    throttle_scope = "auth"

    @extend_schema(
        request=LoginRequestSerializer,
        description=(
            "Authenticate using the legacy email/password fields or identifier/password, "
            "where identifier accepts Login ID and approved legacy aliases. The shared password field accepts existing legacy passwords or newer six-digit PINs; the system is not PIN-only for existing accounts. Viewer accounts cannot authenticate. The response "
            "contains an access JWT and user profile; the refresh JWT is set only in "
            "the HttpOnly cookie."
        ),
        responses={
            200: inline_serializer(
                name="LoginResponse",
                fields={"access": serializers.CharField(), "user": UserSerializer()},
            )
        },
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
            ),
            OpenApiParameter(
                name="X-CSRFToken",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                description="Masked token from the CSRF bootstrap response.",
                required=True,
            ),
        ],
        description=(
            "Rotate the refresh token from the HttpOnly cookie. A valid CSRF cookie "
            "and matching X-CSRFToken header are required. The refresh token is never "
            "accepted from the request body."
        ),
        responses={
            200: inline_serializer(
                name="RefreshResponse",
                fields={"access": serializers.CharField(), "user": UserSerializer()},
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
    request=None,
    parameters=[
        OpenApiParameter(
            name="refresh",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.COOKIE,
            description="HttpOnly refresh token cookie to blacklist and clear.",
            required=False,
        ),
        OpenApiParameter(
            name="X-CSRFToken",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description="Masked token from the CSRF bootstrap response.",
            required=True,
        ),
    ],
    description=(
        "Requires a valid access JWT. Blacklist the refresh token when present, "
        "then clear the refresh and CSRF cookies. A valid CSRF cookie and matching "
        "X-CSRFToken header are required."
    ),
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


_PIN_RESET_GENERIC = "If this Shop Admin account is eligible, a reset request has been sent to Back Office."


@extend_schema(
    request=inline_serializer(name="ShopAdminPinResetRequestInput", fields={"phone": serializers.CharField()}),
    responses={200: inline_serializer(name="ShopAdminPinResetRequestResult", fields={"detail": serializers.CharField()})},
    description="Public request only; phone does not verify identity or change a PIN. Response does not disclose account eligibility.",
)
@api_view(["POST"])
@permission_classes([AllowAny])
def shop_admin_pin_reset_request(request):
    origin = source(request)
    allowed = consume("admin-reset-source", origin, limit=10, minutes=60)
    raw_phone = request.data.get("phone")
    try:
        phone = (
            normalize_user_phone(raw_phone)
            if isinstance(raw_phone, str) and len(raw_phone) <= 32
            else None
        )
    except (InvalidUserPhone, TypeError, ValueError):
        phone = None
    admin = find_eligible_admin(phone) if allowed and phone else None
    if admin:
        allowed = consume(
            "admin-reset-target", str(admin.pk), limit=3, minutes=60
        ) and allowed
    if allowed and admin:
        submit_request(admin, phone)
    response = Response({"detail": _PIN_RESET_GENERIC})
    response["Cache-Control"] = "no-store"
    response["Pragma"] = "no-cache"
    return response


@extend_schema(
    responses={200: inline_serializer(name="PendingShopAdminPinReset", many=True, fields={
        "id": serializers.UUIDField(), "shop": serializers.CharField(), "shop_id": serializers.UUIDField(),
        "name": serializers.CharField(), "login_id": serializers.CharField(allow_null=True),
        "phone": serializers.CharField(), "requested_at": serializers.DateTimeField(),
        "status": serializers.CharField(),
    })},
    description="Main Supplier only. Lists pending Shop ADMIN PIN reset requests.",
)
@api_view(["GET"])
@permission_classes([IsMainSupplierAdmin, PasswordChangeGate])
def shop_admin_pin_reset_list(request):
    rows = ShopAdminPinResetRequest.objects.filter(
        status=ShopAdminPinResetRequest.Status.PENDING
    ).select_related("user", "shop").order_by("requested_at")[:100]
    response = Response([{
        "id": str(row.pk), "shop": row.shop.name, "shop_id": str(row.shop_id),
        "name": row.user.full_name, "login_id": row.user.login_id,
        "phone": row.phone, "requested_at": row.requested_at,
        "status": row.status,
    } for row in rows])
    response["Cache-Control"] = "no-store"
    return response


@extend_schema(
    request=None,
    responses={200: inline_serializer(name="ApprovedShopAdminPinReset", fields={
        "id": serializers.UUIDField(), "status": serializers.CharField(),
        "login_id": serializers.CharField(allow_null=True), "temporary_password": serializers.CharField(),
    })},
    description="Main Supplier approval returns a one-time temporary PIN; never retrievable later.",
)
@api_view(["POST"])
@permission_classes([IsMainSupplierAdmin, PasswordChangeGate])
def shop_admin_pin_reset_approve(request, request_id):
    reset, pin = resolve_request(request.user, request_id, approve=True)
    response = Response({"id": str(reset.pk), "status": reset.status,
                         "login_id": reset.user.login_id, "temporary_password": pin})
    response["Cache-Control"] = "no-store"
    response["Pragma"] = "no-cache"
    return response


@extend_schema(
    request=None,
    responses={200: inline_serializer(name="RejectedShopAdminPinReset", fields={
        "id": serializers.UUIDField(), "status": serializers.CharField(),
    })},
    description="Main Supplier rejects a pending request without changing credentials.",
)
@api_view(["POST"])
@permission_classes([IsMainSupplierAdmin, PasswordChangeGate])
def shop_admin_pin_reset_reject(request, request_id):
    reset, _ = resolve_request(request.user, request_id, approve=False)
    return Response({"id": str(reset.pk), "status": reset.status})
