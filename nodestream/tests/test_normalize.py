import csv
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cibmtr.ontology import load_ontology, normalize_record


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fields)
        writer.writeheader()
        writer.writerows(rows)


class NormalizeTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        root = self.dir.name
        write_csv(
            os.path.join(root, "ontology.csv"),
            [
                {"field_id": "overall_survival.event", "stack": "recode"},
                {"field_id": "overall_survival.time", "stack": "recode"},
                {"field_id": "recipient_age.measure", "stack": "recode"},
                {"field_id": "recipient_sex.category", "stack": "crosswalk"},
                {"field_id": "patient_id.identifier", "stack": "do_not_stack"},
            ],
            ["field_id", "stack"],
        )
        write_csv(
            os.path.join(root, "mapping.csv"),
            [
                self.row("dead", "overall_survival.event", "overall_survival", "event", "", "0=Censoring; 1=Event; 99=Missing"),
                self.row("intxsurv", "overall_survival.time", "overall_survival", "time", "days", ""),
                self.row("age", "recipient_age.measure", "recipient_age", "measure", "", ""),
                self.row("sex", "recipient_sex.category", "recipient_sex", "category", "", "1=Male; 2=Female"),
                self.row("pseudoid", "patient_id.identifier", "patient_id", "identifier", "", ""),
            ],
            ["study_id", "source_variable", "field_id", "concept", "role", "time_unit", "codes"],
        )
        write_csv(
            os.path.join(root, "catalog.csv"),
            [{"study_id": "P-1", "title": "Example", "first_author": "A", "start_year": "2001"}],
            ["study_id", "title", "first_author", "start_year"],
        )
        self.ontology = load_ontology(
            os.path.join(root, "mapping.csv"),
            os.path.join(root, "ontology.csv"),
            os.path.join(root, "catalog.csv"),
        )

    def tearDown(self):
        self.dir.cleanup()

    def row(self, variable, field_id, concept, role, unit, codes):
        return {
            "study_id": "P-1",
            "source_variable": variable,
            "field_id": field_id,
            "concept": concept,
            "role": role,
            "time_unit": unit,
            "codes": codes,
        }

    def test_recodes_event_converts_days_and_keeps_sex_label(self):
        out = normalize_record(
            {
                "__study_id": "P-1",
                "__source_file": "a.sas7bdat",
                "__row_index": 3,
                "PSEUDOID": 15.0,
                "dead": 1.0,
                "intxsurv": 60.0,
                "Age": 40.0,
                "sex": 2.0,
            },
            self.ontology,
        )
        self.assertEqual(out["patient_id"], "15")
        self.assertEqual(out["id_source"], "patient_id")
        by_field = {item["field_id"]: item for item in out["values"]}
        self.assertEqual(by_field["overall_survival.event"]["value_num"], 1)
        self.assertAlmostEqual(by_field["overall_survival.time"]["value_num"], 60 / 30.4375)
        self.assertEqual(by_field["overall_survival.time"]["unit"], "months")
        self.assertEqual(by_field["recipient_sex.category"]["value_text"], "Female")
        self.assertEqual(by_field["recipient_age.measure"]["value_num"], 40.0)

    def test_missing_event_is_dropped_and_row_id_is_used_without_a_pseudonym(self):
        out = normalize_record(
            {
                "__study_id": "P-1",
                "__source_file": "a.sas7bdat",
                "__row_index": 4,
                "dead": 99.0,
            },
            self.ontology,
        )
        self.assertEqual(out["patient_id"], "a.sas7bdat:4")
        self.assertEqual(out["id_source"], "row")
        self.assertEqual(out["values"], [])


if __name__ == "__main__":
    unittest.main()
