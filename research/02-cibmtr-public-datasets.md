# 2. The CIBMTR publicly available datasets

[← Previous](01-question-and-ebmt-data-access.md) · [Research index](README.md) · [Next: screening method →](03-screening-method.md)

## What CIBMTR offers

The Center for International Blood and Marrow Transplant Research (CIBMTR), the main US transplant registry, publishes the de-identified **analysis dataset from many of its published studies** as a free download:
<https://cibmtr.org/CIBMTR/Resources/Publicly-Available-Datasets>

- **160 studies** were listed when this snapshot was taken (2026-10-03), spread over 8 pages.
- Each study has a link to the publication, a **dataset zip** and a **data dictionary**.
- Each dataset zip contains a SAS `.sas7bdat` data file, usually a copy of the dictionary, sometimes a `formats.sas7bcat` value-label catalog or a summary table, and the Terms and Conditions PDF.
- The full set of 160 dataset zips is about **120 MB** (downloaded with [`scripts/download_cibmtr.py`](../scripts/README.md) on 2026-10-03; 160 of 160 succeeded).
- Dictionary formats: 130 xlsx, 15 rtf, 9 docx, 4 xls (some are Excel 2003 XML) and 2 pdf. Most follow a *Variable / Description / Type / Value / Label* layout.

## Site quirks

- **Seven dictionary links are broken.** For P-5181, P-5243, P-5262, P-5273, P-5282, P-5398 and P-5581 the site returns its own web page instead of the file. The dictionary is still inside each dataset zip, and the downloader recovers it automatically.
- **The listing is paged with JavaScript.** Pages 2–8 come from a form POST to `/DataAjax/GetDataListResults` that needs the page's anti-forgery token and cookie. The downloader handles this.

## Terms and Conditions (summary)

Every dataset zip includes *Terms of Use and Conditions for Publicly Available Research Datasets for Secondary Analysis*. Read the full text before use. The key points:

- Downloading a dataset means agreeing to the terms.
- **Credit CIBMTR:** all publications and presentations must acknowledge CIBMTR as a data source and include CIBMTR's specified funding acknowledgement statement.
- **No sale** of information derived from the data without CIBMTR's written permission.
- **Protect the data.** Do not share it with others, and keep administrative, technical and physical safeguards in place.
- **Do not re-identify anyone,** link the data to identify individuals, or **combine it with other patient-level information.**
- **Do not make copies or release the files or data** to anyone without CIBMTR's written approval.
- Only staff with a need to know may access the data. **Destroy the data** when the approved use is complete.
- Follow applicable law and IRB oversight. Publications must state that the study followed human-subjects protection laws.
- **EU patient-level data is redacted,** so a public dataset may not contain the same patients as its publication, and published results may not be fully reproducible.

This is why this repository **does not contain any CIBMTR datasets or dictionary files**. It contains the scripts to fetch them, plus variable-level metadata (names, descriptions and value labels; no patient records) derived from the dictionaries.

## How this compares with the EBMT data

| | EBMT (the two starting papers) | CIBMTR public datasets |
|---|---|---|
| Access | Formal request and approval | Free download, subject to the terms |
| Unit | One registry extract designed for the study | 160 separate per-paper analysis files |
| Size | 28,000–34,000 patients in one model | Hundreds to a few thousand patients per file |
| Harmonization | Single schema | Each file has its own variables and coding |
| Geography | Europe | Mostly US; EU patients redacted |
