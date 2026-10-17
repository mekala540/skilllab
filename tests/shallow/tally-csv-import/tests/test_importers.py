import tempfile
import unittest
from pathlib import Path

from tally.importers import import_orders

from helpers import book, catalog, customers


class ImporterTest(unittest.TestCase):
    def test_unknown_sku(self):
        p = Path(tempfile.mkdtemp()) / "x.csv"
        p.write_text("order_id,customer_id,created_at,sku,qty,unit_price\nX,C1,2026-03-01T10:00:00Z,NOPE,1,1\n")
        r = import_orders(p, catalog(), customers(), book())
        self.assertEqual(r.errors, ["line 2: unknown sku NOPE"])


if __name__ == "__main__":
    unittest.main()
