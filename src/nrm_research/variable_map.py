"""
Role: Map the column names of the six starting_point studies to one name.
Description: Holds the table of concepts, one row per concept and one column
per study, built from the data dictionaries of the studies. Builds the map of
every column in every CSV file, with the dictionary label and value codes,
and renames the columns of each CSV to the common name. A column absent in a
study stays absent. A column with no concept keeps its own name and is marked
unmapped. Renaming changes names only. Value codes can still differ between
studies, and the map marks the concepts where they do.
Author: Bor
"""
import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

STUDIES = ['P-5329', 'P-5370', 'P-5435', 'P-5521', 'P-5646', 'P-5702']

# Columns after the common name follow the order of STUDIES. None marks a
# concept that the study does not have.
CONCEPT_ROWS = [
    # Identifiers
    ('patient_id', 'pseudocrid', 'dummycrid', 'dummycrid', 'dummycrid',
     'dcrid', 'pseudoid'),
    ('center_id', 'pseudocenterid', 'dummyccn', 'dummyccn', 'dummyccn',
     'dccn', 'pseudoccn'),
    # Recipient
    ('age_years', 'age', None, 'age', 'age', 'age', 'age'),
    ('age_group', 'agegp', 'agegpff', 'agegp', 'agegp2', 'agegp', 'agegp'),
    ('sex', 'sex', 'sex', 'sex', 'sex', 'sex', 'sex'),
    ('race_ethnicity', None, None, None, 'ethgpn', 'ethgp', 'racegp'),
    ('karnofsky_score', 'karnofcat', 'kps', 'kps', 'kps', 'kps',
     'karnofcat'),
    ('hct_ci', 'hctci2gp', 'hctcigpc', 'sorror', None, 'hctcigp2',
     'hctcigp2'),
    ('hct_ci_4group', None, None, None, 'hctcigp', None, 'hctcigp'),
    ('bmi_group', None, None, None, None, 'obesity', None),
    ('cmv_recipient', None, None, 'rcmvpr', None, None, None),
    # Disease
    ('disease', None, 'disease', None, None, 'disease', 'dis'),
    ('disease_subgroup', 'strata', None, 'aml', None, None, None),
    ('study_main_group', None, 'strataf', None, None, None, None),
    ('disease_status_at_hct', 'distatprgpa', 'amstatprgp', None,
     'statusmrd', 'distage', 'alstatprgp'),
    ('disease_status_at_hct_mds', None, 'distatus', None, None, None, None),
    ('ipssr_prior_hct', None, None, None, None, 'ipssrpr', None),
    ('mrd_at_hct', None, None, 'mrdpr', None, None, None),
    ('cytogenetic_risk', 'cytogene', None, 'pi_class', 'cytogene',
     'cytogene', None),
    ('mll_subtype', None, None, 'pi_mll', None, None, None),
    ('wbc_at_diagnosis_group', 'wbcdxgp', 'wbcdxgp', 'wbcdxgp10', None,
     None, None),
    ('interval_dx_to_hct_months', 'intdxtx', None, None, None, 'intxdx',
     None),
    ('interval_dx_to_hct_group', 'intdxtxgp', None, None, 'intdxtxgp',
     'intxdxgp', None),
    ('mpn_etiology', 'prelkmpn', None, None, None, None, None),
    ('interval_mpn_mds_to_aml_years', 'intdxlk', None, None, None, None,
     None),
    ('interval_mpn_mds_to_aml_group', 'intdxlkgp', None, None, None, None,
     None),
    ('induction_therapy', 'therapygp', None, None, None, None, None),
    ('extramedullary_disease_dx', None, None, 'exmedx', None, None, None),
    ('prior_disease', None, None, 'l2disc', None, None, None),
    ('prior_disease_therapy', None, None, 'prth', None, None, None),
    ('time_to_cr1_weeks', None, None, 'indxcr1', None, None, None),
    ('time_to_cr1_group', None, None, 'dxcr1gp', None, None, None),
    ('interval_cr1_to_hct_months', None, None, 'incr1tx', None, None,
     None),
    ('interval_cr1_to_hct_group', None, None, 'cr1txgp', None, None, None),
    ('induction_courses', None, None, 'totind', None, None, None),
    ('immunophenotype', None, None, None, 'subgrp', None, None),
    ('ph_positive_status', None, None, None, 'philgptwo', None, None),
    # Transplant
    ('transplant_year', None, 'yeartx', 'yeartx', 'yeartx', 'yeartx',
     'yeartx'),
    ('transplant_year_group', 'yeartxgp', None, None, None, None, None),
    ('donor_type', 'donorgpa', 'donorgp_final', 'donorgp2', 'strato',
     'donorgp2', 'donorgp'),
    ('donor_age_years', None, None, None, 'dnrage', None, 'dnrage_urd'),
    ('donor_age_group_35', None, None, None, 'dnragegp35', None, None),
    ('donor_age_group', None, None, None, None, None, 'dagegp'),
    ('graft_type', 'graftypecat', 'graftype', 'graftype', 'graftypecat',
     'graftype', 'graftype'),
    ('conditioning_intensity', 'condintws', None, 'condintf', 'condescrp',
     'condint3', 'condtbi'),
    ('conditioning_regimen', None, 'condgrp', None, None, None, None),
    ('melphalan_conditioning', None, None, None, None, 'lpamgp', None),
    ('serotherapy', 'invivotdplt', 'atggrp', 'atgcampathgp',
     'atgcampathgp', 'atgcampathgp', 'atgcampathgp2'),
    ('gvhd_prophylaxis', 'gvhd2gp', 'gvhdgpf', 'gvhdgpf', 'gvhdnewtwo',
     'gvhdgp2', 'gvhdprgp'),
    ('gvhd_prophylaxis_alt', None, None, None, None, None, 'gvhdprgp2'),
    ('planned_gcsf_7d', 'plngf7d', None, None, None, None, None),
    ('cmv_donor_recipient', 'drcmvpr', 'drcmvprf', None, 'drcmvpr',
     'cmvmatch', 'drcmvpr'),
    ('sex_match', 'drsex', 'drsex', None, 'drsexno', 'sexmatch', 'drsex'),
    ('sex_mismatch_female_to_male', None, None, None, 'drsexregeno', None,
     None),
    ('abo_match', None, None, None, None, None, 'drabomatch'),
    ('rh_match', None, None, None, None, None, 'drrh'),
    ('rbc_depletion_form_v1_3', None, None, None, None, None, 'rbcreduc13'),
    ('buffy_coat_form_v1_3', None, None, None, None, None, 'buffycp13'),
    ('rbc_depletion_form_v4', None, None, None, None, None, 'rbcreduc4'),
    ('buffy_coat_form_v4', None, None, None, None, None, 'buffycp4'),
    ('plasma_volume_reduction', None, None, None, None, None, 'plasmarmv'),
    ('systemic_antibacterial', None, None, None, None, 'systebac', None),
    ('antibacterial_prophylaxis_type', None, None, None, None, 'antib_fluo',
     None),
    ('flow_mrd_analysis', None, None, None, None, 'flowgp', None),
    ('hospital_days_first_100d', None, None, None, None, 'hospdayi', None),
    ('region', None, None, None, 'regiongpmo', None, None),
    ('ted_flag', None, None, None, 'tedflag', None, None),
    ('sensitivity_analysis_flag', None, None, None, 'second_ana', None,
     None),
    # Outcomes
    ('os_event', 'dead', 'dead', 'dead', 'dead', 'dead', 'dead'),
    ('os_time_months', 'intxsurv', 'intxsurv', 'intxsurv', 'intxsurv',
     'intxsurv', 'intxsurv'),
    ('relapse_event', 'rel', 'rel', 'rel', 'rel', 'rel', 'rel'),
    ('nrm_event', 'trm', 'trm', 'trm', 'trm', 'trm', 'trm'),
    ('dfs_event', 'dfs', 'dfs', 'dfs', 'lfs', 'dfs', 'dfs'),
    ('relapse_or_death_time_months', 'intxrel', 'intxrel', 'intxrel',
     'intxrel', None, 'intxrel'),
    ('relapse_time_days', None, None, None, None, 'intxrel_d', None),
    ('grfs_event', None, None, 'grfs', None, None, None),
    ('grfs_time_months', None, None, 'intxgrfs', None, None, None),
    ('agvhd_grade2_4_event', 'agvhd24', None, None, 'agvhd', 'agvhd24',
     'agvhd24'),
    ('death_wo_agvhd_grade2_4', 'dwoagvhd24', None, None, 'dwoagvhd', None,
     'dwoagvhd24'),
    ('agvhd_grade2_4_time_months', 'intxagvhd24', None, None, 'intxagvhd',
     'intxagvhd24', 'intxagvhd24'),
    ('agvhd_grade2_4_time_days', None, None, None, None, 'intxagvhd24_d',
     None),
    ('agvhd_grade3_4_event', 'agvhd34', None, None, 'agvhd34', None,
     'agvhd34'),
    ('death_wo_agvhd_grade3_4', 'dwoagvhd34', None, None, 'dwoagvhd34',
     None, 'dwoagvhd34'),
    ('agvhd_grade3_4_time_months', 'intxagvhd34', None, None, 'intxagvhd34',
     None, 'intxagvhd34'),
    ('agvhd_lower_gi_grade2_4_event', None, None, None, None, 'agvhd24_lg',
     None),
    ('agvhd_lower_gi_grade2_4_time_months', None, None, None, None,
     'intxagvhd24_lg', None),
    ('cgvhd_event', 'cgvhd', None, None, 'cgvhd', 'cgvhd', 'cgvhd'),
    ('death_wo_cgvhd', 'dwocgvhd', None, None, 'dwocgvhd', None,
     'dwocgvhd'),
    ('cgvhd_time_months', 'intxcgvhd', None, None, 'intxcgvhd', 'intxcgvhd',
     'intxcgvhd'),
    ('cgvhd_gi_event', None, None, None, None, 'cgvhd_gi', None),
    ('cgvhd_gi_time_months', None, None, None, None, 'intxcgvhd_gi', None),
    ('neutrophil_recovery_event', 'anc', None, None, None, 'anc500', 'anc'),
    ('death_wo_neutrophil_recovery', 'dwoanc', None, None, None, None,
     'dwoancrel'),
    ('neutrophil_recovery_time_months', 'intxanc', None, None, None, None,
     'intxanc'),
    ('neutrophil_recovery_time_days', None, None, None, None, 'intx_anc',
     None),
    ('platelet_recovery_event', 'platelet', None, None, None, 'plat',
     'plt'),
    ('death_wo_platelet_recovery', 'dwoplatelet', None, None, None, None,
     'dwoplt'),
    ('platelet_recovery_time_months', 'intxplatelet', None, None, None,
     None, 'intxplt'),
    ('platelet_recovery_time_days', None, None, None, None, 'intx_pla20',
     None),
    ('primary_graft_failure_event', None, None, None, None, None, 'pgf'),
    ('cdi_100d_event', None, None, None, None, 'cdi100', None),
    ('cdi_time_days', None, None, None, None, 'intx_cdi100', None),
    ('cdi_recurrence_1y', None, None, None, None, 'cdi_recur', None),
    ('infection_mortality_event', None, None, None, None, 'infec', None),
    ('infection_mortality_time_months', None, None, None, None,
     'intx_infec', None),
    ('agvhd_before_cdi', None, None, None, None, 'agvh_cdi', None),
    ('agvhd_lower_gi_before_cdi', None, None, None, None, 'agvh_gi', None),
    ('mbi_bsi_near_cdi', None, None, None, None, 'mbicdigp', None),
    ('cmv_near_cdi', None, None, None, None, 'cmvcdigp', None),
    ('vre_bsi_near_cdi', None, None, None, None, 'vrecdigp', None),
]

NOTES = {
    'relapse_or_death_time_months':
        'Dictionaries of P-5370 and P-5435 say time to relapse. For NRM '
        'events the value equals os_time_months in 99.9 to 100 percent of '
        'patients, so it is the time to the first of relapse, death or last '
        'contact.',
    'relapse_time_days': 'P-5646 only. Divide by 30.4375 for months.',
    'neutrophil_recovery_time_days':
        'Unit is days (median 15 in P-5646, dictionary says days).',
    'platelet_recovery_time_days':
        'Unit inferred as days from the median of 19. The dictionary of '
        'P-5646 gives no unit.',
    'interval_dx_to_hct_months':
        'P-5646 intxdx has negative values (minimum -29). Check before use.',
    'sex_match':
        'P-5521 drsexno is not in its dictionary. Its counts match '
        'drsexregeno, so 1=M-M, 2=M-F, 3=F-M, 4=F-F.',
    'donor_age_years': 'P-5702 holds unrelated donors only.',
    'hct_ci': 'P-5370 hctcigpc has no label in its dictionary.',
    'dfs_event': 'P-5521 lfs is leukemia free survival.',
    'cmv_recipient': 'Recipient only. The others give donor and recipient.',
    'death_wo_neutrophil_recovery': 'P-5702 dwoancrel also counts relapse.',
}

LEVELS_DIFFER_NOTE = (
    'Value codes differ between studies. Harmonise the codes before '
    'pooling.')


def _csv_path(csv_dir: Path, study: str) -> Path:
    return csv_dir / (study.lower().replace('-', '_') + '.csv')


def _concept_lookup() -> dict[tuple[str, str], str]:
    """Return (study, column) to common name, checking for duplicates."""
    lookup: dict[tuple[str, str], str] = {}
    for row in CONCEPT_ROWS:
        if len(row) != len(STUDIES) + 1:
            raise ValueError('Concept row has wrong length: %s' % (row,))
        name = row[0]
        for study, column in zip(STUDIES, row[1:]):
            if column is None:
                continue
            key = (study, column)
            if key in lookup:
                raise ValueError(
                    '%s %s is mapped to both %s and %s'
                    % (study, column, lookup[key], name))
            lookup[key] = name
    names = [row[0] for row in CONCEPT_ROWS]
    if len(set(names)) != len(names):
        raise ValueError('A common name appears in two concept rows.')
    return lookup


def _dictionary_entries(variables_csv: Path) -> dict[tuple[str, str], tuple]:
    frame = pd.read_csv(variables_csv)
    entries = {}
    for row in frame.itertuples(index=False):
        label = None if pd.isna(row.description) else str(row.description)
        levels = None if pd.isna(row.levels) else str(row.levels)
        entries[(row.study_id, str(row.variable).lower())] = (label, levels)
    return entries


def build_variable_map(csv_dir: Path, variables_csv: Path) -> pd.DataFrame:
    """Return one row per column of every study CSV.

    Columns: study_id, original_name, common_name, status, dictionary_label,
    dictionary_levels, note. Status is mapped or unmapped. Raises ValueError
    when a concept names a column that is not in the CSV of its study, when
    two columns of one study get the same common name, or when an unmapped
    column keeps a name that a mapped column of the same study also has.
    """
    lookup = _concept_lookup()
    entries = _dictionary_entries(variables_csv)

    rows = []
    for study in STUDIES:
        columns = list(pd.read_csv(_csv_path(csv_dir, study), nrows=0))
        lowered = {c.lower(): c for c in columns}
        for (map_study, column) in lookup:
            if map_study == study and column not in lowered:
                raise ValueError(
                    '%s: concept column %s is not in the CSV'
                    % (study, column))
        for column in columns:
            common = lookup.get((study, column.lower()))
            label, levels = entries.get((study, column.lower()), (None, None))
            rows.append({
                'study_id': study,
                'original_name': column,
                'common_name': common if common is not None else column,
                'status': 'mapped' if common is not None else 'unmapped',
                'dictionary_label': label,
                'dictionary_levels': levels,
                'note': None,
            })
    result = pd.DataFrame(rows)

    duplicated = result.duplicated(['study_id', 'common_name'], keep=False)
    if duplicated.any():
        raise ValueError(
            'Duplicate common names:\n%s'
            % result.loc[duplicated, ['study_id', 'original_name',
                                      'common_name']].to_string())

    _add_notes(result)
    log.info(
        'Map has %s columns, %s mapped, %s unmapped',
        len(result), (result.status == 'mapped').sum(),
        (result.status == 'unmapped').sum())
    return result


def _add_notes(result: pd.DataFrame) -> None:
    for common, group in result[result.status == 'mapped'].groupby(
            'common_name'):
        notes = []
        if common in NOTES:
            notes.append(NOTES[common])
        levels = group.dictionary_levels.dropna().unique()
        if group.study_id.nunique() > 1 and len(levels) > 1:
            notes.append(LEVELS_DIFFER_NOTE)
        if notes:
            result.loc[group.index, 'note'] = ' '.join(notes)


def build_variable_matrix(variable_map: pd.DataFrame) -> pd.DataFrame:
    """Return common names as rows and studies as columns.

    Each cell holds the original name, or is empty when the study has no
    such column. Only the mapped columns are included.
    """
    mapped = variable_map[variable_map.status == 'mapped']
    matrix = mapped.pivot(
        index='common_name', columns='study_id', values='original_name')
    order = [row[0] for row in CONCEPT_ROWS]
    matrix = matrix.reindex(order)[STUDIES]
    matrix.insert(0, 'n_studies', matrix.notna().sum(axis=1))
    return matrix


def normalize_study_csvs(
        variable_map: pd.DataFrame, csv_dir: Path, out_dir: Path
        ) -> list[Path]:
    """Write each study CSV with common column names and a study_id column.

    Returns the paths written. Raises ValueError when a CSV already has a
    study_id column.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for study in STUDIES:
        frame = pd.read_csv(_csv_path(csv_dir, study), low_memory=False)
        if 'study_id' in frame.columns:
            raise ValueError('%s already has a study_id column' % study)
        rows = variable_map[variable_map.study_id == study]
        renames = dict(zip(rows.original_name, rows.common_name))
        frame = frame.rename(columns=renames)
        frame.insert(0, 'study_id', study)
        out_path = out_dir / _csv_path(csv_dir, study).name
        frame.to_csv(out_path, index=False)
        log.info('%s: %s columns -> %s', study, len(frame.columns), out_path)
        written.append(out_path)
    return written
