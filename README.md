# BookMyShow-Style Booking Backend

![CI](https://github.com/preet940/bookmyshow-backend/actions/workflows/ci.yml/badge.svg)

A movie ticket booking REST API built with **Django, DRF and PostgreSQL**. Users browse shows, hold specific seats for 10 minutes, and confirm bookings with an idempotent (mocked) payment. The hard part: two people can never book the same seat.

**API docs (Swagger):** run locally at `/api/docs/`

## Features

- JWT authentication (register, login, refresh)
- Movies and shows with filtering, search and pagination
- Seat map per show with live status (available / held / booked)
- Seat holds with a 10-minute expiry
- Booking confirmation, history and cancellation
- Idempotent payments via the `Idempotency-Key` header
- Swagger/OpenAPI documentation

## Architecture

```
Client -> Caddy (reverse proxy) -> gunicorn / Django -> PostgreSQL
GitHub push -> Actions (pytest on Postgres) -> SSH deploy to AWS EC2
```

Data model: `City -> Theatre -> Screen -> Seat`, `Movie`, `Show`, `ShowSeat` (one row per seat per show), `Booking`, `BookingSeat`, `Payment`.

## Design decisions

- **No double booking:** `select_for_update()` inside `transaction.atomic()` locks the seat rows. Seats are locked in a fixed order (`order_by("seat_id")`) to avoid deadlocks. A unique constraint on `(show, seat)` is the database-level safety net.
- **Proven by a test:** 20 threads, each with its own DB connection, race for the same seat. Exactly one wins.
- **Idempotent payments:** the `Idempotency-Key` is unique in Postgres. A retried request returns the original booking instead of charging twice, even when two retries arrive simultaneously.
- **Hold ownership:** `held_by` is stored, so only the user who holds a seat can confirm it.
- **Constraints in the database, not just Python:** unique and check constraints, `PROTECT` on business data.
- **Money uses `DecimalField`;** booking stores the price paid at the time.
- **Business logic lives in `services.py`,** keeping views thin and logic testable.

## Run locally

```bash
cp .env.example .env
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo
```

Open http://localhost:8000/api/docs/

## Tests

```bash
docker compose run --rm web pytest -v
```

## Main endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/register/`, `/api/auth/login/` | Auth |
| GET | `/api/movies/` | Movies (filter, search) |
| GET | `/api/shows/` | Upcoming shows |
| GET | `/api/shows/<id>/seats/` | Seat map |
| POST | `/api/shows/<id>/hold/` | Hold seats (auth) |
| POST | `/api/bookings/` | Confirm booking (needs `Idempotency-Key`) |
| POST | `/api/bookings/<id>/cancel/` | Cancel |

## Deployment

Production image (`Dockerfile.prod`, gunicorn, non-root user) behind Caddy via `docker-compose.prod.yml`, deployed to AWS EC2. GitHub Actions runs the tests against Postgres and, on success, deploys over SSH.

## Problems I solved

- Containers could not reach Postgres because `localhost` inside a container is the container itself; fixed by using the Compose service name.
- Booking tests failed because `held_by` was set in Python but omitted from `bulk_update`'s field list, so it was never saved.
- Default model ordering caused hidden joins in seat queries; found by reading the generated SQL.
- Postgres ignored a new password because the data volume already existed; reset the volume.

## Possible improvements

Celery for scheduled hold expiry and email (currently a management command), Redis caching, real payment gateway.