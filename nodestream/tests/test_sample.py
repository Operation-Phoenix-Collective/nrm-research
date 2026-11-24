import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cibmtr.steps import sample_records


class SampleRecordsTest(unittest.TestCase):
    def test_short_file_is_kept_whole(self):
        rows = [{"i": i} for i in range(40)]
        self.assertEqual(sample_records(rows, 500, "P-5056"), rows)

    def test_sample_is_stable_and_bounded(self):
        rows = [{"i": i} for i in range(5000)]
        first = sample_records(rows, 500, "P-6210")
        second = sample_records(rows, 500, "P-6210")
        self.assertEqual(first, second)
        self.assertEqual(len(first), 500)
        self.assertEqual(len({row["i"] for row in first}), 500)

    def test_unset_cap_keeps_every_row(self):
        rows = [{"i": i} for i in range(30)]
        self.assertEqual(sample_records(rows, None, "P-5051"), rows)


if __name__ == "__main__":
    unittest.main()
