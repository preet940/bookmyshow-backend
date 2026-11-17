from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Show, ShowSeat


@receiver(post_save, sender=Show)
def create_show_seats(sender, instance, created, **kwargs):
    if not created:
        return
    ShowSeat.objects.bulk_create(
        [ShowSeat(show=instance, seat=seat) for seat in instance.screen.seats.all()]
    )