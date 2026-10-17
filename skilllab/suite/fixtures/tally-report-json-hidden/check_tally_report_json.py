"""Checker for tally-report-json: hidden spec tests plus the project's own tests."""

import subprocess
import sys
from pathlib import Path


def main():
    own = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "tests"],
                         capture_output=True, text=True)
    if own.returncode != 0:
        print("FAIL: the project's own tests fail:\n" + own.stderr[-1500:])
        return 1
    hidden = subprocess.run([sys.executable, "-m", "unittest", "hidden_test_report_json"], capture_output=True, text=True)
    tail = hidden.stderr.strip().splitlines()
    if hidden.returncode != 0:
        print("\n".join(tail[-40:]))
        failed = [l.split(" ", 1)[1].split(" ")[0] for l in tail if l.startswith(("FAIL: ", "ERROR: "))]
        why = next((l for l in reversed(tail) if l.startswith(("AssertionError", "Error", "Exception"))), "")
        print(f"FAIL: spec tests fail: {', '.join(failed)}" + (f" ({why[:200]})" if why else ""))
        return 1
    print("PASS: " + (tail[-3] if len(tail) >= 3 else "spec tests pass"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
