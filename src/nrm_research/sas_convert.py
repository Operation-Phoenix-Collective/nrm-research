"""
Role: Extract CIBMTR study zips and convert their SAS files to CSV.
Description: Extracts the .sas7bdat file of each study zip into a folder named
after the zip. Walks the subfolders of a root folder, finds every .sas7bdat
file in each, and writes a CSV to the output folder. The CSV takes the name
of the project folder, for example p_5411.csv. A folder with more than one
SAS file appends the stem of the source file so no output is overwritten.
Author: Osoro
"""
import logging
import zipfile
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

SAS_SUFFIX = '.sas7bdat'


def extract_study_zips(zip_dir: Path, extract_dir: Path) -> list[Path]:
    """Extract the .sas7bdat members of every zip in zip_dir.

    Each zip is extracted to extract_dir/<zip name>. Members are written by
    file name only, so a path inside the archive cannot leave that folder.

    Returns the zips that held no .sas7bdat file. Raises FileNotFoundError
    when zip_dir does not exist.
    """
    if not zip_dir.is_dir():
        raise FileNotFoundError('Zip folder not found: %s' % zip_dir)

    empty = []
    for zip_path in sorted(zip_dir.glob('*.zip')):
        target = extract_dir / zip_path.stem
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as archive:
            members = [
                m for m in archive.infolist()
                if m.filename.lower().endswith(SAS_SUFFIX)
            ]
            if not members:
                log.warning('No %s file in %s', SAS_SUFFIX, zip_path)
                empty.append(zip_path)
                continue
            for member in members:
                out_path = target / Path(member.filename).name
                out_path.write_bytes(archive.read(member))
                log.info('Extracted %s to %s', member.filename, out_path)
    return empty


def _find_sas_files(project_dir: Path) -> list[Path]:
    return sorted(
        path for path in project_dir.rglob('*')
        if path.is_file() and path.suffix.lower() == SAS_SUFFIX
    )


def _csv_name(sas_file: Path, project_dir: Path, n_files: int) -> str:
    project = project_dir.name.lower().replace('-', '_')
    if n_files == 1:
        name = project
    else:
        name = '%s_%s' % (project, sas_file.stem)
    return name + '.csv'


def convert_project_folders(
        root: Path, out_dir: Path, encoding: str) -> list[Path]:
    """Convert all SAS files under each subfolder of root.

    CSV files are written to out_dir, which is created when absent.

    Returns the SAS files that failed to convert. An empty list means every
    file was converted. Raises FileNotFoundError when root does not exist.
    """
    if not root.is_dir():
        raise FileNotFoundError('Root folder not found: %s' % root)

    out_dir.mkdir(parents=True, exist_ok=True)
    failed = []
    for project_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        sas_files = _find_sas_files(project_dir)
        if not sas_files:
            log.warning('No %s files in %s', SAS_SUFFIX, project_dir)
            continue

        for sas_file in sas_files:
            out_path = out_dir / _csv_name(
                sas_file, project_dir, len(sas_files))
            try:
                frame = pd.read_sas(
                    sas_file, format='sas7bdat', encoding=encoding)
            except (ValueError, OSError) as error:
                log.error('Failed to read %s: %s', sas_file, error)
                failed.append(sas_file)
                continue
            frame.to_csv(out_path, index=False)
            log.info(
                '%s -> %s (%s rows, %s columns)',
                sas_file.name, out_path, len(frame), len(frame.columns))
    return failed
