# Sola History - Architecture Overview

This document describes the **overall system architecture** for the Sola History application, including repository layout, data governance, CI/CD, deployment model, infrastructure on OCI, and security considerations.

## Goals

Sola History aims to provide:

- A lightweight internal web application for planning & analyzing SOLA race data
- Separation of **application code** and **personal data**
- Automated ETL → JSON generation → deployment
- A private, secure deployment on OCI with minimal operational overhead
- A stateless application container pulling data at startup from Object Storage

## High-Level Architecture

```text
 ┌───────────────────────────────┐
 │       GitHub (App Repo)       │
 │  sola-history-app             │
 │  - Streamlit App              │
 │  - Dockerfile                 │
 │  - CI/CD → Build Container    │
 └───────────────┬───────────────┘
                 │ pushes image
                 ▼
        Container Registry (GHCR)
                 │
                 │ pull on deploy
                 ▼
      ┌────────────────────────────┐
      │        OCI Compute         │
      │  docker-compose with:      │
      │  - Nginx Reverse Proxy     │
      │  - Streamlit App           │
      │  - Certbot (Let's Encrypt) │
      └───────────────┬────────────┘
                      │ pulls data
                      ▼
            OCI Object Storage
           Bucket: sola-history-data
           - runners.json
           - races.json
           - teams.json
           - legs.json
           - results.json
           - metadata.json
                      ▲
                      │ uploads via CI
 ┌────────────────────┴────────────────────┐
 │    GitHub (Data Repo)                   │
 │    sola-history-data                     │
 │  - import_excel.py                       │
 │  - fetch_data.py                         │
 │  - upload_data_to_oci.sh                 │
 │  - schemas/                              │
 │  CI/CD → Validate → Upload → Snapshot    │
 └──────────────────────────────────────────┘
```

## Repository Structure

### Application Repository: `sola-history-app`

```text
sola-history-app/
├── app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.example.yml
├── tools/
│   ├── fetch_data.py
│   └── validate_schema.py
└── doc/
    └── architecture.md
```

**Contains:**

- Streamlit application
- Planning logic
- Admin overrides system
- Charts & data visualisation
- Multi-language UI (EN/DE)
- Dockerfile & GH Actions

**Does NOT contain:**

- Personal data
- Runner lists
- Race results

### Data Repository: `sola-history-data`

```text
sola-history-data/
├── data/
│   ├── raw/
│   │   ├── sola_history.xlsx
│   │   └── sola_contacts.xlsx
│   └── processed/
│       ├── runners.json
│       ├── races.json
│       ├── legs.json
│       ├── teams.json
│       └── results.json
├── tools/
│   ├── import_excel.py
│   ├── upload_data_to_oci.sh
│   └── oci_config/
└── schemas/
    └── *.schema.json
```

**Contains:**

- Raw Excel data (local only, not committed)
- All transformation scripts
- JSON schema validation
- Upload tools for OCI Object Storage

**Does NOT contain:**

- The application
- Any deployment code

## Data Pipeline

### Steps (Local or CI)

1. User updates Excel files:

   - `sola_history.xlsx`
   - `sola_contacts.xlsx`

2. Run importer:

```bash
python tools/import_excel.py
```

3. Validate JSON layout against schema:

```bash
python tools/validate_schema.py
```

4. Upload processed data to OCI Object Storage:

```bash
tools/upload_data_to_oci.sh processed/ <bucket>
```

### Data Storage Model

Bucket: **`sola-history-data`**
Objects:

```bash
current/runners.json
current/races.json
current/legs.json
current/teams.json
current/results.json
snapshots/2025-05-10/runners.json
snapshots/... 
```

The app loads **current/** on each start.

## Application Runtime Model

The Streamlit app is completely **stateless**.

### Startup Flow

1. App container starts

2. Loads settings from environment variables:

   - `SOLA_APP_PASSWORD`
   - `SOLA_DATA_BUCKET`
   - `SOLA_DATA_NAMESPACE`

3. Downloads JSON data from Object Storage

4. Applies overrides (`runners_overrides.json`)

5. Renders UI

No data is written back to the server except:

- Runner overrides (JSON file inside container volume)

## Deployment Architecture (OCI)

### Components

- **OCI Compute Instance**

  - Oracle Linux 8/9
  - Docker & docker-compose installed
  - Public IP

- **Nginx Reverse Proxy**

  - HTTPS termination
  - Basic Auth (optional)
  - Forward to `sola-history:8501`

- **Let's Encrypt (Certbot)**

  - Initial certificate
  - Renewal via cron or manual pipeline

- **App Container**

  - Pulls image from GitHub Container Registry
  - Uses Object Storage for data

### docker-compose on the VM

```text
reverse proxy (nginx)
        │
 HTTPS   │
        ▼
sola-history app (streamlit)
        │
 fetch JSON
        ▼
OCI Object Storage bucket
```

## Security Model

### Secrets

Stored securely:

| Secret                      | Location                       |
| --------------------------- | ------------------------------ |
| App password                | OCI Vault or GitHub Secrets    |
| Nginx Basic Auth            | VM only (`htpasswd`)           |
| OCI API key for data upload | GitHub Secret (data repo only) |

No secrets appear in git repositories.

### Access Control

- App protected by:

  - Nginx Basic Auth (optional)
  - Streamlit Password Gate
- VCN security lists restrict:

  - SSH to admin IP only
  - HTTPS to public
  - No open ingress for app port

### Data Governance

- Personal data (names, addresses, contacts) stored **only** in Object Storage
- No PII in app repository
- Encrypted at rest (SSE always active on OCI)
- Access via IAM policies:

  - CI user → write
  - App instance → read
  - No public access

## CI/CD Workflows

### App Repository

| Trigger        | Action                            |
| -------------- | --------------------------------- |
| Push to `main` | Build Docker image → Push to GHCR |
| Tag (`vX.Y.Z`) | Build → Push → Trigger deployment |

### Data Repository

| Trigger                | Action                                          |
| ---------------------- | ----------------------------------------------- |
| Manual ("Update data") | Run importer → Validate → Upload → Tag snapshot |
| Push to `main`         | Same as above                                   |

## Future Enhancements

- Automated SSL renewals with a Certbot sidecar container
- Full Terraform IaC for:

  - VCN
  - Subnets
  - Compute
  - IAM policies
  - Object Storage bucket
- Runner self-service portal (optional)
- Notifications (email or Teams webhook) for planning events

## 10. Summary

This architecture provides:

- Clear separation of **application** and **personal data**
- A secure, minimal operational deployment
- Automated data ingestion and validation
- A clean, modern CI/CD pipeline
- Transparent and easy developer workflow
