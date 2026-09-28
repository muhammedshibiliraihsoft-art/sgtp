from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class VersionedJWTAuthentication(JWTAuthentication):
    """Reject access tokens minted before a password/session revocation event."""

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        token_version = validated_token.get("auth_version", 1)
        if token_version != user.auth_version:
            raise AuthenticationFailed(
                "Invalid or revoked token.", code="token_revoked"
            )
        return user
