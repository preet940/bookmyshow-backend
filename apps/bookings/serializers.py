from rest_framework import serializers

from .models import Booking


class CreateBookingSerializer(serializers.Serializer):
    show_id = serializers.IntegerField()
    seat_ids = serializers.ListField(
        child=serializers.IntegerField(), min_length=1, max_length=10
    )


class BookingSerializer(serializers.ModelSerializer):
    seats = serializers.SerializerMethodField()
    movie_title = serializers.CharField(source="show.movie.title", read_only=True)

    class Meta:
        model = Booking
        fields = ["id", "show", "movie_title", "status", "total_amount", "seats", "created_at"]

    def get_seats(self, obj):
        return [
            f"{bs.show_seat.seat}"
            for bs in obj.booking_seats.all()
        ]