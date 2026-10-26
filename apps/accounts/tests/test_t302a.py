from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.test import TestCase
from unittest.mock import patch
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.accounts.preferences import resolve_locale
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember
from .factories import create_test_user


class T302AAccountTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email="main@example.test",
            password="AdminPass-934!",
            first_name="Main",
            phone="+96550000999",
        )

    def test_phone_login_uses_same_user_and_uuid(self):
        user = create_test_user(
            email="phone@example.test",
            password="ExistingPass-934!",
            phone="+96550000000",
            first_name="Test",
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
        user = create_test_user(
            email="no-phone@example.test",
            password="ExistingPass-934!",
            first_name="Test",
        )
        self.assertIsNone(user.phone)
        create_test_user(
            email="phone-one@example.test",
            password="ExistingPass-934!",
            phone="+96550000000",
            first_name="Test",
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            create_test_user(
                email="phone-two@example.test",
                password="ExistingPass-934!",
                phone="+96550000000",
                first_name="Test",
            )

    def test_locale_fallback_uses_only_an_authorized_shop_default(self):
        self.assertEqual(resolve_locale("ur", authorized_shop_locale="ar-KW"), "ur")
        self.assertEqual(resolve_locale(None, authorized_shop_locale="ar-KW"), "ar-KW")
        self.assertEqual(resolve_locale(None), "en")
        self.assertEqual(
            resolve_locale("invalid", authorized_shop_locale="invalid"), "en"
        )

    def test_admin_controls_phone_lifecycle_and_profile_preferences(self):
        user = create_test_user(
            email="lifecycle-phone@example.test",
            password="ExistingPass-934!",
            first_name="Test",
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
            "/api/v1/auth/users/", {"email": "new@example.test", "first_name": "New"}
        )
        self.assertIn(response.status_code, (401, 403))

    def test_admin_created_initial_password_is_one_time_and_gated(self):
        self.client.force_authenticate(user=self.admin)
        supplier, _ = Supplier.objects.get_or_create(singleton_lock=True)
        shop = Tenant.objects.create(
            supplier=supplier,
            name="Account Shop",
            slug="t302a-account-shop",
            max_users=5,
        )
        response = self.client.post(
            "/api/v1/auth/users/",
            {"email": "new@example.test", "first_name": "New", "login_id": "new_user"}
            | {"shop": str(shop.pk), "role": "STAFF"},
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
                "new_password": "048731",
                "new_password_confirm": "048731",
            },
            format="json",
        )
        self.assertEqual(changed.status_code, 200, changed.data)
        user.refresh_from_db()
        self.assertFalse(user.must_change_password)
        self.assertFalse(user.check_password(initial_password))
        self.assertTrue(changed.cookies["refresh"].value == "")

    def test_email_password_reset_endpoints_are_not_available(self):
        for path in (
            "/api/v1/auth/password/reset/",
            "/api/v1/auth/password/reset/confirm/",
        ):
            response = self.client.post(path, {}, format="json")
            self.assertEqual(response.status_code, 404)


class T302AShopSettingsTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email="shop-admin@example.test",
            password="AdminPass-934!",
            first_name="Main",
            phone="+96550000001",
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
        self.user = create_test_user(
            owning_shop=self.shop,
            email="shop-reader@example.test",
            password="ExistingPass-934!",
            first_name="Test",
        )
        TenantMember.objects.create(
            tenant=self.shop, user=self.user, role=ShopRole.STAFF
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
