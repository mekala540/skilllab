"""Build a 30-commit git history in the workspace. Commit 19 quietly breaks distance()
for negative inputs; nothing in the repo's tests covers that, which is how it slipped in."""

import os
import subprocess

ENV = dict(os.environ, GIT_AUTHOR_NAME="Dev", GIT_AUTHOR_EMAIL="dev@example.com",
           GIT_COMMITTER_NAME="Dev", GIT_COMMITTER_EMAIL="dev@example.com")


def git(*args, date=None):
    env = dict(ENV)
    if date:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = date
    subprocess.run(["git", *args], check=True, capture_output=True, env=env)


HEADER = '"""Small numeric helpers."""\n\n'
GOOD = "def distance(a, b):\n    \"\"\"Absolute distance between two numbers.\"\"\"\n    return abs(a - b)\n"
BAD = "def distance(a, b):\n    \"\"\"Absolute distance between two numbers.\"\"\"\n    return a - b if a > b else b - a if b > 0 else a - b\n"
HELPERS = [
    ("clamp", "def clamp(x, lo, hi):\n    return max(lo, min(hi, x))\n"),
    ("sign", "def sign(x):\n    return (x > 0) - (x < 0)\n"),
    ("mean", "def mean(xs):\n    return sum(xs) / len(xs)\n"),
    ("lerp", "def lerp(a, b, t):\n    return a + (b - a) * t\n"),
    ("is_close", "def is_close(a, b, tol=1e-9):\n    return abs(a - b) <= tol\n"),
    ("median", "def median(xs):\n    s = sorted(xs)\n    n = len(s)\n    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2\n"),
    ("span", "def span(xs):\n    return max(xs) - min(xs)\n"),
    ("total", "def total(xs):\n    return sum(xs)\n"),
]
MESSAGES = [
    "Add calc module", "Add tests", "Add clamp", "Docs: describe calc", "Add sign",
    "Tidy imports", "Add mean", "Add lerp", "Tests for clamp", "Add is_close",
    "Docs: usage examples", "Add median", "Tests for median", "Reformat calc", "Add span",
    "Docs: changelog", "Tests for span", "Add total", "Tidy helpers", "Tests for total",
    "Docs: contributing", "Rename test file sections", "Tidy docstrings", "Docs: badges",
    "Tests: more mean cases", "Docs: FAQ", "Tidy whitespace", "Docs: release notes",
    "Tests: lerp", "Bump version",
]
TESTS = '''import unittest

from calc import clamp, distance, mean


class TestCalc(unittest.TestCase):
    def test_distance(self):
        self.assertEqual(distance(3, 10), 7)
        self.assertEqual(distance(10, 3), 7)

    def test_clamp(self):
        self.assertEqual(clamp(5, 0, 3), 3)

    def test_mean(self):
        self.assertEqual(mean([1, 2, 3]), 2)


if __name__ == "__main__":
    unittest.main()
'''


def main():
    if os.path.exists(".gitkeep"):
        os.remove(".gitkeep")  # placeholder so the empty fixture folder survives in git
    git("init", "-q", "-b", "main")
    git("config", "user.name", "Dev")
    git("config", "user.email", "dev@example.com")
    helpers_added = 0
    docs = ["# calc\n"]
    for i, message in enumerate(MESSAGES, 1):
        broken = i >= 19
        if message.startswith("Add ") and message != "Add calc module" and message != "Add tests":
            helpers_added += 1
        body = HEADER + (BAD if broken else GOOD) + "".join(
            "\n\n" + code for _, code in HELPERS[:helpers_added])
        with open("calc.py", "w") as fh:
            fh.write(body)
        if i >= 2:
            with open("test_calc.py", "w") as fh:
                fh.write(TESTS)
        if message.startswith("Docs") or message.startswith("Tidy") or message.startswith("Bump"):
            docs.append(f"\n- {message}\n")
        with open("README.md", "w") as fh:
            fh.write("".join(docs))
        with open("HISTORY.txt", "a") as fh:
            fh.write(f"{i:02d} {message}\n")
        git("add", "-A")
        git("commit", "-q", "-m", message, date=f"2024-01-{i:02d}T12:00:00")


main()
