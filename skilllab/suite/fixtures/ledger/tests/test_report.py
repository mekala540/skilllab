import unittest
from pathlib import Path

from ledger.importer import load_transactions
from ledger.report import monthly_report

DATA = Path(__file__).resolve().parent.parent / "data" / "march.csv"


class TestMarchReport(unittest.TestCase):
    def test_march_totals(self):
        report = monthly_report(load_transactions(DATA), 2024, 3)
        self.assertEqual(report, {"income": "3669.99", "expenses": "1675.82",
                                  "net": "1994.17", "count": 10})


if __name__ == "__main__":
    unittest.main()
