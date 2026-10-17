"""Import orders from marketplace CSV exports (see docs/specs/csv-import.md)."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List, Optional

from . import discounts
from .catalog import Catalog
from .customers import CustomerBook
from .money import Money
from .orders import Order, OrderBook, OrderLine
from .utils.dates import format_utc, parse_iso

REQUIRED = ("order_id", "customer_id", "created_at", "sku", "qty", "unit_price")
SHARED = ("customer_id", "created_at", "coupon")


@dataclass
class ImportResult:
    orders: List[Order] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def _blank(row: List[str]) -> bool:
    return all(not c.strip() for c in row)


def _row_problems(rec: Dict[str, str], catalog: Catalog, customers: CustomerBook) -> List[str]:
    out = []
    if rec["customer_id"] not in customers.customers:
        out.append(f"unknown customer {rec['customer_id']}")
    if rec["sku"] not in catalog.products:
        out.append(f"unknown sku {rec['sku']}")
    if not (rec["qty"].isdigit() and int(rec["qty"]) >= 1):
        out.append(f"bad qty {rec['qty']!r}")
    try:
        price = Decimal(rec["unit_price"])
        if not price.is_finite() or price < 0 or price.as_tuple().exponent < -2:
            raise InvalidOperation
    except InvalidOperation:
        out.append(f"bad unit_price {rec['unit_price']!r}")
    try:
        parse_iso(rec["created_at"])
    except ValueError:
        out.append(f"bad created_at {rec['created_at']!r}")
    if rec["coupon"]:
        try:
            discounts.coupon_rate(rec["coupon"])
        except discounts.UnknownCoupon:
            out.append(f"unknown coupon {rec['coupon']}")
    return out


def import_orders(path: Path, catalog: Catalog, customers: CustomerBook, existing: OrderBook) -> ImportResult:
    text = Path(path).read_text(encoding="utf-8-sig")
    # reader.line_num is the physical line where each row ends (header = line 1).
    reader = csv.reader(io.StringIO(text, newline=""))
    numbered = []
    for row in reader:
        numbered.append((reader.line_num, row))
    numbered = [(n, r) for n, r in numbered if not _blank(r)]
    result = ImportResult()
    if not numbered:
        return result
    _, header = numbered[0]
    cols = {name.strip().lower(): i for i, name in enumerate(header)}
    for name in REQUIRED:
        if name not in cols:
            result.errors.append(f"header: missing column {name}")
            return result

    groups: Dict[str, dict] = {}
    for line, row in numbered[1:]:
        rec = {name: (row[i].strip() if i < len(row) else "") for name, i in cols.items()}
        rec.setdefault("coupon", "")
        problems = _row_problems(rec, catalog, customers)
        oid = rec["order_id"]
        g = groups.get(oid)
        if g is None:
            g = groups[oid] = {"first": rec, "lines": [], "bad": False}
            if oid in existing.orders:
                problems.append(f"order {oid} already exists")
        else:
            for key in SHARED:
                if rec[key] != g["first"][key]:
                    problems.append(f"order {oid} has conflicting {key}")
        result.errors += [f"line {line}: {p}" for p in problems]
        g["bad"] = g["bad"] or bool(problems)
        if not problems:
            g["lines"].append(OrderLine(rec["sku"], int(rec["qty"]), Money.of(rec["unit_price"], "EUR")))

    for oid, g in groups.items():
        if g["bad"]:
            continue
        first = g["first"]
        result.orders.append(Order(oid, first["customer_id"], format_utc(parse_iso(first["created_at"])),
                                   g["lines"], "open", first["coupon"] or None))
    return result
