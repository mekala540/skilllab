"""Checker for tally-red-build. The '2.5 prep' commit broke four things; the visible tests only
show three. The fourth (German formatting of amounts over a million) must be fixed too."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, ".")


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def main():
    proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "tests"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        fail("the project's own tests still fail:\n" + proc.stderr[-1500:])

    from tally.catalog import Catalog, Product
    from tally.money import Money
    from tally.orders import Order, OrderBook, OrderLine
    from tally.utils.dates import parse_offset

    for value, want in (("1234567.891", "1.234.567,89 €"), ("1000000", "1.000.000,00 €"), ("999.5", "999,50 €"),
                        ("-12345678.9", "-12.345.678,90 €"), ("0.4", "0,40 €")):
        got = Money.of(value, "EUR").format("de")
        if got != want:
            fail(f"Money.of({value!r}, 'EUR').format('de') is {got!r}, expected {want!r}")
    if Money.of("1234567.891", "EUR").format() != "€1,234,567.89":
        fail("English formatting changed")

    for good in ("+05:30", "-03:30", "+14:00", "-00:00"):
        parse_offset(good)
    for bad in ("+5:30", "05:30", "+0530", "5:30", "+15:00", "+05:3"):
        try:
            parse_offset(bad)
        except ValueError:
            continue
        fail(f"parse_offset({bad!r}) was accepted; the documented format is +HH:MM")

    data = json.loads(Path("data/catalog.json").read_text())
    loaded = Catalog.load(Path("data/catalog.json"))
    for d in data["products"]:
        if loaded.get(d["sku"]).tax_class != d["tax_class"]:
            fail(f"{d['sku']}: tax class {d['tax_class']!r} is lost when the catalog is loaded")
    tmp = Path(tempfile.mkdtemp()) / "c.json"
    loaded.save(tmp)
    by_sku = lambda doc: {d["sku"]: d for d in doc["products"]}  # noqa: E731
    if by_sku(json.loads(tmp.read_text())) != by_sku(data):
        fail("saving the loaded catalog does not reproduce data/catalog.json")

    book = OrderBook()
    for oid, status in (("A", "paid"), ("B", "open"), ("C", "cancelled")):
        book.add(Order(oid, "C1", "2026-03-01T10:00:00Z", [OrderLine("HW-1", 1, Money.of("1", "EUR"))], status))
    try:
        book.cancel("A")
        fail("a paid order was cancelled; it must be refunded instead")
    except ValueError:
        pass
    book.cancel("B")
    book.cancel("C")
    if book.get("A").status != "paid" or book.get("B").status != "cancelled":
        fail("cancel() changed the wrong orders")
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True)
    count = subprocess.run(["git", "rev-list", "--count", "main"], capture_output=True, text=True)
    if status.stdout.strip() or int(count.stdout.strip() or 0) < 3:
        fail("the fix isn't committed on main (uncommitted changes, or no new commit)")
    print("PASS: all four regressions from the 2.5 prep commit are fixed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
