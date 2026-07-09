"""Atomic writer for source-index JSON output."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def fsync_directory(path: Path) -> None:
    if os.name != "posix":
        return
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(data, indent=2, sort_keys=False) + "\n"
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            tmp_path = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
        fsync_directory(path.parent)
    except OSError as original:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise original
