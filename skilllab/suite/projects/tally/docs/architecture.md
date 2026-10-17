# Architecture and conventions

## Money

- All amounts are `Money` (a `Decimal` plus a currency). Never use `float` for money.
- Arithmetic keeps full precision. **Round per invoice line**: net, then discount, then tax are each
  rounded half-up to the currency's minor unit. Invoice totals are sums of rounded lines, so a
  printed invoice always adds up.
- Format with `Money.format(locale)`. `tally.money.fmt()` is deprecated (since 2.3) and is being
  removed; don't add new callers.

## Time

- Timestamps are stored as ISO 8601 strings in UTC with a `Z` suffix.
- Reports group by the calendar day **as seen in a fixed UTC offset** passed by the caller
  (`--tz +05:30`). Never use the machine's local time zone.

## Discounts

- A line's discount rate is tier + volume + coupon, capped at `MAX_DISCOUNT` (30%).

## Storage

- Each data file is JSON with a top-level `"version": 1`. Writes go to a temp file in the same
  folder and are moved into place (`os.replace`), so a crash never leaves a half-written file.

## Errors

- Domain errors are `KeyError` subclasses (`UnknownProduct`, `UnknownCustomer`, `UnknownOrder`,
  `UnknownCoupon`, `UnknownTaxRate`) or `ValueError`. The CLI prints them as `tally: <message>`
  and exits 1.

## Tests

- `unittest` only, run with `python3 -m unittest discover -s tests -t tests`.
- Shared in-memory fixtures live in `tests/helpers.py`.
