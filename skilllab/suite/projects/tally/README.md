# tally

Orders, invoices and stock for a small online shop that sells books, coffee and kitchenware
across Europe, the UK, India, Japan and the US.

## Run

```bash
python3 -m tally --data data invoice O00007
python3 -m tally report daily --tz +01:00
python3 -m tally report countries
python3 -m tally stock low --threshold 10
python3 -m tally export customers customers.csv
```

## Test

```bash
python3 -m unittest discover -s tests -t tests
```

No dependencies beyond the Python standard library (3.9+).

## Layout

| Module | What it does |
| --- | --- |
| `tally/money.py` | `Money`: Decimal amounts per currency, half-up rounding, formatting |
| `tally/tax.py` | VAT/GST rates by country and tax class |
| `tally/discounts.py` | tier, volume and coupon discounts, capped |
| `tally/catalog.py`, `customers.py`, `orders.py`, `inventory.py` | the data and their JSON files |
| `tally/invoices.py` | order → invoice lines (net, discount, tax) and text rendering |
| `tally/reports.py` | daily sales, best sellers, revenue by country, customer summary |
| `tally/exports.py` | CSV exports for accounting |
| `tally/cli.py` | the `python3 -m tally` command |
| `tally/utils/` | dates (UTC storage, fixed offsets) and text helpers |

See `docs/architecture.md` for the rules the code follows.
