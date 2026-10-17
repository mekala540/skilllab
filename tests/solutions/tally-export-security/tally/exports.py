"""CSV exports for the accounting team."""

from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import Iterable, List

from .catalog import Catalog
from .customers import CustomerBook
from .orders import OrderBook
from .reports import customer_summary

EXPORT_DIR = "exports"
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
# Cells starting with these are formulas in spreadsheet software (OWASP: CSV injection).
FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def safe_cell(text: str) -> str:
    """Text from customers, made inert: a leading formula character gets a ' in front."""
    return "'" + text if text.startswith(FORMULA_START) else text


def _target(root: Path, filename: str) -> Path:
    if not SAFE_NAME.match(filename) or filename in (".", ".."):
        raise ValueError(f"export file name must be a plain file name, got {filename!r}")
    out_dir = Path(root) / EXPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    if out_dir.is_symlink():
        raise ValueError(f"{out_dir} is a symlink; refusing to export")
    path = out_dir / filename
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError(f"refusing to overwrite {path}: not a regular file")
    return path


def export_rows(rows: Iterable[List[str]], header: List[str], filename: str, root: Path) -> Path:
    """Write rows to <root>/exports/<filename>. Returns the path written."""
    path = _target(root, filename)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    with open(os.open(path, flags, 0o644), "w", newline="", encoding="utf-8") as fh:
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
        rows.append([c.id, safe_cell(c.name), safe_cell(c.email), c.country, r["orders"], r["units"],
                     str(r["spend"].quantize().amount)])
    return export_rows(rows, ["id", "name", "email", "country", "orders", "units", "spend"], filename, root)
