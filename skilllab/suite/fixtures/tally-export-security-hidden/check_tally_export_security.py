"""Checker for tally-export-security: no writes outside exports/ (traversal, absolute paths,
symlinks), and customer text can't become a spreadsheet formula."""

import csv
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, ".")
EVIL = {"C0001": "=HYPERLINK(\"http://evil.example\",\"Refund\")", "C0002": "+SUM(1,2)", "C0003": "-2+3",
        "C0004": "@cmd", "C0005": "\tTabbed", "C0006": "Ana-Maria Rossi", "C0007": "Plain Name"}


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def make_root():
    root = Path(tempfile.mkdtemp())
    shutil.copytree("data", root / "data")
    doc = json.loads((root / "data" / "customers.json").read_text())
    for c in doc["customers"]:
        if c["id"] in EVIL:
            c["name"] = EVIL[c["id"]]
        if c["id"] == "C0008":
            c["email"] = "=cmd|' /C calc'!A0@example.com"
    (root / "data" / "customers.json").write_text(json.dumps(doc))
    return root


def cli(root, filename):
    from tally.cli import main
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(["--data", str(root / "data"), "export", "customers", filename])
    return code, err.getvalue()


def main():
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "tests"],
                           capture_output=True, text=True)
    if tests.returncode != 0:
        fail("the project's own tests fail:\n" + tests.stderr[-1500:])

    root = make_root()
    outside = Path(tempfile.mkdtemp())
    victim = outside / "victim.csv"
    victim.write_text("do not touch\n")
    bad_names = ["../escape.csv", "../../escape.csv", "sub/inner.csv", "..", ".", "",
                 str(outside / "absolute.csv"), "..\\escape.csv"]
    for name in bad_names:
        before = {p for p in root.rglob("*")} | {p for p in outside.rglob("*")}
        code, err = cli(root, name)
        after = {p for p in root.rglob("*")} | {p for p in outside.rglob("*")}
        created = [p for p in after - before if p.is_file()]
        if created:
            fail(f"export with file name {name!r} wrote {created[0]}")
        if code != 1 or not err.startswith("tally: "):
            fail(f"export with file name {name!r} was not refused with a `tally: ...` error (exit {code})")

    (root / "exports").mkdir(exist_ok=True)
    os.symlink(victim, root / "exports" / "link.csv")
    code, err = cli(root, "link.csv")
    if victim.read_text() != "do not touch\n":
        fail("export followed a symlink in exports/ and overwrote a file outside it")
    if code != 1:
        fail("export onto a symlink was not refused")

    code, err = cli(root, "customers-2026-03.csv")
    if code != 0:
        fail(f"a normal export failed: {err}")
    rows = list(csv.DictReader(open(root / "exports" / "customers-2026-03.csv", newline="", encoding="utf-8")))
    by_id = {r["id"]: r for r in rows}
    for cid, name in EVIL.items():
        if cid not in by_id:
            continue
        cell = by_id[cid]["name"]
        risky = name[:1] in ("=", "+", "-", "@", "\t", "\r")
        if risky and cell != "'" + name:
            fail(f"customer name {name!r} is exported as {cell!r}; it would run as a formula")
        if not risky and cell != name:
            fail(f"harmless name {name!r} was changed to {cell!r}")
    if "C0008" in by_id and not by_id["C0008"]["email"].startswith("'="):
        fail("a formula in the email column is not neutralised")
    if not all(r["spend"].replace(".", "").isdigit() and r["orders"].isdigit() for r in rows):
        fail("amounts or counts were changed")
    print("PASS: path traversal, absolute paths and symlinks refused; formulas neutralised")
    return 0


if __name__ == "__main__":
    sys.exit(main())
