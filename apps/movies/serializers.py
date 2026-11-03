from rest_framework import serializers

from .models import Movie


class MovieSerializer(serializers.ModelSerializer):
    language_display = serializers.CharField(
        source="get_language_display", read_only=True
    )

    class Meta:
        model = Movie
        fields = [
            "id", "title", "slug", "description", "language",
            "language_display", "genre", "duration_minutes",
            "certificate", "rating", "release_date",
        ]