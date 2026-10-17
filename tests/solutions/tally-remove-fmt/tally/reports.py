"""Sales reports: by day, by product, by country."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

from .catalog import Catalog
from .customers import CustomerBook
from .invoices import build_invoice
from .money import Money
from .orders import OrderBook
from .utils.dates import local_date


def _invoiced(orders: OrderBook, catalog: Catalog, customers: CustomerBook):
    for order in orders:
        if order.status != "cancelled":
            yield order, build_invoice(order, catalog, customers)


def daily_sales(orders: OrderBook, catalog: Catalog, customers: CustomerBook,
                offset: str = "+00:00", currency: str = "EUR") -> Dict[str, Money]:
    """Invoice totals per calendar day, as seen in `offset`. Only orders in `currency`."""
    out: Dict[str, Money] = {}
    for order, inv in _invoiced(orders, catalog, customers):
        if inv.currency != currency:
            continue
        day = local_date(order.created_at, offset).isoformat()
        out[day] = out.get(day, Money.zero(currency)) + inv.total
    return dict(sorted(out.items()))


def top_products(orders: OrderBook, n: int = 5) -> List[Tuple[str, int]]:
    """Best sellers by units, ties broken by SKU."""
    units: Dict[str, int] = defaultdict(int)
    for order in orders:
        if order.status == "cancelled":
            continue
        for line in order.lines:
            units[line.sku] += line.qty
    return sorted(units.items(), key=lambda kv: (-kv[1], kv[0]))[:n]


def revenue_by_country(orders: OrderBook, catalog: Catalog, customers: CustomerBook,
                       currency: str = "EUR") -> Dict[str, Money]:
    out: Dict[str, Money] = {}
    for order, inv in _invoiced(orders, catalog, customers):
        if inv.currency != currency:
            continue
        c = inv.customer.country
        out[c] = out.get(c, Money.zero(currency)) + inv.total
    return dict(sorted(out.items(), key=lambda kv: -kv[1].amount))


def customer_summary(orders: OrderBook, catalog: Catalog, customers: CustomerBook) -> List[dict]:
    """One row per customer with orders: order count, units and total spend."""
    rows = {}
    for order, inv in _invoiced(orders, catalog, customers):
        row = rows.setdefault(order.customer_id, {"customer_id": order.customer_id, "orders": 0, "units": 0,
                                                  "spend": Money.zero(inv.currency)})
        row["orders"] += 1
        row["units"] += sum(l.qty for l in order.lines)
        row["spend"] = row["spend"] + inv.total
    return sorted(rows.values(), key=lambda r: (-r["spend"].amount, r["customer_id"]))


def render_daily(sales: Dict[str, Money]) -> str:
    lines = [f"{day}  {m.format():>12}" for day, m in sales.items()]
    if sales:
        any_money = next(iter(sales.values()))
        grand = sum((m.amount for m in sales.values()), any_money.amount * 0)
        lines.append(f"{'total':10}  {Money(grand, any_money.currency).format():>12}")
    return "\n".join(lines) + "\n"


def render_countries(rev: Dict[str, Money]) -> str:
    return "".join(f"{country}  {m.format():>12}\n" for country, m in rev.items())
