from django.conf import settings
from django.db import models

from apps.shows.models import Show, ShowSeat


class Booking(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    show = models.ForeignKey(
        Show, on_delete=models.PROTECT, related_name="bookings"
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.CONFIRMED
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"Booking {self.id} ({self.status})"


class BookingSeat(models.Model):
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="booking_seats"
    )
    show_seat = models.ForeignKey(
        ShowSeat, on_delete=models.PROTECT, related_name="booking_seats"
    )
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.show_seat.seat} in booking {self.booking_id}"


class Payment(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    booking = models.ForeignKey(
        Booking, on_delete=models.PROTECT, related_name="payments"
    )
    idempotency_key = models.CharField(max_length=64, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.idempotency_key} ({self.status})"