# Architecture

## Design principle

Parcel is the primary acquisition object. Buildings are spatially joined to parcels.

```text
Official/derived GIS files
        |
        v
Local Python ETL (GeoPandas/Rasterio/Shapely)
        |
        v
PostgreSQL + PostGIS
        |
        +---- lightweight Python CGI API
        |             |
        |             v
        +--------> static MapLibre UI
```

## Why this fits Hetzner shared hosting

The browser and database do most runtime work. CPU-heavy image processing happens locally and uploads normalized geometry/results.

Production request flow:

1. Browser requests map extent.
2. CGI receives `bbox` and filters parcels via PostGIS.
3. API returns GeoJSON.
4. MapLibre renders parcels.
5. User clicks polygon.
6. Browser requests parcel detail by UUID.
7. API returns parcel/building/acquisition metadata.

## Scaling

For hundreds or a few thousand candidate parcels, GeoJSON by viewport is sufficient.

If the database later contains all Munich parcels and performance becomes poor, upgrade in this order:

1. geometry simplification by zoom
2. server-side bbox limits
3. materialized acquisition views
4. vector tiles (Martin/pg_tileserv) on a VPS

Do not start with vector-tile infrastructure.

## Data provenance

Every value should be one of:

- `official`: directly supplied by an official dataset
- `derived`: calculated from official/open geometry or raster
- `manual`: entered by the user

For derived parcels, never label geometry as official cadastral geometry.
