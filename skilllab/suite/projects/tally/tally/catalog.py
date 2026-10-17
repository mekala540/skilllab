"""Products and their prices."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator

from .money import Money


class UnknownProduct(KeyError):
    pass


@dataclass
class Product:
    sku: str
    name: str
    price: Money  # net, per unit
    tax_class: str = "standard"
    weight_g: int = 0

    def to_dict(self) -> dict:
        return {"sku": self.sku, "name": self.name, "price": str(self.price.amount),
                "currency": self.price.currency, "tax_class": self.tax_class, "weight_g": self.weight_g}

    @classmethod
    def from_dict(cls, d: dict) -> "Product":
        return cls(d["sku"], d["name"], Money.of(d["price"], d["currency"]),
                   d.get("tax_class", "standard"), int(d.get("weight_g", 0)))


class Catalog:
    def __init__(self, products: Dict[str, Product] = None):
        self.products: Dict[str, Product] = dict(products or {})

    def __iter__(self) -> Iterator[Product]:
        return iter(sorted(self.products.values(), key=lambda p: p.sku))

    def __len__(self) -> int:
        return len(self.products)

    def add(self, product: Product) -> None:
        self.products[product.sku] = product

    def get(self, sku: str) -> Product:
        try:
            return self.products[sku]
        except KeyError:
            raise UnknownProduct(sku) from None

    @classmethod
    def load(cls, path: Path) -> "Catalog":
        path = Path(path)
        if not path.exists():
            return cls()
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if data.get("version") != 1:
            raise ValueError(f"{path}: unsupported catalog version {data.get('version')!r}")
        return cls({d["sku"]: Product.from_dict(d) for d in data["products"]})

    def save(self, path: Path) -> None:
        path = Path(path)
        data = {"version": 1, "products": [p.to_dict() for p in self]}
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".catalog-", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
