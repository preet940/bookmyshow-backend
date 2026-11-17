from django.apps import AppConfig


class ShowsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.shows'

    def ready(self):
        from . import signals  # noqa: F401