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