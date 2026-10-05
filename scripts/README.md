# Scripts

| Script | Purpose | Dependencies |
|---|---|---|
| [`download_cibmtr.py`](download_cibmtr.py) | Download CIBMTR dataset zips and/or data dictionaries into a folder you choose | Python 3.8+ standard library only |
| [`parse_dictionaries.py`](parse_dictionaries.py) | Parse every dictionary (xlsx/xls/docx/rtf/pdf) into `variables_long.csv` | `openpyxl xlrd python-docx striprtf pdfplumber` |
| [`analyze_nrm.py`](analyze_nrm.py) | Tag concepts, classify NRM availability and disease scope, then score and tier | standard library |
| [`dataset_sizes.py`](dataset_sizes.py) | Count patients and TRM events in downloaded dataset zips (aggregate counts only) | `pandas` |
| [`build_workbook.py`](build_workbook.py) | Build `CIBMTR_NRM_dataset_analysis.xlsx` | `openpyxl` |
| [`make_findings_tables.py`](make_findings_tables.py) | Print the Markdown tables used in `research/04-findings.md` | standard library |
| [`tests/test_download.py`](tests/test_download.py) | Offline test of the downloader against a local mock of the site | standard library |

```bash
pip3 install -r requirements.txt   # from the repo root; only needed for the analysis scripts
```

---

## `download_cibmtr.py`: the download utility

Downloads CIBMTR "Publicly Available Datasets" (dataset zips and/or data dictionaries) into a folder you choose.

**Verified against the live site on 2026-10-03:** all 160 datasets downloaded (about 120 MB), and all 160 dictionaries were obtained, 7 of them recovered from the dataset zips.

> Downloading means accepting the [CIBMTR Terms and Conditions](https://cibmtr.org/Files/Publicly-Available-Datasets/TermsAndConditions.pdf): do not redistribute the data, credit CIBMTR in publications, and destroy the data after use. Do **not** commit downloaded files to this repository; `data/datasets/` and `data/dictionaries/` are already in `.gitignore`.

### Quick start

```bash
# Everything: all datasets and all dictionaries
python3 scripts/download_cibmtr.py --out data

# All datasets only, unzipped
python3 scripts/download_cibmtr.py --out data --what datasets --extract

# Dictionaries only
python3 scripts/download_cibmtr.py --out data --what dictionaries

# Specific studies
python3 scripts/download_cibmtr.py --out data --ids P-5646 P-5702 P-5370

# Only the tier A studies from this analysis
python3 scripts/download_cibmtr.py --out data --ids-from data/nrm_candidate_ranking.csv --tier A --extract

# Refresh the catalog without downloading anything
python3 scripts/download_cibmtr.py --out data --list-only
```

Using `--out data` puts files where the analysis scripts expect them. Any other folder works too, for example `--out ~/Documents/CIBMTR-data`.

### Options

| Option | Default | Description |
|---|---|---|
| `-o, --out DIR` | *(required)* | Download folder; created if missing. `~` is expanded |
| `-w, --what` | `all` | `all`, `datasets` or `dictionaries` |
| `--ids P-XXXX ...` | all studies | Only these study IDs |
| `--ids-from CSV` | | Only study IDs found in a CSV's `study_id` column |
| `--tier T ...` | | With `--ids-from`: keep rows whose `tier` column starts with one of these (e.g. `A B`) |
| `--catalog CSV` | read the live site | Use a saved catalog instead of the website's list (e.g. `data/catalog.csv`) |
| `--list-only` | | Write `catalog.csv` and stop |
| `--extract` | | Unzip each dataset into `datasets_extracted/<study>/` |
| `--overwrite` | | Re-download files that already exist (otherwise they are skipped) |
| `--delay SECONDS` | `0.5` | Pause between downloads |
| `--retries N` | `3` | Attempts per file, with exponential back-off |
| `--timeout SECONDS` | `120` | Per-request timeout |
| `-q, --quiet` | | Suppress progress output |

### Output layout

```
<out>/
├── catalog.csv                  every study found, with URLs
├── manifest.csv                 one row per file: status, bytes, sha256, timestamp
├── datasets/P-XXXX.zip          SAS data + dictionary + Terms and Conditions
├── datasets_extracted/P-XXXX/   (with --extract)
└── dictionaries/
    ├── P-XXXX__<original name>
    ├── P-XXXX__from-dataset-zip__<name>   recovered when the site link is broken
    └── _broken_site_links/                pages the site served instead of a file
```

### How it works

1. **Catalog.** Loads the listing page (which sets the session cookie and anti-forgery token) and parses page 1. It then POSTs to the site's listing endpoint (`/DataAjax/GetDataListResults`) for the remaining pages and removes duplicates.
2. **Selection.** Applies `--ids`, `--ids-from` and `--tier`, and warns about any requested ID that isn't on the site.
3. **Download.** Each file is streamed to `*.part` and renamed when complete. Existing files are skipped, so **re-running is safe and resumes where it stopped.**
4. **Broken links.** If the site returns an HTML page instead of a dictionary, the page is set aside in `_broken_site_links/` and the dictionary is extracted from the dataset zip instead (the zip is fetched temporarily if needed).
5. **Manifest.** Every attempt is logged with its status (`downloaded`, `skipped (exists)`, `broken link`, `extracted`, `failed: ...`), size and SHA-256.
6. **Exit code.** `0` on success, `1` if any file failed.

If the site's list can't be read (for example after a redesign), the script falls back to an existing `catalog.csv` in the output folder, or you can pass `--catalog data/catalog.csv`.

---

## Analysis pipeline

```bash
pip3 install -r requirements.txt
python3 scripts/download_cibmtr.py --out data --what dictionaries   # step 1: fetch the dictionaries
python3 scripts/parse_dictionaries.py                               # -> data/variables_long.csv, parse_summary.csv
python3 scripts/download_cibmtr.py --out data --what datasets       # optional: fetch the data for counts
python3 scripts/dataset_sizes.py data                               # -> data/dataset_sizes.csv
python3 scripts/analyze_nrm.py                                      # -> data/nrm_candidate_ranking.csv, variables_by_study.csv
python3 scripts/build_workbook.py                                   # -> data/CIBMTR_NRM_dataset_analysis.xlsx
python3 scripts/make_findings_tables.py A                           # Markdown table for tier A (or B)
```

- **Data folder:** the analysis scripts read and write `data/` by default. Pass a different folder as the first argument, or set `CIBMTR_DATA_DIR`.
- **Patient counts are optional:** `analyze_nrm.py` adds them to the ranking only if `data/dataset_sizes.csv` exists.
- **Reproducibility:** the committed outputs in `data/` were produced by exactly this pipeline, and rerunning it on the same dictionaries gives identical CSVs.

### Reading the datasets

Datasets are SAS `.sas7bdat` files, sometimes with a `formats.sas7bcat` catalog of value labels.

```python
import pandas as pd
df = pd.read_sas("data/datasets_extracted/P-5370/P-5370 (LK16-02)/lk1602public.sas7bdat", encoding="latin-1")

import pyreadstat   # with value labels
df, meta = pyreadstat.read_sas7bdat("...sas7bdat", catalog_file="...sas7bcat")
```

```r
library(haven)
df <- read_sas("...sas7bdat", "...sas7bcat")
```

---

## Tests

```bash
python3 scripts/tests/test_download.py
```

This runs the downloader against a local HTTP mock of cibmtr.org built from a real captured listing page and listing response (`tests/cibmtr_fixture.json`, with the anti-forgery token replaced). It checks catalog parsing, pagination, de-duplication, ID filtering, extraction, broken-link recovery, skip-on-rerun and the manifest.
