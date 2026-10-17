import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, ".")
from tally.catalog import Catalog  # noqa: E402
from tally.customers import CustomerBook  # noqa: E402
from tally.orders import OrderBook  # noqa: E402

DATA = Path("data")
HEADER = "order_id,customer_id,created_at,sku,qty,unit_price,coupon\n"


def load():
    return Catalog.load(DATA / "catalog.json"), CustomerBook.load(DATA / "customers.json"), OrderBook.load(DATA / "orders.json")


class ImportTest(unittest.TestCase):
    def setUp(self):
        from tally.importers import import_orders
        self.import_orders = import_orders
        self.cat, self.cust, self.book = load()
        self.tmp = Path(tempfile.mkdtemp())

    def run_csv(self, text, encoding="utf-8"):
        p = self.tmp / "in.csv"
        p.write_bytes(text.encode(encoding))
        return self.import_orders(p, self.cat, self.cust, self.book)

    def test_sample_file(self):
        r = self.import_orders(Path("samples/marketplace-2026-03-14.csv"), self.cat, self.cust, self.book)
        self.assertEqual(r.errors, [])
        self.assertEqual([o.id for o in r.orders], ["M-1001", "M-1002", "M-1003"])
        m1, m2, m3 = r.orders
        self.assertEqual([(l.sku, l.qty, str(l.unit_price.amount)) for l in m1.lines],
                         [("HW-3001", 2, "14.99"), ("CF-2001", 4, "9.75")])
        self.assertEqual(m2.coupon, "WELCOME10")
        self.assertIn(m1.coupon, (None, ""))
        self.assertEqual(m3.created_at, "2026-03-14T10:05:00Z")
        self.assertEqual({o.status for o in r.orders}, {"open"})
        self.assertEqual(m1.lines[0].unit_price.currency, "EUR")

    def test_bom_header_order_case_spaces_extra_column(self):
        text = " SKU ,Order_ID,qty, Unit_Price ,customer_id,notes,created_at\nHW-3001,X1,3,14.99,C0003,hi,2026-03-14T09:00:00Z\n"
        r = self.run_csv("﻿" + text)
        self.assertEqual(r.errors, [])
        self.assertEqual([(o.id, o.lines[0].sku, o.lines[0].qty) for o in r.orders], [("X1", "HW-3001", 3)])

    def test_blank_lines_count_for_line_numbers(self):
        text = "\n" + HEADER + "X1,C0003,2026-03-14T09:00:00Z,HW-3001,1,14.99,\n\n , ,\nX2,C9999,2026-03-14T09:00:00Z,HW-3001,1,14.99,\n"
        r = self.run_csv(text)
        self.assertEqual(r.errors, ["line 6: unknown customer C9999"])
        self.assertEqual([o.id for o in r.orders], ["X1"])

    def test_missing_column(self):
        r = self.run_csv("order_id,customer_id,created_at,sku,unit_price\nX1,C0003,2026-03-14T09:00:00Z,HW-3001,1\n")
        self.assertEqual(r.errors, ["header: missing column qty"])
        self.assertEqual(r.orders, [])

    def test_several_problems_in_one_row_in_table_order(self):
        r = self.run_csv(HEADER + "X1,C9999,2026-03-14 10:00,XX-1,0,1.999,FREE\n")
        self.assertEqual(r.errors, ["line 2: unknown customer C9999", "line 2: unknown sku XX-1", "line 2: bad qty '0'",
                                    "line 2: bad unit_price '1.999'", "line 2: bad created_at '2026-03-14 10:00'",
                                    "line 2: unknown coupon FREE"])

    def test_values(self):
        rows = ["X1,C0003,2026-03-14T09:00:00Z,HW-3001,2.5,1,", "X2,C0003,2026-03-14T09:00:00Z,HW-3001,abc,1,",
                "X3,C0003,2026-03-14T09:00:00Z,HW-3001,1,-1,", "X4,C0003,2026-03-14T09:00:00Z,HW-3001,1,abc,",
                "X5,C0003,2026-03-14T09:00:00Z,HW-3001, 3 , 0.5 , welcome10 ",
                "X6,C0003,2026-03-14T09:00:00,HW-3001,1,1,"]
        r = self.run_csv(HEADER + "\n".join(rows) + "\n")
        self.assertEqual(r.errors, ["line 2: bad qty '2.5'", "line 3: bad qty 'abc'", "line 4: bad unit_price '-1'",
                                    "line 5: bad unit_price 'abc'", "line 7: bad created_at '2026-03-14T09:00:00'"])
        self.assertEqual([o.id for o in r.orders], ["X5"])
        self.assertEqual((r.orders[0].lines[0].qty, str(r.orders[0].lines[0].unit_price.amount)), (3, "0.5"))

    def test_grouping_and_conflicts(self):
        rows = ["A,C0003,2026-03-14T09:00:00Z,HW-3001,1,14.99,", "B,C0004,2026-03-14T09:00:00Z,HW-3002,1,54.00,",
                "A,C0003,2026-03-14T09:00:00Z,CF-2001,2,9.75,", "B,C0005,2026-03-14T09:00:00Z,CF-2001,1,9.75,",
                "C,C0003,2026-03-14T09:00:00Z,HW-3001,1,14.99,SPRING15", "C,C0003,2026-03-14T09:00:00Z,HW-3002,1,54.00,"]
        r = self.run_csv(HEADER + "\n".join(rows) + "\n")
        self.assertEqual(r.errors, ["line 5: order B has conflicting customer_id", "line 7: order C has conflicting coupon"])
        self.assertEqual([(o.id, len(o.lines)) for o in r.orders], [("A", 2)])

    def test_existing_order_and_no_side_effects(self):
        before = len(self.book)
        r = self.run_csv(HEADER + "O00001,C0003,2026-03-14T09:00:00Z,HW-3001,1,14.99,\n")
        self.assertEqual(r.errors, ["line 2: order O00001 already exists"])
        self.assertEqual(len(self.book), before)


class CliImportTest(unittest.TestCase):
    def run_cli(self, *argv):
        from tally.cli import main
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        shutil.copytree(DATA, self.tmp / "data")
        self.csv = self.tmp / "in.csv"
        self.csv.write_text(HEADER + "X1,C0003,2026-03-14T09:00:00Z,HW-3001,1,14.99,\nX2,C9999,2026-03-14T09:00:00Z,HW-3001,1,14.99,\n")

    def orders_on_disk(self):
        return json.loads((self.tmp / "data" / "orders.json").read_text())["orders"]

    def test_dry_run(self):
        before = self.orders_on_disk()
        code, out, err = self.run_cli("--data", str(self.tmp / "data"), "import", "orders", str(self.csv), "--dry-run")
        self.assertEqual((code, out.strip(), err.strip()), (1, "imported 1 orders", "line 3: unknown customer C9999"))
        self.assertEqual(self.orders_on_disk(), before)

    def test_import_saves_valid_orders(self):
        n = len(self.orders_on_disk())
        code, out, err = self.run_cli("--data", str(self.tmp / "data"), "import", "orders", str(self.csv))
        self.assertEqual(code, 1)
        self.assertEqual(len(self.orders_on_disk()), n + 1)
        self.assertEqual(OrderBook.load(self.tmp / "data" / "orders.json").get("X1").status, "open")

    def test_clean_file_exits_zero(self):
        self.csv.write_text(HEADER + "X1,C0003,2026-03-14T09:00:00Z,HW-3001,1,14.99,\n")
        self.assertEqual(self.run_cli("--data", str(self.tmp / "data"), "import", "orders", str(self.csv))[:2],
                         (0, "imported 1 orders\n"))


if __name__ == "__main__":
    unittest.main()
