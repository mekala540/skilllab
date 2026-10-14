"""Refactor check for pricing.py.

1. Same results as the original over long random sequences of calls, including the hidden
   per-customer loyalty counter, the "same as last" flag, reset(), and every exception's
   type and message.
2. No `global` statements, no function body over 15 lines, at least 5 functions.
"""

import ast
import importlib
import random
import sys

MAX_BODY = 15
MIN_FUNCS = 5


def outcome(mod, call):
    name, args = call
    try:
        return ("ok", getattr(mod, name)(*args))
    except Exception as exc:  # noqa: BLE001 - comparing behavior, errors included
        return ("raises", type(exc).__name__, str(exc))


def random_call(rng):
    if rng.random() < 0.03:
        return ("reset", ())
    customer = {"id": rng.choice(["c1", "c2", "c3", "c4"]),
                "tier": rng.choice(["basic", "gold", "platinum", "platinum", "silver"] if rng.random() < 0.1
                                   else ["basic", "gold", "platinum"]),
                "country": rng.choice(["US", "DE", "FR", "JP", "BR"])}
    if rng.random() < 0.05:
        del customer["country"]
    skus = ["A100", "B200", "C300", "D400", "E500"] + (["Z999"] if rng.random() < 0.05 else [])
    items = [(rng.choice(skus), rng.choice([1, 2, 4, 5, 6, 9, 10, 12] + ([0, -1] if rng.random() < 0.05 else [])))
             for _ in range(rng.randint(0, 4) if rng.random() < 0.05 else rng.randint(1, 4))]
    day = rng.choice(range(7)) if rng.random() > 0.03 else rng.choice([-1, 7])
    return ("quote", (customer, items, day))


def behavior_ok():
    import pricing
    import pricing_reference
    for seed in range(4):
        importlib.reload(pricing)
        importlib.reload(pricing_reference)
        rng = random.Random(seed)
        for i in range(2500):
            call = random_call(rng)
            want, got = outcome(pricing_reference, call), outcome(pricing, call)
            if want != got:
                print(f"FAIL: seed {seed} call {i} {call}: expected {want}, got {got}")
                return False
    return True


def structure_ok():
    tree = ast.parse(open("pricing.py", encoding="utf-8").read())
    if any(isinstance(n, ast.Global) for n in ast.walk(tree)):
        print("FAIL: `global` statements remain")
        return False
    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if len(funcs) < MIN_FUNCS:
        print(f"FAIL: {len(funcs)} functions; expected at least {MIN_FUNCS}")
        return False
    for f in funcs:
        body = f.body
        if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
            body = body[1:]
        if body and body[-1].end_lineno - body[0].lineno + 1 > MAX_BODY:
            print(f"FAIL: {f.name} body is longer than {MAX_BODY} lines")
            return False
    if not any(f.name == "quote" for f in funcs) or not any(f.name == "reset" for f in funcs):
        print("FAIL: quote() and reset() must stay")
        return False
    print(f"{len(funcs)} functions, no globals, all bodies <= {MAX_BODY} lines")
    return True


if __name__ == "__main__":
    sys.exit(0 if behavior_ok() and structure_ok() else 1)
