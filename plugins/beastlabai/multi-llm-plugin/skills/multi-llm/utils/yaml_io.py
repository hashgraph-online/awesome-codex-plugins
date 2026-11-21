"""YAML parsing for the skill: one safe loader and a stat-keyed file cache.

Every YAML document the skill reads at runtime goes through here:
``providers.yaml`` and its override layers, ``hosts/capabilities.yaml``, a
generated ``--init`` config and an aider settings file. The loader choice and
the cache rules therefore live in one place.

* :data:`SAFE_LOADER` is libyaml's ``CSafeLoader`` when the installed PyYAML
  wheel was built with libyaml, and the pure-Python ``SafeLoader`` otherwise.
  Both are *safe* loaders: plain data only, no Python object tags. Never swap
  in an unsafe loader. They build equal documents for every YAML file in the
  repository (``tests/test_yaml_io.py``); only the text of a parse error's
  position differs, because libyaml's mark has no source snippet. The C loader
  parses ``providers.yaml`` in about 0.6 ms against 16 ms for the pure one.
* :func:`load_file` parses a file once per process while it stays unchanged,
  and hands every caller its own deep copy, so no caller can edit the cached
  document. See :func:`load_file` for the key and the timestamp rule.

The provider-config rules built on this (one entry per set of layer files and
their signatures) are in
``docs/development/providers.md#configuration-and-runner-resolution``.
"""
from __future__ import annotations

import copy
import os
import threading
import time
from typing import IO, Any, Dict, Optional, Tuple, Union

import yaml

from .process_state import process_cache

#: The loader :func:`safe_load` and :func:`load_file` use (see module docstring).
SAFE_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

#: Raised for a document either loader rejects; callers catch this name rather
#: than importing ``yaml`` themselves.
YAMLError = yaml.YAMLError

#: A file changed less than this long ago is parsed but not cached. A file's
#: timestamps have a coarse tick (a few ms on Linux, 1 s on HFS+, 2 s on FAT),
#: so a rewrite of the same size inside one tick keeps the same signature; once
#: the file is older than the slowest tick, an unchanged signature means
#: unchanged bytes.
SETTLE_S = 3.0

#: Most files the cache holds; the oldest entry goes first. A run reads the base
#: ``providers.yaml``, at most one project layer per repository it touches, an
#: env layer and the capability data, so this is never reached in practice.
MAX_ENTRIES = 64

PathLike = Union[str, "os.PathLike[str]"]

# resolved path -> (signature, parsed document). The document is never handed
# out: load_file returns deep copies of it.
_LOCK = threading.Lock()
_CACHE: Dict[str, Tuple[tuple, Any]] = process_cache("utils.yaml_io._CACHE", lock=_LOCK)


def safe_load(stream: Union[str, bytes, IO[str], IO[bytes]]) -> Any:
    """Parse one YAML document from *stream* with :data:`SAFE_LOADER`, uncached."""
    return yaml.load(stream, Loader=SAFE_LOADER)


def _stamp(st: os.stat_result) -> tuple:
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def _signature(resolved: str, st: os.stat_result) -> tuple:
    return (resolved,) + _stamp(st)


def file_signature(path: PathLike) -> Optional[tuple]:
    """The identity of the file at *path* right now, for use in a cache key.

    ``(st_dev, st_ino, st_size, st_mtime_ns, st_ctime_ns)`` of the file the
    path leads to: the device and inode name the file, wherever a symlink
    points, so no path is resolved. For a broken symlink, the link's own
    ``lstat`` fields under the tag ``"link"``, so a broken link and an absent
    file never share a key. ``None`` when nothing is at *path*. Trust it to
    mean unchanged bytes only once :func:`is_settled`.
    """
    try:
        return _stamp(os.stat(path))
    except OSError:
        pass
    try:
        return ("link",) + _stamp(os.lstat(path))
    except OSError:
        return None


def is_settled(signature: Optional[tuple]) -> bool:
    """True when a cache keyed on *signature* can be trusted (see :data:`SETTLE_S`).

    An absent file (``None``) is settled: its appearance changes the signature.
    """
    if signature is None:
        return True
    newest_ns = max(signature[-2], signature[-1])
    return time.time_ns() - newest_ns >= int(SETTLE_S * 1e9)


def load_file(path: PathLike) -> Any:
    """Parse the YAML file at *path*, from the per-process cache when unchanged.

    The cache entry is chosen by the file's resolved path and is valid only
    while the open file's ``fstat`` matches the signature it was stored with
    (the resolved path and :func:`file_signature`'s fields). The signature
    comes from the descriptor that is then read, so a path re-pointed between
    the check and the read cannot pair one file's bytes with another file's
    key. A parse is admitted only when the descriptor's signature is the same
    after the read as before it, and was already settled (:func:`is_settled`)
    when it was taken, before the read began; so a file changed in the last
    :data:`SETTLE_S` seconds is parsed on every call.

    Returns a deep copy, never the cached object. Raises ``OSError`` when the
    file cannot be opened and :data:`YAMLError` when it does not parse,
    including a file that is not UTF-8 text; neither outcome is cached. The
    file is read as UTF-8 text, the way every caller read it before this
    module existed.
    """
    resolved = os.path.realpath(path)
    with open(path, "r", encoding="utf-8") as handle:
        signature = _signature(resolved, os.fstat(handle.fileno()))
        with _LOCK:
            hit = _CACHE.get(resolved)
        if hit is not None and hit[0] == signature:
            return copy.deepcopy(hit[1])
        # Decided before the read: a read that starts inside a timestamp tick
        # and ends after SETTLE_S may still have seen the bytes a same-size
        # rewrite in that tick replaced.
        settled = is_settled(signature)
        try:
            document = yaml.load(handle, Loader=SAFE_LOADER)
        except UnicodeDecodeError as exc:
            # A caller handles one parse error, whatever stopped the parse.
            raise YAMLError(f"not UTF-8 text ({exc})") from exc
        unchanged = _signature(resolved, os.fstat(handle.fileno())) == signature
    if not (settled and unchanged):
        return document
    with _LOCK:
        _CACHE.pop(resolved, None)
        while len(_CACHE) >= MAX_ENTRIES:
            _CACHE.pop(next(iter(_CACHE)))
        _CACHE[resolved] = (signature, document)
    return copy.deepcopy(document)


def clear_cache() -> None:
    """Drop every cached document (tests)."""
    with _LOCK:
        _CACHE.clear()
