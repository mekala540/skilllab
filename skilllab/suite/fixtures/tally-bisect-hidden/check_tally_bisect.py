"""Checker for tally-bisect: right culprit commit, fix on its own branch, main untouched."""

import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

CULPRIT_SUBJECT = "Discounts: tidy discount tables"
MAIN_HEAD_SUBJECT = "Text: truncate keeps the ellipsis inside the width"
MAIN_COMMITS = 40
BRANCH = "fix/volume-threshold"

PROBE = r'''
import sys
sys.path.insert(0, ".")
from decimal import Decimal
from tally import discounts
cases = {19: "0", 20: "0.02", 21: "0.02", 49: "0.02", 50: "0.05", 99: "0.05", 100: "0.08", 150: "0.08"}
for qty, want in cases.items():
    got = discounts.volume_rate(qty)
    if got != Decimal(want):
        print(f"volume_rate({qty}) is {got}, expected {want}")
        sys.exit(1)
if discounts.line_rate("gold", 50) != Decimal("0.15"):
    print("line_rate('gold', 50) should be 0.15")
    sys.exit(1)
'''


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def main():
    log = git("log", "main", "--format=%H %s").stdout.splitlines()
    if len(log) != MAIN_COMMITS or not log[0].endswith(MAIN_HEAD_SUBJECT):
        fail("main was changed: it must keep its original 40 commits and nothing new")
    culprit = next((l.split()[0] for l in log if l.endswith(CULPRIT_SUBJECT)), None)
    if culprit is None:
        fail("main's history was rewritten")
    if not Path("CULPRIT.txt").is_file():
        fail("CULPRIT.txt not found")
    named = Path("CULPRIT.txt").read_text().strip()
    if named != culprit:
        fail(f"CULPRIT.txt names {named[:12] or 'nothing'}, which is not the commit that broke volume discounts")

    if git("rev-parse", "--verify", "-q", BRANCH).returncode != 0:
        fail(f"branch {BRANCH} not found")
    if git("merge-base", "--is-ancestor", "main", BRANCH).returncode != 0:
        fail(f"{BRANCH} was not created from main")
    if git("rev-parse", BRANCH).stdout == git("rev-parse", "main").stdout:
        fail(f"{BRANCH} has no new commit")

    tmp = Path(tempfile.mkdtemp())
    archive = subprocess.run(["git", "archive", "--format=tar", BRANCH], capture_output=True)
    (tmp / "b.tar").write_bytes(archive.stdout)
    with tarfile.open(tmp / "b.tar") as tar:
        tar.extractall(tmp / "tree")
    tree = tmp / "tree"
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "tests"],
                           cwd=tree, capture_output=True, text=True)
    if tests.returncode != 0:
        fail(f"tests fail on {BRANCH}:\n{tests.stderr[-1200:]}")
    probe = subprocess.run([sys.executable, "-c", PROBE], cwd=tree, capture_output=True, text=True)
    if probe.returncode != 0:
        fail(f"on {BRANCH}: {probe.stdout.strip() or probe.stderr[-400:]}")
    print("PASS: culprit found, fixed on its own branch, main untouched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
