# next_run(expr, after) -> datetime

Return the first time **strictly after** `after` that matches the cron expression `expr`.
`after` is a naive `datetime`; seconds and microseconds in it are ignored when matching,
and the result always has second = 0 and microsecond = 0.

## Fields

Five fields separated by whitespace:

| field | allowed values |
| --- | --- |
| minute | 0-59 |
| hour | 0-23 |
| day of month | 1-31 |
| month | 1-12, or `JAN`-`DEC` |
| day of week | 0-7, or `SUN`-`SAT` (0 and 7 both mean Sunday) |

Names are case-insensitive and may be used anywhere a number may, including in ranges (`MON-FRI`).

Each field is a comma-separated list of one or more items. An item is:

- `*`: every allowed value
- `N`: a single value
- `A-B`: every value from A to B inclusive (A must be <= B)
- any of the above followed by `/S`: every S-th value of that set, starting from its first.
  `*/15` in minutes is 0,15,30,45; `10-30/10` is 10,20,30; `N/S` means from N to the
  field's maximum, so `5/20` in minutes is 5,25,45.

## Day of month and day of week

A field is *restricted* unless its text begins with `*`.

- If **both** day of month and day of week are restricted, a day matches when **either** matches.
  `0 0 13 * FRI` runs on every 13th and on every Friday.
- Otherwise a day must match **both** (a `*` field matches every day).
  `0 0 */2 * MON` runs only on Mondays that fall on an odd day of the month.

## Macros

`@yearly` and `@annually` = `0 0 1 1 *`, `@monthly` = `0 0 1 * *`, `@weekly` = `0 0 * * 0`,
`@daily` and `@midnight` = `0 0 * * *`, `@hourly` = `0 * * * *`. Case-insensitive.

## Errors

Raise `ValueError` for: a wrong number of fields, values out of range, unknown names or macros,
malformed items (empty list items, `1-2-3`, `-1`, `a`), a step of 0 or a non-numeric step, a range
whose start is after its end, and expressions with no matching time within the next 5 years
(such as `0 0 30 2 *`).
