"""
Role: Runner that trains all models and stores their results.
Description: Trains DeepSurv, the Faraggi-Simon network, the Cox
proportional hazards model, logistic regression, an SVM and a random forest
with nrm_research.model_comparison on the sets written by
run_prepare_survival_data.py. Writes predictions.csv, metrics.csv,
history.csv and models.json to results/models, each table with a column
model. Run run_prepare_survival_data.py first.
Author: Bor
"""
import configparser
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nrm_research import model_comparison  # noqa: E402

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
DATA_PROCESSED = os.path.join(BASE_PATH, '..', 'results', 'processed')

MODEL_DATA = os.path.join(DATA_PROCESSED, 'survival_model_data')
OUTPUT = os.path.join(BASE_PATH, '..', 'results', 'models')

# Death within this many months is the yes/no outcome of the classifiers.
HORIZON_MONTHS = 12
N_RISK_GROUPS = 4
# None runs every model. Or a list of names from MODEL_REGISTRY, for example
# ['DeepSurv', 'Cox PH'].
MODEL_NAMES = None
# Changed settings: {'DeepSurv': {'hidden_layers': [128, 64]}}.
OVERRIDES = {}


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    metrics = model_comparison.run_models(
        Path(MODEL_DATA).resolve(), Path(OUTPUT).resolve(), HORIZON_MONTHS,
        N_RISK_GROUPS, MODEL_NAMES, OVERRIDES)
    table = metrics.pivot(index='model', columns='set', values='c_index')
    print(table[['train', 'validation', 'test']].round(3).to_string())
