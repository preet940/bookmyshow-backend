from django.db import models
from django.utils.text import slugify


class Movie(models.Model):
    class Language(models.TextChoices):
        ENGLISH = "en", "English"
        HINDI = "hi", "Hindi"
        KANNADA = "kn", "Kannada"
        TAMIL = "ta", "Tamil"
        TELUGU = "te", "Telugu"

    class Certificate(models.TextChoices):
        U = "U", "U"
        UA = "UA", "U/A"
        A = "A", "A"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    language = models.CharField(max_length=2, choices=Language.choices)
    genre = models.CharField(max_length=100)          # e.g. "Action, Thriller"
    duration_minutes = models.PositiveSmallIntegerField()
    certificate = models.CharField(
        max_length=2, choices=Certificate.choices, default=Certificate.UA
    )
    rating = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True
    )
    release_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-release_date"]
        indexes = [
            models.Index(fields=["is_active", "language"]),
            models.Index(fields=["title"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.title}-{self.language}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.get_language_display()})"