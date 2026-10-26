from django.contrib import admin
from .models import Show, ShowSeat


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ("movie", "screen", "start_time", "end_time", "is_active")
    list_filter = ("is_active", "screen__theatre__city")
    search_fields = ("movie__title",)
    autocomplete_fields = ("movie",)

@admin.register(ShowSeat)
class ShowSeatAdmin(admin.ModelAdmin):
    list_display = ("show", "seat", "status", "held_until")
    list_filter = ("status",)    