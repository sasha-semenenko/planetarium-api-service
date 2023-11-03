from datetime import datetime

from django.db.models import F, Count
from rest_framework import mixins, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import GenericViewSet

from planetarium.models import AstronomyShow, ShowTheme, PlanetariumDome, ShowSession, Reservation
from planetarium.serializers import AstronomyShowSerializer, ShowThemeSerializers, PlanetariumDomeSerializer, \
    ShowSessionSerializer, ShowSessionListSerializer, ShowSessionDetailSerializer, ReservationSerializer, \
    ReservationListSerializer


class AstronomyShowViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = AstronomyShow.objects.all()
    serializer_class = AstronomyShowSerializer


class ShowThemeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = ShowTheme.objects.all()
    serializer_class = ShowThemeSerializers


class PlanetariumDomeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = PlanetariumDome.objects.all()
    serializer_class = PlanetariumDomeSerializer


class ShowSessionViewSet(viewsets.ModelViewSet):
    queryset = ShowSession.objects.all()\
        .select_related("astronomy_show", "planetarium_dome")\
        .annotate(tickets_available=(
            F("planetarium_dome__rows") * F("planetarium_dome__seats_in_row")
            - Count("tickets"))
    )
    serializer_class = ShowSessionSerializer

    def get_queryset(self):
        date = self.request.query_params.get("date")
        astronomy_show_id_str = self.request.query_params.get("astronomy_show")

        queryset = self.queryset

        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(show_time__date=date)

        if astronomy_show_id_str:
            queryset = queryset.filter(astronomy_show_id=int(astronomy_show_id_str))

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return ShowSessionListSerializer

        if self.action == "retrieve":
            return ShowSessionDetailSerializer

        return ShowSessionSerializer


class ReservationPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class ReservationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Reservation.objects.prefetch_related(
        "tickets__show_session__astronomy_show", "tickets__show_session__planetarium_dome"
    )
    serializer_class = ReservationSerializer
    pagination_class = ReservationPagination

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer

        return ReservationSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
