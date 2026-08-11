# Data source plan

The source adapter names below are intentionally isolated from UI code.

## Priority 0

### Bavaria Hausumringe
Purpose: official/open building footprint polygons.

Use for:
- footprint area
- building-to-parcel assignment
- building count

### Bavaria LoD2
Purpose: 3D building geometry / descriptive attributes.

Use for:
- approximate height
- roof form
- storey/GFA proxies where defensible

### ALKIS Tatsächliche Nutzung
Purpose: land-use classification.

### Bavaria ALKIS Parzellarkarte (free raster/WMS)
Purpose: visual cadastral boundaries and experimental parcel reconstruction.

Important: derived polygons must be stored with `geometry_status='derived'`.

## Priority 1

### Bodenrichtwerte / VBORIS WMS
Use as display and GetFeatureInfo enrichment where technically/licensingly permitted.

### Munich Open Data CKAN
Catalog API root:

`https://opendata.muenchen.de/api/3/action/`

Use to discover planning/address/municipal datasets rather than hard-coding assumptions.

## Paid/restricted upgrade path

ALKIS simplified vector parcel data without owners is the preferred official parcel source if access/licensing becomes available.

The database schema is designed so derived geometry can later be replaced by official geometry while retaining the same internal parcel UUID and acquisition history.
