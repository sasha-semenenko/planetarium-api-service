import os
import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from planetarium.models import (
    AstronomyShow,
    ShowTheme,
    PlanetariumDome,
    ShowSession
)
from planetarium.serializers import (
    AstronomyShowListSerializer,
    AstronomyShowDetailSerializer
)

ASTRONOMY_SHOW_URL = reverse("planetarium:astronomyshow-list")
SHOW_SESSION_URL = reverse("planetarium:showsession-list")


def sample_astronomy_show(**params):
    default = {
        "title": "Test title",
        "description": "Test description for astronomy show list"
    }
    default.update(params)
    return AstronomyShow.objects.create(**params)


def sample_show_theme(**params):
    data = {
        "name": "test name"
    }
    data.update(params)
    return ShowTheme.objects.create(**data)


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


def astronomy_detail_url(astronomy_id):
    return reverse("planetarium:astronomyshow-detail", args=[astronomy_id])


def image_upload_url(astronomy_id):
    """Return URL for recipe image upload"""
    return reverse("planetarium:astronomyshow-upload-image", args=[astronomy_id])


class UnauthenticatedAstronomyShowApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(ASTRONOMY_SHOW_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAstronomyShowApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpassword"
        )
        self.client.force_authenticate(self.user)

    def test_list_astronomy_show(self):
        sample_astronomy_show()
        astronomy_show_with_show_theme = sample_astronomy_show()

        show_theme1 = ShowTheme.objects.create(name="theme 1")
        show_theme2 = ShowTheme.objects.create(name="theme 2")
        astronomy_show_with_show_theme.show_theme.add(show_theme1, show_theme2)

        response = self.client.get(ASTRONOMY_SHOW_URL)
        astronomy_show = AstronomyShow.objects.all()
        serializer = AstronomyShowListSerializer(astronomy_show, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_astronomy_show_by_show_theme(self):
        astronomy_show1 = sample_astronomy_show(description="Astronomy show 1")
        astronomy_show2 = sample_astronomy_show(description="Astronomy show 2")

        show_theme1 = ShowTheme.objects.create(name="theme 1")
        show_theme2 = ShowTheme.objects.create(name="theme 2")

        astronomy_show1.show_theme.add(show_theme1)
        astronomy_show2.show_theme.add(show_theme2)

        astronomy_show3 = sample_astronomy_show(description="without show theme")

        response = self.client.get(ASTRONOMY_SHOW_URL, {"show_theme": f"{astronomy_show1.id},{astronomy_show2.id}"})

        serializer1 = AstronomyShowListSerializer(astronomy_show1)
        serializer2 = AstronomyShowListSerializer(astronomy_show2)
        serializer3 = AstronomyShowListSerializer(astronomy_show3)

        self.assertIn(serializer1.data, response.data)
        self.assertIn(serializer2.data, response.data)
        self.assertNotIn(serializer3.data, response.data)

    def test_retrieve_astronomy_show_detail(self):
        astronomy_show = sample_astronomy_show()
        astronomy_show.show_theme.add(ShowTheme.objects.create(name="test theme"))

        url = astronomy_detail_url(astronomy_show.id)
        response = self.client.get(url)

        serializer = AstronomyShowDetailSerializer(astronomy_show)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_astronomy_show_forbidden(self):
        data = {
            "title": "new title",
            "description": "new description"
        }

        response = self.client.post(ASTRONOMY_SHOW_URL, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminAstronomyShowAPiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com",
            "adminpassword",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_astronomy_show(self):
        data = {
            "title": "admin title",
            "description": "admin description"
        }

        response = self.client.post(ASTRONOMY_SHOW_URL, data)
        astronomy_show = AstronomyShow.objects.get(id=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for key in data:
            self.assertEqual(data[key], getattr(astronomy_show, key))

    def test_create_astronomy_show_with_show_theme(self):
        show_theme1 = ShowTheme.objects.create(name="theme 1")
        show_theme2 = ShowTheme.objects.create(name="theme 2")

        data = {
            "title": "title",
            "description": "description",
            "show_theme": [show_theme1.id, show_theme2.id]
        }

        response = self.client.post(ASTRONOMY_SHOW_URL, data)
        astronomy_show = AstronomyShow.objects.get(id=response.data["id"])
        show_theme = astronomy_show.show_theme.all()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(show_theme.count(), 2)
        self.assertIn(show_theme1, show_theme)
        self.assertIn(show_theme2, show_theme)

    def test_delete_astronomy_show_not_allowed(self):
        astronomy_show = sample_astronomy_show()

        url = astronomy_detail_url(astronomy_show.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class AstronomyShowImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@myproject.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.astronomy_show = sample_astronomy_show()
        self.show_theme = sample_show_theme()
        self.show_session = sample_show_session(astronomy_show=self.astronomy_show)

    def tearDown(self):
        self.astronomy_show.image.delete()

    def test_upload_image_to_astronomy_show(self):
        """Test uploading an image to movie"""
        url = image_upload_url(self.astronomy_show.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.astronomy_show.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.astronomy_show.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.astronomy_show.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_astronomy_show_list_should_not_work(self):
        url = ASTRONOMY_SHOW_URL
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                url,
                {
                    "title": "Title",
                    "description": "Description",
                    "image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        astronomy_show = AstronomyShow.objects.get(title="Title")
        self.assertFalse(astronomy_show.image)

    def test_image_url_is_shown_on_astronomy_show_detail(self):
        url = image_upload_url(self.astronomy_show.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(astronomy_detail_url(self.astronomy_show.id))

        self.assertIn("image", res.data)

    def test_image_url_is_shown_on_astronomy_show_list(self):
        url = image_upload_url(self.astronomy_show.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(ASTRONOMY_SHOW_URL)

        self.assertIn("image", res.data[0].keys())

    def test_image_url_is_shown_on_show_session_detail(self):
        url = image_upload_url(self.astronomy_show.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(SHOW_SESSION_URL)

        self.assertIn("astronomy_show_title", res.data[0].keys())

    def test_put_astronomy_show_not_allowed(self):
        payload = {
            "title": "New movie",
            "description": "New description",
        }

        astronomy_show = sample_astronomy_show()
        url = astronomy_detail_url(astronomy_show.id)

        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_astronomy_show_not_allowed(self):
        astronomy_show = sample_astronomy_show()
        url = astronomy_detail_url(astronomy_show.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
