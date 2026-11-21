"""Atomic text writes and JSON reads shared by the scripts that rewrite or read user files."""

from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import stat
from pathlib import Path
from typing import Any


def json_loads(text: str | bytes) -> Any:
    """json.loads, except that nesting deeper than the interpreter can parse raises
    json.JSONDecodeError (a ValueError) instead of RecursionError, so callers that treat a
    malformed file as unreadable treat a too-deep one the same way."""
    try:
        return json.loads(text)
    except RecursionError:
        if isinstance(text, (bytes, bytearray)):
            text = text.decode("utf-8", "replace")
        raise json.JSONDecodeError("JSON nested too deeply", text, 0) from None


def json_load(fp) -> Any:
    """json.load with the json_loads nesting behaviour."""
    return json_loads(fp.read())


def read_json(path, *, encoding: str = "utf-8") -> Any:
    """Parse the JSON file at *path*. OSError and UnicodeDecodeError propagate as from open()
    and read(); malformed or too-deeply nested JSON raises json.JSONDecodeError."""
    with open(path, "r", encoding=encoding) as f:
        return json_load(f)


_STREAM_NODES = frozenset(("/dev/stdout", "/dev/stderr", "/dev/null"))
_STREAM_FD = re.compile(r"^/(?:dev|proc/self)/fd/\d+$")


def _is_windows() -> bool:
    return os.name == "nt"


def _is_stream_node(path) -> bool:
    """/dev/stdout, /dev/stderr, /dev/null, /dev/fd/N or /proc/self/fd/N: names that stand for
    an open stream, written in place rather than replaced."""
    p = os.path.abspath(path)
    return p in _STREAM_NODES or bool(_STREAM_FD.match(p))


def atomic_write_text(path, text: str, newline: str | None = "\n", *,
                      follow_symlinks: bool = True, keep_mode: bool = True) -> None:
    """Write UTF-8 text to path via a temp file and os.replace.

    A symlink at *path* is resolved and its target rewritten, unless *follow_symlinks* is
    false: then the link itself is replaced by a regular file and its target is never touched.
    An existing file's mode is kept unless *keep_mode* is false (the new file then gets the
    umask mode). In both modes the stream names /dev/stdout, /dev/stderr, /dev/null,
    /dev/fd/N and /proc/self/fd/N, and a FIFO or device named directly, are written in place,
    as a plain write would. Any other link, under /dev or not, is followed or replaced
    (including a link to a FIFO or device when not following).
    On Windows a target another program holds open, or a read-only one, cannot be replaced:
    that exits with a one-line error, the temp file removed.
    *newline* is passed to the file object: "\n" (the default) writes LF on every platform,
    "" keeps the text's line endings as given."""
    if _is_stream_node(path):
        with open(path, "w", encoding="utf-8", newline=newline) as f:
            f.write(text)
        return
    if follow_symlinks:
        try:
            st_mode = os.stat(path).st_mode
        except OSError:
            st_mode = None
        if st_mode is not None and not stat.S_ISREG(st_mode):
            # a FIFO or a link to one: replacing it would be wrong, so write into it
            with open(path, "w", encoding="utf-8", newline=newline) as f:
                f.write(text)
            return
        target = Path(path).resolve()
    else:
        # only the last component is kept as given; the kernel resolves the directory part
        target = Path(os.path.join(os.path.dirname(path) or ".", os.path.basename(path)))
    existing = target.exists()
    if not follow_symlinks:
        try:
            st_mode = os.lstat(target).st_mode
        except OSError:
            st_mode = None
        if st_mode is not None and not stat.S_ISREG(st_mode):
            if not stat.S_ISLNK(st_mode):
                # a FIFO or device: replacing it would be wrong, so write into it
                fd = os.open(target, os.O_WRONLY | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
                             | getattr(os, "O_BINARY", 0))
                with os.fdopen(fd, "w", encoding="utf-8", newline=newline) as f:
                    f.write(text)
                return
            existing = False    # the link's mode and target are not the new file's
    if not keep_mode:
        existing = False
    # A new target gets 0o666 so the kernel applies the umask; an existing one is rewritten
    # through a private temp until copymode gives it the old mode
    flags = (os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
             | getattr(os, "O_BINARY", 0))
    mode = 0o600 if existing else 0o666
    while True:
        tmp = str(target.parent / f"{target.name}.{secrets.token_hex(6)}.tmp")
        try:
            fd = os.open(tmp, flags, mode)
            break
        except FileExistsError:
            continue
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline=newline) as f:
            f.write(text)
        if existing:
            shutil.copymode(target, tmp)
        try:
            os.replace(tmp, target)
        except PermissionError as exc:
            if not _is_windows():
                raise
            raise SystemExit(f"Error: cannot write {path}: the file is open in another program "
                             f"or read-only; close it or make it writable and run again") from exc
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
