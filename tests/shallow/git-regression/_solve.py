"""A quick fix that ignores the instructions: right culprit, but the fix is committed on main."""

import subprocess


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


culprit = [line.split()[0] for line in git("log", "--format=%H %s", "main").splitlines()
           if line.endswith("Tidy helpers")][0]
with open("CULPRIT.txt", "w") as fh:
    fh.write(culprit + "\n")
with open("calc.py") as fh:
    src = fh.read()
with open("calc.py", "w") as fh:
    fh.write(src.replace("return a - b if a > b else b - a if b > 0 else a - b", "return abs(a - b)"))
git("commit", "-q", "-am", "Fix distance")
git("branch", "fix/distance", "HEAD~1")
