import pytest
from rest_framework.test import APIClient

from catalog.models import Album, AlbumTrack, Artist, Song


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def artist(db):
    return Artist.objects.create(name="The Example")


@pytest.fixture
def album(artist):
    return Album.objects.create(title="First Album", artist=artist, release_year=2024)


@pytest.fixture
def song(db):
    return Song.objects.create(title="Shared Song")


@pytest.fixture
def tracks(album):
    return [
        AlbumTrack.objects.create(
            album=album, song=Song.objects.create(title=f"Song {number}"), track_number=number
        )
        for number in range(1, 4)
    ]
