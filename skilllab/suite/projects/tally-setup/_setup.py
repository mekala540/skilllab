"""Make the workspace a git repo with the project committed, the way a real checkout looks.
Dates and identity are fixed so every workspace has the same commit hashes."""

import os
import subprocess

ENV = dict(os.environ, GIT_AUTHOR_NAME="Tally Dev", GIT_AUTHOR_EMAIL="dev@tally.example",
           GIT_COMMITTER_NAME="Tally Dev", GIT_COMMITTER_EMAIL="dev@tally.example",
           GIT_AUTHOR_DATE="2026-03-02T09:00:00+00:00", GIT_COMMITTER_DATE="2026-03-02T09:00:00+00:00")


def git(*args):
    subprocess.run(["git", *args], check=True, env=ENV, capture_output=True)


git("init", "-q")
git("checkout", "-q", "-b", "main")
git("config", "user.name", "Tally Dev")
git("config", "user.email", "dev@tally.example")
for name in os.listdir("."):
    if name.startswith("_setup"):
        os.remove(name)
git("add", "-A")
git("commit", "-q", "-m", "tally 2.4.1")
