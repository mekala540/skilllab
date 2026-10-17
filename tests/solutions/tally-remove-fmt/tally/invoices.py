"""Invoices: turn an order into priced, discounted, taxed lines.

Each line is rounded on its own (net, discount, tax), and the invoice totals are the sums
of the rounded lines, so the printed lines always add up to the printed total.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from . import discounts, tax
from .catalog import Catalog
from .customers import Customer, CustomerBook
from .money import Money, total
from .orders import Order
from .utils.text import pad_columns


@dataclass
class InvoiceLine:
    sku: str
    name: str
    qty: int
    unit_price: Money
    net: Money
    discount: Money
    tax: Money

    @property
    def gross(self) -> Money:
        return self.net - self.discount + self.tax


@dataclass
class Invoice:
    order_id: str
    customer: Customer
    currency: str
    lines: List[InvoiceLine] = field(default_factory=list)

    @property
    def net(self) -> Money:
        return total((l.net for l in self.lines), self.currency)

    @property
    def discount(self) -> Money:
        return total((l.discount for l in self.lines), self.currency)

    @property
    def tax(self) -> Money:
        return total((l.tax for l in self.lines), self.currency)

    @property
    def total(self) -> Money:
        return self.net - self.discount + self.tax


def build_invoice(order: Order, catalog: Catalog, customers: CustomerBook) -> Invoice:
    if order.status == "cancelled":
        raise ValueError(f"order {order.id} is cancelled")
    customer = customers.get(order.customer_id)
    inv = Invoice(order.id, customer, order.currency)
    for line in order.lines:
        product = catalog.get(line.sku)
        net = (line.unit_price * line.qty).quantize()
        rate = discounts.line_rate(customer.tier, line.qty, order.coupon)
        discount = (net * rate).quantize()
        line_tax = tax.tax_on(net - discount, customer.country, product.tax_class)
        inv.lines.append(InvoiceLine(line.sku, product.name, line.qty, line.unit_price, net, discount, line_tax))
    return inv


def render_text(inv: Invoice) -> str:
    rows = [("SKU", "Item", "Qty", "Unit", "Net", "Discount", "Tax", "Total")]
    for l in inv.lines:
        rows.append((l.sku, l.name, l.qty, l.unit_price.format(),
                     l.net.format(), l.discount.format(),
                     l.tax.format(), l.gross.format()))
    table = pad_columns(rows, [10, 24, 4, 10, 11, 10, 10, 11], ["l", "l", "r", "r", "r", "r", "r", "r"])
    summary = [
        f"Net:       {inv.net.format()}",
        f"Discount: -{inv.discount.format()}",
        f"Tax:       {inv.tax.format()}",
        f"Total:     {inv.total.format()}",
    ]
    head = f"Invoice for order {inv.order_id}\n{inv.customer.name} <{inv.customer.email}> ({inv.customer.country})"
    return "\n\n".join([head, table, "\n".join(summary)]) + "\n"
