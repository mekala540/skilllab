# Security review, March 2026 (excerpt)

**Finding 1 (high): user-controlled path in the customer export.**
`python3 -m tally export customers FILE` writes to `exports/FILE`, and `FILE` comes straight
from the command line (and, since last month, from the admin web form). A crafted name can write
outside `exports/`.

**Finding 2 (medium): CSV injection in the customer export.**
Customer names and emails come from marketplace sign-ups. The export is opened by accounting in
spreadsheet software, which treats some cell contents as formulas. See OWASP "CSV Injection".

Required: fix both. For finding 1 the export must only ever write a regular file directly inside
`exports/`; anything else is refused with an error (the CLI already prints errors as
`tally: <message>` and exits 1). For finding 2, apply OWASP's recommended neutralisation to
text that comes from customers; amounts and counts stay as they are.
