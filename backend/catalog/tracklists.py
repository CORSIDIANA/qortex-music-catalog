from django.db import connection, transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from .exceptions import Conflict
from .models import Album, AlbumTrack, Song


def advance_revision(album):
    album.revision += 1
    album.save(update_fields=["revision"])


@transaction.atomic
def add_track(album_id, data):
    album = get_object_or_404(Album.objects.select_for_update(), pk=album_id)
    song = data.get("song")
    if song and album.tracks.filter(song=song).exists():
        raise ValidationError({"song": "This song is already on this album."})
    number = data.get("track_number")
    if number is None:
        number = (album.tracks.aggregate(last=Max("track_number"))["last"] or 0) + 1
    if number > 32767:
        raise ValidationError({"track_number": "No position available. Reorder tracks first."})
    if album.tracks.filter(track_number=number).exists():
        raise ValidationError({"track_number": "This position is already occupied."})
    if song is None:
        song = Song.objects.create(title=data["title"])
    AlbumTrack.objects.create(album=album, song=song, track_number=number)
    advance_revision(album)


@transaction.atomic
def remove_track(album_id, track_id):
    album = get_object_or_404(Album.objects.select_for_update(), pk=album_id)
    placement = get_object_or_404(AlbumTrack, album=album, pk=track_id)
    placement.delete()
    advance_revision(album)


@transaction.atomic
def reorder_tracks(album_id, data):
    album = get_object_or_404(Album.objects.select_for_update(), pk=album_id)
    if album.revision != data["revision"]:
        raise Conflict("Tracklist changed. Reload this album before saving your order.")
    tracks = {track.pk: track for track in album.tracks.all()}
    ids = data["track_ids"]
    if len(ids) != len(tracks) or set(ids) != set(tracks):
        raise ValidationError({"track_ids": "Include every current placement exactly once."})
    for number, track_id in enumerate(ids, start=1):
        tracks[track_id].track_number = number
    # Defer only this uniqueness check so occupied positions can swap atomically.
    with connection.cursor() as cursor:
        cursor.execute('SET CONSTRAINTS "album_unique_track_number" DEFERRED')
        AlbumTrack.objects.bulk_update(tracks.values(), ["track_number"], batch_size=500)
        cursor.execute('SET CONSTRAINTS "album_unique_track_number" IMMEDIATE')
    advance_revision(album)
