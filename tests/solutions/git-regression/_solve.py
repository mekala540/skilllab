"""Reference solution: bisect to the culprit, then fix on a new branch."""

import subprocess


def git(*args, check=True):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=check).stdout.strip()


def broken(rev):
    src = git("show", f"{rev}:calc.py")
    scope = {}
    exec(src, scope)
    return scope["distance"](-5, -2) != 3


commits = git("rev-list", "--reverse", "main").splitlines()
culprit = next(c for c in commits if broken(c))
with open("CULPRIT.txt", "w") as fh:
    fh.write(culprit + "\n")

git("switch", "-q", "-c", "fix/distance")
with open("calc.py") as fh:
    src = fh.read()
src = src.replace("return a - b if a > b else b - a if b > 0 else a - b", "return abs(a - b)")
with open("calc.py", "w") as fh:
    fh.write(src)
git("commit", "-q", "-am", "Fix distance() for negative numbers")
