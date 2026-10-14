# parse_duration(text) -> int

Returns the duration in whole seconds.

## Valid input

- One or more parts. A part is a number followed by a unit: `h` (hours), `m` (minutes), `s` (seconds).
- Units are case-insensitive: `1H` is the same as `1h`.
- Numbers are non-negative and may have a decimal point with digits on both sides: `1.5h`, `0.25m`.
- Each unit appears at most once, and units appear in the order h, m, s: `1h30m` is valid, `30m1h` is not.
- Whitespace is allowed around the whole string and between parts, and between a number and its unit: `" 1h 30 m "`.
- The total must be a whole number of seconds: `1.5m` is 90, `0.5s` is invalid.

## Invalid input raises ValueError

- empty or whitespace-only strings
- a number without a unit (`90`), a unit without a number (`h`), unknown units (`5x`, `1d`)
- negative numbers (`-1h`), malformed numbers (`1.h`, `.5h`, `1..5h`)
- repeated or out-of-order units (`1h1h`, `5s1m`)
- totals that are not whole seconds (`0.5s`)

## Examples

| input | result |
| --- | --- |
| `"90s"` | 90 |
| `"1h30m"` | 5400 |
| `"2h"` | 7200 |
| `"1h 5m 10s"` | 3910 |
| `"1.5h"` | 5400 |
| `"0s"` | 0 |
| `"10M"` | 600 |
