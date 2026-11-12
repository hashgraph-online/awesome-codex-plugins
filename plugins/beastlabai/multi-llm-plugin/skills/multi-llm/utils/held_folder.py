"""A folder reached from a root without following a link and held by a
descriptor, and the writes beside a plan made through one.

Two things, below every writer that needs them (layer L0: the stdlib,
``atomic_io``, ``process_state`` and, for the platform's own calls,
``process_control`` only, so ``state_file`` and ``status_file`` can use them):

* **The walk and the hold** (:func:`_open_below_root`, :class:`_HeldFolder`):
  a folder below a root reached one component at a time, each opened
  ``O_DIRECTORY|O_NOFOLLOW`` relative to the one above, a missing one made on
  the way relative to its parent's descriptor, and held by its descriptor;
  :meth:`_HeldFolder.in_place` walks again to check it is still the folder at
  its path. ``write_safety``'s rollback restore and its plan-output writes
  (``write_below_root``, ``rename_below_root``, ``remove_below_root``) hold
  their folder this way, and import these names from here.
* **The plan directories** this process writes below (:func:`anchor_plan_dir`,
  each resolved once, when the run locates its outputs:
  ``output_handler.output_dir_path``, or when a command handed the state file
  alone takes its lock: ``state_file.locked``) and the writes, renames and removals made
  through a folder held below one (:func:`write_in_plan_dir`,
  :func:`rename_in_plan_dir`, :func:`remove_in_plan_dir`): ``state.json``,
  ``.status.json`` (and its archive when it is found damaged), the prompt
  sidecars and host views, the executor's JSON records (its results, its
  reports, the write scheduler's report) and the generate-tasks restore's
  ``state.json``. A link swapped in for any folder below the plan's directory
  during the run, the phase folder or the file's own folder, is refused,
  never followed.

See docs/development/write-safety.md#plan-output-containment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional, Sequence, Tuple, Union

from . import process_control
from .atomic_io import DIR_FD_SUPPORTED, atomic_write_bytes
from .process_state import process_cache

PathLike = Union[str, "os.PathLike[str]"]

_CLOEXEC = getattr(os, "O_CLOEXEC", 0)

#: How :func:`_open_below_root` (and ``write_safety.WritePolicy.open_permitted``)
#: opens the file it hands back: never
#: blocking on a FIFO swapped in, never inherited by a child, binary on Windows.
_READ_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_NONBLOCK", 0)
    | _CLOEXEC
    | getattr(os, "O_NOINHERIT", 0)
    | getattr(os, "O_BINARY", 0)
)

#: Whether a file below the root can be reached one component at a time, each
#: opened through its parent's descriptor and never through a link (Linux,
#: macOS). Windows' ``os.open`` takes no ``dir_fd`` and has no ``O_NOFOLLOW``.
OPENS_WITHOUT_FOLLOWING = bool(
    hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY")
    and os.open in os.supports_dir_fd
)


def _open_below_root(root: str, parts: Sequence[str], *,
                     folder: bool = False, make: bool = False) -> Optional[int]:
    """``root/parts`` opened for reading, every component below *root*
    opened through its parent's descriptor without following a link; ``None``
    when one is a link, is gone or is not a directory where one must be.
    With *folder*, ``root/parts`` is a directory too, its descriptor handed
    back (*root*'s own for no *parts*): the rollback restore holds the folder
    it puts a file back in this way (:class:`_HeldFolder`). With *make* too, a
    folder missing on the way is made relative to its parent's descriptor
    (``mkdirat``, which never follows a link) and then opened like the rest
    (``write_safety.write_below_root``, :func:`write_in_plan_dir`). *root* itself is opened by path: a link above
    the repository is the user's (``prompt_files`` walks the phase dir the
    same way)."""
    try:
        handle = os.open(root, os.O_RDONLY | os.O_DIRECTORY | _CLOEXEC)
    except OSError:
        return None
    try:
        for name in (parts if folder else parts[:-1]):
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | _CLOEXEC
            try:
                child = os.open(name, flags, dir_fd=handle)
            except FileNotFoundError:
                if not (make and folder):
                    raise
                try:
                    os.mkdir(name, dir_fd=handle)
                except FileExistsError:
                    pass
                child = os.open(name, flags, dir_fd=handle)
            os.close(handle)
            handle = child
        if folder:
            opened, handle = handle, -1
            return opened
        return os.open(parts[-1], _READ_FLAGS | os.O_NOFOLLOW, dir_fd=handle)
    except OSError:
        return None
    finally:
        if handle >= 0:
            os.close(handle)


#: Where a process's own descriptors are named (Linux): :meth:`_HeldFolder.where`
#: reads a moved folder's path there (:func:`_descriptor_path`); ``write_safety``
#: names an ``O_TMPFILE`` file through it (``linkat(2)`` with ``AT_EMPTY_PATH``
#: needs ``CAP_DAC_READ_SEARCH``).
_PROC_SELF_FD = "/proc/self/fd"


def _descriptor_path(fd: int) -> str:
    """The path the kernel holds now for the open folder *fd*, for a message
    alone: the link at :data:`_PROC_SELF_FD` (Linux), else ``fcntl(2)``'s
    ``F_GETPATH`` (macOS, which has no proc filesystem:
    ``process_control.descriptor_path``); ``""`` where neither answers. Both
    follow the folder when it is moved, which is what
    :meth:`_HeldFolder.where` asks of them. Never a containment check: that is
    the walk's (docs/development/write-safety.md says why, and that
    ``F_GETPATH`` spells the path as the kernel holds it, the link macOS
    keeps at the top of its temp folders resolved).

    Before macOS was read here, a folder moved during a write there was named
    only as "the folder that was at <its old path>", though the kernel knew
    where it had gone (the macOS CI leg, 2026-11-11)."""
    try:
        return os.readlink(f"{_PROC_SELF_FD}/{fd}")
    except OSError:
        return process_control.descriptor_path(fd)


@dataclass(frozen=True)
class _Wording:
    """How a write through a held folder names its work in a message. The
    rollback restore puts a snapshot's file back (:data:`_PUT_BACK`); the
    plan-output writes write a file (:data:`_WRITTEN`) or move one aside
    (:data:`_MOVED`). The steps and the refusals are the same
    (``write_safety._publish_staged``); only the words differ."""

    done: str
    staged: str
    ours: str
    kept: str
    actor: str
    root: str


_PUT_BACK = _Wording(
    done="put back", staged="the file staged to put back",
    ours="the snapshot's file", kept=" (the snapshot is kept)",
    actor="restore", root="the pinned repo root")
_WRITTEN = _Wording(
    done="written", staged="the file staged to write it",
    ours="the file written", kept="", actor="write", root="the folder")
_MOVED = _Wording(
    done="moved", staged="", ours="", kept="", actor="move", root="the folder")


@dataclass(frozen=True)
class _HeldFolder:
    """The folder a restore puts a file back in (Linux, macOS), reached from
    the pinned repo root one component at a time without following a link
    (:func:`_open_below_root`) and held by the descriptor *fd*, which every
    name in it is reached through. A writer of a folder above it can move it
    away and put another folder at its path at any moment, so it must still
    be the folder at its path (:meth:`in_place`) before anything is
    published in it, and again before the restore says ``restored``
    (docs/development/write-safety.md, restore). *root* and *parts* are the
    walk; *shown* is the folder's path as the restore names it; *say* is how
    its messages name the work (:class:`_Wording`): the plan-output writes
    hold their folder the same way (``write_safety.write_below_root``,
    :func:`write_in_plan_dir`)."""

    fd: int
    root: str
    parts: Tuple[str, ...]
    shown: str
    say: _Wording = _PUT_BACK

    @classmethod
    def open(cls, root: str, target: Path, *, make: bool = False,
             say: _Wording = _PUT_BACK, resolve_root: bool = True) -> "_HeldFolder":
        """*target*'s folder below *root*, which ``write_safety._revalidated_target``
        (or the caller's containment check) derived *target* under;
        ``OSError`` when a component on the way is gone, a link or not a
        folder. With *make*, a missing folder on the way is made, never
        through a link (:func:`_open_below_root`). *resolve_root* off: *root*
        is a plan's directory already resolved once for the run
        (:func:`anchor_plan_dir`), and is not resolved again."""
        resolved = str(Path(root).resolve()) if resolve_root else str(root)
        try:
            parts = tuple(target.parent.relative_to(resolved).parts)
        except ValueError:
            raise OSError(f"{target} is not below {say.root} {resolved}, so "
                          f"nothing was {say.done}") from None
        handle = _open_below_root(resolved, parts, folder=True, make=make)
        if handle is None:
            raise OSError(f"{target.parent} could not be reached from {say.root} "
                          f"{resolved} without following a link, so nothing was "
                          f"{say.done}")
        return cls(handle, resolved, parts, str(target.parent), say)

    def in_place(self) -> bool:
        """Whether a fresh walk from the root, without following a link,
        reaches the folder held (``(st_dev, st_ino)`` against ``fstat``)."""
        fresh = _open_below_root(self.root, self.parts, folder=True)
        if fresh is None:
            return False
        try:
            now, held = os.fstat(fresh), os.fstat(self.fd)
        except OSError:
            return False
        finally:
            os.close(fresh)
        return (now.st_dev, now.st_ino) == (held.st_dev, held.st_ino)

    def where(self, name: str, spelled: str) -> str:
        """Where *name* in the folder held is, for a message: *spelled*, its
        path as the restore spelled it, while the folder is in place; once it
        was moved, its path now (:func:`_descriptor_path`: through
        :data:`_PROC_SELF_FD` on Linux, ``F_GETPATH`` on macOS), else *name*
        in the folder that was at its path."""
        if self.in_place():
            return spelled
        now = _descriptor_path(self.fd)
        if os.path.isabs(now):
            return os.path.join(now, name)
        return f"{name} in the folder that was at {self.shown}"


def _folder_moved(folder: _HeldFolder, target: str) -> str:
    say = folder.say
    return (f"{folder.shown} is no longer the folder the {say.actor} opened: it "
            f"was moved or replaced while {target} was being {say.done}, so "
            f"nothing was {say.done}{say.kept}")


_REMOVED = _Wording(
    done="removed", staged="", ours="", kept="", actor="removal", root="the folder")


def _in_held_folder(root: Union[str, "os.PathLike[str]"], path: Path,
                    say: _Wording, act: Callable[[int], None], *,
                    resolve_root: bool = True) -> None:
    """Run *act* on the descriptor of *path*'s folder, held below *root*
    (:class:`_HeldFolder`), once that folder is still the one at its path."""
    folder = _HeldFolder.open(str(root), path, say=say, resolve_root=resolve_root)
    try:
        if not folder.in_place():
            raise OSError(_folder_moved(folder, str(path)))
        act(folder.fd)
    finally:
        os.close(folder.fd)

# ---------------------------------------------------------------------------
# The plan directories, and the writes below one through a held folder
# ---------------------------------------------------------------------------

#: The plan directories this process writes below: each spelling a writer may
#: give one (the absolute path the run spelled it with, and the directory
#: resolved), mapped to the directory as it resolved the first time the run
#: located its outputs there (:func:`anchor_plan_dir`). Emptied only by the
#: suite (``process_state``).
_PLAN_DIRS: Dict[str, str] = process_cache("utils.held_folder._PLAN_DIRS")

#: Whether a write below a plan's directory goes through its folder held
#: (Linux, macOS): the walk opens without following a link, a missing folder
#: is made relative to its parent's descriptor, and ``atomic_io`` writes
#: relative to the folder held (``dir_fd``). Windows writes by the checked path
#: instead (:func:`write_in_plan_dir`).
_WRITES_HELD = bool(
    OPENS_WITHOUT_FOLLOWING and DIR_FD_SUPPORTED and os.mkdir in os.supports_dir_fd
)


class OutsidePlanDir(OSError):
    """A file to write or remove below a plan's directory is in a folder that
    resolves outside it (a link in the plan's output folder leads out), so
    nothing was written or removed."""


def _key(path: str) -> str:
    return os.path.normcase(os.path.abspath(path))


def anchor_plan_dir(directory: PathLike) -> str:
    """Record *directory*, a plan's directory, as the root every write below
    it is held from (:func:`write_in_plan_dir`); the directory resolved.

    Resolved once: the first call for a spelling decides, and later calls
    hand that answer back, so a link swapped in later in the run, in the
    plan's output folder or above it, never moves the root. Its resolved
    spelling is recorded too, for a writer that resolved its folder at the
    start of the run. Cheap after the first call (no system call)."""
    spelled = os.path.abspath(os.fspath(directory))
    key = _key(spelled)
    resolved = _PLAN_DIRS.get(key)
    if resolved is None:
        resolved = _PLAN_DIRS.setdefault(key, os.path.realpath(spelled))
        _PLAN_DIRS.setdefault(_key(resolved), resolved)
    return resolved


def plan_dir_of(path: PathLike) -> Optional[str]:
    """The plan directory, resolved, that *path* is a file below by its
    spelling (absolute, not resolved): the deepest anchored one
    (:func:`anchor_plan_dir`); ``None`` when *path* is below none."""
    spelled = _key(os.fspath(path))
    found: Optional[Tuple[str, str]] = None
    for key, resolved in list(_PLAN_DIRS.items()):
        if spelled.startswith(key.rstrip(os.sep) + os.sep) and (
                found is None or len(key) > len(found[0])):
            found = (key, resolved)
    return found[1] if found else None


def _checked(path: PathLike, root: str, *, what: str) -> Path:
    """*path* with its folder resolved (its own name is not: a writer
    replaces a link at its name and never follows one), which must be *root*
    or below it, or :class:`OutsidePlanDir`."""
    spelled = os.path.abspath(os.fspath(path))
    folder = os.path.realpath(os.path.dirname(spelled))
    if not Path(folder).is_relative_to(root):
        raise OutsidePlanDir(
            f"Refusing to {what} {spelled}: its folder resolves to {folder}, outside "
            f"the plan's directory {root}, so nothing was {_done(what)}: a symlink in "
            f"the plan's output folder leads out of it. Remove the link and re-run.")
    return Path(folder, os.path.basename(spelled))


def _done(what: str) -> str:
    return {"remove": "removed", "move": "moved"}.get(what, "written")


def write_in_plan_dir(path: PathLike, data: bytes, *, make: bool = False,
                      mode: Optional[int] = None, keep_mode: bool = True,
                      fsync: bool = True, temp_prefix: Optional[str] = None) -> None:
    """``atomic_io.atomic_write_bytes(path, data, ...)`` with *mode*,
    *keep_mode*, *fsync* and *temp_prefix* as the writer always passed them,
    published through *path*'s folder held below the plan's directory
    (docs/development/write-safety.md#plan-output-containment).

    The root is the anchored plan directory *path* is below
    (:func:`plan_dir_of`), resolved once for the run. *path*'s folder must
    resolve inside it (:class:`OutsidePlanDir`); then, on Linux and macOS, it
    is reached from the root one component at a time without following a
    link, a missing one made relative to its parent's descriptor where *make*
    asks for the folder (as the writer's ``mkdir`` did), and held
    (:class:`_HeldFolder`). ``atomic_io`` writes relative to that descriptor
    (``dir_fd``): the temp file, the rename over the name (a link at the name
    is replaced, never followed) and the folder's flush. Just before the
    rename, and once after it, the folder must still be the one at its path
    (a fresh walk, :meth:`_HeldFolder.in_place`): a folder swapped for a link,
    or moved away, after the walk is refused (``OSError``), and never written
    through. Windows writes by the checked path (no ``dir_fd``, no
    ``O_NOFOLLOW``): a folder swapped for a link or junction after the check
    is still followed there.

    *path* below no anchored plan directory (a tool or a test given a folder
    directly) is written by its path, as the writer always wrote it.
    """
    root = plan_dir_of(path)
    if root is None:
        if make:
            os.makedirs(os.path.dirname(os.path.abspath(os.fspath(path))), exist_ok=True)
        atomic_write_bytes(path, data, keep_mode=keep_mode, fsync=fsync, mode=mode,
                           temp_prefix=temp_prefix)
        return
    target = _checked(path, root, what="write")
    if not _WRITES_HELD:
        if make:
            os.makedirs(target.parent, exist_ok=True)
        atomic_write_bytes(target, data, keep_mode=keep_mode, fsync=fsync, mode=mode,
                           temp_prefix=temp_prefix)
        return
    folder = _HeldFolder.open(root, target, make=make, say=_WRITTEN, resolve_root=False)
    try:
        def still_in_place() -> None:
            if not folder.in_place():
                raise OSError(_folder_moved(folder, str(target)))

        atomic_write_bytes(target.name, data, keep_mode=keep_mode, fsync=fsync,
                           mode=mode, temp_prefix=temp_prefix, dir_fd=folder.fd,
                           before_replace=still_in_place)
        if not folder.in_place():
            raise OSError(
                f"{folder.shown} was moved or replaced while {target} was being "
                f"written, so the file written is at "
                f"{folder.where(target.name, str(target))}, not at {target}; check both")
    finally:
        os.close(folder.fd)


def rename_in_plan_dir(path: PathLike, name: str) -> Path:
    """Rename the entry *path*, below the plan's directory, to *name* in the
    same folder, as :func:`write_in_plan_dir` writes one: relative to its
    folder held there, which must still be the one at its path, so a name is
    never moved in a folder a link swapped in leads to; the entry is renamed,
    never a link's target. Returns the new path; ``OSError`` when nothing was
    renamed. *path* below no anchored plan directory is renamed by its path.
    The caller picks a *name* that is free: like ``os.replace``, a file
    already at *name* is replaced."""
    spelled = Path(os.path.abspath(os.fspath(path)))
    renamed = spelled.with_name(name)
    root = plan_dir_of(path)
    if root is None:
        os.replace(spelled, renamed)
        return renamed
    target = _checked(path, root, what="move")
    if not _WRITES_HELD:
        os.replace(target, target.with_name(name))
        return renamed

    def rename(fd: int) -> None:
        os.replace(target.name, name, src_dir_fd=fd, dst_dir_fd=fd)

    _in_held_folder(root, target, _MOVED, rename, resolve_root=False)
    return renamed


def remove_in_plan_dir(path: PathLike) -> None:
    """Remove the name *path*, below the plan's directory, as
    :func:`write_in_plan_dir` writes one: relative to its folder held there,
    which must still be the one at its path, so a name is never removed in a
    folder a link swapped in leads to. A name already gone is nothing to
    remove; *path* below no anchored plan directory is removed by its path."""
    root = plan_dir_of(path)
    if root is None:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        return
    target = _checked(path, root, what="remove")
    if not _WRITES_HELD:
        try:
            os.unlink(target)
        except FileNotFoundError:
            pass
        return

    def remove(fd: int) -> None:
        try:
            os.unlink(target.name, dir_fd=fd)
        except FileNotFoundError:
            pass

    _in_held_folder(root, target, _REMOVED, remove, resolve_root=False)
