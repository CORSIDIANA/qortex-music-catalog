from django.contrib import admin
from django.db.models import Count

from .models import Album, AlbumTrack, Artist, Song
from .updates import update_existing


class CatalogAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if change:
            update_existing(
                obj,
                {
                    field.name: getattr(obj, field.name)
                    for field in obj._meta.concrete_fields
                    if field.editable and not field.primary_key
                },
            )
        else:
            super().save_model(request, obj, form, change)


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
class ArtistAdmin(CatalogAdmin):
    list_display = ["name", "album_count"]
    search_fields = ["name"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_album_count=Count("albums"))

    @admin.display(description="Albums", ordering="_album_count")
    def album_count(self, obj):
        return obj._album_count


@admin.register(Album)
class AlbumAdmin(CatalogAdmin):
    list_display = ["title", "artist", "release_year", "revision"]
    list_filter = ["release_year", "artist"]
    search_fields = ["title", "artist__name"]
    autocomplete_fields = ["artist"]
    list_select_related = ["artist"]
    readonly_fields = ["revision"]
    inlines = [TrackInline]


@admin.register(Song)
class SongAdmin(CatalogAdmin):
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
