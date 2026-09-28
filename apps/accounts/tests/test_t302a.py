from urllib.parse import urlparse, parse_qs

from django.core import mail
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from unittest.mock import patch
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.accounts.preferences import resolve_locale
from apps.tenants.models import Supplier, Tenant


class T302AAccountTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email="main@example.test", password="AdminPass-934!"
        )

    def test_phone_login_uses_same_user_and_uuid(self):
        user = User.objects.create_user(
            email="phone@example.test",
            password="ExistingPass-934!",
            phone="+96550000000",
        )
        response = self.client.post(
            "/api/v1/auth/login/",
            {"identifier": "+965 5000 0000", "password": "ExistingPass-934!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["user"]["id"], str(user.pk))
        self.assertNotIn("refresh", response.data)
        self.assertIn("refresh", response.cookies)

    def test_phone_is_unique_and_optional_for_existing_users(self):
        user = User.objects.create_user(
            email="no-phone@example.test", password="ExistingPass-934!"
        )
        self.assertIsNone(user.phone)
        User.objects.create_user(
            email="phone-one@example.test",
            password="ExistingPass-934!",
            phone="+96550000000",
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user(
                email="phone-two@example.test",
                password="ExistingPass-934!",
                phone="+96550000000",
            )

    def test_locale_fallback_uses_only_an_authorized_shop_default(self):
        self.assertEqual(resolve_locale("ur", authorized_shop_locale="ar-KW"), "ur")
        self.assertEqual(resolve_locale(None, authorized_shop_locale="ar-KW"), "ar-KW")
        self.assertEqual(resolve_locale(None), "en")
        self.assertEqual(
            resolve_locale("invalid", authorized_shop_locale="invalid"), "en"
        )

    def test_password_reset_token_expires(self):
        user = User.objects.create_user(
            email="expired@example.test", password="ExistingPass-934!"
        )
        generator = PasswordResetTokenGenerator()
        with (
            override_settings(PASSWORD_RESET_TIMEOUT=0),
            patch.object(generator, "_num_seconds", side_effect=[100000, 100001]),
        ):
            token = generator.make_token(user)
            self.assertFalse(generator.check_token(user, token))

    def test_admin_controls_phone_lifecycle_and_profile_preferences(self):
        user = User.objects.create_user(
            email="lifecycle-phone@example.test", password="ExistingPass-934!"
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/auth/users/{user.pk}/", {"phone": "+965 5000 0000"}, format="json"
        )
        self.assertEqual(response.status_code, 200, response.data)
        user.refresh_from_db()
        self.assertEqual(user.phone, "+96550000000")

        self.client.force_authenticate(user=user)
        preferences = self.client.patch(
            "/api/v1/auth/users/update_profile/",
            {
                "preferred_locale": "ar-KW",
                "appearance_preference": "dark",
                "is_active": False,
            },
            format="json",
        )
        self.assertEqual(preferences.status_code, 200, preferences.data)
        user.refresh_from_db()
        self.assertEqual(user.preferred_locale, "ar-KW")
        self.assertEqual(user.appearance_preference, "dark")
        self.assertTrue(user.is_active)

    def test_anonymous_account_creation_is_denied(self):
        response = self.client.post(
            "/api/v1/auth/users/", {"email": "new@example.test"}
        )
        self.assertIn(response.status_code, (401, 403))

    def test_admin_created_initial_password_is_one_time_and_gated(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/auth/users/", {"email": "new@example.test"}
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(response["Pragma"], "no-cache")
        initial_password = response.data["initial_password"]
        user = User.objects.get(email="new@example.test")
        self.assertTrue(user.must_change_password)
        self.assertTrue(user.check_password(initial_password))
        self.assertNotIn("initial_password", User.objects.values().get(pk=user.pk))

        login = self.client.post(
            "/api/v1/auth/login/",
            {"identifier": user.email, "password": initial_password},
            format="json",
        )
        self.assertEqual(login.status_code, 200, login.data)
        self.client.force_authenticate(user=None)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        gated = self.client.get("/api/v1/auth/users/me/")
        self.assertEqual(gated.status_code, 403)
        changed = self.client.post(
            "/api/v1/auth/users/password/change/",
            {
                "current_password": initial_password,
                "new_password": "NewSecure-936!Pass",
                "new_password_confirm": "NewSecure-936!Pass",
            },
            format="json",
        )
        self.assertEqual(changed.status_code, 200, changed.data)
        user.refresh_from_db()
        self.assertFalse(user.must_change_password)
        self.assertFalse(user.check_password(initial_password))
        self.assertTrue(changed.cookies["refresh"].value == "")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        PASSWORD_RESET_URL="https://frontend.example.test/reset",
    )
    def test_email_reset_is_generic_single_use_and_revokes_sessions(self):
        user = User.objects.create_user(
            email="reset@example.test", password="ExistingPass-934!"
        )
        logged_in = self.client.post(
            "/api/v1/auth/login/",
            {"email": user.email, "password": "ExistingPass-934!"},
            format="json",
        )
        refresh_value = logged_in.cookies["refresh"].value
        csrf_value = logged_in.cookies["csrftoken"].value
        request_existing = self.client.post(
            "/api/v1/auth/password/reset/", {"email": user.email}
        )
        request_unknown = self.client.post(
            "/api/v1/auth/password/reset/", {"email": "absent@example.test"}
        )
        self.assertEqual(request_existing.status_code, request_unknown.status_code)
        self.assertEqual(request_existing.data, request_unknown.data)
        self.assertEqual(len(mail.outbox), 1)
        query = parse_qs(
            urlparse(
                mail.outbox[0].body.split("Use this link to reset your password: ")[1]
            ).query
        )

        confirm = self.client.post(
            "/api/v1/auth/password/reset/confirm/",
            {
                "uid": query["uid"][0],
                "token": query["token"][0],
                "new_password": "ResetSecure-937!Pass",
                "new_password_confirm": "ResetSecure-937!Pass",
            },
            format="json",
        )
        self.assertEqual(confirm.status_code, 200, confirm.data)
        user.refresh_from_db()
        self.assertFalse(user.check_password("ExistingPass-934!"))
        self.assertTrue(user.check_password("ResetSecure-937!Pass"))
        self.client.force_authenticate(user=None)
        stale_access = self.client.get(
            "/api/v1/auth/users/me/",
            HTTP_AUTHORIZATION=f"Bearer {logged_in.data['access']}",
        )
        self.assertEqual(stale_access.status_code, 401)
        replay = self.client.post(
            "/api/v1/auth/password/reset/confirm/",
            {
                "uid": query["uid"][0],
                "token": query["token"][0],
                "new_password": "AnotherSecure-938!Pass",
                "new_password_confirm": "AnotherSecure-938!Pass",
            },
            format="json",
        )
        self.assertEqual(replay.status_code, 400)
        self.client.cookies["refresh"] = refresh_value
        self.client.cookies["csrftoken"] = csrf_value
        refresh = self.client.post(
            "/api/v1/auth/token/refresh/",
            HTTP_X_CSRFTOKEN=csrf_value,
            format="json",
        )
        self.assertEqual(refresh.status_code, 401)


class T302AShopSettingsTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="shop-reader@example.test", password="ExistingPass-934!"
        )
        self.admin = User.objects.create_superuser(
            email="shop-admin@example.test", password="AdminPass-934!"
        )
        supplier = Supplier.objects.get(singleton_lock=True)
        self.shop = Tenant.objects.create(
            supplier=supplier,
            name="Test Shop",
            slug="t302a-shop",
            max_users=10,
            created_by=self.admin,
            default_locale="ar-KW",
            default_timezone="Asia/Kuwait",
            default_currency="KWD",
        )

    def test_regular_user_global_reads_do_not_expose_new_shop_settings(self):
        self.client.force_authenticate(user=self.user)
        listing = self.client.get("/api/v1/tenants/")
        detail = self.client.get(f"/api/v1/tenants/{self.shop.pk}/")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(detail.status_code, 200)
        for payload in (listing.data["results"][0], detail.data):
            self.assertNotIn("default_locale", payload)
            self.assertNotIn("default_timezone", payload)
            self.assertNotIn("default_currency", payload)
        update = self.client.patch(
            f"/api/v1/tenants/{self.shop.pk}/",
            {"default_locale": "ur"},
            format="json",
        )
        self.assertEqual(update.status_code, 403)
        self.shop.refresh_from_db()
        self.assertEqual(self.shop.default_locale, "ar-KW")

    def test_main_supplier_admin_can_read_and_update_shop_defaults(self):
        self.client.force_authenticate(user=self.admin)
        detail = self.client.get(f"/api/v1/tenants/{self.shop.pk}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["default_currency"], "KWD")
        updated = self.client.patch(
            f"/api/v1/tenants/{self.shop.pk}/",
            {
                "default_locale": "ur",
            },
            format="json",
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        self.shop.refresh_from_db()
        self.assertEqual(self.shop.default_locale, "ur")
