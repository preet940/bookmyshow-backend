from rest_framework.routers import DefaultRouter

from apps.movies.views import MovieViewSet
from apps.shows.views import ShowViewSet

router = DefaultRouter()
router.register("movies", MovieViewSet, basename="movie")
router.register("shows", ShowViewSet, basename="show")

urlpatterns = router.urls