"""``state.json``, a plan's workflow state: its lock, readers and one writer.

``StateManager`` (``utils/state_manager.py``) owns the document's meaning.
This module owns the file, for the manager and for every raw reader and
writer outside it:

* :func:`locked`: the lock every read-modify-write of the file holds, an
  interprocess lock beside it plus a process-wide thread lock
  (``metrics.state_file_lock`` is the same function, under its old name).
* :func:`read_document` never raises and returns ``None`` for a missing,
  unreadable, malformed or non-object file; :func:`read_document_strict`
  raises instead (:class:`StateDocumentError` for a file that is there but
  holds no JSON object, which a command reports as its own refusal). A raw
  read creates, migrates and writes nothing, which is
  why the raw readers exist: a read-only look at a plan must not build a
  ``StateManager`` (its load upgrades legacy values and writes them back).
* :func:`write_document`: the one writer, ``atomic_io``'s atomic write of
  ``indent=2`` JSON (hosts read the file raw), owner-only, without ``fsync``,
  through the output folder held below the plan's directory
  (``held_folder.write_in_plan_dir``); :func:`write_bytes` is the same write
  of bytes a caller already has (the old-location move), and
  :func:`remove_document` the removal made the same way.
* :func:`update`: read, change and write the document under the lock.
* :class:`StateDoc`: the top-level keys the skill writes, the contract that
  ``schemas/state_file.schema.json`` follows (a test compares the two, and
  the keys ``StateManager``'s writers put in the file with both).

See docs/development/runtime.md#atomic-file-writes. Layer L1; it imports only
``process_control`` and the stdlib-only ``held_folder`` from the project.
"""

from __future__ import annotations

import contextlib
import copy
import json
import os
import threading
import time
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, TypedDict, Union

from . import process_control
from .held_folder import anchor_plan_dir, remove_in_plan_dir, write_in_plan_dir

PathLike = Union[str, "os.PathLike[str]"]

#: The state file's name, at the top of a plan's output folder.
STATE_FILENAME = "state.json"

#: The interprocess lock every read-modify-write of ``state.json`` holds
#: (:func:`locked`): a sibling of the state file, dot-prefixed, created on
#: demand and never unlinked (an unlinked lock file would put two writers on
#: two inodes of "the" lock; see ``process_control.FileMutex``).
STATE_LOCK_FILENAME = ".state.lock"

#: How long a state write waits for its turn. A holder runs one JSON read and
#: write plus, for ``util batch-done`` and ``util finalize-tracking``, the
#: dirty-tree census (seconds on a large repository); a host that records
#: several parallel tasks at once queues that many. Generous, because the only
#: thing the bound is for is a holder that is stopped rather than dead.
STATE_LOCK_TIMEOUT_S = 120.0

#: The temp-file prefix of :func:`write_document` when the caller names none.
#: Every writer's temp file ends in ``.tmp`` (``output_handler`` reads such a
#: dot-file as the workflow's own).
STATE_TEMP_PREFIX = ".state_"


def _anchor_plan_dir_of(state_path: PathLike) -> None:
    """Record the plan's directory *state_path* is written below
    (``held_folder.anchor_plan_dir``): the state file sits in the plan's
    output folder, whose parent is the plan's directory, so a command handed
    the file alone (``--state-file``) records that grandparent. The first
    record for a spelling decides; a run that located its outputs made it
    already (docs/development/write-safety.md#plan-output-containment)."""
    anchor_plan_dir(os.path.dirname(os.path.dirname(os.path.abspath(state_path))))


class StateLockTimeout(OSError):
    """The state-file lock was not free in time; nothing was written."""


class StateDocumentError(ValueError):
    """The state file was read but holds no JSON object: not UTF-8, not
    JSON, or another top-level value. ``detail`` says which, without the
    path; a caller turns it into its own handled refusal."""

    def __init__(self, path: PathLike, detail: str) -> None:
        super().__init__(f"{path}: {detail}")
        self.path = os.fspath(path)
        self.detail = detail


#: Serializes this process's own state writes across threads; the file lock
#: serializes processes. Reentrant, because a holder may call a helper that
#: takes the lock again (see :func:`locked`).
_STATE_THREAD_LOCK = threading.RLock()

#: The state-file locks this process holds, by lock path. Only touched under
#: :data:`_STATE_THREAD_LOCK`, so a present key is this thread's outer frame.
_HELD_STATE_LOCKS: Dict[str, Any] = {}


@contextlib.contextmanager
def locked(state_path: PathLike) -> Iterator[None]:
    """Hold ``<state dir>/.state.lock`` for one read-modify-write of *state_path*.

    The native write leg's per-batch records are separate processes the host
    may start in parallel — implement.md lets same-batch tasks run together,
    and ``util batch-done`` reads ``state.json``, runs the dirty-tree census
    and writes the whole file back — so two unlocked records read the same
    file and the later write dropped the earlier one's ``task_status``.
    ``util batch-done``, ``util metrics record|start|finish``,
    ``util finalize-tracking`` and ``StateManager.save`` take this lock from
    their read to their write.

    Reentrant within a process (an inner frame does not take the file lock a
    second time: an OS lock is per open file, so it would wait on itself). A
    state file whose directory does not exist yet has nothing to lock. One
    deadline, :data:`STATE_LOCK_TIMEOUT_S` from entry, bounds both waits: for
    another thread of this process (:data:`_STATE_THREAD_LOCK`, process-wide,
    so a thread writing another plan's state counts) and then for another
    process (the file lock gets what is left). A lock not free by then raises
    :class:`StateLockTimeout` and the caller writes nothing: an unserialized
    write is exactly the lost record this lock exists to prevent. The
    same-thread reentry takes neither wait. It is the innermost lock: nothing
    else is taken while it is held.

    Entry records the plan's directory as the root the write is held from
    (:func:`_anchor_plan_dir_of`), before the read this lock is held around:
    a command handed the state file alone keeps the directory it read from,
    so one swapped for a link between its read and its write is refused.
    """
    _anchor_plan_dir_of(state_path)
    timeout_s = STATE_LOCK_TIMEOUT_S
    deadline = time.monotonic() + max(0.0, float(timeout_s))
    if not _STATE_THREAD_LOCK.acquire(timeout=max(0.0, float(timeout_s))):
        raise StateLockTimeout(
            f"another thread of this process held the state lock for "
            f"{timeout_s:g}s while it was writing state (perhaps of another "
            f"plan), so nothing was written to {state_path}. Run this command "
            f"again once that write has finished."
        )
    try:
        folder = os.path.dirname(os.path.abspath(str(state_path)))
        key = os.path.realpath(os.path.join(folder, STATE_LOCK_FILENAME))
        if key in _HELD_STATE_LOCKS or not os.path.isdir(folder):
            yield
            return
        mutex = process_control.FileMutex(key)
        if not mutex.acquire(timeout_s=max(0.0, deadline - time.monotonic()),
                             poll_interval_s=0.02):
            raise StateLockTimeout(
                f"{key} was not free within {timeout_s:g}s: another multi-llm "
                f"command is still writing {state_path} (or the lock file "
                f"cannot be opened), so nothing was written. Run this command "
                f"again once that one has finished."
            )
        _HELD_STATE_LOCKS[key] = mutex
        try:
            yield
        finally:
            del _HELD_STATE_LOCKS[key]
            mutex.release()
    finally:
        _STATE_THREAD_LOCK.release()


def read_document_strict(path: PathLike) -> Dict[str, Any]:
    """*path*'s document. Raises ``OSError`` (``FileNotFoundError`` for no
    file) or :class:`StateDocumentError`, a ``ValueError`` (not UTF-8, not
    JSON, or not a JSON object)."""
    with open(path, "r", encoding="utf-8") as handle:
        try:
            document = json.load(handle)
        except ValueError as exc:  # JSONDecodeError, UnicodeDecodeError
            raise StateDocumentError(path, f"not UTF-8 JSON ({exc})") from exc
    if not isinstance(document, dict):
        raise StateDocumentError(
            path, f"the top-level value is {type(document).__name__}, not an object"
        )
    return document


def read_document(path: PathLike) -> Optional[Dict[str, Any]]:
    """*path*'s document, or ``None`` when it is missing, unreadable,
    malformed or not a JSON object. Never raises for any of those."""
    try:
        return read_document_strict(path)
    except (OSError, ValueError):
        return None


def write_document(path: PathLike, document: Dict[str, Any], *,
                   temp_prefix: str = STATE_TEMP_PREFIX) -> str:
    """Replace *path* with *document*; the JSON text written.

    ``indent=2``, ``\\n`` newlines, UTF-8, owner-only (0600), by ``atomic_io``'s
    atomic write: a reader sees the old file or the new one. No ``fsync``, as
    every writer of the file always had: it is rewritten dozens of times a
    run under :func:`locked`, where a flush (milliseconds each) would hold up
    every waiting writer. The parent folder is created if missing. Hold
    :func:`locked` around the read this write is based on.

    The file is published through its folder held below the plan's directory
    (``held_folder.write_in_plan_dir``), so a link swapped in for the output
    folder during the run is refused, never written through
    (docs/development/write-safety.md#plan-output-containment). The root is
    the one recorded when the run located its outputs, or else by
    :func:`locked` before the read; a write made without either records it
    here (:func:`_anchor_plan_dir_of`)."""
    text = json.dumps(document, indent=2)
    write_bytes(path, text.encode("utf-8"), temp_prefix=temp_prefix)
    return text


def write_bytes(path: PathLike, data: bytes, *,
                temp_prefix: str = STATE_TEMP_PREFIX) -> None:
    """Replace *path* with *data* as given: :func:`write_document`'s write
    (owner-only, no ``fsync``, the folder made, published through it held
    below the plan's directory) for a caller that has the file's bytes
    rather than a document, ``StateManager``'s move of a state file from its
    old location (docs/development/write-safety.md#plan-output-containment).
    Hold :func:`locked` around it."""
    _anchor_plan_dir_of(path)
    write_in_plan_dir(path, data, make=True, mode=0o600, fsync=False,
                      temp_prefix=temp_prefix)


def remove_document(path: PathLike) -> None:
    """Remove *path* the way :func:`write_document` writes it: through its
    folder held below the plan's directory (``held_folder.remove_in_plan_dir``),
    so a name is never removed in a folder a link swapped in leads to. A file
    already gone is nothing to remove. Hold :func:`locked` around it."""
    _anchor_plan_dir_of(path)
    remove_in_plan_dir(path)


@contextlib.contextmanager
def update(
    path: PathLike, *, temp_prefix: str = STATE_TEMP_PREFIX,
    on_invalid: Optional[Callable[[StateDocumentError], BaseException]] = None,
) -> Iterator[Dict[str, Any]]:
    """Read *path*'s document, hand it to the body to change, and write it
    back, all under :func:`locked`.

    The read is :func:`read_document_strict`, so a missing or malformed file
    raises before the body runs; *on_invalid* turns the read's
    :class:`StateDocumentError` into the caller's own refusal (the exception
    it returns is raised from it), and only the read's: one the body raises
    passes through. The document is written only when the body returns
    normally and the document differs from what was read; an exception, or a
    body that changed nothing, leaves the file as it was."""
    with locked(path):
        try:
            document = read_document_strict(path)
        except StateDocumentError as exc:
            if on_invalid is None:
                raise
            raise on_invalid(exc) from exc
        before = copy.deepcopy(document)
        yield document
        if document != before:
            write_document(path, document, temp_prefix=temp_prefix)


class StateDoc(TypedDict, total=False):
    """The top-level keys of ``state.json`` the skill writes, besides the
    per-phase families of :data:`STATE_KEY_PREFIXES`.

    The written contract: ``schemas/state_file.schema.json`` lists exactly
    these properties, and every key a ``StateManager`` writer puts in the
    file is one of them (``tests/test_state_file.py`` checks both). Adding a
    key means a line here and a property there."""

    schema_version: str
    plan_path: str
    plan_hash: str
    plan_changed: bool
    plan_preamble: str
    created_at: str
    updated_at: str
    head_at_start: str
    head_before_implement: str
    head_ref: Dict[str, Any]
    branch_name: str
    commit_range: Dict[str, Any]
    review_phase_completed: bool
    review_scope_files: List[Any]
    phases_completed: Dict[str, Any]
    phases_skipped: Dict[str, Any]
    phases_started: Dict[str, Any]
    state_resets: Dict[str, Any]
    full_workflow: Dict[str, Any]
    tracked_files: List[Any]
    pre_existing_changes: List[Any]
    metrics: Dict[str, Any]
    metrics_progress: Dict[str, Any]
    metrics_left_out: Dict[str, Any]
    metrics_set_aside: Dict[str, Any]
    scope_policy: Dict[str, Any]
    scope_policy_runs: Dict[str, Any]
    apply_fix_batch_checks: Dict[str, Any]
    batch_snapshot_records: Dict[str, Any]
    dependency_overrides: Dict[str, Any]
    human_task_strategy: str
    human_task_decisions: Dict[str, Any]
    implement_task_ids: List[str]
    implement_human_task_ids: List[str]
    implement_task_depends_on: Dict[str, Any]
    implement_task_reset_at: Dict[str, Any]
    task_status: Dict[str, Any]
    task_status_reasons: Dict[str, Any]
    task_titles: Dict[str, Any]
    task_check_findings: Dict[str, Any]
    task_check_trees: Dict[str, Any]
    task_batch_check: Dict[str, Any]
    task_batch_check_accepted: Dict[str, Any]
    task_batch_check_repeats: Dict[str, Any]
    task_own_check_note: Dict[str, Any]
    task_own_check_ran: List[Any]
    task_own_text: Dict[str, Any]


#: The per-phase key families: ``<prefix><phase>`` (``processed_apply``,
#: ``human_decisions_code_review``, ...). The schema has one
#: ``patternProperties`` entry ``^<prefix>`` for each.
STATE_KEY_PREFIXES: Tuple[str, ...] = (
    "human_decisions_",
    "human_decision_unresolved_",
    "human_decision_verdicts_",
    "processed_",
    "progress_",
)
