from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from planetarium.models import (
    AstronomyShow,
    PlanetariumDome,
    ShowSession
)
from planetarium.serializers import (
    ShowSessionSerializer,
    ShowSessionListSerializer,
    ShowSessionDetailSerializer
)

SHOW_SESSION_URL = reverse("planetarium:showsession-list")


def sample_astronomy_show(**params):
    default = {
        "title": "Test session",
        "description": "Test description for astronomy show session list"
    }
    default.update(params)
    return AstronomyShow.objects.create(**params)


def sample_planetarium_dome(**params):
    data = {
        "name": "test show session",
        "rows": 3,
        "seats_in_row": 4
    }
    data.update(params)
    return PlanetariumDome.objects.create(**data)


def sample_show_session(**params):
    data = {
        "astronomy_show": sample_astronomy_show(),
        "planetarium_dome": sample_planetarium_dome(),
        "show_time": "2023-02-02T15:28:10Z"
    }
    data.update(params)
    return ShowSession.objects.create(**data)


def detail_url(show_session_id: int):
    return reverse("planetarium:showsession-detail", args=[show_session_id])


class UnauthenticatedShowSessionApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(SHOW_SESSION_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedShowSessionApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "show_session@session.com",
            "passsession"
        )
        self.client.force_authenticate(self.user)

    def test_list_show_session(self):
        sample_show_session()

        response = self.client.get(SHOW_SESSION_URL)
        show_session = ShowSession.objects.all()
        serializer = ShowSessionListSerializer(show_session, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_show_session_detail(self):
        show_session = sample_show_session()

        url = detail_url(show_session.id)
        response = self.client.get(url)

        serializer = ShowSessionDetailSerializer(show_session)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_filter_show_session_by_date(self):
        sample_show_session(show_time="2022-06-02T14:00:00")

        sample_show_session(show_time="2022-01-01T14:00:00Z")

        res = self.client.get(SHOW_SESSION_URL, {"show_time": "2022-06-02T14:00:00Z"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data[0]["show_time"], "2022-06-02T14:00:00Z"
        )
        self.assertNotEquals(
            res.data[0]["show_time"], "2022-01-01T14:00:00Z"
        )


    def test_filter_show_session_by_astronomy_ids(self):
        planetarium = PlanetariumDome.objects.create(
            name="new", rows=1, seats_in_row=2
        )

        astronomy = AstronomyShow.objects.create(
            title="test",
            description="new"
        )

        session = ShowSession.objects.create(
            astronomy_show=astronomy,
            planetarium_dome=planetarium,
            show_time="2023-02-02T15:28:10Z"

        )

        res = self.client.get(SHOW_SESSION_URL, {"astronomy_show": astronomy.id})

        serializer = ShowSessionListSerializer(session)

        self.assertIn(serializer.data, res.data)

    def test_create_show_session_forbidden(self):
        data = {
            "astronomy_show": sample_astronomy_show(),
            "planetarium_dome": sample_planetarium_dome(),
            "show_time": "2023-04-04 10:48:59"
        }

        response = self.client.post(SHOW_SESSION_URL, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminShowSessionAPiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admintest@admin.com",
            "adminnewpassword",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_show_session(self):
        astronomy = sample_astronomy_show()
        planetarium_dome = sample_planetarium_dome()
        payload = {
            "astronomy_show": astronomy.id,
            "planetarium_dome": planetarium_dome.id,
            "show_time": "2023-02-02T15:28:10Z"
        }
        res = self.client.post(SHOW_SESSION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        show_session = ShowSession.objects.get(id=res.data["id"])
        serializer = ShowSessionSerializer(show_session)
        for key in payload.keys():
            self.assertEqual(payload[key], serializer.data[key])
