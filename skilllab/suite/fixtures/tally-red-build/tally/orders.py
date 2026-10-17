"""Orders and order lines."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from .money import Money
from .utils.dates import parse_iso

STATUSES = ("open", "paid", "cancelled")


class UnknownOrder(KeyError):
    pass


@dataclass
class OrderLine:
    sku: str
    qty: int
    unit_price: Money  # net price agreed when the order was placed

    def to_dict(self) -> dict:
        return {"sku": self.sku, "qty": self.qty, "unit_price": str(self.unit_price.amount),
                "currency": self.unit_price.currency}

    @classmethod
    def from_dict(cls, d: dict) -> "OrderLine":
        return cls(d["sku"], int(d["qty"]), Money.of(d["unit_price"], d["currency"]))


@dataclass
class Order:
    id: str
    customer_id: str
    created_at: str  # ISO 8601 in UTC, e.g. 2026-03-01T23:30:00Z
    lines: List[OrderLine] = field(default_factory=list)
    status: str = "open"
    coupon: Optional[str] = None

    def __post_init__(self):
        if self.status not in STATUSES:
            raise ValueError(f"order {self.id}: unknown status {self.status!r}")
        parse_iso(self.created_at)  # fail early on a bad timestamp

    @property
    def currency(self) -> str:
        return self.lines[0].unit_price.currency if self.lines else "EUR"

    def to_dict(self) -> dict:
        return {"id": self.id, "customer_id": self.customer_id, "created_at": self.created_at,
                "status": self.status, "coupon": self.coupon, "lines": [l.to_dict() for l in self.lines]}

    @classmethod
    def from_dict(cls, d: dict) -> "Order":
        return cls(d["id"], d["customer_id"], d["created_at"],
                   [OrderLine.from_dict(l) for l in d["lines"]], d.get("status", "open"), d.get("coupon"))


class OrderBook:
    def __init__(self, orders: Dict[str, Order] = None):
        self.orders: Dict[str, Order] = dict(orders or {})

    def __iter__(self) -> Iterator[Order]:
        return iter(sorted(self.orders.values(), key=lambda o: (o.created_at, o.id)))

    def __len__(self) -> int:
        return len(self.orders)

    def add(self, order: Order) -> None:
        if order.id in self.orders:
            raise ValueError(f"order {order.id} already exists")
        self.orders[order.id] = order

    def get(self, order_id: str) -> Order:
        try:
            return self.orders[order_id]
        except KeyError:
            raise UnknownOrder(order_id) from None

    def by_customer(self, customer_id: str) -> List[Order]:
        return [o for o in self if o.customer_id == customer_id]

    def cancel(self, order_id: str) -> Order:
        order = self.get(order_id)
        order.status = "cancelled"
        return order

    @classmethod
    def load(cls, path: Path) -> "OrderBook":
        path = Path(path)
        if not path.exists():
            return cls()
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if data.get("version") != 1:
            raise ValueError(f"{path}: unsupported orders version {data.get('version')!r}")
        return cls({d["id"]: Order.from_dict(d) for d in data["orders"]})

    def save(self, path: Path) -> None:
        path = Path(path)
        data = {"version": 1, "orders": [o.to_dict() for o in self]}
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".orders-", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
