import pytest

from app import api_core


def test_health_reports_postgis(loaded_parcels):
    result = api_core.health()
    assert result["ok"] is True
    assert "postgis" in result


def test_parcels_bbox_returns_feature_collection(loaded_parcels):
    fc = api_core.parcels_bbox("11.57,48.136,11.578,48.138")
    assert fc["type"] == "FeatureCollection"
    addresses = {f["properties"]["address_text"] for f in fc["features"]}
    assert addresses == {"Teststrasse 1, 80331 Munich", "Teststrasse 2, 80331 Munich"}


def test_parcels_bbox_excludes_out_of_range(loaded_parcels):
    fc = api_core.parcels_bbox("0,0,0.01,0.01")
    assert fc["features"] == []


def test_parcels_bbox_requires_four_values(loaded_parcels):
    with pytest.raises(ValueError):
        api_core.parcels_bbox("1,2,3")


def test_parcel_detail_returns_summary_fields(loaded_parcels):
    fc = api_core.parcels_bbox("11.57,48.136,11.578,48.138")
    parcel_id = fc["features"][0]["id"]
    detail = api_core.parcel_detail(parcel_id)
    assert detail["id"] == parcel_id
    assert detail["building_count"] == 0
    assert "map_area_m2" in detail


def test_parcel_detail_missing_id_returns_none(loaded_parcels):
    assert api_core.parcel_detail("00000000-0000-0000-0000-000000000000") is None
