import io
import json
import sys
import unittest
import warnings
from contextlib import redirect_stdout
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, ".")
warnings.simplefilter("ignore", DeprecationWarning)
from tally.catalog import Catalog  # noqa: E402
from tally.customers import CustomerBook  # noqa: E402
from tally.orders import OrderBook  # noqa: E402
from tally.reports import customer_summary, daily_sales, revenue_by_country  # noqa: E402

DATA = Path("data")
CAT, CUST, ORD = Catalog.load(DATA / "catalog.json"), CustomerBook.load(DATA / "customers.json"), OrderBook.load(DATA / "orders.json")


def cli(*argv):
    from tally.cli import main
    out = io.StringIO()
    with redirect_stdout(out):
        code = main(["--data", str(DATA), *argv])
    return code, out.getvalue()


def q(m):
    return str(m.quantize().amount)


def no_floats(obj, test):
    if isinstance(obj, float):
        test.fail(f"float in JSON: {obj!r}")
    if isinstance(obj, dict):
        for v in obj.values():
            no_floats(v, test)
    if isinstance(obj, list):
        for v in obj:
            no_floats(v, test)


class JsonReportTest(unittest.TestCase):
    def test_daily(self):
        code, out = cli("report", "daily", "--tz", "+05:30", "--format", "json")
        self.assertEqual(code, 0)
        self.assertTrue(out.endswith("}\n"))
        doc = json.loads(out)
        no_floats(doc, self)
        sales = daily_sales(ORD, CAT, CUST, "+05:30")
        self.assertEqual({k: doc[k] for k in ("report", "currency", "tz")}, {"report": "daily", "currency": "EUR", "tz": "+05:30"})
        self.assertEqual(doc["days"], [{"date": d, "total": q(m)} for d, m in sales.items()])
        grand = sum((m.amount for m in sales.values()), Decimal(0)).quantize(Decimal("0.01"))
        self.assertEqual(doc["total"], str(grand))
        self.assertEqual(out, json.dumps(doc, indent=2, ensure_ascii=False) + "\n")

    def test_countries(self):
        doc = json.loads(cli("report", "countries", "--format", "json")[1])
        rev = revenue_by_country(ORD, CAT, CUST)
        self.assertEqual(doc, {"report": "countries", "currency": "EUR",
                               "countries": [{"country": c, "total": q(m)} for c, m in rev.items()]})

    def test_customers(self):
        doc = json.loads(cli("report", "customers", "--format", "json")[1])
        rows = customer_summary(ORD, CAT, CUST)
        want = [{"id": r["customer_id"], "name": CUST.get(r["customer_id"]).name, "orders": r["orders"],
                 "units": r["units"], "spend": q(r["spend"]), "currency": "EUR"} for r in rows]
        self.assertEqual(doc, {"report": "customers", "customers": want})
        self.assertTrue(all(len(c["spend"].split(".")[1]) == 2 for c in doc["customers"]))

    def test_amounts_keep_trailing_zeros(self):
        doc = json.loads(cli("report", "countries", "--format", "json")[1])
        for c in doc["countries"]:
            self.assertRegex(c["total"], r"^-?\d+\.\d\d$")

    def test_text_unchanged_and_customers_text(self):
        from tally.reports import render_countries, render_daily
        self.assertEqual(cli("report", "daily")[1], render_daily(daily_sales(ORD, CAT, CUST)))
        self.assertEqual(cli("report", "countries", "--format", "text")[1], render_countries(revenue_by_country(ORD, CAT, CUST)))
        lines = cli("report", "customers")[1].splitlines()
        first = customer_summary(ORD, CAT, CUST)[0]
        self.assertTrue(lines[0].startswith(f"{first['customer_id']}  {CUST.get(first['customer_id']).name}  {first['orders']}  {first['units']}  €"))
        self.assertEqual(len(lines), len(customer_summary(ORD, CAT, CUST)))


if __name__ == "__main__":
    unittest.main()
