# Spec: importing orders from CSV

Marketplace orders arrive as CSV exports. We need to load them into `data/orders.json`.

## Command

```
python3 -m tally import orders FILE [--dry-run]
```

- Prints `imported N orders` (N may be 0) on stdout.
- Prints each error on stderr, one per line, in file order.
- Exit code 0 if there were no errors, 1 if there were any (valid orders are still imported).
- `--dry-run`: validate and report exactly the same way, but don't change `orders.json`.

## Python API

`tally/importers.py`:

```python
def import_orders(path, catalog, customers, existing) -> ImportResult
```

`existing` is the current `OrderBook`. `ImportResult` has `orders` (a list of new `Order`
objects, in the order they first appear in the file) and `errors` (a list of strings).
`import_orders` never modifies `existing` and never writes files; the CLI does that.

## File format

- UTF-8, with or without a byte order mark. Comma separated, standard CSV quoting.
- The first non-blank line is the header. Column names are case-insensitive and may have
  surrounding spaces; columns can come in any order; unknown columns are ignored.
- Required columns: `order_id`, `customer_id`, `created_at`, `sku`, `qty`, `unit_price`.
  Optional: `coupon`. If a required column is missing, the result is a single error
  `header: missing column <name>` (the first missing one, in the order listed here) and no orders.
- Blank lines (or lines with only commas/whitespace) are ignored anywhere.
- One row per order line. Rows with the same `order_id` form one order, even if they are not
  next to each other. All rows of an order must agree on `customer_id`, `created_at` and
  `coupon`.
- Imported orders get status `open`. Prices are in EUR. `created_at` is stored the way all
  timestamps are: converted to UTC, formatted like `2026-03-14T10:05:00Z`.

## Validation

Every problem is reported as `line N: <message>`, where N is the line number in the file
(the header is line 1, blank lines count). Messages:

| Problem | Message |
| --- | --- |
| customer not in customers.json | `unknown customer C9999` |
| SKU not in the catalog | `unknown sku XX-1` |
| qty not a whole number ≥ 1 | `bad qty 'abc'` |
| unit_price not a number ≥ 0 with at most 2 decimals | `bad unit_price '1.999'` |
| created_at not ISO 8601 with a time zone | `bad created_at '2026-03-01 10:00'` |
| coupon not a known code (empty is fine) | `unknown coupon FREE` |
| order_id already in orders.json | `order O00001 already exists` |
| a row disagrees with the first row of its order | `order X1 has conflicting customer_id` (or `created_at`, `coupon`) |

A row can have several problems; report each one (in the table's order). If any row of an
order has a problem, the whole order is rejected; the other orders are still imported.
Values are trimmed of surrounding spaces before checking.
