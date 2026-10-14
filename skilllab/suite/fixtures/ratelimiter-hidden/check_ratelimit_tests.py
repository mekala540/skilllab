"""Mutation check: the agent's tests must pass on ratelimit.py and fail on every broken copy."""

import os
import shutil
import subprocess
import sys
import tempfile

MUTANTS = {
    "starts empty": ("self.tokens = float(capacity)", "self.tokens = 0.0"),
    "no capacity cap": ("min(self.capacity, self.tokens + elapsed * self.rate)", "self.tokens + elapsed * self.rate"),
    "exact tokens refused": ("if self.tokens >= cost:", "if self.tokens > cost:"),
    "failed allow still takes": ("            self.tokens -= cost\n            return True\n        return False",
                                 "            self.tokens -= cost\n            return True\n        self.tokens -= cost\n        return False"),
    "zero cost accepted": ("if cost <= 0:\n            raise ValueError(\"cost must be > 0\")", "if cost < 0:\n            raise ValueError(\"cost must be > 0\")"),
    "cost above capacity accepted": ("if cost > self.capacity:", "if cost > self.capacity + 1:"),
    "zero capacity accepted": ("if capacity <= 0:", "if capacity < 0:"),
    "zero rate accepted": ("if rate <= 0:", "if rate < 0:"),
    "clock backwards removes tokens": ("        if elapsed > 0:\n            self.tokens = min(", "        if True:\n            self.tokens = min("),
    "clock backwards double counts": ("self.last = max(self.last, now)", "self.last = now"),
    "wait_time scales wrong": ("return deficit / self.rate", "return deficit * self.rate"),
    "wait_time ignores refill": ("        self._check_cost(cost)\n        self._refill()\n        deficit",
                                 "        self._check_cost(cost)\n        deficit"),
}


def run_tests(source):
    d = tempfile.mkdtemp()
    try:
        with open(os.path.join(d, "ratelimit.py"), "w", encoding="utf-8") as fh:
            fh.write(source)
        shutil.copytree("tests", os.path.join(d, "tests"))
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=d, capture_output=True, text=True, timeout=120,
        )
        out = proc.stdout + proc.stderr
        return proc.returncode == 0 and "Ran 0 tests" not in out, out
    except subprocess.TimeoutExpired:
        return False, "timeout"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    if not os.path.isfile(os.path.join("tests", "test_ratelimit.py")):
        print("FAIL: tests/test_ratelimit.py not found")
        return 1
    original = open("ratelimit.py", encoding="utf-8").read()
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
    print(f"killed {len(MUTANTS) - len(survived)}/{len(MUTANTS)} mutants"
          + (f"; survived: {', '.join(survived)}" if survived else ""))
    return 0 if not survived else 1


if __name__ == "__main__":
    sys.exit(main())
