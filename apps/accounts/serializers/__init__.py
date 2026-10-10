from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import User
from ..identity import USER_CODE_PATTERN, LOGIN_ID_PATTERN, normalize_email, normalize_login_id
from ..security import validate_pin
from ..abuse import consume, release, source
from ..phone_numbers import InvalidUserPhone, normalize_user_phone
from apps.tenants.models import Tenant


class UserSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(read_only=True)
    must_change_password = serializers.BooleanField(read_only=True)
    user_code = serializers.CharField(read_only=True)
    login_id = serializers.CharField(read_only=True)
    is_main_supplier_admin = serializers.SerializerMethodField()
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    first_name = serializers.CharField(required=True, allow_blank=False, max_length=30)

    class Meta:
        model = User
        fields = (
            "id",
            "user_code",
            "login_id",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
            "phone",
            "preferred_locale",
            "appearance_preference",
            "must_change_password",
            "is_main_supplier_admin",
        )
        read_only_fields = (
            "id",
            "user_code",
            "login_id",
            "date_joined",
            "is_active",
            "phone",
            "email",
            "must_change_password",
            "is_main_supplier_admin",
        )

    def get_is_main_supplier_admin(self, obj) -> bool:
        return bool(obj.is_active and obj.is_superuser)


class UserAdminSerializer(UserSerializer):
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields
        read_only_fields = ("id", "date_joined", "must_change_password", "is_active")

    def validate_phone(self, value):
        try:
            normalized = normalize_user_phone(value)
        except InvalidUserPhone as exc:
            raise serializers.ValidationError(str(exc), code="invalid_phone") from exc
        if (
            normalized
            and User.objects.filter(phone=normalized)
            .exclude(pk=getattr(self.instance, "pk", None))
            .exists()
        ):
            raise serializers.ValidationError(
                "This login phone is already assigned.", code="duplicate_login_phone"
            )
        return normalized

    def validate_email(self, value):
        normalized = normalize_email(value)
        if normalized and User.objects.filter(email__iexact=normalized).exclude(
            pk=getattr(self.instance, "pk", None)
        ).exists():
            raise serializers.ValidationError("This email is already assigned.", code="duplicate_email")
        if self.instance and self.instance.is_superuser and not normalized:
            raise serializers.ValidationError("Main Supplier accounts require email.")
        self._normalized_email = normalized
        return normalized

    def validate_first_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("First name is required.")
        return value

    def validate(self, attrs):
        email = attrs.get("email", getattr(self.instance, "email", None))
        phone = attrs.get("phone", getattr(self.instance, "phone", None))
        is_superuser = getattr(self.instance, "is_superuser", False)
        if is_superuser and (not email or not phone):
            raise serializers.ValidationError("Main Supplier accounts require email and phone.")
        if self.instance and self.instance.pk:
            from apps.tenants.models import TenantMember, ShopRole

            active_admin = TenantMember.objects.filter(
                user=self.instance, role=ShopRole.ADMIN, is_active=True,
                deleted__isnull=True,
            ).exists()
            if active_admin and (not email or not phone):
                raise serializers.ValidationError("Active Shop Admin accounts require email and phone.")
        return attrs

    def update(self, instance, validated_data):
        if "email" in validated_data:
            validated_data["email"] = normalize_email(validated_data["email"])
        return super().update(instance, validated_data)


class UserCreateSerializer(serializers.ModelSerializer):
    login_id = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=32)
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    first_name = serializers.CharField(required=True, allow_blank=False, max_length=30)
    phone = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, write_only=True
    )
    shop = serializers.PrimaryKeyRelatedField(
        queryset=Tenant.objects.all(),
        required=True,
        write_only=True,
    )
    role = serializers.ChoiceField(
        choices=("ADMIN", "STAFF", "VIEWER"), required=True, write_only=True
    )

    class Meta:
        model = User
        fields = ("user_code", "login_id", "email", "first_name", "last_name", "phone", "shop", "role")
        read_only_fields = ("user_code",)

    def validate_email(self, value):
        normalized = normalize_email(value)
        if normalized and User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("This email is already assigned.", code="duplicate_email")
        return normalized

    def validate_login_id(self, value):
        if value in (None, ""):
            return None
        try:
            normalized = normalize_login_id(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        if User.objects.filter(login_id__iexact=normalized).exists():
            raise serializers.ValidationError("This User ID is unavailable.")
        return normalized

    def validate_first_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("First name is required.")
        return value

    def validate_phone(self, value):
        try:
            normalized = normalize_user_phone(value)
        except InvalidUserPhone as exc:
            raise serializers.ValidationError(str(exc), code="invalid_phone") from exc
        if normalized and User.objects.filter(phone=normalized).exists():
            raise serializers.ValidationError(
                "This login phone is already assigned.", code="duplicate_login_phone"
            )
        return normalized

    def validate(self, attrs):
        role = attrs.get("role")
        login_id = attrs.get("login_id")
        if role == "VIEWER" and login_id:
            raise serializers.ValidationError({"login_id": "Viewer accounts do not have login credentials."})
        if role != "VIEWER" and not login_id:
            raise serializers.ValidationError({"login_id": "This field is required for login-enabled accounts."})
        return attrs

    def create(self, validated_data):
        from apps.tenants.services.shop_accounts import create_shop_account

        shop = validated_data.pop("shop")
        role = validated_data.pop("role")
        user, self.initial_password = create_shop_account(
            actor=self.context["request"].user,
            shop_id=shop.pk,
            role=role,
            account_data=validated_data,
        )
        return user


class ShopUserCreateSerializer(UserCreateSerializer):
    shop = None

    class Meta(UserCreateSerializer.Meta):
        fields = ("user_code", "login_id", "email", "first_name", "last_name", "phone", "role")

    def to_internal_value(self, data):
        if "shop" in data or "tenant" in data or "owning_shop" in data:
            raise serializers.ValidationError(
                {"shop": "Shop is determined by the authorized URL context."}
            )
        return super().to_internal_value(data)

    def create(self, validated_data):
        from apps.tenants.services.shop_accounts import create_shop_account

        role = validated_data.pop("role")
        context = self.context["shop_context"]
        user, self.initial_password = create_shop_account(
            actor=self.context["request"].user,
            shop_id=context.shop.pk,
            role=role,
            account_data=validated_data,
        )
        return user


class EmailOrPhoneTokenObtainPairSerializer(TokenObtainPairSerializer):
    identifier = serializers.CharField(
        required=False, write_only=True, trim_whitespace=True, max_length=254
    )
    password = serializers.CharField(write_only=True, required=False, max_length=256)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = False
        self.fields["password"].required = False

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["auth_version"] = user.auth_version
        return token

    def _normalize_identifier(self, raw):
        if not raw:
            raise AuthenticationFailed(
                "Invalid credentials.", code="invalid_credentials"
            )
        value = raw.strip()
        if USER_CODE_PATTERN.fullmatch(value.upper()):
            return ("user_code", value.upper())
        if "@" in value:
            return ("email", normalize_email(value))
        if LOGIN_ID_PATTERN.fullmatch(value):
            return ("login_id", value)
        if not value.startswith("+"):
            raise AuthenticationFailed(
                "Invalid credentials.", code="invalid_credentials"
            )
        try:
            return ("phone", normalize_user_phone(value))
        except InvalidUserPhone as exc:
            raise AuthenticationFailed(
                "Invalid credentials.", code="invalid_credentials"
            ) from exc

    def validate(self, attrs):
        legacy_email = attrs.get("email")
        identifier = attrs.get("identifier")
        if not legacy_email and not identifier:
            raise serializers.ValidationError(
                {
                    "email": ["This field is required."],
                    "password": ["This field is required."],
                }
            )
        if not attrs.get("password"):
            raise serializers.ValidationError({"password": ["This field is required."]})
        if legacy_email and identifier:
            normalized_email = normalize_email(legacy_email)
            kind, normalized_identifier = self._normalize_identifier(identifier)
            if kind != "email" or normalized_email != normalized_identifier:
                raise AuthenticationFailed(
                    "Invalid credentials.", code="invalid_credentials"
                )
        elif identifier:
            kind, normalized_identifier = self._normalize_identifier(identifier)
        elif legacy_email:
            kind, normalized_identifier = self._normalize_identifier(legacy_email)
        else:
            raise AuthenticationFailed(
                "Invalid credentials.", code="invalid_credentials"
            )

        request = self.context.get("request")
        source_id = source(request) if request else "unknown"
        identifier_lookup = {
            f"{kind}__iexact" if kind == "login_id" else kind: normalized_identifier
        }
        candidate = User.objects.filter(**identifier_lookup).only("pk").first()
        source_allowed = consume("login-source", source_id, limit=60)
        counter_kind = "login-account" if candidate else "login-unknown-source"
        counter_value = str(candidate.pk) if candidate else source_id
        counter_limit = 8 if candidate else 12
        allowed = consume(
            counter_kind, counter_value, limit=counter_limit
        ) and source_allowed
        authenticated_user = authenticate(
            request=self.context.get("request"),
            identifier=normalized_identifier,
            identifier_kind=kind,
            password=attrs["password"],
        )
        if not allowed or not authenticated_user:
            raise AuthenticationFailed(
                "Invalid credentials.", code="invalid_credentials"
            )

        # Re-read under a row lock so a concurrent phone reassignment/password change
        # cannot mint a token for stale credentials or phone ownership.
        from django.db import transaction

        with transaction.atomic():
            user = (
                User.objects.select_for_update()
                .filter(pk=authenticated_user.pk)
                .first()
            )
            if (
                not user
                or not user.is_active
                or user.password != authenticated_user.password
                or not User.objects.filter(
                    pk=user.pk,
                    **identifier_lookup,
                ).exists()
            ):
                raise AuthenticationFailed(
                    "Invalid credentials.", code="invalid_credentials"
                )
            self.user = user
            refresh = self.get_token(user)
            data = {"refresh": str(refresh), "access": str(refresh.access_token)}
            if api_settings.UPDATE_LAST_LOGIN:
                update_last_login(None, user)
            release("login-source", source_id, limit=60)
            release(counter_kind, counter_value, limit=counter_limit)
            return data


class VersionedTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        try:
            refresh = RefreshToken(attrs["refresh"])
            user_id = refresh.get(api_settings.USER_ID_CLAIM)
            user = (
                User.objects.filter(pk=user_id)
                .first()
            )
            token_version = refresh.get("auth_version", 1)
        except TokenError as exc:
            raise InvalidToken(exc.args[0]) from exc
        except (KeyError, TypeError, ValueError) as exc:
            raise InvalidToken("Token is invalid or revoked.") from exc
        if (
            not user
            or not user.is_active
            or not user.login_enabled
            or token_version != user.auth_version
        ):
            raise InvalidToken("Token is invalid or revoked.")
        data = super().validate(attrs)
        data["user"] = UserSerializer(user).data
        return data


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, max_length=256)
    new_password = serializers.CharField(write_only=True, max_length=256)
    new_password_confirm = serializers.CharField(write_only=True, max_length=256)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )
        try:
            validate_pin(attrs["new_password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {"new_password": list(exc.messages)}
            ) from exc
        if attrs["new_password"] == attrs["current_password"]:
            raise serializers.ValidationError({"new_password": "Choose a different PIN."})
        return attrs
