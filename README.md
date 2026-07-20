# Vitalab — plateforme data (v0)

> ⚠️ **Projet volontairement vulnérable, à des fins pédagogiques (module CYB01 — Sécurité dès la Conception).**
> Il contient de nombreux défauts de sécurité **intentionnels** et des secrets **fictifs**.
> **Ne jamais déployer ce code, ni réutiliser ces valeurs.** Objectif : l'auditer et le corriger.

*Vitalab* est un réseau **fictif** de laboratoires d'analyses médicales. Cette petite plateforme
data ingère les résultats d'analyses (API du logiciel de laboratoire + CSV de partenaires),
les stocke (PostgreSQL en couches + bucket objet) et les expose (API interne + dashboard).

## Architecture

```text
Sources                 Ingestion            Stockage                     Exposition
API LabSoft ─┐                               PostgreSQL                   results_api.py
CSV partenaires ├─▶ app/ingest.py ─▶  raw ─▶ staging ─▶ mart      ─┬─▶  /patient · /kpi · /dashboard
Référentiel  ─┘   (compte svc-pipeline)      + bucket objet         └─▶  Dashboard BI (externe)
                                             (raw/ partners/ exports/)
```

Le pipeline écrit les données brutes dans `raw`, les recopie « nettoyées » dans `staging`, puis
alimente `mart` (restitution patient + indicateurs agrégés). Les mêmes résultats nominatifs se
retrouvent donc dans plusieurs couches, plus le bucket, plus des exports CSV et des notebooks.

## Contenu

| Chemin | Rôle |
| --- | --- |
| `app/config.py` | configuration et accès (secrets, base, bucket) |
| `app/db.py` | connexion à la base + client du bucket objet |
| `app/ingest.py` | ingestion et transformation `raw → staging → mart` (API, CSV partenaires, référentiel, copies bucket, export pilotage) |
| `app/results_api.py` | API interne d'exposition (Flask) : `/patient`, `/kpi`, `/dashboard`, `/report` |
| `sql/schema.sql` | schéma PostgreSQL (`raw` / `staging` / `mart` / `ref`) |
| `notebooks/analyse_adhoc.ipynb` | analyse ad hoc de l'analyste (extraction nominative + exports) |
| `data/` | jeux de données **fictifs** (référentiel public, dépôt partenaire) |
| `infra/` | infrastructure : `docker-compose`, `bucket-policy.json`, `main.tf`, `dashboard/datasource.yml` |

## Accès externes (documentés, hors code exécutable ici)

Certains usages se font depuis des outils extérieurs mais s'appuient sur les mêmes accès :

- **Analystes → bucket objet.** Pour récupérer et déposer les exports (`exports/`), les analystes
  se connectent au bucket avec les **clés d'accès partagées de l'équipe** (`BUCKET_ACCESS_KEY` /
  `BUCKET_SECRET_KEY` de `app/config.py`), via un client S3/MinIO ou `mc`. La même clé donne accès à
  **tout** le bucket (préfixes `raw/`, `partners/`, `exports/`). Voir `notebooks/analyse_adhoc.ipynb`.
- **Dashboard BI → schéma `mart`.** L'outil BI est branché directement sur `mart` via
  `infra/dashboard/datasource.yml` : identifiants partagés, **sans filtrage par profil** — pilotage et
  médecins voient les mêmes données, dont les résultats nominatifs de tous les patients.

## Lancer (indicatif)

```bash
pip install -r requirements.txt
docker compose -f infra/docker-compose.yml up   # postgres + minio + api
python -m app.ingest
```

## Votre mission (fil rouge du module)

Auditer ce projet sous l'angle sécurité, corriger ses défauts, puis en proposer une reconception
« secure by design ». Les activités du cours vous guident chapitre par chapitre.
