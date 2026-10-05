# 3. How the datasets were screened

[← Previous](02-cibmtr-public-datasets.md) · [Research index](README.md) · [Next: findings →](04-findings.md)

The goal was to rank all 160 CIBMTR public datasets by how well they could support a model that predicts **NRM/TRM after allogeneic HCT for leukemia or MDS** from information available before transplant. Every step is scripted (see [scripts/README.md](../scripts/README.md)).

## Pipeline

| Step | Script | Output |
|---|---|---|
| 1. Catalog the site (all 8 listing pages) | `download_cibmtr.py --list-only` | `data/catalog.csv` |
| 2. Download all 160 data dictionaries, recovering the 7 broken links from the dataset zips | `download_cibmtr.py --what dictionaries` | `data/dictionaries/` (not committed) |
| 3. Parse the dictionaries into one table | `parse_dictionaries.py` | `data/variables_long.csv` (22,520 rows), `data/parse_summary.csv` |
| 4. Tag concepts, classify NRM availability and disease scope, then score and tier | `analyze_nrm.py` | `data/nrm_candidate_ranking.csv`, `data/variables_by_study.csv` (6,976 variables) |
| 5. Download the datasets and count patients and TRM events | `download_cibmtr.py --what datasets`, then `dataset_sizes.py` | `data/dataset_sizes.csv` (aggregate counts only) |
| 6. Build the workbook | `build_workbook.py` | `data/CIBMTR_NRM_dataset_analysis.xlsx` |

## Parsing the dictionaries

The dictionaries come in five formats (xlsx, Excel-2003 XML saved as .xls, docx, rtf and pdf). The parser finds the header row (*Variable / Description / Type / Value / Label* and its variants, such as *Variable name / Definition / Code*), carries the variable name forward across its value-label rows, and falls back to text-layout parsing for the two PDFs. All 160 dictionaries parsed, with a median of 42 variables each (maximum 145).

## Concept tagging

Keyword rules applied to each variable's name and description flag:

- **Outcomes:** NRM/TRM, overall survival, relapse, disease-free survival, cause of death, acute and chronic GVHD, and time-to-event intervals.
- **Pre-transplant predictors:** age, Karnofsky performance score (KPS), HCT comorbidity index (HCT-CI), disease risk index (DRI), disease, disease status/remission, cytogenetics/MRD, donor type, HLA match, graft source, conditioning intensity, TBI, GVHD prophylaxis, ATG/alemtuzumab, CMV serostatus, donor–recipient sex match, transplant year, time from diagnosis to transplant, and race/socioeconomic status.

The ranking lists the **actual variable names** matched for each concept, which serves as a starting point for harmonizing variables across studies.

## Is NRM available?

| Class | Rule | Studies in tiers A–B |
|---|---|---:|
| Explicit variable | A variable such as `trm` or `nrm` | 94 |
| Coded inside another variable | Value labels mention TRM/NRM (e.g. P-5300 `relstat`: 0 = censored, 1 = relapse, 2 = TRM) | 1 |
| Derivable | Death plus relapse (or DFS) present, so NRM = death without prior relapse (a competing risk) | 3 |
| Approximate via cause of death | Death and cause of death only | 3 |
| Not available | None of the above | (tier C) |

## Disease scope

Assigned from the study title, falling back to the disease variable's value labels:

- leukemia/MDS (title)
- mixed malignancies including leukemia/MDS
- lymphoma/myeloma/MPN (including myelofibrosis and plasma cell leukemia)
- non-malignant (aplastic anemia, sickle cell, HLH and similar)
- not an allogeneic-recipient study (autologous, CAR-T, donor-safety, COVID)

## Score and tiers

**Score** = disease-scope weight + NRM availability weight + weighted presence of predictors. HCT-CI, KPS, DRI and conditioning carry the most weight, followed by disease status and donor type.

| Tier | Rule | Count |
|---|---|---:|
| **A**: core training candidate | Leukemia/MDS title, NRM available, score ≥ 85 | 31 |
| **B**: useful / supplementary | Leukemia/MDS or mixed malignancies, NRM available, score ≥ 70 | 48 |
| **B-**: NRM present, weaker fit | NRM available, but lymphoma/myeloma/MPN or an unclear population | 22 |
| **C**: no NRM/TRM | NRM not available | 17 |
| **D**: out of scope | Not an allogeneic-recipient study | 42 |

## Patient and event counts

`dataset_sizes.py` opens each downloaded zip, takes the largest `.sas7bdat` as the primary analysis file, and records the row count and, where a variable named exactly `trm` is coded 0/1, the number of TRM events. **The TRM rate is a crude proportion, not a cumulative incidence.** Only these aggregate counts are written to the repository.
