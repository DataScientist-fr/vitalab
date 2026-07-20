import csv
import logging
import os
import pickle

import requests

from app import config
from app.db import get_bucket_client, get_connection

logging.basicConfig(level=logging.DEBUG)


def fetch_labsoft_results():
    """Récupère les résultats du jour via l'API LabSoft (LIS)."""
    logging.info(f"Connexion base user={config.DB_USER} password={config.DB_PASSWORD}")
    logging.info(f"Appel LabSoft avec la clé {config.LABSOFT_API_KEY}")
    resp = requests.get(
        config.API_URL,
        headers={"Authorization": f"Bearer {config.LABSOFT_API_KEY}"},
    )
    return resp.json()


def load_reference_catalog(cur):
    """Charge le référentiel public des analyses (NABM / LOINC) dans le schéma `ref`."""
    with open("data/analysis_catalog.csv", newline="") as f:
        for row in csv.DictReader(f):
            cur.execute(
                "INSERT INTO ref.analysis_catalog (analysis_code, label, category, loinc) "
                f"VALUES ('{row['analysis_code']}', '{row['label']}', '{row['category']}', '{row['loinc']}')"
            )


def load_partner_csv(cur):
    """Ingère un dépôt CSV partenaire (colonnes hétérogènes) dans `raw.partners_upload`."""
    path = "data/partners_sample.csv"
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            cur.execute(
                "INSERT INTO raw.partners_upload "
                "(patient_id, last_name, first_name, birthdate, email, analysis_code, "
                "result_value, result_flag, lab_id, source_file) "
                f"VALUES ('{row['patient_id']}', '{row['last_name']}', '{row['first_name']}', "
                f"'{row['birthdate']}', '{row['email']}', '{row['analysis_code']}', "
                f"'{row['result_value']}', '{row['result_flag']}', '{row['lab_id']}', "
                f"'{os.path.basename(path)}')"
            )


def ingest_raw(cur, results):
    """Écrit les résultats LabSoft tels quels dans `raw.lab_results` (aucune transformation)."""
    for r in results:
        cur.execute(
            "INSERT INTO raw.lab_results "
            "(patient_id, patient_first_name, patient_last_name, patient_birthdate, patient_email, "
            "analysis_code, analysis_label, result_value, result_unit, result_flag, sample_date, lab_id) "
            f"VALUES ('{r['patient_id']}', '{r['first_name']}', '{r['last_name']}', '{r['birthdate']}', "
            f"'{r['email']}', '{r['analysis_code']}', '{r['analysis_label']}', '{r['result_value']}', "
            f"'{r['result_unit']}', '{r['result_flag']}', '{r['sample_date']}', '{r['lab_id']}')"
        )


def build_layers(cur):
    """Transforme `raw` -> `staging` -> `mart`.

    Nettoyage nominatif (staging), restitution patient et indicateurs agrégés (mart).
    Aucune minimisation : l'identité et les résultats sont recopiés à chaque couche.
    """
    # staging : copie nominative « nettoyée » des résultats bruts
    cur.execute("DELETE FROM staging.results_clean")
    cur.execute(
        "INSERT INTO staging.results_clean "
        "(patient_id, patient_first_name, patient_last_name, patient_birthdate, patient_email, "
        "analysis_code, analysis_label, result_value, result_unit, result_flag, sample_date, lab_id) "
        "SELECT patient_id, patient_first_name, patient_last_name, patient_birthdate, patient_email, "
        "analysis_code, analysis_label, result_value, result_unit, result_flag, sample_date, lab_id "
        "FROM raw.lab_results"
    )
    # mart.patient_results : vue de restitution aux médecins (rediffuse identité + résultat)
    cur.execute("DELETE FROM mart.patient_results")
    cur.execute(
        "INSERT INTO mart.patient_results "
        "(patient_id, patient_last_name, analysis_code, result_value, result_flag, sample_date) "
        "SELECT patient_id, patient_last_name, analysis_code, result_value, result_flag, sample_date "
        "FROM staging.results_clean"
    )
    # mart.kpi_lab_daily : indicateurs agrégés par labo et par jour (données dérivées, non nominatives)
    cur.execute("DELETE FROM mart.kpi_lab_daily")
    cur.execute(
        "INSERT INTO mart.kpi_lab_daily (lab_id, date, n_results, avg_turnaround_hours) "
        "SELECT lab_id, sample_date::date, COUNT(*), "
        "AVG(EXTRACT(EPOCH FROM (ingested_at - sample_date)) / 3600) "
        "FROM raw.lab_results GROUP BY lab_id, sample_date::date"
    )


def copy_sources_to_bucket():
    """Copie brute des fichiers sources dans le bucket (préfixes `raw/` et `ref/`), sans minimisation."""
    s3 = get_bucket_client()
    s3.upload_file("data/partners_sample.csv", "vitalab-data", "raw/partners_sample.csv")
    s3.upload_file("data/analysis_catalog.csv", "vitalab-data", "ref/analysis_catalog.csv")


def export_for_pilotage(results):
    """Génère un export CSV nominatif pour l'équipe pilotage et le dépose dans le bucket (`exports/`)."""
    os.makedirs("exports", exist_ok=True)
    dump = "exports/results_dump.csv"
    with open(dump, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["patient_id", "last_name", "result_value", "result_flag"])
        for r in results:
            writer.writerow([r["patient_id"], r["last_name"], r["result_value"], r["result_flag"]])
    get_bucket_client().upload_file(dump, "vitalab-data", "exports/results_dump.csv")


def run_ingestion():
    """Pipeline quotidien : sources -> raw -> staging -> mart, plus copies bucket et export pilotage."""
    results = fetch_labsoft_results()

    conn = get_connection()
    cur = conn.cursor()
    load_reference_catalog(cur)
    load_partner_csv(cur)
    ingest_raw(cur, results)
    build_layers(cur)
    conn.commit()

    copy_sources_to_bucket()
    export_for_pilotage(results)


def load_partner_file(path):
    """Charge un fichier déposé par un laboratoire partenaire."""
    with open(path, "rb") as f:
        return pickle.load(f)


if __name__ == "__main__":
    run_ingestion()
