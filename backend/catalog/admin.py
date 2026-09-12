from django.contrib import admin
from django.db.models import Count

from .models import Album, AlbumTrack, Artist, Song


class TrackInline(admin.TabularInline):
    model = AlbumTrack
    fields = ["track_number", "song"]
    readonly_fields = fields
    can_delete = False
    extra = 0
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ["name", "album_count"]
    search_fields = ["name"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_album_count=Count("albums"))

    @admin.display(description="Albums", ordering="_album_count")
    def album_count(self, obj):
        return obj._album_count


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ["title", "artist", "release_year", "revision"]
    list_filter = ["release_year", "artist"]
    search_fields = ["title", "artist__name"]
    autocomplete_fields = ["artist"]
    list_select_related = ["artist"]
    readonly_fields = ["revision"]
    inlines = [TrackInline]

    def save_model(self, request, obj, form, change):
        if change:
            obj.save(update_fields=["title", "artist", "release_year"])
        else:
            obj.save()


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ["title"]
    search_fields = ["title"]


@admin.register(AlbumTrack)
class AlbumTrackAdmin(admin.ModelAdmin):
    list_display = ["album", "track_number", "song"]
    list_filter = ["album__artist"]
    search_fields = ["album__title", "song__title"]
    list_select_related = ["album", "song"]
    readonly_fields = ["album", "song", "track_number"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.site_header = "Music Catalog administration"
admin.site.site_title = "Music Catalog"
