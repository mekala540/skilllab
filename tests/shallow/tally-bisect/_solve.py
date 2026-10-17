# Plausible but wrong: right culprit and fix, but committed straight onto main.
import subprocess
from pathlib import Path


def git(*a):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], check=True,
                          capture_output=True, text=True).stdout


h = [l.split()[0] for l in git("log", "--format=%H %s").splitlines() if l.endswith("tidy discount tables")][0]
Path("CULPRIT.txt").write_text(h + "\n")
p = Path("tally/discounts.py")
p.write_text(p.read_text().replace("if qty > threshold:", "if qty >= threshold:"))
git("commit", "-q", "-am", "Fix volume threshold")
git("branch", "fix/volume-threshold")
