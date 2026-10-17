# Local Nodestream project. Run from this directory: make help
# Variables: TARGET=neo4j (or dry-run), PIPELINES="fields studies patients"
PYTHON ?= python3
VENV   := .venv
PY     := $(VENV)/bin/python
PIP    := $(VENV)/bin/pip
NS     := $(VENV)/bin/nodestream
TARGET ?= neo4j
PIPELINES ?= fields studies patients

.DEFAULT_GOAL := help
.PHONY: help setup install validate migrate pare-down ingest

help:          ## Show this help
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-13s %s\n", $$1, $$2}'

setup:         ## Create .venv and .env (does not overwrite an existing .env)
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	@test -f .env || cp .env.example .env
	@echo "Set NEO4J_PASSWORD in .env before make ingest"

install: setup ## Install Nodestream, the SAS plugin, and this project into .venv
	$(PIP) install -e .

validate:     ## Check .env values and Neo4j connectivity
	@test -x $(PY) || { echo "Run make install first"; exit 1; }
	@$(PY) scripts/validate_env.py

pare-down: validate ## Drop patients and centers so the next ingest is the 500-row sample
	@set -a && . ./.env && set +a && $(PY) scripts/pare_down.py

migrate: validate ## Write the schema migration if needed, then apply it to Neo4j
	@set -a && . ./.env && set +a && \
	  $(NS) migrations make && \
	  $(NS) migrations run --target neo4j

ingest: install ## Migrate Neo4j, then load fields, studies, and patients
	@test -d ../data/datasets_extracted || { echo "Extract the SAS files first: make -C .. download"; exit 1; }
	@test -f ../data/field_ontology.csv && test -f ../data/field_dataset_mapping.csv && test -f ../data/catalog.csv || \
	  { echo "Missing ontology files in ../data (field_ontology.csv, field_dataset_mapping.csv, catalog.csv)"; exit 1; }
	@if [ "$(TARGET)" = "neo4j" ]; then $(MAKE) --no-print-directory validate; fi
	@set -a && . ./.env && set +a && \
	  if [ "$(TARGET)" = "neo4j" ]; then $(NS) migrations make && $(NS) migrations run --target neo4j; fi && \
	  $(NS) run $(PIPELINES) --target $(TARGET)
