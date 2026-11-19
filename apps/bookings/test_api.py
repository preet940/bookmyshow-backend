from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.movies.models import Movie
from apps.shows.models import Show
from apps.theatres.models import City, Screen, Seat, Theatre
from apps.users.models import User


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


def make_client(email):
    user = User.objects.create_user(email=email, password="pw-12345-x")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def seat_ids(show, n=2):
    return list(show.show_seats.values_list("seat_id", flat=True)[:n])


def test_hold_requires_login(show):
    resp = APIClient().post(
        f"/api/shows/{show.id}/hold/", {"seat_ids": seat_ids(show)}, format="json"
    )
    assert resp.status_code == 401


def test_booking_requires_login(show):
    resp = APIClient().post("/api/bookings/", {}, format="json")
    assert resp.status_code == 401


def test_booking_requires_idempotency_key(show):
    client = make_client("a@example.com")
    ids = seat_ids(show)
    client.post(f"/api/shows/{show.id}/hold/", {"seat_ids": ids}, format="json")
    resp = client.post(
        "/api/bookings/", {"show_id": show.id, "seat_ids": ids}, format="json"
    )
    assert resp.status_code == 400


def test_full_flow_and_idempotent_replay(show):
    client = make_client("a@example.com")
    ids = seat_ids(show)
    assert client.post(
        f"/api/shows/{show.id}/hold/", {"seat_ids": ids}, format="json"
    ).status_code == 200

    body = {"show_id": show.id, "seat_ids": ids}
    first = client.post("/api/bookings/", body, format="json", HTTP_IDEMPOTENCY_KEY="k1")
    second = client.post("/api/bookings/", body, format="json", HTTP_IDEMPOTENCY_KEY="k1")
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.data["id"] == second.data["id"]


def test_second_user_cannot_hold_taken_seats(show):
    a = make_client("a@example.com")
    b = make_client("b@example.com")
    ids = seat_ids(show)
    assert a.post(f"/api/shows/{show.id}/hold/", {"seat_ids": ids}, format="json").status_code == 200
    resp = b.post(f"/api/shows/{show.id}/hold/", {"seat_ids": ids}, format="json")
    assert resp.status_code == 409


def test_user_sees_only_own_bookings(show):
    a = make_client("a@example.com")
    b = make_client("b@example.com")
    ids = seat_ids(show)
    a.post(f"/api/shows/{show.id}/hold/", {"seat_ids": ids}, format="json")
    a.post("/api/bookings/", {"show_id": show.id, "seat_ids": ids},
           format="json", HTTP_IDEMPOTENCY_KEY="k2")
    assert len(a.get("/api/bookings/").data["results"]) == 1
    assert len(b.get("/api/bookings/").data["results"]) == 0