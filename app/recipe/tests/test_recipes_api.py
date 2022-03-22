from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Main course'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinnamon'):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample Recipe',
        'time_minutes': 10,
        'price': 5.00,
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


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
            'test@unittest.com',
            'password123'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        sample_recipe(self.user)
        sample_recipe(self.user, title='Second Recipe')

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
        sample_recipe(user2)
        sample_recipe(self.user,)

        resp = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(self.user)
        recipe.tags.add(sample_tag(self.user))
        recipe.ingredients.add(sample_ingredient(self.user))

        url = detail_url(recipe.id)
        resp = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(resp.data, serializer.data)
