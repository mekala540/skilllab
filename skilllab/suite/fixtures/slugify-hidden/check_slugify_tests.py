"""Mutation check: the agent's tests must pass on slugify.py and fail on every broken copy."""

import os
import shutil
import subprocess
import sys
import tempfile

MUTANTS = {
    "keeps accents": ('text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")', "pass"),
    "no lowercase": ("text = text.lower()", "pass"),
    "no run collapsing": ('r"[^a-z0-9]+"', 'r"[^a-z0-9]"'),
    "trailing separator after cut": ("text[:max_length].rstrip(separator)", "text[:max_length]"),
    "ignores separator": ('re.sub(r"[^a-z0-9]+", separator, text)', 're.sub(r"[^a-z0-9]+", "-", text)'),
    "off-by-one length": ("text[:max_length]", "text[:max_length - 1]"),
    "accepts max_length 0": ("if max_length < 1:", "if max_length < 0:"),
}


def run_tests(source):
    d = tempfile.mkdtemp()
    try:
        with open(os.path.join(d, "slugify.py"), "w", encoding="utf-8") as fh:
            fh.write(source)
        shutil.copytree("tests", os.path.join(d, "tests"))
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=d, capture_output=True, text=True, timeout=120,
        )
        out = proc.stdout + proc.stderr
        return proc.returncode == 0 and "Ran 0 tests" not in out, out
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    if not os.path.isfile(os.path.join("tests", "test_slugify.py")):
        print("FAIL: tests/test_slugify.py not found")
        return 1
    original = open("slugify.py", encoding="utf-8").read()
    ok, out = run_tests(original)
    if not ok:
        print("FAIL: tests do not pass on the correct implementation\n" + out[-1500:])
        return 1
    survived = []
    for name, (old, new) in MUTANTS.items():
        assert old in original, name
        passed, _ = run_tests(original.replace(old, new, 1))
        if passed:
            survived.append(name)
    killed = len(MUTANTS) - len(survived)
    print(f"killed {killed}/{len(MUTANTS)} mutants" + (f"; survived: {', '.join(survived)}" if survived else ""))
    return 0 if not survived else 1


if __name__ == "__main__":
    sys.exit(main())
