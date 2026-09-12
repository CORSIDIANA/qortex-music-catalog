"""Exercise the public API through the same origin as the browser."""

import json
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


def smoke(base_url):
    def request(method, path, payload=None, expected=200):
        data = None if payload is None else json.dumps(payload).encode()
        req = Request(
            base_url.rstrip("/") + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            response = urlopen(req, timeout=15)
        except HTTPError as error:
            response = error
        with response:
            body = response.read()
            assert response.status == expected, (method, path, response.status, body)
            return json.loads(body) if body else None

    with urlopen(base_url, timeout=15) as response:
        assert response.status == 200 and b'<div id="app"' in response.read()
    request("GET", "/api/health/")
    suffix = uuid4().hex[:10]
    artist = request("POST", "/api/artists/", {"name": f"Smoke artist {suffix}"}, 201)
    albums, songs = [], []
    try:
        for title in ("First", "Second"):
            albums.append(
                request(
                    "POST",
                    "/api/albums/",
                    {
                        "title": f"{title} {suffix}",
                        "artist": artist["id"],
                        "release_year": 2024,
                    },
                    201,
                )
            )
        song = request("POST", "/api/songs/", {"title": f"Shared song {suffix}"}, 201)
        songs.append(song)
        for album, position in zip(albums, (2, 7), strict=True):
            detail = request(
                "POST",
                f"/api/albums/{album['id']}/tracks/",
                {
                    "song": song["id"],
                    "track_number": position,
                },
                201,
            )
            assert [(row["song"], row["track_number"]) for row in detail["tracks"]] == [
                (song["id"], position)
            ]
        appearances = request("GET", f"/api/songs/{song['id']}/")["appears_on"]
        assert {(row["album"], row["track_number"]) for row in appearances} == {
            (albums[0]["id"], 2),
            (albums[1]["id"], 7),
        }
        request("DELETE", f"/api/songs/{song['id']}/", expected=409)
        album_path = f"/api/albums/{albums[0]['id']}/"
        original = request("GET", album_path)
        request(
            "PUT",
            album_path + "tracks/reorder/",
            {
                "track_ids": [original["tracks"][0]["id"], original["tracks"][0]["id"]],
                "revision": original["revision"],
            },
            400,
        )
        assert request("GET", album_path) == original
        saved = request(
            "PUT",
            album_path + "tracks/reorder/",
            {
                "track_ids": [original["tracks"][0]["id"]],
                "revision": original["revision"],
            },
        )
        assert saved["tracks"][0]["track_number"] == 1
        request(
            "PUT",
            album_path + "tracks/reorder/",
            {
                "track_ids": [original["tracks"][0]["id"]],
                "revision": original["revision"],
            },
            409,
        )
        request("DELETE", album_path + f"tracks/{saved['tracks'][0]['id']}/", expected=204)
        remaining = request("GET", f"/api/songs/{song['id']}/")["appears_on"]
        assert len(remaining) == 1 and remaining[0]["track_number"] == 7
    finally:
        for album in albums:
            request("DELETE", f"/api/albums/{album['id']}/", expected=204)
        for song in songs:
            request("DELETE", f"/api/songs/{song['id']}/", expected=204)
        request("DELETE", f"/api/artists/{artist['id']}/", expected=204)
    print(
        "PASS: frontend, readiness, shared Song at positions 2/7, atomic validation, "
        "reorder, stale conflict, protected deletion and placement removal"
    )


if __name__ == "__main__":
    smoke(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5173")
