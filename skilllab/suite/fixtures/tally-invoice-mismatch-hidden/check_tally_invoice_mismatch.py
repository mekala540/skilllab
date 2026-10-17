"""Checker for tally-invoice-mismatch. Two root causes: half-even rounding in Money.quantize
and the coupon stacked on top of the discount cap. Fixing one is not enough."""

import json
import subprocess
import sys
import warnings
from decimal import Decimal
from itertools import product
from pathlib import Path

sys.path.insert(0, ".")
sys.path.insert(0, "tests")
warnings.simplefilter("ignore", DeprecationWarning)


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def main():
    proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "tests"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        fail("the project's own tests fail:\n" + proc.stderr[-1500:])

    from tally import discounts
    from tally.catalog import Catalog
    from tally.customers import CustomerBook
    from tally.invoices import build_invoice
    from tally.money import Money
    from tally.orders import OrderBook

    for value, cur, want in (("2.345", "EUR", "2.35"), ("-2.345", "EUR", "-2.35"), ("0.125", "EUR", "0.13"),
                             ("10.005", "GBP", "10.01"), ("1234.5", "JPY", "1235"), ("2.5", "JPY", "3"),
                             ("2.344", "EUR", "2.34")):
        got = Money.of(value, cur).quantize().amount
        if got != Decimal(want):
            fail(f"Money.of({value!r}, {cur!r}).quantize() is {got}, finance rounds half up to {want}")

    for tier, qty, coupon in product(discounts.TIER_RATES, (1, 19, 20, 49, 50, 99, 100, 500),
                                     (None, "WELCOME10", "SPRING15", "STAFF25")):
        rate = discounts.line_rate(tier, qty, coupon)
        want = min(discounts.TIER_RATES[tier] + discounts.volume_rate(qty) + discounts.coupon_rate(coupon),
                   discounts.MAX_DISCOUNT)
        if rate != want:
            fail(f"line_rate({tier!r}, {qty}, {coupon!r}) is {rate}, expected {want} (cap {discounts.MAX_DISCOUNT})")

    expected = json.loads(Path("expected_totals.json").read_text())
    d = Path("data")
    cat, cust, orders = Catalog.load(d / "catalog.json"), CustomerBook.load(d / "customers.json"), OrderBook.load(d / "orders.json")
    wrong = []
    for oid, want in sorted(expected.items()):
        inv = build_invoice(orders.get(oid), cat, cust)
        if inv.total.amount != Decimal(want):
            wrong.append(f"{oid}: {inv.total.amount} != {want}")
        if sum(l.net.amount - l.discount.amount + l.tax.amount for l in inv.lines) != inv.total.amount:
            fail(f"{oid}: invoice lines don't add up to the total")
    if wrong:
        fail(f"{len(wrong)} sample invoices have the wrong total, e.g. {wrong[:3]}")
    print(f"PASS: rounding is half up, the cap holds for every rule combination, {len(expected)} invoices match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
