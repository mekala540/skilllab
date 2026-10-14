"""Git regression check.

1. CULPRIT.txt names the commit that broke distance() ("Tidy helpers", commit 19 of 30).
2. main is untouched: same 30 commit messages in order, and its calc.py still has the bug.
3. Branch fix/distance starts from main, adds at least one commit, and its calc.py is correct.
"""

import os
import shutil
import subprocess
import sys
import tempfile

CULPRIT_MESSAGE = "Tidy helpers"
MAIN_MESSAGES = 30
MAIN_TIP = "Bump version"
BUG_LINE = "return a - b if a > b else b - a if b > 0 else a - b"

CALC_TEST = '''
import unittest
from calc import distance, clamp, mean, median, span, total, lerp, is_close, sign

class T(unittest.TestCase):
    def test_distance(self):
        for a in range(-6, 7):
            for b in range(-6, 7):
                self.assertEqual(distance(a, b), abs(a - b), (a, b))
        self.assertEqual(distance(-2.5, 1.5), 4.0)

    def test_others_kept(self):
        self.assertEqual(clamp(5, 0, 3), 3)
        self.assertEqual(mean([1, 2, 3]), 2)
        self.assertEqual(median([3, 1, 2, 4]), 2.5)
        self.assertEqual(span([1, 5, -2]), 7)
        self.assertEqual(total([1, 2]), 3)
        self.assertEqual(lerp(0, 10, 0.5), 5)
        self.assertTrue(is_close(0.1 + 0.2, 0.3))
        self.assertEqual(sign(-4), -1)

unittest.main()
'''


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def fail(msg):
    print("FAIL: " + msg)
    return 1


def main():
    try:
        culprit = open("CULPRIT.txt", encoding="utf-8").read().strip().split()[0]
    except (OSError, IndexError):
        return fail("CULPRIT.txt missing or empty")
    resolved = git("rev-parse", "--verify", "--quiet", culprit + "^{commit}")
    if resolved.returncode != 0:
        return fail(f"CULPRIT.txt does not name a commit: {culprit!r}")
    if git("log", "-1", "--format=%s", resolved.stdout.strip()).stdout.strip() != CULPRIT_MESSAGE:
        return fail("CULPRIT.txt names the wrong commit")

    messages = git("log", "--format=%s", "main").stdout.strip().splitlines()
    if len(messages) != MAIN_MESSAGES or messages[0] != MAIN_TIP:
        return fail("main's history was changed")
    if BUG_LINE not in git("show", "main:calc.py").stdout:
        return fail("main was modified; the fix belongs on fix/distance")

    if git("rev-parse", "--verify", "--quiet", "fix/distance").returncode != 0:
        return fail("branch fix/distance not found")
    if git("merge-base", "--is-ancestor", "main", "fix/distance").returncode != 0:
        return fail("fix/distance does not start from main")
    ahead = git("rev-list", "--count", "main..fix/distance").stdout.strip()
    if not ahead.isdigit() or int(ahead) < 1:
        return fail("fix/distance has no new commit")

    d = tempfile.mkdtemp()
    try:
        with open(os.path.join(d, "calc.py"), "w") as fh:
            fh.write(git("show", "fix/distance:calc.py").stdout)
        with open(os.path.join(d, "t.py"), "w") as fh:
            fh.write(CALC_TEST)
        proc = subprocess.run([sys.executable, "t.py"], cwd=d, capture_output=True, text=True, timeout=60)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    if proc.returncode != 0:
        return fail("calc.py on fix/distance is still wrong\n" + proc.stderr[-800:])
    print(f"culprit found, main untouched, fix/distance is {ahead} commit(s) ahead and correct")
    return 0


if __name__ == "__main__":
    sys.exit(main())
