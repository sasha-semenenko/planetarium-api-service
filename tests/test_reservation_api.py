from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from planetarium.models import (
    AstronomyShow,
    PlanetariumDome,
    ShowSession,
    Reservation,

    Ticket
)
from planetarium.serializers import ReservationListSerializer


def sample_astronomy_show(**params):
    default = {
        "title": "Test title",
        "description": "Test description for astronomy show list"
    }
    default.update(params)
    return AstronomyShow.objects.create(**params)


def sample_show_session(**params):
    planetarium_dome = PlanetariumDome.objects.create(
        name="planetarium dome name", rows=2, seats_in_row=3
    )
    data = {
        "astronomy_show": sample_astronomy_show(),
        "planetarium_dome": planetarium_dome,
        "show_time": "2023-01-01 22:22:22"
    }
    data.update(params)
    return ShowSession.objects.create(**data)


RESERVATION_LIST = reverse("planetarium:reservation-list")


class UnauthenticatedReservationApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(RESERVATION_LIST)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedReservationApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "reservation@reservation.com",
            "reservationpassword"
        )
        self.client.force_authenticate(self.user)


    def test_reservation_list(self):
        reservation = Reservation.objects.create(
            created_at="2023-02-02T15:28:10Z", user=self.user
        )
        ticket = Ticket.objects.create(
            row=1,
            seat=1,
            reservation=reservation,
            show_session=sample_show_session(),
        )
        reservation.tickets.add(ticket)

        res = self.client.get(RESERVATION_LIST)
        serializer = ReservationListSerializer(reservation)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0], serializer.data)

    def test_create_reservation_forbidden(self):
        data = {
            "created_at": "2023-02-02T15:28:10Z",
            "user": self.user
        }

        response = self.client.post(RESERVATION_LIST, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
