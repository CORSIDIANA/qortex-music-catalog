# Music Catalog specification

Status: implementation contract, 2026-09-12. Changes must retain the acceptance cases below.

## Purpose and scope

A small catalog for browsing and editing artists, albums, songs and ordered tracklists.
One song is a reusable catalog identity, even when placed on several albums.
Titles and artist names are not globally unique; different recordings can share a title.

## Domain

- Artist: integer ID, nonblank name (200 characters maximum).
- Album: integer ID, nonblank title (200), artist FK, release year (1–9999), tracklist revision.
- Song: integer ID, nonblank title (200).
- AlbumTrack: integer ID, album FK, song FK, positive track number (1–32767).
- Album exposes songs through AlbumTrack. Track number never belongs to Song.
- Database checks enforce positive track numbers and valid release years.
- Database unique constraints protect (album, track_number) and (album, song).
- Album deletion removes its placements, not its songs. Artist deletion is protected while it has albums.
- Song deletion is protected while it is placed; removing a placement never deletes a Song.
- Stable ordering: artists/songs by name/title then ID; albums by descending year then title/ID; tracks by number.
- Track-number gaps are allowed for explicit placement. Reorder normalizes to 1…N.
- Django Admin exposes placements read-only; placement writes use the API mutation path so revision checks remain meaningful.

## API contract

All routes use `/api/` and trailing slashes. JSON errors follow standard DRF field errors or `detail`.
List responses are `{count, next, previous, results}` with 24 rows per page.
`search` applies to artist names, album title/artist name and song title.
Albums accept `artist` and `release_year` filters. Invalid filters return 400.

| Route | Methods | Representation / input |
| --- | --- | --- |
| artists/ and artists/{id}/ | GET, POST / GET, PUT, PATCH, DELETE | id, name, album_count; detail includes albums |
| albums/ and albums/{id}/ | GET, POST / GET, PUT, PATCH, DELETE | id, title, artist (ID), artist_name, release_year, track_count, revision; detail includes tracks |
| songs/ and songs/{id}/ | GET, POST / GET, PUT, PATCH, DELETE | id, title, album_count; detail includes appears_on |
| albums/{id}/tracks/ | POST | song (existing ID) OR title (new song), optional track_number; creates one placement atomically |
| albums/{id}/tracks/{track_id}/ | DELETE | remove this placement only |
| albums/{id}/tracks/reorder/ | PUT | {track_ids: [placement IDs in desired order], revision: integer} |
| health/ | GET | readiness checks database access |

Tracks serialize as `{id, song, song_title, track_number}`.
Appears-on rows serialize as `{album, album_title, artist_name, track_number}`.
Create returns 201, read/update 200, successful deletion 204, malformed input 400, missing resource 404,
protected deletion / stale revision 409. Track mutation responses return the refreshed album detail (POST: 201).
DELETE placement returns 204; frontend reloads album.
Metadata edits target existing rows only: if an item is deleted during an update, return 404 without recreating it.
Reorder requires each current placement exactly once. Foreign, missing or repeated IDs are rejected with no change.
Every track mutation locks the parent album and increments its revision. A stale reorder gets 409.
Reorder must be atomic under PostgreSQL constraints, including when swapping occupied numbers.
Omitted track_number appends at the current maximum plus one; exceeding 32767 returns 400.
IDs, revisions and track numbers must be integers, never booleans or fractional numbers. Mutation payloads must be objects.

## User experience

- Responsive albums overview with search, artist filter, counts and clear loading/empty/error states.
- Album detail with metadata editing, deletion confirmation and ordered tracks.
- Smart editor supports pointer drag-and-drop and keyboard move up/down controls.
- Changes to order remain a local draft until Save order; Cancel restores persisted order.
- Existing-song search, inline song creation, duplicate-placement feedback, remove placement.
- Artists can be browsed/created/edited/deleted, with links to their albums.
- Songs can be searched/created/edited/deleted; detail shows Appears on with album, artist and track number.
- Forms have labels, visible focus, pending state and server-side validation feedback.
- Navigating away from an unsaved order asks before discarding it.
- Switching directly to another album applies the same unsaved-order guard.

## Acceptance

1. One Song X exists in the database and API; Album A places it at 2 and Album B at 7.
2. Direct database writes cannot create repeated album positions, duplicate placements or nonpositive numbers.
3. CRUD, search, pagination, validation, missing/foreign IDs and protected deletion have exercised API tests.
4. Failed/stale reorder does not partially alter the tracklist; valid reorder normalizes numbers and preserves song identities.
5. PostgreSQL tests use simultaneous connections: same-revision reorders yield one 200 and one 409;
   concurrent duplicate placements yield one 201 and one 400/409. Neither leaves a partial write.
6. `cp .env.example .env` and `docker compose up --build` start PostgreSQL, Django and Vue from a fresh volume.
7. The default development seed creates an immediately useful catalog, including case 1, and is safe to repeat.
8. Django check, migration drift check, backend tests, lint/format, frontend typecheck/build and Docker smoke all exit zero.
9. Browser verification covers the central song-reuse flow, order save, error/empty states and narrow-screen layout.

## Deliberate non-goals

Authentication for the public demo API, streaming/audio, image uploads, external music APIs, OAuth,
recommendations, deployment automation and a general-purpose repository/service framework.
The development stack binds only to loopback. Django Admin retains Django staff authentication.
No internal business logic, proprietary documents, customer data, credentials or external endpoints are imported.
