"""Small text-formatting helpers shared by the user-facing messages.

Stdlib only; layer L0 (``tests/test_import_layers.py``).
"""

from __future__ import annotations

from typing import Optional

__all__ = ["plural"]


def plural(count: int, singular: str, plural: Optional[str] = None) -> str:
    """``<count> <noun>``, the noun plural unless *count* is 1: ``1 file``,
    ``2 files``; *plural* names an irregular form (``2 batches``)."""
    return f"{count} {singular if count == 1 else (plural or singular + 's')}"
