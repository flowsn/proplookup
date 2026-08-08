CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE data_origin AS ENUM ('official', 'derived', 'manual');
CREATE TYPE geometry_status AS ENUM ('official', 'derived', 'unknown');
CREATE TYPE owner_status AS ENUM ('unknown', 'suspected', 'contacted', 'self_identified', 'verified');
CREATE TYPE pipeline_status AS ENUM ('new', 'researching', 'target', 'contacted', 'responded', 'negotiating', 'due_diligence', 'passed', 'acquired');

CREATE TABLE IF NOT EXISTS parcels (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_key text,
    flurstueckskennzeichen text,
    gemarkung text,
    official_area_m2 numeric,
    derived_area_m2 numeric,
    address_text text,
    geometry_status geometry_status NOT NULL DEFAULT 'unknown',
    geometry_confidence numeric CHECK (geometry_confidence IS NULL OR geometry_confidence BETWEEN 0 AND 1),
    geom geometry(MultiPolygon, 4326) NOT NULL,
    acquisition_score numeric CHECK (acquisition_score IS NULL OR acquisition_score BETWEEN 0 AND 100),
    pipeline_status pipeline_status NOT NULL DEFAULT 'new',
    owner_status owner_status NOT NULL DEFAULT 'unknown',
    notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(source_key)
);

CREATE INDEX IF NOT EXISTS parcels_geom_gix ON parcels USING gist (geom);
CREATE INDEX IF NOT EXISTS parcels_score_idx ON parcels (acquisition_score DESC);
CREATE INDEX IF NOT EXISTS parcels_pipeline_idx ON parcels (pipeline_status);

CREATE TABLE IF NOT EXISTS buildings (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_key text UNIQUE,
    address_text text,
    footprint_m2 numeric,
    height_m numeric,
    floors_estimated numeric,
    gfa_estimated_m2 numeric,
    roof_type text,
    mfh_probability numeric CHECK (mfh_probability IS NULL OR mfh_probability BETWEEN 0 AND 1),
    geom geometry(MultiPolygon, 4326) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS buildings_geom_gix ON buildings USING gist (geom);

CREATE TABLE IF NOT EXISTS parcel_buildings (
    parcel_id uuid NOT NULL REFERENCES parcels(id) ON DELETE CASCADE,
    building_id uuid NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    overlap_ratio numeric,
    PRIMARY KEY (parcel_id, building_id)
);

CREATE TABLE IF NOT EXISTS owners (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    owner_type text,
    company_number text,
    contact_address text,
    status owner_status NOT NULL DEFAULT 'suspected',
    confidence numeric CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS parcel_owner_links (
    parcel_id uuid NOT NULL REFERENCES parcels(id) ON DELETE CASCADE,
    owner_id uuid NOT NULL REFERENCES owners(id) ON DELETE CASCADE,
    source_note text,
    verified_at timestamptz,
    PRIMARY KEY (parcel_id, owner_id)
);

CREATE TABLE IF NOT EXISTS outreach (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parcel_id uuid NOT NULL REFERENCES parcels(id) ON DELETE CASCADE,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    channel text,
    recipient text,
    result text,
    asking_price_eur numeric,
    next_follow_up date,
    notes text
);

CREATE INDEX IF NOT EXISTS outreach_parcel_idx ON outreach(parcel_id, occurred_at DESC);

CREATE TABLE IF NOT EXISTS data_provenance (
    id bigserial PRIMARY KEY,
    parcel_id uuid REFERENCES parcels(id) ON DELETE CASCADE,
    building_id uuid REFERENCES buildings(id) ON DELETE CASCADE,
    field_name text NOT NULL,
    origin data_origin NOT NULL,
    source_name text,
    source_url text,
    source_feature_id text,
    retrieved_at timestamptz,
    calculation_method text,
    confidence numeric CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1),
    CHECK (parcel_id IS NOT NULL OR building_id IS NOT NULL)
);

CREATE OR REPLACE VIEW parcel_summary AS
SELECT
    p.id,
    p.address_text,
    p.official_area_m2,
    p.derived_area_m2,
    p.geometry_status,
    p.geometry_confidence,
    p.acquisition_score,
    p.pipeline_status,
    p.owner_status,
    COUNT(pb.building_id)::int AS building_count,
    COALESCE(SUM(b.footprint_m2), 0) AS building_footprint_m2,
    COALESCE(SUM(b.gfa_estimated_m2), 0) AS gfa_estimated_m2
FROM parcels p
LEFT JOIN parcel_buildings pb ON pb.parcel_id = p.id
LEFT JOIN buildings b ON b.id = pb.building_id
GROUP BY p.id;
