from django.utils import timezone
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Show
from .serializers import ShowSeatSerializer, ShowSerializer
from .services import SeatUnavailable, hold_seats


class HoldSeatsSerializer(serializers.Serializer):
    seat_ids = serializers.ListField(
        child=serializers.IntegerField(), min_length=1, max_length=10
    )


class ShowViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ShowSerializer
    filterset_fields = ["movie", "screen__theatre", "screen__theatre__city"]
    ordering_fields = ["start_time"]

    def get_queryset(self):
        return (
            Show.objects.filter(is_active=True, start_time__gte=timezone.now())
            .select_related("movie", "screen__theatre__city")
        )

    @action(detail=True, methods=["get"])
    def seats(self, request, pk=None):
        show = self.get_object()
        show_seats = (
            show.show_seats.select_related("seat")
            .order_by("seat__row", "seat__number")
        )
        return Response(ShowSeatSerializer(show_seats, many=True).data)

    @action(detail=True, methods=["post"],
            permission_classes=[permissions.IsAuthenticated])
    def hold(self, request, pk=None):
        show = self.get_object()
        serializer = HoldSeatsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            held = hold_seats(show.id, serializer.validated_data["seat_ids"])
        except SeatUnavailable as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response({
            "held_until": held[0].held_until,
            "seats": ShowSeatSerializer(held, many=True).data,
        })