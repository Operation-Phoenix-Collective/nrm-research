"""Score each CIBMTR public dataset for usefulness in NRM/TRM prediction for
allogeneic HCT in leukemia, using the parsed data dictionaries."""
import csv, sys, os, re, collections
# Data folder: first CLI argument, else $CIBMTR_DATA_DIR, else <repo>/data
ROOT = os.path.abspath(os.path.expanduser(
    (sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else None)
    or os.environ.get('CIBMTR_DATA_DIR')
    or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')))
cat = {r['study_id']: r for r in csv.DictReader(open(os.path.join(ROOT, 'catalog.csv')))}
long = list(csv.DictReader(open(os.path.join(ROOT, 'variables_long.csv'))))

# one row per study x variable, levels concatenated
vars_ = collections.OrderedDict()
for r in long:
    k = (r['study_id'], r['variable'])
    v = vars_.setdefault(k, {'study_id': r['study_id'], 'variable': r['variable'], 'description': r['description'], 'type': r['type'], 'levels': []})
    if r['value'] or r['label']:
        v['levels'].append(f"{r['value']}={r['label']}".strip('='))
for v in vars_.values(): v['levels'] = '; '.join(v['levels'])[:2000]

# concept -> regex on "variable :: description"
C = {
 # outcomes
 'out_NRM_TRM':      r'\b(trm|nrm)\b|non[- ]?relapse mort|treatment[- ]related mort|transplant[- ]related mort',
 'out_OS':           r'^(dead|os|intxsurv|intxdeath)\b|overall survival|vital status',
 'out_relapse':      r'^(rel|relapse|intxrel)\b|relapse(?! ?free)',
 'out_cause_death':  r'cause of death|\bcod\b|primary cause',
 'out_aGVHD':        r'acute gvhd|agvh|acute graft',
 'out_cGVHD':        r'chronic gvhd|cgvh|chronic graft',
 'out_time_vars':    r'^int|interval|time (from|to)|months|days from',
 # pre-transplant predictors
 'p_age':            r'^(age|agegp|ageg|agecat)|age at (hct|transplant|tx)|recipient age',
 'p_KPS':            r'karnof|\bkps\b|performance (score|status)',
 'p_HCT_CI':         r'hct[- ]?ci|comorbidit|sorror',
 'p_DRI':            r'disease risk index|\bdri\b',
 'p_disease':        r'^(disease|disgp|dis|main|dxgp)\b|disease (type|group)|diagnosis',
 'p_disease_status': r'disease status|remission|\bcr1\b|\bcr2\b|stage at|status at (hct|transplant)',
 'p_cytogenetics':   r'cytogen|karyotyp|\belr?n\b|mrd',
 'p_donor_type':     r'donor (type|group)|dnrgp|donorgp|haplo|unrelated|sibling',
 'p_HLA':            r'\bhla\b|mismatch|matching',
 'p_graft_source':   r'graft (type|source)|graftype|graftgp|bone marrow|peripheral blood|cord blood',
 'p_conditioning':   r'condint|condgp|conditioning|myeloablat|reduced[- ]intens|\bric\b|\bmac\b',
 'p_TBI':            r'\btbi\b|total body',
 'p_GVHD_prophylaxis': r'gvhd prophylaxis|gvhdgp|ptcy|post[- ]?transplant cyclophos|tacrolimus|methotrexate',
 'p_ATG':            r'\batg\b|campath|alemtuzumab|in vivo t',
 'p_CMV':            r'\bcmv\b|cytomegalo',
 'p_sex_match':      r'sex ?match|gender match|donor[- ]recipient sex',
 'p_year':           r'year of (transplant|hct|tx)|yeartx|yeargp',
 'p_time_dx_tx':     r'diagnosis to (hct|transplant|tx)|dx to|time from diagnosis',
 'p_race_SES':       r'\brace\b|ethnic|income|poverty|insurance|zip|neighborhood',
}
CR = {k: re.compile(v, re.I) for k, v in C.items()}

flags = collections.defaultdict(lambda: collections.defaultdict(list))
for v in vars_.values():
    s = f"{v['variable']} :: {v['description']}"
    for k, rx in CR.items():
        if rx.search(s): flags[v['study_id']][k].append(v['variable'])
    if re.search(r'\b(trm|nrm)\b|non[- ]?relapse|treatment[- ]related|transplant[- ]related', v['levels'], re.I) and not CR['out_NRM_TRM'].search(s):
        flags[v['study_id']]['nrm_in_value_labels'].append(v['variable'])
    if re.search(r'^dfs$|disease[- ]free|leukemia[- ]free|relapse[- ]free', s, re.I):
        flags[v['study_id']]['out_DFS'].append(v['variable'])

LEUK = re.compile(r'\bAML\b|acute myeloid|\bALL\b|acute lympho|\bMDS\b|myelodysplas|acute leuk|\bCML\b|chronic myel|\bCMML\b|leukemia', re.I)
EXCL = re.compile(r'autologous|CAR[- ]?T|chimeric antigen|idecabtagene|tisagenlecleucel|mobilization|apheresis|interdonation|bone marrow donation|bone marrow harvest|donor toxicity|peripheral blood progenitor cells in 1 day|COVID|vaccination', re.I)
NONMAL = re.compile(r'sickle|\baplastic|\bSAA\b|non-?malignant|hemophagocytic|amegakaryocytic', re.I)
LYMPH  = re.compile(r'lymphoma|myeloma|amyloid|POEMS|germ cell|Hodgkin|DLBCL|plasma cell|Richter|T-cell|myelofibrosis|MPN', re.I)

def disease_scope(sid):
    title = cat[sid]['title']
    labels = ' '.join(v['levels'] + ' ' + v['description'] for v in vars_.values() if v['study_id'] == sid and re.search(r'^(disease|disgp|dis|main|dxgp|strata)|disease|diagnos', v['variable'] + ' ' + v['description'], re.I))
    if EXCL.search(title) and not re.search(r'allogeneic', title, re.I): return 'not allo-recipient (auto/CAR-T/donor/other)'
    if NONMAL.search(title): return 'non-malignant'
    if re.search(r'plasma cell leukemia|myelofibrosis', title, re.I): return 'lymphoma/myeloma/MPN'
    if LEUK.search(title): return 'leukemia/MDS (title)'
    if LYMPH.search(title) and not LEUK.search(title): return 'lymphoma/myeloma/MPN'
    if LEUK.search(labels): return 'mixed malignancies incl. leukemia/MDS'
    return 'unclear / mixed'

W = {'out_NRM_TRM': 30, 'p_age': 4, 'p_KPS': 6, 'p_HCT_CI': 8, 'p_DRI': 6, 'p_disease_status': 5, 'p_cytogenetics': 3,
     'p_donor_type': 5, 'p_HLA': 3, 'p_graft_source': 3, 'p_conditioning': 6, 'p_TBI': 2, 'p_GVHD_prophylaxis': 3,
     'p_ATG': 2, 'p_CMV': 3, 'p_sex_match': 2, 'p_year': 2, 'p_time_dx_tx': 2, 'out_cause_death': 4, 'out_OS': 2, 'out_relapse': 3}
SCOPE_W = {'leukemia/MDS (title)': 25, 'mixed malignancies incl. leukemia/MDS': 18, 'unclear / mixed': 6,
           'lymphoma/myeloma/MPN': 0, 'non-malignant': -10, 'not allo-recipient (auto/CAR-T/donor/other)': -40}

out = []
nvars = collections.Counter(v['study_id'] for v in vars_.values())
for sid, c in cat.items():
    f = flags[sid]; sc = disease_scope(sid)
    if f.get('out_NRM_TRM'): nrm = 'explicit variable'
    elif f.get('nrm_in_value_labels'): nrm = 'coded inside another variable (' + ';'.join(sorted(set(f['nrm_in_value_labels']))) + ')'
    elif f.get('out_OS') and (f.get('out_relapse') or f.get('out_DFS')): nrm = 'derivable (death without relapse)'
    elif f.get('out_OS') and f.get('out_cause_death'): nrm = 'approx. via cause of death'
    else: nrm = 'not available'
    score = SCOPE_W[sc] + sum(w for k, w in W.items() if f.get(k) and k != 'out_NRM_TRM')
    score += {'explicit variable': 30, 'derivable (death without relapse)': 20, 'approx. via cause of death': 12, 'not available': 0}.get(nrm, 28)
    if nrm == 'not available': tier = 'C - no NRM/TRM outcome'
    elif sc in ('leukemia/MDS (title)',) and score >= 85: tier = 'A - core training candidate'
    elif sc in ('leukemia/MDS (title)', 'mixed malignancies incl. leukemia/MDS') and score >= 70: tier = 'B - useful / supplementary'
    elif sc.startswith('not allo') or sc == 'non-malignant': tier = 'D - out of scope'
    else: tier = 'B- - NRM present, weaker fit'
    if sc.startswith('not allo'): tier = 'D - out of scope'
    out.append({'study_id': sid, 'tier': tier, 'score': score, 'disease_scope': sc, 'nrm_outcome': nrm, 'title': c['title'], 'first_author': c['first_author'],
                'start_year': c['start_year'], 'n_variables': nvars[sid],
                **{k: ';'.join(sorted(set(f.get(k, []))))[:300] for k in list(C) + ['out_DFS']},
                'publication_url': c['publication_url'], 'dataset_zip_url': c['dataset_zip_url'], 'data_dictionary_url': c['data_dictionary_url']})
# optional: patient counts from scripts/dataset_sizes.py
sizes_path = os.path.join(ROOT, 'dataset_sizes.csv')
sizes = {r['study_id']: r for r in csv.DictReader(open(sizes_path))} if os.path.exists(sizes_path) else {}
for r in out:
    z = sizes.get(r['study_id'], {})
    r['n_patients'], r['trm_events'], r['trm_rate'] = z.get('n_patients_rows', ''), z.get('trm_events', ''), z.get('trm_rate', '')
out.sort(key=lambda r: (r['tier'], -r['score']))
with open(os.path.join(ROOT, 'nrm_candidate_ranking.csv'), 'w', newline='') as fh:
    w = csv.DictWriter(fh, list(out[0].keys())); w.writeheader(); w.writerows(out)
with open(os.path.join(ROOT, 'variables_by_study.csv'), 'w', newline='') as fh:
    w = csv.DictWriter(fh, ['study_id', 'variable', 'description', 'type', 'levels']); w.writeheader(); w.writerows(vars_.values())
print(collections.Counter(r['tier'] for r in out))
for r in out:
    if r['tier'][0] in 'AB': print(r['tier'][:3], r['score'], r['study_id'], r['disease_scope'][:12], '|', r['nrm_outcome'][:14], '|', r['title'][:80])
