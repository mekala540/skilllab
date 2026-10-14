import csv
import os
import tempfile
import unittest
from datetime import date
from decimal import Decimal

from ledger.dates import month_range
from ledger.importer import load_transactions
from ledger.money import format_amount, parse_amount
from ledger.report import monthly_report


def write_csv(rows):
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "date", "description", "amount"])
        w.writerows(rows)
    return path


class HiddenLedger(unittest.TestCase):
    def test_parse_amount(self):
        self.assertEqual(parse_amount("(45.00)"), Decimal("-45.00"))
        self.assertEqual(parse_amount("($1,234.50)"), Decimal("-1234.50"))
        self.assertEqual(parse_amount("-3.20"), Decimal("-3.20"))
        self.assertEqual(parse_amount("$12.00"), Decimal("12.00"))

    def test_format_rounds_half_up(self):
        self.assertEqual(format_amount(Decimal("2.675")), "2.68")
        self.assertEqual(format_amount(Decimal("1.005")), "1.01")
        self.assertEqual(format_amount(Decimal("-0.125")), "-0.13")
        self.assertEqual(format_amount(Decimal("10")), "10.00")

    def test_month_range(self):
        self.assertEqual(month_range(2024, 3), (date(2024, 3, 1), date(2024, 3, 31)))
        self.assertEqual(month_range(2024, 2), (date(2024, 2, 1), date(2024, 2, 29)))
        self.assertEqual(month_range(2023, 2), (date(2023, 2, 1), date(2023, 2, 28)))
        self.assertEqual(month_range(2024, 4), (date(2024, 4, 1), date(2024, 4, 30)))
        self.assertEqual(month_range(2024, 12), (date(2024, 12, 1), date(2024, 12, 31)))

    def test_dedupe_by_id_only(self):
        path = write_csv([
            ["a1", "2024-02-29", "Coffee", "-4.50"],
            ["a2", "2024-02-29", "Coffee", "-4.50"],
            ["a2", "2024-02-29", "Coffee", "-4.50"],
            ["a3", "2024-02-10", "Pay", "100.00"],
        ])
        try:
            txs = load_transactions(path)
        finally:
            os.unlink(path)
        self.assertEqual([t["id"] for t in txs], ["a1", "a2", "a3"])
        self.assertEqual(monthly_report(txs, 2024, 2),
                         {"income": "100.00", "expenses": "9.00", "net": "91.00", "count": 3})

    def test_half_cent_report(self):
        txs = [{"id": "x", "date": date(2024, 5, 31), "description": "", "amount": Decimal("2.675")}]
        self.assertEqual(monthly_report(txs, 2024, 5)["income"], "2.68")


if __name__ == "__main__":
    unittest.main()
