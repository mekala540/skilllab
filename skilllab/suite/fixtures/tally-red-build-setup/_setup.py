"""Two commits: the released 2.4.1, then the '2.5 prep' commit that the agent has to clean up."""

import os
import shutil
import subprocess
from pathlib import Path

ENV = dict(os.environ, GIT_AUTHOR_NAME="Tally Dev", GIT_AUTHOR_EMAIL="dev@tally.example",
           GIT_COMMITTER_NAME="Tally Dev", GIT_COMMITTER_EMAIL="dev@tally.example")


def git(*args, date="2026-03-02T09:00:00+00:00"):
    env = dict(ENV, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    subprocess.run(["git", *args], check=True, env=env, capture_output=True)


base = Path("_base")
changed = [p.relative_to(base) for p in base.rglob("*") if p.is_file()]
hold = Path("_hold")
for rel in changed:
    (hold / rel).parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(rel), str(hold / rel))
    shutil.copy2(str(base / rel), str(rel))
git("init", "-q")
git("checkout", "-q", "-b", "main")
git("config", "user.name", "Tally Dev")
git("config", "user.email", "dev@tally.example")
# Setup files (_setup.py, _base, _hold) are removed after setup; keep them out of history.
Path(".git/info/exclude").write_text("/_*\n")
git("add", "-A")
git("commit", "-q", "-m", "tally 2.4.1")
for rel in changed:
    shutil.copy2(str(hold / rel), str(rel))
shutil.rmtree(hold)
git("add", "-A")
git("commit", "-q", "-m", "Prepare 2.5: accept more UTC offset formats, faster number formatting, "
    "tidy model constructors, simplify cancel", date="2026-03-05T16:20:00+00:00")
