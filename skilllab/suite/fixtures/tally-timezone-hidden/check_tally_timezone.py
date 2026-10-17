"""Checker for tally-timezone. Reports must not depend on the machine's time zone: the same
data and --tz must give the same days and hours on a laptop in Mumbai, London or Los Angeles."""

import json
import os
import subprocess
import sys

PROBE = r'''
import json, sys, warnings
warnings.simplefilter("ignore")
sys.path.insert(0, ".")
from pathlib import Path
from tally.catalog import Catalog
from tally.customers import CustomerBook
from tally.orders import OrderBook
from tally.reports import busiest_hours, daily_sales
d = Path("data")
cat, cust, orders = Catalog.load(d / "catalog.json"), CustomerBook.load(d / "customers.json"), OrderBook.load(d / "orders.json")
out = {}
for off in ("+05:30", "-08:00", "+00:00", "+09:00"):
    out[off] = {"daily": {k: str(v.amount) for k, v in daily_sales(orders, cat, cust, off).items()},
                "hours": {str(h): n for h, n in busiest_hours(orders, off).items()}}
print(json.dumps(out))
'''


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def main():
    expected = json.load(open("expected_reports.json"))
    for off in expected:
        expected[off]["hours"] = {str(h): n for h, n in expected[off]["hours"].items()}
    for zone in ("Asia/Kolkata", "Europe/London", "America/Los_Angeles", "UTC"):
        env = dict(os.environ, TZ=zone)
        tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "tests"],
                               capture_output=True, text=True, env=env)
        if tests.returncode != 0:
            fail(f"the project's tests fail on a machine in {zone}:\n{tests.stderr[-1200:]}")
        proc = subprocess.run([sys.executable, "-c", PROBE], capture_output=True, text=True, env=env)
        if proc.returncode != 0:
            fail(f"reports crashed on a machine in {zone}: {proc.stderr[-600:]}")
        got = json.loads(proc.stdout)
        for off, want in expected.items():
            if got[off]["daily"] != want["daily"]:
                fail(f"daily report with --tz {off} is wrong on a machine in {zone}")
            if got[off]["hours"] != want["hours"]:
                fail(f"busiest-hours report with --tz {off} is wrong on a machine in {zone}")
    print("PASS: daily and hourly reports are the same on machines in four time zones")
    return 0


if __name__ == "__main__":
    sys.exit(main())
