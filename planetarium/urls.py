from django.urls import path
from rest_framework import routers

from planetarium.views import AstronomyShowViewSet, ShowThemeViewSet, PlanetariumDomeViewSet, ShowSessionViewSet, \
    ReservationViewSet

router = routers.DefaultRouter()
router.register("astronomy-show", AstronomyShowViewSet)
router.register("show-theme", ShowThemeViewSet)
router.register("planetarium-dome", PlanetariumDomeViewSet)
router.register("show-session", ShowSessionViewSet)
router.register("reservation", ReservationViewSet)

urlpatterns = router.urls

app_name = "planetarium"
