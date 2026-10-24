from django.contrib import admin
from .models import Movie


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "language", "genre", "release_date", "is_active")
    list_filter = ("language", "is_active", "certificate")
    search_fields = ("title", "genre")