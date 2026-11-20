from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.shows.models import ShowSeat


class Command(BaseCommand):
    help = "Release seats whose hold has expired."

    def handle(self, *args, **options):
        released = ShowSeat.objects.filter(
            status=ShowSeat.Status.HELD,
            held_until__lte=timezone.now(),
        ).update(
            status=ShowSeat.Status.AVAILABLE,
            held_until=None,
            held_by=None,
        )
        self.stdout.write(f"Released {released} expired holds.")