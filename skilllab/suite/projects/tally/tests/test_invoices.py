import unittest
import warnings
from decimal import Decimal

from tally.invoices import build_invoice, render_text

from helpers import catalog, customers, order


class InvoiceTest(unittest.TestCase):
    def setUp(self):
        self.cat, self.cust = catalog(), customers()

    def test_simple_line(self):
        inv = build_invoice(order("O1", "C1", "2026-03-01T10:00:00Z", ("HW-1", 2, "14.99")), self.cat, self.cust)
        self.assertEqual(inv.net.amount, Decimal("29.98"))
        self.assertEqual(inv.tax.amount, Decimal("5.70"))
        self.assertEqual(inv.total.amount, Decimal("35.68"))

    def test_reduced_rate_and_zero_rated(self):
        o = order("O2", "C1", "2026-03-01T10:00:00Z", ("BK-1", 1, "18.50"), ("GC-1", 1, "25.00"))
        inv = build_invoice(o, self.cat, self.cust)
        self.assertEqual([l.tax.amount for l in inv.lines], [Decimal("1.30"), Decimal("0.00")])

    def test_tier_discount(self):
        inv = build_invoice(order("O3", "C3", "2026-03-01T10:00:00Z", ("HW-2", 3, "23.33")), self.cat, self.cust)
        line = inv.lines[0]
        self.assertEqual(line.net.amount, Decimal("69.99"))
        self.assertEqual(line.discount.amount, Decimal("7.00"))
        self.assertEqual(line.tax.amount, Decimal("12.60"))

    def test_lines_add_up_to_total(self):
        o = order("O4", "C2", "2026-03-01T10:00:00Z", ("HW-1", 3, "14.99"), ("HW-2", 7, "23.33"), ("BK-1", 2, "18.50"))
        inv = build_invoice(o, self.cat, self.cust)
        self.assertEqual(sum(l.gross.amount for l in inv.lines), inv.total.amount)

    def test_cancelled_order(self):
        o = order("O5", "C1", "2026-03-01T10:00:00Z", ("HW-1", 1, "14.99"), status="cancelled")
        with self.assertRaises(ValueError):
            build_invoice(o, self.cat, self.cust)

    def test_render(self):
        inv = build_invoice(order("O6", "C4", "2026-03-01T10:00:00Z", ("HW-1", 1, "14.99")), self.cat, self.cust)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            text = render_text(inv)
        self.assertIn("Invoice for order O6", text)
        self.assertIn("Total:     €14.99", text)


if __name__ == "__main__":
    unittest.main()
