from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Show
from .serializers import ShowSeatSerializer, ShowSerializer


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