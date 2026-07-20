-- Schéma Vitalab v0 (PostgreSQL).
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS mart;
CREATE SCHEMA IF NOT EXISTS ref;

-- Résultats d'analyses tels qu'ingérés (identité patient et résultats).
CREATE TABLE raw.lab_results (
    id                 BIGSERIAL PRIMARY KEY,
    patient_id         TEXT,
    patient_first_name TEXT,
    patient_last_name  TEXT,
    patient_birthdate  DATE,
    patient_email      TEXT,
    analysis_code      TEXT,
    analysis_label     TEXT,
    result_value       TEXT,
    result_unit        TEXT,
    result_flag        TEXT,       -- normal / anormal / critique
    sample_date        TIMESTAMP,
    lab_id             TEXT,
    ingested_at        TIMESTAMP DEFAULT now()
);

-- Dépôts CSV bruts des laboratoires partenaires (colonnes hétérogènes, avant nettoyage).
CREATE TABLE raw.partners_upload (
    id             BIGSERIAL PRIMARY KEY,
    patient_id     TEXT,
    last_name      TEXT,
    first_name     TEXT,
    birthdate      DATE,
    email          TEXT,
    analysis_code  TEXT,
    result_value   TEXT,
    result_flag    TEXT,
    lab_id         TEXT,
    source_file    TEXT,
    uploaded_at    TIMESTAMP DEFAULT now()
);

-- Référentiel des analyses (public).
CREATE TABLE ref.analysis_catalog (
    analysis_code TEXT PRIMARY KEY,
    label         TEXT,
    category      TEXT,
    loinc         TEXT
);

-- Résultats nettoyés / normalisés (raw -> staging), toujours nominatifs.
CREATE TABLE staging.results_clean (
    id                 BIGSERIAL PRIMARY KEY,
    patient_id         TEXT,
    patient_first_name TEXT,
    patient_last_name  TEXT,
    patient_birthdate  DATE,
    patient_email      TEXT,
    analysis_code      TEXT,
    analysis_label     TEXT,
    result_value       TEXT,
    result_unit        TEXT,
    result_flag        TEXT,
    sample_date        TIMESTAMP,
    lab_id             TEXT,
    cleaned_at         TIMESTAMP DEFAULT now()
);

-- Restitution : résultats par patient.
CREATE TABLE mart.patient_results (
    patient_id        TEXT,
    patient_last_name TEXT,
    analysis_code     TEXT,
    result_value      TEXT,
    result_flag       TEXT,
    sample_date       TIMESTAMP
);

-- Indicateurs agrégés par laboratoire et par jour.
CREATE TABLE mart.kpi_lab_daily (
    lab_id                TEXT,
    date                  DATE,
    n_results             INTEGER,
    avg_turnaround_hours  NUMERIC
);
