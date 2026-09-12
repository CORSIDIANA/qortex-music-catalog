from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connections
from django.test import Client
from django.urls import reverse
from rest_framework.test import APIClient

from catalog.models import Album, Artist, Song
from catalog.serializers import AlbumSerializer, ArtistSerializer, SongSerializer

pytestmark = pytest.mark.django_db(transaction=True)


def request_after_delete(model, instance, entry_class, entry_name, request):
    reached = Event()
    resume = Event()
    original = getattr(entry_class, entry_name)

    def wait_before_update(*args, **kwargs):
        reached.set()
        assert resume.wait(timeout=10)
        return original(*args, **kwargs)

    def worker():
        close_old_connections()
        try:
            return request().status_code
        finally:
            connections.close_all()

    with (
        patch.object(entry_class, entry_name, wait_before_update),
        ThreadPoolExecutor(max_workers=1) as executor,
    ):
        future = executor.submit(worker)
        try:
            assert reached.wait(timeout=10)
            # The second connection completes deletion after the first loaded its instance.
            assert APIClient().delete(f"/api/{model}/{instance.pk}/").status_code == 204
        finally:
            resume.set()
        status_code = future.result(timeout=10)
    assert not type(instance).objects.filter(pk=instance.pk).exists()
    assert status_code == 404


def make_item(model):
    if model == "albums":
        artist = Artist.objects.create(name="Race artist")
        instance = Album.objects.create(title="Race album", artist=artist, release_year=2024)
        return instance, {"title": "Edited album", "artist": artist.pk, "release_year": 2025}
    if model == "artists":
        return Artist.objects.create(name="Race artist"), {"name": "Edited artist"}
    return Song.objects.create(title="Race song"), {"title": "Edited song"}


@pytest.mark.parametrize(
    "model,serializer_class",
    [("albums", AlbumSerializer), ("artists", ArtistSerializer), ("songs", SongSerializer)],
)
@pytest.mark.parametrize("empty_patch", [False, True])
def test_api_update_does_not_restore_concurrently_deleted_item(
    model, serializer_class, empty_patch
):
    instance, fields = make_item(model)

    def request():
        return APIClient(raise_request_exception=False).patch(
            f"/api/{model}/{instance.pk}/", {} if empty_patch else fields, format="json"
        )

    request_after_delete(model, instance, serializer_class, "update", request)


@pytest.mark.parametrize("model", ["albums", "artists", "songs"])
def test_admin_update_does_not_restore_concurrently_deleted_item(model):
    instance, fields = make_item(model)
    user = get_user_model().objects.create_superuser(
        username="race-admin", password="test-password"
    )
    client = Client(raise_request_exception=False)
    client.force_login(user)
    if model == "albums":
        fields |= {
            "tracks-TOTAL_FORMS": "0",
            "tracks-INITIAL_FORMS": "0",
            "tracks-MIN_NUM_FORMS": "0",
            "tracks-MAX_NUM_FORMS": "0",
        }
    url = reverse(f"admin:catalog_{instance._meta.model_name}_change", args=[instance.pk])
    model_admin = admin.site._registry[type(instance)]
    request_after_delete(
        model, instance, type(model_admin), "save_model", lambda: client.post(url, fields)
    )
