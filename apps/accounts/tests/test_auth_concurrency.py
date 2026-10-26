"""PostgreSQL-only races for auth limits, identity, and credential changes."""

import threading
from concurrent.futures import ThreadPoolExecutor

from django.db import close_old_connections, connection
from django.test import TransactionTestCase
from rest_framework.exceptions import ValidationError

from apps.accounts.abuse import consume
from apps.accounts.models import AuthAttemptBucket, ShopAdminPinResetRequest, User
from apps.accounts.security import set_password_and_revoke_sessions
from apps.accounts.services.shop_admin_pin_reset import resolve_request, submit_request
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember
from apps.tenants.services.shop_accounts import create_shop_account


class AuthConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.assertEqual(connection.vendor, "postgresql", "Auth lock tests require PostgreSQL.")
        supplier, _ = Supplier.objects.get_or_create(singleton_lock=True)
        self.shop = Tenant.objects.create(
            supplier=supplier, name="Auth Race Shop", slug="auth-race-shop", max_users=10
        )
        self.main = User.objects.create_superuser(
            email="auth-race-main@example.test",
            password="Test-Legacy-Admin-1!",
            first_name="Main",
            phone="+96550001001",
        )
        self.admin = User.objects.create_user(
            email="auth-race-admin@example.test",
            password="048731",
            first_name="Shop Admin",
            phone="+96550001002",
            login_id="race_admin",
            owning_shop=self.shop,
        )
        TenantMember.objects.create(
            tenant=self.shop, user=self.admin, role=ShopRole.ADMIN, is_active=True
        )

    @staticmethod
    def concurrently(*operations):
        barrier = threading.Barrier(len(operations))

        def run(operation):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    return operation()
                except ValidationError:
                    return "conflict"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=len(operations)) as pool:
            return list(pool.map(run, operations))

    def test_concurrent_failed_attempts_do_not_lose_bucket_increments(self):
        barrier = threading.Barrier(12)

        def attempt():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return consume("login-account", "shared-test-account", limit=4)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(lambda _index: attempt(), range(12)))

        self.assertEqual(sum(results), 4)
        bucket = AuthAttemptBucket.objects.get()
        self.assertEqual(bucket.count, 5)
        self.assertEqual(bucket.blocked_until, bucket.window_ends_at)

    def test_casefold_login_id_race_returns_one_controlled_conflict(self):
        base_data = {
            "first_name": "Race User",
            "email": "race-user-one@example.test",
            "phone": "+96550001003",
        }

        def create(data):
            return lambda: create_shop_account(
                self.admin, self.shop.pk, ShopRole.STAFF, data
            ) and "created"

        results = self.concurrently(
            create({**base_data, "login_id": "race_login"}),
            create({**base_data, "email": "race-user-two@example.test", "phone": "+96550001004", "login_id": "RACE_LOGIN"}),
        )
        self.assertCountEqual(results, ["created", "conflict"])
        self.assertEqual(User.objects.filter(login_id__iexact="race_login").count(), 1)

    def test_simultaneous_shop_admin_requests_create_one_pending_row(self):
        self.concurrently(
            lambda: submit_request(self.admin, self.admin.phone) or "submitted",
            lambda: submit_request(self.admin, self.admin.phone) or "submitted",
        )
        self.assertEqual(
            ShopAdminPinResetRequest.objects.filter(
                user=self.admin, status=ShopAdminPinResetRequest.Status.PENDING
            ).count(),
            1,
        )

    def test_approval_and_rejection_race_resolves_once_and_issues_pin_only_on_approval(self):
        reset = ShopAdminPinResetRequest.objects.create(
            user=self.admin, shop=self.shop, phone=self.admin.phone
        )
        issued_pins = []

        def approve():
            _, pin = resolve_request(self.main, reset.pk, approve=True)
            if pin:
                issued_pins.append(pin)
            return "approved"

        def reject():
            resolve_request(self.main, reset.pk, approve=False)
            return "rejected"

        results = self.concurrently(approve, reject)
        self.assertEqual(results.count("conflict"), 1)
        self.assertEqual(sum(result in {"approved", "rejected"} for result in results), 1)
        reset.refresh_from_db()
        self.admin.refresh_from_db()
        if reset.status == ShopAdminPinResetRequest.Status.APPROVED:
            self.assertEqual(len(issued_pins), 1)
            self.assertTrue(self.admin.check_password(issued_pins[0]))
            self.assertTrue(self.admin.must_change_password)
        else:
            self.assertEqual(reset.status, ShopAdminPinResetRequest.Status.REJECTED)
            self.assertEqual(issued_pins, [])
            self.assertTrue(self.admin.check_password("048731"))

    def test_stale_current_pin_loses_concurrent_change_race(self):
        def change(pin):
            def validate(locked_user):
                if not locked_user.check_password("048731"):
                    raise ValidationError("Current PIN is incorrect.")

            return lambda: set_password_and_revoke_sessions(
                self.admin, pin, validate_locked_user=validate
            ) and "changed"

        results = self.concurrently(change("849203"), change("927405"))
        self.assertCountEqual(results, ["changed", "conflict"])
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.auth_version, 2)
        self.assertTrue(
            self.admin.check_password("849203") or self.admin.check_password("927405")
        )
