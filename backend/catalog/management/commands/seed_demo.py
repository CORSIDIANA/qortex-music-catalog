from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Album, AlbumTrack, Artist, Song


class Command(BaseCommand):
    help = "Add a fictional demo catalog only when the catalog is completely empty."

    @transaction.atomic
    def handle(self, *args, **options):
        if Artist.objects.exists() or Album.objects.exists() or Song.objects.exists():
            self.stdout.write("Catalog already contains data; nothing changed.")
            return
        atlas = Artist.objects.create(name="Atlas & the Echo")
        mira = Artist.objects.create(name="Mira Sol")
        north = Artist.objects.create(name="Northbound")
        songs = {
            title: Song.objects.create(title=title)
            for title in [
                "First Light",
                "Satellite Hearts",
                "Velvet Morning",
                "After the Rain",
                "Slow Orbit",
                "Tide Pools",
                "Golden Hour",
                "Paper Planes",
                "Blue Geometry",
                "Almost Home",
                "Open Water",
                "Last Train",
            ]
        }
        albums = [
            (
                "Afterglow",
                atlas,
                2024,
                ["First Light", "Satellite Hearts", "Velvet Morning", "After the Rain"],
            ),
            (
                "Collected Signals",
                atlas,
                2025,
                [
                    "Slow Orbit",
                    "Tide Pools",
                    "Golden Hour",
                    "Paper Planes",
                    "Blue Geometry",
                    "Almost Home",
                    "Satellite Hearts",
                ],
            ),
            ("Soft Focus", mira, 2023, ["Golden Hour", "Tide Pools", "Open Water"]),
            ("The Long Way Home", north, 2025, ["Last Train", "Paper Planes", "Almost Home"]),
        ]
        for title, artist, year, titles in albums:
            album = Album.objects.create(title=title, artist=artist, release_year=year, revision=1)
            AlbumTrack.objects.bulk_create(
                [
                    AlbumTrack(album=album, song=songs[song_title], track_number=number)
                    for number, song_title in enumerate(titles, start=1)
                ]
            )
        self.stdout.write(self.style.SUCCESS("Created 3 artists, 4 albums and 12 reusable songs."))
