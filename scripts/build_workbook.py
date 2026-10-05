"""Assemble CIBMTR_NRM_dataset_analysis.xlsx from the CSV outputs."""
import csv, sys, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
# Data folder: first CLI argument, else $CIBMTR_DATA_DIR, else <repo>/data
ROOT = os.path.abspath(os.path.expanduser(
    (sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else None)
    or os.environ.get('CIBMTR_DATA_DIR')
    or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')))
rd = lambda f: list(csv.DictReader(open(os.path.join(ROOT, f), encoding='utf-8')))
rank, vars_ = rd('nrm_candidate_ranking.csv'), rd('variables_by_study.csv')
wb = Workbook(); H = Font(bold=True, color='FFFFFF'); HF = PatternFill('solid', fgColor='1F3A5F')
TF = {'A': 'D9EAD3', 'B': 'FFF2CC', 'C': 'F4CCCC', 'D': 'EEEEEE'}

def sheet(ws, rows, cols, widths=None, link_cols=()):
    ws.append(cols)
    for c in ws[1]: c.font, c.fill, c.alignment = H, HF, Alignment(wrap_text=True, vertical='top')
    for r in rows:
        ws.append([r.get(c, '') for c in cols])
    for i, c in enumerate(cols, 1):
        ws.column_dimensions[get_column_letter(i)].width = (widths or {}).get(c, 14)
        if c in link_cols:
            for cell in ws.iter_rows(min_row=2, min_col=i, max_col=i):
                if cell[0].value: cell[0].hyperlink, cell[0].font = cell[0].value, Font(color='1155CC', underline='single')
    ws.freeze_panes = 'C2'; ws.auto_filter.ref = ws.dimensions

ws = wb.active; ws.title = 'README'
notes = [
 'CIBMTR publicly available datasets: screening for NRM / TRM prediction (allogeneic HCT, leukemia/MDS)',
 '',
 'Source: https://cibmtr.org/CIBMTR/Resources/Publicly-Available-Datasets (160 studies, captured 2026-10-03; datasets downloaded and counted 2026-10-03).',
 'Every data dictionary was downloaded and parsed (folder: dictionaries/). 7 dictionary links on the site were broken; those were recovered from the dataset zips.',
 '',
 'Tiers (see "NRM ranking"):',
 '  A  core training candidate: allogeneic HCT in leukemia/MDS (from title) with an NRM/TRM outcome and most standard pre-transplant predictors',
 '  B  useful/supplementary: mixed malignancy allo cohorts that include leukemia/MDS and carry NRM/TRM (filter on disease variable)',
 '  B- NRM present but lymphoma/myeloma/MPN cohorts: useful for external validation of general toxicity models',
 '  C  no NRM/TRM outcome found (and not derivable)',
 '  D  out of scope: autologous, CAR-T, donor-safety or COVID studies',
 '',
 'nrm_outcome column: "explicit variable" = a trm/nrm event variable; "coded inside another variable" = e.g. relstat with 2=TRM;',
 '  "derivable" = death + relapse/DFS present, so NRM = death without prior relapse (competing-risk). "approx. via cause of death" = weaker.',
 'Score = disease-scope weight + NRM availability + presence of predictors (age, KPS, HCT-CI, DRI, disease status, cytogenetics, donor type, HLA,',
 '  graft source, conditioning intensity, TBI, GVHD prophylaxis, ATG, CMV, sex match, year, dx-to-HCT time, cause of death, OS, relapse).',
 'Predictor columns list the actual variable names found in each dictionary, so you can see exactly what to harmonize.',
 '',
 'Caveats: flags come from automated keyword matching on dictionaries; verify against the dictionary before modelling.',
 'Each dataset is the analysis file of one paper: inclusion criteria, eras and variable coding differ between studies, and the same patient',
 '  may appear in more than one dataset (IDs are pseudonymized per study, so pooled datasets cannot be de-duplicated).',
 'n_patients / trm_events / trm_rate come from scripts/dataset_sizes.py (largest SAS file per zip; trm coded 0/1; crude proportion, not cumulative incidence).',
 'Day-100 mortality is usually derivable from dead + intxsurv (months) where present.',
 'Use is governed by the CIBMTR Terms and Conditions (included in every dataset zip).',
]
for n in notes: ws.append([n])
ws['A1'].font = Font(bold=True, size=14); ws.column_dimensions['A'].width = 150

concept_cols = [c for c in rank[0] if c.startswith(('out_', 'p_'))]
cols = ['study_id', 'tier', 'score', 'n_patients', 'trm_events', 'trm_rate', 'nrm_outcome', 'disease_scope', 'title', 'first_author', 'start_year', 'n_variables'] + concept_cols + ['publication_url', 'dataset_zip_url', 'data_dictionary_url']
w = {'title': 70, 'tier': 26, 'nrm_outcome': 26, 'disease_scope': 26, 'publication_url': 40, 'dataset_zip_url': 40, 'data_dictionary_url': 40, 'score': 7, 'start_year': 8, 'n_variables': 8}
sheet(wb.create_sheet('NRM ranking'), rank, cols, w, ('publication_url', 'dataset_zip_url', 'data_dictionary_url'))
wsr = wb['NRM ranking']
for row in wsr.iter_rows(min_row=2):
    t = (row[1].value or ' ')[0]
    for c in row[:9]: c.fill = PatternFill('solid', fgColor=TF.get(t, 'FFFFFF'))

# coverage matrix (1/0) for tier A/B
cov = []
for r in rank:
    if r['tier'][0] in 'AB':
        cov.append({'study_id': r['study_id'], 'tier': r['tier'][:2].strip(), 'title': r['title'], **{c: (1 if r[c] else 0) for c in concept_cols}})
sheet(wb.create_sheet('Coverage A-B'), cov, ['study_id', 'tier', 'title'] + concept_cols, {'title': 60})
wsc = wb['Coverage A-B']
for row in wsc.iter_rows(min_row=2, min_col=4):
    for c in row:
        c.fill = PatternFill('solid', fgColor='B6D7A8' if c.value == 1 else 'F4CCCC'); c.alignment = Alignment(horizontal='center')
# totals row
wsc.append(['TOTAL', '', f'{len(cov)} studies'] + [sum(r[c] for r in cov) for c in concept_cols])
for c in wsc[wsc.max_row]: c.font = Font(bold=True)

sheet(wb.create_sheet('All variables'), vars_, ['study_id', 'variable', 'description', 'type', 'levels'], {'description': 60, 'levels': 90, 'variable': 18})
# variable-name frequency across tier A/B
ab = {r['study_id'] for r in rank if r['tier'][0] in 'AB'}
freq = {}
for v in vars_:
    if v['study_id'] in ab:
        k = v['variable'].lower(); f = freq.setdefault(k, {'variable': k, 'n_studies': 0, 'example_description': v['description'], 'studies': []})
        f['n_studies'] += 1; f['studies'].append(v['study_id'])
fr = sorted(freq.values(), key=lambda x: -x['n_studies'])
for f in fr: f['studies'] = ' '.join(f['studies'])
sheet(wb.create_sheet('Common variables (A-B)'), fr, ['variable', 'n_studies', 'example_description', 'studies'], {'example_description': 60, 'studies': 90, 'variable': 18})
wb.save(os.path.join(ROOT, 'CIBMTR_NRM_dataset_analysis.xlsx')); print('saved', len(rank), len(vars_), len(fr))
