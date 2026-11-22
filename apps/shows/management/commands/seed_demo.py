from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.movies.models import Movie
from apps.shows.models import Show
from apps.theatres.models import City, Screen, Seat, Theatre


class Command(BaseCommand):
    help = "Create demo data: city, theatre, screen with seats, movies and shows."

    @transaction.atomic
    def handle(self, *args, **options):
        city, _ = City.objects.get_or_create(name="Bengaluru", defaults={"state": "Karnataka"})
        theatre, _ = Theatre.objects.get_or_create(
            city=city, name="PVR Orion", defaults={"address": "Rajajinagar, Bengaluru"}
        )
        screen, _ = Screen.objects.get_or_create(theatre=theatre, name="Screen 1")

        if not screen.seats.exists():
            seats = []
            for row in "ABCDEFGH":
                seat_type = (
                    Seat.SeatType.REGULAR if row in "AB"
                    else Seat.SeatType.PREMIUM if row in "CDEF"
                    else Seat.SeatType.RECLINER
                )
                for number in range(1, 11):
                    seats.append(Seat(screen=screen, row=row, number=number, seat_type=seat_type))
            Seat.objects.bulk_create(seats)

        today = timezone.now().date()
        movies = [
            ("Demo Thriller", "en", "Thriller", 128),
            ("Demo Action", "hi", "Action", 150),
        ]
        created_shows = 0
        for i, (title, lang, genre, minutes) in enumerate(movies):
            movie, _ = Movie.objects.get_or_create(
                title=title, language=lang,
                defaults={"genre": genre, "duration_minutes": minutes, "release_date": today},
            )
            for day in range(1, 4):
                start = timezone.now().replace(hour=12 + i * 4, minute=0, second=0, microsecond=0) + timedelta(days=day)
                _, made = Show.objects.get_or_create(
                    screen=screen, start_time=start,
                    defaults={
                        "movie": movie,
                        "end_time": start + timedelta(minutes=minutes),
                        "price_regular": 150, "price_premium": 250, "price_recliner": 400,
                    },
                )
                created_shows += made

        self.stdout.write(self.style.SUCCESS(f"Seed done. New shows: {created_shows}"))