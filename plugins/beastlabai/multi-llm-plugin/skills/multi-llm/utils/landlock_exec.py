#!/usr/bin/env python3
"""``plugin-landlock``: jail a command's writes with Landlock, then ``exec`` it.

``landlock_exec.py [--allow KIND:PATH]... [--allow-optional KIND:PATH]... -- CMD [ARGS...]``

**Why this exists.** On a host where Codex's own sandbox cannot start (bwrap
needs a user namespace the kernel refuses), the sandbox ladder used to have one
rung left: ``danger-full-access``, with nothing between the model's commands and
the repository. This wrapper is the rung in between. It applies a Landlock
ruleset to *itself* that handles every filesystem write right, grants those
rights only beneath the entries it was given, sets ``NO_NEW_PRIVS``, restricts
itself and ``exec``\\s the command. The domain is inherited, so the command and
everything it spawns can read anything and write only where the parent allowed.
It is a fallback, never a replacement: a dispatch whose standard sandbox probe
passes never comes here (plan ``codex-sandbox-unavailable-findings-and-fixes``,
§6 F1 "Where it sits").

**It fails closed, and it decides nothing.**

* **ABI floor 3 (Linux 6.2).** ABI 1 and 2 have no ``TRUNCATE`` right, and
  before it truncation is always allowed: ``truncate(2)`` would empty any repo
  file while a create-only canary still passed. So below the floor the wrapper
  exits :data:`EXIT_UNAVAILABLE` exactly as when Landlock is absent. There is no
  reduced mode with a weaker mask.
* **The syscall numbers come from a table keyed by machine name**
  (:data:`SYSCALLS`) and are never assumed. Any other machine is unavailable,
  with a note naming it.
* **Every entry is opened once**, ``O_PATH | O_NOFOLLOW | O_CLOEXEC``, and that
  descriptor is ``fstat``\\ed, so the rule lands on the inode that was checked.
  A *required* entry that is missing, a symlink or not of its declared kind
  exits :data:`EXIT_REQUIRED_ENTRY` before any ruleset exists. Only optional
  entries (``/dev/ptmx``, ``/dev/pts``) are skipped, with a note.
* **The wrapper never creates a path and never resolves a symlink.** The parent
  ``realpath``-resolved every entry and made every directory it grants. A symlink
  seen here appeared after that resolution, which is exactly what must not be
  granted. (``O_NOFOLLOW`` binds the final component only; the parent's
  resolution covers the rest.)
* **It knows no job kind.** Which entries a dispatch gets is the parent's
  decision (``allow_entries``); this file only enforces them.

**Rights.** A ``dir`` entry gets the whole handled mask beneath it; a ``file``
entry (any non-directory, ``/dev/null`` included) gets ``WRITE_FILE | TRUNCATE``:
Landlock refuses directory rights on a file rule with ``EINVAL``, and those two
are what an in-place edit needs. Reads, execute, ``IOCTL_DEV`` and the network
are not handled, so they stay unrestricted (plan F1 Limits).

**Launch: ``sys.executable -I -S`` and stdlib only.** Nothing but this file may
run before ``landlock_restrict_self``. ``-I`` keeps ``PYTHONPATH``, the other
``PYTHON*`` variables, user site-packages and this script's own directory off
``sys.path``, so nothing can shadow ``ctypes``, ``os`` or ``struct``. ``-S``
skips ``site``, so no ``.pth`` line executes first. For the same reason this
module never imports the ``utils`` package, even though it lives inside it.

**Exit codes**, each chosen not to collide with Python's own exit 2
(``can't open file``: a packaging fault must never read as a probe result):

============================  ====  =============================================
constant                      code  meaning
============================  ====  =============================================
:data:`EXIT_USAGE`            122   bad arguments; nothing was checked
:data:`EXIT_REQUIRED_ENTRY`   125   a required entry is missing, a symlink or of
                                    the wrong kind; no ruleset was created
:data:`EXIT_UNAVAILABLE`      126   no Landlock (``ENOSYS``, ``EOPNOTSUPP``), an
                                    ABI below :data:`ABI_FLOOR`, an unknown
                                    machine, or a Landlock call that failed; the
                                    command never ran
:data:`EXIT_EXEC_FAILED`      127   the jail was applied but ``execvp`` failed
============================  ====  =============================================

**Diagnostics.** Every note is one stderr line, :data:`NOTE_PREFIX` then a
stable reason word: ``usage:``, ``unavailable:``, ``required-entry:``,
``optional-entry-skipped:`` or ``exec-failed:``. The parent keys on the exit
code; the line is for the person reading the report.

**The seam.** :class:`Kernel` holds the Landlock calls; :func:`main` takes a
``kernel``, an ``execvp`` and a ``stderr``, so every decision above is
unit-tested with a fake and no kernel (plan §8.1, tier 1).
"""

import ctypes
import errno
import os
import platform
import stat
import struct
import sys

# ---------------------------------------------------------------------------
# Exit codes and the note prefix (the interface the parent depends on)
# ---------------------------------------------------------------------------

#: The lowest Landlock ABI the wrapper accepts: 3 is the first with ``TRUNCATE``.
ABI_FLOOR = 3

EXIT_UNAVAILABLE = 126
EXIT_REQUIRED_ENTRY = 125
EXIT_USAGE = 122
EXIT_EXEC_FAILED = 127

NOTE_PREFIX = "landlock_exec: "

USAGE = (
    "landlock_exec.py [--allow KIND:PATH]... [--allow-optional KIND:PATH]... "
    "-- CMD [ARGS...]"
)

FLAG_REQUIRED = "--allow"
FLAG_OPTIONAL = "--allow-optional"
KIND_DIR = "dir"
KIND_FILE = "file"
KINDS = (KIND_DIR, KIND_FILE)

#: Optional entries whose absence costs Codex its pseudo-terminals. The note
#: says so, because the failure it predicts surfaces much later, inside a turn.
TTY_ENTRIES = frozenset({"/dev/ptmx", "/dev/pts"})
TTY_NOTE = "tty: true exec sessions will fail (failed to openpty)"

# ---------------------------------------------------------------------------
# The kernel ABI
# ---------------------------------------------------------------------------

#: ``landlock_create_ruleset``, ``landlock_add_rule``, ``landlock_restrict_self``
#: by ``uname -m``. The generic syscall table gives both the same numbers; that
#: is asserted here per machine rather than assumed for all of them.
SYSCALLS = {"x86_64": (444, 445, 446), "aarch64": (444, 445, 446)}

LANDLOCK_CREATE_RULESET_VERSION = 1
LANDLOCK_RULE_PATH_BENEATH = 1
PR_SET_NO_NEW_PRIVS = 38

# ``LANDLOCK_ACCESS_FS_*`` (include/uapi/linux/landlock.h).
EXECUTE = 1 << 0
WRITE_FILE = 1 << 1
READ_FILE = 1 << 2
READ_DIR = 1 << 3
REMOVE_DIR = 1 << 4
REMOVE_FILE = 1 << 5
MAKE_CHAR = 1 << 6
MAKE_DIR = 1 << 7
MAKE_REG = 1 << 8
MAKE_SOCK = 1 << 9
MAKE_FIFO = 1 << 10
MAKE_BLOCK = 1 << 11
MAKE_SYM = 1 << 12
REFER = 1 << 13      # ABI 2
TRUNCATE = 1 << 14   # ABI 3
IOCTL_DEV = 1 << 15  # ABI 5: deliberately never handled

#: The ten write rights ABI 1 knows.
WRITE_RIGHTS_ABI1 = (
    WRITE_FILE | REMOVE_DIR | REMOVE_FILE | MAKE_CHAR | MAKE_DIR | MAKE_REG
    | MAKE_SOCK | MAKE_FIFO | MAKE_BLOCK | MAKE_SYM
)

#: What a ``file`` entry is granted: an in-place write, and its truncation.
FILE_RIGHTS = WRITE_FILE | TRUNCATE

#: ``struct landlock_ruleset_attr`` carries ``handled_access_fs`` (ABI 1),
#: ``handled_access_net`` (ABI 4) and ``scoped`` (ABI 6). Only the first 8
#: bytes are passed: the kernel requires at least ``offsetofend(
#: handled_access_fs)`` and zero-fills the fields it knows beyond the size it
#: was given, so 8 bytes is accepted by every ABI and leaves the network and
#: scope fields 0. The jail handles no network right and scopes nothing.
RULESET_ATTR_SIZE = 8

#: ``struct landlock_path_beneath_attr`` is ``__attribute__((packed))``:
#: ``__u64 allowed_access`` then ``__s32 parent_fd``, 12 bytes, no padding.
PATH_BENEATH_ATTR_SIZE = 12


def handled_mask(abi: int) -> int:
    """The write rights the ruleset handles on a kernel of *abi*.

    The same set on every accepted kernel: ABI 1's ten write rights, ``REFER``
    from ABI 2, ``TRUNCATE`` from ABI 3. It is still derived from the running
    ABI because an older kernel rejects a right it does not know; with the floor
    at 3 that only matters for a right newer than ABI 3, and ``IOCTL_DEV`` is
    never one of them. Never a reason to run below :data:`ABI_FLOOR`.
    """
    mask = WRITE_RIGHTS_ABI1
    if abi >= 2:
        mask |= REFER
    if abi >= 3:
        mask |= TRUNCATE
    return mask


def ruleset_attr(mask: int) -> bytes:
    """``handled_access_fs`` alone, :data:`RULESET_ATTR_SIZE` bytes."""
    return struct.pack("=Q", mask)


def path_beneath_attr(rights: int, path_fd: int) -> bytes:
    """The packed ``landlock_path_beneath_attr`` for one rule."""
    return struct.pack("=Qi", rights, path_fd)


class Kernel:
    """The real Landlock calls, through libc's ``syscall(2)``.

    The seam :func:`main` is tested through: a fake with the same six methods
    returns a chosen ABI or raises, and records what it was asked to apply.
    Every failure is an :class:`OSError` carrying the kernel's errno.
    """

    def __init__(self) -> None:
        self._libc = None

    def machine(self) -> str:
        """``uname -m`` on Linux; elsewhere the platform is named too, so a
        non-Linux ``x86_64`` never matches a Linux syscall table row."""
        name = platform.machine()
        if sys.platform.startswith("linux"):
            return name
        return f"{name} ({sys.platform})"

    def abi(self) -> int:
        """``landlock_create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION)``."""
        return self._syscall(0, None, 0, LANDLOCK_CREATE_RULESET_VERSION)

    def create_ruleset(self, mask: int) -> int:
        """A ruleset handling *mask*; returns its (close-on-exec) descriptor."""
        data = ruleset_attr(mask)
        attr = ctypes.create_string_buffer(data, len(data))
        return self._syscall(0, attr, len(data), 0)

    def add_rule(self, ruleset_fd: int, rights: int, path_fd: int) -> None:
        """One ``LANDLOCK_RULE_PATH_BENEATH`` rule on *path_fd*'s inode."""
        data = path_beneath_attr(rights, path_fd)
        attr = ctypes.create_string_buffer(data, len(data))
        self._syscall(1, ruleset_fd, LANDLOCK_RULE_PATH_BENEATH, attr, 0)

    def no_new_privs(self) -> None:
        """``prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)``, which an unprivileged
        ``landlock_restrict_self`` requires."""
        libc = self._load()
        ctypes.set_errno(0)
        rc = libc.prctl(
            ctypes.c_int(PR_SET_NO_NEW_PRIVS), ctypes.c_ulong(1),
            ctypes.c_ulong(0), ctypes.c_ulong(0), ctypes.c_ulong(0),
        )
        if rc != 0:
            raise _errno_error()

    def restrict(self, ruleset_fd: int) -> None:
        """``landlock_restrict_self(ruleset_fd, 0)``: from here on, this process
        and everything it ``exec``\\s is jailed."""
        self._syscall(2, ruleset_fd, 0)

    # -- plumbing -----------------------------------------------------------

    def _load(self):
        if self._libc is None:
            libc = ctypes.CDLL(None, use_errno=True)
            libc.syscall.restype = ctypes.c_long
            libc.prctl.restype = ctypes.c_int
            self._libc = libc
        return self._libc

    def _syscall(self, index: int, *args) -> int:
        numbers = SYSCALLS.get(self.machine())
        if numbers is None:
            raise OSError(errno.ENOSYS, os.strerror(errno.ENOSYS))
        # Every integer goes in as a full ``long``: syscall(2) is variadic and
        # reads each argument as one, so a narrower type would leave the upper
        # half of the register undefined.
        converted = [
            arg if arg is None or isinstance(arg, ctypes.Array) else ctypes.c_long(arg)
            for arg in args
        ]
        libc = self._load()
        ctypes.set_errno(0)
        rc = libc.syscall(ctypes.c_long(numbers[index]), *converted)
        if rc < 0:
            raise _errno_error()
        return int(rc)


def _errno_error() -> OSError:
    code = ctypes.get_errno()
    return OSError(code, os.strerror(code))


# ---------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------

class UsageError(ValueError):
    """An argument the wrapper cannot act on. Always :data:`EXIT_USAGE`."""


class Entry:
    """One allow-list entry: a declared kind, a path, and whether it is required."""

    __slots__ = ("kind", "path", "required")

    def __init__(self, kind: str, path: str, required: bool) -> None:
        self.kind = kind
        self.path = path
        self.required = required

    @property
    def spec(self) -> str:
        return f"{self.kind}:{self.path}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Entry):
            return NotImplemented
        return (self.kind, self.path, self.required) == (
            other.kind, other.path, other.required)

    def __repr__(self) -> str:
        flag = FLAG_REQUIRED if self.required else FLAG_OPTIONAL
        return f"Entry({flag} {self.spec})"


def parse_entry(spec: str, required: bool) -> Entry:
    """``KIND:PATH``, split at the *first* colon: a path may contain colons,
    a kind never does."""
    kind, sep, path = spec.partition(":")
    if not sep:
        raise UsageError(f"entry {spec!r} is not KIND:PATH")
    if kind not in KINDS:
        raise UsageError(
            f"entry {spec!r} has unknown kind {kind!r} (expected dir or file)")
    if not path:
        raise UsageError(f"entry {spec!r} has an empty path")
    return Entry(kind, path, required)


def parse_args(argv):
    """``(entries, command)``: the entries in order, and the argv after the
    *first* ``--``, verbatim (the command may carry ``--`` of its own)."""
    argv = list(argv)
    if "--" not in argv:
        raise UsageError("no '--' before the command")
    split = argv.index("--")
    options, command = argv[:split], argv[split + 1:]
    if not command:
        raise UsageError("empty command after '--'")
    entries = []
    index = 0
    while index < len(options):
        flag = options[index]
        if flag not in (FLAG_REQUIRED, FLAG_OPTIONAL):
            raise UsageError(f"unknown option {flag!r}")
        if index + 1 >= len(options):
            raise UsageError(f"{flag} needs KIND:PATH")
        entries.append(parse_entry(options[index + 1], flag == FLAG_REQUIRED))
        index += 2
    return entries, command


# ---------------------------------------------------------------------------
# Entries
# ---------------------------------------------------------------------------

REASON_MISSING = "missing"
REASON_SYMLINK = "symlink"
REASON_WRONG_KIND = "wrong-kind"


def open_entry(entry: Entry):
    """``(fd, None)`` for an entry the rule can land on, else ``(None, reason)``.

    One ``O_PATH | O_NOFOLLOW`` open, then ``fstat`` on that descriptor: a
    symlink opens as itself and reads ``S_ISLNK``, and the kind is judged on the
    same inode the rule will be bound to, never on a second lookup. Any open
    failure is ``missing``: there is no inode here to grant.
    """
    try:
        fd = os.open(entry.path, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError:
        return None, REASON_MISSING
    try:
        mode = os.fstat(fd).st_mode
    except OSError:
        os.close(fd)
        return None, REASON_MISSING
    if stat.S_ISLNK(mode):
        os.close(fd)
        return None, REASON_SYMLINK
    if stat.S_ISDIR(mode) != (entry.kind == KIND_DIR):
        os.close(fd)
        return None, REASON_WRONG_KIND
    return fd, None


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------

#: A hint for the errnos whose meaning is not obvious from ``strerror``.
#: ``getattr``: the module must import on every platform the suite runs on.
_ERRNO_HINTS = {
    code: hint for code, hint in (
        (getattr(errno, "ENOSYS", None), "no Landlock in this kernel"),
        (getattr(errno, "EOPNOTSUPP", None),
         "Landlock is built in but not enabled at boot"),
    ) if code is not None
}


#: Names the Landlock docs use where ``errno.errorcode`` picks an alias: on
#: Linux ``EOPNOTSUPP`` and ``ENOTSUP`` share a number and the table says the
#: latter, while the kernel documents the former.
_ERRNO_NAMES = {
    code: name for code, name in (
        (getattr(errno, "EOPNOTSUPP", None), "EOPNOTSUPP"),
    ) if code is not None
}


def _errno_text(exc: OSError) -> str:
    if exc.errno is None:
        return str(exc)
    name = _ERRNO_NAMES.get(exc.errno) or errno.errorcode.get(exc.errno, str(exc.errno))
    text = f"{name}, {exc.strerror or os.strerror(exc.errno)}"
    hint = _ERRNO_HINTS.get(exc.errno)
    return f"{text}; {hint}" if hint else text


def _note(stream, text: str) -> None:
    """One line, always: a path carrying a newline cannot split a note."""
    line = text.replace("\r", "\\r").replace("\n", "\\n")
    stream.write(f"{NOTE_PREFIX}{line}\n")
    stream.flush()


def bootstrap_streams() -> None:
    """Make stderr UTF-8 before a note carries a non-ASCII path.

    A stdlib copy of ``utils.stream_bootstrap.bootstrap_streams``, which this
    file may not import (nothing from ``utils`` runs before the ruleset). Named
    the same so the entry-point guard counts it. ``backslashreplace`` rather
    than ``replace``: the notes carry paths, and a path's bytes matter more than
    tidy output. Only stderr: the wrapper writes nothing else, and the command
    it ``exec``\\s gets the file descriptors, not these Python objects.
    """
    reconfigure = getattr(sys.stderr, "reconfigure", None)
    if reconfigure is None:
        return
    try:
        reconfigure(line_buffering=True, encoding="utf-8", errors="backslashreplace")
    except (AttributeError, ValueError, OSError):
        pass


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv=None, *, kernel=None, execvp=os.execvp, stderr=None) -> int:
    """Apply the jail and ``exec`` the command; return an exit code on failure.

    Order is the contract: arguments, machine, ABI, every entry, and only then
    the ruleset. A required-entry failure therefore leaves no ruleset behind,
    and an unusable kernel is reported before any path is touched. With the
    real ``os.execvp`` a success never returns; a fake that returns gives 0.
    """
    argv = sys.argv[1:] if argv is None else list(argv)
    stream = sys.stderr if stderr is None else stderr

    try:
        entries, command = parse_args(argv)
    except UsageError as exc:
        _note(stream, f"usage: {exc}; expected {USAGE}")
        return EXIT_USAGE

    kernel = Kernel() if kernel is None else kernel
    machine = kernel.machine()
    if machine not in SYSCALLS:
        known = ", ".join(sorted(SYSCALLS))
        _note(stream, f"unavailable: machine {machine!r} is not in the syscall "
                      f"table ({known})")
        return EXIT_UNAVAILABLE

    try:
        abi = int(kernel.abi())
    except OSError as exc:
        _note(stream, f"unavailable: Landlock ABI none ({_errno_text(exc)}); "
                      f"the floor is {ABI_FLOOR}")
        return EXIT_UNAVAILABLE
    if abi < ABI_FLOOR:
        _note(stream, f"unavailable: Landlock ABI {abi} found; the floor is "
                      f"{ABI_FLOOR} (below it truncation cannot be denied)")
        return EXIT_UNAVAILABLE
    mask = handled_mask(abi)

    opened = []
    try:
        failed = []
        skipped = []
        for entry in entries:
            fd, reason = open_entry(entry)
            if fd is not None:
                opened.append((entry, fd))
            elif entry.required:
                failed.append((entry, reason))
            else:
                skipped.append((entry, reason))
        if failed:
            for entry, reason in failed:
                _note(stream, f"required-entry: {entry.spec}: {reason}")
            return EXIT_REQUIRED_ENTRY
        for entry, reason in skipped:
            tail = f"; {TTY_NOTE}" if entry.path in TTY_ENTRIES else ""
            _note(stream, f"optional-entry-skipped: {entry.spec}: {reason}{tail}")

        try:
            ruleset_fd = kernel.create_ruleset(mask)
        except OSError as exc:
            _note(stream, f"unavailable: landlock_create_ruleset failed "
                          f"({_errno_text(exc)})")
            return EXIT_UNAVAILABLE
        for entry, fd in opened:
            rights = mask if entry.kind == KIND_DIR else FILE_RIGHTS & mask
            try:
                kernel.add_rule(ruleset_fd, rights, fd)
            except OSError as exc:
                _note(stream, f"unavailable: landlock_add_rule failed for "
                              f"{entry.spec} ({_errno_text(exc)})")
                return EXIT_UNAVAILABLE
        try:
            kernel.no_new_privs()
        except OSError as exc:
            _note(stream, f"unavailable: PR_SET_NO_NEW_PRIVS failed "
                          f"({_errno_text(exc)})")
            return EXIT_UNAVAILABLE
        try:
            kernel.restrict(ruleset_fd)
        except OSError as exc:
            _note(stream, f"unavailable: landlock_restrict_self failed "
                          f"({_errno_text(exc)})")
            return EXIT_UNAVAILABLE
    finally:
        for _entry, fd in opened:
            os.close(fd)

    try:
        execvp(command[0], command)
    except OSError as exc:
        _note(stream, f"exec-failed: {command[0]}: {exc.strerror or exc}")
        return EXIT_EXEC_FAILED
    return 0


if __name__ == "__main__":
    bootstrap_streams()
    sys.exit(main())
