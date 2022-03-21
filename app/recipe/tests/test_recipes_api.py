from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import RecipeSerializer


RECIPES_URL = reverse('recipe:recipe-list')

FAKE_RECIPE = {'title': 'Fake Recipe', 'time_minutes': 30, 'price': 10.00}
FAKE_RECIPE_2 = {'title': 'Fake Recipe 2', 'time_minutes': 15, 'price': 5.00}


class PublicRecipeApiTests(TestCase):
    """Test the publicly available recipes API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving recipes"""
        resp = self.client.get(RECIPES_URL)

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test the authorized user recipes API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@unittes.com',
            'password123'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        Recipe.objects.create(user=self.user, **FAKE_RECIPE)
        Recipe.objects.create(user=self.user, **FAKE_RECIPE_2)

        resp = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)
        self.assertEqual(resp.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test retrieving recipes for user"""
        user2 = get_user_model().objects.create_user(
            'new_user@unittest.com',
            'password123'
        )
        Recipe.objects.create(user=user2, **FAKE_RECIPE)
        recipe = Recipe.objects.create(user=self.user, **FAKE_RECIPE_2)

        resp = self.client.get(RECIPES_URL)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['title'], recipe.title)
        self.assertNotIn(FAKE_RECIPE_2['title'], resp.data)

    def test_create_recipe_successful(self):
        """Test creating a new recipe"""
        resp = self.client.post(RECIPES_URL, FAKE_RECIPE)

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=resp.data['id'])
        for key in FAKE_RECIPE.keys():
            self.assertEqual(FAKE_RECIPE[key], getattr(recipe, key))

    def test_create_recipe_invalid(self):
        """Test creating invalid recipe fails"""
        payload = {'title': ''}
        resp = self.client.post(RECIPES_URL, payload)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
