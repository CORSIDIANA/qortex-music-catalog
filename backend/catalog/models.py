from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

nonblank = RegexValidator(r"\S", "This value must contain a non-whitespace character.")


class Artist(models.Model):
    name = models.CharField(max_length=200, db_index=True, validators=[nonblank])

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name


class Song(models.Model):
    title = models.CharField(max_length=200, db_index=True, validators=[nonblank])

    class Meta:
        ordering = ["title", "id"]

    def __str__(self):
        return self.title


class Album(models.Model):
    title = models.CharField(max_length=200, validators=[nonblank])
    artist = models.ForeignKey(Artist, on_delete=models.PROTECT, related_name="albums")
    release_year = models.PositiveSmallIntegerField(
        db_index=True, validators=[MinValueValidator(1), MaxValueValidator(9999)]
    )
    revision = models.PositiveIntegerField(default=0, editable=False)
    songs = models.ManyToManyField(Song, through="AlbumTrack", related_name="albums")

    class Meta:
        ordering = ["-release_year", "title", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(release_year__gte=1, release_year__lte=9999),
                name="album_valid_release_year",
            )
        ]

    def __str__(self):
        return f"{self.title} ({self.release_year})"


class AlbumTrack(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="tracks")
    song = models.ForeignKey(Song, on_delete=models.PROTECT, related_name="placements")
    track_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(32767)]
    )

    class Meta:
        ordering = ["track_number", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(track_number__gte=1, track_number__lte=32767),
                name="track_number_in_range",
            ),
            models.UniqueConstraint(
                fields=["album", "track_number"],
                name="album_unique_track_number",
                deferrable=models.Deferrable.IMMEDIATE,
            ),
            models.UniqueConstraint(fields=["album", "song"], name="album_unique_song"),
        ]

    def __str__(self):
        return f"{self.track_number}. {self.song} — {self.album}"
