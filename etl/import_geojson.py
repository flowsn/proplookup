#!/usr/bin/env python3
"""Import/upsert parcel GeoJSON into PostGIS.

Expected properties (all optional except source_key):
- source_key
- address_text
- geometry_status: official|derived|unknown
- geometry_confidence: 0..1
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import geopandas as gpd
import psycopg

UPSERT = """
INSERT INTO parcels (
    source_key, address_text, derived_area_m2, geometry_status,
    geometry_confidence, geom
)
VALUES (
    %(source_key)s, %(address_text)s, %(area)s, %(geometry_status)s,
    %(confidence)s,
    ST_Multi(ST_Transform(ST_SetSRID(ST_GeomFromWKB(%(geom_wkb)s), 25832), 4326))
)
ON CONFLICT (source_key) DO UPDATE SET
    address_text = EXCLUDED.address_text,
    derived_area_m2 = EXCLUDED.derived_area_m2,
    geometry_status = EXCLUDED.geometry_status,
    geometry_confidence = EXCLUDED.geometry_confidence,
    geom = EXCLUDED.geom,
    updated_at = now();
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("geojson", type=Path)
    args = parser.parse_args()

    db = os.environ["DATABASE_URL"]
    gdf = gpd.read_file(args.geojson)
    if gdf.crs is None:
        raise SystemExit("Input must declare a CRS")

    metric = gdf.to_crs(25832)
    with psycopg.connect(db) as conn:
        for idx, row in metric.iterrows():
            source_key = row.get("source_key") or f"derived:{idx}"
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
            if not geom.is_valid:
                geom = geom.buffer(0)
            conn.execute(
                UPSERT,
                {
                    "source_key": source_key,
                    "address_text": row.get("address_text"),
                    "area": float(geom.area),
                    "geometry_status": row.get("geometry_status") or "derived",
                    "confidence": float(row.get("geometry_confidence") or 0.5),
                    "geom_wkb": bytes(geom.wkb),
                },
            )
        conn.commit()


if __name__ == "__main__":
    main()
