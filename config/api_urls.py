from rest_framework.routers import DefaultRouter

from apps.movies.views import MovieViewSet

router = DefaultRouter()
router.register("movies", MovieViewSet, basename="movie")

urlpatterns = router.urls