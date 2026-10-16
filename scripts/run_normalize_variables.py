"""
Role: Runner that gives the six study CSV files one set of column names.
Description: Builds the map of column names from the dictionaries, writes the
map and the coverage matrix, then writes each CSV with common names to
results/processed/sas_files_normalized.
Author: Bor
"""
import configparser
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nrm_research import variable_map  # noqa: E402

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
DATA_RAW = os.path.join(BASE_PATH, '..', 'data')
DATA_PROCESSED = os.path.join(BASE_PATH, '..', 'results', 'processed')

DATA_SAS_CSV = os.path.join(DATA_PROCESSED, 'sas_files')
DATA_NORMALIZED = os.path.join(DATA_PROCESSED, 'sas_files_normalized')

VARIABLES_CSV = os.path.join(DATA_RAW, 'variables_by_study.csv')
MAP_CSV = os.path.join(DATA_PROCESSED, 'variable_name_map.csv')
MATRIX_CSV = os.path.join(DATA_PROCESSED, 'variable_name_matrix.csv')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    name_map = variable_map.build_variable_map(
        Path(DATA_SAS_CSV).resolve(), Path(VARIABLES_CSV).resolve())
    name_map.to_csv(Path(MAP_CSV).resolve(), index=False)
    matrix = variable_map.build_variable_matrix(name_map)
    matrix.to_csv(Path(MATRIX_CSV).resolve())
    variable_map.normalize_study_csvs(
        name_map, Path(DATA_SAS_CSV).resolve(),
        Path(DATA_NORMALIZED).resolve())
    unmapped = name_map[name_map.status == 'unmapped']
    print('%s columns mapped, %s unmapped.'
          % ((name_map.status == 'mapped').sum(), len(unmapped)))
    if len(unmapped):
        print(unmapped[['study_id', 'original_name']].to_string(index=False))
