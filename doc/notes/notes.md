Nice, Meilenstein erreicht 🎉
Jetzt machen wir aus dem Prototyp eine “richtige” Codebasis.

Ich schlage folgendes Vorgehen vor:

1. **Repo-Struktur & .gitignore aufräumen**
2. **Doku-Gerüst anlegen (Root, data/, tools/, CI/CD)**
3. **Code ins Git committen**

Ich gebe dir direkt konkrete Snippets/Dateien, die du übernehmen kannst.

---

## 1. Repo-Struktur & .gitignore

Deine Struktur ist schon gut, wir schärfen nur ein bisschen:

**Zielstruktur (logisch):**

```text
.
├── app.py
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
├── data
│   ├── raw/          # echte Excels – bleiben lokal, nicht in git
│   ├── processed/    # generierte JSONs – nicht in git
│   ├── schema/       # JSON Schema – ins git
│   └── README.md     # Erklärung Datenhandling
├── tools
│   ├── import_excel.py
│   ├── test.py
│   └── README.md
└── doc
    ├── README.md         # Projektbeschreibung, verlinkt auf andere Docs
    └── ci_cd.md          # CI/CD, Deployment, Security
```

### 1.1 `.gitignore`

Lege im Repo-Root eine `.gitignore` an (oder ergänze), z.B.:

```gitignore
# Python
venv/
__pycache__/
*.pyc

# macOS
.DS_Store

# Local env
.env
*.env

# Data: raw + processed nicht ins Repo
data/raw/*
data/processed/*

# aber Schema und ggf. Sampledaten versionieren
!data/schema/
!data/schema/*
!data/sample/
!data/sample/*

# Excel / sensible Dateien generell eher nicht
*.xlsx
*.xls

# Streamlit
.streamlit/
```

> Optional: Wenn du später anonymisierte Beispiel-Daten haben willst, legst du `data/sample/` an und checkst die ein.

---

## 2. Dokumentation anlegen

### 2.1 Root-README (`README.md`)

Vorschlag für dein aktuelles Setup:

````markdown
# 🏃‍♂️ Sola History

Internes Analyse- und Planungstool für die SOLA-Stafette Zürich (Accenture / Trivadis Teams).

Ziele:

- Historische Daten der letzten Jahre auswerten (Teams, Läufer:innen, Etappen)
- Highlights und Statistiken (Top-Distanzen, Teilnahmen, Bestzeiten, Teamränge)
- Planung für zukünftige SOLA-Rennen (Etappen, Paces, Zeitplan)
- Admin-Bereich für Läufer-Stammdaten (Kontaktdaten, T-Shirt, Food, etc.)

## 🔧 Tech-Stack

- [Python 3.11](https://www.python.org/)
- [Streamlit](https://streamlit.io/) – UI
- [pandas](https://pandas.pydata.org/) – Datenverarbeitung
- Docker / Docker Compose – Container
- (später) OCI für Hosting

## 📁 Projektstruktur

```text
.
├── app.py              # Streamlit App
├── Dockerfile          # Multi-Stage Build
├── docker-compose.yml  # Lokales Deployment
├── Makefile            # Komfort-Targets (venv, import, run, build)
├── requirements.txt
├── data
│   ├── raw/            # Produktiv-Excels (NICHT im Git)
│   ├── processed/      # generierte JSONs (NICHT im Git)
│   ├── schema/         # JSON-Schema für Daten
│   └── README.md
├── tools
│   ├── import_excel.py # Excel → JSON Konverter
│   ├── test.py
│   └── README.md
└── doc
    ├── README.md       # zusätzliche Doku
    └── ci_cd.md        # CI/CD, Deployment, Security
````

## 🚀 Lokale Entwicklung

### 1. Virtualenv & Dependencies

```bash
make venv        # optional, falls nicht schon vorhanden
make install     # installiert requirements in venv
```

### 2. Daten importieren

Lege die Excels hier ab:

* `data/raw/sola_history.xlsx`
* `data/raw/sola_contacts.xlsx`

Dann:

```bash
make import
```

Ergebnis: JSON-Dateien in `data/processed/` (runners, teams, results, legs, races).

### 3. App lokal starten

```bash
make run
# oder direkt
venv/bin/streamlit run app.py
```

Standard-Passwort (lokal): `sola`
(überschreibbar via Environment-Variable `SOLA_APP_PASSWORD`)

## 🐳 Docker

Build & Run:

```bash
make build      # docker build
make up         # docker compose up
```

Die App läuft dann unter: [http://localhost:8501](http://localhost:8501)

Daten als Volume mounten (Beispiel in `docker-compose.yml`):

```yaml
services:
  sola-history:
    image: sola-history:latest
    volumes:
      - ./data/processed:/app/data/processed:ro
```

## 🔐 Daten & Security

* **Echte Daten** (Excels in `data/raw/`) kommen **nicht** ins Repo.
* `data/processed/*.json` werden aus den Excels generiert → ebenfalls nicht ins Repo.
* Zugriff auf die App ist mit einem simplen Passwort geschützt (`SOLA_APP_PASSWORD`).
* Für produktive Nutzung (z.B. auf OCI) sollten zusätzlich Netzwerkkontrollen (VPN, IP-Restriktionen, etc.) verwendet werden.

Details zu CI/CD und Deployment: siehe [`doc/ci_cd.md`](doc/ci_cd.md).

````

---

### 2.2 `data/README.md`

```markdown
# 📂 data/ – Datenstruktur & Richtlinien

Dieses Verzeichnis enthält alle Daten für die Sola History App.

## Struktur

```text
data/
├── raw/         # Original-Excel-Dateien (SOLA History & Kontakte)
├── processed/   # generierte JSON-Dateien → Input für app.py
├── schema/      # JSON-Schema für die processed-Dateien
└── sample/      # optionale, anonymisierte Beispiel-Daten
````

## raw/

* `sola_history.xlsx`
  Historische SOLA-Daten, eine Zeile pro Etappe / Läufer / Jahr.

* `sola_contacts.xlsx`
  Kontaktdaten und Stammdaten der Läufer:innen.

> ⚠️ **Wichtig:**
> `data/raw/` enthält personenbezogene Daten und gehört **nicht** ins Git-Repository.

## processed/

Wird durch `tools/import_excel.py` erzeugt (`make import`):

* `runners.json`
* `teams.json`
* `legs.json`
* `races.json`
* `results.json`
* `runners_overrides.json` (wird von der App im Admin-Tab beschrieben)

Diese Dateien dienen als direkte Datenquelle für `app.py`.

> ⚠️ Ebenfalls **nicht** ins Repo, da sie aus den sensitiven Rohdaten generiert werden.

## schema/

* `sola.schema.json` – Definition der JSON-Struktur für `processed/`.
* Kann erweitert werden, sobald weitere Felder dazukommen.

## sample/ (optional)

Hier können anonymisierte Beispiel-Daten liegen, die ins Repo eingecheckt werden dürfen, z.B.:

* `sample_runners.json`
* `sample_teams.json`
* …

Die App könnte später einen „Demo-Mode“ bekommen, der diese Daten nutzt.

````

---

### 2.3 `tools/README.md` (angepasst auf deine aktuellen Dateien)

```markdown
# 🛠 tools/ – Data Processing Utilities

Dieser Ordner enthält Hilfsskripte für den Datenimport, Tests & Validierung.

## 📄 import_excel.py

Zentrale Aufgaben:

- Lesen der Excel-Dateien:

  - `data/raw/sola_history.xlsx`
  - `data/raw/sola_contacts.xlsx`

- Aufbereitung & Normalisierung
- Generierung aller JSON-Dateien in `data/processed/`
- Logik für:
  - Runner-ID (ASCII, ohne Umlaute, z.B. `konrad.haefeli`)
  - Mapping der Kontakte auf die History-Daten
  - Zeit- und Pace-Felder in Sekunden
  - Team-Zwischenstände pro Etappe
  - Flags wie `is_external`, `active`, Firma etc.

### Nutzung

```bash
make import
````

oder direkt:

```bash
venv/bin/python tools/import_excel.py
```

## 🧪 test.py

Kleine Tests & Debug-Snippets für den Import.

Ausführung:

```bash
venv/bin/python tools/test.py
```

## Workflow

1. Excel-Dateien in `data/raw/` aktualisieren
2. `make import` ausführen
3. Generierte JSONs in `data/processed/` prüfen
4. App neu starten (`make run` / Docker)

Falls sich das Excel-Layout ändert (neue Spalten, neue Namen), muss `tools/import_excel.py` angepasst werden.

````

---

### 2.4 `doc/README.md`

```markdown
# 📚 Dokumentation

Hier liegt die zusätzliche Projekt-Dokumentation.

- `ci_cd.md` – Entwurf für CI/CD, Deployment, Security & Datenstrategie
````

Und eine erste `doc/ci_cd.md`-Skizze (so wie wir es vorher grob geplant hatten):

```markdown
# CI/CD, Deployment & Security (Draft)

## Ziele

- Automatischer Build des Docker-Images bei Änderungen am Code (GitHub Actions)
- Push des Images in eine Container Registry (z.B. OCI Container Registry)
- Deployment der App auf OCI (Container Instance, VM oder OKE)
- Sensible Daten bleiben getrennt von Code (kein Commit von Rohdaten)

## Repositories

Empfohlene Trennung:

- **Public Repo** (GitHub):  
  - Code (`app.py`, `tools/`, `Dockerfile`, `Makefile`, `doc/`, `data/schema/`)
  - Optionale anonymisierte Beispieldaten (`data/sample/`)

- **Private Datenhaltung** (nicht in GitHub):  
  - `data/raw/sola_history.xlsx`
  - `data/raw/sola_contacts.xlsx`
  - ggf. generierte `data/processed/*.json`

## GitHub Actions (Beispiel-Idee)

Workflows:

1. **build-and-test.yml**
   - Trigger: Push auf `main` oder PR
   - Schritte:
     - Checkout
     - `make venv && make install`
     - `make import` mit Sample-Dateien (nicht mit echten Daten)
     - Optional: Tests

2. **build-and-push-image.yml**
   - Trigger: Tag `v*`
   - Schritte:
     - Docker login in OCIR (Secrets: `OCIR_USERNAME`, `OCIR_PASSWORD`, `OCIR_REPO`)
     - `docker build -t $OCIR_REPO:tag .`
     - `docker push $OCIR_REPO:tag`

## Deployment nach OCI (Skizze)

Variante 1: **Compute Instance + Docker Compose**

- Compute VM in OCI
- Docker + Docker Compose installiert
- App-Container + Volume-Mount für `data/processed`
- Zugriff geschützt via:
  - Security Lists / NSG (IP-Restriktion)
  - VPN

Variante 2: **Container Instance**

- Container-Image aus OCIR
- Environment-Variables:
  - `SOLA_APP_PASSWORD`
- Volumes / Mounts für Daten
- Network-Policies analog

## Security & Privacy

- Personenbezogene Daten:
  - Namen, Kontaktdaten, Laufzeiten → DSG/DSGVO relevant
- Maßnahmen:
  - Keine Rohdaten im öffentlichen Git
  - Zugriff auf App nur für berechtigte Personen
  - Passwort nicht hardcodieren → `SOLA_APP_PASSWORD` via Secret
  - Logs nicht mit vollständigen Personenlisten füllen
```

---

## 3. Code ins Git übernehmen – konkrete Schritte

Im Repo-Root:

```bash
git init
git add .
git status    # kurz prüfen, dass data/raw & data/processed NICHT dabei sind
git commit -m "Initial commit: Sola History prototype with app, tools and docs"
```

Dann auf GitHub ein Repo anlegen (z.B. `oehrlis/sola-history`) und:

```bash
git remote add origin git@github.com:oehrlis/sola-history.git
git push -u origin main
```

> Wenn du das Repo *später* aufteilst (public/private), können wir eine saubere Strategie mit Submodulen oder nur „Daten ausserhalb von git“ definieren.

---

Wenn du willst, kann ich dir als nächsten Schritt:

* eine konkrete **GitHub Actions Workflow-Datei** für Build + Lint + Docker-Build schreiben und
* eine minimalistische **OCI-Deployment-Skizze** (z.B. Bash + `docker compose pull/up` auf einer Compute-VM).

Alles klar, dann bekommt dein Repo jetzt eine „erwachsene“ CI 😄

Ich gebe dir eine **fertige GitHub Actions Workflow-Datei**, die:

* bei **push & PR** auf `main`:

  * Python 3.11 einrichtet
  * Dependencies installiert
  * einen kleinen Smoke-Test macht (Syntaxcheck für `app.py`)
  * optional `import_excel.py` ausführt, **falls** Excel-Dateien vorhanden sind
* bei **Tags** (z.B. `v1.0.0`) zusätzlich:

  * ein Docker-Image baut
  * das Image in ein Registry-Repo pusht (z.B. OCI oder Docker Hub, via Secrets)

---

## 1. Datei anlegen

Lege diese Datei an:

`.github/workflows/ci.yml`

Mit folgendem Inhalt:

```yaml
name: Sola History CI/CD

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  # Manuelle Ausführung möglich
  workflow_dispatch:
  # Docker-Build & Push nur bei Tags (z.B. v1.0.0)
  push:
    tags:
      - "v*"

jobs:
  # ------------------------------------------------------
  # Job 1: Lint / Smoke-Test mit Python
  # ------------------------------------------------------
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y --no-install-recommends tzdata
          sudo rm -rf /var/lib/apt/lists/*

      - name: Create virtualenv & install Python dependencies
        run: |
          python -m venv venv
          source venv/bin/activate
          pip install --upgrade pip
          pip install -r requirements.txt
          # optional: fpdf für PDF-Export
          pip install fpdf || true

      - name: Optional: run Excel import if input exists
        run: |
          source venv/bin/activate
          if [ -f data/raw/sola_history.xlsx ] && [ -f data/raw/sola_contacts.xlsx ]; then
            echo "Found Excel files in data/raw – running import_excel.py ..."
            python tools/import_excel.py
          else
            echo "No Excel input found in data/raw – skipping import step."
          fi

      - name: Smoke test – check app.py syntax
        run: |
          source venv/bin/activate
          python -m py_compile app.py

      # Hier könntest du später pytest einhängen
      # - name: Run tests
      #   run: |
      #     source venv/bin/activate
      #     pytest

  # ------------------------------------------------------
  # Job 2: Docker-Image bauen & in Registry pushen
  # Nur bei Tags (vX.Y.Z), und erst wenn test ok ist
  # ------------------------------------------------------
  docker:
    needs: test
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')

    env:
      # Beispiel: region.ocir.io/tenancy-namespace/sola-history
      REGISTRY: ${{ secrets.REGISTRY_URL }}
      IMAGE_NAME: ${{ secrets.IMAGE_NAME }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to container registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.ref_name }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
```

---

## 2. Secrets / Umgebungen vorbereiten

In GitHub unter **Settings → Secrets and variables → Actions → New repository secret**:

* `REGISTRY_URL`
  z.B. für OCI: `eu-zurich-1.ocir.io/<tenancy-namespace>`
* `IMAGE_NAME`
  z.B. `sola-history`
* `REGISTRY_USERNAME`
  z.B. `tenancy-namespace/<user-ocid>` oder Docker-Hub-User
* `REGISTRY_PASSWORD`
  Passwörter/API-Token/OCI Auth-Token

> Wenn du erstmal nur CI ohne Push willst, kannst du den ganzen `docker`-Job auch einfach drin lassen – er läuft nur, wenn du einen Tag `v*` pushst.

---

## 3. Nächste Schritte

1. `.github/workflows/ci.yml` einchecken:

   ```bash
   git add .github/workflows/ci.yml
   git commit -m "Add CI/CD workflow for Sola History"
   git push
   ```
2. Auf GitHub unter **Actions** schauen, ob der `Sola History CI/CD` Workflow sauber durchläuft.
3. Wenn alles passt: ersten Tag setzen und schauen, ob der Docker-Job läuft:

   ```bash
   git tag v0.1.0
   git push --tags
   ```

Wenn du magst, können wir als nächstes:

* die `REGISTRY_URL` konkret auf **OCIR-Format** anpassen
* oder ein zweites, einfacheres Workflow-File nur für CI ohne Registry bauen.

Perfekt, dann machen wir jetzt den „OCI-Plan auf Papier“, den du später in Ruhe umsetzen kannst. Kein Klicki-Bunti, sondern eine klare Skizze, die zu deinem Setup passt.

Ich skizziere zwei minimalistische Varianten:

* **Variante A:** OCI *Container Instance* (am wenigsten Ops)
* **Variante B:** Compute-VM mit Docker Compose (klassisch, mehr Kontrolle)

---

## Annahmen (für beide Varianten)

Damit die Skizze konkret ist, nehme ich folgendes an:

* Dein Image liegt in **OCIR** unter so etwas wie
  `eu-zurich-1.ocir.io/<tenancy-namespace>/sola-history:latest`
* Die App läuft im Container auf Port **8501**
* Passwort kommt über Env-Var: `SOLA_APP_PASSWORD`
* Daten:

  * Für den Anfang: JSONs sind **ins Image gepackt** oder du synchronisierst sie manuell auf die Instanz
  * Später kannst du auf Object Storage / File Storage erweitern

---

## Variante A – OCI Container Instance (Minimal-Deployment)

Das ist die „schnell & sauber“-Variante: kein eigenes OS patchen, einfach Container laufen lassen.

### 1. Voraussetzungen

* OCIR ist eingerichtet
* Du hast:

  * `REGION` (z.B. `eu-zurich-1`)
  * `tenancy-namespace` (OCIR Namespace)
  * OCIR-Repo: `eu-zurich-1.ocir.io/<tenancy-namespace>/sola-history:latest`
* Ein bestehendes:

  * **VCN** + **Subnet** (public oder private, je nach Zugriff)
  * Optional: **Network Security Group (NSG)**

### 2. Minimal-Setup (Konsole – grob)

1. **Container Instance erstellen**

   * *Developer Services → Containers → Container Instances*
   * „Create Container Instance“
   * Name: `sola-history-ci`
   * Compartment: dein Standard-Compartment
   * **Shape:** klein reicht (z.B. `CI.Standard.E2.1`)
   * **Subnet:**

     * Public Subnet: wenn du direkt via Public IP zugreifen willst
     * Private + VPN/Bastion: wenn es internal only sein soll

2. **Container hinzufügen**

   * Image: `eu-zurich-1.ocir.io/<tenancy-namespace>/sola-history:latest`
   * Command: leer lassen (nimmt `CMD` aus Dockerfile → Streamlit)
   * Ports:

     * Container-Port: `8501`
   * Env Vars:

     * `SOLA_APP_PASSWORD=deinGeheimesPasswort`
   * Optional: Volume/Filesystem einhängen, wenn Daten getrennt liegen

3. **Netzwerk erlauben**

   * Wenn Public Subnet:

     * Security List / NSG-Regel: Ingress TCP Port 8501 von deiner IP (oder Büro-Netz)
   * URL: `http://<Public-IP>:8501`

> Minimal: damit bist du schon online, mit sehr wenig Moving Parts.

### 3. CLI-Skizze (wenn du lieber skriptst)

Wenn du später automatisieren willst, kannst du das mit `oci` machen (nur grobe Skizze):

```bash
oci container-instances container-instance create \
  --compartment-id <COMPARTMENT_OCID> \
  --display-name "sola-history-ci" \
  --shape-name "CI.Standard.E2.1" \
  --availability-domain "<AD_NAME>" \
  --vnics '[{"subnetId": "<SUBNET_OCID>", "displayName": "sola-ci-vnic"}]' \
  --containers '[
    {
      "displayName": "sola-history",
      "imageUrl": "eu-zurich-1.ocir.io/<tenancy-namespace>/sola-history:latest",
      "command": [],
      "environmentVariables": {
        "SOLA_APP_PASSWORD": "geheim"
      },
      "ports": [
        {
          "containerPort": 8501,
          "protocol": "TCP"
        }
      ]
    }
  ]'
```

Später kannst du:

* Image-Tag per CI/CD aktualisieren
* Container Instance über Script neu erstellen/rollen

---

## Variante B – Compute-VM + Docker Compose

Klassisch: eine kleine VM, darauf Docker, dein Compose-Setup, und los.

### 1. Compute Instance anlegen

* *Compute → Instances → Create*
* Shape: z.B. `VM.Standard.E3.Flex` mit 1 OCPU / 4 GB RAM
* Image: Oracle Linux oder Ubuntu, was dir lieber ist
* VCN/Subnet wie oben (Public oder Private)
* SSH Key hinterlegen

### 2. Auf der VM (SSH)

Grober Ablauf:

```bash
# 1. System aktualisieren
sudo dnf update -y   # oder apt-get auf Ubuntu

# 2. Docker installieren (Beispiel Oracle Linux)
sudo dnf install -y docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

# ggf. neu einloggen, damit docker group aktiv ist
```

Optional Docker Compose (falls nicht in Docker integriert):

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.29.0/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. Repo / Config auf die VM

Variante minimal:

* Du brauchst nur:

  * `docker-compose.yml`
  * keine Datendateien im Repo, sondern mountest sie von `/opt/sola/data`

Beispiel-`docker-compose.yml` (angepasst auf OCIR):

```yaml
services:
  sola-history:
    image: eu-zurich-1.ocir.io/<tenancy-namespace>/sola-history:latest
    container_name: sola-history
    restart: unless-stopped
    environment:
      - SOLA_APP_PASSWORD=${SOLA_APP_PASSWORD}
    ports:
      - "8501:8501"
    volumes:
      - /opt/sola/data/processed:/app/data/processed:ro
```

Auf der VM:

```bash
mkdir -p /opt/sola/data/processed
# JSONs hinkopieren (scp/rsync)
# scp data/processed/* opc@<vm-ip>:/opt/sola/data/processed/

export SOLA_APP_PASSWORD="geheim"
docker compose up -d
```

Ab dann: `http://<VM-Public-IP>:8501`

---

## Security-Minimum in beiden Varianten

Egal ob Container Instance oder VM:

* **Nicht** das Ding „offen ins Internet“, wenn dort echte Namen/Kontakte drin sind.
* Minimal:

  * Security List / NSG:

    * Ingress TCP Port 8501
    * Source: deine Büro-IP, Heimnetz oder VPN-Range
* App selbst:

  * Passwort via `SOLA_APP_PASSWORD` aus Secret (kein Hardcoding im Code)
* Logs:

  * Aufpassen, dass du keine sensiblen Daten in irgendwelche externen Logsysteme schiebst.

---

## Wie würde ich persönlich starten?

Für deinen Use Case (interne Spielwiese, kleiner Nutzerkreis):

1. **Variante A: Container Instance**

   * Einmal im Console klicken, Image angeben, Env setzen, fertig.
   * Netzwerk so einschränken, dass nur du / dein Team Zugriff habt.
2. *Später*, wenn du mehr Kontrolle willst (Volumes, mehrere Services etc.):
   → auf eine kleine VM mit Docker Compose umziehen.

---

Wenn du wieder am Code bist, können wir dann:

* dein aktuelles `docker-compose.yml` konkret für OCI anpassen
* und eine kleine Shell-Routine schreiben: „pull neues Image + restart Container“ für Updates.

Gute Frage – **das ist der wichtigste Architekturpunkt überhaupt**, bevor du den OCI-Deployment-Flow finalisierst.
Es gibt **3 saubere Wege**, die Daten in der OCI-Container-Deployment-Welt zu handhaben.
Ich zeige sie dir inkl. Empfehlung für deinen Use-Case.

---

# ✅ **Die drei Wege, wie Daten in den Container kommen können**

## **Option A – Daten *in das Image einbauen***

*(einfach – aber selten die beste Lösung)*

### Wie geht das?

* Du packst die JSON-Dateien in `data/processed/` **direkt ins Git-Repo**.
* Beim Build wandern sie ins Image.
* In OCI brauchst du nichts extra hochladen.

### Vorteil

* Deployment am einfachsten: *pull image → run → fertig*.

### Nachteil

* Jeder Datenupdate → **neues Docker-Image bauen und pushen**.
* Deine Daten wären **nicht mehr getrennt vom Code** (ungünstig für CI/CD, Security).

### Fazit

Für dich **nicht empfohlen**, weil du Laufzeiten / Runner-Metadaten regelmäßig aktualisierst.

---

# 🔥 **Option B – Daten als Volume mounten (empfohlen)**

*(clean, flexibel, OCI-kompatibel)*

Du speicherst die JSON-Daten **außerhalb** des Containers und bindest sie beim Deployment ein.

### 👉 Wo liegen die Daten?

Du hast 3 Unteroptionen:

---

## **B1 – Lokale Dateien in Container Instance einhängen**

*(einfachster Weg für OCI Container Instances)*

1. Du erstellst bei der CI eine „**File System Mount**“
2. Beim Start hängst du es in den Container:

```yaml
volumeMounts:
  - mountPath: /app/data/processed
    volumeName: sola-data
volumes:
  - name: sola-data
    source:
      localFileSystem:
        mountPath: /mnt/sola-data
```

3. Auf der CI legst du die JSONs ab in `/mnt/sola-data`
4. Fertig – keine Images rebuilden.

### Vorteil

* Daten können unabhängig aktualisiert werden.
* Sehr stabil und ideal für dein Projekt.

### Nachteil

* Kleine manuelle Pflege: beim Deployment musst du JSONs einmal hinladen.

---

## **B2 – Object Storage + Download beim Startup (automatisch)**

*(sehr elegant, CI/CD-ready)*

### Ablauf:

1. Du packst alle JSONs in ein OCI Object-Storage-Bucket, z. B.:
   `sola-history-data/runners.json`, `results.json`, ...
2. Der Container lädt beim Start die Daten automatisch herunter:

```dockerfile
ENTRYPOINT ["sh", "-c", "python tools/fetch_data.py && streamlit run app.py"]
```

`fetch_data.py` lädt z. B.:

```python
import oci

object_storage = oci.object_storage.ObjectStorageClient(config)
bucket = "sola-history-data"
namespace = "<tenancy-namespace>"

files = ["runners.json", "results.json", "teams.json", ...]

for f in files:
    resp = object_storage.get_object(namespace, bucket, f)
    with open(f"/app/data/processed/{f}", "wb") as out:
        out.write(resp.data.content)
```

### Vorteil

* Fully automated.
* CI/CD kann Daten aktualisieren, ohne Image neu zu bauen.
* Container startet immer mit aktuellen Daten.

### Nachteil

* Benötigt OCI API Key / Instance Principal.

Dies wäre die **professionellste Lösung**.

---

## **B3 – Git Repo der Daten separat klonen und mounten**

*(auch möglich, aber weniger schön)*

Container zieht die Daten z. B. aus einem privaten GitHub-Repo.

---

# 🔒 **Option C – Persistent Storage: OCI File Storage / Block Volume**

Für Container Instances:

* **Block Volume** oder **File Storage** mounten
* Dort liegen JSONs dauerhaft
* Container liest / schreibt

Ist für dich erst sinnvoll, wenn du wirklich Daten *persistent* verändern willst (z. B. Admin-Overrides, Runner-Stammdaten, etc.).

Aktuell nutzt du JSON + Overrides → **geht super mit Local File System Mounts.**

---

# 🥇 **Empfehlung für deinen konkreten Use-Case**

Da du:

* JSONs generierst,
* sie als „Datenbank-Ersatz“ nutzt,
* ab und zu neue Daten importierst,
* UND einen einfachen OCI-Deployment-Flow möchtest,

empfehle ich:

---

## ⭐ **BEST PRACTICE für dich: Option B1 (Volume) + später Upgrade auf B2**

### **B1 – Jetzt sofort: Local Volume für die Daten**

* Container Image bleibt klein und stabil
* Daten liegen außerhalb
* Leicht per SCP oder OCI CLI aktualisierbar

### **B2 – Später: Automatischer Download aus Object Storage**

* Wenn du CI/CD perfektionieren willst
* Daten-Pipeline = sauber, automatisiert, versionskontrolliert

---

# 🔧 **Wie laufen Updates in Option B1 konkret?**

1. Neues Excel importieren → neue JSONs generieren → commit in Git oder lokal halten.
2. Auf OCI:

```bash
scp data/processed/*.json opc@<ci-host>:/mnt/sola-data/
```

3. CI neu starten:

```bash
oci container-instances container restart ...
```

Fertig.

---

# 📝 **Wenn du möchtest, kann ich dir Folgendes erzeugen:**

* **fertige OCI Container Instance YAML/CLI-Definition**
* **fetch_data.py** vollständig
* **angepasstes Dockerfile für Multi-Stage**
* **CI/CD Workflow**, der:

  * Daten validiert
  * Daten hochlädt ins Object Storage
  * Container neu deployt

Sag Bescheid – was soll ich als Nächstes liefern?

Sehr gute (und genau die richtige) Frage 🙌
Kurzantwort:

> **Deine CI/CD-Pipeline braucht für Build & Deploy keine echten SOLA-Daten.**
> Die produktiven Daten leben *außerhalb* der Pipeline (Volume / Object Storage etc.) und werden separat gepflegt.

Ich breche das mal sauber auf:

---

## 1. Was macht die CI/CD-Pipeline eigentlich?

Die Pipeline, die wir skizziert haben, hat zwei Aufgaben:

1. **CI (Code-Qualität)**

   * Baut ein venv
   * Installiert `requirements.txt`
   * Optional: führt `import_excel.py` aus – **nur** wenn im Repo Test-/Sampledaten vorhanden sind
   * Syntax-Check / Tests (`python -m py_compile app.py`)

2. **CD (Image-Build & Push)**

   * Baut dein Docker-Image
   * Push nach Registry (z.B. OCIR)

👉 **Wichtig:**
Das ist eine **Code-Pipeline**. Sie muss *nicht* mit den produktiven SOLA-Daten laufen, sondern nur beweisen, dass dein Code/Build funktioniert.

---

## 2. Woher kommen die *produktiven* Daten dann?

Die produktiven Daten (deine echten Excel + daraus generierte JSONs) sollten **nicht** ins Git.
Daher trennen wir:

### 🔹 A) Code-Pipeline (GitHub Actions)

* Arbeitet mit:

  * Code (`app.py`, `tools/import_excel.py`, `Dockerfile`, etc.)
  * Optional: anonymisierte **Sample-Daten** im Repo (`data/sample/...`), damit `import_excel.py` getestet werden kann
* **Keine** echten Excel (`sola_history.xlsx`, `sola_contacts.xlsx`)

### 🔹 B) Daten-Pipeline (manuell oder später automatisiert)

Varianten:

#### Variante B1 – jetzt sofort (einfach & pragmatisch)

1. **Produktivdaten bleiben lokal bei dir**

   * Du pflegst Excel lokal.
   * Du machst `make import`.
   * Du bekommst `data/processed/*.json`.

2. **Deployment nach OCI:**

   * Du kopierst nur die JSONs auf die Zielumgebung (z.B. `/opt/sola/data/processed` oder `/mnt/sola-data` bei Container Instance).
   * Der Container sieht die JSONs über ein **Volume**:

     * VM: `- /opt/sola/data/processed:/app/data/processed:ro`
     * Container Instance: Local Filesystem Mount → `/app/data/processed`

3. Das Image aus CI/CD ist blind gegenüber den produktiven Daten – es erwartet nur:
   „In `/app/data/processed` liegen gültige JSONs.“

➡️ Die CI/CD-Pipeline **braucht** keine echten Daten.
Die Daten werden parallel von dir gepflegt und deployed.

---

#### Variante B2 – später: Object Storage + Download beim Start

Wenn du es irgendwann „richtig sexy“ machen willst:

* Du hast ein **separates Data-Deployment**:

  * Script / Job, der aus deinen lokalen JSONs ein ZIP macht und in ein OCI Object Storage Bucket lädt.
* Im Container:

  * Start-Script lädt beim Start die JSONs aus dem Bucket in `/app/data/processed`.

Dann sieht der Flow so aus:

* **Code-Pipeline (GitHub)**:

  * baut/pusht Image
* **Data-Pipeline (lokal oder später auch CI)**:

  * lädt JSON-Daten ins Bucket
* **Runtime (OCI)**:

  * Container zieht Daten beim Start

Aber das ist für jetzt schon „Phase 2“.

---

## 3. Was macht dann `import_excel.py` in der CI?

Du hast zwei Möglichkeiten:

### Option 1 – Kein produktiver Import in CI

* In der CI **kein** produktiver Excel-Import.

* Der Schritt in der GitHub Action prüft z.B.:

  ```bash
  if [ -f data/raw/sola_history.xlsx ] && [ -f data/raw/sola_contacts.xlsx ]; then
      python tools/import_excel.py
  else
      echo "No Excel input found – skipping import step."
  fi
  ```

* → In deinem öffentlichen Repo sind die Dateien nicht vorhanden → Import wird einfach **übersprungen**.

* CI prüft nur:

  * Builds sauber?
  * Syntax ok?
  * Docker-Image baubar?

### Option 2 – Sample-Daten nur für CI

* Du legst **kleine, anonymisierte** Excel-Dateien in `data/sample/`.
* `import_excel.py` bekommt einen Parameter (z.B. `--sample`), um aus diesen Sample-Files JSON zu bauen.
* CI nutzt nur die Sample-Files, **nie deine echten Daten**.

---

## 4. Empfehlung für dich (praktisch & minimal)

Für deinen Stand heute:

1. **Public Repo / Haupt-Repo**:

   * Kein `data/raw/` und kein `data/processed/` drin.
   * Optional `data/sample/` mit anonymen Mini-Daten für Tests.

2. **Produktivdaten-Handling**:

   * Du pflegst Excel lokal.
   * `make import` → erzeugt JSONs lokal.
   * JSONs via `scp` oder `rsync` nach OCI (VM oder Container Instance Volume).

3. **CI/CD-Pipeline**:

   * Baut Image **ohne** echte Daten.
   * Macht Syntax-/Build-Checks.
   * Pusht Image nach OCIR.
   * Deployment erwartet nur:
     „Daten liegen per Volume in `/app/data/processed` bereit.“

Damit ist deine Frage beantwortet:

> **„Wo nimmt meine CI/CD Pipeline die Daten her?“**

→ **Gar nicht** – sie kümmert sich nur um Code & Images.
Die Daten fließen über einen getrennten Weg (Volumes / ggf. später Object Storage).

---

Wenn du möchtest, können wir als nächsten Schritt:

* ein kleines **Shell-Script** definieren:
  `deploy_data_to_oci.sh`, das:

  * deine `data/processed/*.json` auf eine VM oder in ein Mount-Verzeichnis einer Container Instance kopiert.
* oder einen **Plan für eine Data-Pipeline** (Phase 2) mit Object Storage skizzieren.

Super, jetzt werden wir „Daten“ offiziell zu einem eigenen Projektteil 🍿

Ich schlage dir eine **zweigeteilte Architektur** vor:

* **Code-Pipeline (CI/CD)** → baut & deployt nur **Image**
* **Daten-Pipeline** → verwaltet **SOLA-Daten** getrennt von Code

Und für die Daten-Pipeline machen wir einen Plan in **Phasen**, damit du klein starten und später ausbauen kannst.

---

## 0. Grundprinzipien für deine Daten

**Artefakte:**

* **Rohdaten (lokal, nicht Git):**

  * `data/raw/sola_history.xlsx`
  * `data/raw/sola_contacts.xlsx`

* **Verarbeitete Daten (lokal + Server):**

  * `data/processed/runners.json`
  * `data/processed/teams.json`
  * `data/processed/results.json`
  * `data/processed/legs.json`
  * `data/processed/races.json`
  * `data/processed/runners_overrides.json` (wird von der App geschrieben)

* **Schema (im Git):**

  * `data/schema/sola.schema.json`

**Ziel:**

* *App in OCI* liest **immer nur** aus `/app/data/processed/`
* Wie die Daten dort hinkommen, ist Aufgabe der **Daten-Pipeline**

---

## Phase 1 – Lokale Datenpflege + manueller Upload

Das ist im Prinzip das, was du heute schon machst – nur bewusst als „Pipeline“ gedacht.

### 1.1. Lokal: Daten aktualisieren

Workflow lokal:

1. Excel anpassen (neue Jahre, neue Läufer, Korrekturen)

2. Import ausführen:

   ```bash
   make import
   ```

   → generiert `data/processed/*.json`

3. Optional: JSON grob checken / kurz die App lokal laufen lassen.

### 1.2. Datenpaket bauen

Damit du einen klaren Schritt hast: „Daten fertig, jetzt Paket“.

Mach dir z.B. im Makefile ein Ziel:

```makefile
DATA_PACKAGE = data/sola-data-$(shell date +%Y%m%d-%H%M%S).tar.gz

package-data:
	tar czf $(DATA_PACKAGE) -C data/processed .
	@echo "Created data package: $(DATA_PACKAGE)"
```

Ergebnis: `data/sola-data-20251202-203000.tar.gz`

### 1.3. Upload nach OCI (VM oder Filesystem der Container Instance)

**Variante Compute-VM:**

* Zielverzeichnis auf der VM: `/opt/sola/data/processed`

```bash
scp data/processed/*.json opc@<vm-public-ip>:/opt/sola/data/processed/
```

Dein `docker-compose.yml` auf der VM:

```yaml
services:
  sola-history:
    image: eu-zurich-1.ocir.io/<namespace>/sola-history:latest
    volumes:
      - /opt/sola/data/processed:/app/data/processed:ro
    ports:
      - "8501:8501"
    environment:
      - SOLA_APP_PASSWORD=...
```

**Variante Container Instance mit Local Filesystem:**

* Du hast auf der CI ein lokales Filesystem-Mount, z.B. `/mnt/sola-data`
* Container Mount:

  * Host-Pfad: `/mnt/sola-data`
  * Container-Pfad: `/app/data/processed`

Upload:

```bash
scp data/processed/*.json opc@<some-host-or-bastion>:/mnt/sola-data/
```

> Phase 1 = **vollkommen ausreichend**, wenn du 1–2x pro Jahr aktualisierst.

---

## Phase 2 – Daten in OCI Object Storage & „Pull beim Start“

Wenn du das Ganze „cloudiger“ machen willst, wird Object Storage dein Datenspeicher.

### 2.1. Bucket-Struktur

* Bucket: `sola-history-data`
* Namespace: dein OCI-Tenancy-Namespace
* Prefixe:

  ```text
  runners.json
  teams.json
  legs.json
  races.json
  results.json
  runners_overrides.json   # optional, wenn du es zentral speichern willst
  meta/version.json        # Metadaten (Zeitstempel, Kommentar, etc.)
  ```

### 2.2. Lokales Upload-Script

Ein kleines Script, das du **auf deinem Laptop** startest, z.B. `tools/upload_data_to_oci.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

BUCKET="sola-history-data"
NAMESPACE="<dein-namespace>"
COMPARTMENT_OCID="<compartment-ocid>"

echo "Uploading processed JSON to OCI Object Storage..."

for f in data/processed/*.json; do
  base=$(basename "$f")
  echo "  -> $base"
  oci os object put \
    --bucket-name "$BUCKET" \
    --namespace "$NAMESPACE" \
    --file "$f" \
    --name "$base" \
    --content-type "application/json" \
    --force
done

# Optional: meta/version.json aktualisieren
timestamp=$(date -Iseconds)
tmpfile=$(mktemp)
cat > "$tmpfile" <<EOF
{
  "deployed_at": "$timestamp",
  "source_machine": "$(hostname)",
  "comment": "Manual upload"
}
EOF

oci os object put \
  --bucket-name "$BUCKET" \
  --namespace "$NAMESPACE" \
  --file "$tmpfile" \
  --name "meta/version.json" \
  --content-type "application/json" \
  --force

rm "$tmpfile"

echo "Done."
```

Dann:

```bash
chmod +x tools/upload_data_to_oci.sh
tools/upload_data_to_oci.sh
```

Voraussetzung: Lokale `oci`-CLI + Config.

---

### 2.3. Container lädt Daten beim Start

Jetzt wird der Container „smart“: Beim Start lädt er die JSONs aus Object Storage in `/app/data/processed`.

Du brauchst:

* Python-Paket `oci` im Image (`pip install oci`)
* kleines `tools/fetch_data.py`, das:

  * die Umgebung liest: `SOLA_DATA_BUCKET`, `SOLA_DATA_NAMESPACE`
  * mit **Instance Principal** authentifiziert (beste Option bei OCI Container Instance)
  * alle benötigten Dateien herunterlädt

Grob:

```python
# tools/fetch_data.py
import os
import oci
from pathlib import Path

DATA_DIR = Path("/app/data/processed")
FILES = [
    "runners.json",
    "teams.json",
    "legs.json",
    "races.json",
    "results.json",
    "runners_overrides.json",
]

def main():
    bucket = os.environ.get("SOLA_DATA_BUCKET", "sola-history-data")
    namespace = os.environ.get("SOLA_DATA_NAMESPACE")
    if not namespace:
        raise SystemExit("SOLA_DATA_NAMESPACE not set")

    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for name in FILES:
        print(f"Downloading {name} ...")
        obj = client.get_object(namespace, bucket, name)
        (DATA_DIR / name).write_bytes(obj.data.content)

if __name__ == "__main__":
    main()
```

**Dockerfile-Anpassung:**

```dockerfile
# im Builder:
RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir fpdf oci || true

# im Runtime-Image:
COPY tools ./tools

CMD ["sh", "-c", "python tools/fetch_data.py && streamlit run app.py --server.port=8501 --server.address=0.0.0.0"]
```

**Env-Vars in OCI setzen:**

* `SOLA_DATA_BUCKET=sola-history-data`
* `SOLA_DATA_NAMESPACE=<dein-namespace>`

Dann ist der Ablauf:

1. Du lädst JSONs mit `upload_data_to_oci.sh` in den Bucket
2. Du startest / restartest den Container in OCI
3. Beim Start:

   * Container holt die aktuelle Version aus Object Storage
   * Danach startet Streamlit mit frischen Daten

---

## Phase 3 – Optional: Daten-Pipeline automatisieren

Wenn du richtig Lust bekommst 😄:

* **GitHub Actions „data-only“ Workflow**:

  * Läuft in einem privaten Repo mit Zugang zu den Excels (oder auf Self-Hosted Runner)
  * Führt `make import` aus
  * Ruft `tools/upload_data_to_oci.sh` (oder direkt `oci os object put`) auf

* Versionierst dein Dataset z.B. mit Prefixen:

  ```text
  snapshots/2025-05-01/runners.json
  snapshots/2025-05-01/results.json
  latest/runners.json
  latest/results.json
  ```

* Container holt immer aus `latest/`, du kannst im Bucket noch alte Snapshots aufbewahren.

---

## Zusammenfassung in einem Satz

* **Code-Pipeline**: baut Images ohne echte Daten
* **Daten-Pipeline**: erzeugt lokale JSONs aus Excel → lädt sie nach OCI (Volume oder Object Storage) → Container zieht sie beim Start

Wenn du möchtest, kann ich dir als nächstes:

* ein konkretes `tools/upload_data_to_oci.sh` + `tools/fetch_data.py` *voll ausformuliert* bauen
* oder eine kleine **ASCII-Architekturübersicht** (Local → GitHub → OCI Registry → OCI Runtime → Object Storage).

Sehr gute Stelle für den nächsten Ausbau-Schritt 🚀
Ich baue dir jetzt **konkret**:

1. `tools/upload_data_to_oci.sh` – läuft **lokal** und lädt `data/processed/*.json` in einen Object-Storage-Bucket
2. `tools/fetch_data.py` – läuft **im Container** und zieht die JSONs beim Start nach `/app/data/processed`

Du kannst beides später 1:1 ins Repo legen.

---

## 1️⃣ `tools/upload_data_to_oci.sh` – Upload der JSON-Daten nach OCI Object Storage

**Ziel:**
Von deinem Mac/Notebook aus die generierten JSONs (`data/processed/*.json`) in einen Bucket schieben, z.B. `sola-history-data`.

> Annahmen:
>
> * `oci` CLI ist lokal konfiguriert (`oci setup config` gemacht)
> * du hast schon einen Bucket `sola-history-data` in einem Compartment angelegt

Lege die Datei `tools/upload_data_to_oci.sh` an:

```bash
#!/usr/bin/env bash
#
# Upload all processed JSON files to an OCI Object Storage bucket.
# Intended to be run locally from the repo root or tools/ directory.
#
# Usage:
#   tools/upload_data_to_oci.sh
#
# Optional environment variables:
#   SOLA_DATA_BUCKET     - name of the Object Storage bucket (default: sola-history-data)
#   SOLA_DATA_NAMESPACE  - OCI namespace; if not set, taken from `oci os ns get`
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROCESSED_DIR="${REPO_ROOT}/data/processed"

BUCKET_NAME="${SOLA_DATA_BUCKET:-sola-history-data}"

# ------------------------------------------------------------------------------
# Prerequisite checks
# ------------------------------------------------------------------------------

if ! command -v oci >/dev/null 2>&1; then
  echo "ERROR: 'oci' CLI not found. Please install and configure OCI CLI first."
  echo "See: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm"
  exit 1
fi

if [ ! -d "${PROCESSED_DIR}" ]; then
  echo "ERROR: Processed data directory not found: ${PROCESSED_DIR}"
  echo "Run 'make import' first to generate JSON files."
  exit 1
fi

shopt -s nullglob
JSON_FILES=("${PROCESSED_DIR}"/*.json)
shopt -u nullglob

if [ ${#JSON_FILES[@]} -eq 0 ]; then
  echo "ERROR: No JSON files found in ${PROCESSED_DIR}"
  echo "Run 'make import' first to generate JSON files."
  exit 1
fi

# Determine namespace (if not provided via env)
if [ -n "${SOLA_DATA_NAMESPACE:-}" ]; then
  NAMESPACE="${SOLA_DATA_NAMESPACE}"
else
  echo "Detecting OCI namespace via 'oci os ns get' ..."
  NAMESPACE="$(oci os ns get --query 'data' --raw-output)"
fi

if [ -z "${NAMESPACE}" ]; then
  echo "ERROR: Could not determine OCI Object Storage namespace."
  exit 1
fi

echo "============================================"
echo " Uploading SOLA data to OCI Object Storage"
echo "--------------------------------------------"
echo " Namespace : ${NAMESPACE}"
echo " Bucket    : ${BUCKET_NAME}"
echo " Source    : ${PROCESSED_DIR}"
echo " Files     : ${#JSON_FILES[@]}"
echo "============================================"
echo

# ------------------------------------------------------------------------------
# Upload JSON files
# ------------------------------------------------------------------------------

for f in "${JSON_FILES[@]}"; do
  base="$(basename "${f}")"
  echo "Uploading ${base} ..."
  oci os object put \
    --bucket-name "${BUCKET_NAME}" \
    --namespace "${NAMESPACE}" \
    --file "${f}" \
    --name "${base}" \
    --content-type "application/json" \
    --force \
    >/dev/null
done

# ------------------------------------------------------------------------------
# Write a small version/metadata object
# ------------------------------------------------------------------------------

echo
echo "Writing meta/version.json ..."

TMP_META="$(mktemp)"
TIMESTAMP="$(date -Iseconds)"
HOSTNAME="$(hostname || echo 'unknown-host')"

cat > "${TMP_META}" <<EOF
{
  "deployed_at": "${TIMESTAMP}",
  "source_host": "${HOSTNAME}",
  "processed_dir": "data/processed",
  "comment": "Manual upload of SOLA data"
}
EOF

oci os object put \
  --bucket-name "${BUCKET_NAME}" \
  --namespace "${NAMESPACE}" \
  --file "${TMP_META}" \
  --name "meta/version.json" \
  --content-type "application/json" \
  --force \
  >/dev/null

rm -f "${TMP_META}"

echo
echo "✅ Upload completed."
echo "Bucket:  ${BUCKET_NAME}"
echo "Ns:      ${NAMESPACE}"
```

**Nicht vergessen:**

```bash
chmod +x tools/upload_data_to_oci.sh
```

Typischer Flow dann:

```bash
make import
tools/upload_data_to_oci.sh
```

---

## 2️⃣ `tools/fetch_data.py` – Download im Container beim Start

**Ziel:**
Dieser Code läuft im Container (oder optional lokal) und zieht die JSONs aus Object Storage nach `/app/data/processed`.

> Annahmen:
>
> * Image enthält das Python-Paket `oci`
> * Im Container sind gesetzt:
>
>   * `SOLA_DATA_BUCKET` (z.B. `sola-history-data`)
>   * **optional** `SOLA_DATA_NAMESPACE` (wenn nicht gesetzt, wird es via API geholt)
> * Auth im Container: **Instance Principals** (Container Instance) oder `config.from_file()` für lokalen Test

### 2.1 Datei `tools/fetch_data.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch processed SOLA data JSON files from OCI Object Storage and write them
to data/processed/ so that the Streamlit app can consume them.

Intended usage:
  - run in OCI (Container Instance or VM) with Instance Principals
  - optionally: run locally with an OCI CLI config (~/.oci/config)

Environment variables:
  SOLA_DATA_BUCKET     - name of the Object Storage bucket (default: sola-history-data)
  SOLA_DATA_NAMESPACE  - namespace; if not set, it is fetched via get_namespace()
"""

import os
import sys
from pathlib import Path

import oci


# Files we expect in the bucket
FILES = [
    "runners.json",
    "teams.json",
    "legs.json",
    "races.json",
    "results.json",
    "runners_overrides.json",  # optional, if you decide to keep overrides in Object Storage
]


def get_object_storage_client():
    """
    Try to create an ObjectStorageClient.

    Priority:
    1. Instance Principals (OCI runtime, e.g. Container Instance)
    2. Local config via ~/.oci/config (profile: DEFAULT)
    """
    # Try instance principals
    try:
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        # region is taken from instance metadata; the SDK usually picks that up
        cfg = {"region": signer.region}
        print(f"[fetch_data] Using Instance Principals (region={signer.region})")
        return oci.object_storage.ObjectStorageClient(config=cfg, signer=signer)
    except Exception as e:
        print(f"[fetch_data] Instance Principals not available ({e}), trying config file...")

    # Fallback: local config (~/.oci/config)
    try:
        cfg = oci.config.from_file()
        print(f"[fetch_data] Using config from ~/.oci/config (region={cfg.get('region')})")
        return oci.object_storage.ObjectStorageClient(config=cfg)
    except Exception as e:
        print(f"[fetch_data] ERROR: Could not create ObjectStorageClient via config file: {e}")
        raise


def main() -> int:
    base_dir = Path(__file__).resolve().parents[1]  # /app (assuming tools/ inside repo root)
    data_dir = base_dir / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)

    bucket_name = os.environ.get("SOLA_DATA_BUCKET", "sola-history-data")

    client = get_object_storage_client()

    # Determine namespace
    namespace = os.environ.get("SOLA_DATA_NAMESPACE")
    if namespace:
        print(f"[fetch_data] Using namespace from env: {namespace}")
    else:
        print("[fetch_data] No SOLA_DATA_NAMESPACE set, calling get_namespace() ...")
        ns_resp = client.get_namespace()
        namespace = ns_resp.data
        print(f"[fetch_data] Discovered namespace: {namespace}")

    print("============================================")
    print(" Fetching SOLA JSON data from Object Storage")
    print("--------------------------------------------")
    print(f" Namespace : {namespace}")
    print(f" Bucket    : {bucket_name}")
    print(f" Target    : {data_dir}")
    print("============================================")

    for name in FILES:
        try:
            print(f"[fetch_data] Downloading {name} ...")
            obj = client.get_object(namespace, bucket_name, name)
            target = data_dir / name
            target.write_bytes(obj.data.content)
            print(f"[fetch_data]   -> wrote {target}")
        except oci.exceptions.ServiceError as se:
            if se.status == 404:
                print(f"[fetch_data] WARNING: Object not found: {name} (status=404)")
            else:
                print(f"[fetch_data] ERROR: Could not fetch {name}: {se}", file=sys.stderr)
        except Exception as e:
            print(f"[fetch_data] ERROR: Unexpected error fetching {name}: {e}", file=sys.stderr)

    print("[fetch_data] Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

---

## 3️⃣ Dockerfile-Integration (kurze Erinnerung)

Damit `fetch_data.py` im Container funktioniert, musst du:

1. **`oci` ins Image installieren**
   → `requirements.txt` ergänzen oder direkt im Dockerfile:

```dockerfile
# im Builder-Stage:
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir fpdf oci || true
```

2. **`tools/` ins Image kopieren**

In deinem bestehenden Dockerfile (Runtime-Stage):

```dockerfile
WORKDIR /app

# libs aus builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# App-Code
COPY app.py ./app.py
COPY data/schema ./data/schema
COPY tools ./tools

RUN mkdir -p data/processed

EXPOSE 8501

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

CMD ["sh", "-c", "python tools/fetch_data.py && streamlit run app.py --server.port=8501 --server.address=0.0.0.0"]
```

3. **Env-Variablen beim Deployment setzen (OCI)**

Bei Container Instance oder Compose-File:

* `SOLA_DATA_BUCKET=sola-history-data`
* (optional) `SOLA_DATA_NAMESPACE=<dein-namespace>` – kann auch automatisch herausgefunden werden

---

## 4️⃣ Typischer Gesamt-Flow

Lokal:

```bash
# 1. Daten aus Excel neu generieren
make import

# 2. JSONs in Object Storage hochladen
tools/upload_data_to_oci.sh

# 3. Code ändern, committen, Tag setzen → CI/CD baut/pusht Image
#    (Workflow hatten wir ja vorhin)
```

OCI:

* Container neu starten:

  * Beim Start ruft er `fetch_data.py` auf
  * Holt die JSONs aus dem Bucket nach `/app/data/processed`
  * Startet Streamlit mit aktuellen Daten

---

Wenn du möchtest, können wir als nächstes:

* dein Dockerfile genau mit `fetch_data.py` & `oci` zusammenführen
* oder eine kleine ASCII-Zeichnung/Übersicht machen, wie **Excel → JSON → Object Storage → Container** zusammenhängt.

Alles klar, dann machen wir jetzt die „Big Picture“-Übersicht – so, dass du sie auch später in eine Doku oder Folien übernehmen kannst 🚀

---

## Gesamtarchitektur – Sola History (Code + Daten)

Ich teile es in **zwei Flüsse**:

1. **Datenfluss**: Excel → JSON → Object Storage → Container
2. **Codefluss**: GitHub → CI/CD → OCIR → Container

Am Ende treffen sich beide im Container in OCI.

---

## 1️⃣ Datenfluss – von Excel bis in den Container

```text
┌─────────────────────┐
│  Dein Laptop        │
│  (lokal)            │
└────────┬────────────┘
         │
         │ 1) Excel pflegen
         │    - data/raw/sola_history.xlsx
         │    - data/raw/sola_contacts.xlsx
         │
         ▼
┌────────────────────────────────┐
│ tools/import_excel.py          │
│  - liest Excel                 │
│  - normalisiert / rechnet um   │
│  - schreibt JSONs nach         │
│    data/processed/*.json       │
└────────────────────────────────┘
         │
         │ 2) JSONs stehen bereit
         │
         ▼
┌────────────────────────────────┐
│ tools/upload_data_to_oci.sh    │
│  - nutzt OCI CLI               │
│  - lädt alle JSONs nach        │
│    Object Storage:             │
│    Bucket: sola-history-data   │
│    (z.B. runners.json, ...)    │
└────────────────────────────────┘
         │
         │ 3) JSONs liegen nun zentral
         ▼
┌─────────────────────────────────────────┐
│ OCI Object Storage                      │
│ Bucket: sola-history-data               │
│  - runners.json                         │
│  - teams.json                           │
│  - races.json                           │
│  - legs.json                            │
│  - results.json                         │
│  - meta/version.json (Metadaten)        │
└─────────────────────────────────────────┘
```

Im **Container** läuft dann:

```text
┌────────────────────────────────┐
│  Container (OCI)               │
│  /app                          │
│                                │
│  tools/fetch_data.py           │
│   - beim Start ausgeführt      │
│   - holt JSONs aus             │
│     Bucket sola-history-data   │
│   - schreibt nach              │
│     /app/data/processed        │
│                                │
│  app.py (Streamlit)            │
│   - liest nur aus              │
│     data/processed/*.json      │
└────────────────────────────────┘
```

**Merke:**
Die App kennt nur `data/processed`.
Woher die Daten dorthin kommen, ist Aufgabe von `fetch_data.py` (im Container) und `upload_data_to_oci.sh` (bei dir lokal).

---

## 2️⃣ Codefluss – von GitHub bis zum laufenden Container

```text
┌──────────────────────┐
│  Github Repo         │
│  - app.py            │
│  - tools/*.py/.sh    │
│  - Dockerfile        │
│  - Makefile          │
│  - data/schema/*     │
└────────┬─────────────┘
         │
         │ 1) Commit / Push
         ▼
┌─────────────────────────────────────────┐
│ GitHub Actions (CI/CD)                  │
│  - baut Python-venv                     │
│  - installiert requirements.txt         │
│  - optional: Tests / Syntaxcheck        │
│  - baut Docker-Image                    │
│  - pusht Image nach Registry            │
└─────────────────────────────────────────┘
         │
         │ 2) Neues Image
         ▼
┌─────────────────────────────────────────┐
│ OCI Container Registry (OCIR)          │
│  z.B. eu-zurich-1.ocir.io/…/sola-history│
│  - Tags: v0.1.0, latest, …             │
└─────────────────────────────────────────┘
         │
         │ 3) Deployment
         ▼
┌─────────────────────────────────────────┐
│ Compute VM / Container Instance         │
│  - zieht Image aus OCIR                 │
│  - startet Container mit Env-Vars:      │
│      SOLA_APP_PASSWORD=...              │
│      SOLA_DATA_BUCKET=sola-history-data │
│      SOLA_DATA_NAMESPACE=... (optional) │
│  - Container ruft:                      │
│      python tools/fetch_data.py         │
│      streamlit run app.py               │
└─────────────────────────────────────────┘
```

---

## 3️⃣ Zusammenspiel – in einem Bild

Einmal alles zusammen:

```text
          LOKAL (bei dir)                            OCI (Cloud)
──────────────────────────────────        ──────────────────────────────────────
 Excel-Dateien                           Object Storage (Bucket)
  - sola_history.xlsx                      - runners.json
  - sola_contacts.xlsx                     - teams.json
        │                                   - results.json
        │                                   - ...
        ▼
 tools/import_excel.py
  → data/processed/*.json
        │
        │ tools/upload_data_to_oci.sh
        ▼
   OCI Object Storage  ◄─────────────────────────────┐
        ▲                                            │
        │ fetch_data.py                              │
        │                                            │
Container Image (Code)                       Compute/CI zieht Image
  - aus OCIR                                  - Docker/Container Instance
  - via CI/CD                                 - Env: SOLA_APP_PASSWORD, ...
        │                                     - Start: fetch_data.py → app.py
        ▼
  Laufende App (Streamlit)
  - liest nur data/processed/*.json
  - zeigt UI, Stats, Planung
```

---

Wenn du das so ungefähr im Kopf hast, ist alles andere (Dockerfile, oci-Config, CI-Details) „nur noch Umsetzung“.

Wenn du magst, können wir als nächstes:

* einen kleinen Abschnitt für deine `doc/README.md` formulieren („Architecture Overview“)
* oder deine bestehenden Docs (Root-README, `doc/ci_cd.md`) um diese Architektur ergänzen – dann hast du das sauber dokumentiert, bevor du weiter am Code schraubst.

Sehr gut, dann machen wir das Dockerfile jetzt „richtig“ – schlank, multi-stage, ohne Secrets, mit `fetch_data.py` integriert ✅

Ich gehe davon aus:

* `app.py` liegt im Repo-Root
* `tools/fetch_data.py` existiert wie von uns gebaut
* `data/schema/` existiert
* `data/processed/` wird **zur Laufzeit** gefüllt (nicht ins Image kopiert)
* Python-Abhängigkeiten stehen in `requirements.txt`

Hier das komplette Dockerfile, das du 1:1 übernehmen kannst:

```dockerfile
# ============================================================
# Stage 1: Builder
#  - installiert Python-Abhängigkeiten
# ============================================================
FROM python:3.11-slim AS builder

# Verzeichnis setzen
WORKDIR /app

# System-Pakete (nur was wir wirklich brauchen)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
 && rm -rf /var/lib/apt/lists/*

# Requirements ins Image kopieren
COPY requirements.txt .

# Python-Abhängigkeiten installieren
# - fpdf: für PDF-Export
# - oci: für Object Storage Zugriff
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir fpdf oci || true


# ============================================================
# Stage 2: Runtime
#  - nur das Nötigste aus dem Builder übernehmen
# ============================================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Zeitzone-Paket (falls du mit Zeiten arbeitest)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
 && rm -rf /var/lib/apt/lists/*

# Python-Runtime + installierte Pakete aus dem Builder übernehmen
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# App-Code kopieren
COPY app.py ./app.py
COPY tools ./tools
COPY data/schema ./data/schema

# Laufzeit-Verzeichnis für Daten (wird per fetch_data.py/Object Storage gefüllt
# oder als Volume gemountet)
RUN mkdir -p data/processed

# Environment-Defaults (keine Secrets!)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Port für Streamlit
EXPOSE 8501

# Start-Kommando:
# 1) Daten aus Object Storage holen (tools/fetch_data.py)
# 2) Streamlit-App starten
CMD ["sh", "-c", "python tools/fetch_data.py && streamlit run app.py --server.port=8501 --server.address=0.0.0.0"]
```

---

### Wie passt das in deinen Flow?

**Build lokal:**

```bash
docker build -t sola-history:latest .
```

**Run lokal mit Daten aus Volume (ohne Object Storage):**

```bash
docker run --rm -p 8501:8501 \
  -e SOLA_APP_PASSWORD=sola \
  -v $(pwd)/data/processed:/app/data/processed:ro \
  sola-history:latest
```

**Run in OCI mit Object Storage:**

* Env vars setzen:

  * `SOLA_APP_PASSWORD=…`
  * `SOLA_DATA_BUCKET=sola-history-data`
  * optional `SOLA_DATA_NAMESPACE=<dein-namespace>`
    (sonst ermittelt `fetch_data.py` das selbst)

* Container Instance / Compose-Definition zeigt einfach auf dieses Image – `fetch_data.py` holt die JSONs beim Start.

---

Wenn du mir später noch dein aktuelles `docker-compose.yml` zeigst, kann ich es dir auch direkt auf dieses Dockerfile + OCI-Deployment trimmen (lokal & remote kompatibel).

Perfekt — dann definieren wir jetzt **die saubere, professionelle Repo-Struktur** für **zwei getrennte Repositories**:

1️⃣ **sola-history-app** → enthält *nur Code*, kein einziges personenbezogenes Datum
2️⃣ **sola-history-data** → enthält *Datenpipelines*, aber **keine Rohdaten**, sondern nur Tools für Daten-Upload/Download

➡️ Die echten Rohdaten (`sola_contacts.xlsx`, `sola_history.xlsx`, Ergebnisse etc.) bleiben **lokal oder in OCI Object Storage**, aber **niemals im Git**.

---

# 📁 **Repository 1: sola-history-app**

🔹 *enthält die App, das Dockerfile, die Import-Tools & die Daten-Schemata — aber keine echten Daten*

```
sola-history-app/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
├── README.md
│
├── data/
│   ├── schema/
│   │   └── sola.schema.json
│   │
│   └── processed/              # Wird zur Laufzeit gefüllt!
│       ├── runners.json        # NICHT im Repo!
│       ├── teams.json
│       ├── results.json
│       ├── legs.json
│       ├── races.json
│
├── tools/
│   ├── import_excel.py         # Parser (lokal genutzt)
│   ├── fetch_data.py           # Holt JSONs aus OCI
│   ├── upload_data_to_oci.sh   # Upload Script (optional)
│   ├── test.py
│   └── README.md
│
└── ci/
    ├── build.yml               # GitHub Actions → Docker Build & Push
    └── security.yml            # Dependabot, Linting, Security Checks
```

### 🔒 Was geht *NICHT* in dieses Repo?

❌ `sola_history.xlsx`
❌ `sola_contacts.xlsx`
❌ irgendeine JSON-Datei mit Personen oder Laufdaten
❌ Secrets (OCI Keys, Passwörter)

**→ Nur Tools & Schemas. Keine echten Daten.**

---

# 📁 **Repository 2: sola-history-data**

🔹 *dient als Datenverwaltung, Upload-Tools, Validierung und Data Governance*

```
sola-history-data/
├── README.md
│
├── raw/                          # Rohdaten (NIE ins Repo!)
│   ├── sola_history.xlsx
│   ├── sola_contacts.xlsx
│   └── previous_years/
│
├── processed/                    # Output nach import_excel.py
│   ├── runners.json
│   ├── teams.json
│   ├── results.json
│   ├── legs.json
│   ├── races.json
│
├── tools/
│   ├── import_excel.py          # identisch wie in App-Repo
│   ├── validate_schema.py       # optional JSON Validator
│   ├── upload_data_to_oci.sh    # Daten nach OCI pushen
│   └── diff_data.py             # Vergleicht alte/neue Daten
│
└── ci/
    ├── validate.yml             # Check Excel, Check JSON Schema
    └── publish.yml              # Publish processed JSONs to OCI bucket
```

🧠 **Wichtig:**
Dieses Repo ist **PRIVATE ONLY** – aber auch hier *keine personenbezogenen Rohdaten ins Git*.

Die Rohdaten liegen lokal oder in OCI, und werden durch `upload_data_to_oci.sh` automatisiert ins Bucket geschrieben.

---

# 🎯 Zweck der Trennung

| Bereich                      | sola-history-app | sola-history-data |
| ---------------------------- | ---------------- | ----------------- |
| App-Code                     | ✔️               | ❌                 |
| Dockerfile                   | ✔️               | ❌                 |
| Streamlit                    | ✔️               | ❌                 |
| Daten-Import                 | ✔️ (Tools)       | ✔️                |
| JSON-Schema                  | ✔️               | ✔️                |
| Personen-/Laufdaten JSON     | ❌                | ✔️                |
| Rohdaten Excel               | ❌                | ❌ (nur lokal)     |
| CI/CD → App Deployment       | ✔️               | ❌                 |
| CI/CD → Data Upload nach OCI | ❌                | ✔️                |

---

# 🚛 Datenflow (End-to-End)

### **Local → Data Repo → OCI → App Repo → Container → Runtime**

```
Excel → import_excel.py → processed JSON → upload_data_to_oci.sh
                                          ↓
                                 OCI Object Storage (Bucket)
                                          ↓
                                sola-history-app Container
                                 runs fetch_data.py on startup
                                          ↓
                                   /app/data/processed/*
                                 Streamlit UI uses JSON
```

---

# 🧩 CI/CD Empfehlungen

### **sola-history-app CI/CD**

* Build Docker Image (GitHub Actions)
* Push to GitHub Container Registry (GHCR)
* Optional: Push to OCI Registry (`iad.ocir.io/...`)
* Trigger deployment auf OCI:

  * Container Instance
  * Functions
  * Kubernetes (OKE)
  * Container Apps

### **sola-history-data CI/CD**

* Validate Excel (Header, Zeitformate, Runner IDs)
* Generate JSON using import_excel.py
* Validate JSON against schema
* Upload JSON → OCI Object Storage

---

# 🧱 Was muss dokumentiert werden?

### In sola-history-app/README.md

* Run local
* Run via compose
* Build Docker
* Start in OCI
* Data loading (fetch_data.py)

### In sola-history-data/README.md

* Wie Excel strukturiert sein muss
* Import Workflow
* JSON Output Beschreibung (fields)
* Upload nach OCI
* Governances (keine Rohdaten im Repo)

---

# ✔️ Bereit für den nächsten Schritt

Wenn du möchtest, kann ich jetzt für dich erzeugen:

### ✅ Vollständige GitHub READMEs (beide Repos)

### ✅ GitHub Actions CI/CD Workflows

### ✅ Terraform für OCI deployment

### ✅ Daten-Governance-Beschreibung

### ✅ Branching- und Release-Konzept

Sag mir einfach, womit wir weitermachen wollen.


Alles klar — hier kommt **Teil 1/2** der Lieferung:
➡️ **Komplette, einsatzbereite READMEs für beide Repos**
➡️ **Komplette GitHub Actions Workflows für Build/Deploy & Data Pipeline**

**Teil 2** (Terraform, Governance, Branching, Release-Konzept) sende ich direkt danach.

---

# ✅ **1. README für Repo: `sola-history-app`**

(Datei: `README.md`)

---

# 🏃‍♂️ **SOLA History – App Repository**

Interne Analytics- & Planungslösung für Accenture/Trivadis SOLA-Läufe

Dieses Repository enthält **nur die Anwendung** (Streamlit App), Dockerfiles, CI/CD und Tools für den Import der verarbeiteten JSON-Dateien.
**Wichtig:** Hier liegen **keine personenbezogenen Rohdaten** und auch **keine gefertigten JSONs** im Git.

---

# 📁 Repository Structure

```
sola-history-app/
├── app.py                     # Main Streamlit Application
├── Dockerfile                 # Multi-stage OCI-ready build
├── docker-compose.yml         # Local dev runner
├── Makefile                   # Local build/test automation
├── requirements.txt
│
├── data/
│   ├── schema/                # JSON schema definitions
│   │    └── sola.schema.json
│   └── processed/             # (Filled at runtime; NOT in Git)
│
├── tools/
│   ├── import_excel.py        # Parser (local-only)
│   ├── fetch_data.py          # Loads data from OCI bucket at app startup
│   ├── upload_data_to_oci.sh  # CI tool for deployments
│   └── test.py
│
└── .github/
    └── workflows/
        ├── build.yml          # Docker Build & Push
        └── lint.yml           # Optional: Code quality
```

---

# 🚀 Running locally

### 1) Install dependencies

```bash
make install
```

### 2) Import processed JSONs

(Nur wenn du lokal Excel importieren willst)

```bash
make import
```

### 3) Start Streamlit

```bash
make run
```

---

# 🐳 Running via Docker Compose

```bash
docker compose up --build
```

Die App läuft dann unter:
➡️ [http://localhost:8501](http://localhost:8501)

---

# 📦 Docker Build (Multi-Stage, Slim)

```bash
docker build -t sola-history:latest .
```

Das Image ist ~200–250 MB groß dank Multi-Stage & Slim-Base.

---

# 🔐 Handling Data (safe workflow)

Die App lädt beim Start über `tools/fetch_data.py` alle JSONs automatisch:

* `runners.json`
* `teams.json`
* `results.json`
* `races.json`
* `legs.json`

→ aus **OCI Object Storage**

Die Daten liegen **nicht im Container-Image**, sondern werden **beim Start nachgeladen**.

---

# 🛠 CI/CD (GitHub Actions)

Dieses Repo erzeugt:

* Docker Image → **GHCR**
* Optional: Push in OCI Registry
* Optional: Deployment (Container Instance, OKE oder Container Apps)

Workflows liegen unter `.github/workflows/`.

---

# 🔗 Required environment variables (for deployment)

| Variable               | Description                  |
| ---------------------- | ---------------------------- |
| `OCI_BUCKET_NAMESPACE` | OCI namespace                |
| `OCI_BUCKET_NAME`      | Bucket name containing JSONs |
| `OCI_BUCKET_REGION`    | Region                       |
| `OCI_BUCKET_URL`       | Prebuilt HTTPS URL           |
| `SOLA_APP_PASSWORD`    | App login                    |

---

# ✔️ Recommended Setup

* Dieses App-Repo bleibt **öffentlich möglich**, aber ohne Daten.
* Alle personenbezogenen Daten kommen **aus dem Data-Repo** oder OCI-Bucket.
* Deployment in OCI basiert auf CI/CD Workflow.

---

# 🎯 End of README for sola-history-app

---

# ✅ **2. README für Repo: `sola-history-data`**

(Datei: `README.md`)

---

# 🗂️ SOLA History – Data Repository

Dieses Repository verwaltet **alle Datenprozesse**:

* Rohdaten (werden **nicht eingecheckt**)
* Import der Excel-Dateien
* Generieren der JSON-Ausgabedaten
* Validieren per JSON-Schema
* Upload nach OCI Object Storage
* Automatisierte Data-Pipeline (CI/CD)

---

# 📁 Repository Structure

```
sola-history-data/
├── raw/                      # NEVER in Git
│   ├── sola_history.xlsx
│   ├── sola_contacts.xlsx
│   └── previous_years/
│
├── processed/                # JSON Outputs (generated)
│   ├── runners.json
│   ├── results.json
│   ├── teams.json
│   ├── races.json
│   └── legs.json
│
├── tools/
│   ├── import_excel.py       # Build JSONs from Excel
│   ├── validate_schema.py    # Ensure data matches schema
│   ├── upload_data_to_oci.sh # Upload processed JSON → OCI
│   ├── diff_data.py          # Compare old/new output
│   └── README.md
│
└── .github/
    └── workflows/
        ├── validate.yml      # Validate Excel/JSON
        └── publish.yml       # Upload JSONs to OCI
```

---

# 🚀 Workflow

## Schritt 1: Rohdaten vorbereiten

Die Excel-Dateien liegen lokal in:

```
raw/sola_history.xlsx
raw/sola_contacts.xlsx
```

⚠️ **Diese Dateien dürfen NICHT ins Git!**

---

## Schritt 2: JSON generieren

```bash
python tools/import_excel.py
```

Output landet in `processed/`.

---

## Schritt 3: Daten validieren (Schema)

```bash
python tools/validate_schema.py
```

---

## Schritt 4: Upload nach OCI

```bash
tools/upload_data_to_oci.sh processed/*.json
```

Dies aktualisiert die Daten, die das App-Repo konsumiert.

---

# 🔐 OCI Requirements

* OCI Tenancy OCID
* User OCID
* API Key
* Bucket Name
* Namespace
* Region

Alle Werte müssen als GitHub Secrets gespeichert werden:

| Secret             | Description            |
| ------------------ | ---------------------- |
| `OCI_USER_OCID`    | API user               |
| `OCI_TENANCY_OCID` | Tenancy                |
| `OCI_FINGERPRINT`  | Public key fingerprint |
| `OCI_PRIVATE_KEY`  | PEM private key        |
| `OCI_REGION`       | Region                 |
| `OCI_BUCKET`       | Data bucket            |

---

# 🤖 CI/CD Pipeline

## validate.yml

* prüft Excel Struktur
* prüft Schema
* prüft Python-Code
* erzeugt Artefakte

## publish.yml

* führt Import durch
* erzeugt JSONs
* validated JSON
* lädt JSONs nach OCI hoch

---

# 🎯 End of README for sola-history-data

---

# ✅ **3. GitHub Actions Workflow für App-Repo**

### Datei: `.github/workflows/build.yml`

```yaml
name: Build & Publish App

on:
  push:
    branches: ["main"]
  pull_request:

permissions:
  contents: read
  packages: write

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build Docker Image
        run: |
          docker build -t ghcr.io/${{ github.repository }}:latest .

      - name: Push Docker Image
        run: |
          docker push ghcr.io/${{ github.repository }}:latest
```

(Optional: OCI Registry Push kann ergänzt werden.)

---

# ✅ **4. GitHub Actions Workflow für Data-Repo**

### Datei: `.github/workflows/publish.yml`

```yaml
name: Publish Processed Data

on:
  workflow_dispatch:
  push:
    branches: ["main"]

jobs:
  publish:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install Dependencies
        run: |
          pip install -r requirements.txt

      - name: Run Data Import
        run: |
          python tools/import_excel.py

      - name: Validate JSON Schema
        run: |
          python tools/validate_schema.py

      - name: Upload JSON to OCI
        env:
          OCI_TENANCY_OCID: ${{ secrets.OCI_TENANCY_OCID }}
          OCI_USER_OCID: ${{ secrets.OCI_USER_OCID }}
          OCI_FINGERPRINT: ${{ secrets.OCI_FINGERPRINT }}
          OCI_PRIVATE_KEY: ${{ secrets.OCI_PRIVATE_KEY }}
          OCI_REGION: ${{ secrets.OCI_REGION }}
          OCI_BUCKET: ${{ secrets.OCI_BUCKET }}
        run: |
          bash tools/upload_data_to_oci.sh processed/*.json
```

---

# 🎉 **Bereit für Teil 2?**

Ich liefere dir jetzt:

### 📌 Terraform-Deployment-Draft (Container Instance + Bucket Zugriff)

### 📌 Security & Governance Konzept

### 📌 Branching/Release-Konzept

### 📌 Übersicht über Verantwortlichkeiten & Data Ownership

Sobald du ready bist:
👉 **„Weiter mit Teil 2“**


Sehr gute Zwischenfrage – das Nginx-Thema passt perfekt in Teil 2 rein 😄
Ich packe alles strukturiert:

1. Einfacher **Nginx Reverse Proxy mit SSL + Let’s Encrypt + Basic Auth** (VM + Docker Compose)
2. **Terraform-Draft** für OCI (VM + VCN + Security)
3. **Security & Data-Governance-Skizze**
4. **Branching- & Release-Konzept** (App-Repo & Data-Repo)

---

## 1️⃣ Nginx Reverse Proxy + SSL + Basic Auth (einfach mit Docker Compose)

### Zielbild

* Eine kleine OCI-VM (Oracle Linux / Ubuntu)
* Darauf läuft per `docker-compose`:

  * `proxy` (nginx, Termination von HTTPS, Basic Auth)
  * `certbot` (holt/erneuert Let’s-Encrypt-Zertifikate)
  * `sola-history` (deine Streamlit-App, nur intern erreichbar)

### a) Beispiel `docker-compose.yml` auf der VM

```yaml
version: "3.9"

services:
  sola-history:
    image: ghcr.io/<dein-github-user>/sola-history-app:latest
    container_name: sola-history
    restart: unless-stopped
    environment:
      - SOLA_APP_PASSWORD=${SOLA_APP_PASSWORD}
      - SOLA_DATA_BUCKET=sola-history-data
      - SOLA_DATA_NAMESPACE=<dein-namespace>
    expose:
      - "8501"
    networks:
      - backend

  proxy:
    image: nginx:alpine
    container_name: sola-proxy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/htpasswd:/etc/nginx/htpasswd:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    networks:
      - backend

  # certbot wird "on demand" gestartet (nicht dauerhaft)
  certbot:
    image: certbot/certbot
    container_name: sola-certbot
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt
      - ./nginx/conf.d:/etc/nginx/conf.d
    entrypoint: /bin/sh
    command: "-c 'sleep infinity'"

networks:
  backend:
    driver: bridge
```

> **Hinweis:**
>
> * TLS-Zertifikate liegen in `/etc/letsencrypt` auf der VM
> * `nginx/conf.d` enthält deine `server`-Configs
> * `nginx/htpasswd` enthält die Basic-Auth-User

---

### b) Nginx-Config (`nginx/conf.d/sola.conf`)

```nginx
server {
    listen 80;
    server_name sola.example.com;

    # Redirect everything to HTTPS
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name sola.example.com;

    ssl_certificate     /etc/letsencrypt/live/sola.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sola.example.com/privkey.pem;

    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    # Basic Auth (zusätzlich zu App-Passwort)
    auth_basic           "Restricted Sola History";
    auth_basic_user_file /etc/nginx/htpasswd/sola_users;

    location / {
        proxy_pass         http://sola-history:8501;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

---

### c) Basic Auth User anlegen

Auf der VM (nicht im Container):

```bash
mkdir -p nginx/htpasswd
docker run --rm -it httpd:alpine htpasswd -nbB sola-admin 'DeinStarkesPasswort' \
  > nginx/htpasswd/sola_users
```

=> Nginx fragt dann HTTP Basic Auth ab **vor** der App.

---

### d) Let’s Encrypt – erster Cert-Request (ganz kurz)

1. Einmalig Verzeichnis für Webroot anlegen:

```bash
sudo mkdir -p /var/www/certbot
sudo chown -R $USER /var/www/certbot
```

2. Temporäre Nginx-Config für ACME-Challenge (oder bestehenden 80er-Serverblock wie oben nutzen).

3. Certbot im Container einmal manuell laufen lassen:

```bash
docker run --rm -it \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/www/certbot:/var/www/certbot \
  certbot/certbot certonly \
    --webroot \
    -w /var/www/certbot \
    -d sola.example.com \
    --email deine@mailadresse \
    --agree-tos \
    --no-eff-email
```

4. Danach `docker compose up -d` → Nginx sieht die Zertifikate in `/etc/letsencrypt/live/sola.example.com/`.

5. **Renewal** kann später mit Cron oder einem kleinen `certbot renew`-Container gemacht werden.

Für deinen Scope reicht erstmal: **manuell erstellen, gelegentlich erneuern**.

---

## 2️⃣ Terraform-Draft – OCI Compute + VCN + Security

Wir nehmen das Setup: **eine VM mit Public-IP**, darauf läuft dein `docker-compose` mit nginx + App.

### a) `variables.tf` (Vereinfacht)

```hcl
variable "compartment_ocid" {
  description = "OCI Compartment OCID"
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key for opc user"
  type        = string
}

variable "region" {
  description = "OCI Region"
  type        = string
  default     = "eu-zurich-1"
}

variable "cidr_vcn" {
  description = "VCN CIDR"
  type        = string
  default     = "10.20.0.0/16"
}

variable "cidr_subnet" {
  description = "Subnet CIDR"
  type        = string
  default     = "10.20.10.0/24"
}
```

---

### b) `main.tf` (stark gekürzt, als Draft)

```hcl
provider "oci" {
  region = var.region
}

# VCN
resource "oci_core_vcn" "sola_vcn" {
  cidr_block     = var.cidr_vcn
  compartment_id = var.compartment_ocid
  display_name   = "sola-vcn"
}

resource "oci_core_internet_gateway" "igw" {
  compartment_id = var.compartment_ocid
  display_name   = "sola-igw"
  vcn_id         = oci_core_vcn.sola_vcn.id
  enabled        = true
}

resource "oci_core_route_table" "rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.sola_vcn.id
  display_name   = "sola-rt"

  route_rules {
    network_entity_id = oci_core_internet_gateway.igw.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }
}

resource "oci_core_subnet" "public_subnet" {
  compartment_id      = var.compartment_ocid
  vcn_id              = oci_core_vcn.sola_vcn.id
  cidr_block          = var.cidr_subnet
  display_name        = "sola-public-subnet"
  route_table_id      = oci_core_route_table.rt.id
  dns_label           = "solapub"
  prohibit_public_ip_on_vnic = false
}

# Security List: 22, 80, 443 von deinem Netz
resource "oci_core_security_list" "sl_public" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.sola_vcn.id
  display_name   = "sola-sl-public"

  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 80
      max = 80
    }
  }

  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 443
      max = 443
    }
  }

  # optional: SSH nur von deiner IP
  ingress_security_rules {
    protocol = "6"
    source   = "<DEINE-IP>/32"
    tcp_options {
      min = 22
      max = 22
    }
  }

  egress_security_rules {
    protocol = "all"
    destination = "0.0.0.0/0"
  }
}

# Compute Instance
resource "oci_core_instance" "sola_vm" {
  compartment_id = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name   = "sola-history-vm"

  shape = "VM.Standard.E3.Flex"
  shape_config {
    ocpus         = 1
    memory_in_gbs = 4
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.public_subnet.id
    display_name     = "sola-vnic"
    assign_public_ip = true
    hostname_label   = "sola"
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key

    # optional: cloud-init, um Docker & docker-compose vorzuinstallieren
    user_data = base64encode(<<EOF
#cloud-config
packages:
  - docker
runcmd:
  - systemctl enable docker
  - systemctl start docker
EOF
    )
  }

  source_details {
    source_type = "image"
    # Oracle Linux 8/9 Image OCID für deine Region eintragen
    source_id   = "<ORACLE_LINUX_IMAGE_OCID>"
  }
}
```

Damit hast du:

* VCN + Subnet
* Internet Gateway
* Security List
* VM mit Public-IP

Alles weitere: via SSH auf die VM → `docker-compose.yml` deployen → `docker compose up -d`.

---

## 3️⃣ Security & Data-Governance – Kurzfassung

### a) Daten-Trennung

* **App-Repo** (sola-history-app):

  * Kein PII, keine JSONs mit echten Namen
  * Nur Code, Schema, Tools
* **Data-Repo** (sola-history-data):

  * Tools & Pipelines
  * Rohdaten **nicht im Git**, nur lokal / verschlüsselt

### b) Object Storage Governance

* **Bucket `sola-history-data`**:

  * Server-side encryption (Standard in OCI)
  * IAM-Policy:

    * Nur definierte Gruppen / Dynamic Groups dürfen lesen
    * Schreibrechte nur von Data-Pipeline / Admin
* **Dynamic Group** für Compute-Instances/Container Instances:

  * „darf `get_object` auf Bucket ausführen“

### c) Secrets & Credentials

* Keinerlei Passwörter/Keys im Git:

  * `SOLA_APP_PASSWORD` → OCI Vault Secret oder GitHub Secret
  * OCI API Keys → GitHub Secrets (nur im Data-Repo)
* Nginx Basic Auth:

  * `.htpasswd` nur auf der VM (nicht im Git)

### d) Logging & Monitoring

* Nginx-Logs: Zugriff überwachen (IP, Pfade, Statuscodes)
* App-Logs: im Container, optional in OCI Logging einspeisen
* Keine sensiblen Daten in Logs (keine E-Mails, keine Telefone loggen)

---

## 4️⃣ Branching & Release-Konzept

### a) App Repo (`sola-history-app`)

**Branches:**

* `main`: stabil, Produktion
* `develop`: Integration / neue Features
* `feature/*`: kurzlebige Feature-Branches

**Releases:**

* Tags wie `v1.0.0`, `v1.1.0`, …
* GitHub Action baut & pusht Image mit Tag:

  * `ghcr.io/<user>/sola-history-app:latest`
  * `ghcr.io/<user>/sola-history-app:v1.1.0`

**Deployment:**

* Prod-Deployment triggert auf Tag `v*`
* Optional: Staging-Instance mit `develop`-Image

---

### b) Data Repo (`sola-history-data`)

Daten ändern sich seltener und sind versioniert eher **zeitbasiert** als „Feature“.

**Branches:**

* `main`: aktueller Datenstand
* `datafix/*`: temporäre Branches für Korrekturen

**Tags/Snapshots:**

* `data-YYYYMMDD`
  z.B. `data-2025-05-10` = Stand der JSONs nach SOLA 2025.

**Pipeline:**

* Push auf `main` oder manuelles `workflow_dispatch`:

  * `import_excel.py`
  * `validate_schema.py`
  * `upload_data_to_oci.sh` → Bucket `sola-history-data`

Die App holt sich immer die „aktuelle“ Variante (z.B. `latest.json` im Bucket).
Wenn du Snapshots willst, kannst du Prefixe nutzen:

* `current/runners.json`
* `snapshots/2025-05-10/runners.json`

---

Wenn du magst, können wir als Nächstes:

* dein **konkretes `docker-compose.yml`** für die VM fertigstellen (inkl. Proxy, App, Certbot)
* oder ein kleines `doc/architecture.md` schreiben, das genau diese Punkte (App, Data, Nginx, OCI) auf 1–2 Seiten zusammenfasst.



Hier ist **eine saubere, professionelle und sofort verwendbare**
`doc/architecture.md` für dein Projekt – klar strukturiert, vollständig, GitHub-ready.

---

# `doc/architecture.md`


---

Wenn du willst, kann ich zusätzlich erstellen:

✅ `doc/deployment.md`
✅ vollständige Terraform-Module
✅ komplettes `docker-compose.yml` für die VM
✅ GH Actions für App + Data
✅ Sicherheitskonzept (ISO 27001-like)

Sag einfach *"Bitte Teil 2"* oder *"mach deployment.md"* 😊


Kurz & klar — **ja**, du kannst die Sola-History-App **vollständig auf einer OCI Free Tier VM** betreiben.
Hier ist der **saubere Entscheidungsrahmen**, inklusive DNS-Strategie, SSL, Kosten & Best Practices.

---

# ✅ 1. Kann die VM „Always Free“ sein?

**Ja.**
Die App ist:

* CPU-leicht
* Speicherleicht (~100–300 MB RAM)
* Keine hohe Last
* Kein starker I/O

👉 Die **OCI Free Tier VM.Standard.A1.Flex (Arm)** ist perfekt.

### **Empfohlene Specs**

| Component   | Value                                      |
| ----------- | ------------------------------------------ |
| Shape       | **VM.Standard.A1.Flex** (Arm, Always Free) |
| CPUs        | 1 OCPU                                     |
| Memory      | 2–4 GB                                     |
| Boot Volume | 50 GB (Always Free erlaubt bis zu 200 GB)  |
| OS          | Oracle Linux 8 / 9                         |

Kosten: **0 CHF / 0 EUR**
→ Free Tier.

---

# ✅ 2. DNS / Hostname — 3 mögliche Varianten

## **Option A — Kostenlos via xip.io / sslip.io (simpel)**

Du brauchst *keine eigene Domain*.

**Beispiel:**

```
https://130-61-42-100.sslip.io
```

SSL funktioniert via Let's Encrypt → **funktioniert 100% ohne zusätzliche Konfiguration**.

**Vorteile:**

* Kein Domain-Kauf
* Einfach
* Let's Encrypt funktioniert

**Nachteile:**

* Nicht „schön“
* Kein Branding

👉 **Für schnellen Start absolut ideal.**

---

## **Option B — Eigene Domain (empfohlen für langfristig)**

Du nutzt z.B.:

```
sola.oehrlis.ch
sola-history.ch
history.sola-runs.com
```

### Schritte:

1. Domain kaufen (falls nicht vorhanden)
2. A-Record auf öffentliche IP der OCI VM
3. Nginx + Certbot generiert SSL automatisch

**Kosten:** Domain ~10–15 CHF/Jahr
**Vorteile:** Professioneller, stabil.

---

## **Option C — OCI DNS (kostenpflichtig in Enterprise)**

Nur sinnvoll bei mehreren Zonen oder komplexem Setup.

➡️ **Für dein Projekt nicht nötig.**

---

# ✅ 3. Wie läuft SSL auf der Free Tier VM?

Du hast zwei Varianten:

---

## Variante 1 — **Certbot im Container (empfohlen)**

`docker-compose.yml`:

```
nginx
certbot
sola-history-app
```

Workflow:

1. Certbot holt Let's Encrypt Zertifikate
2. Nginx lädt sie
3. Cron / certbot renew automatisch

Kosten: **0**

---

## Variante 2 — OCI Loadbalancer (Nicht Free Tier)

**Nicht nötig**, ausser du willst später skalieren.

---

# ✅ 4. Wie sieht ein typisches Deployment aus?

```
Incoming User
    │
HTTPS (443)
    ▼
Nginx Reverse Proxy (on VM)
    ▼
sola-history-app container (Streamlit)
    ▼
OCI Object Storage (data bucket)
```

Alles auf **einer Free Tier VM**.

---

# ✅ 5. DNS decision — What should YOU choose?

### ⭐ Empfehlung für dich:

### **Phase 1 – Development / Internal Use**

➡️ Nutze **sslip.io**

Beispiel:

```
https://130-61-42-100.sslip.io
```

### **Phase 2 – Public or Team Deployment**

➡️ Domain:

```
sola-history.ch
sola.oehrlis.ch
sola-team.ch
```

Kosten minimal, Wirkung groß.

---

# ✅ 6. Konkreter Umsetzungsvorschlag

### 6.1 Reserviere statische IP in OCI

```
Public IP: 130.61.42.100
```

### 6.2 Use DNS hostname

```
sola.130-61-42-100.sslip.io
```

### 6.3 docker-compose bereitstellen:

```
app
nginx
certbot
```

### 6.4 Certbot generiert Zertifikate:

```
certbot certonly --webroot -w /var/www/certbot -d 130-61-42-100.sslip.io
```

### 6.5 Your app is now accessible:

```
https://130-61-42-100.sslip.io
```

Gratis, stabil, ohne Domain.

---

# ❓ Was möchtest du nutzen?

Ich empfehle folgende Frage:

## **Möchtest du:**

1. **Kostenlos starten** → sslip.io
2. **Professionelles Deployment** → eigene Domain
3. **Ich schlage eine Domain vor, die zu deinem Projekt passt**
4. **Wildcard domain** (falls du später mehrere Services planst)

---

# 🌟 Bonus: Wenn du willst, mache ich dir direkt:

✓ fertiges DNS-Setup (für Option A oder B)
✓ fertiges docker-compose für Nginx/Certbot/App
✓ README für Deployment
✓ Terraform für vollständige VM-Provisionierung

Sag einfach:

👉 **“Bitte Deployment-Paket erstellen”**

Perfekt — **oradba.ch** ist eine hervorragende Domain für das Projekt.
Damit lässt sich ein **sauberes, professionelles und dennoch simples Deployment** aufbauen.

---

# ✅ Empfehlung für deine Subdomain

Du willst etwas **kurzes**, **eindeutiges** und **ohne Konflikte** in Zukunft.

Ich schlage drei Varianten vor:

### **1️⃣ sola.oradba.ch**

Kurz, eindeutig, gut merkbar.
→ *Empfehlung Nr. 1*

### **2️⃣ history.sola.oradba.ch**

Falls du später weitere SOLA-Dienste baust.

### **3️⃣ sola-history.oradba.ch**

Selbsterklärend, etwas länger.

👉 **Meine klare Empfehlung:**

### ⭐ **`sola.oradba.ch`**

---

# 🔧 Schritte für die Subdomain

## **Step 1 — Statische IP der Free Tier VM reservieren**

In OCI:

```
Networking → Public IPs → Reserve Public IP
```

Beispiel:

```
Public IP: 130.61.42.100
```

---

## **Step 2 — DNS-Record in oradba.ch anlegen**

Bei deinem DNS-Provider (vermutlich hosttech oder cloudflare):

### **A-Record:**

| Type | Name           | Value         | TTL  |
| ---- | -------------- | ------------- | ---- |
| A    | sola.oradba.ch | 130.61.42.100 | auto |

---

## **Step 3 — SSL/HTTPS einrichten**

Mit **Nginx + Certbot** im Docker-Compose (kostet 0 CHF).

### Certbot holt Zertifikat:

```
certbot --nginx -d sola.oradba.ch
```

Oder via Webroot:

```
certbot certonly --webroot -w /var/www/certbot -d sola.oradba.ch
```

---

# 📦 Was ich dir als Nächstes bauen kann

Wenn du sagst **„Go“**, erstelle ich vollständig:

---

## **1. Auslieferbares Deployment-Paket (ready to copy)**

### docker-compose.yml

✔ sola-history-app
✔ nginx reverse proxy
✔ certbot
✔ automatische SSL-Erneuerung
✔ Healthchecks
✔ Logging

---

## **2. Fertiges nginx.conf**

Mit:

* SSL
* Reverse Proxy
* Rate limiting
* Gzip
* Basic Auth möglich

---

## **3. domain-specific README.md**

```
How to deploy sola.oradba.ch on OCI Free Tier
```

Mit allen Befehlen:

* Reserviere IP
* DNS setzen
* Server härten
* Certbot aktivieren
* Logs prüfen

---

## **4. Optional: Terraform Modul**

Damit bekommst du:

* VM
* Security List
* Public IP
* Cloud-Init Deployment
* Docker + Compose Install

Alles in einem Befehl:

```
terraform apply
```

---

# 💬 Noch 2 Fragen bevor ich das Deployment-Paket erstelle:

### **1️⃣ Welche Subdomain möchtest du verwenden?**

* sola.oradba.ch
* sola-history.oradba.ch
* history.sola.oradba.ch
* etwas anderes?

👉 *Ich empfehle:* **sola.oradba.ch**

---

### **2️⃣ Möchtest du Basic Auth zusätzlich zum App-Passwort?**

(z. B. doppelte Absicherung über nginx)

Optionen:

| Option                    | Beschreibung                    |
| ------------------------- | ------------------------------- |
| 🔐 **Basic Auth (nginx)** | Benutzer + Passwort vor der App |
| 🔓 Nur App-Passwort       | Einfacher, aber weniger sicher  |
| 🔑 OAuth (Google Login)   | Komfortabel, aber mehr Aufwand  |

---

Sobald du antwortest, mache ich:

👉 **„Deployment Package – sola.oradba.ch“**
inkl. aller Dateien & Dokumentation.

Sehr cool, dann machen wir jetzt ein **konkretes Deployment Package für `sola.oradba.ch`** – ohne Basic Auth (kommt später), nur mit:

* Free Tier VM auf OCI
* Docker + docker-compose
* Nginx als Reverse Proxy mit HTTPS (Let’s Encrypt)
* Deinem Sola-App-Container

Ich baue dir das so, dass du es 1:1 auf der VM ablegen kannst.

---

## 1. Verzeichnisstruktur auf der VM

Auf der VM z.B. unter `/opt/sola-history`:

```text
/opt/sola-history
├── docker-compose.yml
├── .env
└── nginx/
    ├── conf.d/
    │   └── sola.conf
    └── webroot/              # für Let's Encrypt HTTP-01 Challenge
```

Erstellen:

```bash
sudo mkdir -p /opt/sola-history/nginx/conf.d
sudo mkdir -p /opt/sola-history/nginx/webroot
sudo chown -R $USER:$USER /opt/sola-history
cd /opt/sola-history
```

---

## 2. `.env` – Umgebungsvariablen für docker-compose

Datei: `/opt/sola-history/.env`

```env
# App password for the Streamlit login
SOLA_APP_PASSWORD=change_me_please

# OCI Object Storage settings (für fetch_data.py im Container)
SOLA_DATA_BUCKET=sola-history-data
# Namespace kannst du leer lassen, wenn fetch_data.py ihn automatisch ermitteln soll
SOLA_DATA_NAMESPACE=

# Domain name
VIRTUAL_HOST=sola.oradba.ch
```

> `SOLA_DATA_BUCKET` muss zu deinem Bucket-Namen passen.
> `SOLA_DATA_NAMESPACE` kannst du später setzen, wenn du ihn kennst – ist aber optional.

---

## 3. `docker-compose.yml`

Datei: `/opt/sola-history/docker-compose.yml`

```yaml
version: "3.9"

services:
  sola-history:
    image: ghcr.io/oehrlis/sola-history-app:latest
    container_name: sola-history
    restart: unless-stopped
    environment:
      - SOLA_APP_PASSWORD=${SOLA_APP_PASSWORD}
      - SOLA_DATA_BUCKET=${SOLA_DATA_BUCKET}
      - SOLA_DATA_NAMESPACE=${SOLA_DATA_NAMESPACE}
    # App hört intern auf 8501
    expose:
      - "8501"
    networks:
      - sola-net
    # optional: Persistente Overrides / Logs
    volumes:
      - sola-data:/app/data/processed

  nginx:
    image: nginx:alpine
    container_name: sola-nginx
    restart: unless-stopped
    depends_on:
      - sola-history
    ports:
      - "80:80"
      - "443:443"
    networks:
      - sola-net
    volumes:
      # Nginx Config
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      # Webroot für ACME-Challenges
      - ./nginx/webroot:/var/www/certbot:ro
      # Let's Encrypt Zertifikate vom Host
      - /etc/letsencrypt:/etc/letsencrypt:ro

networks:
  sola-net:
    driver: bridge

volumes:
  sola-data:
```

> **Hinweis zum Image:** ich habe `ghcr.io/oehrlis/sola-history-app:latest` angenommen.
> Falls dein Repo anders heisst, passe die Image-URL an.

---

## 4. Nginx-Konfiguration für `sola.oradba.ch`

Datei: `/opt/sola-history/nginx/conf.d/sola.conf`

Zuerst Version mit HTTP + ACME-Challenge + HTTPS-Redirect + Proxy:

```nginx
# HTTP: nur für Let's Encrypt Challenge und Redirect auf HTTPS
server {
    listen 80;
    server_name sola.oradba.ch;

    # ACME HTTP-01 Challenge für certbot
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS: Reverse Proxy zur Streamlit-App
server {
    listen 443 ssl http2;
    server_name sola.oradba.ch;

    # Diese Pfade werden von Certbot erzeugt
    ssl_certificate     /etc/letsencrypt/live/sola.oradba.ch/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sola.oradba.ch/privkey.pem;

    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    # Optional: etwas Logging
    access_log /var/log/nginx/sola_access.log;
    error_log  /var/log/nginx/sola_error.log;

    # Später kannst du hier Basic Auth ergänzen

    location / {
        proxy_pass         http://sola-history:8501;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

> Die TLS-Pfade funktionieren erst, **nachdem** du Certbot einmal laufen gelassen hast.

---

## 5. Erstes Starten ohne Zertifikate

Zuerst Nginx und App hochfahren (HTTP funktioniert, HTTPS noch nicht):

```bash
cd /opt/sola-history
docker compose pull
docker compose up -d
```

Jetzt sollte unter `http://<VM-IP>` bereits ein Nginx-Fehler oder Redirect laufen.
Wichtig ist: Port 80 funktioniert für die ACME-Challenge.

---

## 6. Let’s Encrypt Zertifikat holen (einmalig)

Auf der VM (nicht im Container):

```bash
sudo mkdir -p /etc/letsencrypt
sudo chown -R $USER:$USER /etc/letsencrypt
```

Dann Certbot als Docker-Container mit Webroot:

```bash
docker run --rm -it \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /opt/sola-history/nginx/webroot:/var/www/certbot \
  certbot/certbot certonly \
    --webroot \
    -w /var/www/certbot \
    -d sola.oradba.ch \
    --email deine.email@oradba.ch \
    --agree-tos \
    --no-eff-email
```

Wenn das durchläuft, hast du Zertifikate unter:

```text
/etc/letsencrypt/live/sola.oradba.ch/
  ├── fullchain.pem
  └── privkey.pem
```

Jetzt Nginx neu starten:

```bash
docker compose restart nginx
```

Ab jetzt:
👉 `https://sola.oradba.ch` sollte erreichbar sein
👉 Streamlit-App hängt hinter Nginx, Passwortschutz macht die App selbst (`SOLA_APP_PASSWORD`)

---

## 7. Zertifikats-Erneuerung (Renewal)

Einmal pro Tag per Cron auf der VM (als root oder user mit Zugriff):

```bash
sudo crontab -e
```

Eintrag:

```cron
# Renew Let's Encrypt certs for sola.oradba.ch daily at 03:30
30 3 * * * docker run --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /opt/sola-history/nginx/webroot:/var/www/certbot \
  certbot/certbot renew --webroot -w /var/www/certbot --quiet && \
  docker compose -f /opt/sola-history/docker-compose.yml reload nginx
```

Falls `reload` nicht geht, kannst du auch `restart nginx` verwenden, ist halt etwas härter.

---

## 8. Wie geht’s weiter? (Basic Auth & OAuth)

### Jetzt:

* Authentisierung nur über `SOLA_APP_PASSWORD` in der App.
* Zugriff über HTTPS abgesichert, mit Let’s Encrypt Zertifikat.
* Domain: `sola.oradba.ch`.

### Später:

1. **Basic Auth in Nginx** ergänzen (einfach):

   * `auth_basic` + `auth_basic_user_file` in der HTTPS-Server-Section
   * `.htpasswd` unter `/opt/sola-history/nginx/htpasswd`

2. **OAuth (Google / AzureAD)**:

   * Vor Nginx z.B. `oauth2-proxy` Container hängen
   * Nginx → oauth2-proxy → sola-history
     (können wir in einem nächsten Schritt sauber designen)

---
scripts/project_issues.txt

Wenn du magst, können wir als Nächstes das `docker-compose.yml` und den Image-Namen exakt auf dein reales GitHub-Repo anpassen – sobald du den finalen Namen hast.
::contentReference[oaicite:0]{index=0}
```
