Sehr cool, dass du schon so weit bist – das ist jetzt ein richtiges kleines Produkt 💪
Ich geh die vier Fragen der Reihe nach durch und mache dir jeweils konkrete Vorschläge + eine “Empfehlung für jetzt”.

---

## 1️⃣ Bewirtschaftung der Läufer (aktiv, E-Mail, Nummer, …)

Im Moment entstehen die Läufer aus dem Excel-Import, und `import_excel.py` erzeugt `runners.json`. Es gibt drei sinnvolle Strategien für die Pflege:

### Option A: “Master-Excel” für Kontakte (empfohlen kurzfristig)

Du hast ja schon `sola_kontakte.xlsx`. Wir können das so machen:

* `sola_kontakte.xlsx` wird die **Masterliste** für:

  * `email`
  * `mobile`
  * `active`
  * ggf. `company`/`is_external` Overrides

* `import_excel.py`:

  * liest wie heute die Laufdaten aus `SOLA_1998-2025.xlsx`
  * liest zusätzlich `sola_kontakte.xlsx`
  * matched über `runner_id` (oder “Läufer”-Name wie bisher)
  * überschreibt:

    * Dummy-E-Mail → echte E-Mail
    * Dummy-Mobile → echte Mobile
    * `active` Flag

**Vorteile:**

* Du pflegst alles in **Excel**, nicht in JSON.
* Änderungen an Kontaktdaten = Excel speichern → `make import` → JSON frisch.
* Kein Risiko, dass Änderungen im JSON beim nächsten Import überbügelt werden.

> Wir müssen dazu nur `import_excel.py` um 2–3 Felder im `CONTACT_COLUMNS`-Block erweitern (z.B. `active`, `company`, `is_external_override`).

---

### Option B: Admin-UI in Streamlit (mittelfristig sexy)

Eine zusätzliche Tab-Seite “Admin”:

* Dropdown / Suche nach Läufer
* Formular:

  * Vorname, Nachname (readonly oder bearbeitbar)
  * Firma
  * extern (Checkbox)
  * aktiv (Checkbox)
  * E-Mail, Mobile editierbar
* Button “Speichern”:

  * schreibt geändertes `runners.json` zurück
    (dann Volume `/data/processed` im Docker nicht `:ro`, sondern `:rw`)

**Vorteil:**
Direkt in der App editieren, kein Excel öffnen.

**Nachteil:**
Komplexer (File-Locks, Versionierung, Race-Import darf Läufer nicht wieder überschreiben). Langfristig eher mit DB sauber.

---

### Option C: Direkt JSON bearbeiten

Kannst du natürlich auch mit VS Code machen, ist aber:

* fehleranfällig,
* doof, sobald du viele Änderungen machst,
* beim nächsten `make import` wieder überschrieben.

**=> Empfehlung:**

**Jetzt sofort:**
→ Option A: `sola_kontakte.xlsx` als Master, Script so erweitern, dass `active`, `email`, `mobile` usw. daraus kommen.

**Später:**
→ Admin-Tab in der Streamlit-App (auf Basis der JSONs).

---

## 2️⃣ Nächstes Jahr: wie kommen die neuen Daten rein?

Kurz gesagt: ja, du wirst jedes Jahr einmal “Excel anfassen”. Aber wir können den Prozess klar definieren, damit es nicht chaotisch wird.

### Vorschlag für deinen Workflow:

1. **Nach dem Lauf** holst du dir die Resultate (entweder:

   * vom offiziellen Excel,
   * oder später automatisiert von TrackMaxx).

2. Du hast **ein “Master-Excel”**:

   * `data/raw/SOLA_1998-2025.xlsx`
     (ggf. irgendwann `SOLA_1998-2030.xlsx` …)
   * gleiche Kopfzeilen wie heute
   * neues Jahr = einfach unten dranhängen oder eigenes Sheet, das `import_excel.py` mitliest.

3. Du pflegst:

   * Distanz
   * Rang / Zeit / Pace
   * `Teams` (Anzahl)
   * Läufer (Namenskonventionen gleich lassen)

4. Dann:

```bash
make import
```

→ JSONs aktualisiert, App zeigt das neue Jahr automatisch.

### Alternative:

Pro Jahr ein separates File:

* `SOLA_1998.xlsx`
* `SOLA_1999.xlsx`
* …
* `import_excel.py` iteriert über alle Dateien im `raw/`-Ordner.

Vorteil:
Mehr Ordnung, leichter zu versionieren.

Wenn du willst, kann ich dir `import_excel.py` so umbauen, dass es:

* **alle `SOLA_*.xlsx`** nacheinander einliest,
* und daraus ein großes `DataFrame` macht.

---

## 3️⃣ CI/CD mit privatem GitHub-Repo

Sehr passend:

* **Code + Datenmodell** auf GitHub (privat),
* Docker-Image erbauen,
* als Artefakt nach **GHCR oder OCI** schieben.

### 3.1. GitHub Actions minimal Setup

Du könntest in `.github/workflows/build.yml` so etwas haben:

```yaml
name: Build & Test

on:
  push:
    branches: [ main ]
  pull_request:

jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run import script
        run: |
          python tools/import_excel.py

      # Optional: Tests, Lint, etc.
      # - name: Run tests
      #   run: pytest
```

Damit stellst du sicher:

* Excel → JSON läuft auch in CI,
* das Repo ist “grün”.

### 3.2. Docker Build & Push (z.B. nach GHCR)

Zusätzlicher Job:

```yaml
  docker-build:
    runs-on: ubuntu-latest
    needs: build-test
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: ghcr.io/${{ github.repository_owner }}/sola-history:latest
```

**Wenn du lieber direkt nach OCI pushen willst:**

* in GitHub Secrets z.B. `OCI_USER`, `OCI_TENANCY`, `OCI_AUTH_TOKEN` etc.
* `docker/login-action` mit `iad.ocir.io` und deinen Credentials
* `tags: iad.ocir.io/<tenancy-namespace>/sola-history:latest`

Dann kannst du auf OCI einfach Container Instances von diesem Image starten.

---

## 4️⃣ Planungsmodul: wer läuft welche Strecke, wann muss er/sie wo sein?

Das wird echt ein cooles Feature 😁

### 4.1. Was wir dafür brauchen (Datenmodell)

Neue Entität, z.B. `race_plan`:

```json
{
  "race_id": "sola-2026",
  "race_date": "2026-05-XX",
  "race_start_time": "09:00",
  "teams": [
    {
      "team_id": "sola-2026-team-310",
      "name": "Optimizers",
      "legs": [
        {
          "leg_id": "sola-2026-leg-01",
          "leg_number": 1,
          "runner_id": "andrea.kennel",
          "expected_pace_sec_per_km": 320,
          "expected_time_seconds": 1400,
          "planned_start": "09:00",
          "planned_finish": "09:23"
        }
      ]
    }
  ]
}
```

Berechnung:

* Distanz pro Leg haben wir ja aus `legs.json`.
* Entweder:

  * Läufer:in gibt **Pace** an → `time = pace * dist`
  * oder du gibst direkt erwartete Zeit ein.

Kette:

* Leg1 start = Race-Start
* Leg1 finish = start + expected_time
* Leg2 start = Leg1 finish (+ evtl. Übergabepuffer)
* usw.

Darauf kannst du dann:

* Pro Läufer:

  * “Du musst spätestens um X Uhr am Start der Etappe Y sein”
  * “Deine voraussichtliche Ankunft am Ziel ist …”

### 4.2. UI-Idee in Streamlit

Neuer Tab: **“Planung”**

1. **Step 1 – Setup**

   * wähle Jahr (oder “nächstes Rennen”)
   * Eingabe: Race-Datum, Startzeit
   * Team selektieren / anlegen

2. **Step 2 – Zuteilung**

   * Tabelle `Leg 1..14`
   * Spalte “Runner” → Dropdown aus `runners.json`
   * Spalte “Erwartete Pace” → Input (mm:ss/km) oder direkt Sekunden
   * Button “Plan berechnen”

3. **Step 3 – Ergebnis**

   * Tabelle je Leg:

     * Leg, Runner, Distanz, expected time, geplante Start-/Zielzeit
   * Tabelle je Runner:

     * “Etappe X, Start um hh:mm, sei am Treffpunkt um hh:mm-10”
   * Optional: Export als CSV/Excel oder PDF.

4. **Persistenz**

   * speichern als `data/processed/plans.json`
   * oder `data/raw/SOLA_PLAN_2026.xlsx` und daraus wieder JSON generieren (analog Resultate).

### 4.3. Später nice-to-have

* Integration mit Strava (real pace vs. predicted).
* Plan vs. Ist im Nachhinein vergleichen.
* “Wer hat sich am meisten verschätzt?” 😄

---

## Zusammengefasst / Empfehlung

* **Runner-Pflege**:
  Kurzfristig via `sola_kontakte.xlsx` als Master (Script erweitern).

* **Neues Jahr**:
  Jahresdaten in Master-Excel hängen → `make import` → fertig.
  Mittelfristig evtl. ein File pro Jahr + Loop im Script.

* **CI/CD**:
  GitHub Actions:

  * Job: Excel→JSON testen
  * Job: Docker-Image bauen & nach GHCR/OCI pushen

* **Planung**:
  eigenes JSON-Modell für `race_plan`,
  neuer Streamlit-Tab “Planung” mit:

  * Runner-Zuteilung pro Leg
  * erwartete Pace / Zeit
  * automatischer Zeitplan.

Wenn du möchtest, können wir als nächsten Schritt sehr konkret:

* `import_excel.py` um `active` / Kontaktdaten erweitern
* und/oder ein erstes Datenmodell + JSON-Stub für `plans.json` definieren und gleich eine einfache Planungs-Tab in deine App einbauen.
