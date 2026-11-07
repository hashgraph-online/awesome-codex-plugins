"""Shared stdlib-only helpers for the onekgpd scripts (no third-party imports)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from typing import Any, NoReturn


def _fail(msg: str) -> NoReturn:
    """Print a clean one-line message to stderr and exit non-zero."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def _split_csv(s: str) -> list[str]:
    """Split a comma-separated value into a list of non-empty trimmed tokens."""
    return [part.strip() for part in s.split(",") if part.strip()]


def _save_json(data: Any, prefix: str, output_path: str | None = None) -> str:
    """Write *data* as indented JSON to *output_path* or a temp file; return path."""
    if output_path:
        path = output_path
        with open(path, "w") as fh:
            json.dump(data, fh, indent=2)
    else:
        fd, path = tempfile.mkstemp(prefix=f"onekgpd_{prefix}_", suffix=".json", text=True)
        with os.fdopen(fd, "w") as fh:
            json.dump(data, fh, indent=2)
    return path


def _emit(data: Any, prefix: str, summary_lines: list[str], output: str | None) -> None:
    """Save full JSON to a file and print the summary + saved-path line to stdout."""
    path = _save_json(data, prefix, output)
    for line in summary_lines:
        print(line)
    print(f"[*] Full JSON saved to {path}")
