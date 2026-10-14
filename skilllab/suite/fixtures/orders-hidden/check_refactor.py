"""Refactor check: same results as the original on random orders, and actually split up."""

import ast
import random
import sys

import orders
import orders_reference

MAX_BODY_LINES = 12
MIN_HELPERS = 3


def outcome(fn, order):
    try:
        return ("ok", fn(order))
    except Exception as exc:  # noqa: BLE001 - comparing behavior, including errors
        return ("raises", type(exc).__name__)


def random_order(rng):
    items = [
        {"price": rng.choice([0, 199, 999, 2500, 4999, 12000]),
         "qty": rng.choice([0, 1, 1, 2, 3, 4, 7]) if rng.random() < 0.97 else -1,
         "category": rng.choice(["books", "electronics", "toys", "food"])}
        for _ in range(rng.randint(0, 5))
    ]
    order = {"items": items, "country": rng.choice(["US", "CA", "FR", "JP"])}
    if rng.random() < 0.8:
        order["coupon"] = rng.choice([None, "", "SAVE10", "HALF", "BOGUS"])
    if rng.random() < 0.8:
        order["member"] = rng.choice([True, False])
    return order


def main():
    rng = random.Random(1234)
    for i in range(5000):
        order = random_order(rng)
        want, got = outcome(orders_reference.process_order, order), outcome(orders.process_order, order)
        if want != got:
            print(f"FAIL: behavior changed for {order}: expected {want}, got {got}")
            return 1

    tree = ast.parse(open("orders.py", encoding="utf-8").read())
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    main_fn = funcs.get("process_order")
    if main_fn is None:
        print("FAIL: process_order is gone")
        return 1
    body = main_fn.body
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
        body = body[1:]  # skip docstring
    lines = (body[-1].end_lineno - body[0].lineno + 1) if body else 0
    helpers = len(funcs) - 1
    print(f"process_order body: {lines} lines, {helpers} helper functions")
    if lines > MAX_BODY_LINES:
        print(f"FAIL: process_order body is longer than {MAX_BODY_LINES} lines")
        return 1
    if helpers < MIN_HELPERS:
        print(f"FAIL: expected at least {MIN_HELPERS} helper functions")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
