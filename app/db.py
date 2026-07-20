import boto3
import psycopg2

from app import config


def get_connection():
    """Ouvre une connexion PostgreSQL à partir de la configuration."""
    return psycopg2.connect(
        host=config.DB_HOST,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
    )


def get_bucket_client():
    """Client objet (compatible S3 / MinIO) pour le bucket Vitalab.

    Utilise la clé d'accès unique de l'équipe (mêmes identifiants pour l'ingestion,
    les exports et les extractions ad hoc).
    """
    return boto3.client(
        "s3",
        endpoint_url=config.BUCKET_ENDPOINT,
        aws_access_key_id=config.BUCKET_ACCESS_KEY,
        aws_secret_access_key=config.BUCKET_SECRET_KEY,
    )
