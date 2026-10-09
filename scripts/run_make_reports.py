"""
Role: Runner that writes the workflow reports as PDF files.
Description: Writes the overall survival workflow report to the docs folder.
Author: Bor
"""
import configparser
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nrm_research import report_pdf, report_text  # noqa: E402

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
DOCS = os.path.join(BASE_PATH, '..', 'docs')

REPORT_SURVIVAL = os.path.join(DOCS, 'os_workflow_starting_point.pdf')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    report_pdf.write_report(
        Path(REPORT_SURVIVAL).resolve(), *report_text.OVERALL_SURVIVAL)
    print('Report written to %s' % Path(DOCS).resolve())
