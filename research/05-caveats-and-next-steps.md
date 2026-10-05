# 5. Caveats and next steps

[← Previous](04-findings.md) · [Research index](README.md)

## Caveats

### About the data

- **Each file belongs to one paper.** Each dataset is the analysis file of a single publication, so inclusion criteria, transplant eras and variable coding differ. Pooling them requires a harmonization map. The *Common variables (A-B)* sheet of the workbook shows the names that recur most (`dead`, `intxsurv`, `intxrel`, `trm`, `rel`, `age`, `kps`, `hctcigp`, `condint`, `donorgp`, ...).
- **Studies overlap.** Patient IDs are scrambled separately for each study, so the same patient can appear in several datasets and cannot be matched. Some pairs look like the same cohort: **P-5390 and P-5597** have identical patient (5,108) and TRM (1,362) counts, and **P-5356 and P-5737** both have 2,744 patients. Treat pooled data as non-independent, or pick one file per cohort.
- **EU patients are redacted.** Results computed from a public file may not reproduce the published paper.
- **Some zips are unusual.**
  - **P-6157** contains a dictionary but no data file.
  - **P-5375**, **P-5238** and **P-5924** contain two data files. The largest is counted. P-5375's second file is a 46-patient dialysis subgroup; P-5238 and P-5924 have separate allogeneic and autologous files.
- **Crude TRM proportions are not cumulative incidence.** Competing-risk methods (Fine–Gray, cause-specific hazards) are needed for a proper NRM estimate, and every study has follow-up times (`intxsurv`, `intxrel`).

### About the screening

- **Tags are automated.** Concept flags come from keyword matching on the dictionaries. A ✓ means a matching variable exists, not that it is well populated. Check the dictionary and the missingness before modelling.
- **Disease scope comes mostly from titles.** Mixed-disease studies (tier B) need filtering on their disease variable.

### About the terms of use

- The [CIBMTR Terms and Conditions](02-cibmtr-public-datasets.md#terms-and-conditions-summary) prohibit releasing copies of the data. This repository therefore holds **no datasets or dictionary files**, only scripts and aggregate or variable-level metadata.
- The terms also say not to **"combine the data with other patient-level information"**. Pooling several CIBMTR public files, or merging them with EBMT or local data, may fall under this. **Confirm with CIBMTR before pooling.**
- Publications must acknowledge CIBMTR with its funding statement, and must state that human-subjects protections were followed.

## Next steps

1. **Profile the tier A data.** For the top tier A datasets, report missingness for each predictor and NRM cumulative incidence (competing risk) at Day 100 and 1 year.
2. **Single-study baseline.** Fit a baseline NRM model on one large file (P-5646, P-5702 or P-5370) with the predictor set used in the EBMT papers. Compare logistic regression or Fine–Gray, gradient boosting and elastic net.
3. **External validation.** Validate on other tier A files that don't share a cohort, for example a model trained on AML (P-5370) tested on AML (P-5435, P-5603), with ALL (P-5521) as a disease-shift test.
4. **Harmonization map.** Build a mapping for the recurring variables (age, KPS, HCT-CI, disease status, donor type, conditioning, GVHD prophylaxis, CMV) if pooling is cleared with CIBMTR.
5. **EBMT route in parallel.** Pursue EBMT access through a member centre or working party if replicating the original EBMT models is a goal.
