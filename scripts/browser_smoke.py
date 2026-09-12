"""Check critical user flows in Chromium, keeping screenshots and cleaning test records."""

import re
import sys
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import expect, sync_playwright


def main(base_url):
    evidence = Path(__file__).resolve().parents[1] / ".local" / "browser"
    evidence.mkdir(parents=True, exist_ok=True)
    suffix = uuid4().hex[:8]
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(base_url=base_url, viewport={"width": 1440, "height": 1050})
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))

        def api(method, path, data=None, expected=200):
            response = context.request.fetch("/api/" + path, method=method, data=data)
            assert response.status == expected, (path, response.status, response.text())
            return response.json() if response.status != 204 else None

        artist = None
        albums = []
        song = None
        try:
            page.goto("/albums")
            expect(page.get_by_role("heading", name="Your albums")).to_be_visible()
            expect(page.locator(".album-card").first).to_be_visible()
            page.screenshot(path=str(evidence / "albums-desktop.png"), full_page=True)
            shared = api("GET", "songs/?search=Satellite%20Hearts")["results"][0]
            page.goto(f"/songs/{shared['id']}")
            expect(page.get_by_role("heading", name="Appears on")).to_be_visible()
            expect(page.get_by_text("Track 02", exact=True)).to_be_visible()
            expect(page.get_by_text("Track 07", exact=True)).to_be_visible()
            page.screenshot(path=str(evidence / "song-appearances.png"), full_page=True)

            page.get_by_role("navigation").get_by_role("link", name="Artists", exact=True).click()
            page.get_by_role("button", name=re.compile("Add artist")).click()
            page.get_by_label("Artist name", exact=True).fill(f"Browser Artist {suffix}")
            page.get_by_role("button", name="Create artist", exact=True).click()
            expect(
                page.get_by_role("heading", name=f"Browser Artist {suffix}", exact=True)
            ).to_be_visible()
            artist = int(page.url.rstrip("/").split("/")[-1])
            page.get_by_role("button", name="Edit artist", exact=True).click()
            page.get_by_label("Artist name", exact=True).fill(f"Browser Artist Updated {suffix}")
            page.get_by_role("button", name="Save changes", exact=True).click()
            expect(
                page.get_by_role("heading", name=f"Browser Artist Updated {suffix}", exact=True)
            ).to_be_visible()

            page.get_by_role("navigation").get_by_role("link", name="Albums", exact=True).click()
            page.get_by_role("button", name=re.compile("Add album")).click()
            page.get_by_label("Album title", exact=True).fill(f"Browser Album {suffix}")
            page.get_by_role("combobox", name="Artist", exact=True).select_option(str(artist))
            page.get_by_label("Release year", exact=True).fill("2024")
            page.get_by_role("button", name="Create album", exact=True).click()
            expect(
                page.get_by_role("heading", name=f"Browser Album {suffix}", exact=True)
            ).to_be_visible()
            album = int(page.url.rstrip("/").split("/")[-1])
            albums.append(album)
            page.get_by_role("button", name="Edit album", exact=True).click()
            page.get_by_label("Album title", exact=True).fill(f"Browser Album Updated {suffix}")
            page.get_by_role("button", name="Save changes", exact=True).click()
            expect(
                page.get_by_role("heading", name=f"Browser Album Updated {suffix}", exact=True)
            ).to_be_visible()

            page.get_by_role("button", name=re.compile("^＋ Add song$")).click()
            page.get_by_label("Find an existing song", exact=True).fill("Satellite Hearts")
            page.locator(".song-suggestions button").filter(has_text="Satellite Hearts").click()
            expect(page.locator(".track-row")).to_have_count(1)
            page.get_by_role("button", name=re.compile("^＋ Add song$")).click()
            page.get_by_label("Find an existing song", exact=True).fill("Satellite Hearts")
            expect(
                page.locator(".song-suggestions button").filter(has_text="Satellite Hearts")
            ).to_be_disabled()
            page.get_by_role("button", name="Create a song", exact=True).click()
            page.get_by_label("New song title", exact=True).fill(f"Browser Song {suffix}")
            page.get_by_role("button", name="Create & add song", exact=True).click()
            expect(page.locator(".track-row")).to_have_count(2)
            detail = api("GET", f"albums/{album}/")
            song = next(
                row["song"]
                for row in detail["tracks"]
                if row["song_title"] == f"Browser Song {suffix}"
            )
            other = api(
                "POST",
                "albums/",
                {
                    "title": f"Second Album {suffix}",
                    "artist": artist,
                    "release_year": 2025,
                },
                201,
            )
            albums.append(other["id"])
            api(
                "POST",
                f"albums/{other['id']}/tracks/",
                {"song": song, "track_number": 7},
                201,
            )
            page.goto(f"/songs/{song}")
            expect(page.locator(".appearance-row")).to_have_count(2)
            expect(page.get_by_text("Track 02", exact=True)).to_be_visible()
            expect(page.get_by_text("Track 07", exact=True)).to_be_visible()
            page.get_by_role("button", name="Edit song", exact=True).click()
            page.get_by_label("Song title", exact=True).fill(f"Browser Song Updated {suffix}")
            page.get_by_role("button", name="Save changes", exact=True).click()
            expect(
                page.get_by_role("heading", name=f"Browser Song Updated {suffix}", exact=True)
            ).to_be_visible()
            expect(page.locator(".appearance-row")).to_have_count(2)

            page.goto(f"/albums/{album}")
            expect(page.locator(".track-row")).to_have_count(2)
            page.get_by_role(
                "button", name=f"Move Browser Song Updated {suffix} up", exact=True
            ).focus()
            page.keyboard.press("Enter")
            expect(page.get_by_text("Unsaved order", exact=True)).to_be_visible()
            page.once("dialog", lambda dialog: dialog.dismiss())
            page.get_by_role("navigation").get_by_role("link", name="Songs", exact=True).click()
            expect(page).to_have_url(re.compile(f"/albums/{album}$"))
            page.get_by_role("button", name="Save order", exact=True).click()
            expect(page.get_by_text("Track order saved.", exact=True).last).to_be_visible()
            assert api("GET", f"albums/{album}/")["tracks"][0]["song"] == song

            page.locator(".track-row").first.drag_to(page.locator(".track-row").last)
            expect(page.get_by_text("Unsaved order", exact=True)).to_be_visible()
            page.screenshot(path=str(evidence / "track-editor-draft.png"), full_page=True)
            latest = api("GET", f"albums/{album}/")
            api(
                "PUT",
                f"albums/{album}/tracks/reorder/",
                {
                    "track_ids": [row["id"] for row in latest["tracks"]],
                    "revision": latest["revision"],
                },
            )
            page.get_by_role("button", name="Save order", exact=True).click()
            expect(page.get_by_role("alert")).to_contain_text("changed in another session")
            page.once("dialog", lambda dialog: dialog.accept())
            page.get_by_role("button", name="Reload latest", exact=True).click()
            expect(page.get_by_text("Latest tracklist loaded.", exact=True).last).to_be_visible()
            page.locator(".track-row").first.drag_to(page.locator(".track-row").last)
            page.get_by_role("button", name="Save order", exact=True).click()
            expect(page.get_by_text("Track order saved.", exact=True).last).to_be_visible()
            page.reload()
            expect(page.locator(".track-row").last).to_contain_text(
                f"Browser Song Updated {suffix}"
            )
            page.get_by_role(
                "button",
                name=f"Remove Browser Song Updated {suffix} from album",
                exact=True,
            ).click()
            failed_refresh = []

            def fail_one_refresh(route):
                if route.request.method == "GET" and not failed_refresh:
                    failed_refresh.append(True)
                    route.abort("failed")
                else:
                    route.continue_()

            page.route(f"**/api/albums/{album}/", fail_one_refresh)
            page.get_by_role("button", name="Remove song", exact=True).click()
            expect(page.get_by_role("alert")).to_contain_text("The song was removed")
            expect(page.get_by_role("button", name=re.compile("^＋ Add song$"))).to_be_disabled()
            page.get_by_role("button", name="Reload latest tracklist", exact=True).click()
            expect(page.locator(".track-row")).to_have_count(1)
            page.unroute(f"**/api/albums/{album}/", fail_one_refresh)
            assert len(api("GET", f"songs/{song}/")["appears_on"]) == 1

            page.goto("/albums")
            page.get_by_role("searchbox", name="Search albums", exact=True).fill(
                "no-match-" + suffix
            )
            expect(page.get_by_text("No albums found", exact=True)).to_be_visible()
            page.get_by_role("searchbox", name="Search albums", exact=True).fill("")
            expect(page.locator(".album-card").first).to_be_visible()
            page.set_viewport_size({"width": 375, "height": 812})
            page.screenshot(path=str(evidence / "albums-mobile.png"), full_page=True)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            for path in (f"/albums/{album}", f"/songs/{song}", f"/artists/{artist}"):
                page.goto(path)
                expect(page.get_by_role("heading", level=1)).to_be_visible()
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            page.goto("/admin/login/")
            expect(page.get_by_label("Username:", exact=True)).to_be_visible()
            assert context.request.get("/static/admin/css/base.css").ok
            assert not errors, errors
        finally:
            if errors:
                print("Browser errors:", errors)
            page.screenshot(path=str(evidence / "last-page.png"), full_page=True)
            for album_id in albums:
                api("DELETE", f"albums/{album_id}/", expected=204)
            if song:
                api("DELETE", f"songs/{song}/", expected=204)
            if artist:
                api("DELETE", f"artists/{artist}/", expected=204)
            browser.close()
        print(
            "PASS: browser CRUD, shared-song appearances, duplicate feedback, "
            "keyboard and drag reorder, unsaved guard, stale conflict, persistence, "
            "removal and refresh recovery, empty state, mobile layouts, "
            "Admin assets, no page errors"
        )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5173")
