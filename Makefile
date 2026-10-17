# Thin wrapper around scripts/. Run `make help` for targets.
# Variables: OUT=<folder> (default data), IDS="P-5370 P-5702", TIER="A B", ARGS="<extra flags>"
PY  := $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)
OUT ?= data
DL  := $(PY) scripts/download_cibmtr.py --out $(OUT) $(if $(IDS),--ids $(IDS)) $(ARGS)

.DEFAULT_GOAL := help
.PHONY: help install check test catalog dictionaries datasets candidates download papers research analysis pare-down

help:          ## Show this help
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-13s %s\n", $$1, $$2}'

install:       ## Check prerequisites and install them (creates .venv)
	@scripts/install.sh $(ARGS)
check:         ## Only report which prerequisites are present
	@scripts/install.sh --check
test:          ## Run the offline test suite
	@scripts/run_tests.sh

catalog:       ## Refresh the list of CIBMTR datasets (no downloads)
	$(DL) --list-only
dictionaries:  ## Download data dictionaries (all, or IDS=...)
	$(DL) --what dictionaries
datasets:      ## Download datasets (all, or IDS=...), unzipped
	$(DL) --what datasets --extract
candidates:    ## Download datasets and dictionaries for the NRM candidates (TIER="A" by default)
	$(DL) --ids-from data/nrm_candidate_ranking.csv --tier $(or $(TIER),A) --extract
download:      ## Download all datasets and dictionaries
	$(DL) --extract
pare-down:     ## Drop loaded patients so the next nodestream ingest is the 500-row sample
	$(MAKE) -C nodestream pare-down

papers:        ## Download the cited papers and reference documents (research/papers.csv)
	$(PY) scripts/download_papers.py --out $(OUT)/papers $(ARGS)
research: papers dictionaries  ## Download everything the research write-ups rely on (papers + dictionaries)

analysis:      ## Rebuild the derived files in data/ from downloaded dictionaries/datasets
	@scripts/build_analysis.sh $(OUT)
