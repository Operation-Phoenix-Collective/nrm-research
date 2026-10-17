#!/usr/bin/env python3
"""Map every parsed dictionary variable onto one field ontology.

Reads data/variables_long.csv and data/catalog.csv. Writes:
  data/field_ontology.csv         one row per canonical field (concept + role)
  data/field_dataset_mapping.csv  one row per study and source variable

Same-name columns are one field. intx* / dwo* / *gp forms of a known concept
join that concept as time, competing risk, or bin. Everything else keeps its
own name under a domain guessed from the description, and is not stacked.
"""
import csv, collections, os, re, sys

ROOT = os.path.abspath(os.path.expanduser(
    (sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else None)
    or os.environ.get('CIBMTR_DATA_DIR')
    or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')))

# concept_id -> domain, label, definition, note appended to the role rule
CONCEPTS = {
    'patient_id': ('identity', 'Patient identifier',
                   'Study-specific pseudonym for the recipient (CRID or patient id).',
                   'Names differ (pseudoid, dummyid, pseudocrid) and values still do not join across studies.'),
    'center_id': ('identity', 'Center identifier',
                  'Study-specific pseudonym for the transplant center.',
                  'dummyccn and pseudoccn are the same kind of identifier and are not a shared center key.'),
    'recipient_age': ('recipient', 'Recipient age',
                      'Recipient age at transplant, in years.',
                      'Prefer the continuous column. Bins use different cut points in each study.'),
    'recipient_sex': ('recipient', 'Recipient sex',
                      'Recipient sex.',
                      'Most studies use 1=Male, 2=Female. Missing is 9 or 99 in some extracts and absent in others.'),
    'recipient_race': ('recipient', 'Recipient race',
                       'Recipient race, as grouped by the study.',
                       'Labels disagree (White vs Caucasian; category order is not stable). Crosswalk labels, not integers.'),
    'recipient_ethnicity': ('recipient', 'Recipient ethnicity',
                            'Recipient ethnicity, separate from race when the study collected both.',
                            ''),
    'kps': ('recipient', 'Karnofsky performance status',
            'Karnofsky performance score before the preparative regimen.',
            'Cut points flip across studies (<90 vs >=90 is not always code 1). Use the score when present.'),
    'hct_ci': ('recipient', 'HCT comorbidity index',
               'HCT-CI / Sorror comorbidity score.',
               'hctci, hctcigp, and sorror are the same index with different binning. The bare name hct is this index only when the description says so; other hct columns are a transplant count or a transplant type.'),
    'donor_weight': ('donor', 'Donor weight', 'Donor weight at collection, in kilograms.', ''),
    'donor_bmi': ('donor', 'Donor BMI', 'Donor body-mass index group.', ''),
    'collection_year': ('donor', 'Collection year', 'Year the donor was collected.', ''),
    'insurance': ('recipient', 'Health insurance', 'Recipient health-insurance type.', ''),
    'baseline_platelets': ('recipient', 'Baseline platelets',
                           'Platelet count at baseline, x10^9/L. Not platelet engraftment.', ''),
    'baseline_wbc': ('recipient', 'Baseline white cell count',
                     'White-cell count at baseline, x10^9/L.', ''),
    'wbc_at_diagnosis': ('disease', 'WBC at diagnosis', 'White-cell count at diagnosis.', ''),
    'prior_therapy_lines': ('disease', 'Lines of prior therapy',
                            'Number of therapy lines before the index HCT or cell therapy.',
                            'The cell-therapy column excludes the cell therapy itself. Do not treat the integer as comparable without that distinction.'),
    'dx_to_cell_therapy': ('cell_therapy', 'Diagnosis to cell therapy',
                           'Time from diagnosis to cell-therapy infusion, in months.',
                           'Not the HCT diagnosis-to-transplant interval.'),
    'lymphodepletion': ('cell_therapy', 'Lymphodepleting regimen',
                        'Lymphodepleting chemotherapy before cell therapy.', ''),
    'ldh_prior': ('cell_therapy', 'LDH before infusion',
                  'Elevated LDH before cell-therapy infusion.', ''),
    'recipient_cmv': ('recipient', 'Recipient CMV serostatus',
                      'Recipient CMV antibody status before transplant.',
                      ''),
    'marital_status': ('recipient', 'Marital status', 'Recipient marital status.', ''),
    'donor_age': ('donor', 'Donor age', 'Donor age at collection or transplant.',
                  'Prefer the continuous column over decade bins.'),
    'donor_sex': ('donor', 'Donor sex', 'Donor sex.', ''),
    'donor_cmv': ('donor', 'Donor CMV serostatus', 'Donor CMV antibody status.', ''),
    'sex_match': ('donor', 'Donor-recipient sex match',
                  'Sex combination of donor and recipient.', ''),
    'cmv_match': ('donor', 'Donor-recipient CMV match',
                  'CMV serostatus combination of donor and recipient.', ''),
    'abo_match': ('donor', 'Donor-recipient ABO match', 'ABO match between donor and recipient.', ''),
    'donor_type': ('donor', 'Donor type',
                   'Donor relation and HLA match group (sibling, unrelated, haploidentical, cord).',
                   'Code lists are study-specific. Do not treat code 1 as the same donor type in every extract.'),
    'hla_match': ('donor', 'HLA match',
                  'Degree of HLA match between donor and recipient.',
                  'Distinct from donor type even when the variable name looks like donorgp.'),
    'disease': ('disease', 'Primary disease',
                'Disease for which the transplant or cell therapy was done.',
                'Each study collapses diseases differently. Keep the label.'),
    'disease_status': ('disease', 'Disease status',
                       'Disease status or stage at transplant.',
                       'CR1/CR2/relapse groupings are not aligned across extracts.'),
    'cytogenetics': ('disease', 'Cytogenetics',
                     'Cytogenetic or molecular risk group.', ''),
    'dri': ('disease', 'Disease risk index', 'Disease risk index.', ''),
    'ipss_r': ('disease', 'IPSS-R', 'MDS IPSS-R risk at transplant.', ''),
    'dx_to_hct': ('disease', 'Diagnosis to transplant',
                  'Time from diagnosis to transplant.',
                  'Unit is months when stated. Do not mix with post-transplant intervals.'),
    'year_of_hct': ('transplant', 'Year of transplant',
                    'Calendar year of hematopoietic cell transplant.',
                    'Use the continuous year. Year groups are study windows, not a shared binning.'),
    'year_of_cell_therapy': ('cell_therapy', 'Year of cell therapy',
                             'Calendar year of the cell-therapy infusion, not of an HCT.',
                             'Keep CAR-T rows off the HCT year column.'),
    'graft_source': ('transplant', 'Graft source',
                     'Stem-cell source: bone marrow, peripheral blood, or cord blood.',
                     'Marrow/PB/cord codes differ (1/22/23 is common and not universal).'),
    'conditioning_intensity': ('transplant', 'Conditioning intensity',
                               'Myeloablative, reduced-intensity, or non-myeloablative conditioning.',
                               ''),
    'conditioning_regimen': ('transplant', 'Conditioning regimen',
                             'Named conditioning regimen, which is not the same as intensity.',
                             ''),
    'tbi': ('transplant', 'Total body irradiation', 'Whether the regimen included TBI, or the TBI dose group.', ''),
    'gvhd_prophylaxis': ('transplant', 'GVHD prophylaxis',
                         'GVHD prophylaxis platform (including post-transplant cyclophosphamide when grouped here).',
                         ''),
    'atg': ('transplant', 'ATG or alemtuzumab',
           'In vivo T-cell depletion with ATG or alemtuzumab.', ''),
    'transplant_type': ('transplant', 'Transplant type',
                        'Autologous versus allogeneic, when the study coded it.', ''),
    'prior_hct': ('transplant', 'Prior transplant', 'A transplant before the index procedure.', ''),
    'melphalan_dose': ('transplant', 'Melphalan dose', 'Melphalan dose in the conditioning regimen.', ''),
    'overall_survival': ('outcome', 'Overall survival',
                         'Death from any cause, and the time from transplant to death or last follow-up.',
                         'Use this clock for non-relapse mortality too. There is no separate NRM time column.'),
    'nrm': ('outcome', 'Non-relapse mortality',
            'Death without relapse (TRM/NRM). Not a survival time.',
            'Some extracts censor a later HCT and some do not. The description says which; keep that as a flag rather than pooling blindly.'),
    'relapse': ('outcome', 'Relapse or progression',
                'Relapse or progression after transplant, and the time to that event.',
                'Lymphoma studies often fold progression into this indicator.'),
    'dfs': ('outcome', 'Disease-free survival',
            'Treatment failure defined as relapse or death.',
            'In several lymphoma dictionaries the description of dfs is progression-free survival. Read the description before merging with pfs.'),
    'pfs': ('outcome', 'Progression-free survival',
            'Progression or death. Kept separate from dfs because the event definitions are not the same in every study.',
            ''),
    'chronic_gvhd': ('outcome', 'Chronic GVHD',
                     'Any chronic GVHD, the time to it, and death without it.', ''),
    'acute_gvhd_24': ('outcome', 'Acute GVHD grades II-IV',
                      'Grade II-IV acute GVHD, the time to it, and death without it.',
                      'Not interchangeable with grade III-IV.'),
    'acute_gvhd_34': ('outcome', 'Acute GVHD grades III-IV',
                      'Grade III-IV acute GVHD, the time to it, and death without it.',
                      'Trust the variable name when a description disagrees: a few dictionaries put the grade II-IV or chronic-GVHD text on the grade III-IV column.'),
    'acute_gvhd': ('outcome', 'Acute GVHD, any grade',
                   'Acute GVHD without a grade restriction.',
                   'Do not fill this from the grade II-IV column.'),
    'neutrophil_recovery': ('outcome', 'Neutrophil recovery',
                            'Neutrophil engraftment, usually ANC >= 0.5 x 10^9/L sustained three days.',
                            ''),
    'platelet_recovery': ('outcome', 'Platelet recovery',
                          'Platelet engraftment. Baseline platelet count is a different field.', ''),
    'graft_failure': ('outcome', 'Graft failure', 'Graft failure and the time to it.', ''),
    'grfs': ('outcome', 'GVHD-free relapse-free survival',
             'GRFS event (grade III-IV acute GVHD, chronic GVHD requiring systemic therapy, relapse, or death).',
             ''),
    'crfs': ('outcome', 'Chronic-GVHD-free relapse-free survival', 'CRFS event.', ''),
    'cause_of_death': ('outcome', 'Cause of death',
                       'Primary cause of death, grouped by the study.', ''),
    'bacterial_infection': ('outcome', 'Bacterial infection', 'Bacterial infection after transplant.', ''),
    'fungal_infection': ('outcome', 'Fungal infection', 'Fungal infection after transplant.', ''),
    'bridging_therapy': ('cell_therapy', 'Bridging therapy',
                         'Therapy given between leukapheresis and cell-therapy infusion.', ''),
    'cell_product': ('cell_therapy', 'Cell-therapy product', 'CAR-T or other cellular product.', ''),
    'crs': ('cell_therapy', 'Cytokine release syndrome', 'CRS grade or status after cell therapy.', ''),
    'neurotoxicity': ('cell_therapy', 'Neurotoxicity', 'ICANS or neurotoxicity grade or status after cell therapy.', ''),
    'ct_response': ('cell_therapy', 'Cell-therapy response',
                    'Response after cell therapy (complete response, or complete plus partial).', ''),
}

# exact source name -> (concept_id, role)
ALIAS = {}

def alias(concept, role, *names):
    for n in names:
        ALIAS[n.lower()] = (concept, role)

def compact_alias(var):
    """sex_match and sexmatch are the same column when every underscore-free spelling agrees."""
    c = var.lower().replace('_', '')
    hits = {val for key, val in ALIAS.items() if key.replace('_', '') == c}
    if len(hits) == 1:
        concept, role = hits.pop()
        return concept, role, 'alias'
    return None

alias('patient_id', 'identifier', 'pseudoid', 'dummyid', 'pseudocrid', 'dummycrid', 'dcrid')
alias('center_id', 'identifier', 'dummyccn', 'pseudoccn', 'pseudocenterid', 'dccn')
alias('recipient_age', 'measure', 'age')
alias('recipient_age', 'bin', 'agegp', 'agegp2', 'age65', 'age_gp', 'agecat', 'agegrp', 'ragecat')
alias('recipient_sex', 'category', 'sex', 'ct_sex')
alias('recipient_race', 'category', 'racegp', 'racegrp', 'race', 'race5gp', 'race_gp', 'racen', 'racegp2')
alias('recipient_ethnicity', 'category', 'ethnicit', 'ethgp')
alias('kps', 'measure', 'kps', 'kpr')
alias('kps', 'bin', 'kpsgp', 'kps2', 'kps_gp', 'kps80', 'karnofcat', 'karnofgp')
alias('hct_ci', 'measure', 'hctci', 'sorror', 'coorgscore')
alias('hct_ci', 'bin', 'hctcigp', 'hctci2gp', 'hctcigrp', 'hctcigp2', 'sorrorgp', 'sorror_grp')
alias('donor_weight', 'measure', 'd_wt')
alias('donor_bmi', 'bin', 'd_bmi_grp')
alias('collection_year', 'measure', 'coll_yr')
alias('insurance', 'category', 'insurgrp', 'insurance')
alias('baseline_platelets', 'measure', 'plt0')
alias('baseline_wbc', 'measure', 'wbc0')
alias('wbc_at_diagnosis', 'bin', 'wbcdxgp')
alias('prior_therapy_lines', 'measure', 'nchemo', 'ct_ntreatvpr_noct')
alias('dx_to_cell_therapy', 'time', 'intdxct_month')
alias('lymphodepletion', 'category', 'ct_ldchemolst')
alias('ldh_prior', 'category', 'ct_ldhprgp')
alias('acute_gvhd_34', 'competing_risk', 'dwoagvhd3')
alias('recipient_cmv', 'category', 'rcmvpr', 'cmv', 'cmvgp', 'rcmv')
alias('marital_status', 'category', 'marstat')
alias('donor_age', 'measure', 'dnrage', 'coll_age')
alias('donor_age', 'bin', 'dnragegp', 'dnrage_gp', 'dagecat', 'dagegp')
alias('donor_sex', 'category', 'drsex', 'dsex')
alias('donor_cmv', 'category', 'drcmvpr', 'drcmvpr_2')
alias('sex_match', 'category', 'sexmatch', 'sexmatchgp')
alias('cmv_match', 'category', 'cmvmatch', 'cmvmatchgp')
alias('abo_match', 'category', 'drabomatch')
alias('donor_type', 'category', 'donorgp', 'donorgrp', 'donor', 'donor2gp', 'dnrgp')
alias('hla_match', 'category', 'donorgp2', 'hla_match')
alias('disease', 'category', 'disease', 'diseasegp', 'disgp', 'dis', 'disgrp', 'discat', 'dis_grp')
alias('disease_status', 'category', 'distat', 'distat2', 'distatgp', 'distatgrp', 'disstat', 'status', 'myestaprgp', 'mds_stagegp', 'distage', 'ct_dstprm')
alias('cytogenetics', 'category', 'cytogene', 'cytogener', 'cytogenetics')
alias('dri', 'measure', 'dri')
alias('dri', 'bin', 'drigp')
alias('ipss_r', 'category', 'ipssrpr')
alias('dx_to_hct', 'time', 'intdxtx', 'intdxtxgp', 'intdxtx6gp', 'indxtx', 'indxtxgp', 'indxtx2', 'indxtx1', 'intdxdt', 'intxdx')
alias('year_of_hct', 'measure', 'yeartx', 'year')
alias('year_of_hct', 'bin', 'yeartxgp', 'yeargp', 'yeargrp')
alias('year_of_cell_therapy', 'measure', 'yearct')
alias('graft_source', 'category', 'graftype', 'graftypecat', 'graftype2', 'graftypegp', 'graftgp', 'graft')
alias('conditioning_intensity', 'category', 'condint', 'condint2', 'condintgp', 'condint3', 'condintgrp', 'condintted')
alias('conditioning_regimen', 'category', 'condgrp', 'condgp', 'cond', 'cond2', 'condcat', 'condreg', 'conditioning_regimen')
alias('tbi', 'category', 'tbi', 'tbigp', 'tbi_gp', 'condtbi')
alias('gvhd_prophylaxis', 'category', 'gvhdgp', 'gvhdgrp', 'gvhd2gp', 'gvhd_gp', 'gvhdgp2', 'gvhdgp3', 'gvhdgp4', 'gvhdgpn', 'gvhdgroup', 'gvhprhrx', 'gvhdgp_cat', 'gvhdgp0', 'gvhdgpcat')
alias('atg', 'category', 'atgcampathgp', 'atgcampath', 'atgcamp', 'atggp', 'atg')
alias('transplant_type', 'category', 'txtype')
alias('prior_hct', 'category', 'priauto', 'priautogp', 'ct_priorhct', 'ct_priortxtype')
alias('melphalan_dose', 'bin', 'lpamgp')
alias('overall_survival', 'event', 'dead', 'dead25', 'dead24')
alias('overall_survival', 'time', 'intxsurv', 'intxsurv0', 'intxsurv24', 'inctsurv_month')
alias('nrm', 'event', 'trm', 'trm25', 'trm24', 'nrm')
alias('relapse', 'event', 'rel', 'rel25', 'rel24', 'progrel')
alias('relapse', 'time', 'intxrel', 'intxrel0', 'intxrel24', 'intctrel_month')
alias('dfs', 'event', 'dfs', 'dfs25', 'dfs24')
alias('pfs', 'event', 'pfs')
alias('chronic_gvhd', 'event', 'cgvhd', 'cgvhd_24')
alias('chronic_gvhd', 'time', 'intxcgvhd', 'intxcgvhd_24')
alias('chronic_gvhd', 'competing_risk', 'dwocgvhd', 'dwocgvhd_24')
alias('acute_gvhd_24', 'event', 'agvhd24')
alias('acute_gvhd_24', 'time', 'intxagvhd24')
alias('acute_gvhd_24', 'competing_risk', 'dwoagvhd24')
alias('acute_gvhd_34', 'event', 'agvhd34')
alias('acute_gvhd_34', 'time', 'intxagvhd34')
alias('acute_gvhd_34', 'competing_risk', 'dwoagvhd34')
alias('acute_gvhd', 'event', 'agvhd')
alias('acute_gvhd', 'time', 'intxagvhd')
alias('acute_gvhd', 'competing_risk', 'dwoagvhd')
alias('neutrophil_recovery', 'event', 'anc', 'anc500')
alias('neutrophil_recovery', 'time', 'intxanc', 'intxanc500', 'intctanc')
alias('neutrophil_recovery', 'competing_risk', 'dwoanc', 'dwoanc500')
alias('platelet_recovery', 'event', 'platelet', 'plt')
alias('platelet_recovery', 'time', 'intxplatelet', 'intxplt', 'intctplatelet')
alias('platelet_recovery', 'competing_risk', 'dwoplatelet', 'dwoplt')
alias('graft_failure', 'event', 'gf')
alias('graft_failure', 'time', 'intxgf')
alias('graft_failure', 'competing_risk', 'dwogf')
alias('grfs', 'event', 'grfs', 'grfs24')
alias('grfs', 'time', 'intxgrfs', 'intxgrfs24')
alias('grfs', 'bin', 'grfscat')
alias('crfs', 'event', 'crfs')
alias('cause_of_death', 'category', 'grpcod', 'deathgp', 'ct_primdeath')
alias('bacterial_infection', 'category', 'bacgp')
alias('fungal_infection', 'category', 'fungp', 'funghxpr')
alias('bridging_therapy', 'category', 'ct_treatbg', 'bridge')
alias('cell_product', 'category', 'car_prdtype')
alias('crs', 'category', 'ct_crsgrade_h1', 'crsstat')
alias('crs', 'time', 'intcrs')
alias('neurotoxicity', 'category', 'ct_neutoxgrade_h1', 'neutoxstat')
alias('neurotoxicity', 'time', 'intneutox')
alias('ct_response', 'category', 'ct_lymcrrate_100d', 'ct_lymbrrate_100d')

# remainder after intx/dwo/intct -> concept, used only when the full name is not aliased
STEM = {
    'surv': 'overall_survival', 'dead': 'overall_survival',
    'rel': 'relapse', 'relapse': 'relapse', 'progrel': 'relapse',
    'trm': 'nrm', 'dfs': 'dfs', 'pfs': 'pfs',
    'cgvhd': 'chronic_gvhd', 'agvhd24': 'acute_gvhd_24', 'agvhd34': 'acute_gvhd_34', 'agvhd': 'acute_gvhd',
    'anc': 'neutrophil_recovery', 'anc500': 'neutrophil_recovery',
    'platelet': 'platelet_recovery', 'plt': 'platelet_recovery',
    'gf': 'graft_failure', 'grfs': 'grfs', 'crfs': 'crfs',
}
BIN_OF = {
    'age': 'recipient_age', 'yeartx': 'year_of_hct', 'year': 'year_of_hct',
    'kps': 'kps', 'karnof': 'kps', 'dnrage': 'donor_age', 'dage': 'donor_age',
    'hctci': 'hct_ci', 'dri': 'dri', 'graftype': 'graft_source',
}

ROLE_TYPE = {
    'event': 'categorical', 'competing_risk': 'categorical', 'category': 'categorical', 'bin': 'categorical',
    'time': 'continuous', 'measure': 'continuous', 'identifier': 'identifier',
}
ROLE_STACK = {
    'event': 'recode', 'competing_risk': 'recode', 'time': 'recode', 'measure': 'recode',
    'category': 'crosswalk', 'bin': 'derive_from_continuous', 'identifier': 'do_not_stack',
}
ROLE_RULE = {
    'event': 'Recode to 1 = event, 0 = censored, blank = missing. Study dictionaries use Yes/No, Censoring/Event, and 99 = missing for the same indicator.',
    'time': 'Store months. Divide by 30.4375 when the description says days. If the description does not state a unit, leave the value unconverted.',
    'competing_risk': 'Recode like an event. Pair it with the event column and with overall-survival time; these extracts rarely have a separate clock.',
    'measure': 'Stack the numeric value. Do not fill it from a binned sibling.',
    'bin': 'Cut points differ by study. After stacking, derive groups from the continuous sibling, or keep the bin inside one study.',
    'category': 'Crosswalk the labels. The same integer means different levels in different extracts.',
    'identifier': 'Do not join rows across studies on this value.',
}

DOMAIN_RULES = (
    ('cell_therapy', r'car-?t|cytokine release|\bcrs\b|neurotox|icans|infusion|apheresis|lymphodeplet'),
    ('outcome', r'\bgvhd\b|graft-versus|relapse|progress|mortality|\btrm\b|\bnrm\b|survival|engraft|neutrophil|platelet recovery|graft failure|cause of death'),
    ('transplant', r'condition|myeloablat|\btbi\b|prophylaxis|graft source|donor type|hla|year of (hct|transplant)'),
    ('donor', r'\bdonor\b'),
    ('disease', r'disease|cytogen|karyotyp|diagnosis|remission|\baml\b|lymphoma|myeloma'),
    ('recipient', r'\bage\b|karnofsky|\bkps\b|comorbid|race|ethnic|\bsex\b|\bbmi\b|performance'),
    ('identity', r'pseudo|de-identif|dummy |center id|patient id'),
)


def type_class(raw):
    t = (raw or '').strip().lower()
    if t in ('categorical', 'character', 'char'): return 'categorical'
    if t in ('continuous', 'numeric', 'num', 'integer', 'continous'): return 'continuous'
    if not t or t in ('na', 'n/a', 'none', 'no label'): return 'unknown'
    return 'misparsed'


def time_unit(desc):
    d = (desc or '').lower()
    if 'day' in d: return 'days'
    if 'month' in d: return 'months'
    if 'year' in d: return 'years'
    return ''


def stem_concept(rest):
    rest = re.sub(r'(_month|_months|_day|_days)$', '', rest)
    return STEM.get(rest)


def resolve(var, desc):
    v = var.lower()
    # "hct" is the comorbidity index only when the description says so.
    if v == 'hct' and re.search(r'sorror|hct-?\s*ci|comorbid', desc or '', re.I):
        return 'hct_ci', 'measure', 'description'
    if v in ALIAS:
        concept, role = ALIAS[v]
        return concept, role, 'alias'
    hit = compact_alias(v)
    if hit: return hit
    # intct/inct are cell-therapy clocks and stay off the HCT fields unless aliased above.
    for pre, role in (('intx', 'time'), ('dwo', 'competing_risk')):
        if v.startswith(pre) and len(v) > len(pre) + 1:
            concept = stem_concept(v[len(pre):].lstrip('_'))
            if concept: return concept, role, 'structural'
    for suf in ('gp', 'grp', 'cat', '_gp', '_grp'):
        if v.endswith(suf) and len(v) > len(suf) + 1:
            stem = v[:-len(suf)].rstrip('_')
            if stem in BIN_OF: return BIN_OF[stem], 'bin', 'structural'
    return None


def other_domain(var, desc):
    s = f'{var} {desc}'.lower()
    if var.lower().startswith('ct_'): return 'cell_therapy'
    for domain, rx in DOMAIN_RULES:
        if re.search(rx, s): return domain
    return 'other'


def other_role(var, desc, tclass):
    v = var.lower()
    if v.startswith(('intx', 'intct', 'inct', 'intdx')) or re.search(r'\btime\b|interval', desc or '', re.I):
        return 'time'
    if v.startswith('dwo') or re.search(r'^death without', desc or '', re.I):
        return 'competing_risk'
    if re.search(r'pseudo|dummy|de-identif|\bid\b', f'{v} {desc or ""}', re.I):
        return 'identifier'
    if tclass == 'continuous': return 'measure'
    return 'category'


def slug(var):
    s = re.sub(r'[^a-z0-9]+', '_', var.lower()).strip('_')
    return s or 'blank'


def load_pairs():
    """One record per study and variable, with its code list."""
    acc = {}
    for r in csv.DictReader(open(os.path.join(ROOT, 'variables_long.csv'), newline='', encoding='utf-8')):
        key = (r['study_id'], r['variable'])
        d = acc.setdefault(key, {'desc': '', 'type': '', 'codes': []})
        if r['description'] and not d['desc']: d['desc'] = r['description'].strip()
        if r['type'] and not d['type']: d['type'] = r['type'].strip()
        if r['value'] or r['label']: d['codes'].append(f"{r['value']}={r['label']}".strip('='))
    titles = {}
    cat = os.path.join(ROOT, 'catalog.csv')
    if os.path.exists(cat):
        for r in csv.DictReader(open(cat, newline='', encoding='utf-8')):
            titles[r['study_id']] = r.get('title', '')
    return acc, titles


def main():
    acc, titles = load_pairs()
    mapping = []
    for (sid, var), d in acc.items():
        hit = resolve(var, d['desc'])
        if hit:
            concept, role, how = hit
            domain = CONCEPTS[concept][0]
            field = f'{concept}.{role}'
        else:
            role = other_role(var, d['desc'], type_class(d['type']))
            domain = other_domain(var, d['desc'])
            concept = slug(var)
            field = f'{domain}.{concept}.{role}'
            how = 'same_name'
        mapping.append({
            'study_id': sid,
            'dataset_title': titles.get(sid, ''),
            'source_variable': var,
            'source_description': d['desc'],
            'source_type': d['type'],
            'type_class': type_class(d['type']),
            'time_unit': time_unit(d['desc']) if role == 'time' else '',
            'n_levels': len(d['codes']),
            'codes': '; '.join(d['codes'][:12]),
            'field_id': field,
            'taxonomy': f'{domain} / {concept} / {role}',
            'domain': domain,
            'concept': concept,
            'role': role,
            'match_method': how,
        })

    by_field = collections.defaultdict(list)
    for m in mapping: by_field[m['field_id']].append(m)

    ontology = []
    for field, rows in by_field.items():
        domain, concept, role = rows[0]['domain'], rows[0]['concept'], rows[0]['role']
        shared = rows[0]['match_method'] != 'same_name'
        if shared and concept in CONCEPTS:
            label_domain, label, definition, note = CONCEPTS[concept]
            domain = label_domain
        else:
            shared = False
            label = rows[0]['source_description'] or concept
            definition = label
            note = 'Occurs under one source name. Kept out of the shared column set.'
        studies = {r['study_id'] for r in rows}
        names = collections.Counter(r['source_variable'] for r in rows)
        descs = collections.Counter(r['source_description'] for r in rows if r['source_description'])
        codes = collections.Counter(r['codes'] for r in rows if r['codes'])
        units = collections.Counter(r['time_unit'] for r in rows if r['time_unit'])
        rule = ROLE_RULE.get(role, '')
        if note: rule = (rule + ' ' + note).strip()
        if role == 'time' and units:
            rule += ' Units seen: ' + ', '.join(f'{u} ({n})' for u, n in units.most_common()) + '.'
        ontology.append({
            'field_id': field,
            'taxonomy': f'{domain} / {label} / {role}',
            'domain': domain,
            'concept': concept,
            'concept_label': label,
            'role': role,
            'definition': definition,
            'canonical_type': ROLE_TYPE.get(role, ''),
            'stack': ROLE_STACK.get(role, 'do_not_stack') if shared else 'do_not_stack',
            'n_studies': len(studies),
            'n_source_variables': len(names),
            'source_variables': ' | '.join(f'{n} ({c})' for n, c in names.most_common()),
            'description_variants': ' | '.join(f'{c}: {d}' for d, c in descs.most_common(5)),
            'n_distinct_code_lists': len(codes),
            'modal_codes': codes.most_common(1)[0][0] if codes else '',
            'harmonization': rule,
        })

    ontology.sort(key=lambda r: (r['domain'], -r['n_studies'], r['field_id']))
    mapping.sort(key=lambda r: (r['study_id'], r['field_id'], r['source_variable']))

    ont_fields = ['field_id', 'taxonomy', 'domain', 'concept', 'concept_label', 'role', 'definition',
                  'canonical_type', 'stack', 'n_studies', 'n_source_variables', 'source_variables',
                  'description_variants', 'n_distinct_code_lists', 'modal_codes', 'harmonization']
    map_fields = ['study_id', 'dataset_title', 'source_variable', 'source_description', 'source_type',
                  'type_class', 'time_unit', 'n_levels', 'codes', 'field_id', 'taxonomy', 'domain',
                  'concept', 'role', 'match_method']
    def write(name, rows, fields):
        path = os.path.join(ROOT, name)
        with open(path, 'w', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, fields, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
        return path

    op = write('field_ontology.csv', ontology, ont_fields)
    mp = write('field_dataset_mapping.csv', mapping, map_fields)

    core = [r for r in mapping if r['match_method'] != 'same_name']
    print(f'{len(mapping)} source variables, {len({r["study_id"] for r in mapping})} studies')
    shared = sum(1 for r in ontology if r['stack'] != 'do_not_stack')
    print(f'{len(ontology)} ontology fields, {shared} shared fields')
    print(f'mapped onto a shared concept: {len(core)} ({100 * len(core) / len(mapping):.0f}%)')
    print('by method', dict(collections.Counter(r['match_method'] for r in mapping)))
    print('by domain', dict(collections.Counter(r['domain'] for r in mapping)))
    fell = collections.Counter(r['source_variable'].lower() for r in mapping if r['match_method'] == 'same_name')
    frequent = [(n, c) for n, c in fell.most_common(25) if c >= 5]
    print('frequent names left unmerged:')
    for n, c in frequent: print(f'  {c:3} {n}')
    # the shared survival pair must land on the curated fields
    got = {(r['source_variable'].lower(), r['field_id']) for r in mapping}
    want = {('dead', 'overall_survival.event'), ('intxsurv', 'overall_survival.time'),
            ('trm', 'nrm.event'), ('agegp', 'recipient_age.bin'), ('dwoagvhd24', 'acute_gvhd_24.competing_risk'),
            ('dwoagvhd3', 'acute_gvhd_34.competing_risk'), ('plt0', 'baseline_platelets.measure')}
    missing = [w for w in want if w not in got]
    bad = [r['field_id'] for r in mapping if r['source_variable'].lower() == 'inctsurv' and r['field_id'] == 'overall_survival.time']
    if missing or bad: sys.exit(f'ontology check failed: {missing} {bad}')
    print('wrote', op)
    print('wrote', mp)

if __name__ == '__main__':
    main()
