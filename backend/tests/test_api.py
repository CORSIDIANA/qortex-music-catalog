from unittest.mock import patch

import pytest
from django.db import DatabaseError
from django.urls import reverse

from catalog.models import Album, AlbumTrack, Artist, Song
from catalog.serializers import AlbumSerializer

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("resource,field", [("artists", "name"), ("songs", "title")])
def test_artist_and_song_crud(client, resource, field):
    response = client.post(f"/api/{resource}/", {field: "  New entry  "}, format="json")
    assert response.status_code == 201
    assert response.data[field] == "New entry"
    assert response.data["album_count"] == 0
    url = f"/api/{resource}/{response.data['id']}/"
    assert client.get(url).status_code == 200
    response = client.patch(url, {field: "Changed"}, format="json")
    assert response.status_code == 200
    assert response.data[field] == "Changed"
    response = client.put(url, {field: "Replaced"}, format="json")
    assert response.status_code == 200
    assert response.data[field] == "Replaced"
    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404


def test_album_crud(client, artist):
    body = {"title": "An Album", "artist": artist.pk, "release_year": 2025}
    response = client.post("/api/albums/", body, format="json")
    assert response.status_code == 201
    assert response.data["artist_name"] == artist.name
    assert response.data["tracks"] == []
    assert response.data["track_count"] == 0
    url = f"/api/albums/{response.data['id']}/"
    assert client.get(url).status_code == 200
    response = client.patch(url, {"title": "Updated", "revision": 999}, format="json")
    assert response.status_code == 200
    assert response.data["title"] == "Updated"
    assert response.data["revision"] == 0
    response = client.put(url, body | {"release_year": 2026}, format="json")
    assert response.status_code == 200
    assert response.data["release_year"] == 2026
    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404


def test_same_song_two_albums_api_and_database(client, album, song):
    other = Album.objects.create(title="Anthology", artist=album.artist, release_year=2025)
    for target, number in [(album, 2), (other, 7)]:
        response = client.post(
            f"/api/albums/{target.pk}/tracks/",
            {"song": song.pk, "track_number": number},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["tracks"][0]["song"] == song.pk
        assert response.data["tracks"][0]["track_number"] == number
    detail = client.get(f"/api/songs/{song.pk}/").data
    assert detail["album_count"] == 2
    assert {(row["album"], row["track_number"]) for row in detail["appears_on"]} == {
        (album.pk, 2),
        (other.pk, 7),
    }
    assert Song.objects.count() == 1
    assert list(AlbumTrack.objects.filter(song=song).values_list("track_number", flat=True)) == [
        2,
        7,
    ]


def test_add_inline_append_remove_keeps_song(client, album):
    url = f"/api/albums/{album.pk}/tracks/"
    first = client.post(url, {"title": "New Song", "track_number": 7}, format="json")
    assert first.status_code == 201
    second = client.post(url, {"title": "Next Song"}, format="json")
    assert second.status_code == 201
    assert [row["track_number"] for row in second.data["tracks"]] == [7, 8]
    assert second.data["revision"] == 2
    placement = first.data["tracks"][0]
    assert client.delete(f"{url}{placement['id']}/").status_code == 204
    assert Song.objects.filter(pk=placement["song"]).exists()
    assert client.get(f"/api/albums/{album.pk}/").data["revision"] == 3


def test_duplicate_placement_and_position_rejected(client, album, song):
    url = f"/api/albums/{album.pk}/tracks/"
    assert client.post(url, {"song": song.pk}, format="json").status_code == 201
    assert client.post(url, {"song": song.pk}, format="json").status_code == 400
    response = client.post(url, {"title": "Must not survive", "track_number": 1}, format="json")
    assert response.status_code == 400
    assert not Song.objects.filter(title="Must not survive").exists()
    assert Album.objects.get(pk=album.pk).revision == 1


def test_append_overflow_does_not_create_orphan(client, album, song):
    AlbumTrack.objects.create(album=album, song=song, track_number=32767)
    response = client.post(f"/api/albums/{album.pk}/tracks/", {"title": "No room"}, format="json")
    assert response.status_code == 400
    assert Song.objects.count() == 1
    album.refresh_from_db()
    assert album.revision == 0


def test_reorder_swaps_and_normalizes(client, album, tracks):
    tracks[2].track_number = 32767
    tracks[2].save()
    ids = [track.pk for track in reversed(tracks)]
    response = client.put(
        f"/api/albums/{album.pk}/tracks/reorder/", {"track_ids": ids, "revision": 0}, format="json"
    )
    assert response.status_code == 200
    assert [row["id"] for row in response.data["tracks"]] == ids
    assert [row["track_number"] for row in response.data["tracks"]] == [1, 2, 3]
    assert response.data["revision"] == 1
    assert Song.objects.count() == 3


@pytest.mark.parametrize("mode", ["duplicate", "missing", "foreign", "stale"])
def test_bad_reorder_leaves_everything_unchanged(client, album, tracks, mode):
    ids = [track.pk for track in tracks]
    body = {"track_ids": list(reversed(ids)), "revision": 0}
    if mode == "duplicate":
        body["track_ids"] = [ids[0], ids[0], ids[2]]
    elif mode == "missing":
        body["track_ids"] = ids[:-1]
    elif mode == "foreign":
        other = Album.objects.create(title="Other", artist=album.artist, release_year=2024)
        foreign = AlbumTrack.objects.create(album=other, song=tracks[0].song, track_number=1)
        body["track_ids"] = [*ids[:-1], foreign.pk]
    else:
        body["revision"] = 10
    response = client.put(f"/api/albums/{album.pk}/tracks/reorder/", body, format="json")
    assert response.status_code == (409 if mode == "stale" else 400)
    assert list(album.tracks.values_list("pk", flat=True)) == ids
    assert list(album.tracks.values_list("track_number", flat=True)) == [1, 2, 3]
    album.refresh_from_db()
    assert album.revision == 0


def test_unexpected_failure_rolls_back_reorder(client, album, tracks):
    original = list(album.tracks.values_list("id", "track_number"))
    with (
        patch("catalog.tracklists.advance_revision", side_effect=RuntimeError("Injected failure")),
        pytest.raises(RuntimeError, match="Injected failure"),
    ):
        client.put(
            f"/api/albums/{album.pk}/tracks/reorder/",
            {"track_ids": [track.pk for track in reversed(tracks)], "revision": 0},
            format="json",
        )
    assert list(album.tracks.values_list("id", "track_number")) == original


def test_metadata_update_does_not_clobber_revision(album):
    stale_instance = Album.objects.get(pk=album.pk)
    Album.objects.filter(pk=album.pk).update(revision=5)
    serializer = AlbumSerializer(stale_instance, data={"title": "Metadata"}, partial=True)
    assert serializer.is_valid()
    serializer.save()
    album.refresh_from_db()
    assert album.revision == 5


def test_admin_metadata_update_does_not_clobber_revision(album):
    from django.contrib import admin

    stale_instance = Album.objects.get(pk=album.pk)
    Album.objects.filter(pk=album.pk).update(revision=5)
    stale_instance.title = "Admin metadata"
    admin.site._registry[Album].save_model(None, stale_instance, None, change=True)
    album.refresh_from_db()
    assert album.revision == 5
    assert album.title == "Admin metadata"


def test_empty_tracklist_can_be_saved(client, album):
    response = client.put(
        f"/api/albums/{album.pk}/tracks/reorder/",
        {"track_ids": [], "revision": 0},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["tracks"] == []
    assert response.data["revision"] == 1


def test_protected_delete_and_related_detail(client, album, song):
    AlbumTrack.objects.create(album=album, song=song, track_number=1)
    assert client.delete(f"/api/songs/{song.pk}/").status_code == 409
    assert client.delete(f"/api/artists/{album.artist_id}/").status_code == 409
    artist = client.get(f"/api/artists/{album.artist_id}/").data
    assert artist["album_count"] == 1
    assert artist["albums"][0]["track_count"] == 1


@pytest.mark.parametrize("resource", ["albums", "artists", "songs"])
@pytest.mark.parametrize("identifier", [999999, "invalid", "-1", "1.5", "9" * 100])
def test_missing_resources(client, resource, identifier):
    assert client.get(f"/api/{resource}/{identifier}/").status_code == 404


def test_missing_and_foreign_tracks(client, album, tracks):
    other = Album.objects.create(title="Other", artist=album.artist, release_year=2020)
    assert client.delete(f"/api/albums/{other.pk}/tracks/{tracks[0].pk}/").status_code == 404
    assert client.delete("/api/albums/invalid/tracks/1/").status_code == 404
    assert (
        client.post("/api/albums/999999/tracks/", {"title": "X"}, format="json").status_code == 404
    )
    assert (
        client.post(f"/api/albums/{album.pk}/tracks/", {"song": 999999}, format="json").status_code
        == 400
    )


@pytest.mark.parametrize("payload", [None, [], "hello", 5, True])
def test_invalid_object_payload(client, album, payload):
    import json

    response = client.generic(
        "POST",
        f"/api/albums/{album.pk}/tracks/",
        json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": " "},
        {"title": 20},
        {"title": "x" * 201},
        {"title": "x", "song": 1},
        {"song": None},
    ],
)
def test_invalid_add_payload(client, album, payload):
    assert client.post(f"/api/albums/{album.pk}/tracks/", payload, format="json").status_code == 400


@pytest.mark.parametrize("invalid", [0, -1, 32768, True, 1.5, "2"])
def test_invalid_track_number(client, album, invalid):
    response = client.post(
        f"/api/albums/{album.pk}/tracks/", {"title": "X", "track_number": invalid}, format="json"
    )
    assert response.status_code == 400
    assert Song.objects.count() == 0


@pytest.mark.parametrize("invalid", [True, 1.5, "1"])
def test_strict_ids_and_revision(client, album, song, tracks, invalid):
    assert (
        client.post(f"/api/albums/{album.pk}/tracks/", {"song": invalid}, format="json").status_code
        == 400
    )
    for body in [
        {"track_ids": [track.pk for track in tracks], "revision": invalid},
        {"track_ids": [invalid], "revision": 0},
    ]:
        assert (
            client.put(f"/api/albums/{album.pk}/tracks/reorder/", body, format="json").status_code
            == 400
        )


@pytest.mark.parametrize(
    "change",
    [
        {"title": " "},
        {"artist": 999999},
        {"artist": True},
        {"release_year": 0},
        {"release_year": 10000},
        {"release_year": 1.5},
    ],
)
def test_album_validation(client, artist, change):
    body = {"title": "Album", "artist": artist.pk, "release_year": 2024} | change
    assert client.post("/api/albums/", body, format="json").status_code == 400


def test_search_filters_and_pagination(client, album, song):
    assert client.get("/api/albums/?search=example").data["count"] == 1
    assert client.get("/api/albums/?search=missing").data["count"] == 0
    assert client.get(f"/api/albums/?artist={album.artist_id}&release_year=2024").data["count"] == 1
    assert client.get("/api/albums/?release_year=1990").data["count"] == 0
    assert client.get("/api/artists/?search=example").data["count"] == 1
    assert client.get("/api/songs/?search=shared").data["count"] == 1
    Song.objects.bulk_create([Song(title=f"Song {i:02d}") for i in range(30)])
    first = client.get("/api/songs/").data
    assert first["count"] == 31
    assert len(first["results"]) == 24
    assert first["next"] is not None
    second = client.get("/api/songs/?page=2").data
    assert len(second["results"]) == 7
    assert second["previous"] is not None
    assert not set(row["id"] for row in first["results"]) & set(
        row["id"] for row in second["results"]
    )


def test_paginated_lists_have_explicit_stable_order(client, artist):
    older = Album.objects.create(title="Alpha", artist=artist, release_year=2000)
    later_z = Album.objects.create(title="Zulu", artist=artist, release_year=2025)
    later_a = Album.objects.create(title="Alpha", artist=artist, release_year=2025)
    later_a2 = Album.objects.create(title="Alpha", artist=artist, release_year=2025)
    assert [row["id"] for row in client.get("/api/albums/").data["results"]] == [
        later_a.pk,
        later_a2.pk,
        later_z.pk,
        older.pk,
    ]
    early_artist = Artist.objects.create(name="Alpha")
    assert [row["id"] for row in client.get("/api/artists/").data["results"]] == [
        early_artist.pk,
        artist.pk,
    ]
    z_song = Song.objects.create(title="Zulu")
    a_song = Song.objects.create(title="Alpha")
    a_song2 = Song.objects.create(title="Alpha")
    assert [row["id"] for row in client.get("/api/songs/").data["results"]] == [
        a_song.pk,
        a_song2.pk,
        z_song.pk,
    ]


@pytest.mark.parametrize(
    "query", ["artist=x", "artist=0", "release_year=abc", "release_year=10000", "release_year=1.5"]
)
def test_invalid_filters(client, query):
    assert client.get(f"/api/albums/?{query}").status_code == 400


def test_album_list_and_detail_query_budget(client, album, tracks, django_assert_max_num_queries):
    for index in range(10):
        another = Album.objects.create(
            title=f"Another {index}", artist=album.artist, release_year=2024
        )
        AlbumTrack.objects.create(album=another, song=tracks[0].song, track_number=1)
    with django_assert_max_num_queries(2):
        response = client.get("/api/albums/")
    assert response.status_code == 200
    assert response.data["count"] == 11
    with django_assert_max_num_queries(2):
        response = client.get(f"/api/albums/{album.pk}/")
    assert response.status_code == 200
    assert len(response.data["tracks"]) == 3


def test_health_reflects_database_availability(client):
    assert client.get("/api/health/").status_code == 200
    with patch("catalog.views.connection.cursor", side_effect=DatabaseError("private connection")):
        response = client.get("/api/health/")
    assert response.status_code == 503
    assert "private" not in str(response.data)


def test_malformed_json(client):
    assert (
        client.post("/api/songs/", '{"title":', content_type="application/json").status_code == 400
    )


def test_admin_registered(client):
    assert client.get(reverse("admin:login")).status_code == 200
    from django.contrib import admin

    assert all(model in admin.site._registry for model in [Artist, Album, Song, AlbumTrack])
