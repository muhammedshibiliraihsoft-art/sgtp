"""
Tests for B2-01 DRF API Baseline.
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

class APIBaselineTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_unauthenticated_requests_return_401(self):
        """Deny-by-default auth should return 401 for unauthenticated requests."""
        response = self.client.get('/api/v1/tenants/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_versioned_routing_resolves(self):
        """The /api/v1/ namespace should properly route requests."""
        response = self.client.post('/api/v1/auth/login/', {'email': 'x', 'password': 'x'})
        # Returns 401 which implies routing succeeded and auth failed
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_json_response_contract(self):
        """API should return application/json content type."""
        response = self.client.get('/api/v1/tenants/')
        self.assertIn('application/json', response['Content-Type'])
        
    def test_pagination_default(self):
        """List responses should include pagination structure."""
        user = User.objects.create_user(email='test@test.com', password='pw')
        self.client.force_authenticate(user=user)
        response = self.client.get('/api/v1/tenants/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
