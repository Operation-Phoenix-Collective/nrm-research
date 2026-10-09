"""
Role: Runner for the conversion of SAS files to CSV.
Description: Sets the folders, extracts the six study zips in
data/starting_point, then converts their SAS files with
nrm_research.sas_convert. The CSV files are written to
results/processed/sas_files, for example p_5329.csv.
Author: Bor
"""
import configparser
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nrm_research import sas_convert  # noqa: E402

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
DATA_RAW = os.path.join(BASE_PATH, '..', 'data')

DATA_PROCESSED = os.path.join(BASE_PATH, '..', 'results', 'processed')

DATA_STARTING = os.path.join(DATA_RAW, 'starting_point')
DATA_STARTING_EXTRACTED = os.path.join(DATA_RAW, 'starting_point_extracted')
DATA_SAS_CSV = os.path.join(DATA_PROCESSED, 'sas_files')

ENCODING = 'latin-1'


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    empty_zips = sas_convert.extract_study_zips(
        Path(DATA_STARTING).resolve(),
        Path(DATA_STARTING_EXTRACTED).resolve())
    failed_files = sas_convert.convert_project_folders(
        Path(DATA_STARTING_EXTRACTED).resolve(),
        Path(DATA_SAS_CSV).resolve(), ENCODING)
    if empty_zips or failed_files:
        print('%s zip(s) without SAS file, %s file(s) failed, see the log.'
              % (len(empty_zips), len(failed_files)))
        sys.exit(1)
    print('All files converted.')
