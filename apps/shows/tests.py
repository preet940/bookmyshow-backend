from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from django.db import connection
from django.utils import timezone

from apps.movies.models import Movie
from apps.shows.models import Show, ShowSeat
from apps.shows.services import SeatUnavailable, hold_seats
from apps.theatres.models import City, Screen, Seat, Theatre


@pytest.fixture
def show_with_seats(db):
    city = City.objects.create(name="Testville")
    theatre = Theatre.objects.create(city=city, name="Test Theatre", address="x")
    screen = Screen.objects.create(theatre=theatre, name="S1")
    Seat.objects.bulk_create(
        [Seat(screen=screen, row="A", number=n) for n in range(1, 6)]
    )
    movie = Movie.objects.create(
        title="Test Movie", language="en", genre="Drama",
        duration_minutes=120, release_date=timezone.now().date(),
    )
    start = timezone.now() + timedelta(days=1)
    show = Show.objects.create(
        movie=movie, screen=screen, start_time=start,
        end_time=start + timedelta(hours=2),
        price_regular=100, price_premium=200, price_recliner=300,
    )
    ShowSeat.objects.bulk_create(
        [ShowSeat(show=show, seat=s) for s in screen.seats.all()]
    )
    return show


def test_second_hold_on_same_seat_fails(show_with_seats):
    seat_id = show_with_seats.show_seats.first().seat_id
    hold_seats(show_with_seats.id, [seat_id])
    with pytest.raises(SeatUnavailable):
        hold_seats(show_with_seats.id, [seat_id])


@pytest.mark.django_db(transaction=True)
def test_no_double_booking_under_concurrency(show_with_seats):
    seat_id = show_with_seats.show_seats.first().seat_id

    def attempt(_):
        try:
            hold_seats(show_with_seats.id, [seat_id])
            return "won"
        except SeatUnavailable:
            return "lost"
        finally:
            connection.close()   # each thread has its own DB connection

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(attempt, range(20)))

    assert results.count("won") == 1
    assert results.count("lost") == 19