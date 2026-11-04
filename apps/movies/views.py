from rest_framework import viewsets

from .models import Movie
from .serializers import MovieSerializer


class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Movie.objects.filter(is_active=True)
    serializer_class = MovieSerializer
    lookup_field = "slug"
    filterset_fields = ["language", "certificate"]
    search_fields = ["title", "genre"]
    ordering_fields = ["release_date", "rating", "title"]