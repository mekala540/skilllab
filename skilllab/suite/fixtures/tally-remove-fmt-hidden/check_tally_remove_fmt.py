"""Checker for tally-remove-fmt: fmt() is gone, nobody calls it, output is byte-identical,
and nothing raises a DeprecationWarning any more."""

import ast
import subprocess
import sys
from pathlib import Path

COMMANDS = {f"invoice-{o}.txt": ["invoice", o] for o in ("O00007", "O00269", "O00010", "O00100", "O00334")}
COMMANDS["daily.txt"] = ["report", "daily", "--tz", "+01:00"]
COMMANDS["countries.txt"] = ["report", "countries"]


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def main():
    tests = subprocess.run([sys.executable, "-W", "error::DeprecationWarning", "-m", "unittest", "discover",
                            "-s", "tests", "-t", "tests"], capture_output=True, text=True)
    if tests.returncode != 0:
        fail("tests fail (deprecation warnings are errors here):\n" + tests.stderr[-1500:])
    for path in sorted(list(Path("tally").rglob("*.py")) + list(Path("tests").rglob("*.py"))):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "fmt":
                fail(f"{path} still defines fmt()")
            if isinstance(node, ast.Name) and node.id == "fmt":
                fail(f"{path}:{node.lineno} still uses fmt")
            if isinstance(node, ast.Attribute) and node.attr == "fmt":
                fail(f"{path}:{node.lineno} still uses .fmt")
            if isinstance(node, ast.ImportFrom) and any(a.name == "fmt" for a in node.names):
                fail(f"{path}:{node.lineno} still imports fmt")
    for name, argv in COMMANDS.items():
        proc = subprocess.run([sys.executable, "-W", "error::DeprecationWarning", "-m", "tally", *argv],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            fail(f"`tally {' '.join(argv)}` failed: {proc.stderr[-400:]}")
        if proc.stdout != Path("golden", name).read_text(encoding="utf-8"):
            fail(f"`tally {' '.join(argv)}` output changed")
    print("PASS: fmt() removed, every caller migrated, output identical")
    return 0


if __name__ == "__main__":
    sys.exit(main())
