"""Focused Login ID, PIN, and reviewed Shop ADMIN recovery coverage."""

from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.identity import normalize_login_id
from apps.accounts.models import AuthAttemptBucket, ShopAdminPinResetRequest, User
from apps.accounts.security import generate_initial_password, validate_pin
from apps.accounts.services.shop_admin_pin_reset import resolve_request
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember


class PinPureTests(SimpleTestCase):
    def test_user_id_preserves_case_trims_outer_whitespace_and_rejects_invalid_syntax(self):
        self.assertEqual(normalize_login_id("  Ahmed_01  "), "Ahmed_01")
        for value in ("a", "12ahmed", "ah med", "a@b", "a-b", "a" * 33):
            with self.assertRaises(ValueError):
                normalize_login_id(value)

    def test_pin_format_and_weak_patterns(self):
        validate_pin("048731")
        for value in (
            "123456",
            "654321",
            "121212",
            "000000",
            "111111",
            "12345",
            "1234567",
            "abcdef",
            "٠٤٨٧٣١",
        ):
            with self.assertRaises(ValidationError):
                validate_pin(value)
        for _ in range(20):
            pin = generate_initial_password(None)
            self.assertRegex(pin, r"^[0-9]{6}$")
            validate_pin(pin)


class LoginPinResetTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        supplier, _ = Supplier.objects.get_or_create(singleton_lock=True)
        self.shop = Tenant.objects.create(
            supplier=supplier, name="PIN Shop", slug="pin-shop", max_users=10
        )
        self.main = User.objects.create_superuser(
            first_name="Main",
            email="main-pin@example.test",
            phone="+96550000101",
            password="Legacy-Strong-1!",
        )
        self.admin = User.objects.create_user(
            first_name="Admin",
            login_id="admin_pin",
            email="admin-pin@example.test",
            phone="+96550000102",
            owning_shop=self.shop,
            password="048731",
        )
        TenantMember.objects.create(
            tenant=self.shop,
            user=self.admin,
            role=ShopRole.ADMIN,
            is_active=True,
            created_by=self.main,
        )

    def test_login_id_alias_and_legacy_aliases(self):
        for identifier in (
            "ADMIN_PIN",
            self.admin.user_code,
            self.admin.email,
            self.admin.phone,
        ):
            response = self.client.post(
                "/api/v1/auth/login/",
                {"identifier": identifier, "password": "048731"},
                format="json",
            )
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(response.data["user"]["login_id"], "admin_pin")
        cache.clear()
        for _ in range(5):
            response = self.client.post(
                "/api/v1/auth/login/",
                {"identifier": "admin_pin", "password": "048731"},
                format="json",
            )
            self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(all(bucket.count == 0 for bucket in AuthAttemptBucket.objects.all()))
        self.assertIsNone(self.main.login_id)

    def test_user_id_preserves_entered_case_and_login_is_case_insensitive(self):
        user = User.objects.create_user(
            first_name="Case Preserved",
            login_id="Tailor_A01",
            owning_shop=self.shop,
            password="048731",
        )
        self.assertEqual(user.login_id, "Tailor_A01")
        for identifier in ("Tailor_A01", "tailor_a01", "TAILOR_A01"):
            response = self.client.post(
                "/api/v1/auth/login/",
                {"identifier": identifier, "password": "048731"},
                format="json",
            )
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(response.data["user"]["login_id"], "Tailor_A01")

    def test_password_change_requires_six_digits_and_replaces_old_credential(self):
        self.client.force_authenticate(self.admin)
        changed = self.client.post(
            "/api/v1/auth/users/password/change/",
            {
                "current_password": "048731",
                "new_password": "849203",
                "new_password_confirm": "849203",
            },
            format="json",
        )
        self.assertEqual(changed.status_code, 200, changed.data)
        self.client.force_authenticate(user=None)

        old_login = self.client.post(
            "/api/v1/auth/login/",
            {"identifier": "admin_pin", "password": "048731"},
            format="json",
        )
        self.assertEqual(old_login.status_code, 401)
        new_login = self.client.post(
            "/api/v1/auth/login/",
            {"identifier": "admin_pin", "password": "849203"},
            format="json",
        )
        self.assertEqual(new_login.status_code, 200, new_login.data)

    def test_database_accepts_case_preserved_user_ids(self):
        user = User.objects.create_user(
            first_name="Mixed Case",
            login_id="MixedCase_12",
            owning_shop=self.shop,
            password="048731",
        )
        self.assertEqual(user.login_id, "MixedCase_12")

    def test_casefold_global_uniqueness_and_hashed_pin(self):
        self.assertNotEqual(self.admin.password, "048731")
        self.assertTrue(self.admin.check_password("048731"))
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(
                    first_name="Other",
                    login_id="ADMIN_PIN",
                    owning_shop=self.shop,
                    password="857204",
                )

    def test_database_allows_multiple_legacy_null_login_ids(self):
        for first_name in ("Legacy One", "Legacy Two"):
            User.objects.create_user(
                first_name=first_name,
                owning_shop=self.shop,
                password="Legacy-Strong-1!",
            )
        self.assertEqual(User.objects.filter(login_id__isnull=True).count(), 3)

    def test_new_main_supplier_with_login_id_is_forced_to_replace_bootstrap_secret(self):
        new_main = User.objects.create_superuser(
            email="new-main@example.test",
            password="Bootstrap-Secret-938!",
            first_name="New Main",
            phone="+96550000109",
            login_id="new_main",
        )
        self.assertEqual(new_main.login_id, "new_main")
        self.assertTrue(new_main.must_change_password)

    def test_database_rejects_invalid_login_id_even_when_model_validation_is_bypassed(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.filter(pk=self.admin.pk).update(login_id="not valid")

    def test_database_enforces_abuse_and_reset_state_constraints(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AuthAttemptBucket.objects.create(
                    key="not-a-sha256-key", count=1, window_ends_at=timezone.now()
                )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AuthAttemptBucket.objects.create(
                    key="b" * 64, count=-1, window_ends_at=timezone.now()
                )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ShopAdminPinResetRequest.objects.create(
                    user=self.admin,
                    shop=self.shop,
                    phone=self.admin.phone,
                    status="APPROVED",
                )

    def test_legacy_password_and_six_digit_pin_both_authenticate_without_login_length_gate(self):
        legacy = User.objects.create_user(
            email="legacy-password@example.test",
            first_name="Legacy",
            owning_shop=self.shop,
            login_id="legacy_password",
            password="Existing-Long-Password-934!",
        )
        legacy_response = self.client.post(
            "/api/v1/auth/login/",
            {"identifier": legacy.login_id, "password": "Existing-Long-Password-934!"},
            format="json",
        )
        self.assertEqual(legacy_response.status_code, 200, legacy_response.data)
        self.assertTrue(legacy.check_password("Existing-Long-Password-934!"))

        pin_user = User.objects.create_user(
            email="pin-credential@example.test",
            first_name="Pin",
            owning_shop=self.shop,
            login_id="pin_credential",
            password="048731",
        )
        TenantMember.objects.create(tenant=self.shop, user=pin_user, role=ShopRole.STAFF)
        pin_response = self.client.post(
            "/api/v1/auth/login/",
            {"identifier": pin_user.login_id, "password": "048731"},
            format="json",
        )
        self.assertEqual(pin_response.status_code, 200, pin_response.data)

    def test_viewer_only_user_cannot_login_but_credential_hash_is_preserved(self):
        viewer = User.objects.create_user(
            email="viewer-only@example.test",
            first_name="Viewer",
            owning_shop=self.shop,
            login_id="viewer_only",
            login_enabled=False,
            password="Existing-Long-Password-934!",
        )
        TenantMember.objects.create(tenant=self.shop, user=viewer, role=ShopRole.VIEWER)
        previous_hash = viewer.password
        response = self.client.post(
            "/api/v1/auth/login/",
            {"identifier": viewer.login_id, "password": "Existing-Long-Password-934!"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        refresh = RefreshToken.for_user(viewer)
        refresh["auth_version"] = viewer.auth_version
        access = str(refresh.access_token)
        stale_session = self.client.get(
            "/api/v1/auth/users/me/",
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )
        self.assertEqual(stale_session.status_code, 401)
        viewer.refresh_from_db()
        self.assertEqual(viewer.password, previous_hash)

    def test_stale_current_pin_cannot_change_credentials_twice(self):
        self.client.force_authenticate(self.admin)
        first = self.client.post(
            "/api/v1/auth/users/password/change/",
            {
                "current_password": "048731",
                "new_password": "849203",
                "new_password_confirm": "849203",
            },
            format="json",
        )
        self.assertEqual(first.status_code, 200, first.data)
        stale = self.client.post(
            "/api/v1/auth/users/password/change/",
            {
                "current_password": "048731",
                "new_password": "927405",
                "new_password_confirm": "927405",
            },
            format="json",
        )
        self.assertEqual(stale.status_code, 400, stale.data)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password("849203"))
        self.assertFalse(self.admin.check_password("927405"))
        self.assertEqual(self.admin.auth_version, 2)

        self.client.force_authenticate(user=None)
        old_login = self.client.post(
            "/api/v1/auth/login/",
            {"identifier": "admin_pin", "password": "048731"},
            format="json",
        )
        new_login = self.client.post(
            "/api/v1/auth/login/",
            {"identifier": "admin_pin", "password": "849203"},
            format="json",
        )
        self.assertEqual(old_login.status_code, 401)
        self.assertEqual(new_login.status_code, 200, new_login.data)

    def test_approval_failure_rolls_back_credential_and_request_state(self):
        reset = ShopAdminPinResetRequest.objects.create(
            user=self.admin, shop=self.shop, phone=self.admin.phone
        )
        previous_hash = self.admin.password
        with patch.object(
            ShopAdminPinResetRequest,
            "save",
            side_effect=RuntimeError("injected save failure"),
        ):
            with self.assertRaises(RuntimeError):
                resolve_request(self.main, reset.pk, approve=True)
        self.admin.refresh_from_db()
        reset.refresh_from_db()
        self.assertEqual(self.admin.password, previous_hash)
        self.assertTrue(self.admin.check_password("048731"))
        self.assertEqual(self.admin.auth_version, 1)
        self.assertEqual(reset.status, ShopAdminPinResetRequest.Status.PENDING)

    def test_public_request_is_generic_and_approval_is_one_time(self):
        for phone in ("+96550000102", "+96550000999", "invalid"):
            response = self.client.post(
                "/api/v1/auth/pin-reset-requests/", {"phone": phone}, format="json"
            )
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("admin_pin", str(response.data))
        self.assertEqual(
            ShopAdminPinResetRequest.objects.filter(status="PENDING").count(), 1
        )
        self.assertEqual(
            AuthAttemptBucket.objects.count(),
            2,
            "Only the source and eligible-account buckets should be persisted.",
        )
        reset = ShopAdminPinResetRequest.objects.get(status="PENDING")
        denied = self.client.post(
            f"/api/v1/auth/pin-reset-requests/{reset.pk}/approve/", {}, format="json"
        )
        self.assertIn(denied.status_code, (401, 403))
        self.client.force_authenticate(self.main)
        approved = self.client.post(
            f"/api/v1/auth/pin-reset-requests/{reset.pk}/approve/", {}, format="json"
        )
        self.assertEqual(approved.status_code, 200, approved.data)
        pin = approved.data["temporary_password"]
        self.assertRegex(pin, r"^[0-9]{6}$")
        self.admin.refresh_from_db()
        reset.refresh_from_db()
        self.assertTrue(self.admin.check_password(pin))
        self.assertTrue(self.admin.must_change_password)
        self.assertEqual(self.admin.auth_version, 2)
        self.assertEqual(reset.status, "APPROVED")
        self.assertNotIn(pin, str(reset.__dict__))
        self.assertEqual(approved["Cache-Control"], "no-store")
        repeated = self.client.post(
            f"/api/v1/auth/pin-reset-requests/{reset.pk}/approve/", {}, format="json"
        )
        self.assertEqual(repeated.status_code, 400)

    def test_pending_queue_is_main_supplier_only_and_lists_pending_rows(self):
        other_shop = Tenant.objects.create(
            supplier=self.shop.supplier, name="Other PIN Shop", slug="other-pin-shop", max_users=10
        )
        other_admin = User.objects.create_user(
            first_name="Other Admin", login_id="other_admin", phone="+96550000103",
            owning_shop=other_shop, password="581947",
        )
        TenantMember.objects.create(tenant=other_shop, user=other_admin, role=ShopRole.ADMIN)
        first = ShopAdminPinResetRequest.objects.create(
            user=self.admin, shop=self.shop, phone=self.admin.phone
        )
        second = ShopAdminPinResetRequest.objects.create(
            user=other_admin, shop=other_shop, phone=other_admin.phone
        )
        resolved = ShopAdminPinResetRequest.objects.create(
            user=other_admin, shop=other_shop, phone=other_admin.phone,
            status=ShopAdminPinResetRequest.Status.REJECTED,
            resolved_at=timezone.now(), resolved_by=self.main,
        )

        url = "/api/v1/auth/pin-reset-requests/pending/"
        self.assertIn(self.client.get(url).status_code, (401, 403))
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(url).status_code, 403)

        staff = User.objects.create_user(
            first_name="Staff", login_id="pin_staff", owning_shop=self.shop, password="481729"
        )
        TenantMember.objects.create(tenant=self.shop, user=staff, role=ShopRole.STAFF)
        self.client.force_authenticate(staff)
        self.assertEqual(self.client.get(url).status_code, 403)

        self.client.force_authenticate(self.main)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual({row["id"] for row in response.data}, {str(first.pk), str(second.pk)})
        self.assertNotIn(str(resolved.pk), {row["id"] for row in response.data})
        self.assertEqual({row["shop_id"] for row in response.data}, {str(self.shop.pk), str(other_shop.pk)})
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertNotIn("password", str(response.data).lower())

    def test_reject_endpoint_permissions_response_and_resolution_safety(self):
        reset = ShopAdminPinResetRequest.objects.create(
            user=self.admin, shop=self.shop, phone=self.admin.phone
        )
        url = f"/api/v1/auth/pin-reset-requests/{reset.pk}/reject/"
        self.assertIn(self.client.post(url, {}, format="json").status_code, (401, 403))

        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.post(url, {}, format="json").status_code, 403)

        self.client.force_authenticate(self.main)
        rejected = self.client.post(url, {}, format="json")
        self.assertEqual(rejected.status_code, 200, rejected.data)
        self.assertEqual(rejected.data, {"id": str(reset.pk), "status": "REJECTED"})
        self.assertNotIn("temporary_password", rejected.data)
        self.admin.refresh_from_db()
        reset.refresh_from_db()
        self.assertTrue(self.admin.check_password("048731"))
        self.assertEqual(reset.status, ShopAdminPinResetRequest.Status.REJECTED)

        already_resolved = self.client.post(url, {}, format="json")
        self.assertEqual(already_resolved.status_code, 400)
        missing = self.client.post(
            "/api/v1/auth/pin-reset-requests/00000000-0000-0000-0000-000000000000/reject/",
            {}, format="json",
        )
        self.assertEqual(missing.status_code, 404)
