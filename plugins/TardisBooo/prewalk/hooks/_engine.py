"""Resolve the vendored ``prewalk_engine`` package for this install layout.

Every Codex hook and helper imports this module *before* importing the
engine. Why the indirection: the Codex marketplace installs only the plugin
subtree (``hosts/codex/``), so each host carries its own byte-identical copy
of the package under ``hooks/prewalk_engine/`` — and loose installs, dev
checkouts, and plugin sandboxes each put that directory somewhere slightly
different.

Resolution order:

1. ``$PREWALK_ENGINE`` — a directory containing ``prewalk_engine/`` (tests
   and unusual layouts);
2. this script's own directory — the normal vendored case, because the
   package sits next to the hooks;
3. a short upward walk, for checkouts that run hooks from the repo root.

Usage at the top of a script, before importing the engine::

    import _engine  # noqa: F401  (locates the package; no symbol needed)
    import prewalk_engine as core
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_PACKAGE = "prewalk_engine"


def _holds_package(directory: Path) -> bool:
    try:
        return (directory / _PACKAGE / "__init__.py").is_file()
    except OSError:
        return False


def _add(directory: Path) -> bool:
    path = str(directory)
    if path not in sys.path:
        sys.path.insert(0, path)
    return True


def _locate_engine() -> None:
    override = os.environ.get("PREWALK_ENGINE")
    if override and _holds_package(Path(override)):
        _add(Path(override))
        return

    here = Path(__file__).resolve().parent
    if _holds_package(here):
        _add(here)
        return

    node = here
    for _ in range(5):
        if node.parent == node:
            break
        node = node.parent
        if _holds_package(node):
            _add(node)
            return


_locate_engine()
