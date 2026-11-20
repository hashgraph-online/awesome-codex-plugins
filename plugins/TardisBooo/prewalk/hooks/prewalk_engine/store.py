"""Durable state storage: one JSON document per host, keyed by session.

Concurrent access is the norm, not the exception — a host fires hooks as
separate processes while skills and CLI inspection run next to them. The
store therefore guarantees:

* **Cross-process mutual exclusion.** A sidecar ``.lock`` file is held with
  ``msvcrt`` on Windows and ``fcntl`` elsewhere for the duration of every
  read-modify-write cycle, plus an in-process lock so threads serialize too.
* **Crash-safe replacement.** Writes land in a sibling temp file, get
  fsynced, and are moved into place with ``os.replace`` — readers see either
  the old or the new document, never a half-written one.
* **Fail-closed corruption handling.** A store that is not a JSON object of
  objects is renamed to ``*.corrupt`` and reported as a status instead of
  being silently rebuilt on top of lost data.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .protocol import V4_SCHEMA_VERSION

_PROCESS_LOCK = threading.Lock()


def state_path(store_file: str | os.PathLike[str]) -> Path:
    """Return the store path, creating its parent directory if needed."""
    path = Path(store_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def utc_timestamp() -> str:
    """Current UTC time in the compact ISO-8601 form persisted in records."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@contextmanager
def _store_lock(store_file: str | os.PathLike[str]) -> Iterator[None]:
    """Hold the store's advisory lock across threads and hook processes."""
    with _PROCESS_LOCK:
        path = state_path(store_file)
        lock_path = path.with_name(path.name + ".lock")
        with open(lock_path, "a+b") as lock_file:
            if os.name == "nt":
                # msvcrt.locking refuses zero-byte regions on some Windows
                # releases, so make sure byte 0 exists before locking it.
                import msvcrt

                lock_file.seek(0, os.SEEK_END)
                if lock_file.tell() == 0:
                    lock_file.write(b"\0")
                    lock_file.flush()
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl

                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                lock_file.seek(0)
                if os.name == "nt":
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _quarantine_corrupt_store(store_file: str | os.PathLike[str]) -> None:
    """Move an unreadable store aside so the next write starts clean."""
    path = Path(store_file)
    backup = path.with_name(path.name + ".corrupt")
    try:
        os.replace(path, backup)
    except FileNotFoundError:
        pass


def _read_all_with_status(
    store_file: str | os.PathLike[str],
) -> tuple[dict[str, dict[str, Any]], str]:
    """Read every session record; report *missing* / *corrupt_store* / *ok*."""
    try:
        with open(store_file, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return {}, "missing"
    except (json.JSONDecodeError, UnicodeDecodeError):
        _quarantine_corrupt_store(store_file)
        return {}, "corrupt_store"
    if not isinstance(data, dict) or any(not isinstance(value, dict) for value in data.values()):
        _quarantine_corrupt_store(store_file)
        return {}, "corrupt_store"
    return data, "ok"


def _read_all(store_file: str | os.PathLike[str]) -> dict[str, dict[str, Any]]:
    return _read_all_with_status(store_file)[0]


def _write_all(store_file: str | os.PathLike[str], data: dict[str, dict[str, Any]]) -> None:
    """Replace the store atomically: temp file, fsync, rename."""
    path = state_path(store_file)
    descriptor, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def has_record(store_file: str | os.PathLike[str], session_id: str) -> bool:
    """Cheap membership check used by disarm and status rendering."""
    return session_id in _read_all(store_file)


def workspace_identity(workspace_root: str | os.PathLike[str]) -> str:
    """Stable, non-reversible identity of a canonical workspace path.

    Records refuse to load in a different workspace than the one that armed
    them; hashing (rather than storing) the path keeps the state file free of
    absolute local paths.
    """
    canonical = str(Path(workspace_root).expanduser().resolve())
    return "ws-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


# --- Legacy 0.3 record access -------------------------------------------------
#
# The v4 machine owns the real workflow; these accessors remain for the
# compatibility event machine in ``legacy`` and treat v4 records as absent.


def load_state(store_file: str | os.PathLike[str], session_id: str):
    """Load one legacy 0.3 record, ignoring v4 records."""
    if not session_id:
        return None
    with _store_lock(store_file):
        record = _read_all(store_file).get(session_id)
    if not record or record.get("schema_version") == V4_SCHEMA_VERSION:
        return None
    from .records import PrewalkState  # local import: avoid a cycle at module load

    return PrewalkState.from_dict(record)


def save_state(store_file: str | os.PathLike[str], state) -> None:
    """Persist one legacy 0.3 record."""
    with _store_lock(store_file):
        data = _read_all(store_file)
        data[state.session_id] = state.to_dict()
        _write_all(store_file, data)


def clear_state(store_file: str | os.PathLike[str], session_id: str) -> None:
    """Drop one record (either vintage) if present."""
    with _store_lock(store_file):
        data = _read_all(store_file)
        if data.pop(session_id, None) is not None:
            _write_all(store_file, data)
