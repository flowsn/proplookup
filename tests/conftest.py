from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import psycopg
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXTURE_GEOJSON = Path(__file__).parent / "fixtures" / "sample_parcels.geojson"


@pytest.fixture(scope="session")
def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "postgresql://mfh:mfh@localhost:5432/mfh")
    try:
        with psycopg.connect(url, connect_timeout=2):
            pass
    except psycopg.OperationalError:
        pytest.skip("DATABASE_URL not reachable; run `docker compose up -d db` and load sql/schema.sql")
    os.environ["DATABASE_URL"] = url
    return url


@pytest.fixture
def run_import(database_url):
    def _run() -> None:
        subprocess.run(
            [sys.executable, str(ROOT / "etl" / "import_geojson.py"), str(FIXTURE_GEOJSON)],
            check=True,
            env=os.environ,
        )

    return _run


@pytest.fixture
def loaded_parcels(database_url, run_import) -> str:
    with psycopg.connect(database_url) as conn:
        conn.execute("TRUNCATE parcels CASCADE")
        conn.commit()
    run_import()
    return database_url
