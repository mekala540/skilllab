"""Customers: who they are, where they are taxed, and their discount tier."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterator, List
from .storage import load_document, save_document

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.I)


class UnknownCustomer(KeyError):
    pass


@dataclass
class Customer:
    id: str
    name: str
    email: str
    country: str  # ISO 3166 alpha-2, decides the tax rate
    tier: str = "standard"
    currency: str = "EUR"

    def validate(self) -> List[str]:
        problems = []
        if not EMAIL.match(self.email):
            problems.append(f"bad email {self.email!r}")
        if len(self.country) != 2 or not self.country.isupper():
            problems.append(f"bad country {self.country!r}")
        return problems


class CustomerBook:
    def __init__(self, customers: Dict[str, Customer] = None):
        self.customers: Dict[str, Customer] = dict(customers or {})

    def __iter__(self) -> Iterator[Customer]:
        return iter(sorted(self.customers.values(), key=lambda c: c.id))

    def __len__(self) -> int:
        return len(self.customers)

    def add(self, customer: Customer) -> None:
        problems = customer.validate()
        if problems:
            raise ValueError(f"customer {customer.id}: {'; '.join(problems)}")
        self.customers[customer.id] = customer

    def get(self, customer_id: str) -> Customer:
        try:
            return self.customers[customer_id]
        except KeyError:
            raise UnknownCustomer(customer_id) from None

    @classmethod
    def load(cls, path: Path) -> "CustomerBook":
        data = load_document(path, "customers")
        if data is None:
            return cls()
        return cls({d["id"]: Customer(**d) for d in data["customers"]})

    def save(self, path: Path) -> None:
        save_document(path, "customers", {"customers": [asdict(c) for c in self]})
