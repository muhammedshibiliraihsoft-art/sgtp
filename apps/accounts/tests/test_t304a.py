from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.admin import UserAdmin
from apps.accounts.models import User
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember
from .factories import create_test_user


class T304AIdentityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email="main@example.test",
            phone="+96550000001",
            first_name="Main",
            password="Strong-Admin-934!",
        )

    def test_user_code_and_optional_contacts_are_generated_for_normal_user(self):
        user = create_test_user(
            first_name="  Noor ", last_name="  Khan ", password="Strong-User-934!"
        )
        self.assertRegex(user.user_code, r"^U-[23456789ABCDEFGHJKMNPQRSTUVWXYZ]{16}$")
        self.assertIsNone(user.email)
        self.assertIsNone(user.phone)
        self.assertEqual(user.full_name, "Noor Khan")
        self.assertEqual(str(user), "Noor Khan")

    def test_authorized_account_creation_supports_user_without_email_or_phone(self):
        self.client.force_authenticate(user=self.admin)
        supplier, _ = Supplier.objects.get_or_create(singleton_lock=True)
        shop = Tenant.objects.create(
            supplier=supplier, name="Creation Shop", slug="t304a-create-shop", max_users=5
        )
        response = self.client.post(
            "/api/v1/auth/users/",
            {"first_name": "Noor", "shop": str(shop.pk), "role": "STAFF"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(response["Pragma"], "no-cache")
        self.assertIsNone(response.data["email"])
        user = User.objects.get(user_code=response.data["user_code"])
        self.assertIsNone(user.phone)
        self.assertTrue(user.check_password(response.data["initial_password"]))

    def test_user_code_is_immutable_and_not_caller_supplied(self):
        user = create_test_user(first_name="Noor")
        code = user.user_code
        user.user_code = "U-2345678923456789"
        with self.assertRaisesMessage(Exception, "User ID is immutable"):
            user.save()
        with self.assertRaisesMessage(ValueError, "user_code is generated"):
            create_test_user(first_name="Other", user_code=code)

    def test_user_code_collision_retries_only_that_constraint(self):
        existing = create_test_user(first_name="First")
        with patch(
            "apps.accounts.models.users.generate_user_code",
            side_effect=[existing.user_code, "U-2345678923456789"],
        ) as generate:
            created = create_test_user(first_name="Second")
        self.assertEqual(generate.call_count, 2)
        self.assertNotEqual(existing.user_code, created.user_code)

    def test_first_name_is_required_and_trimmed_and_last_name_optional(self):
        with self.assertRaisesMessage(ValueError, "first_name field must be set"):
            create_test_user(first_name="   ")
        user = create_test_user(first_name="  Noor  ")
        self.assertEqual(user.first_name, "Noor")
        self.assertEqual(user.full_name, "Noor")

    def test_superuser_requires_nonblank_email_phone_and_first_name(self):
        with self.assertRaisesMessage(ValueError, "Superusers require email"):
            User.objects.create_superuser(
                email=" ", phone=" ", first_name="Main", password="Secret-939!"
            )

    def test_email_is_trimmed_and_casefold_unique(self):
        user = create_test_user(
            first_name="Noor", email="  Person@Example.test "
        )
        self.assertEqual(user.email, "person@example.test")
        with self.assertRaises(Exception):
            create_test_user(first_name="Other", email="PERSON@example.test")

    def test_user_id_email_and_phone_login_resolve_same_uuid(self):
        user = create_test_user(
            first_name="Noor",
            email="Person@Example.test",
            phone="+96550000002",
            password="Strong-User-935!",
        )
        self.client.force_authenticate(user=None)
        for identifier in (user.user_code, "PERSON@example.TEST", "+965 5000 0002"):
            response = self.client.post(
                "/api/v1/auth/login/",
                {"identifier": identifier, "password": "Strong-User-935!"},
                format="json",
            )
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(response.data["user"]["id"], str(user.pk))
            self.assertEqual(response.data["user"]["user_code"], user.user_code)

    def test_no_email_reset_request_is_generic_and_sends_nothing(self):
        response = self.client.post("/api/v1/auth/password/reset/", {}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(response["Pragma"], "no-cache")

    def test_main_supplier_can_reset_credentials_once_and_sessions_are_revoked(self):
        user = create_test_user(first_name="Noor", password="Old-Strong-936!")
        login = self.client.post(
            "/api/v1/auth/login/",
            {"identifier": user.user_code, "password": "Old-Strong-936!"},
            format="json",
        )
        self.assertEqual(login.status_code, 200, login.data)
        old_version = user.auth_version
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/v1/auth/users/{user.pk}/reset-credentials/", {}, format="json"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(response["Pragma"], "no-cache")
        self.assertEqual(response.data["user_code"], user.user_code)
        user.refresh_from_db()
        self.assertTrue(user.must_change_password)
        self.assertEqual(user.auth_version, old_version + 1)
        self.assertTrue(user.check_password(response.data["temporary_password"]))
        self.client.force_authenticate(user=None)
        gated = self.client.get(
            "/api/v1/auth/users/me/",
            HTTP_AUTHORIZATION=f"Bearer {login.data['access']}",
        )
        self.assertEqual(gated.status_code, 401)

    def test_shop_admin_cannot_reset_global_credentials(self):
        supplier, _ = Supplier.objects.get_or_create(singleton_lock=True)
        shop = Tenant.objects.create(
            supplier=supplier, name="Identity Shop", slug="identity-shop", max_users=5
        )
        shop_admin = create_test_user(
            owning_shop=shop,
            first_name="Shop",
            email="shop@example.test",
            phone="+96550000003",
            password="Shop-Strong-937!",
        )
        TenantMember.objects.create(tenant=shop, user=shop_admin, role=ShopRole.ADMIN)
        target = create_test_user(first_name="Target")
        self.client.force_authenticate(user=shop_admin)
        response = self.client.post(
            f"/api/v1/auth/users/{target.pk}/reset-credentials/", {}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_active_shop_admin_cannot_remove_required_contacts(self):
        supplier, _ = Supplier.objects.get_or_create(
            singleton_lock=True, defaults={"name": "Main Supplier"}
        )
        shop = Tenant.objects.create(
            supplier=supplier,
            name="Contact Shop",
            slug="contact-shop-t304a",
            max_users=5,
        )
        shop_admin = create_test_user(
            owning_shop=shop,
            first_name="Shop", email="shop-contact@example.test", phone="+96550000005"
        )
        TenantMember.objects.create(tenant=shop, user=shop_admin, role=ShopRole.ADMIN)
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/auth/users/{shop_admin.pk}/",
            {"phone": ""},
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.data)
        shop_admin.refresh_from_db()
        self.assertEqual(shop_admin.phone, "+96550000005")

    def test_global_user_delete_is_disabled_and_admin_delete_denied(self):
        user = create_test_user(first_name="Retained")
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/v1/auth/users/{user.pk}/")
        self.assertEqual(response.status_code, 405)
        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        model_admin = UserAdmin(User, AdminSite())
        self.assertFalse(model_admin.has_delete_permission(None))
        self.assertNotIn(
            "auth_user_password_change",
            {url.name for url in model_admin.get_urls()},
        )

    def test_createsuperuser_cli_collects_required_fields_and_generates_code(self):
        with patch.dict("os.environ", {"DJANGO_SUPERUSER_PASSWORD": "Strong-CLI-938!"}):
            call_command(
                "createsuperuser",
                interactive=False,
                email="cli@example.test",
                first_name="CLI",
                phone="+96550000004",
                verbosity=0,
            )
        user = User.objects.get(email="cli@example.test")
        self.assertTrue(user.is_superuser)
        self.assertRegex(user.user_code, r"^U-[23456789ABCDEFGHJKMNPQRSTUVWXYZ]{16}$")
