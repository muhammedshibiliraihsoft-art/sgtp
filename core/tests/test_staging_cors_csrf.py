from django.test import Client, SimpleTestCase, override_settings


@override_settings(
    ALLOWED_HOSTS=["api-staging.birky.com"],
    CORS_ALLOW_ALL_ORIGINS=False,
    CORS_ALLOW_CREDENTIALS=True,
    CORS_ALLOWED_ORIGINS=["https://staging.birky.com"],
    CSRF_TRUSTED_ORIGINS=["https://staging.birky.com"],
    CSRF_COOKIE_SECURE=True,
    CSRF_COOKIE_SAMESITE="Lax",
)
class StagingCorsCsrfTests(SimpleTestCase):
    def test_approved_origin_receives_credentialed_preflight(self):
        response = Client().options(
            "/api/v1/auth/csrf/",
            HTTP_ORIGIN="https://staging.birky.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type,x-csrftoken",
            HTTP_HOST="api-staging.birky.com",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Access-Control-Allow-Origin"], "https://staging.birky.com"
        )
        self.assertEqual(response["Access-Control-Allow-Credentials"], "true")
        self.assertIn("origin", response.get("Vary", "").lower())

    def test_unapproved_origin_receives_no_cors_permission(self):
        response = Client().options(
            "/api/v1/auth/csrf/",
            HTTP_ORIGIN="https://evil.example",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
            HTTP_HOST="api-staging.birky.com",
        )

        self.assertNotIn("Access-Control-Allow-Origin", response)

    def test_csrf_bootstrap_sets_secure_host_only_cookie_for_staging_origin(self):
        client = Client()
        response = client.get(
            "/api/v1/auth/csrf/",
            secure=True,
            HTTP_ORIGIN="https://staging.birky.com",
            HTTP_HOST="api-staging.birky.com",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["csrf_token"])
        self.assertEqual(
            response["Access-Control-Allow-Origin"], "https://staging.birky.com"
        )
        self.assertEqual(response["Access-Control-Allow-Credentials"], "true")
        csrf_cookie = response.cookies["csrftoken"]
        self.assertTrue(csrf_cookie["secure"])
        self.assertFalse(csrf_cookie["httponly"])
        self.assertEqual(csrf_cookie["samesite"], "Lax")
        self.assertFalse(csrf_cookie["domain"])
        self.assertEqual(response["Cache-Control"], "no-store")
