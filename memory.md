# Session memory

Running log of what's been done on munich-mfh-scout across sessions, so a new
session (human or agent) can pick up context fast. Append a new entry per
session instead of editing old ones. Newest entry on top.

Related: `AGENTS.md` (rules), `docs/CLAUDE_CODE_CODEX_HANDOFF.md` (product/eng
spec and the two acceptance tests).

---

## 2026-08-08

**Context:** Repo `flowsn/proplookup` previously held an unrelated NYC BBL
lookup tool. Replaced entirely with the munich-mfh-scout starter kit (user's
explicit choice) on branch `claude/new-session-7dhou5`. PR #3 open,
`claude/new-session-7dhou5` → `main`, not yet merged.

**Done:**
- Swapped repo contents: removed `app.py`/`paster.html`/`app.yaml`/
  `requirements.txt` (old NYC tool), added the munich-mfh-scout starter
  (`app/`, `etl/`, `sql/`, `docs/`, `tests/`).
- Verified handoff doc's **first acceptance test** end-to-end locally:
  - Installed PostGIS + started Postgres directly (no Docker daemon in this
    sandbox — `docker compose up -d db` will work on a normal machine, used
    `sudo apt-get install postgresql-16-postgis-3` here instead).
  - Loaded `sql/schema.sql` into a local `mfh` db.
  - Built a synthetic 2-parcel fixture (`tests/fixtures/sample_parcels.geojson`,
    two ~500m² polygons near Munich center) and ran it through
    `etl/import_geojson.py` — confirmed valid geometry and idempotent upsert
    (re-running doesn't duplicate rows).
  - Ran `app/dev_server.py` (Flask) and `app/cgi-bin/api.py` (CGI) side by
    side against the same DB — confirmed identical JSON contract for
    `/health`, `/parcels?bbox=...`, `/parcels/{id}`.
- **Bug found + fixed:** `api_core.parcel_detail()` returned `id` as a Python
  `UUID` object while `api_core.parcels_bbox()` returned it as `str` (the
  bbox SQL casts `p.id::text`, the `parcel_summary` view doesn't). Harmless
  on the wire (Flask's default JSON encoder stringifies UUIDs) but an
  inconsistent contract at the Python level — a test caught it. Fixed by
  casting in `parcel_detail()`.
- Replaced `tests/test_placeholder.py` with 12 real tests: `test_import_geojson.py`,
  `test_api_core.py`, `test_cgi_parity.py`. All passing against local PostGIS.
  Tests skip cleanly if `DATABASE_URL` isn't reachable (see `tests/conftest.py`).
- Added `.gitignore` (`.venv/`, `__pycache__/`, `data/raw|processed/*`, `.env`)
  and `.gitkeep` placeholders for `data/raw/` and `data/processed/` (repo had
  no `.gitignore` before).
- Opened PR #3 for the branch, no PR template existed in the repo.

**Not done / blocked:**
- **MapLibre frontend unverified in a real browser.** `app/static/index.html`
  loads maplibre-gl JS/CSS from `unpkg.com` and basemap tiles from
  `tile.openstreetmap.org`. This sandbox's outbound network policy blocks
  `unpkg.com` (403 on CONNECT, confirmed via the proxy status log) — not an
  app bug, just can't be screenshotted from here. Should work fine in a
  normal browser or on the Hetzner deploy target. Open question sent to user:
  vendor maplibre-gl locally so it also works offline / in restricted
  networks? **Not yet answered.**
- **Second acceptance test (raster → parcel polygonization) not attempted.**
  `etl/fetch_parzellarkarte.py` hits Bavaria's real WMS
  (`geoservices.bayern.de`) — also blocked by this sandbox's network policy
  (confirmed 403). Can't run the real fetch here. Next useful step: fabricate
  a small synthetic GeoTIFF (grid of black outlines, mimicking the real
  Parzellarkarte black-outline layer) and run it through
  `etl/vectorize_parcels.py` to prove the polygonization logic itself, since
  that part needs no network. The real WMS fetch needs to be run by the user
  on a machine with normal internet access.
- **GitHub repo is still named `proplookup`.** The GitHub App integration in
  this session can't create or rename repos (403, "Resource not accessible
  by integration") — tried `create_repository`, no rename tool exists either.
  User needs to rename manually: repo Settings → Repository name →
  `munich-mfh-scout`. User said they'll do this later.

**Environment notes for future sessions:**
- No Docker daemon available in this sandbox; use local Postgres + the
  `postgresql-16-postgis-3` apt package instead of `docker-compose.yml` for
  local testing here. `sudo apt-get update` first — the mirror 404s on some
  packages otherwise (unrelated PPA signing issues can be ignored).
- Outbound network is proxied and allowlisted; arbitrary external hosts
  (`unpkg.com`, `geoservices.bayern.de`) are blocked. `pypi.org` and
  `registry.npmjs.org` work fine for installing dependencies.
- Local Postgres in this sandbox: `postgresql://mfh:mfh@localhost:5432/mfh`,
  role `mfh` has `CREATEDB`, schema already applied there as of this session.
