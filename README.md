# Munich MFH Scout

Private parcel-first acquisition intelligence tool for Munich multifamily properties.

## Goal

Build an NYC-property-portal-style map where a parcel can be clicked and enriched with:

- derived/cadastral parcel geometry
- building footprints and LoD2 attributes
- land use
- Bodenrichtwert/planning layers
- acquisition score
- owner research status
- outreach notes

## Deployment target

Primary target: Hetzner shared Webhosting with:

- static HTML/CSS/JS frontend
- Python CGI API
- PostgreSQL + PostGIS
- local/offline Python ETL for heavy GIS processing

Heavy raster/vector processing is intentionally **not** performed on shared hosting.

## First milestone

1. Take one Munich test-area cadastral GeoTIFF.
2. Derive candidate parcel polygons locally.
3. Load them into PostGIS.
4. Serve parcel GeoJSON through the Python API.
5. Display parcels in MapLibre.
6. Click a parcel to see area/building/acquisition fields.

## Repository layout

- `app/static/` browser UI
- `app/cgi-bin/` lightweight production Python API
- `etl/` local GIS processing
- `sql/` PostGIS schema
- `docs/` architecture, data-source and handoff notes
- `tests/` initial tests

## Local development

Python 3.11+ recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Run PostgreSQL/PostGIS using Docker:

```bash
docker compose up -d db
psql "$DATABASE_URL" -f sql/schema.sql
```

Start the local API:

```bash
python -m app.dev_server
```

Serve `app/static` with any static server, for example:

```bash
python -m http.server 8080 -d app/static
```

Then open `http://localhost:8080`.

## Production note

The production CGI entrypoint is `app/cgi-bin/api.py`. Configure its database credentials through environment variables or a server-side config file outside the public web root.

Do not put raw cadastral source files, database passwords, or ownership research exports in the public web directory.

## Real Bavaria parcel-raster proof of concept

The official public WMS exposes a black parcel-outline layer. Fetch a small Munich
extent into a georeferenced GeoTIFF, then vectorize it:

```bash
python etl/fetch_parzellarkarte.py data/raw/sample.tif \
  --bbox 691800 5336050 692300 5336550 --width 3000 --height 3000 \
  --layer black-outline

python etl/vectorize_parcels.py data/raw/sample.tif data/processed/parcels.geojson
```

The sample BBOX is a roughly 500 x 500 m central-Munich test extent in EPSG:25832.
All output polygons are *derived screening geometries*, not official cadastral
parcel geometries.
