"""Checker for tally-slow-export: `export customers` on 40,000 orders and 2,000 customers must
be fast (within a few times a straightforward one-pass version, timed on this machine) and
produce exactly the same CSV."""

import csv
import json
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, ".")
LIMIT_FACTOR = 6
MIN_LIMIT = 4.0


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def make_data(root: Path):
    rng = random.Random(42)
    data = root / "data"
    data.mkdir(parents=True)
    catalog = json.loads(Path("data/catalog.json").read_text())
    skus = [(p["sku"], p["price"]) for p in catalog["products"]]
    countries = ["DE", "FR", "NL", "GB", "IN", "JP", "US"]
    customers = [{"id": f"C{i:05d}", "name": f"Customer {i}", "email": f"c{i}@example.com",
                  "country": countries[i % 7], "tier": ["standard", "silver", "gold"][i % 3], "currency": "EUR"}
                 for i in range(1, 2001)]
    orders = []
    for i in range(1, 40001):
        lines = [{"sku": s, "qty": rng.choice([1, 2, 3, 25]), "unit_price": p, "currency": "EUR"}
                 for s, p in rng.sample(skus, rng.choice([1, 2, 3]))]
        orders.append({"id": f"X{i:06d}", "customer_id": f"C{rng.randrange(1, 1801):05d}",
                       "created_at": f"2026-03-{1 + i % 28:02d}T{i % 24:02d}:00:00Z",
                       "status": rng.choice(["paid", "paid", "open", "cancelled"]), "coupon": None, "lines": lines})
    for name, payload in (("catalog", catalog), ("customers", {"version": 1, "customers": customers}),
                          ("orders", {"version": 1, "orders": orders})):
        (data / f"{name}.json").write_text(json.dumps(payload))
    return data


REFERENCE = r'''
import csv, sys, time
sys.path.insert(0, ".")
from pathlib import Path
from tally.catalog import Catalog
from tally.customers import CustomerBook
from tally.invoices import build_invoice
from tally.money import Money
from tally.orders import OrderBook
data, out = Path(sys.argv[1]), Path(sys.argv[2])
t = time.perf_counter()
cat, cust, orders = Catalog.load(data / "catalog.json"), CustomerBook.load(data / "customers.json"), OrderBook.load(data / "orders.json")
rows = {}
for o in orders:
    if o.status == "cancelled":
        continue
    inv = build_invoice(o, cat, cust)
    r = rows.setdefault(o.customer_id, [0, 0, Money.zero(inv.currency)])
    r[0] += 1; r[1] += sum(l.qty for l in o.lines); r[2] = r[2] + inv.total
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "name", "email", "country", "orders", "units", "spend"])
    for cid, (n, units, spend) in sorted(rows.items(), key=lambda kv: (-kv[1][2].amount, kv[0])):
        c = cust.get(cid)
        w.writerow([c.id, c.name, c.email, c.country, n, units, str(spend.quantize().amount)])
print(time.perf_counter() - t)
'''


def main():
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "tests"],
                           capture_output=True, text=True)
    if tests.returncode != 0:
        fail("the project's own tests fail:\n" + tests.stderr[-1500:])
    root = Path(tempfile.mkdtemp())
    data = make_data(root)
    ref = subprocess.run([sys.executable, "-c", REFERENCE, str(data), str(root / "reference.csv")],
                         capture_output=True, text=True)
    if ref.returncode != 0:
        fail("reference export crashed (did build_invoice or the loaders change?): " + ref.stderr[-400:])
    limit = max(MIN_LIMIT, LIMIT_FACTOR * float(ref.stdout.strip()))
    start = time.perf_counter()
    try:
        proc = subprocess.run([sys.executable, "-W", "ignore", "-m", "tally", "--data", str(data),
                               "export", "customers", "big.csv"], capture_output=True, text=True, timeout=limit + 5)
    except subprocess.TimeoutExpired:
        fail(f"export customers took more than {limit:.1f}s on 40,000 orders")
    took = time.perf_counter() - start
    if proc.returncode != 0:
        fail("export customers failed: " + proc.stderr[-400:])
    if took > limit:
        fail(f"export customers took {took:.1f}s on 40,000 orders; it should take under {limit:.1f}s here")
    got = (root / "exports" / "big.csv").read_bytes()
    if got != (root / "reference.csv").read_bytes():
        fail("export customers output changed")
    print(f"PASS: export of 40,000 orders in {took:.1f}s (limit {limit:.1f}s), output identical")
    return 0


if __name__ == "__main__":
    sys.exit(main())
