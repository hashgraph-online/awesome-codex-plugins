"""Shared Packet/MCP path policy. This file also ships with the standalone Skill.

The bridge serializes its own writes. This is not an OS sandbox against another
process running as the owner and concurrently replacing workspace directories.
"""
from __future__ import annotations

import fnmatch
import hashlib
import os
import re
import stat
import tempfile
from pathlib import Path, PurePosixPath

DENY_NAMES = frozenset({".git", ".hg", ".svn", "node_modules", ".venv", "venv",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".idea", ".ssh", ".aws", ".gnupg"})
DENY_GLOBS = frozenset({"*.pem", "*.key", "*.p12", "*.pfx", "*.kdbx", "*.token",
    ".env", ".env.*", "id_rsa", "id_ed25519", "credentials.json", "service-account*.json",
    "*secret*.json", ".review-mcp-token", ".npmrc", ".pypirc"})
ALLOW_GLOBS = frozenset({".env.example", ".env.sample", ".env.template"})


def relative_path(raw: str, *, allow_root: bool = False) -> PurePosixPath:
    if not isinstance(raw, str) or len(raw) > 4096:
        raise ValueError("invalid relative path")
    if raw == "." and allow_root:
        return PurePosixPath(".")
    if (not raw or raw.startswith("/") or "\\" in raw or ":" in raw
            or any(ord(c) < 32 or ord(c) == 127 for c in raw)):
        raise ValueError("invalid relative path")
    for part in raw.split("/"):
        if (part in {"", ".", ".."} or part.endswith((".", " "))
                or any(c in part for c in '*?<>|"')
                or re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part)):
            raise ValueError("invalid relative path")
    return PurePosixPath(raw)


def denied(relative: PurePosixPath, patterns=()) -> bool:
    parts = [part.casefold() for part in relative.parts]
    for part in parts:
        if part in DENY_NAMES:
            return True
        if part in ALLOW_GLOBS:
            continue
        if any(fnmatch.fnmatchcase(part, p) for p in DENY_GLOBS):
            return True
    rel = relative.as_posix().casefold()
    return any(fnmatch.fnmatchcase(rel, p.casefold())
               or fnmatch.fnmatchcase(relative.name.casefold(), p.casefold()) for p in patterns)


def linked(st: os.stat_result) -> bool:
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st, "st_file_attributes", 0) & 0x400)


def checked_path(root: Path, raw: str, *, missing=False, allow_root=False, patterns=()) -> Path:
    rel = relative_path(raw, allow_root=allow_root)
    if denied(rel, patterns):
        raise ValueError("path is denied by the shared access policy")
    current = root
    for part in rel.parts:
        current = current / part
        try:
            st = current.lstat()
        except FileNotFoundError:
            if missing:
                continue
            raise ValueError("path does not exist") from None
        if linked(st):
            raise ValueError("linked paths are denied")
        if stat.S_ISREG(st.st_mode) and st.st_nlink != 1:
            raise ValueError("hard-linked files are denied")
        if not (stat.S_ISDIR(st.st_mode) or stat.S_ISREG(st.st_mode)):
            raise ValueError("special files are denied")
    return current


def ignore_patterns(root: Path) -> list[str]:
    path = root / ".chatgpt-agentignore"
    if not path.exists() and not path.is_symlink():
        return []
    checked_path(root, ".chatgpt-agentignore")
    with path.open("rb") as handle:
        data = handle.read(65537)
    if len(data) > 65536:
        raise ValueError("ignore policy exceeds limit")
    return [line.strip() for line in data.decode("utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def read_regular(root: Path, raw: str, *, limit: int = 16_000_000, patterns=()) -> bytes:
    path = checked_path(root, raw, patterns=patterns)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(path, flags)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError("not an ordinary unlinked file")
        if before.st_size > limit:
            raise ValueError("file exceeds read limit")
        with os.fdopen(fd, "rb", closefd=False) as handle:
            data = handle.read(limit + 1)
        after = os.fstat(fd)
        checked_path(root, raw, patterns=patterns)
        current = path.stat()
        if ((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
                != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
                or (current.st_dev, current.st_ino) != (after.st_dev, after.st_ino)
                or len(data) > limit):
            raise ValueError("file changed while being read")
        return data
    finally:
        os.close(fd)


def atomic_write(root: Path, raw: str, data: bytes, *, expected: str | None,
                 create: bool, patterns=(), authorize=None) -> dict:
    """Requires the caller's workspace mutation lock; new paths never overwrite."""
    path = checked_path(root, raw, missing=True, patterns=patterns)
    exists = path.exists()
    if exists:
        old = read_regular(root, raw, patterns=patterns)
        if create or not expected or hashlib.sha256(old).hexdigest() != expected:
            raise ValueError("file changed since it was read")
        mode = stat.S_IMODE(path.stat().st_mode)
    else:
        if not create or expected:
            raise ValueError("new files require create=true and no previous hash")
        mode = 0o600
    path.parent.mkdir(parents=True, exist_ok=True)
    checked_path(root, raw, missing=True, patterns=patterns)
    fd, tmp = tempfile.mkstemp(prefix=".cga-write-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, mode)
        checked_path(root, raw, missing=True, patterns=patterns)
        if authorize is not None:
            authorize()
        if exists:
            if hashlib.sha256(read_regular(root, raw, patterns=patterns)).hexdigest() != expected:
                raise ValueError("file changed since it was read")
            os.replace(tmp, path)
        else:
            # Atomic no-overwrite, unlike exists()+replace(). The staged inode
            # is unlinked before releasing the caller's mutation lock.
            os.link(tmp, path)
        return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
