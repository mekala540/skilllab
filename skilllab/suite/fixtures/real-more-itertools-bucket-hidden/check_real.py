"""Checker for real-tier tasks: the tests that came with the upstream fix must pass, and so must
the project's whole test suite. The upstream test files are taken from the cached repository at
the fix commit and written over the workspace's copies, so the agent can't have edited them."""

import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def main():
    spec = json.loads(Path("real_check.json").read_text())
    gitdir = os.environ.get("SKILLLAB_REPO_GIT")
    if not gitdir:
        fail("SKILLLAB_REPO_GIT not set (run through skilllab)")
    for path in spec["test_files"]:
        blob = subprocess.run(["git", "--git-dir", gitdir, "show", f"{spec['fix']}:{path}"], capture_output=True)
        if blob.returncode != 0:
            fail(f"could not read {path} at the fix commit")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(blob.stdout)
    for conftest in spec.get("conftests", []):
        blob = subprocess.run(["git", "--git-dir", gitdir, "show", f"{spec['fix']}:{conftest}"], capture_output=True)
        if blob.returncode == 0:
            Path(conftest).write_bytes(blob.stdout)

    report = Path(tempfile.mkdtemp()) / "junit.xml"
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-W", "ignore::DeprecationWarning",
           f"--junitxml={report}", *spec.get("pytest_args", []), *spec["suite"]]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    out = proc.stdout.strip().splitlines()
    if not report.exists():
        fail("pytest did not run: " + " ".join(out[-3:]))
    # junit classname comes from the test id: tests/test_x.py::Cls::test -> tests.test_x.Cls
    results = {}
    for case in ET.parse(report).getroot().iter("testcase"):
        status = "passed"
        for child in case:
            if child.tag in ("failure", "error"):
                status = "failed"
            elif child.tag == "skipped":
                status = "skipped"
        results[(case.get("classname", ""), case.get("name", "").split("[")[0])] = \
            results.get((case.get("classname", ""), case.get("name", "").split("[")[0]), []) + [status]
    for test_id in spec["must_pass"]:
        parts = test_id.split("::")
        key = (".".join([parts[0][:-3].replace("/", ".")] + parts[1:-1]), parts[-1].split("[")[0])
        statuses = results.get(key)
        if not statuses:
            fail(f"{test_id} did not run")
        bad = [x for x in statuses if x != "passed"]
        if bad:
            fail(f"{test_id} {bad[0]}: the reported bug isn't fixed")
    if proc.returncode != 0:
        failed = [k for k, s in results.items() if s == "failed"]
        fail(f"{len(failed)} other tests fail, e.g. {failed[:3]}" if failed else "pytest failed: " + " ".join(out[-3:]))
    print(f"PASS: the fix's tests pass and the whole suite passes ({out[-1] if out else ''})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
