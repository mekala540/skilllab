"""Read bank exports."""

import csv

from .dates import parse_date
from .money import parse_amount


def load_transactions(path):
    """Read a bank CSV with columns id,date,description,amount.

    Banks sometimes export the same transaction twice; rows with the same id are the
    same transaction, so only the first is kept. Different ids are always different
    transactions, even when the date and amount match.
    """
    seen = set()
    out = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            tx = {
                "id": row["id"].strip(),
                "date": parse_date(row["date"]),
                "description": row["description"].strip(),
                "amount": parse_amount(row["amount"]),
            }
            key = tx["id"]
            if key in seen:
                continue
            seen.add(key)
            out.append(tx)
    return out
