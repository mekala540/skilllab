"""CSV exports for the accounting team."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, List

from .catalog import Catalog
from .customers import CustomerBook
from .orders import OrderBook
from .reports import customer_summary

EXPORT_DIR = "exports"


def export_rows(rows: Iterable[List[str]], header: List[str], filename: str, root: Path) -> Path:
    """Write rows to <root>/exports/<filename>. Returns the path written."""
    out_dir = Path(root) / EXPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for row in rows:
            w.writerow([str(c) for c in row])
    return path


def export_customers(orders: OrderBook, catalog: Catalog, customers: CustomerBook,
                     filename: str, root: Path) -> Path:
    rows = []
    for r in customer_summary(orders, catalog, customers):
        c = customers.get(r["customer_id"])
        rows.append([c.id, c.name, c.email, c.country, r["orders"], r["units"], str(r["spend"].quantize().amount)])
    return export_rows(rows, ["id", "name", "email", "country", "orders", "units", "spend"], filename, root)
