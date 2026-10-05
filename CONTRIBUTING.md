# Contributing

Thanks for your interest in improving this project. It collects research notes, derived metadata and tools for finding open data to model non-relapse mortality (NRM) after allogeneic transplant. Contributions are welcome: bug fixes, better parsing, new analyses, corrections to the research write-ups, and new candidate datasets or papers.

This guide covers [prerequisites](#prerequisites), [installation](#installation), [getting the data](#getting-the-data), the [development workflow](#development-workflow) and the [data-use rules](#data-use-rules-read-before-contributing) every contributor must follow.

## Code of conduct

Be respectful, constructive and patient. We follow the spirit of the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). Report unacceptable behavior to the maintainers through a private channel (see [Getting help](#getting-help)).

## Prerequisites

| Requirement | Version | Needed for | How to get it |
|---|---|---|---|
| Python | 3.8 or newer | Everything | macOS: `brew install python` · Debian/Ubuntu: `sudo apt install python3 python3-venv python3-pip` · Fedora: `sudo dnf install python3` · Windows: use [WSL](https://learn.microsoft.com/windows/wsl/install), or install from [python.org](https://www.python.org/downloads/) |
| GNU Make | any recent | The `make` shortcuts (optional; every target is a script in `scripts/`) | macOS: `xcode-select --install` · Debian/Ubuntu: `sudo apt install make` |
| Git | any recent | Contributing changes | macOS: `xcode-select --install` · Debian/Ubuntu: `sudo apt install git` |
| Bash | 3.2 or newer | `scripts/*.sh` | Preinstalled on macOS and Linux; use WSL on Windows |
| Internet access | | Downloads only, to `cibmtr.org` and `www.ebi.ac.uk` (Europe PMC) | Some corporate networks block these hosts |
| Disk space | about 300 MB | All datasets (120 MB zipped) plus extracted copies | |

Python packages are listed in [`requirements.txt`](requirements.txt). **The two downloaders need only the Python standard library.** The packages are used by the analysis scripts (dictionary parsing, dataset counts and the workbook).

## Installation

### Recommended: `make install`

```bash
git clone https://github.com/<owner>/<repo>.git
cd <repo>
make install        # checks prerequisites, creates .venv, installs requirements.txt
make check          # optional: re-run the checks without changing anything
make test           # offline tests; should all pass
```

`make install` runs [`scripts/install.sh`](scripts/install.sh), which:

1. Finds Python 3.8+. If it's missing, it offers to install it with Homebrew, apt or dnf (asking first; pass `ARGS=--yes` to skip the prompts).
2. Reports whether `git` and `make` are present.
3. Creates a virtual environment in `.venv/` (installing `python3-venv` if your distribution split it out) and installs `requirements.txt` into it.
4. Verifies each package imports, and checks that `cibmtr.org` and Europe PMC are reachable.

Every other `make` target uses `.venv` automatically when it exists.

Options (pass them through `ARGS`, or call the script directly):

```bash
make install ARGS=--no-venv    # install with pip --user instead of a virtual environment
make install ARGS=--yes        # don't prompt before installing system packages
PYTHON=python3.12 make install # choose the interpreter used for .venv
```

### Manual installation

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows (WSL): same; PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/tests/test_download.py && python scripts/tests/test_download_papers.py
```

### Without `make`

Every Makefile target is a one-line call to a script in `scripts/`; run `make -n <target>` to see it. For example, `make datasets` is:

```bash
python3 scripts/download_cibmtr.py --out data --what datasets --extract
```

## Getting the data

Run `make help` for the full list of targets.

| Command | What it does |
|---|---|
| `make catalog` | Refresh `data/catalog.csv` from the CIBMTR site (no downloads) |
| `make dictionaries` | Download all 160 data dictionaries into `data/dictionaries/` |
| `make datasets` | Download and unzip all datasets into `data/datasets/` and `data/datasets_extracted/` (about 120 MB zipped) |
| `make candidates` | Only the NRM candidate studies: tier A by default, or `TIER="A B"` |
| `make download` | All datasets and dictionaries |
| `make papers` | The cited papers and reference documents listed in [`research/papers.csv`](research/papers.csv), saved to `data/papers/` |
| `make research` | Everything the research write-ups rely on (`papers` + `dictionaries`) |
| `make analysis` | Rebuild every derived file in `data/` from what you've downloaded |

Common variables:

```bash
make datasets IDS="P-5646 P-5702 P-5370"     # specific studies
make download OUT=~/Data/cibmtr              # a different folder
make dictionaries ARGS="--overwrite"         # extra flags for the script
make candidates TIER="A B"                   # tiers A and B
```

**About papers:** `make papers` only downloads PDFs that are legally open access (via Europe PMC). For subscription-only papers it saves the citation, abstract and DOI link, so you can get the full text through a library.

## Project layout

```
README.md            overview and table of contents
CONTRIBUTING.md      this file
Makefile             thin wrapper; all logic lives in scripts/
requirements.txt     Python packages for the analysis scripts
research/            the write-ups (Markdown) and papers.csv (the list of cited papers)
scripts/             downloaders, analysis pipeline, install and test scripts
  tests/             offline tests and captured fixtures
data/                derived, shareable outputs; downloads land here (git-ignored)
```

## Development workflow

1. **Open an issue first** for anything bigger than a typo, so the approach can be agreed before you invest time.
2. **Fork and branch** from `main`, using a descriptive name such as `fix/rtf-parser-merged-cells` or `research/add-cibmtr-2027-datasets`.
3. **Make focused changes.** One logical change per pull request.
4. **Run the tests:** `make test` must pass. Add or update a test in `scripts/tests/` for any change to download or parsing behavior. Tests must run offline: use a local mock server and a captured fixture, as the existing tests do.
5. **Regenerate the outputs** if your change affects them: `make analysis`. Then update the tables in `research/04-findings.md` with `python3 scripts/make_findings_tables.py A` (and `B`), and commit the regenerated files in `data/` together with the code change.
6. **Open a pull request** that explains *what* changed and *why*, links the issue, and notes any change to the findings (for example, a study moving between tiers).

### Coding conventions

- **Python 3.8 compatible.** Follow [PEP 8](https://peps.python.org/pep-0008/); keep functions small and use clear names.
- **No dependencies in the downloaders.** `download_cibmtr.py` and `download_papers.py` must stay standard-library only, so anyone can run them without installing anything.
- **Scripts are configurable and polite.** Every script takes its input and output folders as arguments with sensible defaults, prints progress, and returns a non-zero exit code on failure. Be gentle with remote servers: keep the default delays and retries.
- **Logic belongs in scripts.** Shell scripts use `set -euo pipefail` and source `scripts/lib.sh` for the interpreter choice. Keep the Makefile thin: a new target should be one line calling a script.

### Documentation

- **Research write-ups** live in `research/`, numbered in reading order. If you add one, link it from `research/README.md` and from the table of contents in the root `README.md`.
- **New papers:** add a row to `research/papers.csv` (`key,type,identifier,url,description`). Articles use `DOI:`, `PMID:` or `PMCID:` identifiers; documents use a `url`.
- **State the evidence.** Separate what the data shows from interpretation, and note the date of any snapshot of a website.

### Commit messages

Use the imperative mood with a short summary line (about 72 characters or fewer), a blank line, then the details. For example:

```
Recover dictionaries from dataset zips when the site link is broken

The CIBMTR site returns an HTML page for 7 dictionary links. Detect HTML
responses, move them aside and extract the dictionary from the zip.
```

## Data-use rules (read before contributing)

The CIBMTR datasets are governed by the [CIBMTR Terms and Conditions](https://cibmtr.org/Files/Publicly-Available-Datasets/TermsAndConditions.pdf). By downloading them you accept those terms. For this repository that means:

- **Never commit CIBMTR data files:** no datasets, `.sas7bdat` or `.sas7bcat` files, original dictionaries, or patient-level extracts of any kind. `.gitignore` covers the default locations; check `git status` before every commit.
- **Only commit aggregate or variable-level metadata:** counts, variable names, descriptions and value labels. Never commit row-level data, small-cell counts that could identify a patient, or anything that links records.
- **Don't combine CIBMTR files with other patient-level data** (including each other) in committed code or outputs without written approval from CIBMTR.
- **Credit CIBMTR** using its funding acknowledgement statement in any publication or presentation that uses the data.
- **Don't commit downloaded papers.** `data/papers/` is git-ignored because most PDFs and abstracts are copyrighted. Commit only `research/papers.csv` entries.

Pull requests that add restricted data will be closed, and the history will be rewritten to remove it.

## Reporting bugs and requesting features

Open a GitHub issue with:

- what you ran (the exact command), and what you expected versus what happened
- the relevant output (the error message, and the `manifest.csv` row if a download failed)
- your OS and Python version (`make check` prints both)

Sites change: if the CIBMTR listing or Europe PMC responses change format, say so in the issue, and if possible attach a fresh capture. Never include patient data.

## Getting help

Open a GitHub issue or discussion. For anything sensitive, such as a data-use concern or a conduct report, contact the maintainers privately through the email on their GitHub profile.

## License

No license has been chosen yet. Until one is added, contributions are accepted on the understanding that they will be released under the license the maintainers adopt. CIBMTR data always remains under CIBMTR's own terms.
