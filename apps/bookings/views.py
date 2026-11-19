from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response

from .models import Booking
from .serializers import BookingSerializer, CreateBookingSerializer
from .services import BookingError, confirm_booking


class BookingViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Booking.objects.filter(user=self.request.user)
            .select_related("show__movie")
            .prefetch_related("booking_seats__show_seat__seat")
        )

    def create(self, request):
        key = request.headers.get("Idempotency-Key")
        if not key:
            return Response(
                {"detail": "Idempotency-Key header is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CreateBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            booking, created = confirm_booking(
                request.user,
                serializer.validated_data["show_id"],
                serializer.validated_data["seat_ids"],
                key,
            )
        except BookingError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        data = BookingSerializer(booking).data
        return Response(data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)