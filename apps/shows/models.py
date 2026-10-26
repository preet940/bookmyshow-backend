from django.db import models
from django.db.models import F, Q

from apps.movies.models import Movie
from apps.theatres.models import Screen, Seat


class Show(models.Model):
    movie = models.ForeignKey(
        Movie,
        on_delete=models.PROTECT,
        related_name="shows",
    )
    screen = models.ForeignKey(
        Screen,
        on_delete=models.PROTECT,
        related_name="shows",
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    price_regular = models.DecimalField(max_digits=8, decimal_places=2)
    price_premium = models.DecimalField(max_digits=8, decimal_places=2)
    price_recliner = models.DecimalField(max_digits=8, decimal_places=2)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["start_time"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gt=F("start_time")),
                name="show_end_after_start",
            ),
            models.UniqueConstraint(
                fields=["screen", "start_time"],
                name="unique_show_start_per_screen",
            ),
        ]
        indexes = [
            models.Index(fields=["movie", "start_time"]),
            models.Index(fields=["screen", "start_time"]),
        ]

    def __str__(self):
        return f"{self.movie.title} @ {self.start_time:%Y-%m-%d %H:%M}"



class ShowSeat(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        HELD = "held", "Held"
        BOOKED = "booked", "Booked"

    show = models.ForeignKey(
        Show,
        on_delete=models.CASCADE,
        related_name="show_seats",
    )
    seat = models.ForeignKey(
        Seat,
        on_delete=models.PROTECT,
        related_name="show_seats",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    held_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["show_id", "seat_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["show", "seat"],
                name="unique_seat_per_show",
            )
        ]
        indexes = [
            models.Index(fields=["show", "status"]),
            models.Index(fields=["status", "held_until"]),
        ]

    def __str__(self):
        return f"{self.seat} - {self.status}"    