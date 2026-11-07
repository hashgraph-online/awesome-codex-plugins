"""Atomic text writes shared by the scripts that rewrite user files."""

from __future__ import annotations

import os
import secrets
import shutil
import stat
from pathlib import Path


def atomic_write_text(path, text: str, newline: str | None = "\n", *,
                      follow_symlinks: bool = True, keep_mode: bool = True) -> None:
    """Write UTF-8 text to path via a temp file and os.replace.

    A symlink at *path* is resolved and its target rewritten, unless *follow_symlinks* is
    false: then the link itself is replaced by a regular file and its target is never touched.
    An existing file's mode is kept unless *keep_mode* is false (the new file then gets the
    umask mode). In both modes nothing is replaced for a FIFO or device named directly, or for
    a link or non-regular node under /dev or /proc (/dev/stdout, /dev/null, /dev/fd/N): the
    text is written into the existing node, as a plain write would. The modes differ only for
    other links: followed, or replaced (including a link to a FIFO or device when not
    following).
    *newline* is passed to the file object: "\n" (the default) writes LF on every platform,
    "" keeps the text's line endings as given."""
    if follow_symlinks:
        try:
            st_mode = os.stat(path).st_mode
        except OSError:
            st_mode = None
        system = os.path.islink(path) and os.path.abspath(path).startswith(("/dev/", "/proc/"))
        if st_mode is not None and (system or not stat.S_ISREG(st_mode)):
            # /dev/stdout, a FIFO or a link to one: replacing it would be wrong, so write into it
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
            link = stat.S_ISLNK(st_mode)
            system = os.path.abspath(path).startswith(("/dev/", "/proc/"))
            if system or not link:
                # /dev/stdout, /dev/null, a FIFO: replacing it would be wrong, so write into it
                with open(target, "w", encoding="utf-8", newline=newline) as f:
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
        os.replace(tmp, target)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
