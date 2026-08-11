import psycopg


def test_import_creates_valid_geometry(loaded_parcels):
    with psycopg.connect(loaded_parcels) as conn:
        rows = conn.execute(
            "SELECT source_key, geometry_status, ST_IsValid(geom), derived_area_m2 "
            "FROM parcels ORDER BY source_key"
        ).fetchall()
    assert [r[0] for r in rows] == ["test:001", "test:002"]
    assert all(r[2] for r in rows)
    assert rows[0][1] == "derived"
    assert rows[1][1] == "official"
    assert all(r[3] > 0 for r in rows)


def test_import_upserts_instead_of_duplicating(loaded_parcels, run_import):
    run_import()
    with psycopg.connect(loaded_parcels) as conn:
        count = conn.execute("SELECT count(*) FROM parcels").fetchone()[0]
    assert count == 2
