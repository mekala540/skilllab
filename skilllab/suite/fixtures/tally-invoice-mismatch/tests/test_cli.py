import io
import shutil
import tempfile
import unittest
import warnings
from contextlib import redirect_stdout
from pathlib import Path

from tally.cli import main

DATA = Path(__file__).resolve().parent.parent / "data"


def run(*argv):
    out = io.StringIO()
    with redirect_stdout(out), warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        code = main(["--data", str(DATA), *argv])
    return code, out.getvalue()


class CliTest(unittest.TestCase):
    def test_invoice(self):
        code, out = run("invoice", "O00007")
        self.assertEqual(code, 0)
        self.assertIn("Invoice for order O00007", out)
        self.assertIn("Total:", out)

    def test_unknown_order(self):
        self.assertEqual(run("invoice", "O99999")[0], 1)

    def test_report_daily(self):
        code, out = run("report", "daily", "--tz", "+01:00")
        self.assertEqual(code, 0)
        self.assertTrue(out.splitlines()[-1].startswith("total"))

    def test_report_countries(self):
        code, out = run("report", "countries")
        self.assertEqual(out.split()[0], "DE")

    def test_stock_low(self):
        code, out = run("stock", "low")
        self.assertIn("HW-3004", out)

    def test_export(self):
        tmp = Path(tempfile.mkdtemp())
        shutil.copytree(DATA, tmp / "data")
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["--data", str(tmp / "data"), "export", "customers", "c.csv"]), 0)
        self.assertTrue((tmp / "exports" / "c.csv").read_text().startswith("id,name,email"))


if __name__ == "__main__":
    unittest.main()
