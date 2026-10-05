# 4. Findings

[← Previous](03-screening-method.md) · [Research index](README.md) · [Next: caveats and next steps →](05-caveats-and-next-steps.md)

## Summary

- **The data behind the two EBMT papers is not available** without a formal EBMT request ([section 1](01-question-and-ebmt-data-access.md)).
- **CIBMTR's public collection is a workable substitute.** Of 160 studies, **31 are core candidates (tier A)** for NRM prediction in leukemia/MDS and **48 more are useful supplements (tier B)**. Together they hold about **300,000 patient rows**: 58,622 in tier A and 243,161 in tier B (before removing overlap; see [caveats](05-caveats-and-next-steps.md)).
- **No single file matches the EBMT scale.** The largest tier A dataset has 7,551 patients, compared with 28,000–34,000 in the EBMT models. Larger tier B files, of 13,000–18,500 patients, mix diseases.
- **Crude TRM proportions in tier A range from 13% to 31%** (27 of 31 studies have a 0/1 `trm` variable), which is plausible for allogeneic HCT and gives enough events to model.
- **Only one dataset comes from an actual prediction-model paper** in leukemia/MDS (P-5300, Nazha, MDS). Two more come from scoring-system papers in mixed-disease groups (P-6062, P-5542).

## Recommendations

### Start here: large leukemia/MDS datasets with a full predictor set

| Study | Patients | Why |
|---|---:|---|
| **P-5646** | 7,551 | Acute leukemia/MDS (C. difficile study). Largest tier A file; has HCT-CI, KPS, disease status, cytogenetics, conditioning and donor |
| **P-5329** | 5,508 | AML: de novo, post-MDS and blast-phase MPN. Same broad predictor set |
| **P-5702** | 4,946 | Acute leukemia (ABO mismatch). HCT-CI, KPS, disease status, conditioning, donor |
| **P-5370** | 4,387 | AML/MDS, myeloablative vs reduced-intensity conditioning by disease risk |
| **P-5521** | 4,037 | ALL, haploidentical vs sibling, unrelated or cord blood donors |
| **P-5435** | 3,677 | AML, risk classification at diagnosis (intermediate, adverse and KMT2A-rearranged) |
| **P-5603** | 3,065 | AML, induction and consolidation cycles before transplant |
| **P-5445**, **P-5531** | 2,492 / 2,253 | AML: depth of response in first remission, and adapted ELN genetic risk |

### Most complete predictor set, but small

- **P-6238** (938 patients, pediatric and young adult AML) and **P-5411** (603, MDS) are the only tier A files with DRI as well as HCT-CI, KPS, cytogenetics, conditioning and donor type.
- **P-5798** (925, B-ALL) has everything except DRI, plus cause of death.

### Closest to the original papers (prediction or scoring models)

- **P-5300** (1,503 patients, MDS): Nazha's personalized prediction model. TRM is coded inside `relstat`. It also has IPSS/IPSS-R, blood counts, cytogenetics and cause of death.
- **P-6062** (2,319, mixed diseases): a scoring system for ranking transplants.
- **P-5542** (1,434, mixed diseases): HLA-based risk prediction after haploidentical transplant with post-transplant cyclophosphamide.

### Large mixed-disease groups (filter to leukemia/MDS)

- **P-5262** (18,547), **P-5242** (16,550; bloodstream infections in the first 100 days, the closest to a Day-100 endpoint), **P-5540** (15,903), **P-5900** (14,825), **P-5375** (13,187; DRI, HCT-CI and KPS).
- **P-5423** (7,348) and **P-6219** (5,873) both carry DRI, HCT-CI and KPS.

## Tier A: all 31 core candidates

Sorted by patient count. ✓ means the data dictionary has a matching variable. TRM events count rows with `trm = 1`; the crude % is out of patients with `trm` recorded as 0 or 1.

| Study | Patients | TRM events (crude %) | NRM outcome | Age | KPS | HCT-CI | DRI | Disease status | Cytogenetics | Conditioning | Donor | Cause of death | Title |
|---|---:|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|
| [P-5646](https://cibmtr.org/Manuscript/a028W000012MwL3QAK/P-5646) | 7,551 | 1,378 (18%) | variable | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | – | The incidence and impact of clostridioides difficile infection on transplant outcomes in a… |
| [P-5329](https://cibmtr.org/Manuscript/a020h00001F1KI7AAN/P-5329) | 5,508 | 1,509 (28%) | variable | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | – | Comparison of outcomes of HCT in blast phase of BCR-ABL1-MPN with de novo AML and with AML… |
| [P-5702](https://cibmtr.org/Manuscript/a028W00001IhmoQQAR/P-5702) | 4,946 | 968 (20%) | variable | ✓ | ✓ | ✓ | – | ✓ | – | ✓ | ✓ | – | Association of ABO mismatch with the outcomes of allogeneic hematopoietic cell transplanta… |
| [P-5370](https://cibmtr.org/Manuscript/a020h00001F1sihAAB/P-5370) | 4,387 | 1,105 (25%) | variable | ✓ | ✓ | ✓ | – | ✓ | – | ✓ | ✓ | – | Myeloablative conditioning for allogeneic transplantation results in superior disease-free… |
| [P-5521](https://cibmtr.org/Manuscript/a020h00001HHFOaAAP/P-5521) | 4,037 | 828 (21%) | variable | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | – | Haploidentical vs sibling, unrelated, or cord blood hematopoietic cell transplantation for… |
| [P-5435](https://cibmtr.org/Manuscript/a020h00001HHAmdAAH/P-5435) | 3,677 | 776 (21%) | variable | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | – | Risk classification at diagnosis predicts post-HCT outcomes in intermediate-, adverse-risk… |
| [P-5603](https://cibmtr.org/Manuscript/a028a00001Ktap0AAB/P-5603) | 3,065 | 624 (20%) | variable | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | – | Impact of pre-transplant induction and consolidation cycles on AML allogeneic transplant o… |
| [P-5445](https://cibmtr.org/Manuscript/a020h00001HHBKpAAP/P-5445) | 2,492 | 583 (23%) | variable | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | – | Impact of depth of clinical response on outcomes of acute myeloid leukemia patients in fir… |
| [P-5531](https://cibmtr.org/Manuscript/a028a00001HHFrKAAX/P-5531) | 2,253 | 432 (19%) | variable | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | – | Correction to: An adapted European LeukemiaNet genetic risk stratification for acute myelo… |
| [P-5147](https://cibmtr.org/Manuscript/a020h00001DvjyZAAR/P-5147) | 1,840 | 538 (30%) | variable | ✓ | ✓ | – | – | – | – | ✓ | – | – | Donor HLA-E status associates with disease-free survival and transplant-related mortality … |
| [P-5568](https://cibmtr.org/Manuscript/a028a00001HHHbPAAX/P-5568) | 1,735 | 454 (26%) | variable | ✓ | ✓ | ✓ | – | – | – | ✓ | ✓ | – | Relapse and disease-free survival in patients with myelodysplastic syndrome undergoing all… |
| [P-5166](https://cibmtr.org/Manuscript/a020h00001Dvz6GAAR/P-5166) | 1,673 | – | approx. via cause of death | ✓ | ✓ | ✓ | – | – | ✓ | ✓ | ✓ | ✓ | Increased overall and bacterial infections following myeloablative allogeneic HCT for pati… |
| [P-5300](https://cibmtr.org/Manuscript/a020h00001GkuIpAAJ/P-5300) | 1,503 | – | coded inside another variable | ✓ | ✓ | – | – | ✓ | ✓ | ✓ | ✓ | ✓ | A personalized prediction model for outcomes after allogeneic hematopoietic cell transplan… |
| [P-5281](https://cibmtr.org/Manuscript/a020h00001G9VhGAAV/P-5281) | 1,413 | 394 (28%) | variable | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | – | Reduced intensity conditioning for acute myeloid leukemia using melphalan- vs busulfan-bas… |
| [P-5074](https://cibmtr.org/Manuscript/a020h00001BQKuHAAX/P-5074) | 1,408 | 439 (31%) | variable | ✓ | ✓ | – | – | ✓ | ✓ | ✓ | ✓ | – | Impact of cytogenetic abnormalities on outcomes of adult Philadelphia-negative acute lymph… |
| [P-5526](https://cibmtr.org/Manuscript/a028a00001HHFmOAAX/P-5526) | 1,311 | 339 (26%) | variable | ✓ | ✓ | ✓ | – | – | ✓ | ✓ | ✓ | – | Age is no barrier for adults undergoing HCT for AML in CR1: Contemporary CIBMTR analysis. |
| [P-5225](https://cibmtr.org/Manuscript/a020h00001DwdViAAJ/P-5225) | 1,280 | 367 (29%) | variable | ✓ | ✓ | ✓ | – | – | ✓ | ✓ | ✓ | – | Comparison of patient age groups in transplantation for myelodysplastic syndrome: The Medi… |
| [P-5263](https://cibmtr.org/Manuscript/a020h00001Dx8ixAAB/P-5263) | 1,070 | 263 (25%) | variable | ✓ | ✓ | – | – | ✓ | – | ✓ | ✓ | ✓ | Timing of allogeneic hematopoietic cell transplantation (alloHCT) for chronic myeloid leuk… |
| [P-5457](https://cibmtr.org/Manuscript/a020h00001HHBmKAAX/P-5457) | 1,045 | 306 (29%) | variable | ✓ | ✓ | ✓ | – | – | ✓ | ✓ | ✓ | ✓ | Fludarabine and melphalan compared with reduced doses of busulfan and fludarabine improve … |
| [P-6238](https://cibmtr.org/Manuscript/a02UG00000JEJflYAH/P-6238) | 938 | 124 (13%) | variable | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | Impact of extramedullary disease at diagnosis on outcomes post allogeneic hematopoietic ce… |
| [P-5798](https://cibmtr.org/Manuscript/a028W00001fvFh7QAE/P-5798) | 925 | 225 (25%) | variable | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | ✓ | Younger matched unrelated donors confer decreased relapse risk compared to older sibling d… |
| [P-5282](https://cibmtr.org/Manuscript/a020h00001G9WFjAAN/P-5282) | 744 | – | variable | ✓ | ✓ | – | – | ✓ | ✓ | ✓ | ✓ | ✓ | Late effects after ablative allogeneic stem cell transplantation for adolescent and young … |
| [P-5303](https://cibmtr.org/Manuscript/a020h00001F13EiAAJ/P-5303) | 713 | 142 (20%) | variable | ✓ | ✓ | – | – | ✓ | – | ✓ | ✓ | – | Investigation of donor KIR content and matching in children undergoing hematopoietic cell … |
| [P-5261](https://cibmtr.org/Manuscript/a020h00001Dx8inAAB/P-5261) | 611 | 83 (14%) | variable | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | – | Comparison of total body irradiation versus non-total body irradiation containing regimens… |
| [P-5411](https://cibmtr.org/Manuscript/a020h00001HH9wwAAD/P-5411) | 603 | 165 (28%) | variable | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | Alternative donor transplantation for myelodysplastic syndromes: Haploidentical relative a… |
| [P-5346](https://cibmtr.org/Manuscript/a020h00001F1ft9AAB/P-5346) | 480 | 88 (18%) | variable | ✓ | ✓ | – | – | ✓ | ✓ | ✓ | ✓ | – | Superior survival with pediatric-style chemotherapy compared to myeloablative allogeneic h… |
| [P-5135](https://cibmtr.org/Manuscript/a020h00001DvTweAAF/P-5135) | 374 | 101 (27%) | variable | ✓ | ✓ | – | – | ✓ | – | ✓ | ✓ | – | Maintenance tyrosine kinase inhibitors following allogeneic hematopoietic stem cell transp… |
| [P-5537](https://cibmtr.org/Manuscript/a028a00001HHFv8AAH/P-5537) | 311 | 95 (31%) | variable | ✓ | ✓ | ✓ | – | – | – | ✓ | ✓ | – | The mutational landscape in chronic myelomonocytic leukemia and its impact on allogeneic h… |
| [P-5279](https://cibmtr.org/Manuscript/a020h00001G9VDiAAN/P-5279) | 290 | 19 (24%) | variable | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | – | Prognostic impact of serum CXC chemokine ligands 4 and 7 on myelodysplastic syndromes post… |
| [P-5530](https://cibmtr.org/Manuscript/a028a00001HHFrFAAX/P-5530) | 241 | 71 (30%) | variable | ✓ | ✓ | ✓ | – | ✓ | – | ✓ | ✓ | ✓ | Outcomes of allogeneic hematopoietic cell transplantation in T-cell prolymphocytic leukemi… |
| [P-5221](https://cibmtr.org/Manuscript/a020h00001DwaOXAAZ/P-5221) | 198 | – | derivable | ✓ | ✓ | ✓ | – | ✓ | – | ✓ | ✓ | – | The role of donor lymphocyte infusion (DLI) in post hematopoietic cell transplant (HCT) re… |

## Tier B: 48 supplementary datasets

| Study | Patients | TRM events (crude %) | NRM outcome | Age | KPS | HCT-CI | DRI | Disease status | Cytogenetics | Conditioning | Donor | Cause of death | Title |
|---|---:|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|
| [P-5181](https://cibmtr.org/Manuscript/a020h00001DwCF4AAN/P-5181) | 23,090 | – | approx. via cause of death | ✓ | ✓ | ✓ | – | – | – | ✓ | ✓ | ✓ | Incidence, risk factors for and outcomes of transplant-associated thrombotic microangiopat… |
| [P-5581](https://cibmtr.org/Manuscript/a028a00001HHJGbAAP/P-5581) | 21,008 | – | variable | ✓ | ✓ | ✓ | ✓ | – | – | ✓ | ✓ | ✓ | Noninfectious pulmonary toxicity after allogeneic hematopoietic cell transplantation. |
| [P-5262](https://cibmtr.org/Manuscript/a020h00001Dx8isAAB/P-5262) | 18,547 | 3,197 (18%) | variable | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | – | Community health status and outcomes after allogeneic hematopoietic cell transplantation i… |
| [P-5242](https://cibmtr.org/Manuscript/a020h00001DwtmGAAR/P-5242) | 16,550 | 3,401 (25%) | variable | ✓ | ✓ | ✓ | – | – | – | ✓ | ✓ | ✓ | Incidence, risk factors, and outcomes of patients who develop mucosal barrier injury-labor… |
| [P-5540](https://cibmtr.org/Manuscript/a028a00001HHG5qAAH/P-5540) | 15,903 | 3,317 (21%) | variable | ✓ | ✓ | ✓ | ✓ | – | – | ✓ | ✓ | – | Does recipient body mass index inform donor selection for allogeneic haematopoietic cell t… |
| [P-5900](https://cibmtr.org/Manuscript/a02UG000002D41TYAS/P-5900) | 14,825 | 3,727 (25%) | variable | ✓ | ✓ | ✓ | ✓ | – | – | ✓ | ✓ | – | Racial, ethnic and socioeconomic diversity and outcomes of patients with graft-versus-host… |
| [P-5375](https://cibmtr.org/Manuscript/a020h00001F1wPFAAZ/P-5375) | 13,187 | 2,403 (18%) | variable | ✓ | ✓ | ✓ | ✓ | – | – | ✓ | ✓ | – | Impact of pretransplantation renal dysfunction on outcomes after allogeneic hematopoietic … |
| [P-6265](https://cibmtr.org/Manuscript/a02UG00000Kl49VYAR/P-6265) | 9,231 | 2,096 (23%) | variable | ✓ | ✓ | ✓ | ✓ | – | – | ✓ | – | – | Higher HLA‑DRB1 evolutionary divergence is associated with reduced relapse and improved su… |
| [P-5373](https://cibmtr.org/Manuscript/a020h00001F1wKKAAZ/P-5373) | 7,421 | 1,919 (26%) | variable | ✓ | ✓ | – | – | – | – | ✓ | – | ✓ | Specific class I HLA supertypes but not HLA zygosity or expression are associated with out… |
| [P-5423](https://cibmtr.org/Manuscript/a020h00001HHAQsAAP/P-5423) | 7,348 | 1,531 (21%) | variable | ✓ | ✓ | ✓ | ✓ | – | – | ✓ | ✓ | ✓ | The effect of donor graft cryopreservation on allogeneic hematopoietic cell transplantatio… |
| [P-6144](https://cibmtr.org/Manuscript/a02UG00000CMFZNYA5/P-6144) | 7,055 | – | variable | ✓ | ✓ | ✓ | ✓ | – | – | ✓ | ✓ | ✓ | Choosing between HLA-mismatched unrelated and haploidentical donors: Donor age considerati… |
| [P-6219](https://cibmtr.org/Manuscript/a02UG00000I1tmUYAR/P-6219) | 5,873 | – | variable | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Matched unrelated vs haploidentical donor hematopoietic cell transplantation using post-tr… |
| [P-5628](https://cibmtr.org/Manuscript/a028W000011GtqwQAC/P-5628) | 5,787 | 1,088 (19%) | variable | ✓ | ✓ | ✓ | – | – | – | ✓ | ✓ | – | Adapting the HCT-CI definitions for children, adolescents, and young adults with hematolog… |
| [P-5824](https://cibmtr.org/Manuscript/a028W00001nWUnoQAG/P-5824) | 5,473 | 1,263 (23%) | variable | ✓ | – | ✓ | ✓ | – | – | ✓ | ✓ | – | Racial and Socioeconomic Disparities in Long-Term Outcomes in ≥1 Year Allogeneic Hematopoi… |
| [P-5597](https://cibmtr.org/Manuscript/a028a00001GmezfAAB/P-5597) | 5,108 | 1,362 (27%) | variable | ✓ | ✓ | ✓ | – | ✓ | – | ✓ | – | – | A core group of structurally similar HLA-DPB1 alleles drives permissiveness after hematopo… |
| [P-5390](https://cibmtr.org/Manuscript/a020h00001HH8ecAAD/P-5390) | 5,108 | 1,362 (27%) | variable | ✓ | ✓ | ✓ | – | ✓ | – | ✓ | – | – | Impact of previously unrecognized HLA mismatches using ultrahigh resolution typing in unre… |
| [P-5498](https://cibmtr.org/Manuscript/a020h00001HHDlDAAX/P-5498) | 4,365 | 1,098 (25%) | variable | ✓ | ✓ | ✓ | ✓ | – | – | ✓ | ✓ | – | Chronic graft-versus-host disease, nonrelapse mortality, and disease relapse in older vers… |
| [P-5482](https://cibmtr.org/Manuscript/a020h00001HHD6sAAH/P-5482) | 4,105 | – | variable | ✓ | ✓ | – | – | ✓ | – | ✓ | ✓ | – | Neither donor nor recipient mitochondrial haplotypes are associated with unrelated donor t… |
| [P-5884](https://cibmtr.org/Manuscript/a02UG000001GqN3YAK/P-5884) | 4,064 | 1,116 (28%) | variable | ✓ | ✓ | ✓ | – | ✓ | – | ✓ | ✓ | – | Incidence of bacterial blood stream infections in patients with acute GVHD. |
| [P-5296](https://cibmtr.org/Manuscript/a020h00001G9aR7AAJ/P-5296) | 3,749 | 429 (22%) | variable | ✓ | ✓ | – | – | ✓ | – | ✓ | – | – | Neighborhood poverty and pediatric allogeneic hematopoietic cell transplantation outcomes:… |
| [P-5448](https://cibmtr.org/Manuscript/a020h00001HHBP1AAP/P-5448) | 3,242 | 839 (26%) | variable | ✓ | ✓ | ✓ | ✓ | – | – | ✓ | ✓ | – | Genetics of HLA peptide presentation, and impact on outcomes in HLA-matched allo-HCT. |
| [P-5356](https://cibmtr.org/Manuscript/a020h00001F1mbaAAB/P-5356) | 2,744 | 493 (18%) | variable | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | – | ✓ | Posttransplant cyclophosphamide is associated with increased cytomegalovirus infection: a … |
| [P-5737](https://cibmtr.org/Manuscript/a028W00001TOdRNQA1/P-5737) | 2,744 | 546 (20%) | variable | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | – | ✓ | Post-transplantation cyclophosphamide is associated with increased bacterial infections |
| [P-5383](https://cibmtr.org/Manuscript/a020h00001HH8BlAAL/P-5383) | 2,569 | – | derivable | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | – | A validated pediatric disease risk index for allogeneic hematopoietic cell transplantation… |
| [P-5129](https://cibmtr.org/Manuscript/a020h00001CRRHYAA5/P-5129) | 2,533 | 784 (31%) | variable | ✓ | ✓ | – | – | ✓ | – | – | ✓ | ✓ | Comparison of high doses of total body irradiation in myeloablative conditioning before he… |
| [P-5645](https://cibmtr.org/Manuscript/a028W0000127oR3QAI/P-5645) | 2,515 | – | variable | ✓ | ✓ | ✓ | – | ✓ | – | ✓ | – | – | Natural killer cell alloreactivity predicted by killer cell immunoglobulin-like receptor l… |
| [P-5906](https://cibmtr.org/Manuscript/a02UG000002mhWBYAY/P-5906) | 2,512 | 682 (27%) | variable | ✓ | ✓ | ✓ | – | ✓ | – | ✓ | – | – | Impact of Race/Ethnicity on Outcomes after Umbilical Cord Blood Transplantation. |
| [P-5441](https://cibmtr.org/Manuscript/a020h00001HHB4VAAX/P-5441) | 2,320 | 379 (16%) | variable | ✓ | ✓ | ✓ | ✓ | – | – | ✓ | ✓ | ✓ | HLA-haploidentical vs matched unrelated donor transplants with posttransplant cyclophospha… |
| [P-6062](https://cibmtr.org/Manuscript/a02UG000008UaXhYAK/P-6062) | 2,319 | 871 (38%) | variable | ✓ | ✓ | ✓ | – | ✓ | – | ✓ | – | – | Novel scoring system for ranking hematopoietic stem cell transplantation. |
| [P-5063](https://cibmtr.org/Manuscript/a020h00001BQKVEAA5/P-5063) | 2,116 | 781 (38%) | variable | ✓ | ✓ | ✓ | ✓ | – | – | ✓ | – | – | Composite GRFS and CRFS outcomes after adult alternative donor HCT. |
| [P-6090](https://cibmtr.org/Manuscript/a02UG00000A5kR4YAJ/P-6090) | 2,089 | 244 (12%) | variable | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | ✓ | Delayed T cell recovery after hematopoietic cell transplantation is associated with decrea… |
| [P-5562](https://cibmtr.org/Manuscript/a028a00001HHHBTAA5/P-5562) | 2,062 | – | variable | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | – | Characteristics of graft-versus-host disease (GvHD) after post-transplant cyclophosphamide… |
| [P-5961](https://cibmtr.org/Manuscript/a02UG00000504S9YAI/P-5961) | 2,005 | 742 (37%) | variable | ✓ | ✓ | ✓ | – | ✓ | – | ✓ | – | – | The health risk of social disadvantage is transplantable into a new host. |
| [P-5542](https://cibmtr.org/Manuscript/a028a00001HHGEcAAP/P-5542) | 1,434 | 274 (19%) | variable | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | – | HLA informs risk predictions after haploidentical stem cell transplantation with post-tran… |
| [P-5397](https://cibmtr.org/Manuscript/a020h00001HH9CNAA1/P-5397) | 1,365 | – | derivable | ✓ | ✓ | ✓ | – | – | – | ✓ | – | – | Return to work among young adult survivors of allogeneic hematopoietic cell transplantatio… |
| [P-6001](https://cibmtr.org/Manuscript/a02UG000006cbSvYAI/P-6001) | 1,336 | 173 (13%) | variable | ✓ | ✓ | ✓ | ✓ | – | – | ✓ | ✓ | ✓ | Donor type does not impact late graft failure following reduced-intensity allogeneic hemat… |
| [P-5546](https://cibmtr.org/Manuscript/a028a00001HHGKCAA5/P-5546) | 1,293 | 212 (16%) | variable | ✓ | ✓ | ✓ | ✓ | – | – | – | ✓ | – | Umbilical cord blood or HLA-haploidentical transplantation: Real-world outcomes versus ran… |
| [P-5545](https://cibmtr.org/Manuscript/a028a00001HHGJxAAP/P-5545) | 1,287 | 245 (19%) | variable | ✓ | ✓ | ✓ | ✓ | – | – | ✓ | – | – | Number of HLA-mismatched eplets is not associated with major outcomes in haploidentical tr… |
| [P-5569](https://cibmtr.org/Manuscript/a028a00001HHHlcAAH/P-5569) | 1,175 | 66 (6%) | variable | ✓ | ✓ | – | – | ✓ | – | ✓ | ✓ | – | Association of chronic graft-versus-host disease with late effects following allogeneic he… |
| [P-5330](https://cibmtr.org/Manuscript/a020h00001F1MP4AAN/P-5330) | 1,082 | 302 (29%) | variable | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | – | Optimal donor for African Americans with hematologic malignancy: HLA-haploidentical relati… |
| [P-5726](https://cibmtr.org/Manuscript/a028W00001QCvZFQA1/P-5726) | 1,004 | – | variable | ✓ | – | – | – | ✓ | – | ✓ | – | – | HLA class I genotype is associated with relapse risk after allogeneic stem cell transplant… |
| [P-5515](https://cibmtr.org/Manuscript/a020h00001HHEjIAAX/P-5515) | 874 | 201 (23%) | variable | ✓ | ✓ | ✓ | ✓ | – | – | ✓ | ✓ | ✓ | Planned granulocyte colony-stimulating factor adversely impacts survival after allogeneic … |
| [P-5273](https://cibmtr.org/Manuscript/a020h00001G9TlMAAV/P-5273) | 736 | 80 (11%) | variable | ✓ | ✓ | ✓ | – | – | – | ✓ | ✓ | – | Prevalence of decisional regret among patients who underwent allogeneic hematopoietic stem… |
| [P-5510](https://cibmtr.org/Manuscript/a020h00001HHEETAA5/P-5510) | 708 | 110 (16%) | variable | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Comparison of haploidentical and umbilical cord blood transplantation after myeloablative … |
| [P-5237](https://cibmtr.org/Manuscript/a020h00001DwtRjAAJ/P-5237) | 646 | 106 (17%) | variable | ✓ | ✓ | ✓ | ✓ | – | – | ✓ | ✓ | – | Risk factors for graft-versus-host disease in haploidentical hematopoietic cell transplant… |
| [P-5799](https://cibmtr.org/Manuscript/a028W00001hYGrtQAG/P-5799) | 299 | 60 (20%) | variable | ✓ | ✓ | – | – | ✓ | – | – | – | – | Pilot study of donor-engrafted clonal hematopoiesis evolution and clinical outcomes in all… |
| [P-5056](https://cibmtr.org/Manuscript/a020h00001BQJ99AAH/P-5056) | 234 | – | approx. via cause of death | ✓ | ✓ | ✓ | – | ✓ | – | ✓ | ✓ | ✓ | Survival outcomes of allogeneic hematopoietic cell transplants with EBV-positive or EBV-ne… |
| [P-5805](https://cibmtr.org/Manuscript/a028W00001j6ahkQAA/P-5805) | 121 | 31 (28%) | variable | ✓ | ✓ | ✓ | – | ✓ | – | – | ✓ | – | Unfavorable transcriptome profiles and social disadvantage in hematopoietic cell transplan… |

Tier B- (22 lymphoma/myeloma/MPN allogeneic groups), tier C and tier D are listed in [`data/nrm_candidate_ranking.csv`](../data/nrm_candidate_ranking.csv) and the workbook.

*The tables are generated by `scripts/make_findings_tables.py`.*
