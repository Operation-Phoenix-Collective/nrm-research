# Scripts

All functionality lives here; the root [`Makefile`](../Makefile) only calls these scripts (run `make -n <target>` to see the exact command).

| Script | Purpose | Make target | Dependencies |
|---|---|---|---|
| [`install.sh`](install.sh) | Check prerequisites; install Python if missing (Homebrew/apt/dnf, asks first), create `.venv`, install `requirements.txt` | `make install`, `make check` | bash |
| [`download_cibmtr.py`](download_cibmtr.py) | Download CIBMTR dataset zips and/or data dictionaries into a folder you choose | `make catalog`, `dictionaries`, `datasets`, `candidates`, `download` | Python 3.8+ standard library only |
| [`download_papers.py`](download_papers.py) | Download the cited papers (Europe PMC metadata, abstracts, legal open-access PDFs) and reference documents listed in `research/papers.csv` | `make papers` | standard library only |
| [`build_analysis.sh`](build_analysis.sh) | Run the whole analysis pipeline below on a data folder | `make analysis` | bash + requirements |
| [`run_tests.sh`](run_tests.sh) | Run every test in `tests/` | `make test` | bash |
| [`lib.sh`](lib.sh) | Shared shell helpers (picks `.venv/bin/python` when present) | | |
| [`parse_dictionaries.py`](parse_dictionaries.py) | Parse every dictionary (xlsx/xls/docx/rtf/pdf) into `variables_long.csv` | via `make analysis` | `openpyxl xlrd python-docx striprtf pdfplumber` |
| [`dataset_sizes.py`](dataset_sizes.py) | Count patients and TRM events in downloaded dataset zips (aggregate counts only) | via `make analysis` | `pandas` |
| [`analyze_nrm.py`](analyze_nrm.py) | Tag concepts, classify NRM availability and disease scope, then score and tier | via `make analysis` | standard library |
| [`build_workbook.py`](build_workbook.py) | Build `CIBMTR_NRM_dataset_analysis.xlsx` | via `make analysis` | `openpyxl` |
| [`make_findings_tables.py`](make_findings_tables.py) | Print the Markdown tables used in `research/04-findings.md` | | standard library |
| [`tests/test_download.py`](tests/test_download.py) | Offline test of the CIBMTR downloader against a local mock of the site | `make test` | standard library |
| [`tests/test_download_papers.py`](tests/test_download_papers.py) | Offline test of the paper downloader against a local mock of the Europe PMC API | `make test` | standard library |

Prerequisites and installation are covered in [CONTRIBUTING.md](../CONTRIBUTING.md). In short: `make install`.

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

## `download_papers.py`: papers and reference documents

Downloads the papers and documents listed in [`research/papers.csv`](../research/papers.csv) into `data/papers/` (git-ignored).

```bash
make papers                                         # or: python3 scripts/download_papers.py
python3 scripts/download_papers.py --keys shouval-2016-plosone --out ~/papers
python3 scripts/download_papers.py --no-pdf         # metadata and abstracts only
```

| Option | Default | Description |
|---|---|---|
| `-o, --out DIR` | `data/papers` | Output folder |
| `-l, --list CSV` | `research/papers.csv` | Paper list (`key,type,identifier,url,description`) |
| `-k, --keys KEY ...` | all rows | Only these keys |
| `--no-pdf` | | Don't download PDFs |
| `--no-documents` | | Skip `document` rows |

What each row produces:

- **`article` rows** (identifier `DOI:`, `PMID:` or `PMCID:`) are looked up in the [Europe PMC REST API](https://europepmc.org/RestfulWebService). The script writes:
  - `<key>.json`: raw metadata
  - `<key>.md`: citation, open-access status, licence, all access links and the abstract
  - `<key>.pdf`: only when Europe PMC lists a legal open-access PDF. The file is checked to really be a PDF.

  Subscription-only papers get the metadata and DOI link, not the PDF.
- **`document` rows** are downloaded from their `url` as a PDF or an HTML snapshot.
- **`index.md` and `manifest.csv`** summarize the run.

Current list (October 2026 status):

| Key | Item | Full text |
|---|---|---|
| `shouval-2015-jco` | Shouval et al., *J Clin Oncol* 2015 | Subscription; free author copy (HTML landing page) in the University of Liège repository |
| `mussetti-2024-bmt` | Mussetti et al., *Bone Marrow Transplant* 2024 | Subscription only |
| `shouval-2016-plosone` | Shouval et al., *PLoS One* 2016 (PMC4778768) | Open access (CC BY): PDF via Europe PMC or PLOS |
| `cibmtr-terms` | CIBMTR Terms and Conditions | PDF |
| `cibmtr-datasets-page` | CIBMTR Publicly Available Datasets page | HTML snapshot |
| `ebmt-data-sharing` | EBMT data-sharing policy page | HTML snapshot |

---

## Analysis pipeline

The short way:

```bash
make install && make dictionaries && make datasets && make analysis
```

Step by step (this is what `scripts/build_analysis.sh` runs):

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
make test          # or: scripts/run_tests.sh
```

Both tests run offline against local HTTP mocks built from real captured responses:

- **`test_download.py`** uses the CIBMTR listing page and listing response (`tests/cibmtr_fixture.json`, with the anti-forgery token replaced). It checks catalog parsing, pagination, de-duplication, ID filtering, extraction, broken-link recovery, skip-on-rerun and the manifest.
- **`test_download_papers.py`** uses a Europe PMC search response for the three papers (`tests/europepmc_fixture.json`). It checks DOI and PMCID lookup, the open-access PDF download (and its `%PDF` check), the HTML-only and subscription-only cases, document downloads, not-found handling, `--keys`, `--no-pdf` and the index and manifest.
