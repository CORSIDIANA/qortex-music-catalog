import pytest
from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from catalog.models import Album, AlbumTrack, Song

pytestmark = pytest.mark.django_db


def test_one_song_can_have_different_positions(album, song):
    other = Album.objects.create(title="Second Album", artist=album.artist, release_year=2025)
    first = AlbumTrack.objects.create(album=album, song=song, track_number=2)
    second = AlbumTrack.objects.create(album=other, song=song, track_number=7)
    assert first.song_id == second.song_id
    assert first.pk != second.pk
    assert Song.objects.count() == 1
    assert list(song.albums.order_by("id")) == [album, other]


def test_database_rejects_duplicate_position(album, song):
    AlbumTrack.objects.create(album=album, song=song, track_number=1)
    other_song = Song.objects.create(title="Other")
    with pytest.raises(IntegrityError), transaction.atomic():
        AlbumTrack.objects.create(album=album, song=other_song, track_number=1)


def test_database_rejects_duplicate_song(album, song):
    AlbumTrack.objects.create(album=album, song=song, track_number=1)
    with pytest.raises(IntegrityError), transaction.atomic():
        AlbumTrack.objects.create(album=album, song=song, track_number=2)


@pytest.mark.parametrize("number", [0, -1, 32768])
def test_database_rejects_invalid_position(album, song, number):
    with pytest.raises((IntegrityError, DataError)), transaction.atomic():
        AlbumTrack.objects.create(album=album, song=song, track_number=number)


@pytest.mark.parametrize("year", [0, -1, 10000])
def test_database_rejects_invalid_year(artist, year):
    with pytest.raises(IntegrityError), transaction.atomic():
        Album.objects.create(title="Invalid", artist=artist, release_year=year)


def test_foreign_key_integrity_is_checked_at_commit(album):
    with pytest.raises(IntegrityError), transaction.atomic():
        AlbumTrack.objects.create(album=album, song_id=999999, track_number=1)
        from django.db import connection

        connection.check_constraints()


def test_model_validation_and_strings(album, song):
    track = AlbumTrack(album=album, song=song, track_number=0)
    with pytest.raises(ValidationError):
        track.full_clean()
    assert str(album) == "First Album (2024)"
    assert str(album.artist) == "The Example"
    assert str(song) == "Shared Song"
    assert "Shared Song" in str(track)
    song.title = "  "
    with pytest.raises(ValidationError):
        song.full_clean()


def test_protection_and_album_cascade(album, song):
    AlbumTrack.objects.create(album=album, song=song, track_number=1)
    with pytest.raises(ProtectedError):
        song.delete()
    with pytest.raises(ProtectedError):
        album.artist.delete()
    album.delete()
    assert AlbumTrack.objects.count() == 0
    assert Song.objects.filter(pk=song.pk).exists()
