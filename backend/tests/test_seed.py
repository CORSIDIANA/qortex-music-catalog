from io import StringIO

import pytest
from django.core.management import call_command

from catalog.models import Album, AlbumTrack, Artist, Song

pytestmark = pytest.mark.django_db


def test_demo_seed_is_repeatable_and_shares_song():
    call_command("seed_demo", stdout=StringIO())
    counts = [model.objects.count() for model in (Artist, Album, Song, AlbumTrack)]
    shared = Song.objects.get(title="Satellite Hearts")
    assert list(shared.placements.values_list("track_number", flat=True)) == [2, 7]
    assert counts == [3, 4, 12, 17]
    Album.objects.filter(title="Afterglow").update(title="User edit")
    call_command("seed_demo", stdout=StringIO())
    assert counts == [model.objects.count() for model in (Artist, Album, Song, AlbumTrack)]
    assert Album.objects.filter(title="User edit").exists()


def test_seed_does_not_modify_existing_catalog(song):
    call_command("seed_demo", stdout=StringIO())
    assert Song.objects.count() == 1
    assert Artist.objects.count() == 0
