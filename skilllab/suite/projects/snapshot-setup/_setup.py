"""Make the workspace a git repo holding the project snapshot as one commit, like a fresh checkout.
Fixed identity and dates, so hashes are the same in every run. No upstream history comes along,
so the commit that fixed the bug can't be looked up."""

import os
import subprocess
from pathlib import Path

ENV = dict(os.environ, GIT_AUTHOR_NAME="Dev", GIT_AUTHOR_EMAIL="dev@example.com",
           GIT_COMMITTER_NAME="Dev", GIT_COMMITTER_EMAIL="dev@example.com",
           GIT_AUTHOR_DATE="2026-10-01T09:00:00+00:00", GIT_COMMITTER_DATE="2026-10-01T09:00:00+00:00")


def git(*args):
    subprocess.run(["git", *args], check=True, env=ENV, capture_output=True)


git("init", "-q")
git("checkout", "-q", "-b", "main")
git("config", "user.name", "Dev")
git("config", "user.email", "dev@example.com")
Path(".git/info/exclude").write_text("/_setup.py\n")
git("add", "-A")
git("commit", "-q", "-m", "Current main")
