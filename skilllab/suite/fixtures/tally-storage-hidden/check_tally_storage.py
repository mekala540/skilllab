"""Checker for tally-storage: one storage module, same bytes on disk, same errors, and a failed
save leaves nothing behind."""

import ast
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, ".")
KINDS = [("tally.catalog", "Catalog", "catalog"), ("tally.customers", "CustomerBook", "customers"),
         ("tally.orders", "OrderBook", "orders"), ("tally.inventory", "Inventory", "inventory")]


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def file_handling(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [a.name for a in node.names if a.name in ("json", "tempfile")]
        elif isinstance(node, ast.ImportFrom) and node.module in ("json", "tempfile"):
            found.append(node.module)
        elif isinstance(node, ast.Attribute) and node.attr in ("replace", "fdopen", "mkstemp") and \
                isinstance(node.value, ast.Name) and node.value.id in ("os", "tempfile"):
            found.append(f"{node.value.id}.{node.attr}")
    return found


def main():
    proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "tests"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        fail("the project's own tests fail:\n" + proc.stderr[-1500:])
    if not Path("tally/storage.py").is_file():
        fail("tally/storage.py not found")
    for path in sorted(Path("tally").rglob("*.py")):
        if path.as_posix() == "tally/storage.py":
            continue
        found = file_handling(path)
        if found:
            fail(f"{path} still does its own JSON file handling ({', '.join(sorted(set(found)))})")

    import importlib
    tmp = Path(tempfile.mkdtemp())
    for mod, cls_name, kind in KINDS:
        cls = getattr(importlib.import_module(mod), cls_name)
        obj = cls.load(Path("data") / f"{kind}.json")
        out = tmp / f"{kind}.json"
        obj.save(out)
        if out.read_bytes() != Path("golden", f"{kind}.json").read_bytes():
            fail(f"{cls_name}.save() no longer writes the same file as before the refactor")
        if len(cls.load(tmp / "missing.json").__dict__[next(iter(cls().__dict__))]) != 0:
            fail(f"{cls_name}.load() of a missing file is not empty")
        bad = tmp / f"bad-{kind}.json"
        bad.write_text('{"version": 7}')
        try:
            cls.load(bad)
            fail(f"{cls_name}.load() accepted version 7")
        except ValueError as exc:
            if str(exc) != f"{bad}: unsupported {kind} version 7":
                fail(f"{cls_name}.load() error message changed: {exc}")
        target = tmp / f"dir-{kind}"
        target.mkdir()
        before = set(os.listdir(tmp))
        try:
            obj.save(target)  # the final move fails: the target is a folder
            fail(f"{cls_name}.save() onto a folder did not raise")
        except OSError:
            pass
        leftovers = set(os.listdir(tmp)) - before
        if leftovers:
            fail(f"a failed {cls_name}.save() left a temp file behind: {sorted(leftovers)}")
        if not target.is_dir():
            fail("a failed save destroyed the existing target")
    print("PASS: storage in one module, files byte-identical, errors unchanged, failed saves clean up")
    return 0


if __name__ == "__main__":
    sys.exit(main())
