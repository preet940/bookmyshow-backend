from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from django.db import connection
from django.utils import timezone

from apps.movies.models import Movie
from apps.shows.models import Show, ShowSeat
from apps.shows.services import SeatUnavailable, hold_seats
from apps.theatres.models import City, Screen, Seat, Theatre
from apps.users.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(email="u@example.com", password="pw-12345-x")


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
    # ShowSeat rows are created automatically by the post_save signal
    return Show.objects.create(
        movie=movie, screen=screen, start_time=start,
        end_time=start + timedelta(hours=2),
        price_regular=100, price_premium=200, price_recliner=300,
    )


def test_second_hold_on_same_seat_fails(show_with_seats, user):
    seat_id = show_with_seats.show_seats.first().seat_id
    hold_seats(show_with_seats.id, [seat_id], user)
    with pytest.raises(SeatUnavailable):
        hold_seats(show_with_seats.id, [seat_id], user)


@pytest.mark.django_db(transaction=True)
def test_no_double_booking_under_concurrency(show_with_seats, user):
    seat_id = show_with_seats.show_seats.first().seat_id

    def attempt(_):
        try:
            hold_seats(show_with_seats.id, [seat_id], user)
            return "won"
        except SeatUnavailable:
            return "lost"
        finally:
            connection.close()   # each thread has its own DB connection

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(attempt, range(20)))

    assert results.count("won") == 1
    assert results.count("lost") == 19

def test_hold_records_who_holds_it(show_with_seats, user):
    seat_id = show_with_seats.show_seats.first().seat_id
    hold_seats(show_with_seats.id, [seat_id], user)
    ss = show_with_seats.show_seats.get(seat_id=seat_id)
    assert ss.held_by_id == user.id
    assert ss.status == "held"

def test_release_expired_holds_command(show_with_seats, user):
    from django.core.management import call_command

    seat_id = show_with_seats.show_seats.first().seat_id
    hold_seats(show_with_seats.id, [seat_id], user)
    show_with_seats.show_seats.filter(seat_id=seat_id).update(
        held_until=timezone.now() - timedelta(minutes=1)
    )
    call_command("release_expired_holds")
    ss = show_with_seats.show_seats.get(seat_id=seat_id)
    assert ss.status == "available"
    assert ss.held_by_id is None    