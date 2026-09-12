from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connections
from rest_framework.test import APIClient

from catalog.models import Album, AlbumTrack, Artist, Song

pytestmark = pytest.mark.django_db(transaction=True)


def concurrent_requests(method, url, bodies):
    barrier = Barrier(2)

    def request(body):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return getattr(APIClient(), method)(url, body, format="json").status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        return list(executor.map(request, bodies))


def setup_album():
    artist = Artist.objects.create(name="Concurrent Artist")
    album = Album.objects.create(title="Concurrent Album", artist=artist, release_year=2025)
    return album


def test_simultaneous_reorders_have_exactly_one_winner():
    album = setup_album()
    tracks = [
        AlbumTrack.objects.create(
            album=album, song=Song.objects.create(title=f"Song {i}"), track_number=i
        )
        for i in range(1, 4)
    ]
    ids = [track.pk for track in tracks]
    orders = [list(reversed(ids)), [ids[1], ids[2], ids[0]]]
    results = concurrent_requests(
        "put",
        f"/api/albums/{album.pk}/tracks/reorder/",
        [{"track_ids": order, "revision": 0} for order in orders],
    )
    assert sorted(results) == [200, 409]
    winner = results.index(200)
    assert list(album.tracks.values_list("pk", flat=True)) == orders[winner]
    album.refresh_from_db()
    assert album.revision == 1


def test_simultaneous_duplicate_adds_create_one_placement():
    album = setup_album()
    song = Song.objects.create(title="Only Once")
    results = concurrent_requests(
        "post", f"/api/albums/{album.pk}/tracks/", [{"song": song.pk}, {"song": song.pk}]
    )
    assert sorted(results) == [201, 400]
    assert album.tracks.count() == 1
    assert Song.objects.count() == 1
    album.refresh_from_db()
    assert album.revision == 1


def test_simultaneous_appends_choose_distinct_positions():
    album = setup_album()
    songs = [Song.objects.create(title=f"Song {i}") for i in range(2)]
    results = concurrent_requests(
        "post", f"/api/albums/{album.pk}/tracks/", [{"song": song.pk} for song in songs]
    )
    assert results == [201, 201]
    assert list(album.tracks.values_list("track_number", flat=True)) == [1, 2]
    album.refresh_from_db()
    assert album.revision == 2
