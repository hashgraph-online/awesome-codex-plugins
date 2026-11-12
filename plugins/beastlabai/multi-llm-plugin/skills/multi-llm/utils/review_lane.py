"""What review-plan, review-tasks and review-code share as one review lane.

The review base (``utils/review_orchestrator_base.py``) runs review-plan and
review-tasks; ``code_review_orchestrator.py`` runs review-code. Both fan out to
models, group what came back, resolve a validation round and write a report.
The pieces here are written once for both, so a fix to one lane cannot miss
the other (docs/development/review-results.md, "The shared review lane"):

* :class:`ReviewLane`, the hooks a lane supplies where the lanes differ;
* :func:`select_review_models` and :func:`open_round`, a fan-out's model
  selection and the opening checkpoint of its round;
* :class:`SlotResult`, one model slot's outcome, the shape :func:`run_slot`
  returns and both fan-outs close over;
* :func:`close_fanout`, what follows a fan-out up to grouping: each slot's
  result saved, the losses named, the sandbox words and salvage recorded, and
  the run either continued or ended at exit 3 when no model answered;
* :func:`group_findings` and :func:`materialize_fanout_round`, a fan-out's
  grouping and the validation round it publishes, dispatches or hands out;
* :func:`reaggregate_result_files` and :func:`load_reaggregate_results`, the
  loading half of a ``--reaggregate``;
* :func:`bind_grouping`, the grouping a ``--reaggregate`` reports: the bound
  ``grouped.json`` reused, or the results regrouped;
* :func:`resolve_validation_round`, what a ``--reaggregate`` does with the
  validation round beside its grouping: reuse the verdicts bound to it, merge
  or hand out a round on disk, or build a new one;
* :func:`run_slot`, one model slot: the guard, the ladder and the checks,
  over each lane's :class:`ReviewSlot`, and :func:`reject_slot_answer`, what
  every slot the checks failed leaves behind (an answer that failed its checks
  or never finished them is withheld: docs/development/review-results.md,
  "Withheld slot answers");
* :func:`hand_back_report`, a published report's files handed back on both
  channels;
* :func:`record_phase_complete` and :func:`complete_reaggregate`, the
  completion every ending that records the phase shares.

``tests/test_review_lane_parity.py`` runs the same offline scenarios on both
lanes and fails on any behaviour that differs between them.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Protocol, Sequence, Tuple

from . import cli_common
from .atomic_io import read_back_text
from . import detach as _detach
from . import held_folder as _held_folder
from . import interactive as _interactive
from . import result_files as _result_files
from . import review_round as _review_round
from . import run_record as _run_record
from . import run_registry as _run_registry
from . import scope_policy as _sp
from . import scope_round as _scope_round
from . import status_file as _status_file
from . import subagent_tasks as _subagent_tasks
from . import unattended as _unattended
from .json_extractor import generate_output_path
from .progress_tracker import DEADLINE_ERROR, PhaseProgress
from .provider_outcome import SALVAGE_TEXT_KEY
from .llm_client import SALVAGE_FAILURE_KEY
from .schema_validator import drop_non_record_entries
from .state_manager import CURRENT_FORMAT_VERSION, load_groups_payload, save_groups_payload
from .subagent_tasks import TaskFileError
from .validation import (
    BoundDocument,
    ValidationRound,
    apply_validation_to_groups,
    ensure_prompt_sidecars,
    host_index_path,
    host_views_lock,
    legacy_context_round_reason,
    load_validation_results,
    materialize_validation_round,
    publish_from_task_document,
    resolved_reaggregate_command,
    validation_source_decision,
)
from . import scope_policy_runs as _scope_policy_runs
from . import failure_capture


# ---------------------------------------------------------------------------
# The lane's own hooks, and the base's steps it lends the shared stages
# ---------------------------------------------------------------------------

class ReviewLane(Protocol):
    """What one review lane supplies where the lanes legitimately differ.

    The review base's lane (review-plan, review-tasks) and review-code's
    (``code_review_orchestrator.CodeLane``) each build one per run; the shared
    stages here call these hooks and nothing lane-specific besides.

    * ``mode``: the mode word the user's commands name (``review-plan``,
      ``review-code``); ``phase_name`` the phase dir and state key
      (``review-plan``, ``code-review``); ``phase_dir`` and ``plan_path`` this
      run's.
    * ``retry_command(*flags)``: the follow-up command a refusal or a failed
      run names, in the lane's spelling (review-code spells a commit review's
      command in its commit mode).
    * ``save_slot(slot)``: write one slot's ``{model}.json`` (or the salvage
      request of a losing slot); ``False`` when the slot is a failure.
    * ``adopt_salvaged(model_spec, path)``: the repaired ``{model}.json`` an
      in-process salvage wrote, as the slot it makes this model, or ``None``
      to leave the model failed.
    * ``round_follow_up(document, typed=...)``: the ``--reaggregate`` that
      advances a materialized round, in the lane's spelling; ``typed`` names
      the plan as the user typed it, for the printed hand-off.
      ``orchestrator_script`` is the script the round's durable follow-up
      fields name (``cli_common.durable_reaggregate_fields``).
    * ``fanout_steps()`` and ``round_steps()``: the review base's steps the
      shared stages call, built from the names the lane's own module binds,
      at call time, so a test that patches one there reaches the shared stage
      too.
    * ``reuse_checks_inputs``: whether a ``--reaggregate`` that reuses bound
      verdicts first holds their task file to the lane's current inputs
      (:func:`resolve_validation_round`). review-code's does: its prompts
      embed the reviewed-code excerpt and a commit review's frozen context
      plan, which no snapshot re-hash covers. The base's does not, and its
      reuse is bound by the round's snapshots alone.
    """

    mode: str
    phase_name: str
    phase_dir: str
    plan_path: str
    orchestrator_script: str
    reuse_checks_inputs: bool

    def retry_command(self, *flags: str) -> str: ...

    def round_follow_up(
        self, document: Mapping[str, Any], *, typed: bool = False,
    ) -> Optional[str]: ...

    def save_slot(self, slot: "SlotResult") -> bool: ...

    def adopt_salvaged(self, model_spec: str, path: Path) -> Optional["SlotResult"]: ...

    def fanout_steps(self) -> "FanoutSteps": ...

    def round_steps(self) -> "RoundSteps": ...


# ---------------------------------------------------------------------------
# A damaged checkpoint, recovered at a fresh run's startup
# ---------------------------------------------------------------------------

#: What every earlier model result and salvage file of a phase whose
#: checkpoint was found damaged is renamed with: ``<name>.quarantined-<stamp>``,
#: the stamp the archived checkpoint carries. The name no longer ends in
#: ``.json``, so no reader of the phase dir's results or salvage pairs matches
#: it (the result candidates, every ``salvage_*.json`` glob, a resume's skip).
QUARANTINED_INFIX = ".quarantined-"

#: The warning line of a fresh run that recovered its phase's damaged
#: checkpoint (:func:`recover_damaged_checkpoint`); the round records the same
#: note under ``result_notes``.
CHECKPOINT_RECOVERED_MARKER = "[CHECKPOINT_RECOVERED]"



@dataclass(frozen=True)
class CheckpointRecovery:
    """What :func:`recover_damaged_checkpoint` did: the path of the damaged
    checkpoint's copy, the files it set aside (their new names) and the
    validation round files it retired, and the one *note* the round records
    about it."""

    archived: str
    quarantined: Tuple[str, ...]
    retired: Tuple[str, ...]
    note: str


def recovery_notes(recovery: Optional[CheckpointRecovery]) -> Tuple[str, ...]:
    """The round's notes from *recovery* (``review_round.start_round``'s *notes*)."""
    return (recovery.note,) if recovery is not None else ()


def salvage_refused(phase_dir: str, model_spec: str) -> bool:
    """Whether *model_spec*'s salvage request must not be written, said once
    when so: its phase's damaged checkpoint was replaced
    (``result_files.RECOVERED_KEY``), and a repair is a file on disk, which
    that phase never trusts. The model stays failed."""
    if not _result_files.phase_recovered(phase_dir):
        return False
    print(f"[{model_spec}] No salvage request written: {phase_dir}'s damaged "
          f"checkpoint was replaced, so no repaired file there would be read; "
          f"the model stays failed")
    return True


def recovered_phase_advice(phase_dir: str) -> str:
    """What a stop over a recovered phase (``result_files.RECOVERED_KEY``)
    says: why nothing on disk is read, and the two ways on."""
    return (
        f"its damaged checkpoint was replaced by a fresh run: a run that left it "
        f"behind may still write any file there, so no result file in it is read "
        f"again. Run the phase again without --reaggregate (every selected model "
        f"is dispatched again), or move the whole phase folder {phase_dir} aside, "
        f"or delete it, to start clean."
    )


class _RecoveryStopped(Exception):
    """One step of :func:`recover_damaged_checkpoint` failed; the message says which."""


def _stop_recovery(phase_dir: str, run_id: Optional[str], what: str) -> None:
    message = (f"ERROR: {what} Nothing was dispatched. "
               f"{_status_file.unreadable_checkpoint_advice(phase_dir)}")
    # A detached worker's launch is waiting for its run record: it reports this.
    _detach.record_worker_refusal(phase_dir, run_id, message)
    sys.exit(_unattended.fail_closed(message))


def _is_salvage_name(name: str) -> bool:
    """A salvage request or task still outstanding (``salvage_*.json``)."""
    return name.startswith("salvage_") and name.endswith(".json")


def _earlier_answers(phase_dir: str) -> List[str]:
    """Every name in *phase_dir* a reader could take for a model's answer:
    the result candidates (``result_files.is_model_result_name``, whatever
    their content) and the salvage pairs. ``OSError`` when the folder cannot
    be listed."""
    return [
        name for name in sorted(os.listdir(phase_dir))
        if _result_files.is_model_result_name(name) or _is_salvage_name(name)
    ]


def _quarantine_earlier_answers(phase_dir: str, stamp: str) -> List[str]:
    """Rename every earlier answer in *phase_dir* (:func:`_earlier_answers`)
    to ``<name>.quarantined-<stamp>``, through the folder held below the plan's
    directory; the new names. Raises :class:`_RecoveryStopped` when the folder
    cannot be listed, a rename fails, or an answer is still there after
    (written meanwhile): every one is out, or the caller stops."""
    try:
        names = _earlier_answers(phase_dir)
    except OSError as exc:
        raise _RecoveryStopped(f"{phase_dir} could not be listed ({exc}).") from exc
    moved: List[str] = []
    for name in names:
        target = f"{name}{QUARANTINED_INFIX}{stamp}"
        suffix = 2
        while os.path.lexists(os.path.join(phase_dir, target)):
            target = f"{name}{QUARANTINED_INFIX}{stamp}-{suffix}"
            suffix += 1
        try:
            _held_folder.rename_in_plan_dir(os.path.join(phase_dir, name), target)
        except OSError as exc:
            raise _RecoveryStopped(
                f"{name} could not be set aside ({exc})"
                + (f", after {len(moved)} other file(s) were." if moved else ".")
            ) from exc
        moved.append(target)
    try:
        left = _earlier_answers(phase_dir)
    except OSError as exc:
        raise _RecoveryStopped(f"{phase_dir} could not be listed again ({exc}).") from exc
    if left:
        raise _RecoveryStopped(
            f"{', '.join(left)} appeared in the folder while the earlier results "
            f"were being set aside: something is still writing there.")
    return moved


def _validation_round_left(phase_dir: str) -> List[str]:
    """The validation round's files still in *phase_dir* under their live
    names (``validation.json``, ``validation_tasks.json`` and its host index,
    a batch reply or its prompt sidecar), the ones a round or a host reads."""
    try:
        names = sorted(os.listdir(phase_dir))
    except OSError:
        return [_review_round.TASKS_NAME]
    index = os.path.basename(host_index_path(_review_round.TASKS_NAME))
    return [
        name for name in names
        if name in (_review_round.VALIDATION_NAME, _review_round.TASKS_NAME, index)
        or (name.startswith("validation_batch_") and ".stale" not in name
            and (name.endswith(".json") or name.endswith(".prompt.txt")))
    ]


def recover_damaged_checkpoint(
    *,
    phase_dir: str,
    phase_name: str,
    plan_file: str,
    run_id: Optional[str] = None,
    retire_validation_round: Optional[Callable[..., Any]] = None,
    fields: Optional[Mapping[str, Any]] = None,
) -> Optional[CheckpointRecovery]:
    """A fresh review run's startup over a damaged ``.status.json``: recover
    it, reusing no earlier answer, and go on with a warning; ``None`` when
    the checkpoint is absent or readable, and nothing is done.

    Called by both review fan-outs (never a ``--reaggregate``, which can only
    reuse) in the process that will own the round, after its phase lock and
    the earlier run's cleanup check (``detach.PhaseRun.take``) and before its
    boundary: a detached worker claims its run *in* the checkpoint
    (``RunHandle.start``), so the checkpoint is recovered before that claim,
    and the round is stamped after it (``review_round.start_round``). A
    ``--detach`` launcher leaves it to its worker. In order:

    1. **Damage, not a failed read** (``status_file.checkpoint_damage``): the
       same bytes on every read, from a regular file, that are not a JSON
       object. A read that fails, or anything else, stops the run (exit 3)
       with nothing changed.
    2. **Sole owner.** This process holds the phase's ``.lock``, so no live
       run writes the folder, and the run registry, read strictly
       (``detach.registered_runs_of``), keeps no run of it: the checkpoint
       was the only other record of an earlier run's processes. A registry
       that cannot be listed, or holds an entry whose phase cannot be told,
       stops the run too, nothing changed.
    3. **Every earlier answer set aside first**, with the damaged checkpoint
       still in place: each model result and salvage pair of every model,
       selected or not, renamed ``<name>.quarantined-<stamp>``
       (:data:`QUARANTINED_INFIX`), and the validation round retired
       (*retire_validation_round*: the lane's
       ``retire_stale_validation_round``) and checked gone, its host index
       included, under one hold of the views lock (``host_views_lock``), so
       no refresh republishes the index in between.
    4. **The damaged bytes copied** to ``.status.json.unreadable-<stamp>``
       (``status_file.archive_damaged_checkpoint``), then **a fresh
       checkpoint renamed over the damaged one** in one step, only while it
       still holds those bytes, and read back
       (``status_file.publish_checkpoint``), under one hold of the checkpoint
       mutex. It records ``result_files.RECOVERED_KEY``: a provider the
       crashed run left behind may still write any file of the folder, so no
       result file on disk is trusted there again. Every model, selected,
       unselected or never seen, is withheld (``result_files.withheld_models``):
       a resume reuses nothing, salvage never runs, a ``--reaggregate``
       refuses, and the round counts only the answers it holds in memory.
       And it records the warning under ``result_notes``.
    5. **The warning**: :data:`CHECKPOINT_RECOVERED_MARKER`, and the note the round's
       opening records again (:func:`recovery_notes`).

    A step that fails stops the run at exit 3, ``needs-human``, before
    anything is dispatched, and at every point a checkpoint refuses the
    folder: the damaged one, kept in place until the fresh one, which
    withholds every model, replaces it (docs/development/review-results.md,
    "Withheld slot answers"). A detached worker's stop is recorded for its
    launch (``detach.record_worker_refusal``), identified by *run_id*, which
    the registry check also leaves out.

    *fields* are further keys of the fresh checkpoint, for a phase whose
    checkpoint carries more than a review round's (``ask``'s ``question``);
    a phase with no validation round passes no *retire_validation_round*.
    """
    phase_dir = str(phase_dir)
    status = _status_file.status_path(phase_dir)
    try:
        damage = _status_file.checkpoint_damage(
            phase_dir, attempts=_status_file.CHECKPOINT_READ_ATTEMPTS,
        )
    except _status_file.CheckpointUnreadable as exc:
        cause = exc.__cause__ or exc
        _stop_recovery(phase_dir, run_id, (
            f"{status} could not be read ({cause}), on each of "
            f"{_status_file.CHECKPOINT_READ_ATTEMPTS} reads: nothing shows that "
            f"its bytes are damaged, so it is left as it is."
        ))
        return None
    if damage is None:
        return None
    print(f"WARNING: {status} is damaged ({damage.detail}, {damage.size} bytes); this "
          f"fresh run recovers it before it starts its round.", file=sys.stderr)
    if not _detach.holds_phase_lock(phase_dir):
        _stop_recovery(phase_dir, run_id, (
            f"{status} is damaged, and this process does not hold "
            f"{_detach.lock_path(phase_dir)}: it is never recovered without it."))
    sweep = cli_common.dispatcher_command('util', 'runs', '--sweep')
    try:
        earlier = _detach.registered_runs_of(phase_dir, plan_file=plan_file,
                                            except_run_id=run_id)
    except _run_registry.UnreadableEntries as exc:
        _stop_recovery(phase_dir, run_id, (
            f"{status} is damaged, and the run registry holds entries whose run "
            f"cannot be told ({', '.join(exc.paths)}): any of them may be an earlier "
            f"run of this phase still writing there, so the folder is left as it "
            f"is. Check them with {cli_common.dispatcher_command('util', 'runs')}, "
            f"close them out with {sweep} or remove the ones you know are finished, "
            f"then run this command again."))
        return None
    except OSError as exc:
        _stop_recovery(phase_dir, run_id, (
            f"{status} is damaged, and the run registry could not be read ({exc}): "
            f"whether an earlier run of this phase may still be writing there is "
            f"unknown, so it is left as it is."))
        return None
    if earlier:
        runs = ", ".join(str(entry.get("run_id")) for entry in earlier)
        _stop_recovery(phase_dir, run_id, (
            f"{status} is damaged, and the run registry still keeps an earlier "
            f"run of this phase ({runs}): with its checkpoint unreadable, nothing "
            f"shows that run's processes have stopped, so the folder is left as "
            f"it is. Close it out with {sweep}, then run this command again."))
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    try:
        quarantined = _quarantine_earlier_answers(phase_dir, stamp)
    except _RecoveryStopped as exc:
        _stop_recovery(phase_dir, run_id, (
            f"{status} is damaged, and the earlier results in the folder could not "
            f"all be set aside: {exc} The damaged checkpoint is kept in place, so "
            f"no later run or --reaggregate reads them."))
        return None
    retired: Sequence[Any] = ()
    left: List[str] = []
    if retire_validation_round is not None:
        # One hold across the retirement and the check: a host-index refresh
        # between them would publish the old round's index again
        # (docs/development/delegation.md#the-host-index).
        with host_views_lock(phase_dir):
            retired = retire_validation_round(
                phase_dir, reason="its phase's checkpoint was found damaged",
            ) or ()
            left = _validation_round_left(phase_dir)
    if left:
        _stop_recovery(phase_dir, run_id, (
            f"{status} is damaged, and the earlier validation round could not be "
            f"retired ({', '.join(left)} left in place). The damaged checkpoint is "
            f"kept in place."))
    archived_name = f"{_status_file.STATUS_FILENAME}{_status_file.UNREADABLE_ARCHIVE_INFIX}{stamp}"
    note = (
        f"{_status_file.STATUS_FILENAME} was damaged ({damage.detail}); its bytes are "
        f"kept as {archived_name}; every earlier result in the folder was set aside "
        f"({len(quarantined)} file(s), renamed *{QUARANTINED_INFIX}{stamp}, "
        f"nothing deleted), so this round reuses none of them; a run that left it "
        f"behind may still write there, so no result file in this folder is read "
        f"again: a later run dispatches every model again, no salvage runs and a "
        f"--reaggregate refuses (move the whole phase folder aside to start clean)"
    )
    try:
        with _status_file.checkpoint_lock(phase_dir, required=True):
            try:
                archived = _status_file.archive_damaged_checkpoint(phase_dir, damage, stamp)
            except OSError as exc:
                raise _RecoveryStopped(
                    f"its bytes could not be copied aside ({exc}). The damaged "
                    f"checkpoint is kept in place; the earlier results stay set "
                    f"aside.") from exc
            note = note.replace(archived_name, os.path.basename(archived))
            try:
                _status_file.publish_checkpoint(phase_dir, {
                    "phase": phase_name,
                    "state": _review_round.FANOUT_STATE,
                    _result_files.RECOVERED_KEY: _result_files.recovery_record(),
                    _result_files.RESULT_NOTES_KEY: [note],
                    **dict(fields or {}),
                }, replacing=damage)
            except (OSError, _status_file.CheckpointUnreadable) as exc:
                raise _RecoveryStopped(
                    f"its bytes were copied to {os.path.basename(archived)} and every "
                    f"earlier result set aside, but a fresh checkpoint could not be "
                    f"written over it and read back ({exc}). Either the damaged "
                    f"checkpoint is still in place, or the fresh one, which withholds "
                    f"every model's answer, is.") from exc
    except _status_file.CheckpointLockUnavailable:
        _stop_recovery(phase_dir, run_id, (
            f"{status} is damaged, and {_status_file.STATUS_LOCK_FILENAME} could not "
            f"be taken to replace it. The damaged checkpoint is kept in place; the "
            f"earlier results stay set aside."))
        return None
    except _RecoveryStopped as exc:
        _stop_recovery(phase_dir, run_id, f"{status} is damaged, and {exc}")
        return None
    print(f"{CHECKPOINT_RECOVERED_MARKER} {note}.")
    return CheckpointRecovery(
        archived=archived, quarantined=tuple(quarantined),
        retired=tuple(str(path) for path in retired or ()), note=note,
    )


# ---------------------------------------------------------------------------
# Opening a fan-out's round
# ---------------------------------------------------------------------------

def select_review_models(args: Any, *, mode: str, anchor: str) -> Tuple[List[str], bool]:
    """The models a fan-out runs, and whether it runs unattended (``--yes``).

    ``--quick`` and ``--interactive`` are refused together (exit 1). The
    selection is ``interactive.select_models``: under ``--yes`` it stops at
    ``defaults.models`` and fails closed with exit 3 when nothing resolves
    (D6 row 2), never a rendered multi-select. *mode* picks the mode's
    defaults; *anchor* is the plan the per-project config is found from.
    """
    if args.quick and args.interactive:
        print("ERROR: --quick and --interactive are mutually exclusive.")
        sys.exit(1)
    unattended = bool(getattr(args, "yes", False))
    try:
        model_specs = _interactive.select_models(
            args, mode=mode, anchor=anchor, unattended=unattended,
        )
    except _interactive.ModelSelectionError as e:
        sys.exit(e.exit_code)
    return model_specs, unattended


@dataclass(frozen=True)
class RoundOpening:
    """What the previous attempt of the phase recorded, read by
    :func:`open_round` before its opening write erased it."""

    prior_usage: Dict[str, Dict[str, Any]]
    prior_served: Dict[str, Dict[str, Any]]


def open_round(
    claim: _review_round.Claim,
    steps: "RoundSteps",
    args: Any,
    *,
    phase_name: str,
    phase_dir: str,
    model_specs: Sequence[str],
    scope_round_policy: Any,
    unattended: bool,
    after_opening: Optional[Callable[[], None]] = None,
) -> RoundOpening:
    """The opening checkpoint of a fan-out's round, the same on every lane.

    The previous attempt's ``usage`` and sandbox words are read first: the
    opening write replaces every key but the reserved objects, and a resumed
    slot answered from its result file invokes no adapter to refill them
    (Stage U; the retired-rung notice reads the sandbox words). The write
    itself runs while the round is this run's (``claim.opening``) and records
    the requested specs, the only record of their canonical spelling a
    reaggregate can invert a result-file stem with. It also drops the previous
    run's ``progress``, which on the foreground lane nothing else does, so a
    re-run never opens on the last run's terminal map.

    *after_opening* runs right after the write (review-code reads it back),
    after the round's notes from its start (``claim.notes``: a recovered
    checkpoint's warning, :func:`recover_damaged_checkpoint`) are recorded
    again under ``result_notes``, which the write replaced; in a phase an
    earlier run recovered, one warning that nothing on disk is reused takes
    their place.
    Under ``--yes`` the auto-selected models (D6 row 2) and an untyped scope
    policy (row 16) are recorded as resolutions; then the fan-out's step is
    published.

    The withheld models (``models_rejected``, ``models_unchecked``) survive
    the write, every model's, selected or not: both maps are read whole under
    the same lock as the write, and carried over as read, and so is a
    recovered checkpoint's ``result_files.RECOVERED_KEY``, which withholds
    every model. The resume skip that follows reads them, and refuses to
    reuse their files;
    :func:`close_fanout` writes both maps again. A checkpoint that cannot be
    read, even after ``status_file.CHECKPOINT_READ_ATTEMPTS`` reads, may hold
    either map, and maps rebuilt without it would drop every earlier refusal:
    the run stops there at exit 3, ``needs-human``, before anything is
    written or dispatched (docs/development/review-results.md, "Withheld slot
    answers").
    """
    prior_usage = steps.recorded_usage(phase_dir) or {}
    prior_served = steps.recorded_served_models(phase_dir) or {}
    withheld: Optional[Dict[str, Dict[str, Any]]] = None
    with claim.opening():
        try:
            withheld = _result_files.recorded_withheld(
                phase_dir, attempts=_status_file.CHECKPOINT_READ_ATTEMPTS,
            )
        except _status_file.CheckpointUnreadable:
            pass
        else:
            rejected = withheld[_result_files.REJECTED_MODELS_KEY]
            unchecked = withheld[_result_files.UNCHECKED_MODELS_KEY]
            recovery = withheld.get(_result_files.RECOVERED_KEY)
            steps.write_status(phase_dir, {
                "phase": phase_name,
                "state": "models_running",
                "started_at": datetime.now().isoformat(),
                "models_requested": list(model_specs),
                "error": None,
                _review_round.ROUND_KEY: claim.round_id,
                "progress": None,
                **({_result_files.REJECTED_MODELS_KEY: rejected} if rejected else {}),
                **({_result_files.UNCHECKED_MODELS_KEY: unchecked} if unchecked else {}),
                **({_result_files.RECOVERED_KEY: recovery} if recovery is not None else {}),
            })
    if withheld is None:
        sys.exit(_unattended.fail_closed(
            f"ERROR: {_status_file.status_path(phase_dir)} could not be read "
            f"while this run opened its round, so the records of the answers "
            f"this phase withholds (models whose safety checks failed or never "
            f"finished) could not be carried over; nothing was dispatched. "
            f"{_status_file.unreadable_checkpoint_advice(phase_dir)}"
        ))
    # The round's notes from its start (a recovered checkpoint's warning):
    # the write above replaced the checkpoint's `result_notes`.
    for note in claim.notes:
        _result_files.append_result_note(phase_dir, note)
    if withheld.get(_result_files.RECOVERED_KEY) is not None and not claim.notes:
        # An earlier run recovered the phase: said once, here, rather than per
        # model by the resume skip (docs/development/review-results.md,
        # "Recovering a damaged one").
        note = (
            "an earlier run replaced this phase's damaged checkpoint, and a run "
            "that left it behind may still write there: no result file in the "
            "folder is reused, so every selected model is dispatched again, no "
            "salvage runs and a --reaggregate refuses; move the whole phase "
            "folder aside to start clean"
        )
        print(f"WARNING: {note}.", file=sys.stderr)
        _result_files.append_result_note(phase_dir, note)
    if after_opening is not None:
        after_opening()
    # Recorded rather than merely applied: an auto-selection nobody can see
    # afterwards is indistinguishable from a silent degradation. Only under
    # `--yes`, where it replaced a question.
    if unattended and not args.models and not args.quick:
        _unattended.record_resolution(
            phase_dir, _unattended.row(2).site_id,
            "defaults.models: " + ", ".join(model_specs),
        )
    if unattended:
        _scope_policy_runs.announce(
            phase_dir, scope_round_policy.policy, scope_round_policy.source,
            unattended=True,
        )
    steps.report_progress(
        phase_dir, step="fanout", models_total=len(model_specs),
        models_done=0, models_succeeded=0,
    )
    return RoundOpening(prior_usage=prior_usage, prior_served=prior_served)


# ---------------------------------------------------------------------------
# One slot's outcome
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SlotResult:
    """One model slot's outcome, as both review fan-outs read it.

    ``payload`` is the answer of a run that completed: review-plan's output
    text, review-code's issue list. It is ``None`` on every losing path, so a
    crashed provider's parseable stdout is never saved as a completed review
    (``failure_output_from_result`` is the text salvage reads instead).
    ``details`` is the lane's whole record (review-plan's result dict, with the
    served model, sandbox word and usage the checkpoint records); ``failure``
    is the salvage failure kind the slot recorded. ``rejected`` is the guard's
    reason when the slot's safety checks failed it (:func:`reject_slot_answer`):
    such a slot is never salvaged, adopted or read back. ``checked`` says the
    slot's checks passed with nothing of an earlier answer left in place
    (:func:`run_slot`): only such an attempt supersedes the model's withheld
    answer (:func:`withheld_record`).

    :func:`run_slot` returns one, and so does review-code's slot wrapper in
    ``run_all_reviews``; the slot functions over :func:`run_slot` keep their
    own shapes for their callers (``run_single_model`` a record dict,
    ``run_single_review`` a ``(success, issues, error)`` triple), and
    :func:`slot_results` reads any of the three.
    """

    model_spec: str
    success: bool
    payload: Any = None
    error: Optional[str] = None
    source: Optional[str] = None
    details: Mapping[str, Any] = field(default_factory=dict)
    failure: Optional[str] = None
    rejected: Optional[str] = None
    checked: bool = False

    @classmethod
    def from_record(cls, model_spec: str, record: Mapping[str, Any]) -> "SlotResult":
        """review-plan's slot record (``run_single_model``'s return)."""
        return cls(
            model_spec=model_spec,
            success=bool(record.get("success")),
            payload=record.get("output"),
            error=record.get("error"),
            source=record.get("source"),
            details=record,
            failure=record.get(SALVAGE_FAILURE_KEY),
            rejected=record.get(REJECTED_KEY),
            checked=record.get(CHECKED_KEY) is True,
        )

    @classmethod
    def from_review(cls, model_spec: str, value: Any) -> "SlotResult":
        """review-code's slot triple (``run_single_review``'s return)."""
        success, issues, error = value
        return cls(model_spec=model_spec, success=bool(success), payload=issues,
                   error=error, rejected=getattr(value, "rejected", None),
                   checked=getattr(value, "checked", False) is True)

    @classmethod
    def coerce(cls, model_spec: str, value: Any) -> "SlotResult":
        """*value* as a :class:`SlotResult`, whichever lane's shape it has."""
        if isinstance(value, SlotResult):
            return value
        if isinstance(value, Mapping):
            return cls.from_record(model_spec, value)
        return cls.from_review(model_spec, value)

    def as_review(self) -> tuple:
        """The ``(success, issues, error)`` triple review-code's report reads;
        a :class:`SlotReview` for a rejected or a checked slot."""
        triple = (self.success, self.payload, self.error)
        if self.rejected is not None or self.checked:
            return SlotReview(triple, rejected=self.rejected, checked=self.checked)
        return triple

    def marked_checked(self) -> "SlotResult":
        """This outcome with ``checked`` set, on the record too (review-plan's
        slot function returns the record)."""
        return replace(self, checked=True, details={**self.details, CHECKED_KEY: True})


#: The key a review-plan record carries :attr:`SlotResult.rejected` under.
REJECTED_KEY = "rejected"

#: The key a review-plan record carries :attr:`SlotResult.checked` under.
CHECKED_KEY = "checks_passed"


class SlotReview(tuple):
    """review-code's ``(success, issues, error)`` triple, with the slot's
    ``rejected`` reason and ``checked`` flag.

    A plain triple to every caller that destructures or compares it;
    :meth:`SlotResult.from_review` reads both back, so the fan-out that
    receives the triple from ``run_all_reviews`` still knows whether the slot
    may be salvaged and whether it supersedes a withheld answer.
    """

    rejected: Optional[str]
    checked: bool

    def __new__(cls, triple: tuple, *, rejected: Optional[str] = None,
                checked: bool = False) -> "SlotReview":
        value = super().__new__(cls, triple)
        value.rejected = rejected
        value.checked = checked
        return value

    def __getnewargs_ex__(self) -> Tuple[tuple, Dict[str, Any]]:
        # copy and pickle rebuild it whole
        return (tuple(self),), {"rejected": self.rejected, "checked": self.checked}


def slot_results(results: Mapping[str, Any]) -> Dict[str, SlotResult]:
    """A fan-out's ``{model_spec: outcome}`` map, each outcome a :class:`SlotResult`."""
    return {spec: SlotResult.coerce(spec, value) for spec, value in results.items()}


# ---------------------------------------------------------------------------
# One slot: the guard, the ladder and the checks
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SlotSteps:
    """The names :func:`run_slot` calls, built like :class:`RoundSteps` from
    the calling lane's own module when the slot runs
    (``ReviewSlot.slot_steps``), so a test that patches one there reaches the
    core. ``slot_guard`` and ``refused`` are ``utils.slot_guard``'s
    ``SlotGuard`` and ``Refused``."""

    slot_guard: Callable[..., Any]
    refused: type
    slot_ladder: Callable[..., Any]
    phase_thread: Callable[..., Any]
    misnamed_result_baseline: Callable[..., Any]
    requested_result_baseline: Callable[..., Any]
    invoke_with_file_output: Callable[..., Any]
    dispatch_with_ladder: Callable[..., Any]
    sandbox_fallback_kwargs: Callable[..., Dict[str, Any]]
    retire_salvage_artifacts: Callable[..., Any]
    #: ``review_orchestrator_base.RETIRE_REJECTED``, the word a rejected
    #: slot's retired salvage pair is named with.
    retire_rejected: str


@dataclass(frozen=True)
class SlotDispatch:
    """What a slot's ladder sends, as the lane prepared it.

    ``output_dir`` is the folder the answer is written to, as the lane holds
    it; ``timeout`` the slot's whole budget, taken once as its deadline;
    ``start_line(attempt, attempt_timeout)`` the line each attempt prints;
    ``jail_summary_key`` the closing-summary key the jail's and the home
    check's lines are filed under, for the ladder and the checks alike.
    """

    prompt_template: str
    prompt_context: Mapping[str, Any]
    output_dir: Any
    invoke_phase: str
    log_file: Optional[str]
    timeout: float
    start_line: Callable[[int, int], str]
    jail_summary_key: Any


@dataclass(frozen=True)
class SingleShot:
    """A slot that makes its one dispatch without the ladder: the review
    base's stdout lane, which only a direct call without an output folder
    reaches. ``run(guard)`` dispatches under the guard :func:`run_slot`
    admitted the slot with, and runs that guard's checks itself."""

    run: Callable[[Any], Any]


class ReviewSlot(Protocol):
    """What one lane's model slot supplies to :func:`run_slot`.

    The review base's slot (``review_orchestrator_base.BaseSlot``) and
    review-code's (``code_review_orchestrator.CodeSlot``) each hold one
    slot's identity (``model_spec``; ``anchor``, the plan path every lookup
    is anchored on; ``guard_plan_path``, the plan path as the lane hands it to
    the guard; the provider, display name, project root, tracker and the
    fan-out's model list) and these hooks, where the lanes legitimately
    differ:

    * ``refused(reason)``: the guard refused the slot before anything ran.
    * ``prepare(sandbox)``: the lane's own preparation once the guard admitted
      the slot: a :class:`SlotDispatch` for the ladder, a :class:`SingleShot`,
      or a :class:`SlotResult` that ends the slot undispatched (review-code's
      ``[REVIEW_UNSUPPORTED]``).
    * ``before_dispatch(dispatch)``: once the slot's deadline is taken and
      before the result baselines: a :class:`SlotResult` ends the slot
      undispatched (review-code's argv cap), ``None`` dispatches.
    * ``ladder_refused(reason, duration)``: the budget refused the first
      attempt (§7.5 rule 4); the reason is printed already.
    * ``after_ladder(run)``: what the lane reads off the last attempt before
      the checks run (its provenance, the output-file line).
    * ``outcome(run, violation, duration)``: the slot's ending, with the
      reason it is failed before its answer is parsed: the checks', or
      :data:`UNSHOWN_ANSWER_REASON` for an answer :func:`run_slot` does not
      accept.
    * ``raised(exc)``: a :class:`SlotResult` for an exception raised between
      the deadline and the ending, or ``None`` to let it propagate to the
      fan-out's wrapper (``raised_slot_record``).
    * ``slot_steps()``: the :class:`SlotSteps` from the lane's module.
    """

    model_spec: str
    anchor: str
    guard_plan_path: Any
    provider_name: str
    display_name: str
    project_root: Optional[str]
    tracker: Any
    run_model_specs: Optional[Sequence[str]]

    def slot_steps(self) -> SlotSteps: ...

    def refused(self, reason: str) -> SlotResult: ...

    async def prepare(self, sandbox: Any) -> Any: ...

    def before_dispatch(self, dispatch: SlotDispatch) -> Optional[SlotResult]: ...

    def ladder_refused(self, reason: str, duration: float) -> SlotResult: ...

    def after_ladder(self, run: Any) -> None: ...

    def outcome(self, run: Any, violation: Optional[str], duration: float) -> SlotResult: ...

    def raised(self, exc: Exception) -> Optional[SlotResult]: ...


async def run_slot(slot: ReviewSlot, *, start_time: float) -> SlotResult:
    """One model slot of a review fan-out, the same on every lane.

    D6 step 3: the slot's guard asks the runner's sandbox whether it can start
    before anything is dispatched, and on a fallback rung takes the
    before-snapshots its checks need (``utils/slot_guard.py``). A refused slot
    ends there (``slot.refused``). Otherwise the lane prepares its dispatch;
    then §7.5 rule 1: ONE deadline for the slot (``slot_ladder``), taken
    before the lane's last check and the result baselines, which it pays for.
    The misnamed-result and requested-result baselines are the slot's, taken
    once and handed to every attempt: a file an attempt wrote before it was
    killed is still this slot's answer when a retry writes nothing, and one
    already there when the slot started is never read as this slot's (the
    misnamed one only with the fan-out's model list, which never looks
    otherwise). The ladder loop is ``dispatch_with_ladder``
    (docs/development/delegation.md#read-and-analyze-executor).

    The guard's checks run once, after the last attempt, over every attempt
    (ANDed: a clean retry cannot excuse an earlier attempt that wrote), and
    ahead of the lane's ending: a slot they fail is failed with their reason
    whatever its last attempt reported, nothing it returned is parsed as a
    review, and its answer is refused for good (:func:`reject_slot_answer`,
    with no await between the verdict and it, so the deadline cannot cancel
    the slot in between). *start_time* is the slot's start, for its duration.

    The answer is withheld until the checks pass (docs/development/
    review-results.md, "Withheld slot answers"): the model is recorded under
    ``models_unchecked`` before anything is dispatched, and taken out the
    moment the checks pass with nothing of an earlier answer left in place,
    which also marks the outcome ``checked``. A slot whose record cannot be
    written, or read back, is failed before its dispatch. A slot that ends in
    between (the fan-out's deadline, an interrupt, an exception) keeps the
    record and sets its file aside on the way out. A slot whose checks pass
    while the ``<stem>.json`` it started beside may still be in place (a
    set-aside that failed, a stamp that could not be read) keeps the record
    too, and an answer it read from that file is failed rather than accepted
    (:data:`UNSHOWN_ANSWER_REASON`): nothing shows it is not the earlier
    answer. An answer on stdout, or in a misnamed file adopted by name, is
    this slot's whatever the old file does.
    """

    steps = slot.slot_steps()
    guard = steps.slot_guard(
        provider_name=slot.provider_name, display_name=slot.display_name,
        model_spec=slot.model_spec, project_root=slot.project_root,
        plan_path=slot.guard_plan_path, tracker=slot.tracker,
    )
    gate = await guard.begin()
    if isinstance(gate, steps.refused):
        return slot.refused(gate.reason)
    sandbox = gate.sandbox

    prepared = await slot.prepare(sandbox)
    if isinstance(prepared, SlotResult):
        return prepared
    if isinstance(prepared, SingleShot):
        return await prepared.run(guard)
    dispatch: SlotDispatch = prepared
    result_path = generate_output_path(
        Path(dispatch.output_dir), "output", dispatch.invoke_phase, slot.model_spec,
    )

    try:
        ladder = steps.slot_ladder(slot.provider_name, dispatch.timeout, anchor=slot.anchor)
        ended = slot.before_dispatch(dispatch)
        if ended is not None:
            return ended

        misnamed_baseline = (
            await steps.phase_thread(
                steps.misnamed_result_baseline,
                dispatch.output_dir, dispatch.invoke_phase, slot.model_spec,
            )
            if slot.run_model_specs is not None else None
        )
        requested_baseline = await steps.phase_thread(
            steps.requested_result_baseline,
            dispatch.output_dir, dispatch.invoke_phase, slot.model_spec,
        )

        async def _dispatch(attempt_timeout: int) -> Dict[str, Any]:
            return await steps.phase_thread(
                steps.invoke_with_file_output,
                prompt_template=dispatch.prompt_template,
                model_spec=slot.model_spec,
                prompt_context=dispatch.prompt_context,
                output_dir=dispatch.output_dir,
                phase=dispatch.invoke_phase,
                timeout=attempt_timeout,
                log_file=dispatch.log_file,
                prefer_arrays=True,
                cwd=slot.project_root,
                anchor=slot.anchor,
                # Every model of the fan-out, so a result written under the
                # wrong name is read from where the model put it (live run 10).
                run_model_specs=slot.run_model_specs,
                misnamed_baseline=misnamed_baseline,
                requested_baseline=requested_baseline,
                **steps.sandbox_fallback_kwargs(sandbox),
            )

        armed = arm_slot(slot.model_spec, result_path)
        if armed is False:
            # Nothing would tell a later reader this answer was never checked.
            print(f"[{slot.display_name}] {UNRECORDED_REASON}")
            return slot.ladder_refused(UNRECORDED_REASON, time.time() - start_time)
        try:
            run = await steps.dispatch_with_ladder(
                _dispatch,
                ladder=ladder,
                model_spec=slot.model_spec,
                display_name=slot.display_name,
                timeout=dispatch.timeout,
                start_line=dispatch.start_line,
                jail_summary_key=dispatch.jail_summary_key,
                tracker=slot.tracker,
            )
            duration = time.time() - start_time
            if run.refused:
                # §7.5 rule 4: what is left of the slot cannot hold one worst-case
                # attempt of the adapter's declared envelope, so nothing was
                # spawned; recorded as its own outcome rather than dispatched to be
                # killed part-way through a retry chain the harness cannot see.
                reason = run.refusal_reason(slot.display_name)
                print(f"[{slot.display_name}] {reason}")
                return slot.ladder_refused(reason, duration)
            slot.after_ladder(run)
            violation = await guard.finish(
                run.audits, run.home_checks, summary_key=dispatch.jail_summary_key,
            )
        except asyncio.CancelledError:
            _withhold_unfinished_slot(slot.model_spec, result_path, CANCELLED_REASON)
            raise
        except Exception:
            _withhold_unfinished_slot(slot.model_spec, result_path, RAISED_REASON)
            raise
        # No await from here on: the verdict and its disposition are one step.
        file_left = violation is None and _earlier_file_left(
            steps, dispatch, slot.model_spec, requested_baseline,
        )
        # Read before the lane's ending, which may write this attempt's own
        # salvage request (review-code's does).
        checked = violation is None and not file_left and not _salvage_pair_left(result_path)
        if checked:
            clear_unchecked_slot(slot.model_spec, result_path)
        if file_left and _answer_read_from_result_file(run.result):
            # Nothing shows the answer is not the earlier one, which may be
            # withheld: failed before the lane parses it, and still withheld.
            print(f"[{slot.display_name}] {UNSHOWN_ANSWER_REASON}")
            return _unshown_answer(slot.outcome(run, UNSHOWN_ANSWER_REASON, duration))
        ending = slot.outcome(run, violation, duration)
        if violation is None:
            return ending.marked_checked() if checked else ending
        return reject_slot_answer(steps, ending, reason=violation, result_path=result_path)
    except Exception as exc:
        caught = slot.raised(exc)
        if caught is None:
            raise
        return caught


#: ``models_unchecked``'s reason for a slot recorded before its dispatch.
ARMED_REASON = "its slot was dispatched and its checks have not passed"

#: ... for one cancelled before its checks finished,
CANCELLED_REASON = "its slot was cancelled before its checks finished"

#: ... and for one an exception ended before its checks finished.
RAISED_REASON = "its slot raised an exception before its checks finished"

#: The error of a slot whose checks passed but whose answer was read from
#: its ``<stem>.json`` while the file the slot started beside may still be in
#: place (:func:`run_slot`): nothing shows the answer is this slot's.
UNSHOWN_ANSWER_REASON = (
    "[RESULT_NOT_SHOWN_NEW] answer not accepted: it was read from the model's "
    "result file, and nothing shows that file was written after this slot "
    "started (the earlier answer it started beside may still be there)"
)

#: The error of a slot failed before its dispatch because its
#: ``models_unchecked`` record could not be written or read back.
UNRECORDED_REASON = (
    "[WITHHOLD_NOT_RECORDED] not dispatched: .status.json could not record "
    "that this model's answer is withheld until its safety checks pass"
)


def arm_slot(
    model_spec: str, result_path: Path, *,
    phase_dir: Optional[str] = None, required: bool = False,
) -> Optional[bool]:
    """Record *model_spec* under ``models_unchecked`` before its dispatch.

    ``True`` when the record is there now (read back); ``False`` when the
    phase has a checkpoint and the record could not be written or read back,
    which fails the slot before its dispatch (:func:`run_slot`): nothing would
    tell a later ``--reaggregate`` or resume that an answer it left was never
    checked. ``None`` when the folder has no checkpoint at all: only a direct
    call of a slot function, which no round opened, gets there (a fan-out's
    :func:`open_round` writes it, and its round stamp is read back first), and
    such a call keeps no record. With *required* (a slot whose launch wrote
    the checkpoint) no checkpoint is ``False`` too.

    The record goes into *phase_dir*'s checkpoint, by default the folder of
    *result_path*, the file the slot asks for: the review lanes build that
    path inside the phase folder (``generate_output_path``) and never resolve
    it. Ask's slots arm through here too and name their question folder,
    because their ``answer_<model>.md`` is resolved through links, and a link
    must not take the record, or the no-checkpoint exemption, elsewhere
    (``ask_orchestrator._record_launch`` writes and reads back that folder's
    checkpoint)."""
    phase_dir = str(phase_dir if phase_dir is not None else result_path.parent)
    try:
        if _status_file.load_status(phase_dir) is None:
            return False if required else None
    except _status_file.CheckpointUnreadable:
        return False
    try:
        return _result_files.record_unchecked_model(phase_dir, model_spec, ARMED_REASON)
    except Exception:  # noqa: BLE001 - the slot is failed instead
        return False


def _earlier_file_left(
    steps: SlotSteps, dispatch: SlotDispatch, model_spec: str, baseline: Any,
) -> bool:
    """Whether the ``<stem>.json`` this slot started beside may still be in
    place: an earlier answer, one whose checks failed among them, whose
    set-aside failed. Such an attempt passes its checks but supersedes
    nothing (:func:`run_slot`), and an answer it read from that file is not
    accepted either.

    The two stamps (``requested_result_baseline``) show the file gone only
    when it was absent at the start, is absent now, or has changed since. A
    stamp that could not be read (``None``) shows nothing, so an earlier file
    counts as still there."""
    if baseline == ():
        return False
    now = steps.requested_result_baseline(
        dispatch.output_dir, dispatch.invoke_phase, model_spec,
    )
    if now == ():
        return False
    return baseline is None or now is None or now == baseline


def _salvage_pair_left(result_path: Path) -> bool:
    """Whether a salvage pair of the model is in place before the lane's
    ending writes this attempt's own: an earlier attempt's, whose retirement
    at the attempt's start failed. Such an attempt supersedes nothing."""
    stem = result_path.stem
    return any(
        os.path.lexists(result_path.parent / name)
        for name in (f"salvage_{stem}.json", f"salvage_task_{stem}.json")
    )


#: The ``source`` values of an answer ``invoke_with_file_output`` read from
#: the requested ``<stem>.json`` itself (a misnamed file it adopted carries
#: ``misnamed_from`` as well).
_RESULT_FILE_SOURCES = frozenset({"file", "file_extracted"})


def _answer_read_from_result_file(result: Optional[Mapping[str, Any]]) -> bool:
    """Whether the last attempt answered from the requested ``<stem>.json``,
    rather than on stdout or from a misnamed file it adopted by name, whose
    snapshot shows it written during the slot."""
    return bool(
        result
        and result.get("success")
        and result.get("source") in _RESULT_FILE_SOURCES
        and not result.get("misnamed_from")
    )


def _unshown_answer(ending: SlotResult) -> SlotResult:
    """The failed ending of a slot whose answer :func:`run_slot` did not
    accept, with ``salvage_text`` ``""`` on review-plan's record, as on a
    rejection's: the model stays withheld, so a salvage request of it could
    only be refused."""
    return replace(ending, details={**ending.details, SALVAGE_TEXT_KEY: ""})


def clear_unchecked_slot(
    model_spec: str, result_path: Path, *, phase_dir: Optional[str] = None,
) -> None:
    """Take a slot whose checks passed out of ``models_unchecked`` now, so a
    run that stops before its fan-out closes still reuses its answer;
    :func:`close_fanout` tries again for one this write misses. In the
    checkpoint :func:`arm_slot` recorded it in (*phase_dir*, by default the
    folder of *result_path*)."""
    folder = Path(phase_dir) if phase_dir is not None else result_path.parent
    try:
        cleared = _result_files.clear_unchecked_model(folder, model_spec)
    except Exception:  # noqa: BLE001 - warned below
        cleared = False
    if not cleared:
        print(
            f"Warning: {model_spec}: its safety checks passed, but "
            f"models_unchecked in {folder}/.status.json could not be "
            f"cleared yet; the fan-out's close tries again",
            file=sys.stderr,
        )


def _withhold_unfinished_slot(model_spec: str, result_path: Path, reason: str) -> None:
    """A dispatched slot that ended before its verdict (cancelled, or an
    exception): its answer was never checked. Recorded with *reason* (the
    record :func:`arm_slot` wrote stays when this write fails), and its file
    set aside as ``.json.unchecked``. Synchronous, so nothing cancels it
    part-way; the fan-out's close stops a cancelled slot's provider thread and
    sets aside what it wrote later. Never raises: the slot's own ending
    follows."""
    try:
        _result_files.record_unchecked_model(result_path.parent, model_spec, reason)
    except Exception:  # noqa: BLE001 - the armed record stays
        pass
    try:
        _result_files.set_aside_unchecked_result(
            result_path,
            reason=_result_files.Withheld(
                _result_files.UNCHECKED_MODELS_KEY, reason,
            ).note(model_spec),
        )
    except Exception:  # noqa: BLE001 - the record keeps it out; the close looks again
        pass


def reject_slot_answer(
    steps: SlotSteps,
    ending: SlotResult,
    *,
    reason: str,
    result_path: Path,
) -> SlotResult:
    """A slot the guard's checks failed: its answer refused for good, on every lane.

    The one disposition of every rejection site (:func:`run_slot` for both
    lanes' ladder, the review base's stdout lane twice). Only a reason the
    guard's checks returned counts: a ``[SANDBOX_BYPASSED]`` fallback notice,
    or a change the slot's own audited stream cleared, fails nothing and never
    reaches here. In order:

    1. the rejection is recorded in ``.status.json`` (``models_rejected``,
       :func:`~utils.result_files.record_rejected_model`) first, so whatever
       fails below, ``--reaggregate`` and a resume's skip still refuse the
       model's file;
    2. the model's outstanding salvage pair is retired (``.rejected.`` in its
       new name), and
    3. the ``<stem>.json`` the slot asked for, or a model wrote there, is set
       aside as ``.json.rejected``, outside every result glob.

    Returned as *ending* marked ``rejected``, with ``salvage_text`` set to
    ``""`` on its record: that, not a cleared ``stdout``, is what stops
    ``failure_output_from_result`` falling back to stdout or stderr, so no
    reader of the record can ask for a salvage of it. ``stdout`` stays, for the
    error log; the provenance and spend on the record stay too.

    Fail closed: when the rename or the retirement fails the model stays
    failed anyway (the fan-out never salvages or adopts a rejected slot, and
    the record refuses the file later); a warning names what is left. When
    this record cannot be written either, the one :func:`run_slot` wrote
    before the dispatch (``models_unchecked``) still withholds the files; with
    neither, :func:`close_fanout` stops the phase before anything reads them.
    No step raises: an exception here would reach ``run_slot``'s handler and
    end the slot as a plain exception, without its rejection.
    """
    model_spec = ending.model_spec
    phase_dir = result_path.parent
    stem = result_path.stem
    recorded = False
    try:
        recorded = _result_files.record_rejected_model(phase_dir, model_spec, reason)
    except Exception:  # noqa: BLE001 - another record, or the warning below
        pass
    try:
        steps.retire_salvage_artifacts(str(phase_dir), stem, reason=steps.retire_rejected)
    except Exception:  # noqa: BLE001 - what is left is named below
        pass
    try:
        _result_files.set_aside_rejected_result(
            result_path, reason=_result_files.rejected_result_note(model_spec, reason),
        )
    except Exception:  # noqa: BLE001 - what is left is named below
        pass
    left = [
        name for name in (result_path.name, f"salvage_{stem}.json", f"salvage_task_{stem}.json")
        if os.path.lexists(phase_dir / name)
    ]
    if left:
        if not recorded:
            try:
                recorded = _result_files.withheld_models(phase_dir).recorded(model_spec)
            except Exception:  # noqa: BLE001 - nothing durable, said below
                recorded = False
        kept_out = (
            ".status.json keeps them out of --reaggregate and a resume" if recorded else
            "nothing durable records the rejection either, so the phase stops "
            "before grouping"
        )
        print(
            f"Warning: {model_spec} failed its safety checks, and "
            f"{', '.join(left)} could not be set aside in {phase_dir}; the model "
            f"stays failed, and {kept_out}",
            file=sys.stderr,
        )
    details = {**ending.details, REJECTED_KEY: reason, SALVAGE_TEXT_KEY: ""}
    return replace(
        ending, success=False, payload=None, error=ending.error or reason,
        details=details, failure=None, rejected=reason,
    )


# ---------------------------------------------------------------------------
# Closing a fan-out
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FanoutSteps:
    """The review base's steps :func:`close_fanout` calls, built like
    :class:`RoundSteps` from the calling lane's own module
    (``ReviewLane.fanout_steps``)."""

    backfill_deadline_losses: Callable[..., None]
    record_sandbox_bypassed: Callable[..., Any]
    announce_retired_rungs: Callable[..., Any]
    exec_subagents_requested: Callable[..., bool]
    dispatch_in_round: Callable[..., Any]
    dispatch_salvage_tasks: Callable[..., Any]
    record_models_salvaged: Callable[..., Any]
    sanitize_model_name: Callable[[str], str]
    print_closing_summary: Callable[..., None]


@dataclass(frozen=True)
class FanoutOutcome:
    """What :func:`close_fanout` leaves for grouping.

    ``slots``: every slot that returned, as saved (a slot whose result could
    not be saved is a failure here) and with salvaged models replaced by the
    slot salvage made them. ``failed_models``: ``{model_spec: reason}``, the
    deadline losses included. ``salvaged``: the models this run's in-process
    salvage recovered. ``recovered``: the phase's checkpoint carries
    ``result_files.RECOVERED_KEY``. Grouping reads the answers the lane holds
    (*slots*, the base lane's ``saved``), never the files the close saved
    (docs/development/review-results.md, "Consuming checked bytes").
    """

    slots: Dict[str, SlotResult]
    failed_models: Dict[str, str]
    completed_models: List[str]
    salvaged: List[str]
    recovered: bool = False


async def close_fanout(
    lane: ReviewLane,
    claim: _review_round.Claim,
    args: Any,
    *,
    model_specs: Sequence[str],
    results: Mapping[str, Any],
    served_models: Dict[str, Dict[str, Any]],
    usage: Dict[str, Dict[str, Any]],
    prior_served: Mapping[str, Any],
    tracker: Any,
    unattended: bool,
) -> FanoutOutcome:
    """Everything between a fan-out's return and grouping, the same on every lane.

    In order: each slot's result is saved (``lane.save_slot``); a model the
    deadline lost gets its failure (``backfill_deadline_losses``, the map
    too); the round is checked, since everything after this belongs to it;
    the slots that ran unsandboxed are mirrored for the poller before any
    ending below, the all-failed exit included; under ``--exec-subagents`` the
    salvage tasks run in this process and each model whose repaired file the
    dispatch names is adopted (``lane.adopt_salvaged``). A run where no model
    answered records ``models_failed`` and ``models_served`` and exits 3
    naming the ``--force`` retry; otherwise the partial results are reported
    and ``models_complete`` is recorded with the served models and usage.

    Before the salvage, what a slot left unchecked or rejected is withheld
    (docs/development/review-results.md, "Withheld slot answers"): the
    deadline's losses have their provider threads stopped and joined and
    their files set aside (:func:`_withhold_lost_slots`), both withheld maps
    are written (:func:`withheld_record`), and a model whose refused files are
    still readable while nothing durable withholds them stops the phase
    (:func:`_stop_unless_withheld`). In a recovered phase
    (``result_files.RECOVERED_KEY``) no salvage runs: a failed model stays
    failed, and the run completes partial with a warning.

    *served_models* and *usage* are the slots' provenance (``models_served``,
    ``usage``), recorded as given; *prior_served* is what the previous run
    recorded, for the retired-rung notice.
    """
    phase_dir = str(lane.phase_dir)
    steps = lane.fanout_steps()
    slots = slot_results(results)

    failed_models: Dict[str, str] = {}
    for model_spec, slot in list(slots.items()):
        # `payload` is the answer of a run that completed and is `None` on
        # every losing path; the text a losing run left behind stays in
        # `details`, and only salvage may read it (`save_model_result`).
        if not lane.save_slot(slot):
            failed_models[model_spec] = slot.error or "Unknown error"
            # Grouping reads these slots, so one whose result could not be
            # saved is a failure there too.
            slots[model_spec] = replace(
                slot, success=False, payload=None, error=failed_models[model_spec],
            )

    # F11: a model the deadline cancelled has no result and, so far, no failure
    # entry either; one pass writes both, under `DEADLINE_ERROR`.
    steps.backfill_deadline_losses(
        list(model_specs), results, failed_models, tracker=tracker,
    )

    # The model results are saved (a later `--force` reuses them); everything
    # after this belongs to the round, so a run whose round another run
    # replaced while its models ran stops here (utils/review_round.py).
    claim.check("record its models and group their results")

    # The slots that ran without a sandbox, mirrored for the poller before any
    # ending below: every slot failing does not make them sandboxed.
    # `models_served` is the durable copy.
    steps.record_sandbox_bypassed(phase_dir, served_models)
    steps.announce_retired_rungs(prior_served, served_models, anchor=str(lane.plan_path))

    # What a later `--reaggregate`, resume or salvage refuses, written before
    # this run's salvage reads it: the deadline's losses withheld first.
    lost = [spec for spec in model_specs if spec not in slots]
    settled = _withhold_lost_slots(phase_dir, steps, lost)
    # `None`: the checkpoint cannot be read, so the maps on it stay as they are.
    withheld = withheld_record(phase_dir, slots) or {}
    if withheld:
        _status_file.update_status(phase_dir, withheld)
    _stop_unless_withheld(
        phase_dir, steps, slots, lost, settled=settled, failed_models=failed_models,
        served_models=served_models, withheld=withheld,
    )

    salvaged: List[str] = []
    recovered = _result_files.RECOVERED_KEY in withheld
    if failed_models and recovered:
        # A repair is a file on disk, which a recovered phase never trusts
        # (docs/development/review-results.md, "Recovering a damaged one").
        print(
            f"WARNING: no salvage runs in {phase_dir}: its damaged checkpoint was "
            f"replaced, so no file there is trusted; "
            f"{', '.join(failed_models)} stay failed. Move the whole phase folder "
            f"aside to start clean.",
            file=sys.stderr,
        )
    elif failed_models and steps.exec_subagents_requested(args):
        salvaged = await _salvage_in_process(
            lane, claim, args, steps, slots=slots, failed_models=failed_models,
        )

    # D6 row 3: partial results are usable output (exit 0, `state: "partial"`);
    # a run where no model produced a result has nothing to aggregate and is
    # exit 3 naming the retry command, before anything records the phase.
    completed_models = [m for m in model_specs if m not in failed_models]
    if not completed_models:
        # The failure map, so a later `--reaggregate` names each loss and exits
        # 3 too, and `models_served`: a slot that ran without a sandbox did so
        # whether or not it then failed.
        _status_file.update_status(phase_dir, {
            "models_completed": [],
            "models_failed": failed_models,
            **withheld,
            **({"models_served": served_models} if served_models else {}),
        })
        print("\nERROR: All models failed")
        for model_spec, reason in failed_models.items():
            print(f"  - {model_spec}: {reason}")
        # The home check's and the jail's lines, repeated: this exit is the
        # run's last word.
        steps.print_closing_summary(phase_dir)
        sys.exit(_unattended.report_partial_results(
            completed=completed_models,
            failed=list(failed_models),
            phase_dir=phase_dir,
            retry_command=lane.retry_command("--force"),
        ))
    _unattended.report_partial_results(
        completed=completed_models,
        failed=list(failed_models),
        phase_dir=phase_dir,
        unattended=unattended,
    )

    _status_file.update_status(phase_dir, {
        "state": "models_complete",
        "models_completed": completed_models,
        "models_failed": failed_models,
        **withheld,
        # Added only when something was attributed or reported: no key means
        # nothing was, never that the run was free.
        **({"models_served": served_models} if served_models else {}),
        **({"usage": usage} if usage else {}),
    })
    # Both counters, on the post-salvage truth: `models_done` counts finished
    # slots (every one by now), `models_succeeded` the ones with a result. No
    # `models` key, so the map the fan-out's sweep froze stays as it is.
    _run_record.report_progress(
        phase_dir, step="grouping",
        models_total=len(model_specs),
        models_done=len(model_specs),
        models_succeeded=len(model_specs) - len(failed_models),
    )
    return FanoutOutcome(
        slots=slots, failed_models=failed_models,
        completed_models=completed_models, salvaged=salvaged, recovered=recovered,
    )


def withheld_record(
    phase_dir: str, slots: Mapping[str, SlotResult],
) -> Optional[Dict[str, Dict[str, Any]]]:
    """The ``models_rejected`` and ``models_unchecked`` maps a fan-out leaves,
    and in a recovered phase its ``result_files.RECOVERED_KEY`` record, carried
    as read but for the operator's acceptance of each model a checked attempt
    superseded: that attempt's own answer, or none, is the model's now.

    Every recorded entry stays until a checked attempt of its model supersedes
    it: a slot this run whose checks passed with nothing of an earlier answer
    left in place (:attr:`SlotResult.checked`), succeeded or not, since what
    it leaves (its answer, its salvage request) is its own, checked. A refused
    or budget-refused slot, one the preparation ended, one that raised or was
    cancelled, and a model this run did not select supersede nothing. This
    run's rejections are added, and a rejected slot's own ``models_unchecked``
    entry gives way to its rejection in the same write. ``None`` when the
    checkpoint cannot be read: maps rebuilt without the recorded entries would
    drop them, so the caller writes none.
    """
    try:
        recorded_rejected = _result_files.rejected_models(phase_dir)
        recorded_unchecked = _result_files.unchecked_models(phase_dir)
        recovery = _result_files.recorded_recovery(phase_dir)
    except _status_file.CheckpointUnreadable:
        return None
    superseded = {
        spec for spec, slot in slots.items() if slot.checked and slot.rejected is None
    }
    rejected_now = {
        spec: slot.rejected for spec, slot in slots.items() if slot.rejected is not None
    }
    rejected = {
        spec: reason for spec, reason in recorded_rejected.items() if spec not in superseded
    }
    rejected.update(rejected_now)
    unchecked = {
        spec: reason
        for spec, reason in recorded_unchecked.items()
        if spec not in superseded and spec not in rejected_now
    }
    record: Dict[str, Dict[str, Any]] = {
        _result_files.REJECTED_MODELS_KEY: rejected,
        _result_files.UNCHECKED_MODELS_KEY: unchecked,
    }
    if recovery is not None:
        accepted = recovery[_result_files.ACCEPTED_FIELD]
        record[_result_files.RECOVERED_KEY] = {
            **recovery,
            _result_files.ACCEPTED_FIELD: [
                spec for spec in accepted if spec not in superseded  # type: ignore[union-attr]
            ],
        }
    return record


def _withhold_lost_slots(phase_dir: str, steps: FanoutSteps, lost: Sequence[str]) -> bool:
    """The deadline's losses: no slot result, and checks that never finished.

    Their provider threads are stopped and joined first
    (``detach.stop_phase_work``, on this thread: the join waits for every
    phase thread, so it cannot be one). Then every lost model is withheld as
    unchecked, whether or not its ``<stem>.json`` exists yet (the record its
    slot wrote before dispatching it, or one written now), and a file that is
    there is set aside. A model the deadline lost before dispatching it has
    nothing of this round in that file either, so it is withheld the same way.

    Whether the join finished: when it did not, a provider may still write a
    lost model's file after this, and only the record refuses it
    (:func:`_stop_unless_withheld` stops the phase when there is none).
    """
    if not lost:
        return True
    settled = _detach.stop_phase_work("DEADLINE_SWEEP")
    if not settled:
        print(
            "Warning: a provider call the fan-out's deadline cancelled is still "
            "running; what it writes later is withheld by models_unchecked",
            file=sys.stderr,
        )
    for spec in lost:
        withheld = _result_files.withheld_models(phase_dir)
        disposition = withheld.get(spec) if withheld.recorded(spec) else None
        if disposition is None:
            disposition = _result_files.Withheld(
                _result_files.UNCHECKED_MODELS_KEY, DEADLINE_ERROR,
            )
            _result_files.record_unchecked_model(phase_dir, spec, DEADLINE_ERROR)
        path = Path(phase_dir) / f"{steps.sanitize_model_name(spec)}.json"
        if os.path.lexists(path):
            disposition.set_aside(path, spec)
    return settled


def _stop_unless_withheld(
    phase_dir: str,
    steps: FanoutSteps,
    slots: Mapping[str, SlotResult],
    lost: Sequence[str],
    *,
    settled: bool,
    failed_models: Dict[str, str],
    served_models: Mapping[str, Any],
    withheld: Mapping[str, Any],
) -> None:
    """The last resort, for a record that vanished after :func:`run_slot`
    wrote and read it back before the dispatch: stop the phase when an answer
    this run refused (a rejected slot) or never checked (a deadline loss) may
    still be read and ``.status.json`` records neither verdict, even after one
    more try to record it here.

    "May still be read": one of its files is still in place, or, for a
    deadline loss whose provider thread the join did not stop (*settled*
    false), it may write one later. Exit 3, ``needs-human``, before any
    salvage or grouping, naming the files to move; the slot stays failed."""
    durable = _result_files.withheld_models(phase_dir)
    left: Dict[str, List[str]] = {}
    for spec in [s for s, slot in slots.items() if slot.rejected is not None] + list(lost):
        if durable.recorded(spec):
            continue
        rejected = slots[spec].rejected if spec in slots else None
        try:
            if rejected is not None:
                again = _result_files.record_rejected_model(phase_dir, spec, rejected)
            else:
                again = _result_files.record_unchecked_model(phase_dir, spec, DEADLINE_ERROR)
        except Exception:  # noqa: BLE001 - stopped below
            again = False
        if again:
            continue
        stem = steps.sanitize_model_name(spec)
        names = [f"{stem}.json"]
        if spec in slots:
            names += [f"salvage_{stem}.json", f"salvage_task_{stem}.json"]
        found = [name for name in names if os.path.lexists(Path(phase_dir) / name)]
        if spec not in slots and not settled and not found:
            found = [f"{stem}.json (its provider may still write it)"]
        if found:
            left[spec] = found
    if not left:
        return
    _status_file.update_status(phase_dir, {
        "models_failed": failed_models,
        **withheld,
        **({"models_served": served_models} if served_models else {}),
    })
    lines = "\n".join(f"  - {spec}: {', '.join(names)}" for spec, names in left.items())
    advice = (
        f"{_status_file.status_path(phase_dir)} cannot be read. "
        f"{_status_file.unreadable_checkpoint_advice(phase_dir)}"
        if durable.unreadable else
        "Move these files out of the folder before any --reaggregate or resume "
        "reads them."
    )
    message = (
        f"ERROR: answers this run refused, or never finished checking, may still "
        f"be read in {phase_dir}, and .status.json could not record that they "
        f"are withheld:\n{lines}\n"
        f"The phase stops before grouping. {advice}"
    )
    steps.print_closing_summary(phase_dir)
    sys.exit(_unattended.fail_closed(message))


async def _salvage_in_process(
    lane: ReviewLane,
    claim: _review_round.Claim,
    args: Any,
    steps: FanoutSteps,
    *,
    slots: Dict[str, SlotResult],
    failed_models: Dict[str, str],
) -> List[str]:
    """D3b: run the salvage tasks here and adopt what they repaired.

    The step is published before the dispatch and a phase ticker narrates it,
    off the loop (``dispatch_in_round``), as the validation window does. Only a
    file this dispatch names as repaired is a recovery: a previous round's
    ``{model}.json`` still beside a failed slot under ``--rerun-all`` is never
    adopted, and neither is anything of a model the phase withholds (its
    durable record, or this run's rejection: :func:`reject_slot_answer`),
    whatever a leftover salvage task repaired; the dispatch skips their tasks.
    The per-model map moves with ``failed_models``
    (``record_models_salvaged``), since terminal transitions are idempotent.
    """
    phase_dir = str(lane.phase_dir)
    _run_record.report_progress(phase_dir, step="salvage")
    salvage_ticker = PhaseProgress(phase_dir, anchor=str(lane.plan_path))
    salvage_ticker.start_ticker()
    try:
        repaired = await steps.dispatch_in_round(
            claim, steps.dispatch_salvage_tasks,
            args,
            phase_dir=phase_dir,
            phase=lane.phase_name,
            plan_path=str(lane.plan_path),
        )
    finally:
        await salvage_ticker.stop_ticker()
    repaired_paths = {os.path.abspath(path) for path in repaired or ()}
    salvaged: List[str] = []
    for model_spec in list(failed_models):
        recovered = Path(phase_dir) / f"{steps.sanitize_model_name(model_spec)}.json"
        if os.path.abspath(str(recovered)) not in repaired_paths:
            continue
        withheld = _result_files.withheld_models(phase_dir).get(model_spec)
        rejected = slots[model_spec].rejected if model_spec in slots else None
        if withheld is None and rejected is not None:
            withheld = _result_files.Withheld(_result_files.REJECTED_MODELS_KEY, rejected)
        if withheld is not None:
            withheld.set_aside(recovered, model_spec)
            continue
        # The repair as the dispatch persisted it after its checks, never the
        # file read again (docs/development/review-results.md, "Consuming
        # checked bytes"); a dispatch that reported none leaves the lane to
        # read the file once.
        persisted = claim.checked_result(recovered.name)
        adopted = lane.adopt_salvaged(
            model_spec, recovered,
            **({"data": persisted} if persisted is not None else {}),
        )
        if adopted is None:
            continue
        print(f"[{model_spec}] recovered by salvage: {recovered}")
        slots[model_spec] = adopted
        del failed_models[model_spec]
        salvaged.append(model_spec)
    if salvaged:
        steps.record_models_salvaged(phase_dir, salvaged)
    return salvaged


# ---------------------------------------------------------------------------
# The validation round of a reaggregate
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RoundSteps:
    """The review base's steps the shared stages of a round call: its opening
    (:func:`open_round`), the fan-out's grouping and round
    (:func:`group_findings`, :func:`materialize_fanout_round`), a reaggregate's
    loading, grouping and round (:func:`load_reaggregate_results`,
    :func:`bind_grouping`, :func:`resolve_validation_round`), the report's
    hand-back (:func:`hand_back_report`) and the completion
    (:func:`record_phase_complete`).

    Each lane builds this from the names its own module binds when it calls
    (``ReviewLane.round_steps``), so a test that patches one of them on that
    module reaches this function too, and this module never imports the
    review base.
    """

    # Grouping and the validation round.
    group_similar_suggestions: Callable[..., Any]
    stamp_stable_ids: Callable[..., Any]
    grouped_coverage_gap: Callable[..., List[str]]
    verify_round_context: Callable[..., None]
    bind_plan_for_validation: Callable[..., BoundDocument]
    reopen_phase_for_validation: Callable[..., None]
    retire_stale_validation: Callable[..., Any]
    retire_stale_validation_round: Callable[..., Any]
    retire_validation_for_regroup: Callable[..., Any]
    materialize_validation_round: Callable[..., Dict[str, Any]]
    dispatch_in_round: Callable[..., Any]
    dispatch_subagent_tasks: Callable[..., Any]
    merge_validation_batches: Callable[..., List[Dict[str, Any]]]
    # The checkpoint and the result line.
    write_status: Callable[..., Any]
    update_status: Callable[..., Any]
    report_progress: Callable[..., Any]
    record_next: Callable[..., Any]
    recorded_usage: Callable[..., Any]
    recorded_served_models: Callable[..., Any]
    # A reaggregate's loading half.
    build_unsanitize_map: Callable[..., Dict[str, str]]
    resolve_result_files_by_model: Callable[..., Any]
    record_models_present: Callable[..., List[str]]
    remaining_failed_models: Callable[..., Any]
    announce_remaining_failures: Callable[..., Any]
    exit_when_every_reviewer_failed: Callable[..., Any]
    record_validation_counts: Callable[..., Any]
    # The report's hand-back (:func:`hand_back_report`).
    record_output_files: Callable[..., Any]
    record_review_artifacts: Callable[..., Any]


@dataclass(frozen=True)
class BoundGrouping:
    """What :func:`bind_grouping` left: the groups, whether they are the bound
    ``grouped.json``'s, and what the lane's *annotate* returned for them."""

    groups: List[Dict[str, Any]]
    reused: bool
    annotation: Any = None


def bind_grouping(
    claim: _review_round.Claim,
    steps: RoundSteps,
    *,
    phase_dir: str,
    grouped_path: str,
    validation_path: str,
    records: List[Dict[str, Any]],
    records_by_model: Mapping[str, List[Dict[str, Any]]],
    skip_validation: bool,
    noun: str,
    annotate: Optional[Callable[[List[Dict[str, Any]]], Any]] = None,
) -> BoundGrouping:
    """The grouping a ``--reaggregate`` reports, the same way on every lane.

    A ``grouped.json`` that validation artifacts are bound to is reused, not
    rewritten ("preserves validation alignment"): the task file hashes its
    bytes, so a regroup would make the reaggregate refuse its own round. Bound
    means a ``validation_tasks.json`` beside it (whatever the flags: its
    binding outlives this invocation), or a ``validation.json`` this run will
    use (not under ``--skip-validation``). Zero findings bind nothing.

    Reuse presumes the file still covers the results on disk; a result that
    landed after grouping (a salvage, an out-of-band result) breaks that, so the
    round is retired (renamed) and the results regrouped
    (``grouped_coverage_gap``). A regroup retires the verdicts on disk in the
    same step as the new ``grouped.json``.

    *annotate* is the lane's own pass over the groups (review-code's commit
    attribution): on a reused grouping in memory only, on a regroup before the
    file is written, so the file carries it. *noun* names the findings in the
    printed line.
    """
    validation_tasks_path = os.path.join(phase_dir, "validation_tasks.json")
    has_existing_validation = (
        (os.path.exists(validation_path) and not skip_validation)
        or os.path.exists(validation_tasks_path)
    )
    reuse = bool(records) and has_existing_validation and os.path.exists(grouped_path)
    if reuse:
        # Read once: the digest the verdicts are checked against is this
        # text's, never a second read's (Claim.hold_grouping).
        with open(grouped_path, 'r', encoding='utf-8') as handle:
            grouped_text = handle.read()
        grouped = load_groups_payload(json.loads(grouped_text))
        gap = steps.grouped_coverage_gap(grouped, dict(records_by_model))
        if gap:
            print(
                "grouped.json does not cover the model results on disk; "
                "regrouping and retiring the validation round bound to it:"
            )
            for line in gap:
                print(f"  {line}")
            steps.retire_stale_validation_round(
                phase_dir, reason="grouped.json did not cover the results on disk",
            )
            reuse = False

    if reuse:
        print("Using existing grouped.json (preserves validation alignment)")
        claim.hold_grouping(grouped_text)
        return BoundGrouping(
            groups=grouped, reused=True,
            annotation=annotate(grouped) if annotate is not None else None,
        )

    # Plain dicts on both branches (`load_groups_payload` yields them); the
    # stamped ids read `theme` and each record's `type`/`section`/`details`,
    # never the stamped keys, so the conversion moves no group id.
    raw_grouped = steps.group_similar_suggestions(records)
    grouped = [g.to_dict() if hasattr(g, 'to_dict') else g for g in raw_grouped]
    steps.stamp_stable_ids(grouped)
    annotation = annotate(grouped) if annotate is not None else None
    # D7: a re-group orphans any verdicts on disk, so they leave with it, in the
    # same step as the new grouped.json (replaced whole).
    with claim.held("retire the previous validation and regroup"):
        steps.retire_stale_validation(
            phase_dir, reason="grouped.json rewritten by reaggregate",
        )
        _hold_grouping(claim, _review_round.replace_file(
            grouped_path, json.dumps(save_groups_payload(grouped), indent=2)))
    print(f"Grouped {noun} saved to: {grouped_path}")
    return BoundGrouping(groups=grouped, reused=False, annotation=annotation)


def _on_held_grouping(claim: _review_round.Claim, round_: Any) -> Any:
    """*round_* bound to the ``grouped.json`` text *claim* holds
    (``ValidationRound.grouped_text``), so its task file records the digest
    of the grouping its prompts were built from, never of the file read
    again; as it is when the claim holds none."""
    text = claim.grouping_text
    if text is None or not isinstance(round_, ValidationRound):
        return round_
    return replace(round_, grouped_text=text)


def _hold_grouping(claim: _review_round.Claim, written: Any) -> None:
    """The ``grouped.json`` bytes just written, held on *claim* as a text-mode
    read of them returns them (``Claim.hold_grouping``), for the round's task
    file and verdicts to bind (docs/development/review-results.md, "Consuming
    checked bytes")."""
    if isinstance(written, bytes):
        claim.hold_grouping(read_back_text(written))


@dataclass(frozen=True)
class RoundOutcome:
    """What :func:`resolve_validation_round` left for the report.

    ``groups``: the groups with their verdicts (``[]`` for zero groups), or
    ``None`` when validation was skipped. A recovered fan-out that runs no
    validation (:func:`materialize_fanout_round`) gives the grouping it holds,
    without verdicts (``verdicts`` ``None``): the report and the HIGH-group
    count read them, never ``grouped.json``. ``verdicts``: the
    ``validation.json`` bytes they came from (``Claim.verdicts``).
    ``handed_off``: the round is with the host, or waits for missing batches;
    the caller ends here with the phase open.
    """

    groups: Optional[List[Dict[str, Any]]] = None
    verdicts: Optional[_review_round.Verdicts] = None
    handed_off: bool = False


async def resolve_validation_round(
    claim: _review_round.Claim,
    args: Any,
    steps: RoundSteps,
    *,
    phase_name: str,
    phase_dir: str,
    plan_path: str,
    grouped: List[Dict[str, Any]],
    grouped_path: str,
    validation_path: str,
    current_inputs: Callable[[], Dict[str, Any]],
    reuse_checks_inputs: bool,
    build_round: Callable[[BoundDocument], ValidationRound],
    scope_round_policy: Any,
    scope_baseline: Optional[Mapping[str, Any]],
    findings: str,
    follow_up: Optional[Callable[[Mapping[str, Any]], Optional[str]]] = None,
) -> RoundOutcome:
    """Resolve a ``--reaggregate``'s validation round, the same way on every lane.

    * A round built from truncated context (contract 1) is retired whole first.
    * A ``validation.json`` bound to the grouping beside it (and to the batch
      bytes it merged, ``validation_source_decision``) is reused: its
      snapshots are re-verified and its verdicts applied, nothing is merged
      again. One that does not bind is retired (renamed) and the batch files
      decide. On a lane whose reuse checks its inputs
      (*reuse_checks_inputs*, ``ReviewLane.reuse_checks_inputs``), the task
      file is first read against ``current_inputs()`` as a resume reads it
      (exit 3 when one moved), and verdicts no task file binds to every one of
      those inputs are not reused: the round goes on below as if there were
      no ``validation.json``.
    * Zero groups: the previous round is retired and ``validation.json`` is
      ``[]``.
    * ``--skip-validation``: nothing is read or written.
    * A ``validation_tasks.json`` on disk: refused (exit 3) when its inputs
      (``current_inputs()``) or snapshots moved; stale prompt sidecars are
      rebound and persisted; a whole round of batch files is merged; otherwise
      the missing batches are dispatched under ``--exec-subagents`` or the
      phase is reopened and left to the host.
    * No task file: a new round is built (``build_round``), stamped and
      published, the phase reopened, then dispatched or handed to the host.

    The merge reads a missing batch as ``validation_failed``, so it is only
    ever handed a whole round. No broad ``except`` surrounds the merge or the
    dispatch: one that raises ends the command with the phase open
    (docs/development/review-results.md, "The shared review lane").

    *findings* names what the review returned ("suggestions", "issues") in the
    zero-group retirement's reason. *scope_round_policy* and *scope_baseline*
    are the round on record's scope policy and baseline, from which reused
    verdicts get their validation-stage decision again. *follow_up* is the
    lane's ``--reaggregate`` command for a task document, in the spelling the
    user typed (``ReviewLane.round_follow_up(..., typed=True)``, the command
    the fan-out's hand-off names); every hand-off here prints it and puts it on
    the result line. ``None`` rebuilds it from the document
    (``resolved_reaggregate_command``).
    """
    validation_tasks_path = os.path.join(phase_dir, "validation_tasks.json")

    # Task 2.10: a round materialized under context contract 1 from an
    # over-limit document judged its head alone. Neither its prompts nor the
    # verdicts reached from them are reused: the whole round is retired
    # (renamed, kept for history) and rematerialized below in the path form.
    legacy_round = (
        None if args.skip_validation else legacy_context_round_reason(phase_dir)
    )
    if legacy_round:
        print(f"\n{legacy_round}")
        steps.retire_stale_validation_round(
            phase_dir, reason="validation built from truncated context (contract 1)",
        )

    # D7: a validation.json is honoured only when it binds to the grouped.json
    # beside it (or, for a legacy file without the binding, when no batch file
    # postdates it); otherwise it is retired (renamed, not deleted) and the
    # batch files decide.
    honour_validation_file = (
        os.path.exists(validation_path) and not args.skip_validation
    )
    use_note = ""
    validation_bytes = b""
    round_document = _RoundDocument(present=False)
    if honour_validation_file:
        # §7.1: bound to the exact batch bytes it merged (`batch_sha256` +
        # `batch_manifest`), so a rewritten, restored or missing batch retires
        # it by content; only a file without the binding falls back to the
        # legacy mtime test. Both outcomes name what was checked. Read once
        # each: the validation.json bytes judged here, the task file its round
        # is judged against, and the grouping this run holds
        # (`Claim.grouping_text`) are the ones the reuse below checks and the
        # report is built from. A validation.json that cannot be read now has
        # had nothing checked, so it is retired as the decision retires one it
        # cannot read (docs/development/review-results.md, "Consuming checked
        # bytes").
        try:
            validation_bytes = Path(validation_path).read_bytes()
        except OSError as exc:
            stale_reason = f"could not read {Path(validation_path).name}: {exc}"
        else:
            round_document = _read_round_document(validation_tasks_path)
            stale_reason, use_note = validation_source_decision(
                Path(validation_path), Path(grouped_path), Path(validation_tasks_path),
                validation_bytes=validation_bytes, grouped_text=claim.grouping_text,
                task_document=round_document.document,
            )
        if stale_reason:
            print(f"\nNot using validation.json: {stale_reason}")
            steps.retire_stale_validation(phase_dir, reason=stale_reason)
            honour_validation_file = False

    if grouped and honour_validation_file:
        reuse, reused_round = _round_behind_verdicts(
            phase_dir=phase_dir, validation_tasks_path=validation_tasks_path,
            round_document=round_document,
            current_inputs=current_inputs if reuse_checks_inputs else None,
        )
        if reuse:
            return _reuse_verdicts(
                claim, steps, phase_dir=phase_dir, grouped=grouped,
                validation_path=validation_path,
                validation_bytes=validation_bytes,
                validation_tasks_path=validation_tasks_path,
                reused_round=reused_round, use_note=use_note,
                scope_round_policy=scope_round_policy,
                scope_baseline=scope_baseline,
            )

    if not grouped:
        # Nothing to validate: a leftover round is bound to the grouping just
        # rewritten, so it retires whole and the empty verdicts take its place.
        steps.retire_stale_validation_round(
            phase_dir, reason=f"review returned no {findings}")
        claim.publish(validation_path, "[]\n", "write validation.json")
        return RoundOutcome(groups=[])

    if args.skip_validation:
        print("\nSkipping validation (--skip-validation flag set)")
        return RoundOutcome()

    def typed_follow_up(document: Mapping[str, Any]) -> Optional[str]:
        if follow_up is not None:
            return follow_up(document)
        return resolved_reaggregate_command(dict(document), typed_plan=True)

    if os.path.exists(validation_tasks_path):
        return await _resume_round(
            claim, args, steps, phase_name=phase_name, phase_dir=phase_dir,
            plan_path=plan_path, grouped=grouped, validation_path=validation_path,
            validation_tasks_path=validation_tasks_path, current_inputs=current_inputs,
            follow_up=typed_follow_up,
        )
    return await _materialize_round(
        claim, args, steps, phase_name=phase_name, phase_dir=phase_dir,
        plan_path=plan_path, grouped=grouped, validation_path=validation_path,
        validation_tasks_path=validation_tasks_path, build_round=build_round,
        follow_up=typed_follow_up,
    )


@dataclass(frozen=True)
class _RoundDocument:
    """``validation_tasks.json`` as one read found it: absent (not *present*),
    unreadable (*error*), or parsed (*document*). A reaggregate that reuses
    verdicts judges their round, checks its inputs and verifies its snapshots
    on this one read, so a task file replaced in between cannot pair one
    round's checks with another's (docs/development/review-results.md,
    "Consuming checked bytes")."""

    present: bool
    document: Any = None
    error: Optional[BaseException] = None

    def checked(
        self, path: str, *, phase_dir: str, current_inputs: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """The document, through ``read_task_file``'s checks; raises the
        ``TaskFileError`` that read would."""
        if self.error is not None:
            raise _subagent_tasks.unreadable_task_file(path, phase_dir, self.error)
        return _subagent_tasks.check_task_document(
            self.document, path, phase_dir=phase_dir, current_inputs=current_inputs,
        )


def _read_round_document(path: str) -> _RoundDocument:
    """*path* read once (:class:`_RoundDocument`)."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except FileNotFoundError:
        return _RoundDocument(present=False)
    except (OSError, ValueError) as exc:
        return _RoundDocument(present=True, error=exc)
    try:
        return _RoundDocument(present=True, document=json.loads(text))
    except ValueError as exc:
        return _RoundDocument(present=True, error=exc)


def _round_behind_verdicts(
    *,
    phase_dir: str,
    validation_tasks_path: str,
    round_document: _RoundDocument,
    current_inputs: Optional[Callable[[], Dict[str, Any]]],
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Whether a bound ``validation.json``'s verdicts may be reused, and the
    task file of the round they came from (``None`` when there is none).

    *round_document* is the task file as the caller read it once, the read
    its verdicts were judged against (:class:`_RoundDocument`); nothing here
    reads the file again. *current_inputs* is the lane's when its reuse
    checks them (``ReviewLane.reuse_checks_inputs``), else ``None``. The task
    file is then checked against them exactly as a resume reads it, so an
    input that moved is refused (exit 3) with the resume's message. Reuse also
    needs the task file to record every one of them: with no task file, or one
    that records fewer, nothing ties the verdicts to those inputs, so they are
    not reused and the round goes on as if no ``validation.json`` were there
    (merged again, or built anew). Without *current_inputs*, the verdicts are
    bound by their round's snapshots alone, and a dir with no task file has
    none to verify.
    """
    if not round_document.present:
        if current_inputs is None:
            return True, None
        print(
            "\nNot reusing validation.json: no validation_tasks.json records "
            "the inputs its verdicts were reached on"
        )
        return False, None
    inputs = current_inputs() if current_inputs is not None else None
    try:
        document = round_document.checked(
            validation_tasks_path, phase_dir=phase_dir, current_inputs=inputs,
        )
    except TaskFileError as task_file_error:
        print(f"ERROR: {task_file_error}", file=sys.stderr)
        sys.exit(task_file_error.exit_code)
    if inputs is not None:
        recorded = document.get("inputs") or {}
        unrecorded = sorted(key for key in inputs if key not in recorded)
        if unrecorded:
            print(
                f"\nNot reusing validation.json: validation_tasks.json records "
                f"no {', '.join(unrecorded)}"
            )
            return False, None
    return True, document


def _reuse_verdicts(
    claim: _review_round.Claim,
    steps: RoundSteps,
    *,
    phase_dir: str,
    grouped: List[Dict[str, Any]],
    validation_path: str,
    validation_tasks_path: str,
    reused_round: Optional[Dict[str, Any]],
    use_note: str,
    scope_round_policy: Any,
    scope_baseline: Optional[Mapping[str, Any]],
    validation_bytes: bytes,
) -> RoundOutcome:
    """The verdicts a bound ``validation.json`` holds, applied to *grouped*.

    *reused_round* is the task file :func:`_round_behind_verdicts` checked,
    the same read :func:`validation_source_decision` judged the verdicts'
    round against (its inputs already checked when the lane's reuse checks
    them). The snapshots its prompts named are re-hashed (exit 3 on a missing
    or changed one) and a moved phase dir is rebound before the verdicts are
    reused. *validation_bytes* are the bytes :func:`validation_source_decision`
    judged: the verdicts come from them, never from the file read again.
    """
    if reused_round is not None:
        steps.verify_round_context(reused_round, phase_dir, validation_tasks_path)
    print(
        f"\nUsing validation.json"
        f"{f' ({use_note})' if use_note else ''} for report generation..."
    )
    try:
        # Read once: the report built from these verdicts binds these exact
        # bytes (`claim.verdicts`), the ones judged bound above.
        validation_results = load_validation_results(
            Path(validation_path), raw=claim.hold_verdicts(validation_bytes),
        )
        validated_groups = apply_validation_to_groups(
            [g.to_dict() if hasattr(g, 'to_dict') else g for g in grouped],
            validation_results,
        )
        # The reused verdicts' validation-stage decision, re-derived for the
        # report from the round's policy and baseline.
        _scope_round.record_decisions(phase_dir, _scope_round.annotate_decisions(
            validated_groups, scope_round_policy.policy,
            _sp.baseline_id_of(scope_baseline),
        ))
        print(f"Loaded {len(validation_results)} validation results")
        # §2.4: the reused round re-publishes its own recorded context with the
        # reused verdicts, as every merge does.
        publish_from_task_document(phase_dir, reused_round, validation_results)
    except Exception as e:
        # An unreadable file reports the groups without verdicts rather than
        # ending the reaggregate; nothing here dispatches or merges.
        print(f"Warning: Could not load validation.json: {e}")
        return RoundOutcome()
    return RoundOutcome(groups=validated_groups, verdicts=claim.verdicts)


async def _resume_round(
    claim: _review_round.Claim,
    args: Any,
    steps: RoundSteps,
    *,
    phase_name: str,
    phase_dir: str,
    plan_path: str,
    grouped: List[Dict[str, Any]],
    validation_path: str,
    validation_tasks_path: str,
    current_inputs: Callable[[], Dict[str, Any]],
    follow_up: Callable[[Mapping[str, Any]], Optional[str]],
) -> RoundOutcome:
    """The round a task file on disk describes: merged whole, or handed out.

    A round still missing batch files is handed back as the fan-out handed it
    out: the missing files are named, and the ``--reaggregate`` to run once
    they are written is printed and put on the result line (*follow_up*), so a
    host reading only that line knows the round is not finished."""
    print("\nFound validation_tasks.json, checking for completed batches...")
    # A task file whose inputs moved since materialization, or that an older
    # skill version wrote, is refused before anything is dispatched (exit 3,
    # outside any handler, so nothing below can complete the phase).
    try:
        batch_metadata = _subagent_tasks.read_task_file(
            validation_tasks_path, phase_dir=phase_dir, current_inputs=current_inputs(),
        )
    except TaskFileError as task_file_error:
        print(f"ERROR: {task_file_error}", file=sys.stderr)
        sys.exit(task_file_error.exit_code)
    # The snapshots the stored prompts name are re-hashed; a moved phase dir is
    # rebound to its own copy, and a changed or missing one is exit 3.
    steps.verify_round_context(batch_metadata, phase_dir, validation_tasks_path)
    # A stale `prompt_path` is rebound and persisted before any batch is handed
    # out: native hosts reread the JSON, not this in-memory document.
    with host_views_lock(phase_dir):
        if ensure_prompt_sidecars(batch_metadata, phase_dir):
            try:
                with claim.held("rewrite validation_tasks.json"):
                    failure_capture._atomic_write_json(validation_tasks_path, batch_metadata)
            except OSError as exc:
                print(
                    f"ERROR: Could not persist repaired prompt metadata to "
                    f"{validation_tasks_path}: {exc}. Fix task-file write access "
                    "and retry reaggregation before dispatching native subagents.",
                    file=sys.stderr,
                )
                sys.exit(3)

    total_batches = batch_metadata.get("total_batches", 0)
    missing_batches = [
        name for name in _batch_names(batch_metadata)
        if not os.path.exists(os.path.join(phase_dir, name))
    ]
    batches_found = len(batch_metadata.get("batches", [])) - len(missing_batches)
    if batches_found == total_batches and total_batches > 0:
        print(f"All {total_batches} batch files found, merging...")
        groups = steps.merge_validation_batches(
            phase_dir, batch_metadata, grouped, validation_path, claim=claim,
        )
        return RoundOutcome(groups=groups, verdicts=claim.verdicts)

    # An unfinished round reopens the phase before any batch is handed out: an
    # earlier `--reaggregate --skip-validation` may have recorded it complete.
    claim.check("reopen the phase for validation")
    steps.reopen_phase_for_validation(plan_path, phase_name, phase_dir)
    if await steps.dispatch_in_round(
        claim, steps.dispatch_subagent_tasks,
        args,
        task_file=validation_tasks_path,
        phase_dir=phase_dir,
        phase=phase_name,
        document=batch_metadata,
        plan_path=str(plan_path),
        label="validation",
        retry_command=resolved_reaggregate_command(batch_metadata),
    ):
        # The still-incomplete batches ran in this process (completed ones are
        # skipped by their result files).
        groups = steps.merge_validation_batches(
            phase_dir, batch_metadata, grouped, validation_path, claim=claim,
        )
        return RoundOutcome(groups=groups, verdicts=claim.verdicts)

    _run_record.report_progress(phase_dir, step="validation_pending")
    print(f"Only {batches_found}/{total_batches} batch files found.")
    if missing_batches:
        print(f"Missing: {', '.join(missing_batches)} (tasks: {validation_tasks_path})")
    print("Wait for all validation subagents to complete before reaggregating, "
          "or add --exec-subagents to run the missing batches in this process.")
    # The follow-up the round's first hand-off named, on the result line too.
    reaggregate_cmd = follow_up(batch_metadata)
    print("\nAfter validation completes, run:")
    print(f"  {reaggregate_cmd or ''}")
    steps.record_next(reaggregate_cmd or None)
    return RoundOutcome(handed_off=True)


async def _materialize_round(
    claim: _review_round.Claim,
    args: Any,
    steps: RoundSteps,
    *,
    phase_name: str,
    phase_dir: str,
    plan_path: str,
    grouped: List[Dict[str, Any]],
    validation_path: str,
    validation_tasks_path: str,
    build_round: Callable[[BoundDocument], ValidationRound],
    follow_up: Callable[[Mapping[str, Any]], Optional[str]],
) -> RoundOutcome:
    """A new round for *grouped*: published, then dispatched or handed out."""
    print("\nPreparing batched validation for subagent execution...")
    # A new round binds its own snapshot, from one read of the plan as it is now.
    plan_document = steps.bind_plan_for_validation(str(plan_path), phase_dir)
    with host_views_lock(phase_dir):
        batched_tasks = materialize_validation_round(
            _on_held_grouping(claim, build_round(plan_document)))
        batched_tasks["format_version"] = CURRENT_FORMAT_VERSION
        claim.publish(validation_tasks_path, json.dumps(batched_tasks, indent=2),
                      "write validation_tasks.json")

    # The phase owes validation from here (a completion an earlier
    # `--skip-validation` run recorded is dropped), and the executor's mirror of
    # the previous round's batches is cleared: nothing of this one has run yet.
    claim.check("reopen the phase for validation")
    steps.reopen_phase_for_validation(plan_path, phase_name, phase_dir)
    _run_record.report_progress(phase_dir, step="validation_pending", subagents=None)

    total_batches = batched_tasks["total_batches"]
    stats = batched_tasks.get("batching_stats", {})
    if total_batches == 1:
        print(f"\n[VALIDATION_PENDING] {validation_tasks_path}")
    else:
        print(f"\n[VALIDATION_BATCHES_PENDING] {validation_tasks_path}")
        print(f"Batches: {total_batches}")
    print("\nValidation prepared for subagent execution.")
    print(f"Groups to validate: {stats.get('total_groups', len(grouped))}")

    # Under `--exec-subagents` this process dispatches the round and merges it;
    # otherwise the host runs it and comes back with `--reaggregate`. The task
    # file stores only the durable mode and plan, so the command is resolved
    # from the running skill dir.
    if await steps.dispatch_in_round(
        claim, steps.dispatch_subagent_tasks,
        args,
        task_file=validation_tasks_path,
        phase_dir=phase_dir,
        phase=phase_name,
        document=batched_tasks,
        plan_path=str(plan_path),
        label="validation",
        retry_command=resolved_reaggregate_command(batched_tasks),
    ):
        groups = steps.merge_validation_batches(
            phase_dir, batched_tasks, grouped, validation_path, claim=claim,
        )
        return RoundOutcome(groups=groups, verdicts=claim.verdicts)

    # The plan as the user typed it, when that names the same file.
    reaggregate_cmd = follow_up(batched_tasks)
    print("\nAfter validation completes, run:")
    print(f"  {reaggregate_cmd or ''}")
    # The one follow-up a native-subagent host is owed, also on the result line.
    steps.record_next(reaggregate_cmd or None)
    return RoundOutcome(handed_off=True)


# ---------------------------------------------------------------------------
# A fan-out's grouping and its validation round
# ---------------------------------------------------------------------------

def group_findings(
    claim: _review_round.Claim,
    steps: RoundSteps,
    *,
    phase_dir: str,
    grouped_path: str,
    validation_path: str,
    records: List[Dict[str, Any]],
    noun: str,
    annotate: Optional[Callable[[List[Dict[str, Any]]], Any]] = None,
) -> BoundGrouping:
    """A fan-out's grouping of what its models returned, the same on every lane.

    *records* are the findings of every model that answered, each stamped with
    the slot that returned it. They are grouped, given their stable ids and
    passed to *annotate* (review-code's commit attribution) before
    ``grouped.json`` is written, so the file carries it. The previous round's
    verdicts belong to the grouping this write replaces and retire in the same
    step (``retire_validation_for_regroup``): the whole round when the grouping
    changed, ``validation.json`` alone when the hashes are the same, so a
    resume that skipped every model does not re-run its completed batches. The
    grouping's size is recorded (``grouping_complete``).

    Zero findings are a finished review with zero groups: the whole previous
    round retires, ``grouped.json`` is written empty and ``validation.json``
    is ``[]``, so neither the report nor an apply phase reads an earlier
    round's groups. The retirements run in the directory that holds
    *grouped_path*; *noun* names the findings in the printed lines.
    """
    grouped_dir = os.path.dirname(str(grouped_path))
    if not records:
        with claim.held("retire the previous validation and regroup"):
            steps.retire_stale_validation_round(
                grouped_dir, reason=f"review returned no {noun}")
            _hold_grouping(claim, _review_round.replace_file(
                grouped_path, json.dumps(save_groups_payload([]), indent=2)))
        print(f"Grouped {noun} saved to: {grouped_path} (no {noun})")
        claim.publish(validation_path, "[]\n", "write validation.json")
        return BoundGrouping(groups=[], reused=False)

    raw_grouped = steps.group_similar_suggestions(records)
    grouped = [g.to_dict() if hasattr(g, 'to_dict') else g for g in raw_grouped]
    steps.stamp_stable_ids(grouped)
    annotation = annotate(grouped) if annotate is not None else None
    # The retirement and the new grouped.json (replaced whole: a reaggregate
    # reads it back) are one step of this run's round.
    with claim.held("retire the previous validation and regroup"):
        steps.retire_validation_for_regroup(
            grouped_dir, grouped, reason="grouped.json rewritten by a re-run")
        _hold_grouping(claim, _review_round.replace_file(
            grouped_path, json.dumps(save_groups_payload(grouped), indent=2)))
    print(f"Grouped {noun} saved to: {grouped_path}")
    steps.update_status(phase_dir, {
        "state": "grouping_complete",
        "total_groups": len(grouped),
        "total_suggestions": len(records),
    })
    return BoundGrouping(groups=grouped, reused=False, annotation=annotation)


async def materialize_fanout_round(
    lane: ReviewLane,
    claim: _review_round.Claim,
    args: Any,
    steps: RoundSteps,
    *,
    grouped: List[Dict[str, Any]],
    validation_path: str,
    plan_document: Callable[[], BoundDocument],
    build_round: Callable[[BoundDocument], ValidationRound],
) -> RoundOutcome:
    """The validation round a fan-out publishes for *grouped*, then dispatches
    or hands to the host, the same on every lane.

    *plan_document* is the plan the round binds (the lane's snapshot from
    load, bound before the fan-out); *build_round* the lane's round over it,
    built under ``host_views_lock``. The task file is stamped with the format
    version and published with the phase machine's word for the stretch
    (``validation_pending``) while the round is this run's, before the dispatch
    that may never come back to write it. Under ``--exec-subagents`` the round
    is dispatched here and merged; otherwise the hand-off prints the
    ``--reaggregate`` to run, puts it on the result line, and records the
    markers, the task file and the follow-up in its durable form (mode word,
    plan, replay flags), so ``status`` can name the command that advances the
    phase; the caller then ends with the phase open.

    A phase whose damaged checkpoint a fresh run replaced
    (``result_files.RECOVERED_KEY``) is never handed over: the ``--reaggregate``
    that reads the host's verdicts back refuses there. Without
    ``--exec-subagents`` its round is not validated, as under
    ``--skip-validation``, with a warning that names both ways to a validated
    review: the :class:`RoundOutcome` carries *grouped* as it stands, with no
    verdicts, so the report and ``--fail-on-high`` count the groups this run
    holds and nothing is read back from disk.

    Under ``--exec-subagents`` such a phase merges only the batches its own
    dispatch wrote: the executor dispatches every batch again rather than
    take a file on disk as done (``dispatch_subagent_tasks``), and a batch it
    holds no bytes of its own for, a surviving earlier run's file, leaves the
    round unvalidated with the same warning and outcome
    (docs/development/review-results.md, "Consuming checked bytes").
    """
    phase_dir = str(lane.phase_dir)
    plan_path = str(lane.plan_path)
    recovered = _result_files.phase_recovered(phase_dir)
    if not lane.fanout_steps().exec_subagents_requested(args) and recovered:
        return _recovered_round_unvalidated(phase_dir, grouped, (
            "the --reaggregate that reads a host's verdicts back refuses that "
            "folder; run the phase with --exec-subagents to validate in its own "
            "process"
        ))
    validation_tasks_path = os.path.join(phase_dir, "validation_tasks.json")
    # Host-neutral: printed on every host that dispatches subagent validation.
    print("\nPreparing batched validation for subagent execution...")
    document = plan_document()
    with host_views_lock(phase_dir):
        batched_tasks = steps.materialize_validation_round(
            _on_held_grouping(claim, build_round(document)))
        batched_tasks["format_version"] = CURRENT_FORMAT_VERSION
        with claim.held("write validation_tasks.json"):
            _review_round.replace_file(
                validation_tasks_path, json.dumps(batched_tasks, indent=2))
            steps.update_status(phase_dir, {"state": "validation_pending"})

    total_batches = batched_tasks["total_batches"]
    stats = batched_tasks.get("batching_stats", {})
    if total_batches == 1:
        print(f"\n[VALIDATION_PENDING] {validation_tasks_path}")
    else:
        print(f"\n[VALIDATION_BATCHES_PENDING] {validation_tasks_path}")
        print(f"Batches: {total_batches}")
        if stats.get("efficiency_gain_percent", 0) > 0:
            print(f"Efficiency gain: {stats['efficiency_gain_percent']}%")
    print("\nValidation prepared for subagent execution.")
    print(f"Groups to validate: {stats.get('total_groups', len(grouped))}")
    print(f"HIGH priority groups: {stats.get('high_count', 0)}")
    print(f"Normal priority groups: {stats.get('normal_count', 0)}")

    # D3b: self-contained mode dispatches and merges in this process; the
    # task file stores only the durable mode and plan, so the command is
    # resolved from the running skill dir.
    if await steps.dispatch_in_round(
        claim, steps.dispatch_subagent_tasks,
        args,
        task_file=validation_tasks_path,
        phase_dir=phase_dir,
        phase=lane.phase_name,
        document=batched_tasks,
        plan_path=plan_path,
        label="validation",
        retry_command=lane.round_follow_up(batched_tasks),
    ):
        if not recovered:
            groups = steps.merge_validation_batches(
                phase_dir, batched_tasks, grouped, validation_path, claim=claim,
            )
            return RoundOutcome(groups=groups, verdicts=claim.verdicts)
        undispatched = [
            name for name in _batch_names(batched_tasks)
            if claim.checked_result(name, dispatched=True) is None
        ]
        if undispatched:
            return _recovered_round_unvalidated(phase_dir, grouped, (
                f"this run's dispatch wrote no verdicts of its own for "
                f"{', '.join(undispatched)}, and a batch file it did not write is "
                f"never merged there; run the phase again with --exec-subagents"
            ))
        groups = steps.merge_validation_batches(
            phase_dir, batched_tasks, grouped, validation_path, claim=claim,
            dispatched_only=True,
        )
        return RoundOutcome(groups=groups, verdicts=claim.verdicts)

    # The plan as the user typed it, when that names the same file.
    reaggregate_cmd = lane.round_follow_up(batched_tasks, typed=True)
    print("\nAfter validation completes, run:")
    print(f"  {reaggregate_cmd or ''}")
    steps.record_next(reaggregate_cmd or None)
    # Persisted in its durable, rebindable form, never as the resolved
    # command printed above: the plugin cache is keyed by commit hash, so a
    # stored absolute command points at a directory a plugin update removes.
    steps.update_status(phase_dir, {
        "state": "validation_pending",
        "stdout_markers": (
            ["VALIDATION_BATCHES_PENDING"] if total_batches > 1
            else ["VALIDATION_PENDING"]
        ),
        "validation_tasks_path": validation_tasks_path,
        **cli_common.durable_reaggregate_fields(lane.orchestrator_script, plan_path),
    })
    steps.report_progress(phase_dir, step="validation_pending")
    return RoundOutcome(handed_off=True)


def _batch_names(document: Mapping[str, Any]) -> List[str]:
    """The ``validation_batch_<n>.json`` names a round's task file expects."""
    return [
        f"validation_batch_{batch.get('batch_index')}.json"
        for batch in document.get("batches", [])
    ]


def _recovered_round_unvalidated(
    phase_dir: str, grouped: List[Dict[str, Any]], why: str,
) -> RoundOutcome:
    """A recovered phase's round left unvalidated, *why* naming the cause: the
    warning, the result note, and *grouped* as it stands with no verdicts, for
    the report and ``--fail-on-high`` to count (:func:`materialize_fanout_round`)."""
    note = (
        f"validation was not run: {phase_dir}'s damaged checkpoint was replaced, "
        f"and {why}, or move the whole phase folder aside to start clean"
    )
    print(f"WARNING: {note}.", file=sys.stderr)
    _result_files.append_result_note(phase_dir, note)
    return RoundOutcome(groups=list(grouped))


# ---------------------------------------------------------------------------
# A reaggregate's loading half
# ---------------------------------------------------------------------------

def reaggregate_result_files(
    steps: RoundSteps, *, mode: str, phase_dir: str, plan_path: str,
) -> Optional[List[str]]:
    """The model result files a ``--reaggregate`` reads, or ``None`` when there
    are none and the reaggregate ends here.

    Every phase-dir artifact (the grouped and validation files, the
    executor's and write scheduler's reports) is left out by the one shared
    rule, sorted so the round is reproducible; only the models this phase
    records are read, so a misnamed result file is never loaded as another
    reviewer: any other result file is named and set aside. Nor is a file of a
    model the phase withholds (``models_rejected``, ``models_unchecked``:
    a slot that failed its safety checks or ended before they passed): it
    stays failed. A checkpoint that cannot be read may record any model so,
    and stops the reaggregate at exit 3 with every file left unread. With
    no file left, every requested reviewer having failed is the fan-out's
    exit 3 naming them (decision 11.11), and otherwise exit 0. A phase whose
    damaged checkpoint a fresh run replaced (``result_files.RECOVERED_KEY``)
    trusts no file on disk, so its reaggregate stops at exit 3 first, every
    file left as it is (:func:`recovered_phase_advice`).
    """
    if _result_files.phase_recovered(phase_dir):
        sys.exit(_unattended.fail_closed(
            f"ERROR: --reaggregate reads the result files in {phase_dir}, and "
            f"{recovered_phase_advice(phase_dir)}"
        ))
    result_files = _result_files.model_result_paths(phase_dir)
    result_files = _result_files.set_aside_unrecorded_results(phase_dir, result_files)
    if result_files and _result_files.withheld_models(phase_dir).unreadable:
        names = ", ".join(os.path.basename(path) for path in result_files)
        sys.exit(_unattended.fail_closed(
            f"ERROR: {_status_file.status_path(phase_dir)} cannot be read, so "
            f"nothing shows which result files come from slots whose safety "
            f"checks passed; none is read ({names}). "
            f"{_status_file.unreadable_checkpoint_advice(phase_dir)}"
        ))
    result_files = _result_files.withhold_results(phase_dir, result_files)
    _result_files.publish_result_notes(phase_dir)
    if result_files:
        return result_files
    print(f"No model result files found in: {phase_dir}")
    no_results, _requested = steps.remaining_failed_models(phase_dir, [])
    steps.announce_remaining_failures(phase_dir, no_results)
    steps.exit_when_every_reviewer_failed(
        phase_dir, no_results, mode=mode, plan_path=plan_path,
    )
    return None


@dataclass(frozen=True)
class LoadedResults:
    """What :func:`load_reaggregate_results` read back.

    ``records``: every model's findings, stamped, in file order. ``by_model``:
    each model's own, keyed by its canonical spec. ``stems``: each model's
    result-file stem. ``failed_models``: the requested models still without a
    result once the files on disk were reconciled (``remaining_failed_models``),
    and ``requested`` the recorded requested set (``None`` when none was).
    """

    records: List[Dict[str, Any]]
    by_model: Dict[str, List[Dict[str, Any]]]
    stems: Dict[str, str]
    failed_models: Dict[str, str]
    requested: Optional[Any]

    @property
    def models(self) -> List[str]:
        return sorted(self.by_model)


def load_reaggregate_results(
    steps: RoundSteps,
    result_files: List[str],
    *,
    mode: str,
    phase_dir: str,
    plan_path: str,
    noun: str,
    stamp: Callable[[List[Dict[str, Any]], str], None],
    on_unattributed: Optional[Callable[[], None]] = None,
    on_nothing_readable: Optional[Callable[[], None]] = None,
) -> Optional[LoadedResults]:
    """Read back a ``--reaggregate``'s results, the same way on every lane;
    ``None`` when no file could be read and the reaggregate ends here.

    The canonical specs come from the checkpoint (``build_unsanitize_map``);
    *on_unattributed* runs when it records none, so every group would be
    attributed to a stem. One file per logical model (W3,
    ``resolve_result_files_by_model``). Entries that are not objects are
    dropped before anything is stamped, so one malformed element cannot lose
    every model's findings; *stamp* is the lane's own stamping of one model's
    list (review-code stamps ``model`` before ``source_model``: the file's
    bytes are hashed). A model whose file is on disk has completed, whatever
    the fan-out recorded (a salvage, an out-of-band result), and the failures
    left are read back only after that reconciliation and named.

    No readable result at all: the report's verdict counts are cleared, which
    no report rebuild reaches on this ending (§6 T6.1); *on_nothing_readable*
    is the lane's own recount (review-plan's consolidation recommendation);
    then reviewers recorded failed are exit 3 as on the fan-out, else exit 0.
    Results that hold no findings are a finished review with zero groups, not
    this ending.
    """
    unsanitize = steps.build_unsanitize_map(phase_dir)
    if not unsanitize and on_unattributed is not None:
        on_unattributed()

    records: List[Dict[str, Any]] = []
    by_model: Dict[str, List[Dict[str, Any]]] = {}
    stems: Dict[str, str] = {}
    for model, chosen_path, entries in steps.resolve_result_files_by_model(
        phase_dir, result_files, unsanitize, noun=noun,
    ):
        stems[model] = Path(chosen_path).stem
        entries = drop_non_record_entries(entries, model, noun=noun)
        stamp(entries, model)
        records.extend(entries)
        by_model[model] = entries
        print(f"  Loaded {len(entries)} {noun} from {model}")

    print(f"\nRe-aggregating {len(records)} {noun} from {len(by_model)} models")

    for model in steps.record_models_present(phase_dir, sorted(by_model)):
        print(f"[{model}] result file present; recorded as completed (was failed)")
    failed_models, requested = steps.remaining_failed_models(phase_dir, sorted(by_model))
    steps.announce_remaining_failures(phase_dir, failed_models)

    if not by_model:
        print("No readable model results to aggregate.")
        if on_nothing_readable is not None:
            on_nothing_readable()
        steps.record_validation_counts(phase_dir, [])
        steps.exit_when_every_reviewer_failed(
            phase_dir, failed_models, mode=mode, plan_path=plan_path,
        )
        return None
    return LoadedResults(
        records=records, by_model=by_model, stems=stems,
        failed_models=failed_models, requested=requested,
    )


# ---------------------------------------------------------------------------
# Handing the report back
# ---------------------------------------------------------------------------

def hand_back_report(
    steps: RoundSteps,
    phase_dir: Any,
    *,
    report: Any,
    grouped: Any,
    validation: Any,
    issues: Any = None,
) -> None:
    """A published report's files handed back, the same on every lane.

    A detached run's caller never saw its stdout, so ``status`` hands the
    files back from ``.status.json``'s ``output_files``
    (``record_output_files``: only paths that exist, and nothing in the
    foreground), and the terminal ``MULTI_LLM_RESULT.artifacts`` names them
    too (``record_review_artifacts``: ``validation.json`` and review-code's
    ``issues.json`` only when they exist). Each file is named on both channels
    or on neither: the apply phases read ``validation.json`` (and
    ``issues.json``), and without it treat every group as needing a human or
    stop. ``report.html`` sits beside ``report.md`` in *phase_dir*. Called by
    every site that publishes a report and by review-code's heal of a lost
    completion (docs/development/review-results.md, "The shared review lane").
    """
    report_html = os.path.join(str(phase_dir), "report.html")
    files = {
        "report": str(report),
        "report_html": report_html,
        "grouped": str(grouped),
        "validation": str(validation),
        **({"issues": str(issues)} if issues is not None else {}),
    }
    steps.record_output_files(str(phase_dir), **files)
    steps.record_review_artifacts(
        report, report_html, grouped, validation,
        *((issues,) if issues is not None else ()),
    )


# ---------------------------------------------------------------------------
# Recording the phase complete
# ---------------------------------------------------------------------------

def record_phase_complete(
    claim: Optional[_review_round.Claim],
    steps: RoundSteps,
    *,
    state: Any,
    phase_name: str,
    phase_dir: str,
) -> None:
    """The phase recorded complete, on every ending that completes it.

    While the round on record is still *claim*'s (``None`` only for
    review-code's partial-completion guard, which runs before a round is
    claimed and has proven the files on disk are this round's); then the
    phase machine's terminal word, which ``status`` renders, and the last
    ``progress.step``. Each completion site calls it in its lane's own order,
    with no shared driver around it (docs/development/review-results.md, "Why
    each lane keeps its completion tail").
    """
    if claim is not None:
        claim.check("record the phase complete")
    state.mark_phase_completed(phase_name)
    state.save()
    steps.update_status(phase_dir, {"state": "complete"})
    steps.report_progress(phase_dir, step="complete")


def complete_reaggregate(
    claim: _review_round.Claim,
    steps: RoundSteps,
    loaded: LoadedResults,
    *,
    state: Any,
    phase_name: str,
    phase_dir: str,
) -> None:
    """A reaggregate's completion, the same on every lane.

    A reaggregate that still lacks some models reports ``[PARTIAL_RESULTS:
    …]`` and ``state: "partial"`` (exit 0), as the fan-out does (T5.4b,
    decision 11.11). ``unattended=False``: the ``[AUTO_RESOLVED]`` record that
    call writes names the fan-out's in-process continuation, never a separate
    ``--reaggregate``. The phase is then recorded complete
    (:func:`record_phase_complete`) and no ``next`` is recorded.
    """
    _unattended.report_partial_results(
        completed=loaded.models,
        failed=list(loaded.failed_models),
        phase_dir=phase_dir,
        unattended=False,
    )
    record_phase_complete(
        claim, steps, state=state, phase_name=phase_name, phase_dir=phase_dir,
    )
