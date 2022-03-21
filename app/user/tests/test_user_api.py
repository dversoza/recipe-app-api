from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')

TEST_USER = {
    'email': 'test@unittest.com',
    'password': 'password',
    'name': 'Test User'
}

NEW_USER = {
    'name': 'New User',
    'password': 'new_password',
}


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Creating user with valid payload succeeds"""
        resp = self.client.post(CREATE_USER_URL, TEST_USER)

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(**resp.data)

        self.assertTrue(user.check_password(TEST_USER['password']))
        self.assertNotIn('password', resp.data)

    def test_user_exists_400(self):
        """Creating user that already exists fails"""
        create_user(**TEST_USER)

        resp = self.client.post(CREATE_USER_URL, TEST_USER)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_400(self):
        """Password must be over 8 characters"""
        payload = {
            'email': TEST_USER['email'],
            'password': 'pw',
            'name': TEST_USER['name']
        }
        resp = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(
            email=TEST_USER['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user_success(self):
        """Test that a token is created for the user"""
        create_user(**TEST_USER)
        payload = {
            'email': TEST_USER['email'],
            'password': TEST_USER['password']
        }
        resp = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', resp.data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials_400(self):
        """Test that token is not created if invalid credentials are given"""
        create_user(**TEST_USER)
        payload = {
            'email': TEST_USER['email'],
            'password': 'wrong'
        }
        resp = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', resp.data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user_400(self):
        """Test that token is not created if user doesn't exist"""
        payload = {
            'email': TEST_USER['email'],
            'password': TEST_USER['password']
        }
        resp = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', resp.data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field_400(self):
        """Test that email and password are required"""
        resp = self.client.post(TOKEN_URL, {'email': 'one', 'password': ''})

        self.assertNotIn('token', resp.data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test that authentication is required for users"""
        resp = self.client.get(ME_URL)

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication"""

    def setUp(self):
        self.user = create_user(**TEST_USER)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""
        resp = self.client.get(ME_URL)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_update_user_profile(self):
        """Test updating the user profile for authenticated user"""
        payload = {
            'name': NEW_USER['name'],
            'password': NEW_USER['password']
        }
        resp = self.client.patch(ME_URL, payload)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {
            'email': TEST_USER['email'],
            'name': NEW_USER['name']}
        )

    def test_update_user_profile_with_no_password(self):
        """Test updating the user profile for authenticated user"""
        payload = {
            'name': NEW_USER['name'],
        }
        resp = self.client.patch(ME_URL, payload)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {
            'email': TEST_USER['email'],
            'name': NEW_USER['name']
        })

    def test_update_user_profile_with_invalid_password(self):
        """Test updating the user profile for authenticated user"""
        new_user = {
            'name': NEW_USER['name'],
            'password': 'pw'
        }
        resp = self.client.patch(ME_URL, new_user)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_user_profile_with_invalid_email(self):
        """Test updating the user profile for authenticated user"""
        new_user = {
            'name': NEW_USER['name'],
            'email': 'invalid'
        }
        resp = self.client.patch(ME_URL, new_user)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_user_profile_with_invalid_email_and_password(self):
        """Test updating the user profile for authenticated user"""
        new_user = {
            'name': 'new name',
            'email': 'invalid',
            'password': 'pw'
        }
        resp = self.client.patch(ME_URL, new_user)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
