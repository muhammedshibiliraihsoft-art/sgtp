from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
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
from ..phone_numbers import InvalidUserPhone, normalize_user_phone
from ..security import generate_initial_password


class UserSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(read_only=True)
    must_change_password = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
            "phone",
            "preferred_locale",
            "appearance_preference",
            "must_change_password",
        )
        read_only_fields = (
            "id",
            "date_joined",
            "is_active",
            "phone",
            "must_change_password",
        )


class UserAdminSerializer(UserSerializer):
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)

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


class UserCreateSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, write_only=True
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "phone")

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

    def create(self, validated_data):
        self.initial_password = generate_initial_password(
            User(
                email=validated_data["email"],
                first_name=validated_data.get("first_name", ""),
                last_name=validated_data.get("last_name", ""),
            )
        )
        user = User.objects.create_user(
            password=self.initial_password,
            must_change_password=True,
            **validated_data,
        )
        return user


class EmailOrPhoneTokenObtainPairSerializer(TokenObtainPairSerializer):
    identifier = serializers.CharField(
        required=False, write_only=True, trim_whitespace=True
    )

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
        if "@" in value:
            return ("email", User.objects.normalize_email(value))
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
            normalized_email = User.objects.normalize_email(legacy_email.strip())
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

        matched_phone_user_id = None
        if kind == "phone":
            phone_user = (
                User.objects.filter(phone=normalized_identifier)
                .only("id", "email")
                .first()
            )
            login_email = phone_user.email if phone_user else normalized_identifier
            matched_phone_user_id = phone_user.pk if phone_user else None
        else:
            login_email = normalized_identifier

        authenticated_user = authenticate(
            request=self.context.get("request"),
            email=login_email,
            password=attrs["password"],
        )
        if not authenticated_user:
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
                or (
                    matched_phone_user_id
                    and (
                        user.pk != matched_phone_user_id
                        or user.phone != normalized_identifier
                    )
                )
            ):
                raise AuthenticationFailed(
                    "Invalid credentials.", code="invalid_credentials"
                )
            self.user = user
            refresh = self.get_token(user)
            data = {"refresh": str(refresh), "access": str(refresh.access_token)}
            if api_settings.UPDATE_LAST_LOGIN:
                update_last_login(None, user)
            return data


class VersionedTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        try:
            refresh = RefreshToken(attrs["refresh"])
            user_id = refresh.get(api_settings.USER_ID_CLAIM)
            user = (
                User.objects.filter(pk=user_id)
                .only("auth_version", "is_active")
                .first()
            )
            token_version = refresh.get("auth_version", 1)
        except TokenError as exc:
            raise InvalidToken(exc.args[0]) from exc
        except (KeyError, TypeError, ValueError) as exc:
            raise InvalidToken("Token is invalid or revoked.") from exc
        if not user or not user.is_active or token_version != user.auth_version:
            raise InvalidToken("Token is invalid or revoked.")
        return super().validate(attrs)


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError(
                {"current_password": "Current password is incorrect."}
            )
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )
        try:
            validate_password(attrs["new_password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {"new_password": list(exc.messages)}
            ) from exc
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )
        user = self.context.get("reset_user")
        if user:
            try:
                validate_password(attrs["new_password"], user=user)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(
                    {"new_password": list(exc.messages)}
                ) from exc
        return attrs
