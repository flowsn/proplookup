#!/usr/bin/env python3
"""Fetch a georeferenced ALKIS Parzellarkarte image from Bavaria's public WMS.

The WMS itself returns PNG/JPEG, not GeoTIFF. This script downloads the image and
writes a GeoTIFF using the requested BBOX and CRS, making it suitable for the
parcel-vectorization experiment.
"""
from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path

import numpy as np
import rasterio
import requests
from PIL import Image
from rasterio.transform import from_bounds

WMS_URL = "https://geoservices.bayern.de/od/wms/alkis/v1/parzellarkarte"
LAYERS = {
    "gray": "by_alkis_parzellarkarte_grau",
    "black-outline": "by_alkis_parzellarkarte_umr_schwarz",
    "color": "by_alkis_parzellarkarte_farbe",
}


def fetch(out: Path, bbox: tuple[float, float, float, float], width: int, height: int,
          crs: str, layer: str) -> None:
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "REQUEST": "GetMap",
        "LAYERS": LAYERS[layer],
        "STYLES": "",
        "SRS": crs,
        "BBOX": ",".join(map(str, bbox)),
        "WIDTH": str(width),
        "HEIGHT": str(height),
        "FORMAT": "image/png",
        "TRANSPARENT": "FALSE",
    }
    r = requests.get(WMS_URL, params=params, timeout=60)
    r.raise_for_status()
    ctype = r.headers.get("content-type", "")
    if "image" not in ctype:
        raise RuntimeError(f"WMS did not return an image: {ctype}\n{r.text[:500]}")

    img = Image.open(BytesIO(r.content)).convert("RGB")
    arr = np.asarray(img)
    transform = from_bounds(*bbox, width=width, height=height)

    out.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        out, "w", driver="GTiff", height=height, width=width, count=3,
        dtype=arr.dtype, crs=crs, transform=transform, compress="lzw"
    ) as dst:
        for band in range(3):
            dst.write(arr[:, :, band], band + 1)

    print(f"Wrote {out}")
    print(f"Request URL: {r.url}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("output", type=Path)
    p.add_argument("--bbox", nargs=4, type=float, required=True,
                   metavar=("MINX", "MINY", "MAXX", "MAXY"))
    p.add_argument("--width", type=int, default=3000)
    p.add_argument("--height", type=int, default=3000)
    p.add_argument("--crs", default="EPSG:25832")
    p.add_argument("--layer", choices=LAYERS, default="black-outline")
    args = p.parse_args()
    fetch(args.output, tuple(args.bbox), args.width, args.height, args.crs, args.layer)


if __name__ == "__main__":
    main()
