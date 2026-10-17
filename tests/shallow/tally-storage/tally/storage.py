"""JSON data files: one place for reading, version checks and crash-safe writes."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Optional

VERSION = 1


def load_document(path: Path, kind: str) -> Optional[dict]:
    """The parsed file, or None if it doesn't exist. `kind` names the file in errors."""
    path = Path(path)
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("version") != VERSION:
        raise ValueError(f"{path}: unsupported {kind} version {data.get('version')!r}")
    return data


def save_document(path: Path, kind: str, payload: dict) -> None:
    """Write {"version": 1, **payload} via a temp file in the same folder, moved into place.
    If anything fails, the old file is untouched and the temp file is removed."""
    path = Path(path)
    data = {"version": VERSION, **payload}
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{kind}-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
