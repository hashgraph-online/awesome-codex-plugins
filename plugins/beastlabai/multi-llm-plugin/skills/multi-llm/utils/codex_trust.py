"""Remove the codex trust entries a multi-llm run added to the user's config.

Plan ``codex-sandbox-unavailable-findings-and-fixes`` §5, issue I12 (step 5,
2026-09-30). codex (measured 0.158.0 through 0.159.1) appends

    [projects."<git toplevel>"]
    trust_level = "trusted"

to ``$CODEX_HOME/config.toml`` whenever a ``codex exec`` child runs under
``workspace-write`` or ``danger-full-access`` in a repository the user never
trusted — even with ``--skip-git-repo-check``. Every write-capable child the
plugin starts does this (the fan-out's ``generate``, ``agent-write``, the
uncontained rung and the plugin-landlock rung), so a plugin run silently made a
security decision for the user: that repo's project-level config is honoured in
the user's later Codex sessions.

**Option A was measured and not adopted** (2026-09-30, codex 0.159.0): the one
override that stops the write, ``-c projects={"<cwd>"={trust_level=
"untrusted"}}``, never widens what the child loads but *narrows* it — the child
no longer reads the repo's ``AGENTS.md`` or ``.codex/config.toml``. The plan
admits option A only "if it measures clean"; it does not, so this is option B:
**remove only what the run added.**

* :func:`arm` runs before a codex child starts (the adapter's side-effect-only
  ``note_dispatch`` hook, which ``llm_client.provider_dispatch_context`` calls
  on both spawn sites — not ``hermetic_dispatch``, which stays opencode's
  alone): for the resolved
  ``$CODEX_HOME`` it records, per repository key, whether ``config.toml``
  already had a ``[projects."<key>"]`` table. Idempotent; the first arm of a
  home also keeps its pre-run bytes and mode in memory.
* :func:`restore_all` runs once, from ``multi_llm.main``'s ``finally`` — after
  the run's last codex child exited, on a normal return, an exception, Ctrl-C
  or a foreground SIGTERM — and, for a detached worker, from the two endings
  that ``os._exit`` past that ``finally``: the ``--abort`` signal handler
  (after the CLI sweep) and the heartbeat-lost exit (``utils/detach.py``). It removes a table only if it was absent at arm time and now holds
  exactly ``trust_level = "trusted"``; anything else means someone changed it
  during the run, and it is left with a warning. The edit removes only that
  table's lines (and the one blank line codex inserted before it); every other
  byte, comment and table stays; the pre-run mode is restored (codex forces
  0600); the write goes through a temp file and a rename in the same directory.
  Never a TOML round-trip, which drops comments. Never mid-run: children share
  the file and codex rewrites it by atomic rename.

Residual (the plan's, never worse than before): a SIGKILLed run, or an
overlapping run in the same repo (which sees the earlier run's entry as
pre-existing), can leave an entry behind.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple

try:  # pragma: no cover - import shim mirrors the rest of utils/
    from .git_utils import git_argv
except ImportError:  # pragma: no cover - direct-script import shim
    from utils.git_utils import git_argv

CONFIG_NAME = "config.toml"

#: Reentrant because :func:`restore_all` also runs inside the detached worker's
#: SIGTERM handler, on the main thread, which may have been interrupted inside
#: :func:`arm`'s ``with _LOCK`` — a plain lock would deadlock the abort there.
_LOCK = threading.RLock()


@dataclass
class _HomeRecord:
    home: str
    existed: bool
    pre_bytes: bytes
    pre_mode: Optional[int]
    #: key → whether its table existed at the time the key was armed.
    keys: Dict[str, bool] = field(default_factory=dict)


_RECORDS: Dict[str, _HomeRecord] = {}

#: The test suite turns this off (``tests/conftest.py``) so no test arms the
#: developer's real ``~/.codex``; the tests of this module turn it back on
#: against a temp home.
ENABLED = True


#: realpath'd directory → its :func:`repo_keys`, so a repeat arm for the same
#: anchor and cwd spawns no ``git``. Only answers from a successful
#: ``git rev-parse`` are kept; a directory's toplevel is taken as fixed for the
#: life of a run, so nothing invalidates an entry but :func:`reset`.
_REPO_KEYS: Dict[str, Tuple[str, ...]] = {}


def reset() -> None:
    """Forget every armed home and cached repository key (tests; a new run in
    the same interpreter)."""
    with _LOCK:
        _RECORDS.clear()
        _REPO_KEYS.clear()


def _config_path(home: str) -> str:
    return os.path.join(home, CONFIG_NAME)


def _read(path: str) -> Tuple[bool, bytes, Optional[int]]:
    try:
        with open(path, "rb") as handle:
            data = handle.read()
        return True, data, os.stat(path).st_mode & 0o7777
    except FileNotFoundError:
        return False, b"", None


def _unescape_basic(text: str) -> str:
    return text.replace('\\"', '"').replace("\\\\", "\\")


_HEADER = re.compile(
    r'^\[projects\.(?:"((?:[^"\\]|\\.)*)"|\'([^\']*)\')\][ \t]*$'
)


def _table_keys(text: str) -> Set[str]:
    keys: Set[str] = set()
    for line in text.splitlines():
        match = _HEADER.match(line.strip())
        if match:
            keys.add(_unescape_basic(match.group(1)) if match.group(1) is not None else match.group(2))
    return keys


def repo_keys(directory: Optional[str]) -> List[str]:
    """The keys codex uses for ``directory``: the ``realpath`` of its git
    toplevel and, for a linked worktree, of the main repository root
    (measured 2026-09-30). ``[]`` outside a git repository.

    Memoised per ``realpath``'d directory: :func:`arm` runs before every codex
    child, and only the first call for a directory spawns ``git``. A failed
    probe (not a repository, git missing, a timeout) is not cached."""
    start = os.path.realpath(directory or os.getcwd())
    if os.path.isfile(start):
        start = os.path.dirname(start) or "."
    cached = _REPO_KEYS.get(start)
    if cached is not None:
        return list(cached)
    keys: List[str] = []
    try:
        top = subprocess.run(
            git_argv("rev-parse", "--show-toplevel", "--git-common-dir", cwd=start),
            capture_output=True, text=True, cwd=start, timeout=10,
            encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        return keys
    if top.returncode != 0:
        return keys
    lines = [line.strip() for line in top.stdout.splitlines() if line.strip()]
    if lines:
        keys.append(os.path.realpath(lines[0]))
    if len(lines) > 1:
        common = lines[1]
        if not os.path.isabs(common):
            common = os.path.join(start, common)
        main_root = os.path.realpath(os.path.dirname(os.path.realpath(common)))
        if main_root not in keys:
            keys.append(main_root)
    if keys:
        _REPO_KEYS[start] = tuple(keys)
    return keys


def arm(codex_home: Optional[str], repo_dirs: Iterable[Optional[str]]) -> None:
    """Record, before a codex child starts, which trust tables ``codex_home``'s
    config already holds for the repositories of ``repo_dirs``. Idempotent and
    cheap after the first call per (home, key): the keys come from
    :func:`repo_keys`' cache, and once every key is recorded for the home the
    config is not re-read. Never raises."""
    if not codex_home or not ENABLED:
        return
    try:
        home = os.path.realpath(os.path.expanduser(codex_home))
        keys: List[str] = []
        for directory in repo_dirs:
            for key in repo_keys(directory):
                if key not in keys:
                    keys.append(key)
        with _LOCK:
            record = _RECORDS.get(home)
            if record is not None and all(key in record.keys for key in keys):
                return
            existed, data, mode = _read(_config_path(home))
            if record is None:
                record = _RECORDS[home] = _HomeRecord(
                    home=home, existed=existed, pre_bytes=data, pre_mode=mode,
                )
            present = _table_keys(data.decode("utf-8", errors="replace")) if existed else set()
            for key in keys:
                if key not in record.keys:
                    record.keys[key] = key in present
    except Exception as exc:  # noqa: BLE001 - bookkeeping may never block a dispatch
        print(f"multi-llm warning: could not record codex trust state: {exc}", file=sys.stderr)


def _remove_table(text: str, key: str) -> Tuple[str, str]:
    """``(new text, verdict)`` where verdict is ``removed``, ``absent`` or
    ``changed`` (the table holds more than the expected trust line)."""
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        match = _HEADER.match(line.strip())
        if not match:
            continue
        found = _unescape_basic(match.group(1)) if match.group(1) is not None else match.group(2)
        if found != key:
            continue
        # The table's own lines: the consecutive non-blank lines under the
        # header. They must be exactly the trust line codex writes.
        end = index + 1
        while end < len(lines) and lines[end].strip() and not lines[end].lstrip().startswith("["):
            end += 1
        body = [lines[i].strip() for i in range(index + 1, end)]
        if body != ['trust_level = "trusted"']:
            return text, "changed"
        # Past a blank line, only comments and blank lines may precede the next
        # header: a stray key there would still belong to this table in TOML,
        # and removing the header would hand it to the previous one.
        look = end
        while look < len(lines):
            stripped = lines[look].strip()
            if stripped.startswith("["):
                break
            if stripped and not stripped.startswith("#"):
                return text, "changed"
            look += 1
        # Drop the header, the trust line and the one blank line codex put
        # before the table; the blank lines and comments that follow stay.
        start = index
        if start > 0 and not lines[start - 1].strip():
            start -= 1
        new_lines = lines[:start] + lines[end:]
        return "".join(new_lines), "removed"
    return text, "absent"


def _atomic_write(path: str, data: bytes, mode: int) -> None:
    directory = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(prefix=".multi-llm-trust-", dir=directory)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def restore_home(record: _HomeRecord) -> List[str]:
    """Remove the trust tables this run added to one home. Returns warnings."""
    warnings: List[str] = []
    path = _config_path(record.home)
    added = [key for key, present in record.keys.items() if not present]
    if not added:
        return warnings
    existed, data, mode = _read(path)
    if not existed:
        return warnings
    text = data.decode("utf-8", errors="surrogateescape")
    removed_any = False
    for key in added:
        text, verdict = _remove_table(text, key)
        if verdict == "removed":
            removed_any = True
        elif verdict == "changed":
            warnings.append(
                f"codex's config {path} has a [projects.\"{key}\"] table this run "
                f"did not find there before, but it holds more than the trust entry "
                f"codex adds; left as it is — review it"
            )
    if not removed_any:
        return warnings
    new = text.encode("utf-8", errors="surrogateescape")
    pre = record.pre_bytes
    if record.existed and not pre.endswith(b"\n") and new == pre + b"\n":
        # codex terminated a final line that had no newline before inserting.
        new = pre
    if not record.existed and not new.strip():
        try:
            os.unlink(path)
        except OSError as exc:
            warnings.append(f"could not remove codex's config {path}, which this run's trust entry created: {exc}")
        return warnings
    target_mode = record.pre_mode if record.pre_mode is not None else (mode or 0o600)
    try:
        _atomic_write(path, new, target_mode)
    except OSError as exc:
        warnings.append(f"could not remove this run's codex trust entry from {path}: {exc}")
    return warnings


def restore_all() -> List[str]:
    """Remove every trust table this process's codex children added, then
    forget the records. Called from ``multi_llm.main``'s ``finally`` and from
    a detached worker's ``--abort``/heartbeat-lost exits; a second call finds
    nothing left. Never raises. Returns (and prints) warnings."""
    with _LOCK:
        records = list(_RECORDS.values())
        _RECORDS.clear()
    warnings: List[str] = []
    for record in records:
        try:
            warnings.extend(restore_home(record))
        except Exception as exc:  # noqa: BLE001 - close-out must never mask the result
            warnings.append(f"could not restore codex's config under {record.home}: {exc}")
    for line in warnings:
        print(f"multi-llm warning: {line}", file=sys.stderr)
    return warnings


__all__ = ["arm", "repo_keys", "reset", "restore_all", "restore_home"]
