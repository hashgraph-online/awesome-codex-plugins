"""The doctor's cache of parsed provider CLI versions (``multi_llm.py doctor`` only).

A ``--version`` probe gives the same answer until the executable it runs
changes, and on a machine with fifteen CLIs those probes are most of the
SessionStart hook's CPU. This module remembers the *parsed* version string per
provider, keyed on the executable's identity, so a later doctor run can skip
the spawn.

The rules (docs/development/status.md, "doctor's version cache"):

- **Doctor only.** The executor's ``min_version`` refusal
  (``runner_preflight._detect_version``) and every other runner check read
  the CLI live; nothing outside ``utils/doctor.py`` imports this module, and a
  test holds that.
- **The key is the file, not its bytes.** Resolved executables are often
  launchers (a uv shim, a ``codex.js`` that picks a platform binary) whose
  bytes can be identical across versions, so the key carries
  ``st_mtime_ns``, ``st_ctime_ns`` and ``st_ino`` beside the real path and
  ``st_size``; installers rewrite the launcher, which moves them. A
  hand-made wrapper whose target changes under it is the case the key
  cannot see, so an entry also expires after :data:`TTL_S`, and
  ``doctor --fresh`` re-probes everything.
- **The parser is part of the key.** The cached value is what the adapter's
  ``parse_version`` read, so the file that defines that method (and its
  stat) is in the key too: a plugin update that changes the parser misses.
- **Only parsed version strings, never raw output, and never a failed
  read.** Auth and sandbox probes are never cached: their answers change
  without any file changing.
- **Only what this module could have written is read.** The file and its
  directory must be this user's, not symlinks and not group- or
  world-writable (:func:`directory_refusal`, :func:`_read_trusted`); an entry
  must carry a finite ``probed_at`` inside the expiry window and a version
  the adapter's own parser reads back unchanged (:func:`parser_output`), so a
  planted ``"unknown"`` cannot skip the floor check. A refused file or
  directory is an empty cache and says why only in ``doctor --json``. A
  same-user forgery stays possible: that user can edit the CLI itself.
- **Fail open.** A missing, unreadable, corrupt, refused or foreign-shaped
  file is an empty cache; a write that fails, or would go into a refused
  directory, is skipped. Writes go to a temporary file in the same
  directory and are moved into place with ``os.replace``, merged with what is
  on disk at that moment, so concurrent sessions never see a torn file; the
  cost of a race is at most a lost entry, i.e. one more probe next time.
"""

from __future__ import annotations

import errno
import json
import math
import os
import stat
import threading
import time
from typing import Any, Callable, Dict, Optional, Sequence, Tuple

from .atomic_io import atomic_write_text

#: Bump when an entry's shape or meaning changes; a file with another value is
#: ignored (and replaced on the next write).
SCHEMA = 1

#: An entry older than this is a miss, so a wrapper whose stat never moves is
#: re-read at least weekly.
TTL_S = 7 * 24 * 3600

FILE_NAME = "cli-versions.json"

#: A parsed version is a short dotted token; a longer string is not one.
MAX_VERSION_LEN = 64

#: A cache file larger than this was not written by this module.
MAX_FILE_BYTES = 1 << 20

#: The stat fields that make up a file's identity in the key.
_STAT_FIELDS = ("st_size", "st_mtime_ns", "st_ctime_ns", "st_ino")


def cache_dir() -> str:
    """``$XDG_CACHE_HOME/multi-llm`` (default ``~/.cache/multi-llm``), the
    cache-side twin of ``output_handler.state_home``."""
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(
        os.path.expanduser("~"), ".cache"
    )
    return os.path.join(base, "multi-llm")


def cache_file() -> str:
    return os.path.join(cache_dir(), FILE_NAME)


def _file_identity(path: str) -> Optional[Dict[str, Any]]:
    """``{"path": realpath, st_size, st_mtime_ns, st_ctime_ns, st_ino}`` or
    ``None`` when the file cannot be stat'ed."""
    real = os.path.realpath(path)
    try:
        st = os.stat(real)
    except OSError:
        return None
    identity: Dict[str, Any] = {"path": real}
    for field in _STAT_FIELDS:
        identity[field] = int(getattr(st, field, 0) or 0)
    return identity


def _parser_source(provider: Any) -> str:
    """The file that defines ``type(provider).parse_version``, or ``""``."""
    method = getattr(type(provider), "parse_version", None)
    code = getattr(method, "__code__", None)
    return str(getattr(code, "co_filename", "") or "")


def fingerprint(
    provider: Any, argv: Sequence[str], launcher: Sequence[str]
) -> Optional[Dict[str, Any]]:
    """What an entry must match to be a hit: the probe's argv, the identity
    of every file in the resolved ``launcher`` (one path on POSIX, ``node``
    plus the script for a Windows npm shim) and of the parser's source file.
    ``None`` when the launcher does not resolve to a file, which is never
    cached."""
    files = []
    for element in launcher:
        if not element or not os.path.isabs(element):
            return None
        identity = _file_identity(element)
        if identity is None:
            return None
        files.append(identity)
    if not files:
        return None
    source = _parser_source(provider)
    parser = _file_identity(source) if source else None
    return {"argv": [str(part) for part in argv], "files": files, "parser": parser}


def parser_output(provider: Any, version: Any) -> bool:
    """Whether ``version`` could be what ``provider.parse_version`` returned:
    a short string the adapter's parser reads back as itself, and never the
    ``unknown`` an unread version is reported as (``version_verdict`` skips
    the floor for that). Doctor records nothing else, so an entry failing
    this is a miss."""
    if not isinstance(version, str) or not version or len(version) > MAX_VERSION_LEN:
        return False
    if version.strip().lower() == "unknown":
        return False
    parse = getattr(provider, "parse_version", None)
    if not callable(parse):
        return False
    try:
        return parse(version, "") == version
    except Exception:  # noqa: BLE001 - a parser that raises read nothing
        return False


def _timestamp(value: Any) -> Optional[float]:
    """``value`` as a finite POSIX time, or ``None``: a bool, a string, an
    integer too large for a float, NaN and the infinities are all misses."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        stamp = float(value)
    except (OverflowError, ValueError):
        return None
    return stamp if math.isfinite(stamp) else None


def _my_uid() -> Optional[int]:
    """This process's user id, or ``None`` where there is none (Windows)."""
    getuid = getattr(os, "getuid", None)
    return getuid() if callable(getuid) else None


def _refusal(st: os.stat_result, what: str, is_kind: Callable[[int], bool]) -> str:
    """Why an ``lstat``/``fstat`` result is not a cache ``what`` this user
    made, or ``""``. Ownership and mode bits are POSIX-only; Windows gets the
    symlink and file-kind checks."""
    if stat.S_ISLNK(st.st_mode):
        return f"the cache {what} is a symlink"
    if not is_kind(st.st_mode):
        return f"the cache {what} is not a {'directory' if what == 'directory' else 'regular file'}"
    uid = _my_uid()
    if uid is not None:
        if st.st_uid != uid:
            return f"the cache {what} is owned by uid {st.st_uid}, not this user"
        if st.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            return f"the cache {what} is group- or world-writable"
    return ""


def directory_refusal(directory: str) -> str:
    """``""`` when ``directory`` is missing or one this user made; otherwise
    why the cache must neither read nor write there."""
    try:
        st = os.lstat(directory)
    except (FileNotFoundError, NotADirectoryError):
        return ""
    except OSError as exc:
        return f"the cache directory cannot be inspected ({exc.strerror or exc})"
    return _refusal(st, "directory", stat.S_ISDIR)


def _read_trusted(path: str) -> Tuple[Optional[bytes], str]:
    """``(bytes, "")`` for a file this user made, in a directory this user
    made; ``(None, "")`` when there is none or it cannot be read; ``(None,
    why)`` when the file or its directory is refused. The file is opened
    without following a symlink and without blocking on a FIFO, and judged
    by ``fstat`` of what was opened."""
    why = directory_refusal(os.path.dirname(path) or os.curdir)
    if why:
        return None, why
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if not nofollow and os.path.islink(path):
        return None, "the cache file is a symlink"
    flags = (
        os.O_RDONLY | nofollow | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_BINARY", 0)
    )
    try:
        fd = os.open(path, flags)
    except (FileNotFoundError, NotADirectoryError):
        return None, ""
    except OSError as exc:
        if nofollow and exc.errno in (errno.ELOOP, getattr(errno, "EMLINK", -1)):
            return None, "the cache file is a symlink"
        return None, ""
    try:
        st = os.fstat(fd)
        why = _refusal(st, "file", stat.S_ISREG)
        if why:
            return None, why
        if st.st_size > MAX_FILE_BYTES:
            return None, f"the cache file is larger than {MAX_FILE_BYTES} bytes"
        chunks = []
        while True:
            chunk = os.read(fd, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks), ""
    except OSError:
        return None, ""
    finally:
        os.close(fd)


def _load_entries(path: str) -> Tuple[Dict[str, Dict[str, Any]], str]:
    """``(entries, refusal)``: the file's entries by provider name, empty when
    the file is missing, corrupt, foreign-shaped or refused; ``refusal`` says
    why a file or directory was refused, else ``""``."""
    raw, why = _read_trusted(path)
    if raw is None:
        return {}, why
    try:
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, RecursionError):
        return {}, ""
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        return {}, ""
    entries = data.get("entries")
    if not isinstance(entries, dict):
        return {}, ""
    return {
        str(name): entry for name, entry in entries.items()
        if isinstance(entry, dict)
    }, ""


class _Refused(OSError):
    """The cache directory is not one this user made; nothing is written."""


class VersionCache:
    """One doctor run's view of the cache: loaded once, looked up from the
    probe threads, written back once with :meth:`save`. With ``read=False``
    (``doctor --fresh``) every lookup misses, and what the run reads is still
    recorded. ``refused`` says why the file or its directory was refused
    (``""`` when it was not)."""

    def __init__(
        self, path: Optional[str] = None, *, now: Optional[float] = None, read: bool = True,
    ):
        self.path = path or cache_file()
        self.now = time.time() if now is None else now
        self.read = read
        self._entries, self.refused = _load_entries(self.path) if read else ({}, "")
        self._fresh: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def lookup(self, name: str, key: Optional[Dict[str, Any]], provider: Any) -> Optional[str]:
        """The cached version for ``name`` when its entry matches ``key``,
        holds a version ``provider``'s parser could have returned
        (:func:`parser_output`) and a finite ``probed_at`` no more than
        :data:`TTL_S` old and not in the future; otherwise ``None`` (probe
        it)."""
        if key is None or not self.read:
            return None
        with self._lock:
            entry = self._entries.get(name)
        if not isinstance(entry, dict) or entry.get("key") != key:
            return None
        version = entry.get("version")
        if not parser_output(provider, version):
            return None
        stamp = _timestamp(entry.get("probed_at"))
        if stamp is None or not 0 <= self.now - stamp <= TTL_S:
            return None
        return version

    def record(self, name: str, key: Optional[Dict[str, Any]], version: Optional[str]) -> None:
        """Remember a version just parsed from a live probe. A failed read
        (empty ``version``) or an unresolvable launcher is never recorded."""
        if key is None or not isinstance(version, str) or not version.strip():
            return
        entry = {"key": key, "version": version.strip(), "probed_at": self.now}
        with self._lock:
            self._fresh[name] = entry
            self._entries[name] = entry

    def save(self) -> bool:
        """Write this run's new entries, merged over what is on disk now.
        ``True`` when a file was written. Never raises; a refused directory is
        never written to (``refused`` then says why)."""
        with self._lock:
            fresh = dict(self._fresh)
        if not fresh:
            return False
        try:
            merged, _ = _load_entries(self.path)
            merged.update(fresh)
            _atomic_write_json(self.path, {"schema": SCHEMA, "entries": merged})
        except _Refused as exc:
            self.refused = self.refused or str(exc)
            return False
        except (OSError, TypeError, ValueError):
            return False
        with self._lock:
            for name in fresh:
                self._fresh.pop(name, None)
        return True


def _atomic_write_json(path: str, payload: Dict[str, Any]) -> None:
    directory = os.path.dirname(path) or os.curdir
    os.makedirs(directory, mode=0o700, exist_ok=True)
    why = directory_refusal(directory)
    if why:
        raise _Refused(why)
    # Owner-only, like its 0700 directory. No fsync: a lost write costs one
    # more version probe, and the flush would cost doctor's startup budget.
    text = json.dumps(payload, indent=1, sort_keys=True) + "\n"
    atomic_write_text(path, text, mode=0o600, fsync=False, temp_prefix=".cli-versions.")
