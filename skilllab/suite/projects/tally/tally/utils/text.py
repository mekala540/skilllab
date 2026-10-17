"""Small text helpers for reports and invoices."""

from __future__ import annotations


def truncate(text: str, width: int) -> str:
    if width < 1:
        raise ValueError("width must be at least 1")
    return text if len(text) <= width else text[: width - 1] + "…"


def pad_columns(rows, widths, align=None) -> str:
    """Fixed-width table. align: 'l' or 'r' per column (default left)."""
    align = align or ["l"] * len(widths)
    out = []
    for row in rows:
        cells = []
        for cell, width, a in zip(row, widths, align):
            cell = truncate(str(cell), width)
            cells.append(cell.rjust(width) if a == "r" else cell.ljust(width))
        out.append("  ".join(cells).rstrip())
    return "\n".join(out)
