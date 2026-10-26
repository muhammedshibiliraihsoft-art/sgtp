"""Focused tests for authenticated-client identity and attempt accounting."""

from datetime import timedelta
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from apps.accounts.abuse import consume, release, source
from apps.accounts.models import AuthAttemptBucket


class AuthSourceTests(SimpleTestCase):
    @override_settings(AUTH_TRUSTED_CLIENT_IP_HEADER="REMOTE_ADDR")
    def test_default_ignores_spoofed_proxy_headers(self):
        request = APIRequestFactory().get(
            "/",
            HTTP_CF_CONNECTING_IP="2001:db8::1",
            HTTP_X_REAL_IP="198.51.100.55",
            HTTP_X_FORWARDED_FOR="198.51.100.23, 203.0.113.4",
            REMOTE_ADDR="172.20.0.5",
        )
        self.assertEqual(source(request), "172.20.0.5")

    @override_settings(AUTH_TRUSTED_CLIENT_IP_HEADER="HTTP_CF_CONNECTING_IP")
    def test_render_trusted_proxy_mode_uses_single_cloudflare_header(self):
        request = APIRequestFactory().get(
            "/",
            HTTP_CF_CONNECTING_IP="2001:db8::1",
            HTTP_X_FORWARDED_FOR="198.51.100.23, 203.0.113.4",
            REMOTE_ADDR="172.20.0.5",
        )
        self.assertEqual(source(request), "2001:db8::1")

    @override_settings(AUTH_TRUSTED_CLIENT_IP_HEADER="HTTP_X_REAL_IP")
    def test_native_vps_trusted_proxy_mode_uses_sanitized_x_real_ip(self):
        request = APIRequestFactory().get(
            "/",
            HTTP_X_REAL_IP="198.51.100.55",
            HTTP_X_FORWARDED_FOR="198.51.100.23, 203.0.113.4",
            REMOTE_ADDR="127.0.0.1",
        )
        self.assertEqual(source(request), "198.51.100.55")

    @override_settings(AUTH_TRUSTED_CLIENT_IP_HEADER="HTTP_X_REAL_IP")
    def test_missing_or_invalid_trusted_header_falls_back_to_socket_peer(self):
        request = APIRequestFactory().get(
            "/", HTTP_X_REAL_IP="not-an-ip", REMOTE_ADDR="192.0.2.10"
        )
        self.assertEqual(source(request), "192.0.2.10")

    def test_falls_back_to_valid_socket_address(self):
        request = APIRequestFactory().get("/", REMOTE_ADDR="192.0.2.10")
        self.assertEqual(source(request), "192.0.2.10")

    @override_settings(AUTH_TRUSTED_CLIENT_IP_HEADER="REMOTE_ADDR")
    def test_untrusted_forwarding_header_does_not_become_the_client_identity(self):
        request = APIRequestFactory().get(
            "/", HTTP_CF_CONNECTING_IP="not-an-ip", REMOTE_ADDR="192.0.2.10"
        )
        self.assertEqual(source(request), "192.0.2.10")


class AuthAttemptAccountingTests(TestCase):
    def test_successful_authentication_can_release_its_reserved_failure_slot(self):
        value = "198.51.100.23"
        self.assertTrue(consume("login-source", value, limit=1))
        release("login-source", value, limit=1)
        self.assertTrue(consume("login-source", value, limit=1))
        bucket = AuthAttemptBucket.objects.get()
        self.assertEqual(bucket.count, 1)
        self.assertIsNone(bucket.blocked_until)

    def test_attempt_limit_is_persistent_and_blocks_after_threshold(self):
        self.assertTrue(consume("login-source", "192.0.2.20", limit=2))
        self.assertTrue(consume("login-source", "192.0.2.20", limit=2))
        self.assertFalse(consume("login-source", "192.0.2.20", limit=2))
        bucket = AuthAttemptBucket.objects.get()
        self.assertEqual(bucket.count, 3)
        self.assertEqual(bucket.blocked_until, bucket.window_ends_at)
        self.assertGreater(bucket.window_ends_at, timezone.now())

    def test_expired_attempt_window_resets_count_and_lockout(self):
        self.assertTrue(consume("login-source", "192.0.2.30", limit=1))
        bucket = AuthAttemptBucket.objects.get()
        bucket.window_ends_at = timezone.now() - timedelta(seconds=1)
        bucket.blocked_until = bucket.window_ends_at
        bucket.count = 2
        bucket.save()
        self.assertTrue(consume("login-source", "192.0.2.30", limit=1))
        bucket.refresh_from_db()
        self.assertEqual(bucket.count, 1)
        self.assertIsNone(bucket.blocked_until)

    @patch("apps.accounts.abuse.secrets.randbelow", return_value=0)
    def test_consumption_performs_bounded_stale_bucket_cleanup(self, _random_value):
        stale = AuthAttemptBucket.objects.create(
            key="a" * 64,
            count=2,
            window_ends_at=timezone.now() - timedelta(hours=2),
        )
        self.assertTrue(consume("login-source", "192.0.2.44", limit=5))
        self.assertFalse(AuthAttemptBucket.objects.filter(pk=stale.pk).exists())
