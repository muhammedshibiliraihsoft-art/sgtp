"""OpenAPI schema support for the version-checking JWT authenticator."""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class VersionedJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "apps.accounts.authentication.VersionedJWTAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
