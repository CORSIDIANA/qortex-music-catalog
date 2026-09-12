from django.db import DatabaseError, connection
from django.db.models import Count, Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import Album, AlbumTrack, Artist, Song
from .serializers import (
    AddTrackSerializer,
    AlbumDetailSerializer,
    AlbumFilterSerializer,
    AlbumSerializer,
    ArtistDetailSerializer,
    ArtistSerializer,
    ReorderSerializer,
    SongDetailSerializer,
    SongSerializer,
)
from .tracklists import add_track, remove_track, reorder_tracks


def albums_with_counts():
    return (
        Album.objects.select_related("artist")
        .annotate(track_count=Count("tracks"))
        .order_by("-release_year", "title", "id")
    )


class ArtistViewSet(viewsets.ModelViewSet):
    lookup_value_regex = r"\d+"
    search_fields = ["name"]

    def get_queryset(self):
        queryset = Artist.objects.annotate(album_count=Count("albums")).order_by("name", "id")
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(Prefetch("albums", queryset=albums_with_counts()))
        return queryset

    def get_serializer_class(self):
        return ArtistDetailSerializer if self.action == "retrieve" else ArtistSerializer

    def perform_create(self, serializer):
        artist = serializer.save()
        artist.album_count = 0


class AlbumViewSet(viewsets.ModelViewSet):
    lookup_value_regex = r"\d+"
    search_fields = ["title", "artist__name"]

    def get_queryset(self):
        queryset = albums_with_counts()
        if self.action == "list":
            filters = AlbumFilterSerializer(data=self.request.query_params)
            filters.is_valid(raise_exception=True)
            queryset = queryset.filter(**filters.validated_data)
        if self.action != "list":
            queryset = queryset.prefetch_related(
                Prefetch("tracks", queryset=AlbumTrack.objects.select_related("song"))
            )
        return queryset

    def get_serializer_class(self):
        return AlbumSerializer if self.action == "list" else AlbumDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        album = serializer.save()
        self.kwargs["pk"] = album.pk
        return self.album_response(status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            self.get_object(), data=request.data, partial=kwargs.pop("partial", False)
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.album_response()

    def album_response(self, response_status=status.HTTP_200_OK):
        return Response(AlbumDetailSerializer(self.get_object()).data, status=response_status)

    @action(detail=True, methods=["post"], url_path="tracks")
    def tracks(self, request, pk=None):
        self.get_object()
        serializer = AddTrackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        add_track(pk, serializer.validated_data)
        return self.album_response(status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"tracks/(?P<track_id>\d+)")
    def remove_track(self, request, pk=None, track_id=None):
        remove_track(pk, track_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["put"], url_path="tracks/reorder")
    def reorder(self, request, pk=None):
        self.get_object()
        serializer = ReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reorder_tracks(pk, serializer.validated_data)
        return self.album_response()


class SongViewSet(viewsets.ModelViewSet):
    lookup_value_regex = r"\d+"
    search_fields = ["title"]

    def perform_create(self, serializer):
        song = serializer.save()
        song.album_count = 0

    def get_queryset(self):
        queryset = Song.objects.annotate(album_count=Count("placements")).order_by("title", "id")
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                Prefetch(
                    "placements",
                    queryset=AlbumTrack.objects.select_related("album__artist").order_by(
                        "album__title", "album_id"
                    ),
                )
            )
        return queryset

    def get_serializer_class(self):
        return SongDetailSerializer if self.action == "retrieve" else SongSerializer


@api_view(["GET"])
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return Response({"status": "unavailable"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response({"status": "ok"})
