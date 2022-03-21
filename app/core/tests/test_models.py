from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def sample_user(email='test@unittest.com', password='password'):
    """Create a sample user"""
    return get_user_model().objects.create_user(
        email=email,
        password=password
    )


class ModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email"""
        email = 'test@test.com'
        password = 'password'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized"""
        email = 'test@ERROR.com'
        password = 'password'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test creating user with no email raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email=None,
                password='password'
            )

    def test_create_new_superuser(self):
        """Test creating a new superuser"""
        email = 'test@test.com'
        password = 'password'
        user = get_user_model().objects.create_superuser(
            email=email,
            password=password
        )

        self.assertEqual(user.is_superuser, True)
        self.assertEqual(user.is_staff, True)

    def test_tag_str(self):
        """Test the tag string representation"""
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Healthy'
        )

        self.assertEqual(str(tag), tag.name)
