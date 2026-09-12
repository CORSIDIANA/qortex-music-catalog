from rest_framework import serializers

from .models import Album, AlbumTrack, Artist, Song


class StrictIntegerField(serializers.IntegerField):
    def to_internal_value(self, data):
        if not isinstance(data, int) or isinstance(data, bool):
            self.fail("invalid")
        return super().to_internal_value(data)


class StrictCharField(serializers.CharField):
    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid")
        return super().to_internal_value(data)


class AlbumTrackSerializer(serializers.ModelSerializer):
    song_title = serializers.CharField(source="song.title", read_only=True)

    class Meta:
        model = AlbumTrack
        fields = ["id", "song", "song_title", "track_number"]


class AlbumSerializer(serializers.ModelSerializer):
    title = StrictCharField(max_length=200)
    artist = serializers.PrimaryKeyRelatedField(
        queryset=Artist.objects.all(), pk_field=StrictIntegerField(min_value=1)
    )
    release_year = StrictIntegerField(min_value=1, max_value=9999)
    artist_name = serializers.CharField(source="artist.name", read_only=True)
    track_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Album
        fields = ["id", "title", "artist", "artist_name", "release_year", "track_count", "revision"]
        read_only_fields = ["revision"]

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if validated_data:
            # Metadata edits must not write an older revision over a concurrent track edit.
            instance.save(update_fields=list(validated_data))
        return instance


class AlbumDetailSerializer(AlbumSerializer):
    tracks = AlbumTrackSerializer(many=True, read_only=True)

    class Meta(AlbumSerializer.Meta):
        fields = [*AlbumSerializer.Meta.fields, "tracks"]


class ArtistSerializer(serializers.ModelSerializer):
    name = StrictCharField(max_length=200)
    album_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Artist
        fields = ["id", "name", "album_count"]


class ArtistDetailSerializer(ArtistSerializer):
    albums = AlbumSerializer(many=True, read_only=True)

    class Meta(ArtistSerializer.Meta):
        fields = [*ArtistSerializer.Meta.fields, "albums"]


class AppearanceSerializer(serializers.ModelSerializer):
    album_title = serializers.CharField(source="album.title", read_only=True)
    artist_name = serializers.CharField(source="album.artist.name", read_only=True)

    class Meta:
        model = AlbumTrack
        fields = ["album", "album_title", "artist_name", "track_number"]


class SongSerializer(serializers.ModelSerializer):
    title = StrictCharField(max_length=200)
    album_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Song
        fields = ["id", "title", "album_count"]


class SongDetailSerializer(SongSerializer):
    appears_on = AppearanceSerializer(source="placements", many=True, read_only=True)

    class Meta(SongSerializer.Meta):
        fields = [*SongSerializer.Meta.fields, "appears_on"]


class AddTrackSerializer(serializers.Serializer):
    song = serializers.PrimaryKeyRelatedField(
        queryset=Song.objects.all(), required=False, pk_field=StrictIntegerField(min_value=1)
    )
    title = StrictCharField(max_length=200, required=False)
    track_number = StrictIntegerField(min_value=1, max_value=32767, required=False)

    def validate(self, attrs):
        if ("song" in attrs) == ("title" in attrs):
            raise serializers.ValidationError("Provide either song or title, exactly one.")
        return attrs


class ReorderSerializer(serializers.Serializer):
    track_ids = serializers.ListField(child=StrictIntegerField(min_value=1), max_length=32767)
    revision = StrictIntegerField(min_value=0)

    def validate_track_ids(self, values):
        if len(values) != len(set(values)):
            raise serializers.ValidationError("Each placement must appear exactly once.")
        return values


class AlbumFilterSerializer(serializers.Serializer):
    artist = serializers.IntegerField(min_value=1, required=False)
    release_year = serializers.IntegerField(min_value=1, max_value=9999, required=False)
