Hier kommt eine **komplette, strukturierte & umsetzbare Checkliste**
für die gesamte Sola-History-Implementierung – vom GitHub-Repo über CI/CD bis zur OCI-Bereitstellung.
**Diese Liste kannst du 1:1 abarbeiten und abhaken.**

---

# ✅ **SOLA History – Gesamt-Checkliste zur Umsetzung**

**Version 1.0 — End-to-End Implementation Plan**

---

# 1️⃣ **Repos erstellen & Grundstruktur**

## **A. App-Repository `sola-history-app`**

Enthält:

* `app.py`
* `Dockerfile`
* `docker-compose.yml (dev)`
* `requirements.txt`
* `tools/` inkl. import/export scripts
* `data/schema/*.json` (aber keine realen Daten!)
* `doc/*.md` (Architektur, Deployment, README)
* GitHub Actions Pipeline (Build + Push)

**To-Dos:**

* [ ] Repo `sola-history-app` in GitHub erstellen (privat oder public)
* [ ] deploy key/pat für GHCR definieren (falls private Registry)
* [ ] Repo mit Struktur füllen
* [ ] README.md erstellen
* [ ] architecture.md hinzufügen
* [ ] CONTRIBUTING.md hinzufügen
* [ ] .gitignore (`data/processed/`, venv, secrets)
* [ ] GitHub Actions Workflow `ci.yml` anlegen (Build → GHCR Push)
* [ ] Local run testen (Docker + Streamlit)

---

## **B. Data-Repository `sola-history-data`**

Enthält:

* `sola_history.xlsx`
* `sola_contacts.xlsx`
* `tools/upload_data_to_oci.sh`
* `tools/fetch_data.py`
* `README.md` zur Datenpflege

**To-Dos:**

* [ ] Repo anlegen (privat!)
* [ ] Versionierung über Git (optional: Git-LFS)
* [ ] README.md erstellen (Data Governance)
* [ ] upload_data_to_oci.sh erstellen
* [ ] fetch_data.py für App implementieren
* [ ] GitHub Actions Pipeline erstellen für automatisches Uploaden der Dateien

---

# 2️⃣ **Datenverarbeitung & Import vorbereiten**

**To-Dos:**

* [ ] Excel-Quellen final bereinigen

  * IDs prüfen
  * Zeiten als Sekunden validieren
  * Stage-Nummern prüfen
* [ ] import_excel.py finalisieren
* [ ] Makefile für lokalen Import
* [ ] JSON-Outputs kontrollieren (`data/processed`)
* [ ] Runner Overrides JSON testen
* [ ] Lauffähigen App-Prototyp validieren

---

# 3️⃣ **App-Funktionen fertigstellen**

Alle Features, die du bereits spezifiziert hast:

### **Runner Management**

* [ ] Active/Inactive Filtering
* [ ] Adresse, T-Shirt, Food Preference
* [ ] Default Pace, Preferred Distance, Favourite Stage
* [ ] Overrides Speichern & Exportieren
* [ ] Overrides CSV Download

### **Planung**

* [ ] Stage-Zuweisung
* [ ] Restart-Flag
* [ ] Realistische Start-/Finish-Berechnung
* [ ] Planning Checklist
* [ ] Export (CSV, Excel, PDF)

### **Charts & Highlights**

* [ ] Top-KM
* [ ] Starts
* [ ] Final Team Ranks
* [ ] Top-10 Individual
* [ ] Fastest Stages

### **Mehrsprachigkeit**

* [ ] STRINGS dictionary pflegen
* [ ] Default via Browser Locale
* [ ] English UI finalisieren

---

# 4️⃣ **Docker & Build-Pipeline**

### **Docker**

* [ ] Multistage Dockerfile finalisieren (Alpine, slim)
* [ ] Layer optimieren
* [ ] Tools extrahieren & volume mounten
* [ ] ENV für Password/Config

### **CI/CD**

Pipeline in `sola-history-app/.github/workflows/build.yml`

**To-Dos:**

* [ ] Build läuft auf main branch push
* [ ] Version Tagging für Releases (z. B. `v1.1.0`)
* [ ] Push to GHCR (Public/Private)
* [ ] Image-Scanning aktivieren (optional GH Advanced Security)

---

# 5️⃣ **OCI Infrastruktur vorbereiten**

### **Compute**

* [ ] Free-Tier VM (Arm/A1 oder AMD) erstellen
* [ ] Virtuelle Cloud Netzwerke prüfen
* [ ] Security List Ports (80/443) öffnen
* [ ] SSH Key dokumentieren

### **Object Storage**

* [ ] Bucket `sola-history-data` erstellen
* [ ] Richtige Namespace notieren
* [ ] IAM Policy: Allow bucket read for cloud-init scripts oder für app

### **DNS**

* [ ] A-Record `sola.oradba.ch` auf Public IP der VM setzen

---

# 6️⃣ **Deployment auf OCI**

### **Dokumentiertes Setup nach dein Deployment Guide**

* [ ] /opt/sola-history anlegen
* [ ] docker-compose.yml hochladen
* [ ] .env definieren (PASS + Bucket + Namespace)
* [ ] nginx reverse proxy config
* [ ] Certbot Webroot Verzeichnis
* [ ] docker compose up -d

### **Certbot**

* [ ] Certbot via docker ausführen
* [ ] Zertifikat erstellen
* [ ] HTTPS testen
* [ ] Renewal Cron einrichten

### **App Test**

* [ ] [https://sola.oradba.ch](https://sola.oradba.ch) aufrufen
* [ ] Passwortschutz prüfen
* [ ] UI testen
* [ ] Runner Filter testen
* [ ] Planung testen

---

# 7️⃣ **Security & Hardening**

### **Secrets**

* [ ] Password via OCI Vault oder GitHub Secret
* [ ] Keine Daten im App-Repo
* [ ] Daten-Repo privat

### **Access Control**

* [ ] Basic Auth einrichten (optional)
* [ ] Später: OAuth2 Proxy mit Azure / Google

### **Logging**

* [ ] Nginx Access/Errors
* [ ] docker logs forwarden (optional)

### **Backups**

* [ ] OCI Object Storage versioning aktivieren
* [ ] Daily JSON Backup (Cronjob)
* [ ] Runner Overrides sichern

---

# 8️⃣ **Dokumentation**

### Muss in `sola-history-app/doc/` enthalten sein:

* [ ] architecture.md
* [ ] deployment_sola.oradba.ch.md
* [ ] local_dev.md
* [ ] data_model.md
* [ ] update_procedure.md (z. B. neues Jahr, neue Excel)
* [ ] security_model.md
* [ ] troubleshooting.md

### Im Data Repo:

* [ ] data_governance.md
* [ ] excel_format_spec.md
* [ ] data_upload_workflow.md

---

# 9️⃣ **Nächstes Jahr / neue Daten**

**To-Dos:**

* [ ] Neues `sola_history.xlsx` ergänzen
* [ ] Make import laufen lassen
* [ ] processing JSON Commit (oder OCI Upload)
* [ ] App neu starten (`docker compose pull && restart`)

---

# 🔟 **Final Checks – Go-Live**

**Die finale Abnahme:**

* [ ] HTTPS läuft stabil
* [ ] UI auf Englisch
* [ ] Keine echten Daten im App Repo
* [ ] Daten im Object Storage verfügbar
* [ ] fetch_data.py funktioniert im Container
* [ ] Runner Overrides werden korrekt geladen
* [ ] Planung für nächstes Jahr durchspielbar
* [ ] Docker Image < 200MB (Ziel)
* [ ] CI/CD vollständig automatisiert

---

# 🏁 Fertig!

Wenn du diese Liste durchgehst, steht dem produktiven Betrieb
**sola.oradba.ch** nichts mehr im Weg.

Wenn du möchtest, kann ich dir auch eine **PDF-Version** der Checkliste erstellen oder eine **Kanban-Board Vorlage (GitHub Projects / Notion / Jira)**.
