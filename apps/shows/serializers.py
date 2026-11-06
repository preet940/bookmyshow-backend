from rest_framework import serializers

from .models import Show, ShowSeat


class ShowSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    screen_name = serializers.CharField(source="screen.name", read_only=True)
    theatre_name = serializers.CharField(
        source="screen.theatre.name", read_only=True
    )
    city = serializers.CharField(
        source="screen.theatre.city.name", read_only=True
    )

    class Meta:
        model = Show
        fields = [
            "id", "movie", "movie_title", "theatre_name", "city",
            "screen_name", "start_time", "end_time",
            "price_regular", "price_premium", "price_recliner",
        ]


class ShowSeatSerializer(serializers.ModelSerializer):
    row = serializers.CharField(source="seat.row", read_only=True)
    number = serializers.IntegerField(source="seat.number", read_only=True)
    seat_type = serializers.CharField(source="seat.seat_type", read_only=True)

    class Meta:
        model = ShowSeat
        fields = ["id", "seat", "row", "number", "seat_type", "status"]