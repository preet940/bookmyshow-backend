from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import ShowSeat

HOLD_MINUTES = 10


class SeatUnavailable(Exception):
    pass


def hold_seats(show_id, seat_ids):
    """Hold the given seats for HOLD_MINUTES. All or nothing."""
    now = timezone.now()
    with transaction.atomic():
        show_seats = list(
            ShowSeat.objects.select_for_update()
            .filter(show_id=show_id, seat_id__in=seat_ids)
            .order_by("seat_id")
        )

        if len(show_seats) != len(set(seat_ids)):
            raise SeatUnavailable("Some seats do not exist for this show.")

        for ss in show_seats:
            expired = ss.status == ShowSeat.Status.HELD and ss.held_until <= now
            if ss.status != ShowSeat.Status.AVAILABLE and not expired:
                raise SeatUnavailable(f"Seat {ss.seat} is not available.")

        hold_until = now + timedelta(minutes=HOLD_MINUTES)
        for ss in show_seats:
            ss.status = ShowSeat.Status.HELD
            ss.held_until = hold_until
        ShowSeat.objects.bulk_update(show_seats, ["status", "held_until"])

    return show_seats