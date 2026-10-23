from django.contrib import admin
from .models import City, Theatre , Screen, Seat


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "state", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)

@admin.register(Theatre)
class TheatreAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "is_active")
    list_filter = ("city", "is_active")
    search_fields = ("name", "address")    

@admin.register(Screen)
class ScreenAdmin(admin.ModelAdmin):
    list_display = ("name", "theatre", "is_active")
    list_filter = ("theatre__city", "is_active")
    search_fields = ("name", "theatre__name")


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("screen", "row", "number", "seat_type")
    list_filter = ("seat_type", "screen")    