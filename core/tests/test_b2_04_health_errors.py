import pytest
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from django.db import DatabaseError

class HealthCheckTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_live(self):
        """Liveness probe should return 200."""
        response = self.client.get('/api/health/live/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "alive"})

    def test_health_ready_success(self):
        """Readiness probe should return 200 when DB is connected."""
        response = self.client.get('/api/health/ready/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ready"})

    @patch('core.health.connection.ensure_connection')
    def test_health_ready_failure(self, mock_ensure_connection):
        """Readiness probe should return 503 when DB fails."""
        mock_ensure_connection.side_effect = DatabaseError("DB is down")
        response = self.client.get('/api/health/ready/')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.json(), {"status": "unavailable"})


class ErrorEnvelopeTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_validation_error_is_enveloped(self):
        """A standard DRF validation error should be wrapped in 'errors'."""
        # Sending empty data to login triggers a 400 Bad Request (Validation Error)
        response = self.client.post('/api/v1/auth/login/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Expected structure: {"errors": {"email": [...], "password": [...]}}
        data = response.json()
        self.assertIn("errors", data)
        self.assertIn("email", data["errors"])
        self.assertIn("password", data["errors"])

    def test_authentication_error_is_enveloped(self):
        """A standard DRF authentication error should be wrapped in 'errors'."""
        response = self.client.get('/api/v1/tenants/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        self.assertIn("errors", data)
        self.assertIn("detail", data["errors"])

    @patch('apps.tenants.views.TenantViewSet.list')
    def test_unhandled_exception_is_safely_enveloped(self, mock_list):
        """An unhandled 500 error should return a safe standard envelope."""
        mock_list.side_effect = Exception("Secret internal failure")
        
        # We need an authenticated user to reach the viewset
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(email='test500@test.com', password='pw')
        self.client.force_authenticate(user=user)
        
        response = self.client.get('/api/v1/tenants/')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = response.json()
        self.assertIn("errors", data)
        self.assertEqual(data["errors"]["detail"], "Internal server error.")
        # Ensure secret info is not leaked
        self.assertNotIn("Secret internal failure", str(response.content))


class ThrottlingTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('rest_framework.throttling.SimpleRateThrottle.wait')
    @patch('rest_framework.throttling.ScopedRateThrottle.allow_request')
    def test_login_endpoint_is_throttled(self, mock_allow_request, mock_wait):
        """Login endpoint should return 429 after exceeding the auth scope limit."""
        # Allow first two requests, deny the third
        mock_allow_request.side_effect = [True, True, False]
        mock_wait.return_value = 60
        
        # Request 1
        response1 = self.client.post('/api/v1/auth/login/', {}, REMOTE_ADDR='127.0.0.1')
        self.assertEqual(response1.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Request 2
        response2 = self.client.post('/api/v1/auth/login/', {}, REMOTE_ADDR='127.0.0.1')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Request 3 should be throttled
        response3 = self.client.post('/api/v1/auth/login/', {}, REMOTE_ADDR='127.0.0.1')
        self.assertEqual(response3.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        data = response3.json()
        self.assertIn("errors", data)
        self.assertIn("detail", data["errors"])
        self.assertIn("Request was throttled", data["errors"]["detail"])


class CORSTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @override_settings(CORS_ALLOWED_ORIGINS=['https://allowed.com'])
    def test_cors_allowed_origin(self):
        """Requests from allowed origins should receive CORS headers."""
        response = self.client.options(
            '/api/v1/auth/login/',
            HTTP_ORIGIN='https://allowed.com',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), 'https://allowed.com')
        self.assertEqual(response.headers.get('Access-Control-Allow-Credentials'), 'true')

    @override_settings(CORS_ALLOWED_ORIGINS=['https://allowed.com'])
    def test_cors_disallowed_origin(self):
        """Requests from disallowed origins should NOT receive CORS headers."""
        response = self.client.options(
            '/api/v1/auth/login/',
            HTTP_ORIGIN='https://hacker.com',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.headers.get('Access-Control-Allow-Origin'))
