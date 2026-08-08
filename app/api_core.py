from __future__ import annotations

import json
import os
from typing import Any

import psycopg
from psycopg.rows import dict_row


def _conn():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


def health() -> dict[str, Any]:
    with _conn() as conn:
        row = conn.execute("SELECT current_database() db, PostGIS_Version() postgis").fetchone()
    return {"ok": True, **row}


def parcels_bbox(bbox: str) -> dict[str, Any]:
    vals = [float(x) for x in bbox.split(",")]
    if len(vals) != 4:
        raise ValueError("bbox requires minLon,minLat,maxLon,maxLat")
    minx, miny, maxx, maxy = vals
    sql = """
        SELECT p.id::text, p.address_text, p.geometry_status::text,
               p.geometry_confidence, p.acquisition_score,
               p.pipeline_status::text, p.owner_status::text,
               ST_AsGeoJSON(p.geom)::json AS geometry
        FROM parcels p
        WHERE p.geom && ST_MakeEnvelope(%s,%s,%s,%s,4326)
        ORDER BY p.acquisition_score DESC NULLS LAST
        LIMIT 2500
    """
    with _conn() as conn:
        rows = conn.execute(sql, (minx, miny, maxx, maxy)).fetchall()
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": r["id"],
                "geometry": r.pop("geometry"),
                "properties": r,
            }
            for r in rows
        ],
    }


def parcel_detail(parcel_id: str) -> dict[str, Any] | None:
    sql = """
        SELECT ps.*, p.notes,
               COALESCE(ST_Area(p.geom::geography), 0) AS map_area_m2
        FROM parcel_summary ps
        JOIN parcels p ON p.id = ps.id
        WHERE ps.id = %s::uuid
    """
    with _conn() as conn:
        row = conn.execute(sql, (parcel_id,)).fetchone()
    if row is not None:
        row["id"] = str(row["id"])
    return row


def dumps(payload: Any) -> str:
    return json.dumps(payload, default=str, separators=(",", ":"))
