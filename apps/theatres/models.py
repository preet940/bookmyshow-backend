from django.db import models


class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    state = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "cities"
        ordering = ["name"]

    def __str__(self):
        return self.name

class Theatre(models.Model):
    city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="theatres",
    )
    name = models.CharField(max_length=150)
    address = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["city", "name"],
                name="unique_theatre_name_per_city",
            )
        ]
        indexes = [
            models.Index(fields=["city", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.city.name})"    



class Screen(models.Model):
    theatre = models.ForeignKey(
        Theatre,
        on_delete=models.PROTECT,
        related_name="screens",
    )
    name = models.CharField(max_length=50)   # e.g. "Screen 1", "IMAX"
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["theatre", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["theatre", "name"],
                name="unique_screen_name_per_theatre",
            )
        ]

    def __str__(self):
        return f"{self.theatre.name} - {self.name}"    


class Seat(models.Model):
    class SeatType(models.TextChoices):
        REGULAR = "regular", "Regular"
        PREMIUM = "premium", "Premium"
        RECLINER = "recliner", "Recliner"

    screen = models.ForeignKey(
        Screen,
        on_delete=models.CASCADE,
        related_name="seats",
    )
    row = models.CharField(max_length=2)            # "A", "B", ... "AA"
    number = models.PositiveSmallIntegerField()      # 1, 2, 3 ...
    seat_type = models.CharField(
        max_length=10,
        choices=SeatType.choices,
        default=SeatType.REGULAR,
    )

    class Meta:
        ordering = ["screen_id", "row", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["screen", "row", "number"],
                name="unique_seat_per_screen",
            )
        ]

    def __str__(self):
        return f"{self.row}{self.number}"    