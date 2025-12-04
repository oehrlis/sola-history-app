# 🏃‍♂️ Sola History - Datenplattform & Analyse-App

Dieses Projekt enthält:

- eine **Sola-Stafette Datenplattform** (1998-2025),
- ein Import-Tool zur Aufbereitung der Excel-Dateien,
- eine **Streamlit Web-App** zur Analyse,
- vollständige Docker- und Local-Developer-Setups,
- sowie einen Flow für Deployment in der **Oracle Cloud (OCI)**.

Die Daten umfassen:

- Läufer:innen (mit Firmenzuordnung, extern-Flag, Aktivitäten),
- Teams pro Jahr,
- Etappen und Streckenlängen,
- vollständige Einzel- und Teamzeiten inkl. Pace & Ränge,
- kumulierte Team-Zwischenstände pro Etappe.

## 📁 Projektstruktur

```text
sola-history/
├── app.py                  # Streamlit App
├── Dockerfile
├── docker-compose.yml
├── Makefile                # Komfort-Befehle für Dev & Deployment
├── requirements.txt
├── data/
│   ├── raw/                # Original-Excel-Dateien
│   ├── processed/          # JSON export der Daten (für App)
│   └── schema/             # JSON Schema (Datenmodell)
└── tools/
    └── import_excel.py     # Excel → JSON Konverter
```

Details zu `data/` und `tools/` siehe README-Dateien in diesen Ordnern.

## 🚀 Schnellstart (Lokal, ohne Docker)

### Virtuelle Umgebung erstellen & installieren

```bash
make venv
make install
```

### Daten importieren (Excel → JSON)

```bash
make import
```

### Streamlit lokal starten

```bash
make run-local SOLA_APP_PASSWORD=meinpasswort
```

Danach lokal öffnen:

👉 [http://localhost:8501](http://localhost:8501)

## 🐳 Nutzung mit Docker

### Image bauen

```bash
make build
```

### Container starten

```bash
make up SOLA_APP_PASSWORD=meinpasswort
```

oder im Hintergrund:

```bash
make upd
```

### Container stoppen

```bash
make down
```

## 📦 Docker-Compose (empfohlen)

Das Repo enthält ein fertiges `docker-compose.yml`.
Damit kannst du die App inklusive Passwort und Daten-Mount einfach starten:

```bash
docker compose up
```

Oder mit Passwort:

```bash
SOLA_APP_PASSWORD=meinpass docker compose up
```

## 🌩 OCI Deployment (Oracle Cloud Infrastructure)

Hier der empfohlene Flow zum Deployment:

### Image in die OCI Container Registry pushen

Login:

```bash
docker login iad.ocir.io
```

Taggen:

```bash
docker tag sola-history iad.ocir.io/<tenancy-namespace>/sola-history:latest
```

Pushen:

```bash
docker push iad.ocir.io/<tenancy-namespace>/sola-history:latest
```

### Container Instance erstellen

In OCI → Developer Services → **Container Instances**:

- Image: aus OCI Registry
- CPU/RAM: 1 OCPU, 2 GB (reicht locker)
- Port: 8501
- Env-Var: `SOLA_APP_PASSWORD`
- Volume (optional):
  `/data/processed` → Host-Pfad oder Object Storage FUSE (optional)

### Public Endpoint / Load Balancer

Falls die App extern erreichbar sein soll:

- LB → Listener auf Port 443
- Backend: Container Instance Port 8501
- SSL-Termination → LB

## 🧰 Makefile - wichtigste Kommandos

| Kommando         | Beschreibung                      |
| ---------------- | --------------------------------- |
| `make venv`      | Lokale Python venv erstellen      |
| `make install`   | Requirements in venv installieren |
| `make run-local` | App lokal starten                 |
| `make import`    | Excel → JSON verarbeiten          |
| `make build`     | Docker-Image bauen                |
| `make up`        | Container starten                 |
| `make upd`       | Container im Hintergrund starten  |
| `make down`      | Container stoppen                 |
| `make shell`     | In Container einloggen            |
| `make clean-all` | Docker Cleanup                    |

## 📊 Features der Streamlit-App

- Jahresansicht (Teams, Etappen, Rangverlauf)
- Läufer:innen-Detailseite mit:

  - km pro Jahr
  - Starts pro Jahr
  - beste Ergebnisse
  - Übersicht aller Läufe
- Top-Listen:

  - Top 10 Gesamtkilometer
  - Top 10 Starts
  - Top 5 Teamrangierungen
  - Schnellste Etappen
  - Läufer:innen mit Top-10-Platzierungen
- Interaktive Charts (Altair)

## 🛠 Anforderungen

- Python 3.11+
- Docker & Docker Compose
- Streamlit, Pandas, Altair

## 📄 Lizenz

Interner, nicht-öffentlicher Gebrauch. Keine Weitergabe ohne Zustimmung.
