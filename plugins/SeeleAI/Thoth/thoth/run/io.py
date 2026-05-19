"""Runtime filesystem paths and atomic JSON/JSONL helpers."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any

def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.parent / f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    try:
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp_path.replace(path)
    finally:
        tmp_path.unlink(missing_ok=True)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def project_hash(project_root: Path) -> str:
    return hashlib.sha256(str(project_root.resolve()).encode("utf-8")).hexdigest()[:16]


def _directory_is_writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / f".thoth-write-test-{os.getpid()}"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError:
        return False
    return True


def local_registry_root(project_root: Path) -> Path:
    env = os.environ.get("THOTH_LOCAL_STATE_DIR")
    if env:
        base = Path(env)
    else:
        preferred = Path.home() / ".local" / "state" / "thoth"
        fallback = project_root / ".thoth" / "derived" / "local-state"
        base = preferred if _directory_is_writable(preferred) else fallback
    return base / project_hash(project_root)


def ensure_runtime_tree(project_root: Path) -> None:
    for rel in (
        ".thoth/objects",
        ".thoth/docs",
        ".thoth/runs",
        ".thoth/migrations",
        ".thoth/derived",
    ):
        (project_root / rel).mkdir(parents=True, exist_ok=True)
