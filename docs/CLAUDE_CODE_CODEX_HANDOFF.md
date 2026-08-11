# Handoff brief for Claude Code / Codex

You are implementing a private parcel-first Munich multifamily acquisition map.

## Non-negotiable product behavior

- Map is the primary screen.
- Parcels are clickable.
- Parcel selection opens a side/detail panel.
- Building data is attached spatially to parcels.
- Official, derived and manual data must be visually distinguishable.
- Owner research is never represented as legally verified unless explicitly marked verified.

## Deployment constraints

Target is Hetzner shared Webhosting.

Production architecture must remain compatible with:
- static frontend
- Python CGI
- PostgreSQL/PostGIS

Heavy GIS packages/scripts run locally, not in CGI requests.

Do not introduce Docker as a production dependency. Docker is local-development only.

## First acceptance test

Given a GeoJSON file containing test parcels:

1. `etl/import_geojson.py` imports/upserts them to PostGIS.
2. `/parcels?bbox=minLon,minLat,maxLon,maxLat` returns a GeoJSON FeatureCollection.
3. MapLibre draws those polygons.
4. Clicking a polygon highlights it.
5. `/parcels/{id}` returns its detail.
6. Side panel displays area, geometry status, building count and acquisition status.

## Second acceptance test

Given a georeferenced cadastral raster for a small Munich test area:

1. parcel reconstruction produces candidate polygons,
2. invalid polygons are repaired where safe,
3. very small artifacts are discarded using configurable thresholds,
4. each derived polygon receives confidence/provenance metadata,
5. output can be visually compared over the source raster.

## Engineering rules

- Python 3.11+.
- Type hints for application/ETL functions.
- SQL queries parameterized.
- Keep API response contract independent of CGI implementation.
- Use EPSG:4326 for browser GeoJSON; preserve source CRS metadata in provenance.
- Prefer EPSG:25832 during Munich metric calculations.
- Never calculate area in EPSG:4326.
- ETL must be idempotent.
- Keep raw input immutable.
- Never scrape owner names into a field marked verified.

## Immediate tasks

1. Run schema locally.
2. Implement `etl/import_geojson.py` fully.
3. Implement local dev API and CGI parity.
4. Finish MapLibre parcel loading/click interactions.
5. Add synthetic fixture data and tests.
6. Implement raster polygonization experiment after the base UI works.
