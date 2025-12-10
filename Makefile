# ------------------------------------------------------------------------------
# SOLA History - Makefile
# ------------------------------------------------------------------------------
# Name........: Makefile
# Author......: Stefan Oehrli (oes) stefan.oehrli@oradba.ch
# Editor......: Stefan Oehrli
# Date........: 2024-12-09
# Version.....: v1.0.0
# Purpose.....: Build automation for SOLA History web application.
#               Provides targets for local development, Docker operations,
#               data import, and cleanup tasks.
# Requires....: Python >=3.11, Docker, docker-compose
# Notes.......: Variables can be overridden via command line or environment
# License.....: Apache License Version 2.0
# ------------------------------------------------------------------------------

# Project configuration
PROJECT_NAME    := sola-history
IMAGE_NAME      := sola-history
CONTAINER_NAME  := sola-history

# Application password (can be overridden via command line or environment)
SOLA_APP_PASSWORD ?= sola

# Python configuration
# Can be overridden to use different Python version (e.g., make PYTHON=python3.12)
PYTHON      ?= python3.11

# Data repository location (relative path to sola-history-data repo)
DATA_REPO   ?= ../sola-history-data

# Output directory for processed JSON files
DATA_OUTDIR ?= data/processed

# Virtual environment configuration
VENV_DIR    ?= venv
VENV_PYTHON := $(VENV_DIR)/bin/python3
VENV_PIP    := $(VENV_DIR)/bin/pip

.DEFAULT_GOAL := help

# Docker / Compose
COMPOSE            ?= docker compose
COMPOSE_FILE       ?= docker-compose.dev.yml
SERVICE_NAME       ?= sola-history
CONTAINER_NAME     ?= sola-history-dev

# ------------------------------------------------------------------------------
# PHONY TARGETS DECLARATION
# ------------------------------------------------------------------------------
# Declare all targets that don't represent actual files

.PHONY: help venv install import-data validate-data run-local run-local-debug \
        build rebuild up upd down downv shell logs image ps \
        clean-image clean-dangling clean-venv reinstall clean-all

help:
	@echo ""
	@echo "================================================================================"
	@echo "SOLA History - Makefile Help"
	@echo "================================================================================"
	@echo ""
	@echo "Local Development:"
	@echo "  make venv              Create Python virtual environment"
	@echo "  make install           Install Python dependencies"
	@echo "  make import-data       Import Excel files to JSON (uses DATA_REPO)"
	@echo "  make validate-data     Validate JSON data against schema"
	@echo "  make run-local         Start Streamlit app locally"
	@echo "  make run-local-debug   Start Streamlit app with debug logging"
	@echo ""
	@echo "Docker Operations:"
	@echo "  make build             Build Docker image via docker-compose"
	@echo "  make rebuild           Rebuild Docker image without cache"
	@echo "  make up                Start container (foreground, attached)"
	@echo "  make upd               Start container (detached mode)"
	@echo "  make down              Stop and remove container"
	@echo "  make downv             Stop container and remove volumes"
	@echo "  make shell             Open bash shell in running container"
	@echo "  make logs              Follow container logs"
	@echo ""
	@echo "Information & Cleanup:"
	@echo "  make image             Show project Docker images"
	@echo "  make ps                Show running project containers"
	@echo "  make clean-venv        Remove Python virtual environment only"
	@echo "  make reinstall         Remove venv and reinstall dependencies"
	@echo "  make clean-image       Remove project Docker image"
	@echo "  make clean-dangling    Remove dangling Docker images"
	@echo "  make clean-all         Complete cleanup (venv + images)"
	@echo ""
	@echo "Environment Variables:"
	@echo "  SOLA_APP_PASSWORD      Application password (default: sola)"
	@echo "  PYTHON                 Python executable (default: python3.11)"
	@echo "  DATA_REPO              Data repository path (default: ../sola-history-data)"
	@echo "  DATA_OUTDIR            JSON output directory (default: data/processed)"
	@echo ""
	@echo "Example Usage:"
	@echo "  make install                                    # Install with defaults"
	@echo "  make import-data DATA_REPO=/path/to/data       # Custom data path"
	@echo "  make run-local SOLA_APP_PASSWORD=secret123     # Custom password"
	@echo "  make PYTHON=python3.12 install                 # Use Python 3.12"
	@echo ""
	@echo "================================================================================"
	@echo ""

# ------------------------------------------------------------------------------
# PYTHON VIRTUAL ENVIRONMENT
# ------------------------------------------------------------------------------

# Create virtual environment directory
# This is a real target (not .PHONY) - only runs if venv/ doesn't exist
$(VENV_DIR):
	@echo "Creating virtual environment using $(PYTHON)..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "✓ Virtual environment created in $(VENV_DIR)"

# Convenience target to ensure venv exists
venv: $(VENV_DIR)
	@echo "✓ Virtual environment ready"

# Install Python dependencies
# Depends on: venv (ensures virtual environment exists)
install: venv
	@echo "Upgrading pip..."
	@$(VENV_PIP) install --upgrade pip
	@echo "Installing dependencies from requirements.txt..."
	@$(VENV_PIP) install -r requirements.txt
	@echo "✓ Dependencies installed successfully"

# Import Excel data to JSON format
# Depends on: venv (ensures Python environment exists)
# Uses: DATA_REPO and DATA_OUTDIR variables
import-data: venv
	@echo "Creating output directory: $(DATA_OUTDIR)"
	@mkdir -p $(DATA_OUTDIR)
	@echo "Importing Excel data from $(DATA_REPO)..."
	@$(VENV_PYTHON) $(DATA_REPO)/tools/import_excel.py --output-dir $(DATA_OUTDIR)
	@echo "Validating imported data..."
	@$(MAKE) validate-data
	@echo "✓ Excel import and validation completed (output: $(DATA_OUTDIR))"

# Validate JSON data against schema
# Depends on: venv (ensures Python environment exists)
# Requires: JSON files in DATA_OUTDIR and schema file in DATA_REPO
validate-data: venv
	@echo "Validating data in $(DATA_OUTDIR) against schema..."
	@$(VENV_PYTHON) $(DATA_REPO)/tools/validate_data.py \
		--data-dir $(DATA_OUTDIR) \
		--schema-file $(DATA_REPO)/schemas/sola.schema.json
	@echo "✓ Data in $(DATA_OUTDIR) is valid against schema"

# Run Streamlit app locally (production mode)
# Depends on: install (ensures all dependencies are installed)
# Uses: SOLA_APP_PASSWORD environment variable
run-local: install
	@echo "Starting Streamlit app at http://localhost:8501"
	@echo "Password: $(SOLA_APP_PASSWORD)"
	@SOLA_APP_PASSWORD=$(SOLA_APP_PASSWORD) $(VENV_PYTHON) -m streamlit run app.py

# Run Streamlit app locally with debug logging
# Depends on: install (ensures all dependencies are installed)
# Uses: SOLA_APP_PASSWORD environment variable
run-local-debug: install
	@echo "Starting Streamlit app in DEBUG mode at http://localhost:8501"
	@echo "Password: $(SOLA_APP_PASSWORD)"
	@SOLA_APP_PASSWORD=$(SOLA_APP_PASSWORD) \
		$(VENV_PYTHON) -m streamlit run app.py --logger.level=debug

# ------------------------------------------------------------------------------
# DOCKER OPERATIONS
# ------------------------------------------------------------------------------

# Build Docker image using docker-compose
# Reads configuration from docker-compose.yml
.PHONY: build rebuild up upd down downv shell logs

build:
	@echo "Building Docker image using $(COMPOSE_FILE)..."
	@$(COMPOSE) -f $(COMPOSE_FILE) build $(SERVICE_NAME)
	@echo "✓ Docker image built successfully"

# Rebuild Docker image without using cache
# Useful when dependencies or base image changed
rebuild:
	@echo "Rebuilding Docker image (no cache) using $(COMPOSE_FILE)..."
	@$(COMPOSE) -f $(COMPOSE_FILE) build --no-cache $(SERVICE_NAME)
	@echo "✓ Docker image rebuilt successfully"

# Start container in foreground (attached mode)
# Press Ctrl+C to stop
up:
	@echo "Starting container in foreground mode..."
	@echo "Password: $(SOLA_APP_PASSWORD)"
	@SOLA_APP_PASSWORD=$(SOLA_APP_PASSWORD) @$(COMPOSE) -f $(COMPOSE_FILE) up $(SERVICE_NAME)

# Start container in background (detached mode)
upd:
	@echo "Starting container in detached mode..."
	@echo "Password: $(SOLA_APP_PASSWORD)"
	@SOLA_APP_PASSWORD=$(SOLA_APP_PASSWORD) @$(COMPOSE) -f $(COMPOSE_FILE) up -d $(SERVICE_NAME)
	@echo "✓ Container started. Use 'make logs' to view output"

# Stop and remove container
down:
	@echo "Stopping and removing container..."
	@$(COMPOSE) -f $(COMPOSE_FILE) down
	@echo "✓ Container stopped and removed"

# Stop container and remove volumes
# WARNING: This will delete all persistent data
downv:
	@echo "WARNING: This will remove all volumes and data!"
	@$(COMPOSE) -f $(COMPOSE_FILE) down -v
	@echo "✓ Container and volumes removed"

# Open bash shell in running container
# Fails gracefully if container is not running
shell:
	@echo "Opening shell in container $(CONTAINER_NAME)..."
	@docker exec -it $(CONTAINER_NAME) /bin/bash || \
		echo "Error: Container '$(CONTAINER_NAME)' is not running. Use 'make upd' first."

# Follow container logs in real-time
# Press Ctrl+C to stop following
logs:
	@echo "Following logs for $(SERVICE_NAME)..."
	@$(COMPOSE) -f $(COMPOSE_FILE) logs -f $(SERVICE_NAME) 2>/dev/null || \
		echo "Error: Container '$(CONTAINER_NAME)' is not running. Use 'make upd' first."

# ------------------------------------------------------------------------------
# INFORMATION & CLEANUP
# ------------------------------------------------------------------------------

# Show Docker images for this project
image:
	@docker images | grep "$(IMAGE_NAME)" || \
		echo "No images found for '$(IMAGE_NAME)'"

# Show running containers for this project
ps:
	@docker ps | grep "$(CONTAINER_NAME)" || \
		echo "No running container found for '$(CONTAINER_NAME)'"

# Remove project Docker image
# The '-' prefix ignores errors if image doesn't exist
clean-image:
	@echo "Removing Docker image $(IMAGE_NAME):latest..."
	@-docker rmi $(IMAGE_NAME):latest 2>/dev/null && \
		echo "✓ Image removed" || \
		echo "Image not found or in use"

# Remove dangling Docker images (not tagged and not used)
# Helps free up disk space
clean-dangling:
	@echo "Removing dangling Docker images..."
	@docker image prune -f
	@echo "✓ Dangling images removed"

# Remove Python virtual environment only
# Does not affect Docker images or containers
clean-venv:
	@echo "Removing virtual environment..."
	@rm -rf $(VENV_DIR)
	@echo "✓ Virtual environment removed"

# Remove venv and reinstall all dependencies
# Useful when requirements.txt changed or venv is corrupted
reinstall: clean-venv install
	@echo "✓ Virtual environment recreated and dependencies reinstalled"

# Complete cleanup: remove venv, images, and dangling images
# WARNING: This will require rebuilding everything
clean-all: clean-venv clean-image clean-dangling
	@echo ""
	@echo "================================================================================"
	@echo "✓ Complete cleanup done"
	@echo "  - Virtual environment removed"
	@echo "  - Docker images removed"
	@echo "  - Dangling images removed"
	@echo "================================================================================"
	@echo ""