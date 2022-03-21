from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')

TEST_USER = {
    'email': 'test@unittest.com',
    'password': 'testpass',
    'name': 'Test User'
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
