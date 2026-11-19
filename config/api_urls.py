from rest_framework.routers import DefaultRouter

from apps.movies.views import MovieViewSet
from apps.shows.views import ShowViewSet
from apps.bookings.views import BookingViewSet

router = DefaultRouter()
router.register("movies", MovieViewSet, basename="movie")
router.register("shows", ShowViewSet, basename="show")
router.register("bookings", BookingViewSet, basename="booking")
urlpatterns = router.urls