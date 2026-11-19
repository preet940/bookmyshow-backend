from datetime import timedelta

import pytest
from django.utils import timezone

from apps.bookings.models import Booking, Payment
from apps.bookings.services import BookingError, confirm_booking
from apps.movies.models import Movie
from apps.shows.models import Show, ShowSeat
from apps.shows.services import hold_seats
from apps.theatres.models import City, Screen, Seat, Theatre
from apps.users.models import User
from apps.bookings.services import BookingError, cancel_booking, confirm_booking


@pytest.fixture
def user(db):
    return User.objects.create_user(email="a@example.com", password="pw-12345-x")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(email="b@example.com", password="pw-12345-x")


@pytest.fixture
def show(db):
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
    return Show.objects.create(
        movie=movie, screen=screen, start_time=start,
        end_time=start + timedelta(hours=2),
        price_regular=100, price_premium=200, price_recliner=300,
    )


def seat_ids(show, n=2):
    return list(show.show_seats.values_list("seat_id", flat=True)[:n])


def test_successful_booking(show, user):
    ids = seat_ids(show)
    hold_seats(show.id, ids, user)
    booking, created = confirm_booking(user, show.id, ids, "key-1")
    assert created is True
    assert booking.total_amount == 200          # 2 regular seats x 100
    assert booking.booking_seats.count() == 2
    assert show.show_seats.filter(status="booked").count() == 2


def test_same_key_returns_same_booking_without_double_charge(show, user):
    ids = seat_ids(show)
    hold_seats(show.id, ids, user)
    first, created1 = confirm_booking(user, show.id, ids, "key-2")
    second, created2 = confirm_booking(user, show.id, ids, "key-2")
    assert first.id == second.id
    assert created1 is True and created2 is False
    assert Payment.objects.filter(idempotency_key="key-2").count() == 1
    assert Booking.objects.count() == 1


def test_cannot_book_seats_held_by_another_user(show, user, other_user):
    ids = seat_ids(show)
    hold_seats(show.id, ids, user)
    with pytest.raises(BookingError):
        confirm_booking(other_user, show.id, ids, "key-3")
    assert Booking.objects.count() == 0


def test_cannot_book_without_holding(show, user):
    with pytest.raises(BookingError):
        confirm_booking(user, show.id, seat_ids(show), "key-4")


def test_expired_hold_is_rejected(show, user):
    ids = seat_ids(show)
    hold_seats(show.id, ids, user)
    ShowSeat.objects.filter(show=show, seat_id__in=ids).update(
        held_until=timezone.now() - timedelta(minutes=1)
    )
    with pytest.raises(BookingError):
        confirm_booking(user, show.id, ids, "key-5")
    assert show.show_seats.filter(status="booked").count() == 0

def test_cancel_frees_seats_and_marks_cancelled(show, user):
    ids = seat_ids(show)
    hold_seats(show.id, ids, user)
    booking, _ = confirm_booking(user, show.id, ids, "key-6")
    cancel_booking(user, booking.id)
    booking.refresh_from_db()
    assert booking.status == "cancelled"
    assert show.show_seats.filter(status="available").count() == 5


def test_cannot_cancel_twice(show, user):
    ids = seat_ids(show)
    hold_seats(show.id, ids, user)
    booking, _ = confirm_booking(user, show.id, ids, "key-7")
    cancel_booking(user, booking.id)
    with pytest.raises(BookingError):
        cancel_booking(user, booking.id)


def test_cannot_cancel_someone_elses_booking(show, user, other_user):
    ids = seat_ids(show)
    hold_seats(show.id, ids, user)
    booking, _ = confirm_booking(user, show.id, ids, "key-8")
    with pytest.raises(BookingError):
        cancel_booking(other_user, booking.id)
    booking.refresh_from_db()
    assert booking.status == "confirmed"    