# Design decisions

## D001 — AlbumTrack is an explicit through model

A song has one identity. Its position belongs to its placement on an album. Database constraints
enforce positive positions, unique positions per album and unique song placements. Song titles are
not unique: different recordings can have the same name. Removing a placement preserves the song.

## D002 — PostgreSQL in development and tests

Tests use the same database engine as the application. This makes constraints and transaction behavior
part of the acceptance evidence. A named Docker volume preserves data through container recreation.

## D003 — A small REST boundary

Vue talks to Django REST Framework through the same origin. The frontend proxy avoids permissive
CORS settings. DRF serializers own input validation; PostgreSQL remains the final guard for invariants.
The application uses Django models directly instead of adding repository abstractions.
Metadata updates affect existing rows only, so a late edit cannot recreate an item deleted in another session.
Ordinary metadata edits use last-write-wins; revision checks protect tracklist changes.

## D004 — Adapt generic infrastructure patterns

Generic development infrastructure patterns such as containerization, environment configuration and
test setup were adapted from the author's existing project tooling. Domain implementation was built
specifically for this assignment. No proprietary modules, business data or internal documents are included.

## D005 — A tracklist is saved as a transaction

The editor sends the complete order with the revision it loaded. The API locks the album, rejects a stale
revision and saves the order atomically. Keyboard controls provide the same operation as dragging.
Explicit placements may have gaps; saving a reordered list normalizes positions to 1…N.

## D006 — Frontend dependencies follow demonstrated state needs

Vue 3's Composition API keeps server snapshots in their route pages and the unsaved track order inside
the editor that owns it. Components communicate through typed props and events; the API returns the new
snapshot after every successful mutation. There is no shared draft across routes, so a Pinia store would
add cache lifetime and reset rules without removing existing state. Quasar and Tailwind were also considered,
but the current focused stylesheet already provides the required responsive, accessible interface.
They should be introduced when a larger component system or shared client state creates a concrete need.

## Scope trade-offs

The demo API is intentionally unauthenticated and exposed on loopback only. Authentication and public
deployment hardening belong to a separate scope. Album artwork is generated with CSS; no external API,
image service or asset credentials are needed. A small app does not need a global state store.
