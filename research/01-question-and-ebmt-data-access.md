# 1. The question, and access to the EBMT data

[← Research index](README.md) · [Next: CIBMTR public datasets →](02-cibmtr-public-datasets.md)

## The question

Can we get the patient-level data behind published machine-learning models of mortality after allogeneic hematopoietic cell transplant (HCT), so we can run our own analysis? If not, where can we get comparable data?

The outcome of interest is **non-relapse mortality (NRM)**, also called **treatment- or transplant-related mortality (TRM)**: death from transplant toxicity (infection, GVHD, organ failure) rather than from the leukemia coming back.

## The two starting papers

### Shouval R, et al., *J Clin Oncol* 2015;33:3144–3151

*Prediction of Allogeneic Hematopoietic Stem-Cell Transplantation Mortality 100 Days After Transplantation Using a Machine Learning Algorithm.*
DOI [10.1200/JCO.2014.59.1339](https://doi.org/10.1200/JCO.2014.59.1339) · PMID [26240227](https://pubmed.ncbi.nlm.nih.gov/26240227/)

- **Data:** EBMT registry, Acute Leukemia Working Party; about 28,000 adults with acute leukemia.
- **Method:** alternating decision tree (ADT) predicting Day +100 mortality from pre-transplant information. It outperformed the conventional EBMT risk score, but prediction remained far from perfect.
- **Data access:** the journal site blocked automated reading, so we could not read this paper's own data statement. A later EBMT data-mining study of 25,923 acute leukemia patients ([PMC4778768](https://pmc.ncbi.nlm.nih.gov/articles/PMC4778768)), states that EBMT does not allow registry data to be made public, for ethical reasons. Requests are directed to the Working Party chair (Prof. Arnon Nagler).

### Mussetti A, et al., *Bone Marrow Transplant* 2024;59:232–238

*Artificial intelligence methods to estimate overall mortality and non-relapse mortality following allogeneic HCT in the modern era: an EBMT-TCWP study.*
DOI [10.1038/s41409-023-02147-5](https://doi.org/10.1038/s41409-023-02147-5) · PMID [38007531](https://pubmed.ncbi.nlm.nih.gov/38007531/)

- **Data:** EBMT registry, 2010–2019; 33,927 adults with an allogeneic HCT for a hematologic malignancy, including 4,386 haploidentical transplants.
- **Method:** 70/15/15 split for training, optimization and validation. Gradient boosting was best for overall mortality (AUC 0.64) and elastic net for NRM (AUC 0.62). Logistic regression, support-vector machines and XGBoost were also tested. Analysis was done in R; no code or online tool was released.
- **Data availability statement:** "The study data belong to the EBMT and may be requested through previous authorization."

## Conclusion: the EBMT data is not openly available

Both papers use the EBMT registry, which is not public.

- **Who can request it:** EBMT member centres and study groups. Each request needs approval from the centre's principal investigator and from EBMT, is time-limited and must comply with GDPR.
- **How:** contact the Registry Helpdesk at registryhelpdesk@ebmt.org, which sends the appropriate request form. The service is currently free. See [EBMT Data Sharing](https://www.ebmt.org/registry/ebmt-data-sharing).
- **In practice:** outside researchers usually get access by partnering with an EBMT centre or working party on a proposed study.

The most practical openly available alternative is the CIBMTR public dataset collection, covered next.
