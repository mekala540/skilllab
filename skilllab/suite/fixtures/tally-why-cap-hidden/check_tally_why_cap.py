"""Checker for tally-why-cap: answers from git history, exact, and no code changed."""

import re
import subprocess
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

INTRODUCED = "Cap combined discounts at 25%"
VALUE_CHANGE = "Raise the discount cap to 30% for the spring campaign"
COMMITS = 16


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout


def main():
    log = git("log", "main", "--format=%H %s").splitlines()
    if len(log) != COMMITS:
        fail("main's history was changed")
    if git("status", "--porcelain", "--untracked-files=no").strip():
        fail("tracked files were changed; this task is a question, not a code change")
    by_subject = {l.split(" ", 1)[1]: l.split()[0] for l in log}
    want = {"introduced": by_subject[INTRODUCED], "issue": "214",
            "last_value_change": by_subject[VALUE_CHANGE], "previous_value": Decimal("0.25")}

    if not Path("ANSWER.md").is_file():
        fail("ANSWER.md not found")
    got = {}
    for line in Path("ANSWER.md").read_text().splitlines():
        m = re.match(r"^\s*[-*]?\s*`?(introduced|issue|last_value_change|previous_value)`?\s*:\s*`?([^`\s]+)`?", line)
        if m and m.group(1) not in got:
            got[m.group(1)] = m.group(2).strip()
    for key in want:
        if key not in got:
            fail(f"ANSWER.md has no '{key}:' line")
    if got["introduced"] != want["introduced"]:
        fail("introduced: that is not the commit that first added the cap")
    if got["issue"].lstrip("#") != want["issue"]:
        fail("issue: wrong issue number")
    if got["last_value_change"] != want["last_value_change"]:
        fail("last_value_change: that commit did not change the cap's value")
    try:
        prev = Decimal(got["previous_value"].rstrip("%")) / (100 if got["previous_value"].endswith("%") else 1)
    except InvalidOperation:
        fail("previous_value: not a number")
    if prev != want["previous_value"]:
        fail("previous_value: wrong")
    print("PASS: introduction, issue, last value change and previous value all correct")
    return 0


if __name__ == "__main__":
    sys.exit(main())
