# ------------------------------------------------------------
# Sola History - Makefile
# ------------------------------------------------------------

# Projekt / Docker
PROJECT_NAME    := sola-history
IMAGE_NAME      := sola-history
CONTAINER_NAME  := sola-history

# App-Passwort (kann beim Aufruf überschrieben werden)
SOLA_APP_PASSWORD ?= sola

# Python / venv
PYTHON      ?= python3.11
DATA_REPO   ?= ../sola-history-data
DATA_OUTDIR ?= data/processed

VENV_DIR    ?= venv
VENV_PYTHON := $(VENV_DIR)/bin/python3
VENV_PIP    := $(VENV_DIR)/bin/pip

.DEFAULT_GOAL := help

# ------------------------------------------------------------
# Hilfstargets
# ------------------------------------------------------------

.PHONY: help venv install import run-local run-local-debug \
        build rebuild up upd down downv shell logs image ps \
        clean-image clean-dangling clean-venv reinstall

help:
	@echo ""
	@echo "Sola History - Makefile"
	@echo ""
	@echo " Lokale Entwicklung:"
	@echo "   make venv              - virtuelle Umgebung anlegen"
	@echo "   make install           - Dependencies installieren"
	@echo "   make import-data       - Excel -> JSON verarbeiten (mit DATA_REPO und DATA_OUTDIR)"
	@echo "   make run-local         - Streamlit lokal starten"
	@echo "   make run-local-debug   - Streamlit Debug starten"
	@echo ""
	@echo " Docker / Compose:"
	@echo "   make build             - Compose-Image bauen"
	@echo "   make rebuild           - Compose-Image ohne Cache bauen"
	@echo "   make up                - Container starten (foreground)"
	@echo "   make upd               - Container starten (detached)"
	@echo "   make down              - Container stoppen"
	@echo "   make downv             - Container + Volumes stoppen"
	@echo "   make shell             - Shell in Container öffnen"
	@echo "   make logs              - Logs verfolgen"
	@echo ""
	@echo " Cleanup:"
	@echo "   make clean-venv        - nur venv/ löschen"
	@echo "   make reinstall         - venv löschen + neu installieren"
	@echo "   make clean-image       - nur Projekt-Image löschen"
	@echo "   make clean-dangling    - dangling Images löschen"
	@echo "   make clean-all         - venv + Image + dangling löschen"
	@echo ""

# ------------------------------------------------------------
# Python / venv
# ------------------------------------------------------------

$(VENV_DIR):
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "✓ Virtual environment created in $(VENV_DIR)"

venv: $(VENV_DIR)

install: venv
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt
	@echo "✓ Dependencies installed"

.PHONY: import-data 
import-data: venv
	$(VENV_PYTHON) $(DATA_REPO)/tools/import_excel.py --output-dir $(DATA_OUTDIR)
	@echo "✓ Excel import completed"

run-local: install
	SOLA_APP_PASSWORD=$(SOLA_APP_PASSWORD) $(VENV_PYTHON) -m streamlit run app.py

run-local-debug: install
	SOLA_APP_PASSWORD=$(SOLA_APP_PASSWORD) \
		$(VENV_PYTHON) -m streamlit run app.py --logger.level=debug

# ------------------------------------------------------------
# Docker
# ------------------------------------------------------------

build:
	docker compose build

rebuild:
	docker compose build --no-cache

up:
	SOLA_APP_PASSWORD=$(SOLA_APP_PASSWORD) docker compose up

upd:
	SOLA_APP_PASSWORD=$(SOLA_APP_PASSWORD) docker compose up -d

down:
	docker compose down

downv:
	docker compose down -v

shell:
	docker exec -it $(CONTAINER_NAME) /bin/bash || echo "Container läuft nicht."

logs:
	docker logs -f $(CONTAINER_NAME) || echo "Container läuft nicht."

# ------------------------------------------------------------
# Info / Cleanup
# ------------------------------------------------------------

image:
	docker images | grep "$(IMAGE_NAME)" || echo "Kein Image gefunden."

ps:
	docker ps | grep "$(CONTAINER_NAME)" || echo "Kein Container aktiv."

clean-image:
	-docker rmi $(IMAGE_NAME):latest 2>/dev/null || echo "Image nicht gefunden."

clean-dangling:
	docker image prune -f
	@echo "✓ Dangling images removed"

# Nur das Python venv löschen
clean-venv:
	@echo "Removing virtual environment..."
	rm -rf $(VENV_DIR)
	@echo "✓ venv removed"

# Komplett neu installieren
reinstall: clean-venv install
	@echo "✓ venv recreated and dependencies reinstalled"

clean-all: clean-venv clean-image clean-dangling
	@echo "✓ Complete cleanup done"