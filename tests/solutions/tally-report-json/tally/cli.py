"""Command line: python3 -m tally <command> ...

  invoice ORDER_ID            print an invoice
  report daily [--tz +01:00]  sales per day
  report countries            revenue per country
  stock low [--threshold N]   SKUs running low
  export customers FILE       CSV of customers and their spend
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .catalog import Catalog
from .customers import CustomerBook
from .exports import export_customers
from .inventory import Inventory
from .invoices import build_invoice, render_text
from .orders import OrderBook
from .reports import (countries_json, customer_summary, customers_json, daily_json, daily_sales,
                      render_countries, render_customers, render_daily, revenue_by_country)


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
    rep.add_argument("kind", choices=["daily", "countries", "customers"])
    rep.add_argument("--format", choices=["text", "json"], default="text")
    rep.add_argument("--tz", default="+00:00", help="UTC offset to group days by, e.g. +05:30")
    rep.add_argument("--currency", default="EUR")

    st = sub.add_parser("stock")
    st.add_argument("kind", choices=["low"])
    st.add_argument("--threshold", type=int, default=10)

    ex = sub.add_parser("export")
    ex.add_argument("kind", choices=["customers"])
    ex.add_argument("filename")

    args = p.parse_args(argv)
    data = Path(args.data)
    try:
        if args.cmd == "invoice":
            catalog, customers, orders = _load(data)
            print(render_text(build_invoice(orders.get(args.order_id), catalog, customers)), end="")
        elif args.cmd == "report":
            catalog, customers, orders = _load(data)
            as_json = args.format == "json"
            if args.kind == "daily":
                sales = daily_sales(orders, catalog, customers, args.tz, args.currency)
                doc, text = (daily_json(sales, args.currency, args.tz), None) if as_json else (None, render_daily(sales))
            elif args.kind == "countries":
                rev = revenue_by_country(orders, catalog, customers, args.currency)
                doc, text = (countries_json(rev, args.currency), None) if as_json else (None, render_countries(rev))
            else:
                rows = customer_summary(orders, catalog, customers)
                doc, text = (customers_json(rows, customers), None) if as_json else (None, render_customers(rows, customers))
            print(json.dumps(doc, indent=2, ensure_ascii=False) if as_json else text, end="\n" if as_json else "")
        elif args.cmd == "stock":
            inv_ = Inventory.load(data / "inventory.json")
            for sku in inv_.low_stock(args.threshold):
                print(f"{sku}  {inv_.level(sku).available}")
        elif args.cmd == "export":
            catalog, customers, orders = _load(data)
            print(export_customers(orders, catalog, customers, args.filename, data.parent))
    except (KeyError, ValueError) as exc:
        print(f"tally: {exc}", file=sys.stderr)
        return 1
    return 0
