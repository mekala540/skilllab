import unittest
from datetime import date
from decimal import Decimal

from tally.reports import customer_summary, daily_sales, revenue_by_country, top_products
from tally.utils.dates import local_date, parse_offset

from helpers import book, catalog, customers, order


class DatesTest(unittest.TestCase):
    def test_local_date(self):
        self.assertEqual(local_date("2026-03-01T23:30:00Z", "+01:00"), date(2026, 3, 2))
        self.assertEqual(local_date("2026-03-01T00:30:00Z", "-05:00"), date(2026, 2, 28))

    def test_bad_offset(self):
        for bad in ("+5:30", "0100", "+15:00"):
            with self.assertRaises(ValueError):
                parse_offset(bad)


class ReportsTest(unittest.TestCase):
    def setUp(self):
        self.cat, self.cust = catalog(), customers()
        self.orders = book(
            order("O1", "C1", "2026-03-01T10:00:00Z", ("HW-1", 2, "14.99")),
            order("O2", "C2", "2026-03-01T23:30:00Z", ("BK-1", 1, "18.50")),
            order("O3", "C4", "2026-03-02T09:00:00Z", ("HW-1", 1, "14.99"), ("HW-2", 5, "23.33")),
            order("O4", "C1", "2026-03-02T12:00:00Z", ("HW-2", 9, "23.33"), status="cancelled"),
        )

    def test_daily_sales_utc(self):
        sales = daily_sales(self.orders, self.cat, self.cust)
        self.assertEqual(list(sales), ["2026-03-01", "2026-03-02"])

    def test_daily_sales_shifted(self):
        sales = daily_sales(self.orders, self.cat, self.cust, "+02:00")
        self.assertEqual(len(sales), 2)
        self.assertEqual(sales["2026-03-02"].quantize().amount, Decimal("150.79"))

    def test_top_products_skips_cancelled(self):
        self.assertEqual(top_products(self.orders), [("HW-2", 5), ("HW-1", 3), ("BK-1", 1)])

    def test_revenue_by_country(self):
        self.assertEqual(list(revenue_by_country(self.orders, self.cat, self.cust)), ["US", "DE", "NL"])

    def test_customer_summary(self):
        rows = customer_summary(self.orders, self.cat, self.cust)
        self.assertEqual([r["customer_id"] for r in rows], ["C4", "C1", "C2"])
        self.assertEqual(rows[1]["orders"], 1)


if __name__ == "__main__":
    unittest.main()
