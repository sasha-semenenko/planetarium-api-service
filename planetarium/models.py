import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class ShowTheme(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self) -> str:
        return self.name


def astronomy_show_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    return os.path.join(
        "uploads/astronomy_show/",
        f"{slugify(instance.title)}-{uuid.uuid4()}{extension}"
    )


class AstronomyShow(models.Model):
    title = models.CharField(max_length=64)
    description = models.TextField()
    show_theme = models.ManyToManyField(ShowTheme, null=True, related_name="astronomy_show")
    image = models.ImageField(null=True, upload_to=astronomy_show_image_file_path)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class PlanetariumDome(models.Model):
    name = models.CharField(max_length=64)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self) -> str:
        return self.name


class ShowSession(models.Model):
    astronomy_show = models.ForeignKey(AstronomyShow, on_delete=models.CASCADE)
    planetarium_dome = models.ForeignKey(PlanetariumDome, on_delete=models.CASCADE)
    show_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-show_time"]

    def __str__(self) -> str:
        return self.astronomy_show.title + " " + str(self.show_time)


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return str(self.created_at)


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    show_session = models.ForeignKey(ShowSession, on_delete=models.CASCADE, related_name="tickets")
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name="tickets")

    @staticmethod
    def validate_ticket(row, seat, planetarium_dome, error_to_raise):
        for ticket_attr_value, ticket_attr_name, planetarium_dome_attr_name in [
            (row, "row", "rows"),
            (seat, "seat", "seats_in_row"),
        ]:
            count_attrs = getattr(planetarium_dome, planetarium_dome_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name} "
                                          f"number must be in available range: "
                                          f"(1, {planetarium_dome_attr_name}): "
                                          f"(1, {count_attrs})"
                    }
                )

    def clean(self):
        Ticket.validate_ticket(
            self.row,
            self.seat,
            self.show_session.planetarium_dome,
            ValidationError,
        )

    def save(
            self,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self) -> str:
        return f"{str(self.show_session)} (row: {self.row}, seat: {self.seat})"

    class Meta:
        unique_together = ["show_session", "row", "seat"]
        ordering = ["row", "seat"]
