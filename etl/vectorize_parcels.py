#!/usr/bin/env python3
"""Experimental ALKIS raster -> candidate parcel polygons.

Designed for Bavaria's free Parzellarkarte WMS/GeoTIFF. Output is explicitly
DERIVED geometry and must not be represented as official cadastral geometry.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import shapes
from scipy import ndimage
from shapely.geometry import shape
from shapely.validation import make_valid
from skimage.morphology import binary_closing, disk, remove_small_objects, skeletonize


def read_gray(src: rasterio.DatasetReader) -> np.ndarray:
    arr = src.read()
    if arr.shape[0] == 1:
        return arr[0].astype(np.float32)
    rgb = arr[:3].astype(np.float32)
    # Perceptual luminance; robust for grayscale and black-outline layers.
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def vectorize(src_path: Path, out_path: Path, threshold: int, min_pixels: int,
              min_area_m2: float, max_area_m2: float, close_radius: int) -> int:
    with rasterio.open(src_path) as src:
        gray = read_gray(src)
        transform = src.transform
        crs = src.crs
        bounds = src.bounds

    dark = gray < threshold
    dark = remove_small_objects(dark, min_size=min_pixels)
    if close_radius > 0:
        dark = binary_closing(dark, footprint=disk(close_radius))
    lines = skeletonize(dark)

    # Invert linework and label enclosed connected regions.
    open_space = ~lines
    labels, _ = ndimage.label(open_space)

    geoms = []
    for geom_json, value in shapes(labels.astype("int32"), mask=labels > 0, transform=transform):
        geom = make_valid(shape(geom_json))
        if geom.is_empty:
            continue
        # Dump edge/background region(s) touching image bounds.
        minx, miny, maxx, maxy = geom.bounds
        eps = max(abs(transform.a), abs(transform.e)) * 2
        touches_edge = (
            minx <= bounds.left + eps or miny <= bounds.bottom + eps or
            maxx >= bounds.right - eps or maxy >= bounds.top - eps
        )
        if touches_edge:
            continue
        area = geom.area
        if area < min_area_m2 or area > max_area_m2:
            continue
        geoms.append(geom)

    gdf = gpd.GeoDataFrame(
        {
            "source_key": [f"raster-derived:{i}" for i in range(len(geoms))],
            "geometry_status": ["derived"] * len(geoms),
            "geometry_confidence": [0.30] * len(geoms),
            "area_m2_est": [g.area for g in geoms],
        }, geometry=geoms, crs=crs,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_path, driver="GeoJSON")
    print(f"Wrote {len(gdf)} candidate polygons to {out_path}")
    return len(gdf)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--threshold", type=int, default=120)
    p.add_argument("--min-pixels", type=int, default=8)
    p.add_argument("--min-area-m2", type=float, default=40)
    p.add_argument("--max-area-m2", type=float, default=10000)
    p.add_argument("--close-radius", type=int, default=1)
    args = p.parse_args()
    vectorize(args.input, args.output, args.threshold, args.min_pixels,
              args.min_area_m2, args.max_area_m2, args.close_radius)


if __name__ == "__main__":
    main()
