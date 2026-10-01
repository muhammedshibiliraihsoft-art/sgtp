from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.tenants.models import Supplier, Tenant


class ApiBrowserTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        supplier = Supplier.objects.get(singleton_lock=True)
        shop = Tenant.objects.create(
            supplier=supplier,
            name="API Browser Test Shop",
            slug="api-browser-test-shop",
            max_users=5,
        )
        cls.main_supplier = User.objects.create_superuser(
            email="browser-main@example.test",
            password="Safe-Test-Password-293!",
            first_name="Browser Main",
            phone="+96550009991",
        )
        cls.shop_user = User.objects.create_user(
            email="browser-shop@example.test",
            password="Safe-Test-Password-293!",
            first_name="Browser Shop",
            phone="+96550009992",
            owning_shop=shop,
        )

    def test_browser_page_redirects_anonymous_and_is_not_cacheable(self):
        response = self.client.get(reverse("api-browser"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response["Location"])
        self.assertIn("private", response["Cache-Control"])
        self.assertIn("no-store", response["Cache-Control"])

        root = self.client.get("/")
        self.assertEqual(root.status_code, 302)
        self.assertEqual(root["Location"], reverse("api-browser"))

    def test_main_supplier_sees_browser_and_non_supplier_gets_uniform_404(self):
        self.client.force_login(self.main_supplier)
        response = self.client.get(reverse("api-browser"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("noindex", response["X-Robots-Tag"])
        self.assertContains(response, "SGTP API Browser")
        self.assertContains(response, "Paste access JWT")
        self.assertContains(response, "api_browser.js")
        self.assertContains(response, "Open Swagger docs")

        self.client.force_login(self.shop_user)
        denied = self.client.get(reverse("api-browser"))
        self.assertEqual(denied.status_code, 404)
        self.assertNotIn(b"implemented operations", denied.content)

    def test_admin_session_alone_does_not_authorize_business_api(self):
        self.client.force_login(self.main_supplier)
        response = self.client.get(
            f"/api/v1/shops/{Tenant.objects.get(slug='api-browser-test-shop').pk}/clients/",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_browser_token_is_not_persisted_and_calls_use_bearer_jwt(self):
        script_path = (
            Path(settings.BASE_DIR) / "core" / "static" / "core" / "api_browser.js"
        )
        script = script_path.read_text(encoding="utf-8")
        self.assertNotIn("localStorage", script)
        self.assertNotIn("sessionStorage", script)
        self.assertIn("headers.Authorization = `Bearer ${accessToken}`", script)
        self.assertIn('"/api/v1/"', script)
        self.assertIn('"X-CSRFToken"', script)
