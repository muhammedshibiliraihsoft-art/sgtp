"""
Tests for B2-02 JWT Lifecycle: CSRF, HttpOnly Cookies, Rotation, and Revocation.
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

User = get_user_model()

class AuthLifecycleTest(TestCase):
    def setUp(self):
        # APIClient explicitly sets enforce_csrf_checks=True for these tests
        # We want to test that Django CsrfViewMiddleware correctly rejects/allows our requests.
        self.client = APIClient(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            email='lifecycle@example.com',
            password='testpass123'
        )

    def get_valid_login_cookies(self):
        """Helper to get a valid login state with cookies and CSRF."""
        response = self.client.post('/api/v1/auth/login/', {
            'email': 'lifecycle@example.com',
            'password': 'testpass123'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refresh_cookie = response.cookies.get('refresh')
        csrf_cookie = response.cookies.get('csrftoken')
        
        return refresh_cookie, csrf_cookie, response.data.get('access')

    def test_login_sets_httponly_cookie_and_csrf_cookie(self):
        """Verify /login/ returns access in JSON, sets refresh HttpOnly cookie, and issues csrftoken."""
        refresh_cookie, csrf_cookie, access_token = self.get_valid_login_cookies()
        
        # Verify access token is in JSON
        self.assertIsNotNone(access_token)
        
        # Verify refresh cookie
        self.assertIsNotNone(refresh_cookie)
        self.assertTrue(refresh_cookie['httponly'])
        self.assertEqual(refresh_cookie['samesite'], 'Lax')
        
        # Verify CSRF cookie
        self.assertIsNotNone(csrf_cookie)

    def test_refresh_requires_csrf(self):
        """Verify /refresh/ rejects requests without the X-CSRFToken header."""
        refresh_cookie, _, _ = self.get_valid_login_cookies()
        
        # Send refresh request *without* CSRF header, but *with* the refresh cookie
        self.client.cookies['refresh'] = refresh_cookie.value
        response = self.client.post('/api/v1/auth/token/refresh/', format='json')
        
        # Should be forbidden due to CSRF failure
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_refresh_rotates_cookie(self):
        """Verify valid cookie + CSRF header yields a new access token and rotated refresh cookie."""
        refresh_cookie, csrf_cookie, old_access = self.get_valid_login_cookies()
        
        # Apply cookies
        self.client.cookies['refresh'] = refresh_cookie.value
        self.client.cookies['csrftoken'] = csrf_cookie.value
        
        # Send refresh request WITH CSRF header
        response = self.client.post(
            '/api/v1/auth/token/refresh/',
            HTTP_X_CSRFTOKEN=csrf_cookie.value,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_access = response.data.get('access')
        self.assertIsNotNone(new_access)
        self.assertNotEqual(old_access, new_access)
        
        # Verify new refresh cookie is issued
        new_refresh_cookie = response.cookies.get('refresh')
        self.assertIsNotNone(new_refresh_cookie)
        self.assertNotEqual(refresh_cookie.value, new_refresh_cookie.value)

    def test_token_reuse_rejected(self):
        """Verify attempting to refresh with an old/rotated refresh cookie is rejected."""
        refresh_cookie, csrf_cookie, _ = self.get_valid_login_cookies()
        old_refresh_value = refresh_cookie.value
        
        # 1. First refresh (Rotation)
        self.client.cookies['refresh'] = old_refresh_value
        self.client.cookies['csrftoken'] = csrf_cookie.value
        
        res1 = self.client.post(
            '/api/v1/auth/token/refresh/',
            HTTP_X_CSRFTOKEN=csrf_cookie.value,
            format='json'
        )
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        
        # Verify the old token is now blacklisted in DB
        self.assertTrue(BlacklistedToken.objects.exists())
        
        # 2. Second refresh (Reuse of the old token)
        self.client.cookies['refresh'] = old_refresh_value
        res2 = self.client.post(
            '/api/v1/auth/token/refresh/',
            HTTP_X_CSRFTOKEN=csrf_cookie.value,
            format='json'
        )
        
        # SimpleJWT rejects blacklisted tokens with 401
        self.assertEqual(res2.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("Token is blacklisted", str(res2.data))

    def test_logout_clears_cookie_and_blacklists(self):
        """Verify /logout/ with valid CSRF header clears both cookies and blacklists the refresh token."""
        refresh_cookie, csrf_cookie, access_token = self.get_valid_login_cookies()
        
        self.client.cookies['refresh'] = refresh_cookie.value
        self.client.cookies['csrftoken'] = csrf_cookie.value
        
        response = self.client.post(
            '/api/v1/auth/logout/',
            HTTP_X_CSRFTOKEN=csrf_cookie.value,
            HTTP_AUTHORIZATION=f'Bearer {access_token}',
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify cookies are cleared (value empty and expires in past)
        cleared_refresh = response.cookies.get('refresh')
        cleared_csrf = response.cookies.get('csrftoken')
        
        self.assertEqual(cleared_refresh.value, '')
        self.assertEqual(cleared_csrf.value, '')
        
        # Verify token was blacklisted
        self.assertTrue(BlacklistedToken.objects.exists())
