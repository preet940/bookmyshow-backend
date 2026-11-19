from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.shows.models import Show, ShowSeat

from .models import Booking, BookingSeat, Payment


class BookingError(Exception):
    pass


def _price_for(show, seat_type):
    return {
        "regular": show.price_regular,
        "premium": show.price_premium,
        "recliner": show.price_recliner,
    }[seat_type]


def confirm_booking(user, show_id, seat_ids, idempotency_key):
    # 1. Idempotency: a repeated key returns the original booking.
    existing = Payment.objects.filter(idempotency_key=idempotency_key).select_related("booking").first()
    if existing:
        return existing.booking, False

    now = timezone.now()
    try:
        with transaction.atomic():
            show = Show.objects.get(id=show_id)
            show_seats = list(
                ShowSeat.objects.select_for_update()
                .select_related("seat")
                .filter(show_id=show_id, seat_id__in=seat_ids)
                .order_by("seat_id")
            )
            if len(show_seats) != len(set(seat_ids)):
                raise BookingError("Some seats do not exist for this show.")

            for ss in show_seats:
                valid_hold = (
                    ss.status == ShowSeat.Status.HELD
                    and ss.held_by_id == user.id
                    and ss.held_until is not None
                    and ss.held_until > now
                )
                if not valid_hold:
                    raise BookingError(f"Seat {ss.seat} is not held by you (or the hold expired).")

            prices = {ss.id: _price_for(show, ss.seat.seat_type) for ss in show_seats}
            total = sum(prices.values(), Decimal("0"))

            booking = Booking.objects.create(user=user, show=show, total_amount=total)
            BookingSeat.objects.bulk_create(
                [BookingSeat(booking=booking, show_seat=ss, price=prices[ss.id]) for ss in show_seats]
            )
            # Mocked payment: always succeeds. The unique key is the safety net.
            Payment.objects.create(
                booking=booking, idempotency_key=idempotency_key,
                amount=total, status=Payment.Status.SUCCESS,
            )

            for ss in show_seats:
                ss.status = ShowSeat.Status.BOOKED
                ss.held_until = None
            ShowSeat.objects.bulk_update(show_seats, ["status", "held_until"])
    except IntegrityError:
        # Two identical requests raced: the other one won. Return its booking.
        payment = Payment.objects.select_related("booking").get(idempotency_key=idempotency_key)
        return payment.booking, False

    return booking, True
def cancel_booking(user, booking_id):
    with transaction.atomic():
        booking = (
            Booking.objects.select_for_update()
            .filter(id=booking_id, user=user)
            .first()
        )
        if booking is None:
            raise BookingError("Booking not found.")
        if booking.status == Booking.Status.CANCELLED:
            raise BookingError("Booking is already cancelled.")

        show_seat_ids = list(
            booking.booking_seats.values_list("show_seat_id", flat=True)
        )
        ShowSeat.objects.filter(id__in=show_seat_ids).update(
            status=ShowSeat.Status.AVAILABLE,
            held_until=None,
            held_by=None,
        )
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status"])
    return booking