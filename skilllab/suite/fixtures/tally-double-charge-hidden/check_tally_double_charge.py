"""Checker for tally-double-charge: the list of double-charged orders must be exact (both log
files, voided charges excluded), and a retry after a timeout must never charge twice."""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, ".")
sys.path.insert(0, "tests")


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


class ChargesThenTimesOut:
    """Charges the card, then fails to answer `lost` times. De-duplicates by idempotency key."""

    def __init__(self, lost=1):
        self.lost = lost
        self.by_key, self.charges, self.keys = {}, [], []

    def capture(self, order_id, amount, idempotency_key):
        from tally.payments import GatewayTimeout
        self.keys.append(idempotency_key)
        if idempotency_key not in self.by_key:
            self.by_key[idempotency_key] = f"ch_{len(self.charges) + 1}"
            self.charges.append(order_id)
        if self.lost:
            self.lost -= 1
            raise GatewayTimeout()
        return self.by_key[idempotency_key]


def main():
    proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "tests"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        fail("the project's own tests fail:\n" + proc.stderr[-1500:])

    path = Path("DOUBLE_CHARGED.txt")
    if not path.is_file():
        fail("DOUBLE_CHARGED.txt not found")
    got = [l.strip() for l in path.read_text().splitlines() if l.strip()]
    want = json.loads(Path("expected_double_charged.json").read_text())
    if got != sorted(got):
        fail("DOUBLE_CHARGED.txt is not sorted")
    missing, extra = sorted(set(want) - set(got)), sorted(set(got) - set(want))
    if missing or extra:
        fail(f"DOUBLE_CHARGED.txt: {len(missing)} double-charged orders missing (e.g. {missing[:3]}), "
             f"{len(extra)} listed that aren't (e.g. {extra[:3]})")

    from helpers import order
    from tally.money import Money
    from tally.payments import PaymentFailed, capture_payment

    o1 = order("O1", "C1", "2026-03-01T10:00:00Z", ("HW-1", 1, "14.99"))
    o2 = order("O2", "C1", "2026-03-01T10:00:00Z", ("HW-1", 1, "14.99"))
    for lost in (1, 2):
        gw = ChargesThenTimesOut(lost)
        try:
            charge = capture_payment(gw, o1, Money.of("14.99", "EUR"), retries=3)
        except PaymentFailed:
            fail(f"gave up after {lost} lost answer(s) although retries=3")
        if len(gw.charges) != 1:
            fail(f"after {lost} lost answer(s) the card was charged {len(gw.charges)} times")
        if charge != "ch_1":
            fail("the returned charge id is not the one the gateway created")
    gw = ChargesThenTimesOut(0)
    capture_payment(gw, o1, Money.of("1", "EUR"))
    capture_payment(gw, o2, Money.of("1", "EUR"))
    if len(gw.charges) != 2:
        fail("two different orders must be two charges (idempotency keys must differ per order)")
    try:
        capture_payment(ChargesThenTimesOut(5), o1, Money.of("1", "EUR"), retries=3)
        fail("no PaymentFailed when the gateway never answers")
    except PaymentFailed:
        pass
    print(f"PASS: all {len(want)} double-charged orders found; retries can no longer charge twice")
    return 0


if __name__ == "__main__":
    sys.exit(main())
