"""
Role: Build the training data for a survival model from the six study CSVs.
Description: Combines the normalized study CSV files into one file, then
prepares that file for a survival model such as DeepSurv (Katzman et al.,
2018). Preparing keeps only the variables known before the transplant, takes
overall survival as the outcome, splits the patients into train, validation
and test sets, and encodes each set with settings learned on the train set
only. The prepared files hold the encoded features plus the columns time and
event. Codes of categorical variables differ between studies, so each code is
kept as its own level per study. Only sex has the same codes in all studies.
Author: Bor
"""
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

TIME_COLUMN = 'os_time_months'
EVENT_COLUMN = 'os_event'
STUDY_COLUMN = 'study_id'
ID_COLUMNS = [STUDY_COLUMN, 'patient_id']

# Known before the transplant. Outcomes, complications after the transplant,
# identifiers and study flags are left out so the model cannot see the result.
NUMERIC_FEATURES = [
    'age_years', 'donor_age_years', 'transplant_year',
    'interval_dx_to_hct_months',
]
# Same codes in every study.
POOLED_CATEGORICAL_FEATURES = ['sex']
# Codes differ between studies, so the level is study plus code.
STUDY_CATEGORICAL_FEATURES = [
    'age_group', 'race_ethnicity', 'karnofsky_score', 'hct_ci',
    'hct_ci_4group', 'disease', 'disease_subgroup', 'disease_status_at_hct',
    'disease_status_at_hct_mds', 'cytogenetic_risk', 'wbc_at_diagnosis_group',
    'donor_type', 'graft_type', 'conditioning_intensity', 'serotherapy',
    'gvhd_prophylaxis', 'cmv_donor_recipient', 'sex_match',
]

# A negative interval from diagnosis to transplant is not possible (P-5646).
NON_NEGATIVE_FEATURES = ['interval_dx_to_hct_months']

RARE_LEVEL = 'other'
MISSING_LEVEL = 'missing'


def combine_study_csvs(input_folder, output_csv):
    """Stack all CSV files of a folder into one file and return the table.

    Columns are the union of all files. A column a study does not have is
    empty for its patients. The study_id column tells the studies apart.
    """
    files = sorted(Path(input_folder).glob('*.csv'))
    if not files:
        raise FileNotFoundError('No CSV files in %s' % input_folder)
    tables = []
    for file in files:
        table = pd.read_csv(file, low_memory=False)
        log.info('%s: %s patients, %s columns', file.name, len(table),
                 table.shape[1])
        tables.append(table)
    combined = pd.concat(tables, ignore_index=True, sort=False)
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_csv, index=False)
    log.info('Combined %s files into %s patients and %s columns: %s',
             len(files), len(combined), combined.shape[1], output_csv)
    return combined


def select_model_data(combined):
    """Keep the model variables and the outcome, drop unusable patients.

    Patients without a positive follow-up time or without a known event are
    dropped. A feature that no study has is left out.
    """
    wanted = (NUMERIC_FEATURES + POOLED_CATEGORICAL_FEATURES
              + STUDY_CATEGORICAL_FEATURES)
    present = [c for c in wanted if c in combined.columns]
    ids = [c for c in ID_COLUMNS if c in combined.columns]
    data = combined[ids + present + [TIME_COLUMN, EVENT_COLUMN]].copy()
    for column in NON_NEGATIVE_FEATURES:
        data.loc[data[column] < 0, column] = np.nan
    usable = (data[TIME_COLUMN] > 0) & data[EVENT_COLUMN].isin([0, 1])
    log.info('Dropped %s of %s patients without a usable time or event',
             (~usable).sum(), len(data))
    return data[usable].reset_index(drop=True)


def split_train_val_test(data, val_fraction=0.15, test_fraction=0.15,
                         seed=42):
    """Split the patients at random, balanced by study and event.

    Each study and event group is divided in the same proportions, so every
    set has the studies and the event rate of the whole data.
    """
    rng = np.random.default_rng(seed)
    group = data[STUDY_COLUMN].astype(str) + '_' + data[EVENT_COLUMN].astype(
        int).astype(str)
    train_idx, val_idx, test_idx = [], [], []
    for _, members in data.groupby(group).groups.items():
        members = np.array(members)
        rng.shuffle(members)
        n_val = int(round(len(members) * val_fraction))
        n_test = int(round(len(members) * test_fraction))
        val_idx.extend(members[:n_val])
        test_idx.extend(members[n_val:n_val + n_test])
        train_idx.extend(members[n_val + n_test:])
    return (data.loc[sorted(train_idx)].reset_index(drop=True),
            data.loc[sorted(val_idx)].reset_index(drop=True),
            data.loc[sorted(test_idx)].reset_index(drop=True))


def _level_labels(data, column, per_study):
    """Return the level of every patient as text, study first if needed."""
    codes = data[column].map(
        lambda v: MISSING_LEVEL if pd.isna(v) else format(v, 'g'))
    if per_study:
        return data[STUDY_COLUMN].astype(str) + '_' + codes
    return codes


def fit_preprocessor(train, min_level_count=20):
    """Learn the encoding settings from the train set only."""
    numeric = {}
    for column in [c for c in NUMERIC_FEATURES if c in train.columns]:
        values = train[column].dropna()
        if values.empty:
            continue
        numeric[column] = {
            'median': float(values.median()),
            'mean': float(values.mean()),
            'std': float(values.std()) or 1.0,
            'add_missing_flag': bool(train[column].isna().any()),
        }
    categorical = {}
    for per_study, columns in ((False, POOLED_CATEGORICAL_FEATURES),
                               (True, STUDY_CATEGORICAL_FEATURES)):
        for column in [c for c in columns if c in train.columns]:
            if train[column].isna().all():
                continue
            labels = _level_labels(train, column, per_study)
            counts = labels.value_counts()
            categorical[column] = {
                'per_study': per_study,
                'levels': sorted(counts[counts >= min_level_count].index),
            }
    return {'numeric': numeric, 'categorical': categorical}


def transform(data, preprocessor):
    """Encode a set with the settings of the train set.

    Numbers are filled with the train median and standardized, with a flag
    column where the train set has gaps. Categories become 0/1 columns.
    A level that is rare or unseen in the train set becomes <study>_other.
    Returns the table with the feature columns, time and event.
    """
    parts = {}
    for column, p in preprocessor['numeric'].items():
        values = data[column]
        if p['add_missing_flag']:
            parts[column + '_missing'] = values.isna().astype(float)
        filled = values.fillna(p['median'])
        parts[column] = (filled - p['mean']) / p['std']
    for column, p in preprocessor['categorical'].items():
        labels = _level_labels(data, column, p['per_study'])
        known = set(p['levels'])
        fallback = (data[STUDY_COLUMN].astype(str) + '_' + RARE_LEVEL
                    if p['per_study'] else RARE_LEVEL)
        labels = labels.where(labels.isin(known), fallback)
        wanted = list(p['levels'])
        for level in sorted(set(labels) - known):
            wanted.append(level)
        for level in wanted:
            parts['%s=%s' % (column, level)] = (labels == level).astype(
                float)
    features = pd.DataFrame(parts, index=data.index)
    features['time'] = data[TIME_COLUMN].astype(float)
    features['event'] = data[EVENT_COLUMN].astype(int)
    return features


def prepare_survival_data(combined, output_folder, val_fraction=0.15,
                          test_fraction=0.15, seed=42, min_level_count=20):
    """Select, split and encode the data, and write the three sets.

    Writes train.csv, validation.csv and test.csv with the same feature
    columns, train_ids.csv, validation_ids.csv and test_ids.csv with the
    study and patient id of each row, plus preprocessor.json with the settings and the column list.
    Columns that exist only in other sets are zero. Returns the three sets.
    """
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    data = select_model_data(combined)
    train, val, test = split_train_val_test(
        data, val_fraction, test_fraction, seed)
    preprocessor = fit_preprocessor(train, min_level_count)
    parts = {'train': train, 'validation': val, 'test': test}
    encoded = {name: transform(part, preprocessor)
               for name, part in parts.items()}
    # Same columns in the same order in every set. Columns that only occur
    # as an "other" level in a later set are kept, with zeros elsewhere.
    columns = sorted(set().union(*[set(e.columns) for e in encoded.values()])
                     - {'time', 'event'})
    columns = _order_columns(columns, encoded['train'])
    for name, table in encoded.items():
        table = table.reindex(columns=columns + ['time', 'event'],
                              fill_value=0.0)
        table.to_csv(output_folder / (name + '.csv'), index=False)
        # Same row order as the set file, so predictions can be matched.
        ids = [c for c in ID_COLUMNS if c in parts[name].columns]
        parts[name][ids].to_csv(
            output_folder / (name + '_ids.csv'), index=False)
        encoded[name] = table
        log.info('%s: %s patients, event rate %.3f, %s features', name,
                 len(table), table['event'].mean(), len(columns))
    preprocessor['feature_columns'] = columns
    preprocessor['outcome'] = {'time': TIME_COLUMN, 'event': EVENT_COLUMN}
    preprocessor['seed'] = seed
    with open(output_folder / 'preprocessor.json', 'w') as handle:
        json.dump(preprocessor, handle, indent=2)
    return encoded['train'], encoded['validation'], encoded['test']


def _order_columns(columns, train_table):
    """Order columns as in the train table, extra columns at the end."""
    first = [c for c in train_table.columns if c in columns]
    return first + [c for c in columns if c not in first]
