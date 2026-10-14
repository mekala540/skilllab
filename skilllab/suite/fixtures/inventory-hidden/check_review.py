"""Review check: both seeded bugs reported, by function name, in at most 5 bullets.

Seeded bugs: remove_stock lets stock go negative; apply_discount uses floor division (//)
on prices, so 19.99 at 15% gives 17.99 instead of 16.99. The other functions are correct.
"""

import re
import sys

SEEDED = ["remove_stock", "apply_discount"]
MAX_BULLETS = 5


def main():
    try:
        text = open("REVIEW.md", encoding="utf-8").read()
    except OSError:
        print("FAIL: REVIEW.md not found")
        return 1
    bullets = [line for line in text.splitlines() if re.match(r"^\s*([-*+]|\d+[.)])\s+", line)]
    if not bullets:
        print("FAIL: no bulleted findings")
        return 1
    if len(bullets) > MAX_BULLETS:
        print(f"FAIL: {len(bullets)} bullets; at most {MAX_BULLETS} allowed")
        return 1
    missing = [name for name in SEEDED if name not in text]
    if missing:
        print(f"FAIL: missed {', '.join(missing)}")
        return 1
    print(f"found both seeded bugs in {len(bullets)} bullets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
