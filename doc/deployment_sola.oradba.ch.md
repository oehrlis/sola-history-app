# Deployment Guide - sola.oradba.ch (OCI Free Tier)

Dieses Dokument beschreibt die Schritte, um die **Sola History App** auf einer  
**OCI Free Tier VM** unter der Subdomain **`sola.oradba.ch`** bereitzustellen.

Setup:

- Oracle Cloud Infrastructure - Free Tier VM (Arm oder AMD)
- Docker + docker-compose auf der VM
- Nginx als Reverse Proxy
- Let's Encrypt (Certbot) für HTTPS-Zertifikate
- Streamlit-App im Container (`sola-history`)

## Voraussetzungen

- Domain: `oradba.ch`
- Subdomain: **`sola.oradba.ch`**
- OCI Account mit Free Tier
- Zugriff per SSH auf die VM
- Docker-Image der App in einer Registry, z. B.  
  `ghcr.io/oehrlis/sola-history-app:latest`  
  (bei dir ggf. anpassen)

## OCI VM - Erstellen (Free Tier)

1. In der OCI Console:
   - **Compute → Instances → Create instance**
   - Shape:  
     - z. B. `VM.Standard.A1.Flex` (Arm, Always Free)  
     - 1 OCPU, 4 GB RAM reichen
   - Image:
     - Oracle Linux 8/9
   - Netzwerk:
     - Öffentliches Subnetz mit Internetzugang
   - SSH Key:
     - Deinen öffentlichen Schlüssel hinterlegen

2. Nach Erstellung:
   - **Public IP** notieren, z. B. `130.61.42.100`

## DNS-Eintrag für sola.oradba.ch

Beim DNS-Provider von `oradba.ch` einen **A-Record** erstellen:

| Type | Name           | Value           |
|------|----------------|-----------------|
| A    | sola.oradba.ch | 130.61.42.100   |

Propagation kann ein paar Minuten dauern.

## Vorbereitung der VM (Docker & Verzeichnisse)

Per SSH auf die VM einloggen:

```bash
ssh opc@130.61.42.100
```

### Docker installieren (Oracle Linux)

```bash
sudo dnf install -y docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker opc
```

**WICHTIG:** Danach einmal neu einloggen, damit die Docker-Gruppe aktiv wird:

```bash
exit
ssh opc@130.61.42.100
```

### docker-compose (Plugin) installieren (optional, abhängig vom Image)

Für moderne Docker-Versionen ist `docker compose` bereits integriert. Wenn nicht, kann man `docker-compose` separat installieren - für viele Setups reicht:

```bash
docker compose version || echo "compose-plugin wird evtl. über Paketmanager benötigt"
```

Wenn der Befehl funktioniert (`docker compose version`), bist du ready.

## Verzeichnisstruktur für die App

Auf der VM:

```bash
sudo mkdir -p /opt/sola-history/nginx/conf.d
sudo mkdir -p /opt/sola-history/nginx/webroot
sudo chown -R $USER:$USER /opt/sola-history
cd /opt/sola-history
```

Struktur:

```text
/opt/sola-history
├── docker-compose.yml
├── .env
└── nginx/
    ├── conf.d/
    │   └── sola.conf
    └── webroot/
```

## `.env` anlegen

Datei: `/opt/sola-history/.env`

```env
# Streamlit App password
SOLA_APP_PASSWORD=change_me_please

# OCI Object Storage (für fetch_data.py im Container)
SOLA_DATA_BUCKET=sola-history-data
# optional, falls fetch_data.py das nicht automatisch ermittelt:
SOLA_DATA_NAMESPACE=

# Domain
VIRTUAL_HOST=sola.oradba.ch
```

## `docker-compose.yml` anlegen

Datei: `/opt/sola-history/docker-compose.yml`

> Falls dein Image anders heisst, `image:` Zeile anpassen.

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
    expose:
      - "8501"
    networks:
      - sola-net
    volumes:
      # optional: persistente Daten/Overrides
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
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/webroot:/var/www/certbot:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro

networks:
  sola-net:
    driver: bridge

volumes:
  sola-data:
```

## Nginx-Konfiguration für sola.oradba.ch

Datei: `/opt/sola-history/nginx/conf.d/sola.conf`

```nginx
# HTTP: ACME-Challenge + Redirect auf HTTPS
server {
    listen 80;
    server_name sola.oradba.ch;

    # Webroot für Let's Encrypt HTTP-01 Challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Alles andere auf HTTPS umleiten
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS: Reverse Proxy zur Streamlit-App
server {
    listen 443 ssl http2;
    server_name sola.oradba.ch;

    ssl_certificate     /etc/letsencrypt/live/sola.oradba.ch/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sola.oradba.ch/privkey.pem;

    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    access_log /var/log/nginx/sola_access.log;
    error_log  /var/log/nginx/sola_error.log;

    # Später: hier kann Basic Auth oder OAuth reverse proxy ergänzt werden

    location / {
        proxy_pass         http://sola-history:8501;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

> Hinweis: TLS-Pfade funktionieren erst, wenn Let's Encrypt Zertifikate vorhanden sind.
>
## Erster Start (noch ohne Zertifikate)

App & Nginx starten:

```bash
cd /opt/sola-history
docker compose pull
docker compose up -d
```

Prüfen, ob Nginx auf Port 80 läuft:

```bash
curl -I http://sola.oradba.ch
```

## Let's Encrypt Zertifikat holen (einmalig)

Zuerst Verzeichnis für Zertifikate vorbereiten:

```bash
sudo mkdir -p /etc/letsencrypt
sudo chown -R $USER:$USER /etc/letsencrypt
```

Dann Certbot per Docker ausführen:

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

Wenn der Befehl erfolgreich war, liegen die Zertifikate unter:

```text
/etc/letsencrypt/live/sola.oradba.ch/
  ├── fullchain.pem
  └── privkey.pem
```

Jetzt Nginx neu starten:

```bash
cd /opt/sola-history
docker compose restart nginx
```

Danach sollte die App unter **`https://sola.oradba.ch`** erreichbar sein.

## Zertifikats-Erneuerung (Cron)

Let's Encrypt Zertifikate sind 90 Tage gültig. Renewal kann automatisch z. B. täglich erfolgen.

Als root Crontab öffnen:

```bash
sudo crontab -e
```

Eintrag hinzufügen:

```cron
# Renew Let's Encrypt certs daily at 03:30
30 3 * * * docker run --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /opt/sola-history/nginx/webroot:/var/www/certbot \
  certbot/certbot renew --webroot -w /var/www/certbot --quiet && \
  docker compose -f /opt/sola-history/docker-compose.yml restart nginx
```

## Zugriffsschutz (aktuell) & zukünftige Auth

Aktuell schützt:

- Streamlit-App selbst über `SOLA_APP_PASSWORD`

Später geplant:

- **Nginx Basic Auth** (zusätzlicher Schutz)
- **OAuth2 / OpenID Connect** (z. B. Azure AD, Google) via vorgeschaltetem `oauth2-proxy`

Diese Erweiterungen können direkt in der `nginx`-Konfiguration bzw. im `docker-compose.yml` ergänzt werden.

## Troubleshooting

### Nginx startet nicht / 502 Bad Gateway

- Logs prüfen:

```bash
docker logs sola-nginx
docker logs sola-history
```

- Prüfen, ob App-Container läuft:

```bash
docker ps
```

### Zertifikat-Fehler

- Certbot Logs prüfen (`/var/log/letsencrypt/`)
- DNS-Konfiguration testen:

```bash
dig +short sola.oradba.ch
```

Muss die richtige öffentliche IP der VM liefern.

### Änderungen an Config-Dateien

Nach Anpassungen:

```bash
cd /opt/sola-history
docker compose restart nginx
```

## Zusammenfassung

- **Kosten:** Alles läuft auf einer OCI Free Tier VM → 0 CHF
- **Sicherheit:** HTTPS via Let's Encrypt, App-Passwort aktiv
- **Architektur:** Docker-basiert, einfach wartbar, per CI/CD aktualisierbar
- **Erweiterbarkeit:** Basic Auth, OAuth, zusätzliche Services jederzeit ergänzbar
