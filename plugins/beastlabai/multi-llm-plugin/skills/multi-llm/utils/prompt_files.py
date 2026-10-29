"""The ``prompts/`` folder of a write phase, written without following a link.

Fix round 17 (the Fable review of round 16): a jailed repo-wide codex batch
can write the phase dir — ``plans/<stem>/<phase>`` lies inside the root
grant — and the plugin that keeps each dispatched prompt there is not jailed.
The check of round 16 (``prompts`` must not be a symlink) left two ways to
make the plugin write a prompt file outside the repository: replace the phase
dir itself with a link (the check resolved it and accepted wherever it led),
or swap ``prompts`` for a link between the check and the write. On the native
leg the host's own subagents can write the phase dir too, and ``util
write-prompt`` wrote through a link planted at the file's own name, which
overwrote the file the link named.

So nothing here resolves a path at write time. The phase dir is reached from
the repository root one component at a time, each opened ``O_DIRECTORY |
O_NOFOLLOW`` relative to the one above, and compared with the identity
(``st_dev``, ``st_ino``) pinned before any batch ran; ``prompts`` is opened
the same way below it; and every file is created ``O_EXCL | O_NOFOLLOW`` under
a temporary name and renamed into place, unlinked or listed relative to the
folder's descriptor. A component swapped for a link at any moment is refused,
never followed, and a link or a hard link at a file's name is replaced, never
written through. A platform without these calls (Windows, where no jail runs)
writes by path, checking each component with ``lstat``.

Standard library only, so both legs import it without a shim.
"""

from __future__ import annotations

import os
import stat
import tempfile
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple

__all__ = [
    "FOLDER",
    "PhasePin",
    "PromptFolder",
    "identify",
    "pin_phase_dir",
    "remove_held",
]

#: The folder under the phase dir: what ``util write-prompt`` writes on the
#: native leg and the scheduler keeps on the executor leg.
FOLDER = "prompts"

#: The temporary name prefix of a file being written.
TEMP_PREFIX = ".prompt-"

_CLOEXEC = getattr(os, "O_CLOEXEC", 0)

#: Whether every write can go through descriptors (Linux, macOS).
FD_RELATIVE = bool(
    hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY")
    and os.open in os.supports_dir_fd and os.mkdir in os.supports_dir_fd
    and os.unlink in os.supports_dir_fd and os.rename in os.supports_dir_fd
    and os.stat in os.supports_dir_fd and os.listdir in os.supports_fd
)


@dataclass(frozen=True)
class PhasePin:
    """Where a phase dir is, as the walk reaches it.

    ``root`` is opened by path (a link above the repository is the user's);
    each of ``parts`` is opened below it without following a link.
    ``identity`` is the phase dir's ``(st_dev, st_ino)`` when it was pinned,
    or ``None`` when nothing was pinned earlier.
    """

    root: str
    parts: Tuple[str, ...]
    identity: Optional[Tuple[int, int]] = None

    @property
    def path(self) -> str:
        return os.path.join(self.root, *self.parts)


def _check_name(name: str) -> str:
    """``name`` when it is one plain file name in the folder; else refused,
    since a name with a separator would walk out of the folder's descriptor."""
    text = str(name)
    if (
        not text or text in (os.curdir, os.pardir) or "\0" in text
        or os.sep in text or (os.altsep and os.altsep in text)
    ):
        raise OSError(f"{text!r} is not a file name")
    return text


def _why_not_a_folder(path: str, info: os.stat_result) -> Optional[str]:
    if stat.S_ISLNK(info.st_mode):
        return f"{path} is a symlink"
    if not stat.S_ISDIR(info.st_mode):
        return f"{path} is not a directory"
    return None


def _open_child(parent: int, name: str, shown: str) -> int:
    """``name`` under the descriptor ``parent``, opened as a directory and
    never through a link; refused in words when it is a link or a file."""
    try:
        return os.open(
            name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | _CLOEXEC,
            dir_fd=parent,
        )
    except OSError as exc:
        try:
            info = os.stat(name, dir_fd=parent, follow_symlinks=False)
        except OSError:
            raise exc
        problem = _why_not_a_folder(shown, info)
        if problem:
            raise OSError(problem) from exc
        raise


def _identity(info: os.stat_result) -> Tuple[int, int]:
    return (info.st_dev, info.st_ino)


def _replaced(pin: PhasePin) -> OSError:
    return OSError(
        f"{pin.path} is no longer the folder this run started with (it was "
        f"replaced while the run was going on)"
    )


def _walk(pin: PhasePin) -> int:
    """A descriptor of the phase dir, reached from ``pin.root`` without
    following a link, and checked against ``pin.identity``."""
    current = os.open(pin.root, os.O_RDONLY | os.O_DIRECTORY | _CLOEXEC)
    try:
        shown = pin.root
        for part in pin.parts:
            shown = os.path.join(shown, part)
            child = _open_child(current, part, shown)
            os.close(current)
            current = child
        if pin.identity is not None and _identity(os.fstat(current)) != pin.identity:
            raise _replaced(pin)
        return current
    except BaseException:
        os.close(current)
        raise


def _walk_by_path(pin: PhasePin) -> str:
    """:func:`_walk` where descriptors are not available: each component
    ``lstat``-checked, the identity compared by path."""
    shown = pin.root
    for part in pin.parts:
        shown = os.path.join(shown, part)
        problem = _why_not_a_folder(shown, os.lstat(shown))
        if problem:
            raise OSError(problem)
    if pin.identity is not None and _identity(os.stat(shown)) != pin.identity:
        raise _replaced(pin)
    return shown


def pin_phase_dir(phase_dir: str, repo_root: str) -> PhasePin:
    """Pin ``phase_dir`` under ``repo_root`` before any batch runs.

    Both are ``realpath``-resolved now; the phase dir must lie inside the
    repository, and its identity is taken through the same no-follow walk
    every later write makes, so a later write lands only in this directory.
    Raises ``OSError`` naming the problem (``FileNotFoundError`` while the
    phase dir does not exist yet: pin again later).
    """
    root = os.path.realpath(str(repo_root))
    real = os.path.realpath(str(phase_dir))
    try:
        relative = os.path.relpath(real, root)
    except ValueError:  # pragma: no cover - another drive on Windows
        relative = real
    parts = tuple(part for part in relative.split(os.sep) if part)
    if (
        os.path.isabs(relative) or not parts or parts == (os.curdir,)
        or parts[0] == os.pardir
    ):
        raise OSError(
            f"{phase_dir} resolves to {real}, which is not inside the "
            f"repository {root}"
        )
    return identify(PhasePin(root=root, parts=parts))


def identify(pin: PhasePin) -> PhasePin:
    """``pin`` with the identity of the directory its walk reaches now (no
    link followed), which every later :meth:`PromptFolder.open` of the
    returned pin must reach again."""
    bare = PhasePin(root=pin.root, parts=pin.parts)
    if FD_RELATIVE:
        handle = _walk(bare)
        try:
            identity = _identity(os.fstat(handle))
        finally:
            os.close(handle)
    else:
        identity = _identity(os.stat(_walk_by_path(bare)))
    return PhasePin(root=pin.root, parts=pin.parts, identity=identity)


class PromptFolder:
    """The open ``prompts`` folder of one pinned phase dir.

    ``with PromptFolder.open(pin) as folder:`` then :meth:`names`,
    :meth:`remove` and :meth:`write`, each relative to the folder itself.
    """

    def __init__(self, handle: Optional[int], path: str) -> None:
        self._handle = handle
        self.path = path

    @classmethod
    def open(cls, pin: PhasePin, *, create: bool = True) -> "PromptFolder":
        """Open ``{phase}/prompts``, creating it when ``create``.

        Raises ``OSError`` naming the problem: a component of the phase dir
        or ``prompts`` itself is a link or a file, the phase dir is not the
        pinned one, or (``create`` off) the folder does not exist.
        """
        shown = os.path.join(pin.path, FOLDER)
        if not FD_RELATIVE:
            phase = _walk_by_path(pin)
            if create:
                try:
                    os.mkdir(os.path.join(phase, FOLDER))
                except FileExistsError:
                    pass
            problem = _why_not_a_folder(shown, os.lstat(os.path.join(phase, FOLDER)))
            if problem:
                raise OSError(problem)
            return cls(None, shown)
        phase = _walk(pin)
        try:
            if create:
                try:
                    os.mkdir(FOLDER, dir_fd=phase)
                except FileExistsError:
                    pass
            handle = _open_child(phase, FOLDER, shown)
            try:
                if os.fstat(handle).st_dev != os.fstat(phase).st_dev:
                    raise OSError(f"{shown} is on another file system than {pin.path}")
            except BaseException:
                os.close(handle)
                raise
        finally:
            os.close(phase)
        return cls(handle, shown)

    def close(self) -> None:
        if self._handle is not None:
            os.close(self._handle)
            self._handle = None

    def __enter__(self) -> "PromptFolder":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def names(self) -> List[str]:
        """The folder's entry names."""
        if self._handle is None:
            return os.listdir(self.path)
        return os.listdir(self._handle)

    def remove(self, name: str) -> None:
        """Unlink ``name`` (never what a link names; a directory raises)."""
        name = _check_name(name)
        if self._handle is None:
            os.unlink(os.path.join(self.path, name))
        else:
            os.unlink(name, dir_fd=self._handle)

    def write(self, name: str, text: str) -> None:
        """Write ``text`` to ``name`` by a new file renamed into place: a link
        or a hard link at ``name`` is replaced, never written through, and a
        directory there raises."""
        name = _check_name(name)
        if self._handle is None:
            handle, temporary = tempfile.mkstemp(prefix=TEMP_PREFIX, dir=self.path)
            try:
                with os.fdopen(handle, "w", encoding="utf-8", newline="") as stream:
                    stream.write(text)
                os.replace(temporary, os.path.join(self.path, name))
            except BaseException:
                try:
                    os.unlink(temporary)
                except OSError:
                    pass
                raise
            return
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | _CLOEXEC
        for _ in range(100):
            temporary = TEMP_PREFIX + os.urandom(6).hex()
            try:
                handle = os.open(temporary, flags, 0o600, dir_fd=self._handle)
                break
            except FileExistsError:
                continue
        else:  # pragma: no cover - 100 collisions of 48 random bits
            raise FileExistsError(f"no free temporary name in {self.path}")
        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="") as stream:
                stream.write(text)
            os.replace(
                temporary, name,
                src_dir_fd=self._handle, dst_dir_fd=self._handle,
            )
        except BaseException:
            try:
                os.unlink(temporary, dir_fd=self._handle)
            except OSError:
                pass
            raise


# ---------------------------------------------------------------------------
# Windows: removing through handles held open (round-8 review, 2026-10-24)
# ---------------------------------------------------------------------------

_FILE_ATTRIBUTE_DIRECTORY = 0x10
_FILE_ATTRIBUTE_REPARSE_POINT = 0x400
#: The reparse-tag bit of a tag that names another path: a symlink, a
#: junction (``IsReparseTagNameSurrogate``). OneDrive's, ProjFS's and VFS for
#: Git's tags lack it: those are the directory or file they look like.
_NAME_SURROGATE_BIT = 0x20000000


class _WindowsFiles:  # pragma: no cover - Windows
    """The kernel32 calls :func:`remove_held` makes, typed for 64-bit handles."""

    _FILE_LIST_DIRECTORY = 0x0001
    _FILE_READ_ATTRIBUTES = 0x0080
    _DELETE = 0x00010000
    _SYNCHRONIZE = 0x00100000
    _FILE_SHARE_READ, _FILE_SHARE_WRITE, _FILE_SHARE_DELETE = 0x1, 0x2, 0x4
    _OPEN_EXISTING = 3
    _FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    _FILE_FLAG_BACKUP_SEMANTICS = 0x02000000  # what opens a directory at all
    _FILE_ATTRIBUTE_TAG_INFO = 9
    _FILE_DISPOSITION_INFO = 4

    def __init__(self) -> None:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle, boolean, dword = wintypes.HANDLE, wintypes.BOOL, wintypes.DWORD
        for name, argtypes, restype in (
            ("CreateFileW", [wintypes.LPCWSTR, dword, dword, ctypes.c_void_p,
                             dword, dword, handle], handle),
            ("GetFileInformationByHandleEx",
             [handle, ctypes.c_int, ctypes.c_void_p, dword], boolean),
            ("SetFileInformationByHandle",
             [handle, ctypes.c_int, ctypes.c_void_p, dword], boolean),
            ("GetFinalPathNameByHandleW", [handle, wintypes.LPWSTR, dword, dword], dword),
            ("CloseHandle", [handle], boolean),
        ):
            function = getattr(kernel32, name)
            function.argtypes, function.restype = argtypes, restype

        class TagInfo(ctypes.Structure):
            _fields_ = [("FileAttributes", dword), ("ReparseTag", dword)]

        class Disposition(ctypes.Structure):
            _fields_ = [("DeleteFile", wintypes.BOOLEAN)]

        self._ctypes = ctypes
        self._kernel32 = kernel32
        self._tag_info = TagInfo
        self._disposition = Disposition
        self._invalid = ctypes.c_void_p(-1).value

    def open(self, path: str, *, folder: bool) -> Optional[int]:
        """*path* itself, never what a reparse point there names. A folder is
        opened to list and shared for reading and writing only, so while it
        is held nobody can rename, remove or replace it; a file is opened to
        delete and shared fully, as ``os.unlink`` would find it."""
        if folder:
            access = self._FILE_LIST_DIRECTORY | self._FILE_READ_ATTRIBUTES | self._SYNCHRONIZE
            share = self._FILE_SHARE_READ | self._FILE_SHARE_WRITE
        else:
            access = self._DELETE | self._FILE_READ_ATTRIBUTES | self._SYNCHRONIZE
            share = self._FILE_SHARE_READ | self._FILE_SHARE_WRITE | self._FILE_SHARE_DELETE
        handle = self._kernel32.CreateFileW(
            path, access, share, None, self._OPEN_EXISTING,
            self._FILE_FLAG_OPEN_REPARSE_POINT | self._FILE_FLAG_BACKUP_SEMANTICS, None,
        )
        return None if handle in (None, self._invalid) else handle

    def attributes(self, handle: int) -> Tuple[int, int]:
        """``(FileAttributes, ReparseTag)`` of the opened file itself."""
        info = self._tag_info()
        if not self._kernel32.GetFileInformationByHandleEx(
            handle, self._FILE_ATTRIBUTE_TAG_INFO,
            self._ctypes.byref(info), self._ctypes.sizeof(info),
        ):
            raise self._ctypes.WinError(self._ctypes.get_last_error())
        return int(info.FileAttributes), int(info.ReparseTag)

    def final_path(self, handle: int) -> str:
        size = 512
        while True:
            buffer = self._ctypes.create_unicode_buffer(size)
            length = self._kernel32.GetFinalPathNameByHandleW(handle, buffer, size, 0)
            if not length:
                raise self._ctypes.WinError(self._ctypes.get_last_error())
            if length < size:
                return buffer.value
            size = length + 1

    def delete(self, handle: int) -> bool:
        """Mark the opened file deleted: it goes when the handle closes."""
        info = self._disposition(True)
        return bool(self._kernel32.SetFileInformationByHandle(
            handle, self._FILE_DISPOSITION_INFO,
            self._ctypes.byref(info), self._ctypes.sizeof(info),
        ))

    def close(self, handle: int) -> None:
        self._kernel32.CloseHandle(handle)


_WINDOWS_FILES: List[Any] = []


def _windows_files() -> Optional[Any]:
    """The Windows calls, loaded once; ``None`` where they cannot be."""
    if not _WINDOWS_FILES:
        try:
            _WINDOWS_FILES.append(_WindowsFiles())
        except Exception:  # noqa: BLE001 - the caller walks by path instead
            _WINDOWS_FILES.append(None)
    return _WINDOWS_FILES[0]


def _links_elsewhere(attributes: int, tag: int) -> bool:
    """A reparse point that names another path (a symlink, a junction)."""
    return bool(attributes & _FILE_ATTRIBUTE_REPARSE_POINT and tag & _NAME_SURROGATE_BIT)


def _same_path(left: str, right: str) -> bool:
    return os.path.normcase(left) == os.path.normcase(right)


def remove_held(
    phase_dir: str, wanted: Callable[[str], bool], *, api: Any = None,
) -> Optional[int]:
    """Windows: remove each file in ``{phase_dir}/prompts`` whose name
    *wanted* accepts; how many. ``None`` when the walk could not be made at
    all — the Windows calls cannot be loaded, a folder cannot be opened, or
    a call fails before any file is reached (a volume with no drive letter,
    a redirector without final paths) — so the caller can fall back to its
    path walk; ``0`` when a folder is refused (a link, not a directory, not
    the phase dir's own ``prompts``).

    Nothing is reached through a path that can be swapped between its check
    and its removal (round-8 review): the phase dir and ``prompts`` are each
    opened as themselves, never through a reparse point there, and held open
    without delete sharing, so neither can be renamed, removed or replaced
    until the walk ends; ``prompts`` is opened by the phase dir's final path
    and must be its child by both handles' final paths; and each file is
    opened as itself below that, must be a file in that folder, and is
    deleted through its own handle. A symlink or junction anywhere there
    removes nothing. A reparse point that names no other path (OneDrive Files
    On-Demand, a ProjFS or VFS for Git checkout) is the folder or file it
    looks like, so it is walked; ``lstat`` called it a link and the walk
    removed nothing there. Best-effort: a file that cannot be opened or
    deleted is left.
    """
    files = api if api is not None else _windows_files()
    if files is None:
        return None
    held: List[int] = []

    def hold_folder(path: str) -> Optional[str]:
        """The folder's final path, held open; ``None`` when it is refused.
        One that cannot be opened at all raises: no walk, not a refusal."""
        handle = files.open(path, folder=True)
        if handle is None:
            raise OSError(f"{path} could not be opened")
        held.append(handle)
        attributes, tag = files.attributes(handle)
        if not attributes & _FILE_ATTRIBUTE_DIRECTORY or _links_elsewhere(attributes, tag):
            return None
        return files.final_path(handle)

    removed = 0
    try:
        try:
            phase = hold_folder(str(phase_dir))
            if phase is None:
                return 0
            folder = hold_folder(os.path.join(phase, FOLDER))
            if folder is None or not _same_path(folder, os.path.join(phase, FOLDER)):
                return 0
            names = os.listdir(folder)
        except Exception:  # noqa: BLE001 - nothing reached yet: walk by path
            return None
        for name in names:
            if not wanted(name):
                continue
            entry = os.path.join(folder, name)
            handle = files.open(entry, folder=False)
            if handle is None:
                continue
            try:
                attributes, tag = files.attributes(handle)
                if (
                    attributes & _FILE_ATTRIBUTE_DIRECTORY
                    or _links_elsewhere(attributes, tag)
                    or not _same_path(files.final_path(handle), entry)
                ):
                    continue
                if files.delete(handle):
                    removed += 1
            except Exception:  # noqa: BLE001 - best-effort, like the descriptor walk
                continue
            finally:
                files.close(handle)
    except Exception:  # noqa: BLE001 - best-effort, like the descriptor walk
        return removed
    finally:
        for handle in reversed(held):
            try:
                files.close(handle)
            except Exception:  # noqa: BLE001 - a leaked handle is all it costs
                pass
    return removed
