"""Nodestream steps. The SAS read itself is nodestream_plugin_sas."""
import csv

from nodestream.pipeline import Extractor, Transformer
from nodestream_plugin_sas import Sas7bdatExtractor

from cibmtr.ontology import load_ontology, normalize_record, paths_from_here


class StudySasExtractor(Extractor):
    """Read every extracted sas7bdat and stamp the study id the plugin does not provide.

    `globs` on Sas7bdatExtractor cannot tell a row of P-5370 from a row of P-5702.
    One extractor instance per file keeps that stamp accurate. `study_ids` limits
    the run to those directories; omit it to read every study.
    """

    def __init__(self, datasets_root, study_ids=None, chunksize=10000):
        self.datasets_root = datasets_root
        self.study_ids = set(study_ids) if study_ids else None
        self.chunksize = chunksize

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
                row_index = 0
                async for record in extractor.extract_records():
                    row_index += 1
                    record["__study_id"] = study_dir.name
                    record["__source_file"] = path.name
                    record["__row_index"] = row_index
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
