import json
import os
import subprocess
import sys
from pathlib import Path

from app import api_core

CGI_SCRIPT = Path(__file__).resolve().parent.parent / "app" / "cgi-bin" / "api.py"


def _run_cgi(path_info: str, query_string: str = "") -> subprocess.CompletedProcess:
    env = {**os.environ, "PATH_INFO": path_info, "QUERY_STRING": query_string}
    return subprocess.run(
        [sys.executable, str(CGI_SCRIPT)], check=True, capture_output=True, text=True, env=env
    )


def test_cgi_parcels_matches_api_core(loaded_parcels):
    bbox = "11.57,48.136,11.578,48.138"
    result = _run_cgi("/parcels", f"bbox={bbox}")
    header, _, body = result.stdout.partition("\n\n")
    assert header.startswith("Status: 200")

    cgi_ids = {f["id"] for f in json.loads(body)["features"]}
    direct_ids = {f["id"] for f in api_core.parcels_bbox(bbox)["features"]}
    assert cgi_ids == direct_ids


def test_cgi_health(loaded_parcels):
    result = _run_cgi("/health")
    header, _, body = result.stdout.partition("\n\n")
    assert header.startswith("Status: 200")
    assert json.loads(body)["ok"] is True


def test_cgi_missing_bbox_returns_400(loaded_parcels):
    result = _run_cgi("/parcels")
    assert result.stdout.startswith("Status: 400")


def test_cgi_unknown_route_returns_404(loaded_parcels):
    result = _run_cgi("/nope")
    assert result.stdout.startswith("Status: 404")
