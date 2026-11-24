"""Nodestream steps. The SAS read itself is nodestream_plugin_sas."""
import csv
import logging
import random

from nodestream.pipeline import Extractor, Transformer
from nodestream_plugin_sas import Sas7bdatExtractor

from cibmtr.ontology import load_ontology, normalize_record, paths_from_here

logger = logging.getLogger(__name__)


def reservoir_update(chosen, seen, record, max_rows, rng):
    """Consider one record in a reservoir of max_rows. `seen` is 1-based."""
    if len(chosen) < max_rows:
        chosen.append(record)
        return
    j = rng.randrange(seen)
    if j < max_rows:
        chosen[j] = record


def sample_records(records, max_rows, seed):
    """Reservoir sample. Files no larger than max_rows are returned whole.

    The seed is the study id, so a rerun keeps the same patients. max_rows of
    None, or a number below 1, keeps every row.
    """
    if not max_rows or max_rows < 1:
        return list(records)
    rng = random.Random(seed)
    chosen = []
    for seen, record in enumerate(records, start=1):
        reservoir_update(chosen, seen, record, max_rows, rng)
    return chosen


class StudySasExtractor(Extractor):
    """Read every extracted sas7bdat and stamp the study id the plugin does not provide.

    `globs` on Sas7bdatExtractor cannot tell a row of P-5370 from a row of P-5702.
    One extractor instance per file keeps that stamp accurate. `study_ids` limits
    the run to those directories; omit it to read every study. `max_rows` keeps a
    stable random sample of that many rows from each file.
    """

    def __init__(self, datasets_root, study_ids=None, chunksize=10000, max_rows=None):
        self.datasets_root = datasets_root
        self.study_ids = set(study_ids) if study_ids else None
        self.chunksize = chunksize
        self.max_rows = max_rows

    async def extract_records(self):
        from pathlib import Path

        root = Path(self.datasets_root)
        studies = sorted(
            path for path in root.iterdir() if path.is_dir() and path.name.startswith("P-")
        )
        for study_dir in studies:
            if self.study_ids is not None and study_dir.name not in self.study_ids:
                continue
            files = sorted(
                {
                    *study_dir.rglob("*.sas7bdat"),
                    *study_dir.rglob("*.SAS7BDAT"),
                }
            )
            for path in files:
                extractor = Sas7bdatExtractor(globs=[str(path)], chunksize=self.chunksize)
                chosen = []
                row_index = 0
                rng = random.Random(study_dir.name)
                limit = self.max_rows
                async for record in extractor.extract_records():
                    row_index += 1
                    record["__study_id"] = study_dir.name
                    record["__source_file"] = path.name
                    record["__row_index"] = row_index
                    if not limit or limit < 1:
                        yield record
                        continue
                    reservoir_update(chosen, row_index, record, limit, rng)
                if limit and limit >= 1:
                    logger.info(
                        "%s %s kept %s of %s rows",
                        study_dir.name,
                        path.name,
                        len(chosen),
                        row_index,
                    )
                    for record in chosen:
                        yield record


class CsvExtractor(Extractor):
    def __init__(self, path):
        self.path = path

    async def extract_records(self):
        with open(self.path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                yield row


class NormalizeToOntology(Transformer):
    def __init__(self, mapping_path=None, ontology_path=None, catalog_path=None):
        default_mapping, default_ontology, default_catalog = paths_from_here()
        self.ontology = load_ontology(
            mapping_path or default_mapping,
            ontology_path or default_ontology,
            catalog_path or default_catalog,
        )

    async def transform_record(self, record):
        return normalize_record(record, self.ontology)
