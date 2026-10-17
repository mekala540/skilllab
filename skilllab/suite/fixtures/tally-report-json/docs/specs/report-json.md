# Spec: machine-readable reports

The data team wants to load our reports into their warehouse.

## Command line

Add `--format {text,json}` (default `text`) to `python3 -m tally report ...`, and a new report:

```
python3 -m tally report daily     [--tz +01:00] [--currency EUR] [--format json]
python3 -m tally report countries [--currency EUR]              [--format json]
python3 -m tally report customers                               [--format json]
```

`text` output of the existing reports must not change. `report customers` in text form prints one
line per customer: `<id>  <name>  <orders>  <units>  <spend>` (spend formatted like the other reports).

## JSON

Printed as `json.dumps(document, indent=2, ensure_ascii=False)` followed by a newline.
**Money is always a string with exactly the currency's number of decimals** (`"1234.50"`, never a
number: floats can't hold money exactly). Rounding follows docs/architecture.md.

`report daily`:

```json
{"report": "daily", "currency": "EUR", "tz": "+01:00",
 "days": [{"date": "2026-03-01", "total": "1234.50"}, ...],
 "total": "56789.00"}
```

Days in date order. `total` is the sum of the (unrounded) day totals, then rounded.

`report countries`:

```json
{"report": "countries", "currency": "EUR",
 "countries": [{"country": "DE", "total": "193524.85"}, ...]}
```

Highest total first, like the text report.

`report customers`:

```json
{"report": "customers",
 "customers": [{"id": "C0007", "name": "Greta Lund", "orders": 21, "units": 312,
                "spend": "12345.67", "currency": "EUR"}, ...]}
```

Same order as `reports.customer_summary` (highest spend first). Only customers with orders.
