"""
Role: Runner that builds the train, validation and test data for DeepSurv.
Description: Combines the normalized study CSV files from
results/processed/sas_files_normalized into one file, then prepares and
splits it with nrm_research.survival_data. Writes combined_normalized.csv to
results/processed/combined and train.csv, validation.csv, test.csv and
preprocessor.json to results/processed/survival_model_data.
Author: Bor
"""
import configparser
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nrm_research import survival_data  # noqa: E402

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
DATA_PROCESSED = os.path.join(BASE_PATH, '..', 'results', 'processed')

DATA_NORMALIZED = os.path.join(DATA_PROCESSED, 'sas_files_normalized')
COMBINED_CSV = os.path.join(
    DATA_PROCESSED, 'combined', 'combined_normalized.csv')
MODEL_DATA = os.path.join(DATA_PROCESSED, 'survival_model_data')

VAL_FRACTION = 0.15
TEST_FRACTION = 0.15
SEED = 42
MIN_LEVEL_COUNT = 20


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    combined = survival_data.combine_study_csvs(
        Path(DATA_NORMALIZED).resolve(), Path(COMBINED_CSV).resolve())
    train, val, test = survival_data.prepare_survival_data(
        combined, Path(MODEL_DATA).resolve(), VAL_FRACTION, TEST_FRACTION,
        SEED, MIN_LEVEL_COUNT)
    print('Train %s, validation %s, test %s patients, %s features.'
          % (len(train), len(val), len(test), train.shape[1] - 2))
