from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from planetarium.models import PlanetariumDome
from planetarium.serializers import PlanetariumDomeSerializer

PLANETARIUM_DOME_URL = reverse("planetarium:planetariumdome-list")


def sample_planetarium_dome(**params):
    default = {
        "name": "Your name",
        "rows": 1,
        "seats_in_row": 2
    }
    default.update(params)
    return PlanetariumDome.objects.create(**params)


class UnauthenticatedPlanetariumDomeApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(PLANETARIUM_DOME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPlanetariumDomeApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpassword"
        )
        self.client.force_authenticate(self.user)

    def test_list_planetarium_dome(self):
        sample_planetarium_dome()

        response = self.client.get(PLANETARIUM_DOME_URL)
        planetarium_dome = PlanetariumDome.objects.all()
        serializer = PlanetariumDomeSerializer(planetarium_dome, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_planetarium_dome_forbidden(self):
        data = {
            "name": "test name",
            "rows": 2,
            "seats_in_row": 2
        }

        response = self.client.post(PLANETARIUM_DOME_URL, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class AdminPlanetariumDomeAPiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "planetarium_dome@admin.com",
            "planetariumpassdome",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_planetarium_dome(self):
        data = {
            "name": "planetarium_dome",
            "rows": 4,
            "seats_in_row": 5
        }

        response = self.client.post(PLANETARIUM_DOME_URL, data)
        planetarium_dome = PlanetariumDome.objects.get(id=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for key in data:
            self.assertEqual(data[key], getattr(planetarium_dome, key))
