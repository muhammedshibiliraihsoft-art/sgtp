import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class UserModelTest(TestCase):
    def test_create_user(self):
        """Test creating a user with email"""
        email = "test@example.com"
        password = "testpass123"
        user = User.objects.create_user(email=email, password=password, first_name='Test')
        
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        """Test creating a superuser"""
        email = "admin@example.com"
        password = "adminpass123"
        user = User.objects.create_superuser(email=email, password=password, first_name='Main', phone='+96550000000')
        
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_user_string_representation(self):
        """Test user string representation"""
        email = "test@example.com"
        user = User.objects.create_user(email=email, first_name='Test')
        self.assertEqual(str(user), "Test")


class UserAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }

    def test_create_user_success(self):
        """Only the Main Supplier Admin may create accounts; credentials are one-time."""
        admin = User.objects.create_superuser(email='main@example.com', password='AdminPass-934!', first_name='Main', phone='+96550000001')
        self.client.force_authenticate(user=admin)
        response = self.client.post('/api/v1/auth/users/', {
            'email': self.user_data['email'],
            'first_name': self.user_data['first_name'],
            'last_name': self.user_data['last_name'],
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response['Cache-Control'], 'no-store')
        self.assertEqual(response['Pragma'], 'no-cache')
        self.assertIn('initial_password', response.data)
        created = User.objects.get(email=self.user_data['email'])
        self.assertTrue(created.must_change_password)
        self.assertTrue(created.check_password(response.data['initial_password']))
        self.assertNotEqual(created.password, response.data['initial_password'])

    def test_create_user_password_mismatch(self):
        """Anonymous public registration is prohibited."""
        response = self.client.post('/api/v1/auth/users/', self.user_data)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_login_success(self):
        """Test user login returns access token and sets refresh cookie"""
        # Create user first
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
        )
        
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post('/api/v1/auth/login/', login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertNotIn('refresh', response.data)  # Refresh is moved to cookie
        self.assertIn('refresh', response.cookies)  # It should be in cookies

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_data = {
            'email': 'wrong@example.com',
            'password': 'wrongpass'
        }
        response = self.client.post('/api/v1/auth/login/', login_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_cannot_target_another_user(self):
        """A normal user cannot list, modify, or delete another user."""
        user = User.objects.create_user(email='owner@example.com', password='testpass123', first_name='Test')
        other = User.objects.create_user(email='other@example.com', password='testpass123', first_name='Test')
        self.client.force_authenticate(user=user)

        list_response = self.client.get('/api/v1/auth/users/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data['count'], 1)
        self.assertEqual(list_response.data['results'][0]['id'], str(user.id))

        patch_response = self.client.patch(
            f'/api/v1/auth/users/{other.id}/',
            {'is_active': False, 'email': 'changed@example.com'},
        )
        self.assertEqual(patch_response.status_code, status.HTTP_404_NOT_FOUND)

        delete_response = self.client.delete(f'/api/v1/auth/users/{other.id}/')
        self.assertEqual(delete_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        other.refresh_from_db()
        self.assertTrue(other.is_active)
        self.assertEqual(other.email, 'other@example.com')

    def test_self_profile_update_cannot_change_activation_state(self):
        """Self-service profile updates cannot deactivate the account."""
        user = User.objects.create_user(email='profile@example.com', password='testpass123', first_name='Test')
        self.client.force_authenticate(user=user)

        response = self.client.patch(
            f'/api/v1/auth/users/{user.id}/',
            {'first_name': 'Updated', 'is_active': False},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Updated')
        self.assertTrue(user.is_active)
