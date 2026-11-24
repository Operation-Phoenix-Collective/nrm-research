# CIBMTR graph

One Nodestream project loads every extracted public dataset into a single Neo4j graph. Rows are read with [nodestream-plugin-sas](https://github.com/ccloes/nodestream-plugin-sas). Columns are renamed with `data/field_dataset_mapping.csv` and `data/field_ontology.csv`.

Patient identifiers are unique only inside one study. Centers are the same. Do not join those keys across `study_id`.

## Graph

![Patient enrolled in a Study, treated at a Center, and linked to a Field](./queries/schema.jpg)

| | |
|---|---|
| `(:Study {study_id})` | One publication dataset |
| `(:Patient {study_id, patient_id})` | One person in that study. `id_source = row` means the file had no patient pseudonym |
| `(:Field {field_id})` | One ontology field, including study-specific fields |
| `(:Center {study_id, center_id})` | Transplant center, when the file has one |
| `(:Patient)-[:ENROLLED_IN]->(:Study)` | |
| `(:Patient)-[:TREATED_AT]->(:Center)` | |
| `(:Patient)-[v:HAS_VALUE {source_variable}]->(:Field)` | `value_num`, `value_text`, `unit` |

Event and competing-risk labels `Yes`, `Event`, `Dead`, `Relapse` become `value_num = 1`. `No`, `Censor…`, and `Alive` become `0`. `Missing` is dropped. A label that is neither is stored raw. Times declared in days are stored in months (`unit = 'months'`). A time with no declared unit is stored as reported and `unit` is blank.

`Field.stack` is `recode`, `crosswalk`, `derive_from_continuous`, or `do_not_stack`. Pool only the first across studies. `do_not_stack` fields are still loaded so a single study can be queried.

## Run

Start from the repo root. The short form is in the root [README](../README.md#quick-start). This section is the full path. An agent doing it from a fresh clone should follow [AGENTS.md](../AGENTS.md).

Neo4j is not installed by this repo. It has to be listening before `make validate` or `make ingest`. The sample values in [`.env.example`](.env.example) are `bolt://localhost:7687` and user `neo4j`.

```bash
# from the repo root
make install        # repo .venv; Python 3.8+ is enough for the downloader and analysis
make download       # dictionaries and every dataset, unzipped
                    # SAS files: data/datasets_extracted/P-*/
# start Neo4j, then:
cd nodestream
make setup          # .venv and .env from .env.example; does not overwrite an existing .env
# set NEO4J_PASSWORD in .env
make install        # Nodestream, the Neo4j plugin, and the SAS plugin (from GitHub)
make validate       # check .env and log in to Neo4j once
make ingest         # migrations, then fields, studies, and patients into Neo4j
```

This project's `pyproject.toml` requires Python 3.10 or newer. The repo-root `.venv` can be 3.8. If `python3` on the machine is older than 3.10, create this venv with a newer interpreter: `PYTHON=python3.12 make setup`.

`make ingest` reads `.env` itself and exports `NEO4J_URI`, `NEO4J_USERNAME`, and `NEO4J_PASSWORD` for `nodestream.yaml`. You do not export them by hand when you use `make`. `make ingest` also runs `make install` and, for `TARGET=neo4j`, `make validate`, then `nodestream migrations` and `nodestream run`.

`make ingest` stops unless these exist:

| Path | How it gets there |
|---|---|
| `../data/datasets_extracted/` | `make download` or `make datasets` from the repo root. The error names `make -C .. download`. |
| `../data/catalog.csv` | Already committed. `make catalog` refreshes it from the CIBMTR site. |
| `../data/field_ontology.csv` | Already committed. |
| `../data/field_dataset_mapping.csv` | Already committed. |

`make analysis` does not write the two field files. After a dictionary reparse, rebuild them with `python3 scripts/build_field_ontology.py` from the repo root. That step is described in the [scripts guide](../scripts/README.md#analysis-pipeline).

Three pipelines run, in order: `fields` (`field_ontology.csv` → `Field`), `studies` (`catalog.csv` → `Study`), `patients` (SAS files → `Patient`, `Center`, and `HAS_VALUE`). Limit the run with `make ingest PIPELINES="fields studies"`.

`max_rows` under `StudySasExtractor` in `patients.yaml` is commented out, so `make ingest` loads every row of every SAS file. Uncomment `max_rows: 500` before ingest to keep a stable random 500 from each file, seeded by the study id, so a rerun keeps the same rows. A file of 500 or fewer rows is kept whole. Forty-three of the 160 studies have a primary file under 500 rows. Three studies also have a second SAS file (`P-5238`, `P-5375`, `P-5924`), and that file is sampled on its own. Comment `max_rows` out again to load every row.

`make pare-down` deletes patients and centers already in Neo4j. Field and Study nodes stay. The next `make ingest` then follows whatever `max_rows` is set to. From the repo root the same target is `make pare-down`. `make ingest TARGET=dry-run` parses and discards the graph, which checks the project without Neo4j. To try one study, add `study_ids: [P-5051]` under `StudySasExtractor` in `patients.yaml`.

Questions to ask of the graph are in [queries/questions.md](queries/questions.md).

The graph holds patient-level values. Keep it local; the CIBMTR terms that ship inside each dataset zip still apply.
