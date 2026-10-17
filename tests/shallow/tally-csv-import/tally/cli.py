"""Command line: python3 -m tally <command> ...

  invoice ORDER_ID            print an invoice
  report daily [--tz +01:00]  sales per day
  report countries            revenue per country
  stock low [--threshold N]   SKUs running low
  export customers FILE       CSV of customers and their spend
  import orders FILE          load marketplace orders from CSV [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .catalog import Catalog
from .customers import CustomerBook
from .exports import export_customers
from .importers import import_orders
from .inventory import Inventory
from .invoices import build_invoice, render_text
from .orders import OrderBook
from .reports import daily_sales, render_countries, render_daily, revenue_by_country


def _load(data: Path):
    return (Catalog.load(data / "catalog.json"), CustomerBook.load(data / "customers.json"),
            OrderBook.load(data / "orders.json"))


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="tally", description="Orders, invoices and stock.")
    p.add_argument("--data", default="data", help="data folder (default: ./data)")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    inv = sub.add_parser("invoice")
    inv.add_argument("order_id")

    rep = sub.add_parser("report")
    rep.add_argument("kind", choices=["daily", "countries"])
    rep.add_argument("--tz", default="+00:00", help="UTC offset to group days by, e.g. +05:30")
    rep.add_argument("--currency", default="EUR")

    st = sub.add_parser("stock")
    st.add_argument("kind", choices=["low"])
    st.add_argument("--threshold", type=int, default=10)

    ex = sub.add_parser("export")
    ex.add_argument("kind", choices=["customers"])
    ex.add_argument("filename")

    im = sub.add_parser("import")
    im.add_argument("kind", choices=["orders"])
    im.add_argument("file")
    im.add_argument("--dry-run", action="store_true", help="validate only, don't save")

    args = p.parse_args(argv)
    data = Path(args.data)
    try:
        if args.cmd == "invoice":
            catalog, customers, orders = _load(data)
            print(render_text(build_invoice(orders.get(args.order_id), catalog, customers)), end="")
        elif args.cmd == "report":
            catalog, customers, orders = _load(data)
            if args.kind == "daily":
                print(render_daily(daily_sales(orders, catalog, customers, args.tz, args.currency)), end="")
            else:
                print(render_countries(revenue_by_country(orders, catalog, customers, args.currency)), end="")
        elif args.cmd == "stock":
            inv_ = Inventory.load(data / "inventory.json")
            for sku in inv_.low_stock(args.threshold):
                print(f"{sku}  {inv_.level(sku).available}")
        elif args.cmd == "import":
            catalog, customers, orders = _load(data)
            result = import_orders(Path(args.file), catalog, customers, orders)
            for err in result.errors:
                print(err, file=sys.stderr)
            if not args.dry_run and result.orders:
                for order in result.orders:
                    orders.add(order)
                orders.save(data / "orders.json")
            print(f"imported {len(result.orders)} orders")
            return 1 if result.errors else 0
        elif args.cmd == "export":
            catalog, customers, orders = _load(data)
            print(export_customers(orders, catalog, customers, args.filename, data.parent))
    except (KeyError, ValueError) as exc:
        print(f"tally: {exc}", file=sys.stderr)
        return 1
    return 0
