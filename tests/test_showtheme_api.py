from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from planetarium.models import ShowTheme
from planetarium.serializers import ShowThemeSerializers

SHOW_THEME_URL = reverse("planetarium:showtheme-list")

def sample_show_theme(**params):
    data = {
        "name": "test show theme name"
    }
    data.update(params)
    return ShowTheme.objects.create(**data)


class UnauthenticatedShowThemeApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(SHOW_THEME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedShowThemeApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "theme@theme.com",
            "themepassword"
        )
        self.client.force_authenticate(self.user)

    def test_list_show_theme(self):
        sample_show_theme()
        response = self.client.get(SHOW_THEME_URL)
        show_theme = ShowTheme.objects.all()
        serializer = ShowThemeSerializers(show_theme, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_show_theme_forbidden(self):
        data = {
            "name": "test name"
        }

        response = self.client.post(SHOW_THEME_URL, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminShowThemeAPiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "show_theme@admin.com",
            "showthemepass",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_show_theme(self):
        data = {
            "name": "create name"
        }

        response = self.client.post(SHOW_THEME_URL, data)
        show_theme = ShowTheme.objects.get(id=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for key in data:
            self.assertEqual(data[key], getattr(show_theme, key))
