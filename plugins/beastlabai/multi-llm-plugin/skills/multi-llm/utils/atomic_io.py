"""One atomic file write: a temp file beside the target, flushed, renamed in.

A reader of the target sees the old bytes or the new ones, never part of
either, and a failed write leaves the old bytes and no temp file. Every
replace-a-file-whole writer in the skill goes through here, so the guarantees
are the same everywhere and a call site states only how it differs (no
``fsync`` for a file rewritten many times a run, an explicit mode, writing
through a symlink):

* the temp file sits in the target's directory (the same volume, which is what
  makes ``os.replace`` atomic, on Windows too) and is created exclusively
  (``O_EXCL``: a file or symlink already at its name is never opened);
* while it holds bytes it is owner-only, and never readable more widely
  than its final mode: replacing an existing file, or with an explicit
  *mode*, it is created owner-only (0600); a new file with no explicit mode
  is created empty with the mode ``open()`` would give it (the umask's, read
  back with ``fstat``: the process umask is never set), narrowed to
  owner-only before its first byte (where the filesystem keeps modes);
  either way it gets its final mode only once written;
* the mode is applied before the ``fsync``, so data and mode reach the disk
  together, then ``os.replace``, then (POSIX) the directory is flushed so a
  returned call survives a power loss;
* a failure closes the descriptor, gives the temp file back its owner write
  bit if the final mode had taken it away (Windows deletes no read-only
  file), and removes it;
* with *dir_fd*, the target is a name in a directory the caller holds open,
  and every step (create, rename, removal, directory flush) is relative to
  that descriptor, so a link swapped in for the directory, or for one above
  it, is never followed (POSIX); *before_replace* lets that caller check the
  directory is still the one at its path just before the rename.

See docs/development/runtime.md#atomic-file-writes. Stdlib only; layer L0
(``tests/test_import_layers.py``).
"""

from __future__ import annotations

import io
import os
import secrets
import stat
from typing import Callable, Optional, Tuple, Union

PathLike = Union[str, "os.PathLike[str]"]

#: The temp file's suffix. Folders the workflow owns treat a dot-file with it
#: as its own leftover (``output_handler._WORKFLOW_DOTFILE_SUFFIXES``).
TEMP_SUFFIX = ".tmp"

#: ``O_BINARY`` keeps the Windows CRT from translating newlines: the bytes
#: handed in are the bytes written.
_CREATE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)

#: The temp file's bits while it holds bytes the final mode may not yet allow.
_OWNER_ONLY = 0o600

#: Whether a write can be made relative to a held directory (*dir_fd*):
#: POSIX, not Windows. Read once, at import.
DIR_FD_SUPPORTED = all(call in os.supports_dir_fd for call in (os.open, os.rename, os.unlink))


def temp_path_for(target: str, prefix: Optional[str] = None) -> str:
    """The temp file name used for *target*: ``<prefix><pid>.<random>.tmp``
    beside it, the prefix defaulting to ``.<target name>.``."""
    directory = os.path.dirname(target)
    if prefix is None:
        prefix = f".{os.path.basename(target)}."
    name = f"{prefix}{os.getpid()}.{secrets.token_hex(4)}{TEMP_SUFFIX}"
    return os.path.join(directory, name)


def flush_directory(directory: PathLike, *, dir_fd: Optional[int] = None) -> None:
    """Flush *directory*'s entries (a rename into it) to disk, best-effort;
    with *dir_fd*, the directory that descriptor holds (*directory* unused).

    POSIX only: Windows cannot open a directory for this, and NTFS journals
    the rename itself."""
    if os.name == "nt":
        return
    if dir_fd is not None:
        try:
            os.fsync(dir_fd)
        except OSError:
            pass
        return
    try:
        descriptor = os.open(os.fspath(directory) or os.curdir,
                             os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def _at(dir_fd: Optional[int]) -> dict:
    """The keyword that makes a call relative to *dir_fd*; none by path, so
    the call is the plain one."""
    return {} if dir_fd is None else {"dir_fd": dir_fd}


def _existing_mode(target: str, dir_fd: Optional[int] = None) -> Optional[int]:
    """The permission bits of the file a reader of *target* sees now (through
    a symlink), or ``None`` when there is none."""
    try:
        return stat.S_IMODE(os.stat(target, **_at(dir_fd)).st_mode)
    except (FileNotFoundError, NotADirectoryError):
        return None


def _apply_mode(descriptor: int, temporary: str, mode: int,
                dir_fd: Optional[int] = None) -> None:
    if hasattr(os, "fchmod"):
        os.fchmod(descriptor, mode)
    else:  # Windows before 3.13: only the read-only bit exists
        os.chmod(temporary, mode, **_at(dir_fd))


def _narrow(descriptor: int, temporary: str, mode: int,
            dir_fd: Optional[int] = None) -> bool:
    """Narrow a new temp file to *mode* before its first byte; whether it
    was. A filesystem that keeps no modes (FAT, some network and FUSE
    mounts) refuses the change, and the file keeps the mode ``open()`` gave
    it: never wider than a plain write's."""
    try:
        _apply_mode(descriptor, temporary, mode, dir_fd)
    except OSError:
        return False
    return True


def _close_owned(descriptor: int, identity: Optional[Tuple[int, int]]) -> None:
    """Close this write's *descriptor*, which no stream owns. Before
    ``os.fdopen`` (*identity* ``None``) it is ours; after a failed one, only
    while it still names the file created (``(st_dev, st_ino)``):
    ``fdopen`` closes it itself when it fails after wrapping it, and by then
    the number may be another file's."""
    if identity is not None:
        try:
            now = os.fstat(descriptor)
        except OSError:
            return
        if (now.st_dev, now.st_ino) != identity:
            return
    try:
        os.close(descriptor)
    except OSError:
        pass


#: Windows refuses to delete a read-only file; POSIX unlinks one as it is, and
#: a chmod by name there could follow a link swapped in for the temp.
_CLEAR_READ_ONLY_BEFORE_UNLINK = os.name == "nt"


def _discard(temporary: str, read_only: bool, dir_fd: Optional[int] = None) -> None:
    """Remove this write's own temp file, best-effort. A read-only one gets
    its owner write bit back first: Windows refuses to delete a read-only
    file (a read-only target's mode was copied onto it)."""
    if read_only and _CLEAR_READ_ONLY_BEFORE_UNLINK:
        try:
            os.chmod(temporary, _OWNER_ONLY, **_at(dir_fd))
        except OSError:
            pass
    try:
        os.unlink(temporary, **_at(dir_fd))
    except OSError:
        pass


def _name_in(target: str, dir_fd: Optional[int], follow_symlinks: bool) -> str:
    """*target* checked for a write relative to *dir_fd*: one plain name,
    never followed through a link. Raises ``ValueError``."""
    if follow_symlinks:
        raise ValueError("follow_symlinks cannot be combined with dir_fd")
    if not DIR_FD_SUPPORTED:
        raise ValueError("this platform writes by path only (no dir_fd)")
    separators = {os.sep, os.altsep or os.sep}
    if (not target or target in (os.curdir, os.pardir)
            or any(sep in target for sep in separators)):
        raise ValueError(f"{target!r} is not a single name in the held directory")
    return target


def atomic_write_bytes(
    path: PathLike,
    data: bytes,
    *,
    keep_mode: bool = True,
    fsync: bool = True,
    mode: Optional[int] = None,
    follow_symlinks: bool = False,
    temp_prefix: Optional[str] = None,
    dir_fd: Optional[int] = None,
    before_replace: Optional[Callable[[], None]] = None,
) -> None:
    """Replace *path* with *data*, atomically.

    - *keep_mode*: an existing file's permission bits carry over to the
      replacement. Off, the replacement gets a new file's mode (the umask's).
    - *mode*: the replacement's exact permission bits, whatever the old file
      or the umask say (it overrides *keep_mode*).
    - *fsync*: flush the file before the rename and the directory after it.
      Off only for a file rewritten so often that the flush would cost more
      than a lost last write (``state.json``, under its lock).
    - *follow_symlinks*: a symlink at *path* is written through, so the link
      survives and its target gets the bytes. Off, the link itself is
      replaced by a regular file (its target is left alone; *keep_mode* reads
      the mode through the link).
    - *temp_prefix*: the temp file's name before ``<pid>.<random>.tmp``, for a
      caller whose leftovers something matches by name.
    - *dir_fd*: *path* is one name in the directory this descriptor holds
      open, and the temp file is created, renamed, removed and its directory
      flushed relative to it: a link swapped in for that directory, or for a
      folder above it, after the caller opened it is never followed. POSIX
      (``os.supports_dir_fd``); *follow_symlinks* stays off (``ValueError``).
    - *before_replace*: called once the temp file is written, given its mode
      and flushed, just before the rename; whatever it raises aborts the write
      as any failure does. ``utils/held_folder.py`` checks there that the
      folder it holds (*dir_fd*) is still the one at its path.

    The directory must exist. Raises ``OSError`` (``FileExistsError`` if the
    temp name is taken); on any exception the temp file is removed and the
    old file is untouched.
    """
    target = os.fspath(path)
    if dir_fd is not None:
        target = _name_in(target, dir_fd, follow_symlinks)
    elif follow_symlinks:
        target = os.path.realpath(target)
    final_mode = mode
    if final_mode is None and keep_mode:
        final_mode = _existing_mode(target, dir_fd)
    temporary = temp_path_for(target, temp_prefix)
    if dir_fd is not None:
        # The temp is created relative to the held folder too: one plain name.
        _name_in(temporary, dir_fd, False)
    descriptor = os.open(temporary, _CREATE_FLAGS, 0o666 if final_mode is None else 0o600,
                         **_at(dir_fd))
    # Ours from here: on any failure the descriptor is closed and the file
    # removed.
    identity: Optional[Tuple[int, int]] = None
    stream = None
    read_only = False
    apply_final = final_mode is not None
    try:
        created = os.fstat(descriptor)
        if final_mode is None:
            # The umask's mode, read off the empty file; the bytes go in
            # owner-only and the mode comes back before the fsync.
            final_mode = stat.S_IMODE(created.st_mode)
            if final_mode & ~_OWNER_ONLY:
                apply_final = _narrow(descriptor, temporary, final_mode & _OWNER_ONLY, dir_fd)
        identity = (created.st_dev, created.st_ino)
        stream = os.fdopen(descriptor, "wb")
        with stream:
            stream.write(data)
            stream.flush()
            if apply_final:
                _apply_mode(stream.fileno(), temporary, final_mode, dir_fd)
            read_only = not final_mode & stat.S_IWUSR
            if fsync:
                os.fsync(stream.fileno())
        if before_replace is not None:
            before_replace()
        if dir_fd is None:
            os.replace(temporary, target)
        else:
            os.replace(temporary, target, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
    except BaseException:
        if stream is None:
            _close_owned(descriptor, identity)
        _discard(temporary, read_only, dir_fd)
        raise
    if fsync:
        flush_directory(os.path.dirname(target), dir_fd=dir_fd)


def atomic_write_text(
    path: PathLike,
    text: str,
    *,
    newline: str = "\n",
    keep_mode: bool = True,
    fsync: bool = True,
    mode: Optional[int] = None,
    follow_symlinks: bool = False,
    temp_prefix: Optional[str] = None,
    dir_fd: Optional[int] = None,
) -> bytes:
    """:func:`atomic_write_bytes` of *text* as UTF-8; the bytes written.

    Each ``\\n`` is written as *newline*, ``\\n`` by default, so the bytes
    are the same on every platform. ``newline=os.linesep`` writes what a
    text-mode ``write_text`` would, for a caller that has always written the
    platform's newlines."""
    if newline != "\n":
        text = text.replace("\n", newline)
    data = text.encode("utf-8")
    atomic_write_bytes(
        path, data, keep_mode=keep_mode, fsync=fsync, mode=mode,
        follow_symlinks=follow_symlinks, temp_prefix=temp_prefix, dir_fd=dir_fd,
    )
    return data


def read_back_text(data: bytes) -> str:
    """*data* as a text-mode read of a file holding it returns it: UTF-8, with
    universal newlines (``open(path, encoding="utf-8").read()``). A caller that
    read a file's bytes once, or holds the bytes it wrote, parses this, so it
    parses what a second, text-mode read would have returned without making
    one (docs/development/review-results.md, "Consuming checked bytes")."""

    return io.TextIOWrapper(io.BytesIO(data), encoding="utf-8").read()
