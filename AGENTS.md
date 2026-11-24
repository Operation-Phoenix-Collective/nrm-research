# Agents

Install this repo and load the CIBMTR public datasets into Neo4j, starting from a fresh clone. The human overview is [README.md](README.md). The graph schema, sampling switch, and pipeline flags are in [nodestream/README.md](nodestream/README.md). This file is the order of commands and the checks between them.

Do not commit CIBMTR downloads, `.env`, or patient-level output. `data/datasets/`, `data/datasets_extracted/`, `data/dictionaries/`, and `nodestream/.env` are git-ignored. The terms are in [CONTRIBUTING.md](CONTRIBUTING.md#data-use-rules-read-before-contributing).

## What is already in git

Use these as they are. Do not regenerate them unless the dictionaries were just reparsed.

| File | Used by |
|---|---|
| `data/catalog.csv` | `studies` pipeline |
| `data/field_ontology.csv` | `fields` pipeline and column rename |
| `data/field_dataset_mapping.csv` | column rename in the `patients` pipeline |
| `data/variables_long.csv` | only the ontology rebuild |

SAS files are not in git. `make ingest` exits until `data/datasets_extracted/` exists.

## Order

Work from the repo root unless a step says `cd nodestream`. There are two virtualenvs: `.venv` at the root (Python 3.8+) and `nodestream/.venv` (Python 3.10+, from `nodestream/pyproject.toml`).

### 1. Tooling

```bash
make install
make test
```

`make install` creates `.venv` and installs `requirements.txt`. `make test` is offline and should pass before any download.

### 2. Neo4j

This repo does not install or start Neo4j. Start a local server yourself and confirm Bolt answers on port 7687. The values `make setup` copies into `nodestream/.env` are `NEO4J_URI=bolt://localhost:7687` and `NEO4J_USERNAME=neo4j`. Leave the password blank until step 5, then set `NEO4J_PASSWORD` to the server's password.

### 3. SAS files

```bash
make download
```

That fetches every dictionary and every dataset and unzips the datasets. A smaller stand-in while checking the path is `make datasets IDS="P-5051"`. Confirm a SAS file is present:

```bash
find data/datasets_extracted -iname '*.sas7bdat' -print -quit
```

Study directories are named `P-` plus digits. The `.sas7bdat` is usually one folder deeper, as in `data/datasets_extracted/P-5370/P-5370 (LK16-02)/lk1602public.sas7bdat`.

`make analysis` is not required for ingest. It rebuilds ranking and workbook files. It does not write `field_ontology.csv` or `field_dataset_mapping.csv`. Rebuild those only after `variables_long.csv` changes:

```bash
python3 scripts/build_field_ontology.py
```

### 4. Nodestream environment

```bash
cd nodestream
python3 --version          # must be 3.10 or newer; if not, set PYTHON to one that is
make setup                 # creates .venv and copies .env.example to .env
```

If `python3` is older than 3.10:

```bash
PYTHON=python3.12 make setup
```

`make setup` will not replace an existing `.env`. Edit `nodestream/.env` and set `NEO4J_PASSWORD`. `make validate` and `make ingest` source that file. Export the variables yourself only when calling the `nodestream` binary directly.

```bash
make install               # Nodestream, the Neo4j plugin, and the SAS plugin from GitHub
make validate              # prints the URI and username, confirms the password length, logs in once
```

`make install` here needs network access to PyPI and to GitHub (`nodestream-plugin-sas` is a git dependency). The root `make install` does not install these packages.

`make validate` must succeed before a real ingest. It prints no secret.

### 5. Choose the sample, then load

Open `nodestream/patients.yaml`. `max_rows: 500` under `StudySasExtractor` is commented out, so the next ingest loads every row of every SAS file. Uncomment that line to keep a stable 500-row sample of each file, seeded by the study id. Leave it commented to load everything.

```bash
make ingest                # still inside nodestream/
```

`make ingest` checks the SAS directory and the three CSVs, validates `.env`, runs migrations, then loads `fields`, `studies`, and `patients` into Neo4j. Writes are serial (`execute_chunks_in_parallel: false` in `nodestream.yaml`) because each patient row attaches to shared `Field` nodes.

Checks that do not need a full load:

```bash
make ingest TARGET=dry-run                 # parse and discard; skips the Neo4j login
make ingest PIPELINES="fields studies"     # ontology and catalog only
```

To limit SAS reads to one study, add `study_ids: [P-5051]` under `StudySasExtractor` in `patients.yaml`, run ingest, then remove that key.

### 6. Confirm the graph

Run the first query in [nodestream/queries/questions.md](nodestream/queries/questions.md): count `(:Patient)-[:ENROLLED_IN]->(:Study)`. Patient and center ids are unique only inside one `study_id`.

`make pare-down` (from `nodestream/`, or `make pare-down` at the repo root) deletes `Patient` and `Center` nodes and leaves `Field` and `Study`. The following `make ingest` follows the current `max_rows` setting.

## When a command stops

| Message | Fix |
|---|---|
| `Extract the SAS files first: make -C .. download` | From the repo root, `make download` or `make datasets`. |
| `Missing ontology files in ../data` | Those three CSVs should already be committed. Restore them from git, or run `python3 scripts/build_field_ontology.py` after `data/variables_long.csv` exists. |
| `Run make install first` | You are in `nodestream/` without `nodestream/.venv`. Run `make install` there. |
| `Set NEO4J_PASSWORD in .env` | `make setup` only copies the example. Edit `nodestream/.env`. |
| `NEO4J_PASSWORD is empty` from `make validate` | The password line is still blank, or the shell could not parse it. Quote values that contain spaces, `$`, or `#`. |
| `requires-python` / pip refuses the nodestream package | `nodestream/.venv` was built with Python older than 3.10. Remove `nodestream/.venv` and rerun `PYTHON=python3.12 make setup && make install`. |
| TCP or login failure from `make validate` | Neo4j is not listening on the URI in `.env`, or the password does not match. |

## Leave the tree as you found it

- Do not commit `nodestream/.env`, either `.venv`, or anything under `data/datasets_extracted/`.
- If you uncommented `max_rows` or added `study_ids` only to try a load, revert `patients.yaml` unless the task was to change that default.
