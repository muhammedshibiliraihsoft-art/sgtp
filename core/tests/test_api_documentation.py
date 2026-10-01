import yaml

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember


class InternalApiDocumentationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.supplier = Supplier.objects.get(singleton_lock=True)
        cls.shop = Tenant.objects.create(
            supplier=cls.supplier,
            name="Documentation Test Shop",
            slug="documentation-test-shop",
            max_users=10,
        )
        cls.main_supplier = User.objects.create_superuser(
            email="docs-main@example.test",
            password="Safe-Test-Password-293!",
            first_name="Docs Main",
            phone="+96550009991",
        )
        cls.shop_users = {}
        for role in (ShopRole.ADMIN, ShopRole.STAFF, ShopRole.VIEWER):
            user = User.objects.create_user(
                email=f"docs-{role.lower()}@example.test",
                password="Safe-Test-Password-293!",
                first_name=f"Docs {role}",
                phone=f"+9655000998{(ShopRole.ADMIN, ShopRole.STAFF, ShopRole.VIEWER).index(role)}",
                owning_shop=cls.shop,
            )
            TenantMember.objects.create(user=user, tenant=cls.shop, role=role)
            cls.shop_users[role] = user

    def test_anonymous_docs_schema_and_root_do_not_return_api_content(self):
        for url in (reverse("swagger-ui"), reverse("schema")):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("admin:login"), response["Location"])
                self.assertNotIn(b"openapi", response.content.lower())
                self.assertIn("private", response["Cache-Control"])
                self.assertIn("no-store", response["Cache-Control"])

        redirected = self.client.get("/api/docs/?next=https://outside.example")
        self.assertEqual(redirected.status_code, 302)
        self.assertTrue(redirected["Location"].startswith("/admin/login/"))

        root = self.client.get("/")
        self.assertEqual(root.status_code, 302)
        self.assertEqual(root["Location"], reverse("api-browser"))
        self.assertNotIn(b"api test", root.content.lower())

    def test_only_active_main_supplier_without_password_gate_can_read_docs(self):
        for role, user in self.shop_users.items():
            with self.subTest(role=role):
                self.client.force_login(user)
                for url in (reverse("swagger-ui"), reverse("schema")):
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 404)
                    self.assertNotIn(b"openapi", response.content.lower())
                self.client.logout()

        inactive_main = User.objects.create_superuser(
            email="inactive-docs-main@example.test",
            password="Safe-Test-Password-293!",
            first_name="Inactive Main",
            phone="+96550009992",
        )
        inactive_main.is_active = False
        inactive_main.save(update_fields=("is_active",))
        self.client.force_login(inactive_main)
        self.assertEqual(self.client.get(reverse("schema")).status_code, 302)

        gated_main = User.objects.create_superuser(
            email="gated-docs-main@example.test",
            password="Safe-Test-Password-293!",
            first_name="Gated Main",
            phone="+96550009993",
        )
        gated_main.must_change_password = True
        gated_main.save(update_fields=("must_change_password",))
        self.client.force_login(gated_main)
        response = self.client.get(reverse("schema"))
        self.assertEqual(response.status_code, 404)
        self.assertNotIn(b"openapi", response.content.lower())

    def test_main_supplier_can_read_valid_schema_and_swagger_without_token_storage(
        self,
    ):
        self.client.force_login(self.main_supplier)

        docs = self.client.get(reverse("swagger-ui"))
        self.assertEqual(docs.status_code, 200)
        self.assertIn(reverse("schema"), docs.content.decode())
        self.assertIn("private", docs["Cache-Control"])
        self.assertIn("no-store", docs["Cache-Control"])
        self.assertFalse(
            settings.SPECTACULAR_SETTINGS["SWAGGER_UI_SETTINGS"]["persistAuthorization"]
        )

        response = self.client.get(reverse("schema"), HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("private", response["Cache-Control"])
        self.assertIn("no-store", response["Cache-Control"])
        schema = yaml.safe_load(response.content)
        self.assertEqual(schema["openapi"], "3.0.3")
        self.assertIn("/api/v1/shops/{shop_id}/clients/", schema["paths"])
        self.assertNotIn("/api/v1/shops/{shop_id}/designs/", schema["paths"])
        self.assertNotIn("cookieAuth", schema["components"]["securitySchemes"])

    def test_django_admin_login_returns_main_supplier_to_docs(self):
        response = self.client.post(
            reverse("admin:login"),
            {
                "username": self.main_supplier.email,
                "password": "Safe-Test-Password-293!",
                "next": reverse("swagger-ui"),
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain[-1][0], reverse("swagger-ui"))
        self.assertContains(response, 'id="swagger-ui"')

    def test_docs_session_does_not_authenticate_business_api(self):
        self.client.force_login(self.main_supplier)
        response = self.client.get(
            f"/api/v1/shops/{self.shop.pk}/clients/",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_logout_removes_docs_and_schema_access_and_api_auth_is_absent(self):
        self.client.force_login(self.main_supplier)
        self.assertEqual(self.client.get(reverse("schema")).status_code, 200)
        self.client.logout()
        for url in (reverse("swagger-ui"), reverse("schema")):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertNotIn(b"openapi", response.content.lower())
        self.assertEqual(self.client.get("/api-auth/").status_code, 404)
