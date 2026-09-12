# Verification record

Executed on 2026-09-12, Windows host with Docker Desktop Linux containers.
These are local execution results, not a claim of external human review or public production readiness.

Implementation commit: `0e604d434690a159fc0ce8370b881d8ffaac733c`.
The subsequent evidence commit changes documentation and receipts only.

## Fresh-clone acceptance

A separate Git clone was built with `docker compose build --no-cache` (exit 0), then started under
its own Compose project with a newly created PostgreSQL volume. Only `.env.example` was copied;
the frontend port was changed to 5174 to coexist with the original instance. No virtual environment,
`node_modules`, database contents or local application files were copied into the clone.

`python scripts/verify.py http://127.0.0.1:5174` completed all eight checks with exit 0.
`python scripts/browser_smoke.py http://127.0.0.1:5174` also exited 0 against the new database.
The no-cache image build repeated 17 frontend tests, lint, typecheck and bundling; the fresh database
run repeated all 87 backend tests. This closes the mandatory local submission gates.

Receipts: [cold-start commands and exits](evidence/cold-start.json),
[backend test output](evidence/backend-tests.txt), [frontend build output](evidence/frontend-build.txt),
[browser result](evidence/browser-smoke.txt). The [shared-song screenshot](images/song-appearances.png)
shows the seeded appearance at positions 2 and 7; automated tests establish the underlying identity.

## Executed checks

| Command | Exit | Observed result |
| --- | ---: | --- |
| `docker compose config --quiet` | 0 | Valid configuration |
| `docker compose up --build -d --wait --wait-timeout 180` | 0 | PostgreSQL, backend and frontend healthy |
| `docker compose exec -T backend python manage.py check` | 0 | No issues |
| `docker compose exec -T backend python manage.py makemigrations --check --dry-run` | 0 | No changes detected |
| `docker compose exec -T backend pytest` | 0 | 87 passed, including 3 concurrency tests |
| `docker compose exec -T backend ruff check .` | 0 | All checks passed |
| `docker compose exec -T backend ruff format --check .` | 0 | 26 files formatted |
| `docker compose exec -T backend python -m pip check` | 0 | No broken requirements |
| `npm ci` in frontend | 0 | Lockfile reproduced |
| `npm run lint` in frontend | 0 | No warnings |
| `npm run test` in frontend | 0 | 17 passed across 5 files |
| `npm run build` in frontend | 0 | Vue typecheck and Vite production bundle |
| `npm run format:check` in frontend | 0 | Prettier clean |
| `npm audit --omit=dev` in frontend | 0 | No reported runtime dependency vulnerabilities at execution time |
| `python scripts/verify.py http://127.0.0.1:5174` | 0 | All eight checks passed in the fresh clone |
| `python scripts/browser_smoke.py` | 0 | Critical browser flows, desktop/mobile layout, Admin assets; no page errors |

The Docker frontend build repeats lint, unit tests and the production build with pinned Node 22.23.2.
Raw output is retained locally under `.local/`; `scripts/verify.py` regenerates machine-readable exits
and individual logs. CI uploads its execution logs and browser screenshots as artifacts.

## Domain and failure evidence

- The central database/API test creates one Song and places it at track 2 and track 7 on different albums.
- PostgreSQL rejects duplicate album positions, duplicate song placements and invalid numbers.
- A high-number track is reordered without temporary-position overflow.
- An injected failure after position updates rolls the complete transaction back.
- Separate simultaneous PostgreSQL connections exercise competing reorders, duplicate additions and safe appends.
- A causal mutation temporarily removed the revision comparison in memory. The stale-reorder regression failed
  with 200 instead of 409 (exit 1, one failed). Unmodified code passed the same test (exit 0, one passed).
  No source file was changed for that experiment.
- Browser tests exercise creating/editing artists, albums and songs, shared-song appearances, duplicate feedback,
  keyboard/pointer reorder, unsaved navigation, stale conflicts, persistence and placement removal.
- A browser-injected GET failure after successful deletion verifies that edits lock until the refreshed list loads.
- Frontend regression tests cover failed pagination retry, conflict recovery and preserving related data after PATCH.

## Requirements matrix

| Requirement | Status | Evidence |
| --- | --- | --- |
| Django / DRF / PostgreSQL | PASS | Settings, pinned lock, running containers and PostgreSQL tests |
| Vue 3 Composition API / Vite | PASS | Typed Vue components, frontend build |
| Artist / Album / Song / explicit AlbumTrack | PASS | Models, initial migration, central identity regression |
| Positive and unique per-album numbers | PASS | Database constraint tests |
| No duplicate Song placement in one Album | PASS | Database and concurrent-add tests |
| Referential integrity and safe removal | PASS | PROTECT/CASCADE tests, browser placement removal |
| Artist / Album / Song CRUD | PASS | API suite and browser create/edit flows |
| Album tracks add / remove / reorder | PASS | API, transaction and browser tests |
| Ordered detail / search / filters / pagination | PASS | Stable-order and query-budget regressions; browser search |
| Validation / errors / invalid IDs / 404 | PASS | API negative cases, strict JSON fields |
| Atomic reorder and conflict protection | PASS | Concurrent tests, rollback test and causal mutation |
| Smart editor: drag, keyboard, existing/new songs | PASS | Browser flow and component tests |
| Song Appears on | PASS | Central API test and browser positions 2/7 |
| Demo seed | PASS | Idempotence test; 3 artists, 4 albums, 12 songs, 17 placements |
| Django Admin | PASS | Model registration, read-only placements, login/static browser check |
| Environment and startup hygiene | PASS | Required env, loopback exposure, health dependencies, non-root backend |
| Dependency pins / lint / format / typecheck | PASS | Locks, Ruff, ESLint, Prettier, vue-tsc |
| Responsive / labelled / loading / empty / recovery UI | PASS | Browser layout checks and focused component regressions |
| SPEC / decisions / README / reproducible evidence | PASS | Repository documents and verification scripts |
| Independent review of implementation staged subject | PASS | Non-author reviewer ACCEPT; independently reran 85 model/API/concurrency tests |
| Fresh-clone startup with a new database volume | PASS | No-cache build, all eight verification checks and real browser smoke |

## Review record

The implementation received an accountable architect decision and a separate non-author adversarial
AI-agent review on staged patch `98868a7028d9a9b1035ee88d2ad82d7199ce65fa` before commit.
The reviewer independently checked the domain, concurrent writes, API edges, UI recovery, Docker setup,
source boundaries and observed evidence, and ran 85 model/API/concurrency tests (exit 0).
All confirmed findings were addressed before acceptance. The review is not a human third-party audit.

## Boundaries

The demo API has no authentication and is intended for loopback development. Django Admin requires a
staff account created by the reviewer. Browser acceptance covers Chromium; other browser engines are
not claimed. Hosted GitHub Actions execution is not claimed until this repository is pushed and CI runs.
No external services, music providers or proprietary project modules are included.
