"""``--cascade``: one review-then-apply round per model, one model after another.

A modifier of ``--improve-plan`` and ``--improve-code``. Each model of the
review's resolved list, in its order, gets a stage of its own: today's
composite run (review, validate, apply) with a derived namespace
(:func:`derive_stage_args`), so every rule the composites already follow
(``improve_workflow.skip_reason``, ``step_flags``, ``plan_steps``) decides what
a stage runs. A stage reviews the work as the stages before it left it.

Where a cascade lives. The composite's run dir holds a pointer,
``cascade-current.json`` (:data:`POINTER_NAME`), naming the current cascade's
directory ``cascades/<YYYYmmddTHHMMSS>-<id8>/``, which holds ``record.json``
(:data:`RECORD_NAME`), ``start.md`` (improve-plan: the plan at the start),
``files.txt`` (improve-code: the frozen ``--files`` list, when one was typed),
and the views and stage dirs ``utils/cascade_archive.py`` and
``utils/cascade_ledger.py`` write. Both JSON files are checked on every read
against ``schemas/cascade_record.schema.json``; a file that fails is exit 3
naming it (:class:`CascadeRecordError`), as an unreadable ``state.json`` is.
A new cascade never renames or reuses a path: its directory and record are
written first, an unfinished predecessor is marked ``abandoned``, and only then
is the pointer replaced, so a crash leaves at worst an orphan directory nobody
reads.

Who reads and who writes. :func:`peek` and :func:`applies` are read-only: the
callers ask them before a detach boundary and in the read-only native planner,
so a refused or finished launch leaves nothing behind. :func:`advance` is the
only writer: it creates, continues or abandons a cascade, binds the review
round on record to the current stage through the round's provenance block
(``utils/cascade_provenance.py``), closes out a finished stage
(``cascade_archive.close_out``) and freezes the next stage's inputs
(``cascade_ledger.freeze_inputs``), then hands back the stage to run
(:class:`StagePlan`), :class:`Complete`, or :class:`NotACascade`. It does all
of that holding the composite run dir's phase lock (:func:`_planning`), so
two planners started together never both read "no cascade" and hand out two
cascades' first stages.

The contract, its tables and its history: docs/development/workflows.md,
"A cascade (``--cascade``)".
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import json
import os
import secrets
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union

from . import cascade_provenance as provenance
from . import detach, process_control
from . import improve_workflow as iw
from . import scope_policy, status_file
from .cli_common import EXIT_ERROR, EXIT_NEEDS_HUMAN
from .held_folder import remove_in_plan_dir, write_in_plan_dir
from .output_handler import get_phase_dir, phase_dir_path
from .schema_validator import load_schema, validate_document
from .text_clip import clip, plain_line
from .unattended import NeedsHuman, fail_closed

#: Version of the pointer and the record.
SCHEMA_VERSION = 1
SCHEMA_NAME = "cascade_record.schema.json"

#: The pointer's and the record's names, shared with the review's handoff
#: check (``cascade_provenance.check_current``).
POINTER_NAME = provenance.POINTER_NAME
CASCADES_DIR = "cascades"
RECORD_NAME = provenance.RECORD_NAME
START_NAME = "start.md"
FILES_NAME = "files.txt"
SUMMARY_NAME = "summary.md"

#: A cascade's ``state``.
RUNNING = "running"
FINISHED = "finished"
ABANDONED = "abandoned"

#: A stage's ``state``. ``running`` from the moment its inputs are frozen and
#: it is handed out; ``done`` once closed out; ``skipped`` for a middle stage
#: whose review produced no result.
PENDING = "pending"
STAGE_RUNNING = "running"
DONE = "done"
SKIPPED = "skipped"
_CLOSED = (DONE, SKIPPED)

#: Where the cascade stands: a new cascade, the stage it continues, the stage to run.
CASCADE_MARKER = "[IMPROVE_CASCADE]"
#: A typed flag that is not the unfinished cascade's, a continue call for another
#: cascade, or --cascade --resume with nothing to resume.
CONFLICT_MARKER = "[CASCADE_CONFLICT]"
#: A stage before the last whose review produced no result, recorded skipped.
SKIPPED_MARKER = "[CASCADE_STAGE_SKIPPED]"
ALREADY_COMPLETE_MARKER = "[ALREADY_COMPLETE]"
ONE_MODEL_NOTE = "NOTE: --cascade with one model is a single round"

#: How many times :func:`advance` plans a stage's close-out again after the
#: archive's re-read under the locks no longer showed the stage done.
CLOSE_OUT_ATTEMPTS = 3

#: The D6 row a middle stage's zero-result skip is recorded under (row 3:
#: a review with no result).
_ZERO_RESULT_SITE = "partial-results-recovery"


# ---------------------------------------------------------------------------
# Refusals
# ---------------------------------------------------------------------------

class CascadeRefusal(Exception):
    """The cascade cannot go on: print :attr:`message` whole on stderr, exit :attr:`code`.

    *code* is 3 (``[CASCADE_CONFLICT]``, a stopped last stage, a stage a
    continue call found not finished, a record or review checkpoint that
    cannot be read, an archive refusal) or 1 (``--files-from -``, a scope that
    cannot be read). :func:`refusal_exit` prints it the way each code is
    printed elsewhere.
    """

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = int(code)
        self.message = message


class CascadeRecordError(CascadeRefusal):
    """A pointer or record that is missing, not JSON, or not the schema's shape; exit 3.

    Planning from a damaged record would either start a new paid cascade or
    continue at the wrong stage, so the file is refused, named, and left as
    it is, like ``improve_workflow.StateReadError``.
    """

    def __init__(self, mode: str, path: Union[str, Path], detail: str, pointer: Path):
        self.path = str(path)
        self.detail = detail
        super().__init__(EXIT_NEEDS_HUMAN, (
            f"ERROR: {mode}: cannot read {iw._display_path(path)} ({detail}); nothing "
            f"was run. Repair the file, or move {iw._display_path(pointer)} aside to "
            "leave the cascade, then run the command again."
        ))


class LastStageStopped(CascadeRefusal):
    """The last stage's review produced no result, met on a continue call; exit 3.

    A :class:`CascadeRefusal` of its own kind so a caller can tell the stop a
    re-run recovers from (the user's command starts the stage over) from a
    ``[CASCADE_CONFLICT]`` or a record it cannot read: ``util improve-cascade
    next`` prints the user's continuation beside this one, and nothing beside
    the others. *cascade_id*, *stage* (the last), *of* and *model* name it.
    """

    def __init__(self, message: str, *, cascade_id: str, stage: int, of: int, model: str):
        super().__init__(EXIT_NEEDS_HUMAN, message)
        self.cascade_id = cascade_id
        self.stage = stage
        self.of = of
        self.model = model


class StageNotFinished(CascadeRefusal):
    """A continue call made after stage *k* found stage *k* still open; exit 3.

    The call names the stage it follows (``after_stage``). When, after the
    round on record is bound, a done stage closed out and a zero-result
    middle stage skipped, the current stage is still that one, its steps
    stopped before the stage was done (a review that failed for another
    reason than no result, a validation decision owed, a live lock, a step
    that never ran). Handing the same stage out again would let a host that
    follows the printed block run the paid review again, and again, so the
    call stops instead, and, like :class:`LastStageStopped`, ``util
    improve-cascade next`` prints the user's continuation beside it.
    *cascade_id*, *stage*, *of* and *model* name the stage.
    """

    def __init__(self, message: str, *, cascade_id: str, stage: int, of: int, model: str):
        super().__init__(EXIT_NEEDS_HUMAN, message)
        self.cascade_id = cascade_id
        self.stage = stage
        self.of = of
        self.model = model


def refusal_exit(exc: CascadeRefusal) -> int:
    """Print *exc* and return its exit code: exit 3 marks the result line needs-human."""
    if exc.code == EXIT_NEEDS_HUMAN:
        return fail_closed(exc.message)
    print(exc.message, file=sys.stderr)
    return exc.code


# ---------------------------------------------------------------------------
# What the callers get back
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Peek:
    """:func:`peek`'s read-only answer.

    *kind* is ``none`` (no cascade run: today's rules decide, the
    ``[ALREADY_COMPLETE]`` check included), ``work`` (a cascade with a stage
    to run or a close-out owed) or ``complete`` (re-running a finished
    cascade's command). *lines* holds the ``[ALREADY_COMPLETE]`` line for
    ``complete``; otherwise the notices :func:`advance` would print first,
    for a read-only caller that never calls it.
    """

    kind: str
    lines: Tuple[str, ...]


@dataclass
class StagePlan:
    """The stage to run now.

    *stage_args* is :func:`derive_stage_args`: the namespace the composite's
    pure functions plan the stage from, ``cascade_stage_file`` (the stage's
    absolute manifest path) and ``force`` (a fresh round) included.
    *notices* are the lines to print before the stage, in order.
    """

    cascade_id: str
    cascade_dir: Path
    stage: int
    of: int
    model: str
    stage_args: argparse.Namespace
    notices: Tuple[str, ...]
    summary_path: Path


@dataclass
class Complete:
    """Every stage is closed: the per-round table is at *summary_path*."""

    cascade_id: str
    cascade_dir: Path
    of: int
    summary_path: Path
    notices: Tuple[str, ...]


@dataclass
class NotACascade:
    """No cascade runs: the caller runs today's composite with the user's flags.

    *notices* says why when that is news, e.g. that ``--force`` without
    ``--cascade`` abandoned an unfinished cascade.
    """

    notices: Tuple[str, ...]


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _plan(plan_path: Union[str, Path]) -> Path:
    """The plan as ``improve_workflow.read_records`` resolves it."""
    return Path(os.path.abspath(str(plan_path))).resolve()


def composite_dir(plan_path: Union[str, Path], mode: str) -> Path:
    """The composite's run dir (``improve-plan/`` or ``improve-code/``); computed, never created."""
    return phase_dir_path(_plan(plan_path), iw._row(mode).phase)


def pointer_path(plan_path: Union[str, Path], mode: str) -> Path:
    return composite_dir(plan_path, mode) / POINTER_NAME


def review_dir(plan_path: Union[str, Path], mode: str) -> Path:
    """The live review phase dir whose ``.status.json`` carries the round's provenance."""
    return phase_dir_path(_plan(plan_path), iw._row(mode).sequence_phases[0])


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# The pointer and the record: read, checked, written
# ---------------------------------------------------------------------------

@dataclass
class _Current:
    """The pointer's cascade: its directory and its record (a mutable dict)."""

    mode: str
    pointer: Path
    cascade_dir: Path
    record: Dict[str, Any]

    @property
    def cascade_id(self) -> str:
        return self.record["cascade_id"]

    @property
    def state(self) -> str:
        return self.record["state"]

    @property
    def stages(self) -> List[Dict[str, Any]]:
        return self.record["stages"]

    @property
    def of(self) -> int:
        return len(self.stages)

    @property
    def models(self) -> List[str]:
        return [stage["model"] for stage in self.stages]

    @property
    def record_path(self) -> Path:
        return self.cascade_dir / RECORD_NAME

    @property
    def summary_path(self) -> Path:
        return self.cascade_dir / SUMMARY_NAME


def _schema_problems(document: Any, definition: str) -> List[str]:
    """What is wrong with *document* as the schema's *definition*; empty when nothing."""
    schema = load_schema(SCHEMA_NAME)
    return validate_document(document, schema["definitions"][definition], root=schema)


def _read_json(mode: str, path: Path, pointer: Path) -> Any:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        raise CascadeRecordError(mode, path, "it does not exist", pointer) from None
    except OSError as exc:
        raise CascadeRecordError(mode, path, str(exc), pointer) from None
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise CascadeRecordError(mode, path, str(exc), pointer) from None


def _checked(mode: str, path: Path, pointer: Path, definition: str) -> Dict[str, Any]:
    document = _read_json(mode, path, pointer)
    problems = _schema_problems(document, definition)
    if problems:
        shown = "; ".join(problems[:3]) + (" …" if len(problems) > 3 else "")
        raise CascadeRecordError(mode, path, shown, pointer)
    return document


def _record_problem(mode: str, pointer_doc: Dict[str, Any], record: Dict[str, Any]) -> Optional[str]:
    """What the schema cannot say: the record belongs to this pointer and composite."""
    if record["cascade_id"] != pointer_doc["cascade_id"]:
        return "its cascade_id is not the one the pointer names"
    if not pointer_doc["dir"].endswith("-" + record["cascade_id"][:8]):
        return "its directory name does not end in its cascade_id's first 8 characters"
    if record["mode"] != iw._row(mode).name:
        return f"it is a {record['mode']} cascade, not {iw._row(mode).name}'s"
    for position, stage in enumerate(record["stages"], start=1):
        if stage["index"] != position:
            return f"stage {position} has index {stage['index']}"
    return None


def load_current(plan_path: Union[str, Path], mode: str) -> Optional[_Current]:
    """The pointer's cascade, checked; ``None`` when there is no pointer. Read-only.

    Raises :class:`CascadeRecordError` for a pointer or record that cannot be
    read or fails the schema.
    """
    pointer = pointer_path(plan_path, mode)
    if not os.path.lexists(pointer):
        return None
    pointer_doc = _checked(mode, pointer, pointer, "pointer")
    directory = pointer.parent / pointer_doc["dir"]
    record = _checked(mode, directory / RECORD_NAME, pointer, "record")
    problem = _record_problem(mode, pointer_doc, record)
    if problem:
        raise CascadeRecordError(mode, directory / RECORD_NAME, problem, pointer)
    return _Current(mode=iw._row(mode).name, pointer=pointer, cascade_dir=directory,
                    record=record)


def _write_json(path: Path, document: Dict[str, Any], definition: str) -> None:
    """Write *document* atomically, inside the plan's output dir, after checking it.

    A document this module built that fails its own schema is a bug here, not
    a user's file, so it raises before anything reaches disk.
    """
    problems = _schema_problems(document, definition)
    if problems:  # pragma: no cover - a bug in this module
        raise ValueError(f"refusing to write a {definition} that fails its schema: {problems}")
    write_in_plan_dir(path, (json.dumps(document, indent=2) + "\n").encode("utf-8"),
                      make=True)


def _save(current: _Current) -> None:
    _write_json(current.record_path, current.record, "record")


# ---------------------------------------------------------------------------
# The stage list and the frozen selectors
# ---------------------------------------------------------------------------

def _review_phase(mode: str) -> str:
    return iw._row(mode).sequence_phases[0]


def _model_flag_typed(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "models", None)) or bool(getattr(args, "quick", False))


def _defaults_source(phase: str, plan: Path) -> str:
    """Which config key the default list came from, as the auto-resolution names it."""
    # Imported here: only an untyped stage list reads the configuration.
    from . import provider_registry

    try:
        modes = (provider_registry.load_config(anchor=str(plan)).get("defaults") or {}).get("modes")
    except Exception:  # noqa: BLE001 - a label never fails a run
        modes = None
    if isinstance(modes, dict) and phase in modes:
        return f"defaults.modes.{phase}"
    return "defaults.models"


def resolve_stage_models(
    plan_path: Union[str, Path], mode: str, args: argparse.Namespace
) -> Tuple[List[str], Optional[str]]:
    """``(models, source)``: the stages, and where they came from when no model flag was typed.

    The review's own resolution, unattended and anchored at the plan
    (``interactive.resolve_models``, as the review lanes call it with the
    review's phase word): ``--models`` as typed, else the ``--quick`` list,
    else the review's configured defaults, canonical, order kept, duplicates
    collapsed. Nothing reorders it: weakest-first is the user's order.
    *source* is ``None`` when ``--models`` or ``--quick`` was typed. Raises
    :class:`CascadeRefusal` (exit 3) when nothing resolves.
    """
    # Imported here: model resolution loads the provider registry, which a
    # continuation that types no model flag never needs.
    from . import interactive

    plan = _plan(plan_path)
    phase = _review_phase(mode)
    try:
        models = interactive.resolve_models(
            cli_models=getattr(args, "models", None), interactive=False,
            quick=bool(getattr(args, "quick", False)), mode=phase, anchor=str(plan),
            unattended=True,
        )
    except NeedsHuman as exc:
        raise CascadeRefusal(EXIT_NEEDS_HUMAN, exc.message) from None
    except RuntimeError as exc:
        raise CascadeRefusal(EXIT_ERROR, f"ERROR: {exc}") from None
    if not models:  # pragma: no cover - resolve_models raises first
        raise CascadeRefusal(EXIT_NEEDS_HUMAN, "ERROR: --cascade resolved no models.")
    source = None if _model_flag_typed(args) else _defaults_source(phase, plan)
    return list(models), source


def typed_files(
    plan_path: Union[str, Path], mode: str, args: argparse.Namespace
) -> Optional[Tuple[str, ...]]:
    """The typed ``--files``/``--files-from <file>`` list, repository-relative; ``None`` untyped.

    Read through review-code's own reader (``improve_workflow._requested_scope``),
    so the frozen list is the one the review would record. ``--files-from -``
    is refused (exit 1): a stage's review runs long after the shell's stdin is
    gone, and a continuation could not reproduce it.
    """
    if not iw._reviews_code(mode):
        return None
    if getattr(args, "files_from", None) == "-":
        raise CascadeRefusal(EXIT_ERROR, iw.files_from_stdin_refusal())
    try:
        return iw._requested_scope(mode, _plan(plan_path), args)
    except ValueError as exc:
        if not iw.is_scope_files_error(exc):
            raise
        raise CascadeRefusal(EXIT_ERROR, iw.scope_error_line(exc)) from None


def typed_base_ref(mode: str, args: argparse.Namespace) -> Optional[str]:
    """The typed ``--base-ref`` (improve-code), frozen into the record at the start."""
    if not iw._reviews_code(mode):
        return None
    return getattr(args, "base_ref", None) or None


def _typed_policy(args: argparse.Namespace) -> Optional[str]:
    return scope_policy.normalize_policy(getattr(args, "scope_policy", None))


def recorded_files(current: _Current) -> Optional[Tuple[str, ...]]:
    """The frozen ``files.txt`` list, or ``None`` when no scope flag was typed at the start."""
    if current.record["selectors"]["files_file"] is None:
        return None
    path = current.cascade_dir / FILES_NAME
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CascadeRecordError(current.mode, path, str(exc), current.pointer) from None
    return tuple(line for line in text.splitlines() if line.strip())


@dataclass(frozen=True)
class _Request:
    """What this invocation asks a new cascade for, resolved once."""

    models: Tuple[str, ...]
    source: Optional[str]
    files: Optional[Tuple[str, ...]]
    base_ref: Optional[str]


def _request(plan_path: Union[str, Path], mode: str, args: argparse.Namespace) -> _Request:
    files = typed_files(plan_path, mode, args)
    models, source = resolve_stage_models(plan_path, mode, args)
    return _Request(models=tuple(models), source=source, files=files,
                    base_ref=typed_base_ref(mode, args))


# ---------------------------------------------------------------------------
# The stage namespace
# ---------------------------------------------------------------------------

def derive_stage_args(
    args: argparse.Namespace,
    mode: str,
    current: _Current,
    index: int,
    *,
    force: bool,
    manifest: Optional[Path],
) -> argparse.Namespace:
    """The namespace stage *index* runs on: the user's, with every planning input set here.

    ``improve_workflow``'s pure functions read ``models``, ``quick``,
    ``force``, ``resume``, ``scope_policy``, ``files``, ``files_from`` and
    ``base_ref``; each is set explicitly so nothing leaks from the
    invocation's own ``--force``, ``--resume`` or selectors. The apply's
    ``--resume`` stays ``Records.apply_in_progress``'s inference, which tells a
    new review cycle from an apply in progress. The scope policy is the one
    typed now, else the one the stage started under (a typed one for a round
    already under way meets that round's own conflict rule). *manifest* is the
    stage's frozen inputs manifest, absolute (the dispatcher moves the cwd),
    which ``step_flags`` hands the review as ``--cascade-stage-file``.
    """
    stage = current.stages[index - 1]
    selectors = current.record["selectors"]
    stage_args = copy.copy(args)
    stage_args.models = [stage["model"]]
    stage_args.quick = False
    stage_args.force = bool(force)
    stage_args.resume = False
    stage_args.scope_policy = _typed_policy(args) or stage["scope_policy"]
    stage_args.files = None
    stage_args.files_from = (
        str(current.cascade_dir / FILES_NAME)
        if iw._reviews_code(mode) and selectors["files_file"] else None
    )
    stage_args.base_ref = selectors["base_ref"] if iw._reviews_code(mode) else None
    stage_args.cascade_stage_file = str(manifest) if manifest is not None else None
    stage_args.cascade = True
    return stage_args


# ---------------------------------------------------------------------------
# The review round on record, and the stage it belongs to
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _ReviewView:
    """The live review dir's checkpoint, as binding reads it."""

    block: Optional[Dict[str, Any]]
    round_id: Optional[str]
    completed: Optional[List[Any]]
    failed: Dict[str, str]

    def belongs_to(self, cascade_id: str, index: int) -> bool:
        return bool(self.block) and self.block.get("cascade_id") == cascade_id and (
            self.block.get("stage") == index)

    @property
    def zero_result(self) -> bool:
        """The round's fan-out finished and no model produced a result.

        The review records ``models_completed: []`` beside ``models_failed``
        only on that ending; a live or interrupted fan-out has no
        ``models_completed`` key at all (the opening write drops it).
        """
        return self.completed is not None and not self.completed and bool(self.failed)

    def failure(self, model: str) -> str:
        reason = self.failed.get(model) or next(iter(self.failed.values()), "")
        return plain_line(reason) or "no model produced a result"


def _unreadable_review(mode: str, directory: str, exc: BaseException) -> CascadeRefusal:
    """Exit 3 for a review checkpoint that exists and cannot be read.

    Read as "no block", a bound stage would take the foreign-round path and
    start over, discarding a review that completed; so it stops, naming the
    file, with the advice every stop over that checkpoint gives.
    """
    cause = exc.__cause__ or exc
    path = status_file.status_path(directory)
    return CascadeRefusal(EXIT_NEEDS_HUMAN, (
        f"ERROR: {iw._row(mode).name}: cannot read {iw._display_path(path)} "
        f"({cause}), so the cascade cannot tell which stage the review round on record "
        "belongs to; nothing was run. "
        + status_file.unreadable_checkpoint_advice(directory, phase=_review_phase(mode))
    ))


def _review_view(plan_path: Union[str, Path], mode: str) -> _ReviewView:
    # Imported here: the round id reader is review code that the read-only
    # callers which never reach binding do not load.
    from .review_round import status_round

    directory = str(review_dir(plan_path, mode))
    try:
        status = status_file.load_status(
            directory, attempts=status_file.CHECKPOINT_READ_ATTEMPTS) or {}
    except status_file.CheckpointUnreadable as exc:
        raise _unreadable_review(mode, directory, exc) from None
    block = status.get(provenance.STATUS_KEY)
    try:
        block = (None if block is None
                 else provenance.check_block(block, status_file.status_path(directory)))
    except provenance.CascadeProvenanceError as exc:
        raise CascadeRefusal(EXIT_NEEDS_HUMAN, provenance.error_line(exc)) from None
    completed = status.get("models_completed")
    failed = status.get("models_failed")
    if isinstance(failed, list):
        failed = {str(item): "" for item in failed}
    return _ReviewView(
        block=block,
        round_id=status_round(status),
        completed=completed if isinstance(completed, list) else None,
        failed={str(k): str(v) for k, v in failed.items()} if isinstance(failed, dict) else {},
    )


def _stage_done(plan_path: Union[str, Path], mode: str, stage_args: argparse.Namespace) -> bool:
    """The stage's apply is recorded completed or skipped after its review.

    ``skip_reason`` of the apply on the stage namespace (no ``--force``) and
    a fresh read of the records: ``completed``/``skipped`` only when the
    review is completed and the apply's newer record is not older than it.
    """
    try:
        records = iw.read_records(mode, _plan(plan_path), stage_args)
    except iw.StateReadError as exc:
        raise CascadeRefusal(EXIT_NEEDS_HUMAN, iw.state_read_error_line(mode, exc)) from None
    apply = iw._row(mode).sequence[1]
    return iw.skip_reason(mode, apply, stage_args, records) in ("completed", "skipped")


def _current_index(current: _Current) -> Optional[int]:
    """The first stage not closed, 1-based; ``None`` when every stage is."""
    for stage in current.stages:
        if stage["state"] not in _CLOSED:
            return stage["index"]
    return None


# ---------------------------------------------------------------------------
# The decision at the start of an invocation (the resume / re-run table)
# ---------------------------------------------------------------------------

def _plural(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def already_complete_line(current: _Current) -> str:
    """``[ALREADY_COMPLETE]`` for a finished cascade's command typed again."""
    return (
        f"{ALREADY_COMPLETE_MARKER} cascade finished at "
        f"{current.record['finished_at'] or '(no date)'} ({_plural(current.of, 'stage')}); "
        "--force --cascade starts a new one"
    )


def _where(current: _Current) -> str:
    index = _current_index(current) or current.of
    return f"{current.cascade_id[:8]} (stage {index} of {current.of})"


def continuing_line(current: _Current) -> str:
    index = _current_index(current) or current.of
    return (f"{CASCADE_MARKER} continuing stage {index} of {current.of} "
            f"({current.stages[index - 1]['model']})")


def _describe_files(files: Optional[Sequence[str]]) -> str:
    if files is None:
        return "no --files (review-code's default scope)"
    shown = ", ".join(files)
    return f"{_plural(len(files), 'file')}: {clip(shown, 160)}"


def _conflict(current: _Current, flag: str, recorded: str, typed: str) -> CascadeRefusal:
    return CascadeRefusal(EXIT_NEEDS_HUMAN, (
        f"{CONFLICT_MARKER} {flag}: the unfinished cascade {_where(current)} was "
        f"started with {recorded}; this run asks for {typed}. Re-run without {flag} "
        "to continue the cascade, or with --force --cascade to start a new one."
    ))


def _nothing_to_resume(
    plan_path: Union[str, Path], mode: str, current: Optional[_Current]
) -> CascadeRefusal:
    """Exit 3 for ``--cascade --resume`` with no model flag and no unfinished cascade on record.

    The command asks to go on with a cascade, and there is none to go on
    with (no pointer, or one naming an abandoned cascade), so starting one
    would resolve today's default list behind the user's back; read-only,
    raised by :func:`_decide`, so :func:`peek` refuses it before anything
    is written or detached.
    """
    pointer = iw._display_path(pointer_path(plan_path, mode))
    found = (f"{pointer} does not exist" if current is None else
             f"{pointer} names cascade {current.cascade_id[:8]}, which was abandoned")
    return CascadeRefusal(EXIT_NEEDS_HUMAN, (
        f"{CONFLICT_MARKER} --resume: there is no unfinished {iw._row(mode).name} cascade "
        f"to resume ({found}); nothing was run. --cascade without --resume, or with "
        "--models or --quick, starts one."
    ))


def _typed_difference(
    plan_path: Union[str, Path], mode: str, args: argparse.Namespace, current: _Current
) -> Optional[Tuple[str, str, str]]:
    """The first typed model list or selector that is not *current*'s, or ``None``.

    ``(flag, recorded, typed)``, each value described for a message. Only
    what was typed is compared, so a command that types none (the bare
    continuation every surface prints: ``--cascade --resume``) is the
    record's own request. Models compare in order (the order is the
    cascade); files as a set, as the review compares a scope.
    ``--scope-policy`` is never compared.
    """
    if _model_flag_typed(args):
        models, _source = resolve_stage_models(plan_path, mode, args)
        if models != current.models:
            flag = "--models" if getattr(args, "models", None) else "--quick"
            return flag, ", ".join(current.models), ", ".join(models)
    if not iw._reviews_code(mode):
        return None
    if iw.scope_flags_typed(args):
        files = typed_files(plan_path, mode, args)
        recorded = recorded_files(current)
        if recorded is None or set(recorded) != set(files or ()):
            flag = "--files" if getattr(args, "files", None) else "--files-from"
            return flag, _describe_files(recorded), _describe_files(files)
    typed_ref = typed_base_ref(mode, args)
    recorded_ref = current.record["selectors"]["base_ref"]
    if typed_ref is not None and typed_ref != recorded_ref:
        return ("--base-ref", f"--base-ref {recorded_ref}" if recorded_ref else "no --base-ref",
                f"--base-ref {typed_ref}")
    return None


def check_conflicts(
    plan_path: Union[str, Path], mode: str, args: argparse.Namespace, current: _Current
) -> None:
    """Refuse a typed model list or selector that is not the unfinished cascade's (exit 3).

    :func:`_typed_difference`: only what was typed is compared, so a bare
    continuation reproduces the record. ``--scope-policy`` is never a
    conflict: it becomes the policy of the stages not started yet.
    """
    difference = _typed_difference(plan_path, mode, args, current)
    if difference is not None:
        raise _conflict(current, *difference)


def _scope_policy_note(current: _Current, args: argparse.Namespace) -> Optional[str]:
    typed = _typed_policy(args)
    if typed is None or typed == current.record["scope_policy"]:
        return None
    index = _current_index(current) or current.of
    started = current.stages[index - 1]["state"] != PENDING
    later = index + 1 if started else index
    if later > current.of:
        return (f"NOTE: {scope_policy.FLAG} {typed} reaches no later stage: stage "
                f"{index} is the last and already under way, so its round's own rules decide.")
    return (f"NOTE: {scope_policy.FLAG} {typed} is now the cascade's policy for stages "
            f"{later}..{current.of}" + (f"; stage {index}'s round follows its own rules."
                                         if started else "."))


@dataclass(frozen=True)
class _Decision:
    """What the start of an invocation does with the pointer's cascade.

    *kind*: ``none`` (no cascade run; *abandon* when ``--force`` without
    ``--cascade`` leaves an unfinished one), ``new`` (start one; *abandon*
    the unfinished predecessor first), ``continue`` or ``finished``.
    """

    kind: str
    current: Optional[_Current]
    abandon: bool
    notices: Tuple[str, ...]
    request: Optional[_Request] = None


def _decide(plan_path: Union[str, Path], mode: str, args: argparse.Namespace) -> _Decision:
    """The resume / re-run / ``--force`` table, read-only; refusals raise :class:`CascadeRefusal`.

    * ``--force --cascade``: a new cascade; an unfinished one is abandoned.
    * ``--force`` alone over an unfinished cascade: today's new round with
      today's models, and the cascade abandoned (not a cascade run).
    * an unfinished cascade, with or without ``--cascade``/``--resume``:
      continue it, after :func:`check_conflicts`.
    * ``--cascade`` over a finished cascade: ``[ALREADY_COMPLETE]`` unless a
      typed model list or selector is not the record's
      (:func:`_typed_difference`), which starts a new cascade. An untyped
      one is the record's: the continuation every surface prints while the
      cascade runs (``--cascade --resume``) types none, and run again after
      the finish it must not resolve today's default list and start a new
      paid cascade.
    * ``--cascade`` with no cascade on record (an abandoned one counts as
      none): a new cascade, unless ``--resume`` was typed with no model flag
      (:func:`_nothing_to_resume`). That is the printed continuation, kept
      from a cascade that ``--force`` alone abandoned since, or whose pointer
      was moved aside; it asks to go on, so it never resolves today's default
      list and starts a new paid cascade.
    * anything else: not a cascade run.
    """
    if not iw.takes_cascade(mode):
        return _Decision("none", None, False, ())
    current = load_current(plan_path, mode)
    typed = bool(getattr(args, "cascade", False))
    force = bool(getattr(args, "force", False))
    unfinished = current is not None and current.state == RUNNING
    if force and typed:
        notices: Tuple[str, ...] = ()
        if unfinished:
            notices = (f"NOTE: --force --cascade abandons the unfinished cascade "
                       f"{_where(current)} and starts a new one.",)
        return _Decision("new", current, unfinished, notices, _request(plan_path, mode, args))
    if unfinished and force:
        return _Decision("none", current, True, (
            f"NOTE: --force without --cascade abandons the unfinished cascade "
            f"{_where(current)}: this run starts a new round with today's models. "
            "Pass --force --cascade to start a new cascade instead.",))
    if unfinished:
        check_conflicts(plan_path, mode, args, current)
        note = _scope_policy_note(current, args)
        return _Decision("continue", current, False,
                         (continuing_line(current),) + ((note,) if note else ()))
    if not typed:
        return _Decision("none", current, False, ())
    if (current is None or current.state == ABANDONED) and (
            getattr(args, "resume", False) and not _model_flag_typed(args)):
        raise _nothing_to_resume(plan_path, mode, current)
    if current is not None and current.state == FINISHED and (
            _typed_difference(plan_path, mode, args, current) is None):
        return _Decision("finished", current, False, (already_complete_line(current),))
    return _Decision("new", current, False, (), _request(plan_path, mode, args))


def applies(plan_path: Union[str, Path], mode: str, args: argparse.Namespace) -> bool:
    """Whether a cascade decides this invocation: ``--cascade`` typed, or an unfinished one on record.

    Read-only. Never on a composite that does not take ``--cascade``. Raises
    :class:`CascadeRecordError` for a pointer or record it cannot read.
    """
    if not iw.takes_cascade(mode):
        return False
    if getattr(args, "cascade", False):
        return True
    current = load_current(plan_path, mode)
    return current is not None and current.state == RUNNING


def peek(plan_path: Union[str, Path], mode: str, args: argparse.Namespace) -> Peek:
    """The cascade's answer before anything is written: ``none``, ``work`` or ``complete``.

    Runs every refusal :func:`advance` would make at the start
    (``[CASCADE_CONFLICT]``, ``--files-from -``, a stage list that does not
    resolve, a record that cannot be read) by raising :class:`CascadeRefusal`,
    so a refused or finished launch leaves nothing behind. ``work`` includes a
    close-out owed after a stage's apply completed: completion detection by
    the plain composite rules would read that state as finished.
    """
    decision = _decide(plan_path, mode, args)
    kind = {"none": "none", "finished": "complete"}.get(decision.kind, "work")
    return Peek(kind=kind, lines=decision.notices)


# ---------------------------------------------------------------------------
# Writing: create, abandon, close, finish
# ---------------------------------------------------------------------------

def _new_stage(index: int, model: str) -> Dict[str, Any]:
    return {"index": index, "model": model, "state": PENDING, "bound_round": None,
            "scope_policy": None, "started_at": None, "finished_at": None,
            "skip_reason": None, "counts": None}


def _abandon(current: _Current) -> None:
    """Mark *current* ``abandoned``; done before the pointer moves or goes."""
    current.record["state"] = ABANDONED
    current.record["finished_at"] = current.record["finished_at"] or _now()
    _save(current)


def _create(
    plan_path: Union[str, Path], mode: str, args: argparse.Namespace, decision: _Decision
) -> Tuple[_Current, List[str]]:
    """A new cascade: its directory and files first, then the predecessor abandoned, then the pointer."""
    request = decision.request
    assert request is not None
    plan = _plan(plan_path)
    run_dir = composite_dir(plan, mode)
    while True:
        cascade_id = secrets.token_hex(16)
        relative = f"{CASCADES_DIR}/{datetime.now().strftime('%Y%m%dT%H%M%S')}-{cascade_id[:8]}"
        directory = run_dir / relative
        if not os.path.lexists(directory):
            break
    if not iw._reviews_code(mode):
        write_in_plan_dir(directory / START_NAME, plan.read_bytes(), make=True)
    if request.files is not None:
        write_in_plan_dir(directory / FILES_NAME,
                          "".join(f"{path}\n" for path in request.files).encode("utf-8"),
                          make=True)
    record = {
        "schema_version": SCHEMA_VERSION,
        "cascade_id": cascade_id,
        "mode": iw._row(mode).name,
        "state": RUNNING,
        "started_at": _now(),
        "scope_policy": _typed_policy(args),
        "selectors": {
            "files_file": FILES_NAME if request.files is not None else None,
            "base_ref": request.base_ref,
        },
        "stages": [_new_stage(i, model) for i, model in enumerate(request.models, start=1)],
        "finished_at": None,
    }
    current = _Current(mode=iw._row(mode).name, pointer=run_dir / POINTER_NAME,
                       cascade_dir=directory, record=record)
    _save(current)
    if decision.abandon and decision.current is not None:
        _abandon(decision.current)
    _write_json(current.pointer, {"schema_version": SCHEMA_VERSION,
                                  "cascade_id": cascade_id, "dir": relative}, "pointer")
    notices = list(decision.notices)
    notices.append(f"{CASCADE_MARKER} new cascade {cascade_id[:8]}: "
                   f"{_plural(current.of, 'stage')} ({', '.join(current.models)})")
    if request.source is not None:
        notices.append(f"[AUTO_RESOLVED] models: {', '.join(current.models)} ({request.source})")
    if current.of == 1:
        notices.append(ONE_MODEL_NOTE)
    return current, notices


def _render(current: _Current) -> None:
    # Imported here: the archive is the close-out's, which a read-only caller never reaches.
    from . import cascade_archive

    cascade_archive.render_summary(current.cascade_dir, current.record)


def _mark_done(current: _Current, index: int, counts: Dict[str, Any]) -> None:
    stage = current.stages[index - 1]
    stage.update(state=DONE, finished_at=_now(), counts=counts)
    _save(current)
    _render(current)


def _skip(current: _Current, index: int, reason: str, notices: List[str]) -> None:
    """A middle stage whose review produced no result: recorded skipped, and said so twice."""
    stage = current.stages[index - 1]
    stage.update(state=SKIPPED, finished_at=_now(), skip_reason=reason)
    _save(current)
    _render(current)
    notices.append(f"{SKIPPED_MARKER} {index} {stage['model']}: {reason}")
    notices.append(
        f"[AUTO_RESOLVED] {_ZERO_RESULT_SITE}: cascade stage {index} of {current.of} "
        f"({stage['model']}) produced no result; skipped, continuing at stage {index + 1}"
    )


def _finish(current: _Current, notices: Sequence[str]) -> Complete:
    """Every stage is closed: the cascade is recorded finished and the table rendered."""
    if current.state != FINISHED:
        current.record["state"] = FINISHED
        current.record["finished_at"] = _now()
        _save(current)
        _render(current)
    return _complete(current, notices)


def _complete(current: _Current, notices: Sequence[str]) -> Complete:
    return Complete(cascade_id=current.cascade_id, cascade_dir=current.cascade_dir,
                    of=current.of, summary_path=current.summary_path,
                    notices=tuple(notices))


def last_stage_stopped_message(current: _Current, reason: str) -> str:
    """The exit-3 stop of a last stage whose review produced no result."""
    index = current.of
    model = current.stages[index - 1]["model"]
    closed = "the stages before it are closed (applied, or skipped)" if index > 1 else (
        "it is the only stage")
    return (
        f"ERROR: cascade {current.cascade_id[:8]}: stage {index} of {current.of} "
        f"({model}) produced no review result: {reason}. The cascade stays unfinished "
        f"at stage {index}, and {closed}. Run the command again to start stage "
        f"{index} over."
    )


def stage_not_finished_message(current: _Current, index: int, why: str) -> str:
    """The exit-3 stop of a continue call that found the stage it follows still open."""
    model = current.stages[index - 1]["model"]
    return (
        f"ERROR: cascade {current.cascade_id[:8]}: stage {index} of {current.of} "
        f"({model}) did not finish: {why}. Nothing was closed out and no later stage "
        f"was started. Deal with the stop the stage's steps reported, then run the "
        f"command again to continue stage {index}."
    )


# ---------------------------------------------------------------------------
# Advancing: bind, close out, hand out
# ---------------------------------------------------------------------------

def _freeze(current: _Current, mode: str, index: int, plan: Path) -> Path:
    # Imported here: the ledger reads the archive, which only the writer needs.
    from . import cascade_ledger

    try:
        return Path(cascade_ledger.freeze_inputs(
            cascade_dir=current.cascade_dir, cascade_id=current.cascade_id, mode=current.mode,
            stage=index, of=current.of, model=current.stages[index - 1]["model"],
            plan_path=plan,
        ))
    except provenance.CascadeProvenanceError as exc:
        raise CascadeRefusal(EXIT_NEEDS_HUMAN, provenance.error_line(exc)) from None
    except cascade_ledger.ArchiveRefusal as exc:
        # A missing start.md or an archive it cannot trust: stop, never freeze
        # a ledger from part of the history.
        raise CascadeRefusal(EXIT_NEEDS_HUMAN, exc.message) from None


def _hand_out(
    plan: Path, mode: str, args: argparse.Namespace, current: _Current, index: int,
    *, force: bool, notices: List[str],
) -> StagePlan:
    """Stage *index* to run: inputs frozen (idempotent), then the stage started if pending."""
    manifest = _freeze(current, mode, index, plan)
    stage = current.stages[index - 1]
    if stage["state"] == PENDING:
        _start_stage(current, stage)
        _save(current)
        # The table reads "in progress" for the stage now handed out, so a run
        # that stops in it never shows it as "not started".
        _render(current)
    return StagePlan(
        cascade_id=current.cascade_id, cascade_dir=current.cascade_dir, stage=index,
        of=current.of, model=stage["model"],
        stage_args=derive_stage_args(args, mode, current, index, force=force,
                                     manifest=manifest),
        notices=tuple(notices), summary_path=current.summary_path,
    )


def _close_out(
    plan: Path, mode: str, current: _Current, index: int, round_id: Optional[str],
    stage_args: argparse.Namespace,
) -> Optional[Dict[str, Any]]:
    """Archive stage *index* under the archive's locks: its counts, or ``None`` when raced.

    The archive re-reads after locking through *recheck*: the round still
    carries this stage's block and id, and the apply is still recorded done.
    When it no longer does, nothing is archived and the caller plans again.
    """
    # Imported here: the archive takes phase locks and copies trees, which only
    # the writer reaches.
    from . import cascade_archive

    def recheck() -> bool:
        try:
            view = _review_view(plan, mode)
            return (view.belongs_to(current.cascade_id, index) and view.round_id == round_id
                    and _stage_done(plan, mode, stage_args))
        except CascadeRefusal:
            return False

    try:
        return cascade_archive.close_out(
            plan_path=plan, mode=current.mode, cascade_dir=current.cascade_dir,
            cascade_id=current.cascade_id, stage=index,
            model=current.stages[index - 1]["model"], round_id=round_id, recheck=recheck,
        )
    except cascade_archive.CloseOutRaced:
        return None
    except cascade_archive.ArchiveRefusal as exc:
        raise CascadeRefusal(EXIT_NEEDS_HUMAN, exc.message) from None


def _published_counts(current: _Current, index: int) -> Optional[Dict[str, Any]]:
    """Stage *index*'s counts from its published ``artifacts/``, ``None`` when it has none.

    An ``artifacts/`` whose ``.complete.json`` does not check out (missing,
    invalid, stale, another cascade's or stage's) stops here, at exit 3
    naming the directory, before any binding or hand-out: left to the
    close-out, it would only stop the run after a foreign round had already
    sent the stage's paid review and apply round again.
    """
    # Imported here: as in :func:`_render`.
    from . import cascade_archive, cascade_ledger

    counts = cascade_archive.published_counts(current.cascade_dir, index, current.cascade_id)
    if counts is not None:
        return counts
    artifacts = current.cascade_dir / f"stage-{index}" / "artifacts"
    if not os.path.lexists(artifacts):
        return None
    try:
        cascade_ledger.read_complete(artifacts, cascade_id=current.cascade_id, stage=index)
    except cascade_ledger.ArchiveRefusal as exc:
        raise CascadeRefusal(EXIT_NEEDS_HUMAN, exc.message) from None
    raise CascadeRefusal(EXIT_NEEDS_HUMAN, (  # pragma: no cover - read_complete refuses first
        f"ERROR: the cascade archive {artifacts} cannot be read as stage {index}'s. "
        "Nothing was changed. Start a new cascade with --force --cascade."
    ))


def _start_stage(current: _Current, stage: Dict[str, Any]) -> None:
    """A pending stage starts: its time, and the cascade's policy as the one it runs under."""
    stage.update(state=STAGE_RUNNING, started_at=_now(),
                 scope_policy=current.record["scope_policy"])


def _bind(current: _Current, index: int, round_id: Optional[str]) -> None:
    """Stage *index*'s round is on record: remember its id (a retry stamps a new one)."""
    stage = current.stages[index - 1]
    changed = False
    if stage["state"] == PENDING:
        _start_stage(current, stage)
        changed = True
    if round_id and stage["bound_round"] != round_id:
        stage["bound_round"] = round_id
        changed = True
    if changed:
        _save(current)


def _raced(current: _Current, index: int, attempts: int) -> None:
    if attempts >= CLOSE_OUT_ATTEMPTS:
        raise CascadeRefusal(EXIT_NEEDS_HUMAN, (
            f"ERROR: cascade {current.cascade_id[:8]}: stage {index}'s review or apply "
            "kept changing while it was being archived, so nothing was archived. Let "
            "the other run finish, then run the command again."
        ))


def _not_finished(current: _Current, index: int, after_stage: Optional[int], why: str) -> None:
    """Raise :class:`StageNotFinished` when the call follows stage *index*, still open."""
    if after_stage is not None and after_stage == index:
        raise StageNotFinished(stage_not_finished_message(current, index, why),
                               cascade_id=current.cascade_id, stage=index, of=current.of,
                               model=current.stages[index - 1]["model"])


def _walk(
    plan: Path, mode: str, args: argparse.Namespace, current: _Current, *,
    initial: bool, notices: List[str], after_stage: Optional[int] = None,
) -> Union[StagePlan, Complete]:
    """From the current stage on: close what is done, skip a failed middle stage, hand out the rest.

    Binding the review round on record to stage *k*:

    * the round carries this cascade's stage *k* block and finished with no
      model result: a middle stage is skipped; the last stage starts over on
      the first call of an invocation, and stops (exit 3) on a later one;
    * the block is stage *k*'s otherwise (a first fan-out or a retry, live,
      interrupted or with results): the round is bound and today's rules
      decide what runs, a close-out first when the apply is done;
    * any other block (none, another cascade's, an earlier stage's) while the
      stage is bound: a foreign round replaced it, so the stage starts over;
    * any other block while unbound: the stage has not started; a fresh round.

    A stage whose ``artifacts/`` the archive already published for this
    cascade is closed from those files, whatever the live dirs hold now.

    *after_stage* is the stage a continue call follows: where stage *k*
    would be handed out again with *k* equal to it, :class:`StageNotFinished`
    is raised instead, so a call never prints the block it was called after.
    """
    raced = 0
    while True:
        index = _current_index(current)
        if index is None:
            return _finish(current, notices)
        stage = current.stages[index - 1]
        published = _published_counts(current, index)
        if published is not None:
            _mark_done(current, index, published)
            continue
        view = _review_view(plan, mode)
        if not view.belongs_to(current.cascade_id, index):
            if stage["bound_round"]:
                _not_finished(current, index, after_stage,
                              "the review round on record is no longer this stage's (a round "
                              "outside the cascade replaced it)")
                notices.append(f"NOTE: the review on record is not this cascade's stage "
                               f"{index}; starting stage {index} over")
                stage["bound_round"] = None
                _save(current)
            _not_finished(current, index, after_stage,
                          "no review round of this stage is on record (its review stopped "
                          "before it opened one, or never ran)")
            return _hand_out(plan, mode, args, current, index, force=True, notices=notices)
        if view.zero_result:
            reason = view.failure(stage["model"])
            if index < current.of:
                _skip(current, index, reason, notices)
                continue
            if not initial:
                raise LastStageStopped(last_stage_stopped_message(current, reason),
                                       cascade_id=current.cascade_id, stage=index,
                                       of=current.of, model=stage["model"])
            return _hand_out(plan, mode, args, current, index, force=True, notices=notices)
        _bind(current, index, view.round_id)
        probe = derive_stage_args(args, mode, current, index, force=False, manifest=None)
        if not _stage_done(plan, mode, probe):
            _not_finished(current, index, after_stage,
                          "its review round is on record, but its review and apply are not "
                          "both recorded done")
            return _hand_out(plan, mode, args, current, index, force=False, notices=notices)
        counts = _close_out(plan, mode, current, index, stage["bound_round"] or view.round_id,
                            probe)
        if counts is None:
            raced += 1
            _raced(current, index, raced)
            continue
        _mark_done(current, index, counts)


def _planner_payload(mode: str) -> Dict[str, Any]:
    """Who holds the composite run dir's lock while :func:`advance` plans, for a refusal."""
    payload: Dict[str, Any] = {
        "holder": f"{iw._row(mode).name} cascade planner",
        "mode": iw._row(mode).name,
        "pid": os.getpid(),
        "process_start_time": process_control.process_start_time(os.getpid()),
        "acquired_at": datetime.now().isoformat(),
    }
    active = detach.active_run()
    if active is not None:
        payload["run_id"] = active.run_id
    return payload


@contextlib.contextmanager
def _planning(plan: Path, mode: str, *, make: bool) -> Iterator[None]:
    """Hold the composite run dir's phase lock while :func:`advance` reads, decides and writes.

    The pointer and the record are read, decided on and written as one step:
    without the lock, two planners started together (two native ``util
    improve-cascade next`` calls, or an executor run beside one) both read
    "no cascade", each created its own, and both handed out a paid stage-1
    review. The lock is the ``process_control.PhaseLock`` every writer of
    the run dir takes (docs/development/runtime.md, "One writer per phase
    dir"), so a detached composite's worker, which holds it for its whole
    run, owns the pointer too.

    A lock this process already holds on the run dir (that worker's, or a
    caller's registered with ``improve_workflow.holding``) is used as it is
    and stays held. Otherwise it is taken non-blocking and tried
    ``improve_workflow.STEP_LOCK_ATTEMPTS`` times,
    ``STEP_LOCK_RETRY_S`` apart, as a composite step tries its own (every
    ``status`` poll takes and drops each phase lock); a lock it still cannot
    take is :class:`CascadeRefusal` (exit 3) with
    ``improve_workflow.live_owner_refusal``'s text, and nothing was read or
    written. Either way the lock is registered with
    ``improve_workflow.holding`` for the block, so the close-out it may run
    (``cascade_archive.close_out``: run dir, then review dir, then apply
    dir) uses it instead of refusing itself.

    *make*: create the run dir to lock it when it does not exist (a first
    call about to start a cascade). Without *make* a missing run dir is
    passed over unlocked: it holds no pointer, so there is nothing to read
    or continue and the call writes nothing.
    """
    row = iw._row(mode)
    directory = composite_dir(plan, mode)
    if not directory.is_dir():
        if not make:
            yield
            return
        directory = get_phase_dir(plan, row.phase)
    path = detach.lock_path(str(directory))
    held = iw._held_lock(directory) or process_control.held_phase_lock(path)
    if held is not None:
        with iw.holding(directory, held):
            yield
        return
    lock = process_control.PhaseLock(path)
    refused: Optional[process_control.LockUnavailable] = None
    for attempt in range(iw.STEP_LOCK_ATTEMPTS):
        if attempt:
            time.sleep(iw.STEP_LOCK_RETRY_S)
        try:
            lock.acquire(_planner_payload(mode))
        except process_control.LockUnavailable as exc:
            refused = exc
            continue
        except OSError as exc:
            raise CascadeRefusal(EXIT_NEEDS_HUMAN, (
                f"ERROR: {row.name}: could not lock {iw._display_path(path)} ({exc}). A "
                "cascade is planned only while its run dir's lock is held, so nothing "
                "was run."
            )) from None
        refused = None
        break
    if refused is not None:
        owner = iw._inspect(str(plan), row.phase, directory) or iw.LiveOwner(
            directory=str(directory),
            holder=str(refused.holder.get("holder") or "an unrecorded holder"),
            pid=refused.holder.get("pid"),
            verdict=process_control.holder_verdict(refused.holder or None),
            heartbeat_age_s=None,
            status_command=detach.status_command_for(str(plan), phase=row.phase),
            abort_command=None,
        )
        raise CascadeRefusal(EXIT_NEEDS_HUMAN, iw.live_owner_refusal(mode, owner))
    try:
        with iw.holding(directory, lock):
            yield
    finally:
        lock.release()


def _apply_typed_policy(current: _Current, args: argparse.Namespace) -> None:
    """A typed ``--scope-policy`` becomes the policy of the stages not started yet."""
    typed = _typed_policy(args)
    if typed is None or typed == current.record["scope_policy"]:
        return
    current.record["scope_policy"] = typed
    _save(current)


def advance(
    plan_path: Union[str, Path],
    mode: str,
    args: argparse.Namespace,
    *,
    initial: bool,
    cascade_id: Optional[str] = None,
    after_stage: Optional[int] = None,
) -> Union[StagePlan, Complete, NotACascade]:
    """Move the cascade forward and hand back what runs now; the only writer.

    *initial* is the first call of an invocation, with the user's flags: it
    may start a cascade, continue one, abandon an unfinished one (``--force``)
    or answer :class:`NotACascade`, as :func:`peek` decided. A later call
    (*initial* false) is bound to *cascade_id*: it never starts, restarts or
    abandons, ignores the restart and selector flags, and refuses with
    ``[CASCADE_CONFLICT]`` when the pointer names another cascade.

    A later call also names *after_stage*, the stage it follows: when, after
    binding, close-out and skipping, the current stage is still that one,
    neither closed nor skipped, it raises :class:`StageNotFinished` (exit 3)
    instead of handing the same stage out again. ``None`` (and every initial
    call) checks nothing.

    A stage whose review produced no result: a middle one is recorded
    skipped (``[CASCADE_STAGE_SKIPPED]`` and an ``[AUTO_RESOLVED]`` line among
    the notices) and the next stage comes back; the last one comes back fresh
    (``stage_args.force``) on an *initial* call, and raises
    :class:`LastStageStopped` (a :class:`CascadeRefusal`, exit 3) on a later one.

    Everything that writes runs under the composite run dir's lock
    (:func:`_planning`), and decides from what it reads after taking it. An
    initial call decides once before that, read-only: an answer that writes
    nothing (not a cascade run, a finished cascade's command again) needs no
    lock and creates no run dir. A run dir another live run holds the lock
    of is :class:`CascadeRefusal` (exit 3, the live-owner refusal).
    """
    plan = _plan(plan_path)
    if initial:
        early = _decide(plan, mode, args)
        if early.kind == "none" and not early.abandon:
            return NotACascade(notices=early.notices)
        if early.kind == "finished":
            assert early.current is not None
            return _complete(early.current, early.notices)
    with _planning(plan, mode, make=initial):
        return _advance(plan, mode, args, initial=initial, cascade_id=cascade_id,
                        after_stage=after_stage)


def _advance(
    plan: Path,
    mode: str,
    args: argparse.Namespace,
    *,
    initial: bool,
    cascade_id: Optional[str],
    after_stage: Optional[int],
) -> Union[StagePlan, Complete, NotACascade]:
    """:func:`advance` under the run dir's lock: read, decide, write."""
    if initial:
        decision = _decide(plan, mode, args)
        if decision.kind == "none":
            if decision.abandon and decision.current is not None:
                _abandon(decision.current)
                remove_in_plan_dir(decision.current.pointer)
            return NotACascade(notices=decision.notices)
        if decision.kind == "finished":
            assert decision.current is not None
            return _complete(decision.current, decision.notices)
        if decision.kind == "new":
            current, notices = _create(plan, mode, args, decision)
        else:
            assert decision.current is not None
            current, notices = decision.current, list(decision.notices)
            _apply_typed_policy(current, args)
        return _walk(plan, mode, args, current, initial=True, notices=notices)
    current = load_current(plan, mode)
    if current is None or current.cascade_id != cascade_id or current.state == ABANDONED:
        named = "no cascade" if current is None else (
            f"cascade {current.cascade_id[:8]} ({current.state})")
        raise CascadeRefusal(EXIT_NEEDS_HUMAN, (
            f"{CONFLICT_MARKER} --cascade-id: this call continues cascade "
            f"{str(cascade_id)[:8]}, but {iw._display_path(pointer_path(plan, mode))} names "
            f"{named}: another run started or left a cascade since. Run the composite's "
            "command again to see where it stands."
        ))
    if current.state == FINISHED:
        return _complete(current, ())
    return _walk(plan, mode, args, current, initial=False, notices=[],
                 after_stage=after_stage)


# ---------------------------------------------------------------------------
# Readers for the other surfaces
# ---------------------------------------------------------------------------

def zero_result_stage(plan_path: Union[str, Path], mode: str) -> bool:
    """Whether the review on record is the current stage's and produced no result. Read-only.

    The executor leg asks it when a stage's review step failed, before any
    failure reporting, to tell a middle-stage skip from a stop.
    """
    if not iw.takes_cascade(mode):
        return False
    current = load_current(plan_path, mode)
    if current is None or current.state != RUNNING:
        return False
    index = _current_index(current)
    if index is None:
        return False
    view = _review_view(plan_path, mode)
    return view.belongs_to(current.cascade_id, index) and view.zero_result


def cascade_status(plan_path: Union[str, Path], mode: str) -> Optional[Dict[str, Any]]:
    """``{cascade_id, state, stage, of, model, dir}`` of the pointer's cascade, or ``None``. Read-only.

    *stage* is the first stage not closed (the last one once every stage is).
    For ``status`` and the next-command readers, which answer "continue the
    composite" while *state* is ``running``. Raises :class:`CascadeRecordError`
    for a pointer or record it cannot read.
    """
    if not iw.takes_cascade(mode):
        return None
    current = load_current(plan_path, mode)
    if current is None:
        return None
    index = _current_index(current) or current.of
    return {
        "cascade_id": current.cascade_id,
        "state": current.state,
        "stage": index,
        "of": current.of,
        "model": current.stages[index - 1]["model"],
        "dir": str(current.cascade_dir),
    }

