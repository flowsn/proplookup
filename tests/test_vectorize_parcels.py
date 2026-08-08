"""Synthetic-raster test for the raster polygonization experiment.

Builds a small georeferenced GeoTIFF that mimics the Bavaria black-outline
Parzellarkarte layer (a grid of black lines enclosing white cells) so the
vectorization logic can be exercised without network access to the real WMS.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from etl.vectorize_parcels import vectorize

GRID_SIZE = 4
CELL_PX = 50
LINE_PX = 2
MARGIN_PX = 20
PIXEL_SIZE_M = 1.0
CELL_AREA_M2 = CELL_PX * CELL_PX * PIXEL_SIZE_M**2


@pytest.fixture
def synthetic_parzellarkarte(tmp_path: Path) -> Path:
    grid_extent = LINE_PX * (GRID_SIZE + 1) + GRID_SIZE * CELL_PX
    size = MARGIN_PX * 2 + grid_extent

    arr = np.full((size, size), 255, dtype=np.uint8)
    for k in range(GRID_SIZE + 1):
        offset = MARGIN_PX + k * (CELL_PX + LINE_PX)
        arr[MARGIN_PX:MARGIN_PX + grid_extent, offset:offset + LINE_PX] = 0
        arr[offset:offset + LINE_PX, MARGIN_PX:MARGIN_PX + grid_extent] = 0

    transform = from_origin(691800, 5336550, PIXEL_SIZE_M, PIXEL_SIZE_M)
    out = tmp_path / "synthetic_parzellarkarte.tif"
    with rasterio.open(
        out, "w", driver="GTiff", height=size, width=size, count=1,
        dtype="uint8", crs="EPSG:25832", transform=transform,
    ) as dst:
        dst.write(arr, 1)
    return out


def test_vectorize_recovers_grid_cells(synthetic_parzellarkarte: Path, tmp_path: Path):
    out_path = tmp_path / "parcels.geojson"
    count = vectorize(
        synthetic_parzellarkarte, out_path,
        threshold=120, min_pixels=8, min_area_m2=40, max_area_m2=10000, close_radius=1,
    )
    assert count == GRID_SIZE * GRID_SIZE

    gdf = gpd.read_file(out_path)
    assert len(gdf) == GRID_SIZE * GRID_SIZE
    assert (gdf["geometry_status"] == "derived").all()
    assert (gdf["geometry_confidence"] == 0.30).all()
    assert gdf["source_key"].str.startswith("raster-derived:").all()
    assert gdf.geometry.is_valid.all()

    # Skeletonizing the outline shrinks it to ~1px, so recovered cells are
    # close to but not exactly the drawn 2500 m^2 interior.
    areas = gdf.geometry.area
    assert (areas > CELL_AREA_M2 * 0.8).all()
    assert (areas < CELL_AREA_M2 * 1.2).all()


def test_vectorize_drops_background_touching_edges(synthetic_parzellarkarte: Path, tmp_path: Path):
    out_path = tmp_path / "parcels.geojson"
    vectorize(
        synthetic_parzellarkarte, out_path,
        threshold=120, min_pixels=8, min_area_m2=40, max_area_m2=10000, close_radius=1,
    )
    gdf = gpd.read_file(out_path)
    # The margin/background region is far larger than any grid cell; if it
    # leaked through the edge-touch filter it would dominate max area.
    assert gdf.geometry.area.max() < CELL_AREA_M2 * 1.2
