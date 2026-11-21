"""A review round's identity: one random id per fan-out, recorded by its files.

A review phase's fan-out (review-plan, review-tasks, review-code) stamps a
fresh :data:`ROUND_KEY` into ``{phase}/.status.json`` (:func:`start_round`)
right past its detach boundary, before it replaces or retires any file of the
previous round, and carries it in its opening checkpoint write. Every
validation file and report the round writes records the same id:

* ``validation_tasks.json``: a top-level ``round_id``
  (``validation.RoundProvenance.round_id``, written by
  ``materialize_validation_round``);
* ``validation.json``: ``metadata.round_id``, copied from the task file the
  merge read (``merge_validation_batches``), so the verdicts carry the round
  of the prompts that produced them;
* ``report.md``: the line right after its first
  (``report_markdown.round_line``).

A ``--reaggregate`` continues the round on record: it writes the checkpoint's
id and never a new one. Against the checkpoint, a file is the round's own
(:data:`OWNED`) when its id is the same, another round's (:data:`STALE`) when
it differs, and proves nothing (:data:`LEGACY`) when either side has none: a
file written before round ids, a writer that records none (an empty round's
``validation.json`` is a bare ``[]``) or a checkpoint without one. Readers
keep their conservative rule for a legacy file. The id is a random token, not
a time: a clock set back, a copy that kept its dates or a coarse file system
cannot make an earlier round's file pass for this one's.

The validation batch files carry no id: a host's subagents write them as the
validator replied. They follow the task file beside them: a regroup that
changes the grouping retires them with the round, and the merge joins each
verdict to its group by hash (docs/development/review-results.md, "Round
identity").

Two runs never write one phase dir at once: each review run holds the
dir's ``.lock`` from its entry to its exit and a second is refused there
(``detach.PhaseRun``; docs/development/runtime.md, "One writer per phase
dir"); a live holder's lock is never broken, and a run's exit waits for its
dispatch threads before it lets go. The claim below is defence in depth
behind that lock: should another round be stamped regardless (a lock file
removed by hand), nothing this run publishes passes for it, and a result file
its batch dispatch persists late is dropped (:func:`results_bound_to`).

An invocation captures its round once, as a :class:`Claim` (:func:`start_round`
for a fan-out, :func:`continue_round` for a ``--reaggregate``), and every
writer takes the id from the claim, never from the checkpoint again. Each
publication and completion decision re-reads the checkpoint under its mutex
(:meth:`Claim.held`) and stops the run at exit 3 unless the checkpoint still
records the claim's round. Both checks fail closed: a mutex that cannot be
taken, or a checkpoint that no longer records an id the claim established,
stops the run as surely as another round's id does, and a checkpoint that
cannot be read stops it with the advice every such stop gives
(``status_file.unreadable_checkpoint_advice``). ``report.md``'s round line
also seals the report: it records the digest of the exact ``validation.json``
bytes its verdicts came from (:class:`Verdicts`, captured as the claim wrote or
read them, never by reading the path again; only when they record the claim's
round, so a report never claims a round its verdicts did not come from) and of
its own text below the line (:func:`report_seal`).
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import secrets
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Mapping, NamedTuple, Optional, Sequence, Tuple, Union

from . import report_markdown, status_file
from .atomic_io import atomic_write_bytes, atomic_write_text
from .cli_common import EXIT_NEEDS_HUMAN

#: The key that holds the round id: top level in ``.status.json`` and the task
#: file, under ``metadata`` in ``validation.json``.
ROUND_KEY = "round_id"

#: What a recorded id must look like; anything else is read as no id.
_ROUND_RE = re.compile(r"[0-9a-f]{16,64}")

#: A file's ownership against the checkpoint's round (module docstring).
OWNED = "owned"
STALE = "stale"
LEGACY = "legacy"

#: The checkpoint word that ties a task file *without* a round id to the run
#: ``.status.json`` records: every writer of the task file writes it next, and
#: every fan-out's opening write replaces it (``utils/resume_state.py``).
VALIDATION_PENDING = "validation_pending"

TASKS_NAME = "validation_tasks.json"
VALIDATION_NAME = "validation.json"
REPORT_NAME = "report.md"

PathLike = Union[str, Path]


def new_round_id() -> str:
    """A fresh round id: 16 hex characters from the OS's random source."""
    return secrets.token_hex(8)


def valid_round(value: Any) -> Optional[str]:
    """*value* when it is a round id, else ``None``."""
    return value if isinstance(value, str) and _ROUND_RE.fullmatch(value) else None


def status_round(status: Mapping[str, Any]) -> Optional[str]:
    """The round a ``.status.json`` document records, or ``None``."""
    return valid_round(status.get(ROUND_KEY)) if isinstance(status, Mapping) else None


def current_round(phase_dir: PathLike) -> Optional[str]:
    """The round *phase_dir*'s checkpoint records, or ``None``."""
    return status_round(status_file.read_status(str(phase_dir)))


#: The checkpoint word a stamp writes with the new id: the fan-out's own
#: opening word. One update replaces both, so an earlier
#: :data:`VALIDATION_PENDING` never stands beside the new id and an id-less
#: task file is never read as the new round's (:func:`tasks_file_is_this_rounds`).
FANOUT_STATE = "models_running"


def start_round(phase_dir: PathLike, *, notes: Sequence[str] = ()) -> "Claim":
    """Stamp a fresh round id into *phase_dir*'s checkpoint; this run's claim.

    Called by a fan-out right past its detach boundary, before it replaces or
    retires anything, so an interruption from then on leaves the previous
    round's files reading as another round's. The same update writes
    ``state: models_running`` (:data:`FANOUT_STATE`). The fan-out's opening
    ``write_status`` carries the same id (:meth:`Claim.opening`).

    The stamp and its read-back are one step under the checkpoint mutex, and
    the claim is established only when the id read back is its own: a mutex
    that cannot be taken, or a stamp that did not land, stops the run at exit
    3 before any model is called. So does a checkpoint that cannot be read
    (``status_file.load_status``, read up to
    ``status_file.CHECKPOINT_READ_ATTEMPTS`` times), which the stamp never
    writes over: it may record answers the phase withholds
    (docs/development/review-results.md, "Withheld slot answers"). A damaged
    one was recovered before the boundary, by the fan-out's startup
    (``review_lane.recover_damaged_checkpoint``), never here: a detached
    worker claims its run in the checkpoint before this is reached.

    *notes* are the round's own result notes from its start (that recovery's
    warning): :attr:`Claim.notes`, which the opening write records
    (``review_lane.open_round``).
    """
    round_id = new_round_id()
    # The dir the round is recorded in exists before the stamp (the phase-dir
    # helper creates it; a caller that skipped it would otherwise lose the id).
    Path(phase_dir).mkdir(parents=True, exist_ok=True)
    claim = Claim(str(phase_dir), round_id, started=True, notes=tuple(notes))
    with claim._mutex("start its fan-out"):
        try:
            status_file.load_status(
                str(phase_dir), attempts=status_file.CHECKPOINT_READ_ATTEMPTS,
            )
        except status_file.CheckpointUnreadable:
            raise _unreadable(claim, "start its fan-out") from None
        status_file.update_status(str(phase_dir), {ROUND_KEY: round_id, "state": FANOUT_STATE})
        recorded = current_round(phase_dir)
    if recorded != round_id:
        raise _taken_over(claim, recorded, "start its fan-out")
    return claim


def continue_round(phase_dir: PathLike) -> "Claim":
    """A ``--reaggregate``'s claim: the round *phase_dir*'s checkpoint records
    now (``None``: a checkpoint written before round ids). It never stamps one."""
    return Claim(str(phase_dir), current_round(phase_dir), started=False)


class RoundTakenOver(SystemExit):
    """Exit 3 from a run that cannot prove the checkpoint still records its
    round. A ``SystemExit``, so no ``except Exception`` on the way out turns
    the stop into a report or a completion."""


class Verdicts(NamedTuple):
    """The ``validation.json`` a report's verdicts came from, as the bytes the
    claim wrote or read: the round they record and their digest."""

    round_id: Optional[str]
    digest: str


def verdicts_of(data: bytes) -> Verdicts:
    """:class:`Verdicts` for these exact ``validation.json`` bytes."""
    try:
        recorded = validation_document_round(json.loads(data)) if data else None
    except ValueError:
        recorded = None
    return Verdicts(recorded, digest(data))


@dataclass(frozen=True)
class Claim:
    """The round one invocation writes for, captured once.

    ``started``: this invocation's fan-out stamped it; otherwise a
    ``--reaggregate`` continues the round on record. Every artifact the
    invocation writes records ``round_id`` (the task file, the report), and
    every publication and completion decision runs under :meth:`held`.
    :attr:`verdicts` is the ``validation.json`` this invocation last wrote or
    read for its report.
    """

    phase_dir: str
    round_id: Optional[str]
    started: bool = False
    #: Result notes the round brings from its start (:func:`start_round`).
    notes: Tuple[str, ...] = field(default=(), compare=False)
    _verdicts: List[Verdicts] = field(default_factory=list, compare=False, repr=False)
    #: The result files the latest dispatch bound to this claim persisted or
    #: found complete, by name, as the bytes it wrote or checked and whether
    #: it wrote them itself (:func:`record_checked_result`).
    _results: Dict[str, Tuple[bytes, bool]] = field(
        default_factory=dict, compare=False, repr=False)
    #: The ``batch_provenance`` rows the latest dispatch's report recorded for
    #: those result files, by report kind (:func:`record_batch_provenance`).
    _provenance: Dict[str, Dict[str, Dict[str, Any]]] = field(
        default_factory=dict, compare=False, repr=False)
    #: The ``grouped.json`` text this invocation last wrote or read
    #: (:meth:`hold_grouping`).
    _grouping: List[str] = field(default_factory=list, compare=False, repr=False)

    def describe(self) -> str:
        if self.started:
            return f"started review round {self.round_id}"
        if self.round_id:
            return f"continues review round {self.round_id}"
        return "continues a round with no id"

    def taken_over_by(self, recorded: Optional[str]) -> bool:
        """Whether a checkpoint recording *recorded* (``None``: no id) fails
        to prove the phase is still this claim's. A claim with an id holds
        only while the checkpoint records that id: another round's id is a
        takeover, and so is a checkpoint that lost it, since nothing then
        ties the dir to this run (fail closed). A claim with no id (a
        ``--reaggregate`` of a round from before ids) is taken over by any
        round stamped since."""
        if self.round_id is None:
            return recorded is not None
        return recorded != self.round_id

    @contextlib.contextmanager
    def _mutex(self, doing: str) -> Iterator[None]:
        """The checkpoint mutex, taken or the run stops: a decision about the
        round is never made unserialized."""
        with contextlib.ExitStack() as stack:
            try:
                stack.enter_context(
                    status_file.checkpoint_lock(self.phase_dir, required=True))
            except status_file.CheckpointLockUnavailable:
                raise _unlocked(self, doing) from None
            yield

    @contextlib.contextmanager
    def held(self, doing: str) -> Iterator[None]:
        """Run the block under the checkpoint mutex, after checking that the
        checkpoint still records this claim's round (:meth:`taken_over_by`);
        otherwise print why and raise :class:`RoundTakenOver`. A round stamped
        by another run cannot land between the check and the block's writes,
        and a mutex that cannot be taken stops the run too.

        A checkpoint that cannot be read (``status_file.load_status``, read up
        to ``status_file.CHECKPOINT_READ_ATTEMPTS`` times) is neither a
        missing round nor another one: the run stops with the shared advice
        (``status_file.unreadable_checkpoint_advice``), not the takeover's
        ``--force``. It is never recovered here: mid-run, the round's records
        are in that file, and only a fresh run's startup, holding the phase,
        may replace it (docs/development/review-results.md, "Withheld slot
        answers")."""
        with self._mutex(doing):
            try:
                status = status_file.load_status(
                    self.phase_dir, attempts=status_file.CHECKPOINT_READ_ATTEMPTS,
                )
            except status_file.CheckpointUnreadable:
                raise _unreadable(self, doing) from None
            recorded = status_round(status or {})
            if self.taken_over_by(recorded):
                raise _taken_over(self, recorded, doing)
            yield

    def check(self, doing: str) -> None:
        """:meth:`held` with nothing inside: a run that lost its round stops here."""
        with self.held(doing):
            pass

    @contextlib.contextmanager
    def opening(self) -> Iterator[None]:
        """The fan-out's opening checkpoint write, under :meth:`held`. Only
        :func:`start_round` establishes a round; this write carries it, and a
        write that landed without the id (checkpoint writes are best effort)
        gets it put back before the mutex is released, so the run's later
        checks still find it."""
        with self.held("write its opening checkpoint"):
            yield
            if self.round_id and current_round(self.phase_dir) is None:
                status_file.update_status(self.phase_dir, {ROUND_KEY: self.round_id})

    def publish(self, path: PathLike, data: Union[bytes, str], doing: str) -> bytes:
        """Replace *path* with *data* atomically, while this claim holds; the
        bytes written."""
        with self.held(doing):
            return replace_file(path, data)

    def publish_verdicts(self, path: PathLike, data: Union[bytes, str]) -> Verdicts:
        """Publish ``validation.json`` (:meth:`publish`) and remember the exact
        bytes written as this invocation's :attr:`verdicts`."""
        written = self.publish(path, data, "write validation.json")
        return self._remember(verdicts_of(written))

    def read_verdicts(self, path: PathLike) -> bytes:
        """Read ``validation.json`` once for the report; remembers those bytes
        as :attr:`verdicts` and returns them for the caller to parse."""
        return self.hold_verdicts(Path(path).read_bytes())

    def hold_verdicts(self, data: bytes) -> bytes:
        """The ``validation.json`` bytes a caller has already read and checked,
        remembered as :attr:`verdicts` and returned for it to parse: the report
        binds the bytes it was built from, never a later read of the file."""
        self._remember(verdicts_of(data))
        return data

    def hold_grouping(self, text: str) -> None:
        """Remember the ``grouped.json`` this invocation reports, as the text it
        wrote or read (a text-mode read's): the digests that bind the round's
        task file and verdicts to it are taken over this text, never over a
        later read of the file (:attr:`grouping_text`)."""
        self._grouping[:] = [text]

    @property
    def grouping_text(self) -> Optional[str]:
        """The ``grouped.json`` text this invocation last held, or ``None``."""
        return self._grouping[0] if self._grouping else None

    def checked_result(self, name: str, *, dispatched: bool = False) -> Optional[bytes]:
        """The bytes of the result file *name* that the latest dispatch bound to
        this claim persisted or found complete (:func:`record_checked_result`),
        or ``None`` when it did neither: the round reads these in place of the
        file, which a concurrent writer may have replaced since. With
        *dispatched*, only bytes that dispatch wrote itself count: a file it
        found complete on disk may be another round's
        (docs/development/review-results.md, "Consuming checked bytes")."""
        with _BOUND_LOCK:
            held = self._results.get(name)
        if held is None or (dispatched and not held[1]):
            return None
        return held[0]

    def batch_provenance(self) -> Optional[Dict[str, Dict[str, Any]]]:
        """The ``batch_provenance`` the latest dispatch bound to this claim
        recorded in its report, by ``task_id``, or ``None`` when it recorded
        none (:func:`record_batch_provenance`): the merge credits the held
        result bytes from these rows, never from the report file, which a
        concurrent writer may have replaced since."""
        with _BOUND_LOCK:
            if not self._provenance:
                return None
            return {
                task_id: dict(row)
                for rows in self._provenance.values()
                for task_id, row in rows.items()
            }

    def _remember(self, verdicts: Verdicts) -> Verdicts:
        self._verdicts[:] = [verdicts]
        return verdicts

    @property
    def verdicts(self) -> Optional[Verdicts]:
        """The ``validation.json`` this invocation last wrote or read, or ``None``."""
        return self._verdicts[0] if self._verdicts else None


def _taken_over(claim: Claim, recorded: Optional[str], doing: str) -> RoundTakenOver:
    if recorded is None:
        print(f"ERROR: this run {claim.describe()} in {claim.phase_dir}, and "
              ".status.json no longer records that round: nothing ties the phase "
              "dir to this run any more.")
    else:
        print(f"ERROR: this run {claim.describe()} in {claim.phase_dir}, and "
              f".status.json now records round {recorded}: another run took the "
              "phase over.")
    print(f"  This run stops without going on to {doing}, so nothing it writes "
          "from here can pass for the round on record.")
    print("  Follow the run that took over (`status`). If it stopped too, re-run "
          "with --force: it keeps each reusable model result ([SKIP]), regroups "
          "and validates again.")
    return RoundTakenOver(EXIT_NEEDS_HUMAN)


def _unreadable(claim: Claim, doing: str) -> RoundTakenOver:
    # Imported here to keep resume_state, which loads this module, light.
    from .unattended import fail_closed

    return RoundTakenOver(fail_closed(
        f"ERROR: this run {claim.describe()} in {claim.phase_dir}, and "
        f"{status_file.status_path(claim.phase_dir)} cannot be read. This run "
        f"stops without going on to {doing}: the checkpoint may record answers "
        f"this phase withholds, and nothing is written over it. "
        f"{status_file.unreadable_checkpoint_advice(claim.phase_dir)}"
    ))


def _unlocked(claim: Claim, doing: str) -> RoundTakenOver:
    print(f"ERROR: this run {claim.describe()} in {claim.phase_dir}, and could "
          f"not take {status_file.STATUS_LOCK_FILENAME} to check that the "
          "checkpoint still records it.")
    print(f"  This run stops without going on to {doing}: a round's ownership is "
          "never decided unlocked. Another process is holding the checkpoint "
          "mutex (a stopped `status` or worker); re-run once it is gone, with "
          "--force if this run left the round unfinished.")
    return RoundTakenOver(EXIT_NEEDS_HUMAN)


# ---------------------------------------------------------------------------
# Late results: bound to the round that dispatched them
# ---------------------------------------------------------------------------

#: The claims whose batch dispatches are running, by phase dir
#: (:func:`results_bound_to`); the last bound decides.
_BOUND: Dict[str, List[Claim]] = {}
_BOUND_LOCK = threading.Lock()


def _bound_key(phase_dir: PathLike) -> str:
    return os.path.normcase(os.path.realpath(str(phase_dir)))


@contextlib.contextmanager
def results_bound_to(claim: Claim) -> Iterator[None]:
    """While the block runs, a result file the executor persists into
    *claim*'s phase dir belongs to *claim*'s round
    (:func:`persisting_result`), and the bytes it persists or finds complete
    are remembered on *claim* (:func:`record_checked_result`), those of an
    earlier dispatch forgotten. Thread-safe; held on the dispatch's own
    thread, so it lasts exactly as long as the dispatch."""
    key = _bound_key(claim.phase_dir)
    with _BOUND_LOCK:
        claim._results.clear()
        claim._provenance.clear()
        _BOUND.setdefault(key, []).append(claim)
    try:
        yield
    finally:
        with _BOUND_LOCK:
            claims = _BOUND.get(key, [])
            for index in range(len(claims) - 1, -1, -1):
                if claims[index] is claim:
                    del claims[index]
                    break
            if not claims:
                _BOUND.pop(key, None)


def record_checked_result(
    phase_dir: PathLike, name: str, data: bytes, *, dispatched: bool,
) -> None:
    """Remember *data* on the claim a dispatch into *phase_dir* is bound to,
    as the result file *name*: the bytes the executor wrote there after its
    checks passed (``task_result.persist_result``, *dispatched*), or the
    bytes of a file it found already complete and so did not dispatch again
    (``task_result.task_is_complete``). The round's readers take them from
    the claim (:meth:`Claim.checked_result`), never from the file again, so a
    concurrent writer that replaces it afterwards reaches nothing
    (docs/development/review-results.md, "Consuming checked bytes"). A file
    found complete never displaces bytes the dispatch wrote itself. A phase
    dir no dispatch is bound to remembers nothing."""
    key = _bound_key(phase_dir)
    with _BOUND_LOCK:
        claims = _BOUND.get(key)
        if not claims:
            return
        results = claims[-1]._results
        held = results.get(name)
        if dispatched or held is None or not held[1]:
            results[name] = (bytes(data), dispatched)


def record_batch_provenance(
    phase_dir: PathLike, kind: str, provenance: Dict[str, Dict[str, Any]],
) -> None:
    """Remember the ``batch_provenance`` a dispatch into *phase_dir* recorded
    for its report of *kind*, on the claim it is bound to, beside the result
    bytes it holds (:func:`record_checked_result`): the runner credit belongs
    to those bytes, not to whatever report is on disk when the round merges
    (docs/development/review-results.md, "Consuming checked bytes"). A phase
    dir no dispatch is bound to remembers nothing."""
    key = _bound_key(phase_dir)
    with _BOUND_LOCK:
        claims = _BOUND.get(key)
        if not claims:
            return
        claims[-1]._provenance[str(kind)] = {
            str(task_id): dict(row) for task_id, row in provenance.items()
        }


def bound(claim: Claim, func: Callable[..., Any]) -> Callable[..., Any]:
    """*func* run under :func:`results_bound_to` (*claim*)."""
    def run(*args: Any, **kwargs: Any) -> Any:
        with results_bound_to(claim):
            return func(*args, **kwargs)

    return run


@contextlib.contextmanager
def persisting_result(phase_dir: PathLike, name: str) -> Iterator[bool]:
    """Around one result file the executor persists into *phase_dir*
    (``task_result.persist_result``): ``True`` to write it.

    A phase dir no dispatch is bound to writes as it always did. A bound one
    decides under the checkpoint mutex, held across the write: ``True`` only
    while the checkpoint still records the bound claim's round
    (:meth:`Claim.taken_over_by`). A result of a round another run has since
    replaced, or one whose round cannot be checked (the mutex could not be
    taken), is logged and dropped, never written.
    """
    key = _bound_key(phase_dir)
    with _BOUND_LOCK:
        claims = list(_BOUND.get(key, ()))
    if not claims:
        yield True
        return
    claim = claims[-1]
    with contextlib.ExitStack() as stack:
        try:
            stack.enter_context(status_file.checkpoint_lock(str(phase_dir), required=True))
        except status_file.CheckpointLockUnavailable:
            print(f"NOTE: {name} dropped, not written: this run {claim.describe()} "
                  f"and could not take {status_file.STATUS_LOCK_FILENAME} to check "
                  "that the checkpoint still records it.", file=sys.stderr)
            yield False
            return
        try:
            recorded = status_round(status_file.load_status(str(phase_dir)) or {})
            unreadable = False
        except status_file.CheckpointUnreadable:
            recorded, unreadable = None, True
        if claim.taken_over_by(recorded):
            shown = ("cannot be read" if unreadable
                     else f"records {'round ' + recorded if recorded else 'no round'}")
            print(f"NOTE: {name} dropped, not written: a late result, this run "
                  f"{claim.describe()}, and .status.json {shown} now.",
                  file=sys.stderr)
            yield False
            return
        yield True


def replace_file(path: PathLike, data: Union[bytes, str]) -> bytes:
    """Write *data* by ``atomic_io``'s atomic write, so a reader sees the old
    file or the new one, never part of one; the bytes written. Text is
    encoded as text mode writes it (UTF-8, the platform's newlines, as
    ``write_text`` did); bytes as they are."""
    if isinstance(data, bytes):
        atomic_write_bytes(path, data)
        return data
    return atomic_write_text(path, data, newline=os.linesep)


def task_document_round(document: Any) -> Optional[str]:
    """The round a task file document records, or ``None``."""
    return valid_round(document.get(ROUND_KEY)) if isinstance(document, dict) else None


def validation_document_round(document: Any) -> Optional[str]:
    """The round a ``validation.json`` document records (``metadata``), or ``None``.
    A bare list (an empty round, or a file from before the metadata) has none."""
    if not isinstance(document, dict):
        return None
    metadata = document.get("metadata")
    return valid_round(metadata.get(ROUND_KEY)) if isinstance(metadata, dict) else None


def _read_json(path: Path) -> Any:
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def task_file_round(path: PathLike) -> Optional[str]:
    """The round the task file at *path* records, or ``None``."""
    return task_document_round(_read_json(Path(path)))


def validation_file_round(path: PathLike) -> Optional[str]:
    """The round the ``validation.json`` at *path* records, or ``None``."""
    return validation_document_round(_read_json(Path(path)))


def report_file_round(path: PathLike) -> Optional[str]:
    """The round the ``report.md`` at *path* records (its second line), or ``None``."""
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            head = handle.readline() + handle.readline()
    except OSError:
        return None
    return report_markdown.report_round(head)


# ---------------------------------------------------------------------------
# The report's seal
# ---------------------------------------------------------------------------

def digest(data: Union[bytes, str]) -> str:
    """The 16-hex digest a report's round line records (SHA-256, cut)."""
    raw = data.encode("utf-8") if isinstance(data, str) else data
    return hashlib.sha256(raw).hexdigest()[:16]


def _file_bytes(path: Optional[PathLike]) -> Optional[bytes]:
    if path is None:
        return None
    try:
        return Path(path).read_bytes()
    except OSError:
        return None


def report_text(claim: Optional[Claim], text: str,
                verdicts: Optional[Verdicts] = None) -> str:
    """*text* (a report whose first line is ``ESCAPED_TEXT_MARKER``) with the
    claim's round line inserted as its second line.

    The line records the claim's round, the digest of *verdicts* (the exact
    ``validation.json`` bytes the report's verdicts came from, as the claim
    wrote or read them: :attr:`Claim.verdicts`; ``None`` for a report built
    without them), and the digest of the text below the line. Verdicts that do
    not record the claim's round get no line at all: the report never claims
    a round its verdicts did not come from. No claim, no round, or no marker:
    *text* unchanged.
    """
    if claim is None or not claim.round_id:
        return text
    head, sep, body = text.partition("\n")
    if not sep or head.rstrip() != report_markdown.ESCAPED_TEXT_MARKER:
        return text
    validation = None
    if verdicts is not None:
        if verdicts.round_id != claim.round_id:
            return text
        validation = verdicts.digest
    line = report_markdown.round_line(claim.round_id, validation=validation,
                                      body=digest(body))
    return f"{head}\n{line}\n{body}"


def publish_report(path: PathLike, text: str, *, claim: Optional[Claim] = None,
                   verdicts: Optional[Verdicts] = None) -> None:
    """Publish ``report.md``: :func:`report_text`, written by atomic replace,
    under the claim when there is one (a direct caller passes none)."""
    sealed = report_text(claim, text, verdicts)
    if claim is None:
        replace_file(path, sealed)
    else:
        claim.publish(path, sealed, "write report.md")


class ReportSeal(NamedTuple):
    """What a ``report.md``'s round line records, checked against the disk."""

    round_id: Optional[str]
    #: The report's text below the line still hashes to the recorded digest.
    whole: bool
    #: ``validation.json`` beside it hashes to the recorded digest.
    binds_validation: bool


def report_seal(phase_dir: PathLike) -> ReportSeal:
    """Read *phase_dir*'s ``report.md`` seal. A report cut short, edited, or
    rebuilt from other verdicts than the ``validation.json`` beside it is not
    ``whole`` or does not bind it; a report with no line has neither."""
    return sealed_verdicts(phase_dir)[0]


def sealed_verdicts(phase_dir: PathLike) -> Tuple[ReportSeal, Optional[bytes]]:
    """:func:`report_seal`, and the ``validation.json`` bytes it hashed
    (``None`` when it read none). A caller that acts on a seal binding its
    verdicts reads them from these bytes, never from the file again
    (docs/development/review-results.md, "Consuming checked bytes")."""
    directory = Path(phase_dir)
    try:
        with open(directory / REPORT_NAME, encoding="utf-8", errors="replace") as handle:
            content = handle.read()
    except OSError:
        return ReportSeal(None, False, False), None
    mark = report_markdown.report_round_mark(content)
    if mark is None:
        return ReportSeal(None, False, False), None
    body = content.lstrip("\ufeff").split("\n", 2)
    whole = mark.body is not None and len(body) == 3 and digest(body[2]) == mark.body
    validation = _file_bytes(directory / VALIDATION_NAME)
    binds = (mark.validation is not None and validation is not None
             and digest(validation) == mark.validation)
    return ReportSeal(mark.round_id, whole, binds), validation


def ownership(current: Optional[str], recorded: Optional[str]) -> str:
    """:data:`OWNED`, :data:`STALE` or :data:`LEGACY` (module docstring)."""
    if current is None or recorded is None:
        return LEGACY
    return OWNED if recorded == current else STALE


@dataclass(frozen=True)
class RoundFiles:
    """The task file, ``validation.json`` and ``report.md`` of a phase dir,
    each judged against the round its checkpoint records.

    ``recorded`` maps each file present to the id it records (``None``: none);
    ``owners`` maps it to :func:`ownership`. A file that is absent is in
    neither.
    """

    current: Optional[str]
    recorded: Dict[str, Optional[str]]
    owners: Dict[str, str]

    def owner(self, name: str) -> Optional[str]:
        """The ownership of file *name*, ``None`` when it is absent."""
        return self.owners.get(name)

    def stale(self, *names: str) -> Tuple[str, ...]:
        """Of *names* (default: the task file and ``validation.json``), those
        that record another round's id."""
        names = names or (TASKS_NAME, VALIDATION_NAME)
        return tuple(name for name in names if self.owners.get(name) == STALE)

    def describe(self, names: Tuple[str, ...]) -> str:
        """``validation.json records round 1a2b…`` for each of *names*."""
        def shown(value: Optional[str]) -> str:
            return f"round {value}" if value else "no round"

        return ", ".join(f"{name} records {shown(self.recorded.get(name))}" for name in names)


_READERS = {
    TASKS_NAME: task_file_round,
    VALIDATION_NAME: validation_file_round,
    REPORT_NAME: report_file_round,
}


def round_files(
    phase_dir: PathLike, status: Optional[Mapping[str, Any]] = None
) -> RoundFiles:
    """Judge *phase_dir*'s round-bearing files against its checkpoint.

    *status* is the ``.status.json`` document when the caller already read it.
    Read-only.
    """
    directory = Path(phase_dir)
    current = status_round(status if status is not None
                           else status_file.read_status(str(directory)))
    recorded: Dict[str, Optional[str]] = {}
    owners: Dict[str, str] = {}
    for name, reader in _READERS.items():
        path = directory / name
        if not path.is_file():
            continue
        recorded[name] = reader(path)
        owners[name] = ownership(current, recorded[name])
    return RoundFiles(current=current, recorded=recorded, owners=owners)


def tasks_file_is_this_rounds(rounds: RoundFiles, status: Mapping[str, Any]) -> bool:
    """Whether the phase dir's task file is the round on record's own.

    By its round id; or, for a task file with none, by the checkpoint reading
    :data:`VALIDATION_PENDING`, the proof there was before round ids. A task
    file that is absent is no round's.
    """
    owner = rounds.owner(TASKS_NAME)
    if owner == OWNED:
        return True
    return owner == LEGACY and isinstance(status, Mapping) and (
        status.get("state") == VALIDATION_PENDING
    )


def evidence(rounds: RoundFiles, names: Tuple[str, ...], status: Mapping[str, Any]) -> str:
    """Why *names* are not proven the round on record's, as one clause: the
    checkpoint's round, each file's, and for a task file with no id the
    checkpoint word that would have tied it."""
    checkpoint = (f".status.json records round {rounds.current}" if rounds.current
                  else ".status.json records no round")
    files = rounds.describe(tuple(names))
    text = f"{checkpoint}, {files}" if files else checkpoint
    if TASKS_NAME in names and rounds.owner(TASKS_NAME) == LEGACY:
        state = status.get("state") if isinstance(status, Mapping) else None
        reads = f"reads `{state}`" if isinstance(state, str) and state else "records no state"
        text += (f"; a task file without a round id is this run's only beside a "
                 f"checkpoint reading `{VALIDATION_PENDING}`, and this one {reads}")
    return text


# ---------------------------------------------------------------------------
# --reaggregate: the round on record's own files only
# ---------------------------------------------------------------------------

def foreign_files(claim: Claim) -> Tuple[RoundFiles, Tuple[str, ...]]:
    """The phase dir's files judged against *claim*'s round, and which of the
    task file and ``validation.json`` record another round's id."""
    status = {ROUND_KEY: claim.round_id} if claim.round_id else {}
    rounds = round_files(claim.phase_dir, status)
    return rounds, rounds.stale()


def refuse_foreign_round(claim: Claim, retry_command: str) -> None:
    """The ownership check every ``--reaggregate`` runs before it reuses or
    merges validation (review-plan, review-tasks and review-code alike).

    A task file or ``validation.json`` that records another round than the
    claim's is a file a re-run stopped before replacing: merging or reusing it
    would finish this round on another round's verdicts, under a report that
    claims this one. Refused at exit 3 naming *retry_command* (the ``--force``
    re-run). Files with no id on either side are left to the reaggregate's
    content checks, as before round ids (docs/development/review-results.md,
    "Round identity").
    """

    rounds, stale = foreign_files(claim)
    if not stale:
        return
    print(f"ERROR: --reaggregate refused: {', '.join(stale)} in {claim.phase_dir} "
          f"belong to another review round ({evidence(rounds, stale, {})}).")
    print(f"  A run that started round {claim.round_id} stopped before replacing "
          "them, so reaggregating would finish that round on another round's "
          "verdicts. Nothing was changed.")
    print("  If that run is still going, let it finish (`status`). Otherwise resume "
          "the round with --force: it keeps each reusable model result ([SKIP]), "
          "regroups and validates again:")
    print(f"  {retry_command}")
    raise SystemExit(EXIT_NEEDS_HUMAN)
