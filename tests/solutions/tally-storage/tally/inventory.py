"""Stock levels: what is on hand, what is reserved for open orders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
from .storage import load_document, save_document


class OutOfStock(Exception):
    pass


@dataclass
class StockLevel:
    on_hand: int = 0
    reserved: int = 0

    @property
    def available(self) -> int:
        return self.on_hand - self.reserved


class Inventory:
    def __init__(self, levels: Dict[str, StockLevel] = None):
        self.levels: Dict[str, StockLevel] = dict(levels or {})

    def level(self, sku: str) -> StockLevel:
        return self.levels.setdefault(sku, StockLevel())

    def receive(self, sku: str, qty: int) -> None:
        if qty <= 0:
            raise ValueError("received quantity must be positive")
        self.level(sku).on_hand += qty

    def reserve(self, sku: str, qty: int) -> None:
        lvl = self.level(sku)
        if qty <= 0:
            raise ValueError("reserved quantity must be positive")
        if lvl.available < qty:
            raise OutOfStock(f"{sku}: {lvl.available} available, {qty} requested")
        lvl.reserved += qty

    def release(self, sku: str, qty: int) -> None:
        lvl = self.level(sku)
        lvl.reserved = max(0, lvl.reserved - qty)

    def ship(self, sku: str, qty: int) -> None:
        """Reserved units leave the warehouse."""
        lvl = self.level(sku)
        if lvl.reserved < qty:
            raise ValueError(f"{sku}: only {lvl.reserved} reserved, cannot ship {qty}")
        lvl.reserved -= qty
        lvl.on_hand -= qty

    def low_stock(self, threshold: int = 10) -> List[str]:
        return sorted(sku for sku, lvl in self.levels.items() if lvl.available < threshold)

    @classmethod
    def load(cls, path: Path) -> "Inventory":
        data = load_document(path, "inventory")
        if data is None:
            return cls()
        return cls({sku: StockLevel(**v) for sku, v in data["levels"].items()})

    def save(self, path: Path) -> None:
        save_document(path, "inventory", {"levels": {sku: {"on_hand": l.on_hand, "reserved": l.reserved} for sku, l in sorted(self.levels.items())}})
