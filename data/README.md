# Data

Derived files from the analysis. **No CIBMTR patient-level data and no original CIBMTR files are committed.** Everything here is either study-level metadata, variable-level metadata (names, descriptions and value labels), or aggregate counts.

| File | Description |
|---|---|
| [`CIBMTR_NRM_dataset_analysis.xlsx`](CIBMTR_NRM_dataset_analysis.xlsx) | The analysis workbook. Sheets: README, NRM ranking (color-coded by tier, with links), Coverage A-B (1/0 predictor matrix), All variables, Common variables (A-B) |
| [`nrm_candidate_ranking.csv`](nrm_candidate_ranking.csv) | One row per study: tier, score, patient and TRM counts, NRM availability, disease scope, and, for each concept, the matching variable names |
| [`dataset_sizes.csv`](dataset_sizes.csv) | Patients (rows in the primary SAS file), columns, TRM events and crude TRM proportion per dataset |
| [`catalog.csv`](catalog.csv) | All 160 studies on the CIBMTR page, with publication, dataset and dictionary URLs (snapshot of 2026-10-03) |
| [`field_ontology.csv`](field_ontology.csv) | 2,535 canonical fields (concept and role). Built by [`scripts/build_field_ontology.py`](../scripts/build_field_ontology.py), which is not part of `make analysis` |
| [`field_dataset_mapping.csv`](field_dataset_mapping.csv) | 6,976 study variables mapped onto those fields. Same script |
| [`variables_by_study.csv`](variables_by_study.csv) | One row per study and variable, with value levels in one cell (6,976 rows) |
| [`variables_long.csv`](variables_long.csv) | Every parsed dictionary row: study_id, variable, description, type, value, label (22,520 rows) |
| [`parse_summary.csv`](parse_summary.csv) | Number of variables parsed from each dictionary |

## Not committed (git-ignored)

Created locally by [`scripts/download_cibmtr.py`](../scripts/README.md) with `--out data`:

- `dictionaries/`: the 160 original data dictionaries
- `datasets/`, `datasets_extracted/`: the dataset zips and their SAS files
- `manifest.csv`: the download log

## Key columns in `nrm_candidate_ranking.csv`

| Column | Meaning |
|---|---|
| `tier` | A core, B supplementary, B- weaker fit, C no NRM, D out of scope (see [research/03](../research/03-screening-method.md)) |
| `score` | Disease-scope + NRM-availability + predictor-coverage score |
| `n_patients`, `trm_events`, `trm_rate` | From `dataset_sizes.csv`. The rate is a crude proportion, not a cumulative incidence |
| `nrm_outcome` | explicit variable / coded inside another variable / derivable / approx. via cause of death / not available |
| `disease_scope` | leukemia/MDS, mixed, lymphoma/myeloma/MPN, non-malignant, or not an allogeneic-recipient study |
| `out_*` | Outcome concepts: the matching variable names (blank = none) |
| `p_*` | Pre-transplant predictor concepts: the matching variable names (blank = none) |
