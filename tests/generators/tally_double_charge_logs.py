"""Generate logs/payments.log.1 (older) and logs/payments.log for tally-double-charge, plus the
expected answer. Deterministic. Run from the repo root:

    python3 tests/generators/tally_double_charge_logs.py skilllab/suite/fixtures/tally-double-charge skilllab/suite/fixtures/tally-double-charge-hidden
"""
import json, random, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
F = Path(sys.argv[1]); H = Path(sys.argv[2])
rng = random.Random(9)
start = datetime(2026, 3, 9, 6, 0, tzinfo=timezone.utc)
lines = []  # (time, text)
def ts(t): return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"
def add(t, level, svc, msg): lines.append((t, f"{ts(t)} {level:<5} {svc} {msg}"))
charge_n = [1000]
def new_charge():
    charge_n[0] += rng.randrange(1, 9); return f"ch_{charge_n[0]:06x}"
double, single = set(), set()
t = start
for i in range(1, 1300):
    t = t + timedelta(seconds=rng.randrange(60, 520), milliseconds=rng.randrange(0, 1000))
    oid = f"O{20000 + i:05d}"
    amount = f"{rng.randrange(500, 40000) / 100:.2f}"
    kind = rng.random()
    tt = t
    def req(a, key): add(tt, "INFO", "tally.payments", f"order={oid} attempt={a} key={key} event=capture.request amount={amount} EUR")
    if kind < 0.80:                       # plain success
        req(1, f"{oid}-1"); ch = new_charge()
        tt += timedelta(milliseconds=rng.randrange(300, 1800))
        add(tt, "INFO", "tally.payments", f"order={oid} attempt=1 key={oid}-1 event=capture.ok charge={ch}")
        add(tt + timedelta(seconds=rng.randrange(1, 40)), "INFO", "gateway.webhook", f"event=charge.succeeded charge={ch} order={oid} amount={amount} EUR")
        if rng.random() < 0.04:
            add(tt + timedelta(hours=rng.randrange(2, 30)), "INFO", "gateway.webhook", f"event=charge.refunded charge={ch} order={oid} amount={amount} EUR")
    elif kind < 0.90:                     # timeout, gateway did NOT charge, retry ok -> single
        req(1, f"{oid}-1"); tt += timedelta(seconds=10)
        add(tt, "WARN", "tally.payments", f"order={oid} attempt=1 key={oid}-1 event=capture.timeout")
        req(2, f"{oid}-2"); ch = new_charge(); tt += timedelta(milliseconds=900)
        add(tt, "INFO", "tally.payments", f"order={oid} attempt=2 key={oid}-2 event=capture.ok charge={ch}")
        add(tt + timedelta(seconds=rng.randrange(1, 40)), "INFO", "gateway.webhook", f"event=charge.succeeded charge={ch} order={oid} amount={amount} EUR")
    else:                                 # timeout but the gateway DID charge -> two charges
        req(1, f"{oid}-1"); ch1 = new_charge(); tt += timedelta(seconds=10)
        add(tt, "WARN", "tally.payments", f"order={oid} attempt=1 key={oid}-1 event=capture.timeout")
        add(tt + timedelta(seconds=rng.randrange(20, 90)), "INFO", "gateway.webhook", f"event=charge.succeeded charge={ch1} order={oid} amount={amount} EUR")
        n = 2
        if rng.random() < 0.3:            # two timeouts, third works
            req(2, f"{oid}-2"); tt += timedelta(seconds=10)
            add(tt, "WARN", "tally.payments", f"order={oid} attempt=2 key={oid}-2 event=capture.timeout"); n = 3
        req(n, f"{oid}-{n}"); ch2 = new_charge(); tt += timedelta(milliseconds=800)
        add(tt, "INFO", "tally.payments", f"order={oid} attempt={n} key={oid}-{n} event=capture.ok charge={ch2}")
        add(tt + timedelta(seconds=rng.randrange(1, 40)), "INFO", "gateway.webhook", f"event=charge.succeeded charge={ch2} order={oid} amount={amount} EUR")
        if rng.random() < 0.35:           # support already voided the extra charge
            add(tt + timedelta(hours=rng.randrange(1, 20)), "INFO", "gateway.webhook", f"event=charge.voided charge={ch1} order={oid} amount={amount} EUR reason=duplicate")
            single.add(oid)
        else:
            double.add(oid)
    # noise from other services
    for _ in range(rng.randrange(0, 4)):
        nt = t + timedelta(seconds=rng.randrange(0, 300))
        add(nt, rng.choice(["INFO", "DEBUG", "DEBUG"]), rng.choice(["tally.inventory", "tally.mailer", "tally.http"]),
            rng.choice([f"sku=HW-300{rng.randrange(1,5)} event=reserve qty={rng.randrange(1,9)}",
                        f"to=customer@example.com template=order_confirmation order={oid}",
                        f"GET /orders/{oid} 200 {rng.randrange(3,90)}ms", "pool=db size=8 idle=6"]))
    if rng.random() < 0.01:
        nt = t + timedelta(seconds=5)
        add(nt, "ERROR", "tally.http", f"unhandled error on POST /orders/{oid}/notes\nTraceback (most recent call last):\n  File \"tally/http.py\", line 88, in post_note\n    note = body[\"text\"]\nKeyError: 'text'")
lines.sort(key=lambda x: x[0])
cut = start + timedelta(days=3)
old = [l for tm, l in lines if tm < cut]; new = [l for tm, l in lines if tm >= cut]
(F / "logs" / "payments.log.1").write_text("\n".join(old) + "\n")
(F / "logs" / "payments.log").write_text("\n".join(new) + "\n")
(H / "expected_double_charged.json").write_text(json.dumps(sorted(double)))
print(len(old), len(new), "double", len(double), "voided", len(single), "in old file", sum(1 for o in double if any(o in l and 'succeeded' in l for l in old)))
