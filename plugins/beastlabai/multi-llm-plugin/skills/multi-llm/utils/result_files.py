"""Which ``*.json`` in a review phase dir is a model's result, and what to do with one that is not.

A review phase dir holds one ``<sanitized spec>.json`` per reviewer beside a
dozen other JSON artifacts, and two readers decide which files are results:

* **the slot** (:func:`find_misnamed_result`, called by
  ``llm_client.invoke_with_file_output``): a reviewer that wrote its answer under
  the wrong name. Live run 10 (Claude Code racing 07): pi was asked for
  ``pi_openrouter_deepseek_deepseek-v4_1-flash.json`` and wrote
  ``pi_openrouter_deepseek_deepseek-v4-flash.json``; the slot found nothing at
  the requested name and recorded a model failed whose three findings were on
  disk. The slot now reads the one fresh JSON array its own provider's prefix
  wrote during the run, when that is unambiguous, and renames it to the
  requested name so nothing reads it twice.
* **the aggregate** (:func:`set_aside_unrecorded_results`, called by both
  ``--reaggregate`` copies): the same file, left behind, was globbed as a third
  reviewer named by its stem ("scope unknown"), its findings mixed into
  ``report.md`` and the validation round regrouped away. The aggregate now reads
  only the files of the models the phase's ``.status.json`` records; any other
  result file is named in a note and set aside — renamed to
  ``<name>.set-aside``, never deleted.

Both write their note to ``.status.json`` (``result_notes``), which the report
renders as its ``**Result files:**`` line. A leaf module: ``llm_client`` imports
it, so it imports nothing that imports ``llm_client``.
"""

from __future__ import annotations

import json
import os
import stat
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, NamedTuple, Optional, Sequence, Tuple

from . import status_file as _status_file
from .json_extractor import sanitize_model_name
from .text_clip import plain_line

#: Name fragments of the ``*.json`` artifacts a phase dir holds beside the
#: per-model results: a name containing one is never a model's result. The one
#: list every reader of a phase dir's results uses, through
#: :func:`model_result_paths` (or :func:`snapshot_candidates` for the slot).
NON_MODEL_JSON_MARKERS = (
    'grouped', 'validation', 'salvage', 'revalidation', 'consolidated',
    'consolidation', 'issues', 'fix_tasks', 'report_data', 'subagent_batch_report',
    'subagent_dry_run', 'write_batch_report', 'write_tasks',
)

#: Whole basenames that are never a model's result. ``state.json`` belongs in
#: the plan's output dir, one level up, but the executor reserves the name in
#: a phase dir too (``task_result.RESERVED_OUTPUT_NAMES``); a substring
#: marker would also drop a model whose id contains ``state``.
NON_MODEL_JSON_NAMES = frozenset({'state.json'})

#: Suffix a result file no recorded model owns is renamed with.
SET_ASIDE_SUFFIX = "set-aside"

#: Suffix the previous round's ``<stem>.json`` is renamed with when a slot found
#: it there, unchanged since the slot started (:func:`set_aside_stale_result`).
#: The name no longer ends in ``.json``, so no reader of a phase dir's results
#: matches it: neither reaggregate's ``*.json`` glob (and so neither
#: :func:`set_aside_unrecorded_results`), nor :func:`snapshot_candidates`, nor
#: the salvage recovery loop's ``exists(<stem>.json)``, nor a resume's skip.
STALE_RESULT_SUFFIX = "stale-earlier-run"

#: Suffix a model's ``<stem>.json`` is renamed with when the round refuses the
#: result in it (:func:`set_aside_rejected_result`). Outside every reader of a
#: phase dir's results, as :data:`STALE_RESULT_SUFFIX` is.
REJECTED_RESULT_SUFFIX = "rejected"

#: Suffix a model's ``<stem>.json`` is renamed with when its slot ended before
#: its safety checks passed (:func:`set_aside_unchecked_result`).
UNCHECKED_RESULT_SUFFIX = "unchecked"

#: ``.status.json`` key holding the phase's notes about its result files.
RESULT_NOTES_KEY = "result_notes"

#: ``.status.json`` key holding ``{model_spec: reason}``: the models whose slot
#: failed its safety checks and that no checked attempt has superseded since
#: (:func:`record_rejected_model`; docs/development/review-results.md,
#: "Withheld slot answers"). A file of theirs is never read as a result.
REJECTED_MODELS_KEY = "models_rejected"

#: ``.status.json`` key holding ``{model_spec: reason}``: the models a slot was
#: dispatched for whose safety checks have not passed since. Recorded before
#: the dispatch and cleared the moment the checks pass, so a slot that a
#: deadline, an interrupt or an exception ends in between, or whose verdict
#: could not be recorded, leaves it (:func:`record_unchecked_model`; same
#: section). A file of theirs is never read as a result either.
UNCHECKED_MODELS_KEY = "models_unchecked"

#: Both keys, in the order a model's disposition is named by: a failed check
#: outranks checks that never finished.
WITHHELD_KEYS = (REJECTED_MODELS_KEY, UNCHECKED_MODELS_KEY)

#: The ``models_unchecked`` reason of an ask slot whose checks passed but whose
#: run failed, leaving an unfinished answer at its answer path that could be
#: neither moved nor copied aside: withheld like an unchecked answer until a
#: later slot replaces it or ``--accept-partial`` counts it
#: (docs/development/workflows.md#ask-mode).
UNFINISHED_ANSWER_REASON = (
    "its run failed, and its unfinished answer could not be set aside"
)

#: ``.status.json`` key of a phase whose checkpoint was found damaged and
#: replaced by a fresh run's startup (``review_lane.recover_damaged_checkpoint``):
#: ``{"reason": str, "accepted": [model_spec, ...]}``. What the damaged file
#: withheld is unknown, and a provider of the run that left it may still write
#: any file of the folder, so a recovered phase never trusts a result file on
#: disk: **every** model is withheld, selected, unselected or never seen, but
#: the ones the operator *accepted* (ask's ``--accept-partial``,
#: :func:`clear_withheld_model`; never a passed check). A resume reuses
#: nothing, salvage never runs and a ``--reaggregate`` refuses; a run counts
#: only the answers it holds in memory. Every later round's opening carries
#: the record over; nothing removes it (docs/development/review-results.md,
#: "Recovering a damaged one"). A model one of the maps records is withheld by
#: that record first.
RECOVERED_KEY = "checkpoint_recovered"

#: The reason :data:`RECOVERED_KEY` records, and the one a record of the
#: wrong shape is read with.
RECOVERED_REASON = (
    "the phase's damaged checkpoint was replaced, and a run it left behind may "
    "still write any file of the folder"
)

#: The :data:`RECOVERED_KEY` field naming the models the operator counted anyway.
ACCEPTED_FIELD = "accepted"

#: ``{name: (mtime_ns, size)}`` of a phase dir's candidate files.
Snapshot = Dict[str, Tuple[int, int]]


def is_model_result_name(name: str) -> bool:
    """Whether a phase dir's file *name* can be a model's result.

    A ``*.json`` that is not a dotfile (``.status.json``), not one of
    :data:`NON_MODEL_JSON_NAMES` and contains none of
    :data:`NON_MODEL_JSON_MARKERS`. The name says nothing about who wrote the
    file: :func:`set_aside_unrecorded_results` decides that.
    """
    return (
        name.endswith(".json")
        and not name.startswith(".")
        and name not in NON_MODEL_JSON_NAMES
        and not any(marker in name for marker in NON_MODEL_JSON_MARKERS)
    )


def model_result_paths(phase_dir: os.PathLike | str) -> List[str]:
    """The files in *phase_dir* whose name can be a model's result, sorted.

    Each path is ``os.path.join(phase_dir, name)``, the spelling a
    ``glob(<phase_dir>/*.json)`` returns. ``[]`` when the dir cannot be listed.
    """
    try:
        names = os.listdir(phase_dir)
    except OSError:
        return []
    base = os.fspath(phase_dir)
    return [os.path.join(base, name) for name in sorted(names) if is_model_result_name(name)]


def snapshot_candidates(phase_dir: os.PathLike | str) -> Snapshot:
    """What could be a result file in *phase_dir* now, with its mtime and size."""
    snapshot: Snapshot = {}
    try:
        entries = list(os.scandir(phase_dir))
    except OSError:
        return snapshot
    for entry in entries:
        if not is_model_result_name(entry.name):
            continue
        try:
            # A regular file only, never through a link: a model can leave a
            # link or a FIFO under a `.json` name, and reading a FIFO hangs.
            if not entry.is_file(follow_symlinks=False):
                continue
            st = entry.stat(follow_symlinks=False)
        except OSError:
            continue
        snapshot[entry.name] = (st.st_mtime_ns, st.st_size)
    return snapshot


def _provider_prefix(model_spec: str) -> Optional[str]:
    provider, sep, _model = str(model_spec).partition(":")
    if not sep or not provider:
        return None
    return f"{sanitize_model_name(provider)}_"


def find_misnamed_result(
    phase_dir: os.PathLike | str,
    before: Snapshot,
    model_spec: str,
    run_model_specs: Sequence[str],
) -> Optional[Path]:
    """The one file *model_spec* plausibly wrote under the wrong name, or ``None``.

    A candidate appeared (or changed) in *phase_dir* since *before* was taken at
    the slot's start, is not the requested file of any model in the run, is not a
    phase artifact, and starts with this model's provider prefix
    (``pi_`` for ``pi:…``). It is returned only when there is exactly one, and
    only when no other model of the run shares that prefix — two pi reviewers
    running side by side could each have written it, and a misattributed answer
    is worse than a failed slot.
    """
    prefix = _provider_prefix(model_spec)
    if prefix is None:
        return None
    own = sanitize_model_name(model_spec)
    run_stems = {sanitize_model_name(spec) for spec in run_model_specs} | {own}
    if any(stem != own and stem.startswith(prefix) for stem in run_stems):
        return None
    requested = {f"{stem}.json" for stem in run_stems}
    fresh = [
        name for name, stamp in snapshot_candidates(phase_dir).items()
        if before.get(name) != stamp
        and name not in requested
        and name.startswith(prefix)
    ]
    if len(fresh) != 1:
        return None
    return Path(phase_dir) / fresh[0]


def set_aside_stale_result(path: os.PathLike | str, *, reason: Optional[str] = None) -> Optional[Path]:
    """Rename an earlier run's ``<stem>.json`` to ``<stem>.json.stale-earlier-run``.

    Called by ``llm_client.invoke_with_file_output`` when the file a slot asks
    its model for was there before the slot started and has not moved since:
    an earlier round's answer, which the slot never reads as its own. Left on
    disk it was read anyway, one step later, at exit 0 (Fable review
    2026-10-09): the ``--exec-subagents`` salvage recovery loop moved the model
    out of ``failed_models`` because ``<stem>.json`` existed, and
    ``--reaggregate`` kept it because its stem is a recorded model's — round
    one's findings grouped, validated and applied as round two's.

    A rename, never a delete, under the conventions beside it
    (``.stale-unselected``, code-review's ``.stale-<scope id>``,
    ``.set-aside``): the bytes are what that model said last round, and an
    existing file of the target name is never overwritten (``.<stamp>`` is
    appended). One line names the new file. Non-fatal and loud: a failed rename
    warns on stderr naming the file that survived. Returns the new path, or
    ``None`` when nothing was renamed.

    A new scope-policy round uses the same retirement with an explicit
    ``reason`` so its notice describes the policy change, not a slot retry.
    """
    source = Path(path)
    target = source.with_name(f"{source.name}.{STALE_RESULT_SUFFIX}")
    if os.path.lexists(target):
        target = target.with_name(
            f"{target.name}.{datetime.now().strftime('%Y%m%dT%H%M%S%f')}"
        )
    try:
        os.replace(source, target)
    except OSError as exc:
        print(
            f"Warning: could not set {source.name} aside ({exc}); it is an "
            f"earlier run's answer, still in {source.parent}, and a later "
            f"--reaggregate would read it as this model's result",
            file=sys.stderr,
        )
        return None
    detail = reason or "was there before this slot started and is unchanged, an earlier run's answer"
    print(
        f"[RESULT_STALE] {source.name} {detail}: set aside as {target.name} so "
        f"nothing reads it as this run's (nothing was deleted)"
    )
    return target


def set_aside_rejected_result(path: os.PathLike | str, *, reason: str) -> Optional[Path]:
    """Rename a refused ``<stem>.json`` to ``<stem>.json.rejected`` and note it.

    For a result the round will not save or read; *reason* is the clause
    after the file name in the note. A file-capable provider writes
    ``<stem>.json`` itself, before the round saves the reply, and a file left
    there is read as the model's result by every later step (``--reaggregate``,
    the salvage recovery's ``exists()``, a resume's skip). Renamed like
    :func:`set_aside_stale_result`, never deleted, ``.<stamp>`` appended when
    the target exists; the note goes to ``result_notes``
    (``**Result files:**``). No file to rename returns ``None`` quietly; a
    failed rename warns on stderr and returns ``None``.
    """
    return _set_aside_refused(path, REJECTED_RESULT_SUFFIX, reason)


def set_aside_unchecked_result(path: os.PathLike | str, *, reason: str) -> Optional[Path]:
    """:func:`set_aside_rejected_result` for the file of a slot that ended
    before its safety checks passed: renamed ``<stem>.json.unchecked``."""
    return _set_aside_refused(path, UNCHECKED_RESULT_SUFFIX, reason)


def _set_aside_refused(path: os.PathLike | str, suffix: str, reason: str) -> Optional[Path]:
    source = Path(path)
    if not os.path.lexists(source):
        return None
    target = source.with_name(f"{source.name}.{suffix}")
    if os.path.lexists(target):
        target = target.with_name(
            f"{target.name}.{datetime.now().strftime('%Y%m%dT%H%M%S%f')}"
        )
    try:
        os.replace(source, target)
    except OSError as exc:
        print(
            f"Warning: could not set {source.name} aside ({exc}); it {reason}, "
            f"and it is still in {source.parent}",
            file=sys.stderr,
        )
        return None
    note = f"{source.name} {reason}; set aside as {target.name} (nothing was deleted)"
    print(note)
    append_result_note(source.parent, note)
    return target


#: :attr:`Withheld.key` of every model while ``.status.json`` exists but
#: cannot be read (:func:`withheld_models`): not a checkpoint key.
UNREADABLE_CHECKPOINT = "unreadable"

#: Its reason.
UNREADABLE_CHECKPOINT_REASON = ".status.json could not be read"

CheckpointUnreadable = _status_file.CheckpointUnreadable


def _recorded_in(status: Optional[Dict[str, object]], key: str) -> Dict[str, str]:
    recorded = (status or {}).get(key)
    if not isinstance(recorded, dict):
        return {}
    return {str(spec): str(reason) for spec, reason in recorded.items()}


def recorded_models(phase_dir: Optional[os.PathLike | str], key: str) -> Dict[str, str]:
    """The phase's recorded ``{model_spec: reason}`` under *key*: ``{}`` when
    there is no checkpoint, or one without the key (an older one).

    Raises :class:`CheckpointUnreadable` when the checkpoint exists but cannot
    be read: the caller writes these maps back, or decides on them, and an
    empty map in place of an unread one would drop every record in it.
    """
    if not phase_dir:
        return {}
    return _recorded_in(_status_file.load_status(str(phase_dir)), key)


def _recovery_in(status: Optional[Dict[str, object]]) -> Optional[Dict[str, object]]:
    """The :data:`RECOVERED_KEY` record of *status*, as
    ``{"reason": str, "accepted": [...]}``, or ``None`` when it has none. A
    record of the wrong shape still withholds every model: only a list names
    an accepted model."""
    if not status or RECOVERED_KEY not in status:
        return None
    value = status.get(RECOVERED_KEY)
    record = value if isinstance(value, dict) else {}
    reason = record.get("reason")
    accepted = record.get(ACCEPTED_FIELD)
    return {
        "reason": str(reason) if isinstance(reason, str) and reason else RECOVERED_REASON,
        ACCEPTED_FIELD: (sorted({str(spec) for spec in accepted})
                         if isinstance(accepted, list) else []),
    }


def recovery_record(reason: str = RECOVERED_REASON) -> Dict[str, object]:
    """A fresh :data:`RECOVERED_KEY` record: every model withheld, none accepted."""
    return {"reason": reason, ACCEPTED_FIELD: []}


def recorded_recovery(phase_dir: Optional[os.PathLike | str]) -> Optional[Dict[str, object]]:
    """The phase's :data:`RECOVERED_KEY` record, or ``None`` (no checkpoint,
    or one never recovered). Raises :class:`CheckpointUnreadable`, as
    :func:`recorded_models` does."""
    if not phase_dir:
        return None
    return _recovery_in(_status_file.load_status(str(phase_dir)))


def phase_recovered(phase_dir: Optional[os.PathLike | str]) -> bool:
    """Whether the phase's checkpoint carries a :data:`RECOVERED_KEY` record.
    ``False`` with no checkpoint, one never recovered, or one that cannot be
    read: every reader withholds every model over that one already
    (:class:`WithheldModels`)."""
    try:
        return recorded_recovery(phase_dir) is not None
    except CheckpointUnreadable:
        return False


def recorded_withheld(
    phase_dir: os.PathLike | str, *, attempts: int = 1,
) -> Dict[str, Dict[str, object]]:
    """Both withheld maps, ``{key: {model_spec: reason}}`` for each of
    :data:`WITHHELD_KEYS`, from one read of the checkpoint (``{}`` for each
    with no checkpoint, or an older one), and the :data:`RECOVERED_KEY` record
    under its key when the checkpoint has one. Raises
    :class:`CheckpointUnreadable` when the checkpoint cannot be read on any of
    *attempts* reads (``status_file.load_status``): a writer that carries the
    maps over writes them whole or not at all."""
    status = _status_file.load_status(str(phase_dir), attempts=attempts)
    recorded: Dict[str, Dict[str, object]] = {
        key: dict(_recorded_in(status, key)) for key in WITHHELD_KEYS
    }
    recovery = _recovery_in(status)
    if recovery is not None:
        recorded[RECOVERED_KEY] = recovery
    return recorded


def rejected_models(phase_dir: Optional[os.PathLike | str]) -> Dict[str, str]:
    """The phase's recorded ``{model_spec: reason}`` of rejected slots
    (:func:`recorded_models`)."""
    return recorded_models(phase_dir, REJECTED_MODELS_KEY)


def unchecked_models(phase_dir: Optional[os.PathLike | str]) -> Dict[str, str]:
    """The phase's recorded ``{model_spec: reason}`` of unchecked slots
    (:func:`recorded_models`)."""
    return recorded_models(phase_dir, UNCHECKED_MODELS_KEY)


class Withheld(NamedTuple):
    """Why a model's answer is withheld: the ``.status.json`` *key* that
    records it (one of :data:`WITHHELD_KEYS`, :data:`RECOVERED_KEY`, or
    :data:`UNREADABLE_CHECKPOINT` when no record can be read) and the
    *reason*."""

    key: str
    reason: str

    @property
    def rejected(self) -> bool:
        return self.key == REJECTED_MODELS_KEY

    @property
    def phrase(self) -> str:
        """What the model's slot did, after "a slot that"."""
        if self.rejected:
            return "failed its safety checks"
        if self.key == UNCHECKED_MODELS_KEY:
            if self.reason == UNFINISHED_ANSWER_REASON:
                return "left an unfinished answer"
            return "ended before its safety checks passed"
        if self.key == RECOVERED_KEY:
            return ("is not one this run produced, in a phase whose damaged "
                    "checkpoint was replaced")
        return "cannot be shown to have passed its safety checks"

    def note(self, model_spec: str) -> str:
        """The clause after one of the model's files' names in its note."""
        return (
            f"is not {model_spec}'s result: its slot {self.phrase} "
            f"({plain_line(self.reason)})"
        )

    def set_aside(self, path: os.PathLike | str, model_spec: str) -> Optional[Path]:
        """*path* renamed ``.json.rejected`` or ``.json.unchecked`` (a
        :data:`RECOVERED_KEY` file too: nothing on disk is trusted there) and
        noted. Under :data:`UNREADABLE_CHECKPOINT` nothing is renamed
        (``None``): the file is only left unread while the checkpoint cannot
        be read."""
        if self.rejected:
            return set_aside_rejected_result(path, reason=self.note(model_spec))
        if self.key in (UNCHECKED_MODELS_KEY, RECOVERED_KEY):
            return set_aside_unchecked_result(path, reason=self.note(model_spec))
        return None


#: :meth:`WithheldModels.get`'s answer for every model while the checkpoint
#: cannot be read.
UNREADABLE = Withheld(UNREADABLE_CHECKPOINT, UNREADABLE_CHECKPOINT_REASON)


class WithheldModels:
    """:func:`withheld_models`' answer: the models the phase withholds.

    Read like a mapping of ``{model_spec: Withheld}`` (``in``, ``get``,
    ``[]``, truth). When the checkpoint exists but could not be read
    (``unreadable``) every model is withheld, by :data:`UNREADABLE`: a read
    failure never passes for a checkpoint that records nothing, which is what
    lets a model's answer through. A checkpoint a fresh run recovered
    (*recovered*, from :data:`RECOVERED_KEY`) withholds every model too,
    whatever its files hold, named by a map's record first, but the ones the
    operator *accepted*. :meth:`recorded` is the narrower question a writer
    asks: whether a readable checkpoint records the model.
    """

    def __init__(self, models: Optional[Dict[str, Withheld]] = None, *,
                 unreadable: bool = False, recovered: Optional[Withheld] = None,
                 accepted: Iterable[str] = ()) -> None:
        self.models: Dict[str, Withheld] = dict(models or {})
        self.unreadable = unreadable
        self.recovered = recovered
        self.accepted = frozenset(accepted)

    def get(self, model_spec: str) -> Optional[Withheld]:
        if self.unreadable:
            return UNREADABLE
        withheld = self.models.get(model_spec)
        if (withheld is None and self.recovered is not None
                and model_spec not in self.accepted):
            return self.recovered
        return withheld

    def __contains__(self, model_spec: object) -> bool:
        return isinstance(model_spec, str) and self.get(model_spec) is not None

    def __getitem__(self, model_spec: str) -> Withheld:
        withheld = self.get(model_spec)
        if withheld is None:
            raise KeyError(model_spec)
        return withheld

    def __bool__(self) -> bool:
        return self.unreadable or bool(self.models) or self.recovered is not None

    def recorded(self, model_spec: str) -> bool:
        """Whether the checkpoint, read, records *model_spec* as withheld."""
        return not self.unreadable and self.get(model_spec) is not None

    def owner(self, stem: str) -> Optional[str]:
        """The withheld spec a result file named *stem* would be read as, if
        any (its anchored or pre-anchor stem, as
        :func:`set_aside_unrecorded_results` matches them); *stem* itself
        while the checkpoint cannot be read, and in a recovered phase unless
        an accepted model's own stem is *stem*."""
        if self.unreadable:
            return stem
        recorded = next(
            (spec for spec in self.models if stem in _claimed_stems([spec])), None,
        )
        if recorded is not None or self.recovered is None:
            return recorded
        if any(sanitize_model_name(spec) == stem for spec in self.accepted):
            return None
        return stem


def withheld_models(phase_dir: Optional[os.PathLike | str]) -> WithheldModels:
    """Every model whose answer the phase withholds, from one read of
    ``.status.json``: ``models_rejected`` and ``models_unchecked``, a model in
    both named by its rejection, and, in a phase whose damaged checkpoint a
    fresh run replaced (:data:`RECOVERED_KEY`), every model the operator did
    not accept, whatever its files hold. A checkpoint that records none of
    them (an older one, or a phase that never dispatched) withholds nothing,
    and so does no checkpoint; one that exists but cannot be read withholds
    every model (:class:`WithheldModels`)."""
    if not phase_dir:
        return WithheldModels()
    try:
        status = _status_file.load_status(str(phase_dir))
    except CheckpointUnreadable:
        return WithheldModels(unreadable=True)
    withheld: Dict[str, Withheld] = {}
    for key in reversed(WITHHELD_KEYS):
        withheld.update(
            {spec: Withheld(key, reason) for spec, reason in _recorded_in(status, key).items()}
        )
    recovery = _recovery_in(status)
    if recovery is None:
        return WithheldModels(withheld)
    return WithheldModels(
        withheld, recovered=Withheld(RECOVERED_KEY, str(recovery["reason"])),
        accepted=recovery[ACCEPTED_FIELD],  # type: ignore[arg-type]
    )


def _record_model(phase_dir: os.PathLike | str, key: str, model_spec: str, reason: str) -> bool:
    # Into the checkpoint a fan-out's round opened only, never into a folder
    # no round opened (a direct call of a slot function); and never over a
    # checkpoint this cannot read, whose records the write would drop.
    phase_dir = str(phase_dir)
    with _status_file.checkpoint_lock(phase_dir):
        try:
            status = _status_file.load_status(phase_dir)
        except CheckpointUnreadable:
            return False
        if status is None:
            return False
        recorded = _recorded_in(status, key)
        if recorded.get(model_spec) != reason:
            recorded[model_spec] = reason
            if key == REJECTED_MODELS_KEY:
                _status_file.update_status(phase_dir, {REJECTED_MODELS_KEY: recorded})
            else:
                _status_file.update_status(phase_dir, {UNCHECKED_MODELS_KEY: recorded})
    try:
        return recorded_models(phase_dir, key).get(model_spec) == reason
    except CheckpointUnreadable:
        return False


def record_rejected_model(phase_dir: os.PathLike | str, model_spec: str, reason: str) -> bool:
    """Add *model_spec* to ``.status.json``'s ``models_rejected``; whether it is there now.

    One read-modify-write under the checkpoint lock, as :func:`append_result_note`.
    The status writers are best-effort, so the record is read back: ``False``
    means this write did not land, and the caller looks for another record
    (:meth:`WithheldModels.recorded`) before it warns. A *phase_dir* without
    a ``.status.json`` (no round opened there), or with one that cannot be
    read, is ``False`` too, and nothing is written.
    """
    return _record_model(phase_dir, REJECTED_MODELS_KEY, model_spec, reason)


def record_unchecked_model(phase_dir: os.PathLike | str, model_spec: str, reason: str) -> bool:
    """:func:`record_rejected_model` for ``models_unchecked``."""
    return _record_model(phase_dir, UNCHECKED_MODELS_KEY, model_spec, reason)


def clear_unchecked_model(phase_dir: os.PathLike | str, model_spec: str) -> bool:
    """Take *model_spec* out of ``models_unchecked``; whether it is out now
    (read back, as :func:`record_rejected_model`). ``True`` with no
    checkpoint; ``False``, writing nothing, over one that cannot be read."""
    phase_dir = str(phase_dir)
    with _status_file.checkpoint_lock(phase_dir):
        try:
            status = _status_file.load_status(phase_dir)
        except CheckpointUnreadable:
            return False
        if status is None:
            return True
        recorded = _recorded_in(status, UNCHECKED_MODELS_KEY)
        if model_spec in recorded:
            del recorded[model_spec]
            _status_file.update_status(phase_dir, {UNCHECKED_MODELS_KEY: recorded})
    try:
        return model_spec not in unchecked_models(phase_dir)
    except CheckpointUnreadable:
        return False


def clear_withheld_model(phase_dir: os.PathLike | str, model_spec: str) -> bool:
    """Take *model_spec* out of both withheld maps and, in a recovered phase,
    add it to :data:`RECOVERED_KEY`'s ``accepted``; whether both hold now
    (read back). For the operator's own choice only, never a slot's: ask's
    ``--accept-partial`` counting a withheld model's partial. ``accepted``
    says the operator counted it, never that its checks passed: the model's
    next checked attempt drops it (``review_lane.withheld_record``). ``True``
    with no checkpoint; ``False``, writing nothing, over one that cannot be
    read."""
    phase_dir = str(phase_dir)
    with _status_file.checkpoint_lock(phase_dir):
        try:
            status = _status_file.load_status(phase_dir)
        except CheckpointUnreadable:
            return False
        if status is None:
            return True
        rejected = _recorded_in(status, REJECTED_MODELS_KEY)
        unchecked = _recorded_in(status, UNCHECKED_MODELS_KEY)
        recovery = _recovery_in(status)
        updates: Dict[str, object] = {}
        if model_spec in rejected or model_spec in unchecked:
            rejected.pop(model_spec, None)
            unchecked.pop(model_spec, None)
            updates.update({REJECTED_MODELS_KEY: rejected, UNCHECKED_MODELS_KEY: unchecked})
        if recovery is not None and model_spec not in recovery[ACCEPTED_FIELD]:  # type: ignore[operator]
            updates[RECOVERED_KEY] = {
                **recovery,
                ACCEPTED_FIELD: sorted({*recovery[ACCEPTED_FIELD], model_spec}),  # type: ignore[misc]
            }
        if updates:
            _status_file.update_status(phase_dir, updates)
    try:
        recorded = recorded_withheld(phase_dir)
    except CheckpointUnreadable:
        return False
    recovery = recorded.get(RECOVERED_KEY)
    return not any(model_spec in recorded[key] for key in WITHHELD_KEYS) and (
        recovery is None or model_spec in recovery[ACCEPTED_FIELD]  # type: ignore[operator]
    )


def rejected_result_note(model_spec: str, reason: str) -> str:
    """The clause after a rejected slot's file name in its set-aside note."""
    return Withheld(REJECTED_MODELS_KEY, reason).note(model_spec)


def withhold_results(
    phase_dir: os.PathLike | str, result_files: Sequence[str]
) -> List[str]:
    """The files of *result_files* no withheld model owns; the rest are never read.

    A file a model of :func:`withheld_models` would be read from is set aside
    again (``.json.rejected`` or ``.json.unchecked``) and left out whether or
    not the rename works: the record is what keeps it out, so a set-aside that
    failed when the slot ended fails closed here. While the checkpoint cannot
    be read, every file is left out and none is renamed.
    """
    phase_dir = str(phase_dir)
    withheld = withheld_models(phase_dir)
    if not withheld:
        return list(result_files)
    kept: List[str] = []
    for path in result_files:
        name = os.path.basename(path)
        stem = name[: -len(".json")] if name.endswith(".json") else name
        owner = withheld.owner(stem)
        if owner is None:
            kept.append(path)
            continue
        if withheld[owner].set_aside(path, owner) is None:
            print(f"{name} {withheld[owner].note(owner)}; left in place and not read")
    return kept


def misnamed_result_note(model_spec: str, wrote: str, expected: str) -> str:
    """The one sentence a slot says when it read a misnamed result."""
    return (
        f"{model_spec} wrote its result to {wrote} instead of {expected}; "
        f"read it from there and renamed it to {expected}"
    )


def set_aside_note(
    name: str, target: str, recorded_specs: Sequence[str],
    *, rename_failed: Optional[str] = None,
) -> str:
    """The one sentence the aggregate says about a result file it left out.

    *rename_failed* is why the rename to *target* failed: the file is then
    left where it is, and the sentence says so (review of fix round 24: it
    said "renamed it to <its own name>" on every surface).
    """
    head = (
        f"{name} is not the result file of any model this review ran "
        f"({', '.join(recorded_specs)}), so its findings are left out of the "
        f"report; "
    )
    if rename_failed is not None:
        return f"{head}left in place (rename failed: {plain_line(rename_failed)})"
    return f"{head}renamed it to {target} (nothing was deleted)"


def append_result_note(phase_dir: os.PathLike | str, note: str) -> None:
    """Add *note* to ``.status.json``'s ``result_notes`` once. Best-effort.

    One read-modify-write under the checkpoint lock, so two slots finishing at
    once cannot drop each other's note.
    """
    phase_dir = str(phase_dir)
    if not os.path.isdir(phase_dir):
        return
    with _status_file.checkpoint_lock(phase_dir):
        notes = _status_file.read_status(phase_dir).get(RESULT_NOTES_KEY)
        notes = [str(n) for n in notes] if isinstance(notes, list) else []
        if note in notes:
            return
        notes.append(note)
        _status_file.update_status(phase_dir, {RESULT_NOTES_KEY: notes})
    publish_result_notes(phase_dir)


def publish_result_notes(phase_dir: os.PathLike | str) -> None:
    """Re-publish the recorded notes as ``progress.notes``. Best-effort.

    ``progress.notes`` is what ``status`` prints as ``note:`` lines and a
    terminal poll carries into its ``notice`` — the only result line a tool
    route reads. A detached ``--reaggregate`` claims the dir and drops the
    previous ``progress``, so each reaggregate puts the notes back.
    """
    notes = result_notes(phase_dir)
    if notes:
        _publish(str(phase_dir), notes)


def _publish(phase_dir: str, notes: List[str]) -> None:
    try:
        # Imported here to keep resume_state, which loads this module, light.
        from . import run_record as _run_record
        _run_record.report_progress(phase_dir, notes=list(notes))
    except Exception:  # noqa: BLE001 - reporting never fails a slot
        pass


def result_notes(phase_dir: Optional[os.PathLike | str]) -> List[str]:
    """The phase's recorded notes about its result files (``[]`` when none)."""
    if not phase_dir:
        return []
    notes = _status_file.read_status(str(phase_dir)).get(RESULT_NOTES_KEY)
    return [str(n) for n in notes] if isinstance(notes, list) else []


def result_notes_line(phase_dir: Optional[os.PathLike | str]) -> Optional[str]:
    """``report.md``'s ``**Result files:**`` line, or ``None`` with no notes."""
    notes = result_notes(phase_dir)
    if not notes:
        return None
    return "**Result files:** " + "; ".join(notes)


def recorded_model_specs(phase_dir: os.PathLike | str) -> List[str]:
    """The models this phase's ``.status.json`` says the review ran.

    ``models_requested`` (with any ``models_failed`` key beside it) when the
    checkpoint has it; else the union of ``models_completed`` and
    ``models_failed`` for a checkpoint that never got the field. Not
    ``models_completed`` beside a ``models_requested``: before the aggregate
    learned to set strays aside, a ``--reaggregate`` appended a stray file's
    *stem* there (``record_models_present``), and that entry is exactly what
    must not vouch for the file. ``[]`` when nothing is recorded.
    """
    status = _status_file.read_status(str(phase_dir))
    failed = status.get("models_failed")
    failed_specs = [str(k) for k in failed] if isinstance(failed, dict) else []
    requested = status.get("models_requested")
    if isinstance(requested, list) and requested:
        base = [str(s) for s in requested]
    else:
        completed = status.get("models_completed")
        base = [str(s) for s in completed] if isinstance(completed, list) else []
    specs: List[str] = []
    for spec in base + failed_specs:
        if spec not in specs:
            specs.append(spec)
    return specs


def _claimed_stems(specs: Iterable[str]) -> set:
    """Every stem a recorded spec's result can have: anchored and pre-anchor."""
    stems = set()
    for spec in specs:
        stems.add(sanitize_model_name(spec))
        if ":" in spec:
            stems.add(sanitize_model_name(spec.split(":", 1)[1]))
    return stems


#: How a candidate result file is opened: never through a link (a link
#: swapped in after the ``lstat`` fails the open with ``ELOOP``), and never
#: blocking on a FIFO. ``getattr`` because Windows has neither flag; the
#: identity check in :func:`read_regular_text` covers it there.
_NO_FOLLOW_OPEN_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_NOFOLLOW", 0)
    | getattr(os, "O_NONBLOCK", 0)
    | getattr(os, "O_CLOEXEC", 0)
    | getattr(os, "O_BINARY", 0)
)

#: ``(st_dev, st_ino)`` of a file :func:`read_regular_text` read.
FileIdentity = Tuple[int, int]


def read_regular_text(path: os.PathLike | str) -> Optional[Tuple[str, FileIdentity]]:
    """*path*'s UTF-8 text and identity, when it is a regular file; else ``None``.

    Checked and read through one descriptor (review of fix round 24): the
    ``lstat`` says a regular file, the open never follows a link, and the
    opened descriptor is ``fstat``-ed as a regular file with the ``lstat``'s
    identity, so a link or a FIFO swapped in between the check and the open is
    never read. A file that is not UTF-8 is ``None`` too.
    """
    try:
        before = os.lstat(path)
    except OSError:
        return None
    if not stat.S_ISREG(before.st_mode):
        return None
    try:
        fd = os.open(path, _NO_FOLLOW_OPEN_FLAGS)
    except OSError:
        return None
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or (
            (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)
        ):
            return None
        chunks = []
        while True:
            chunk = os.read(fd, 1 << 20)
            if not chunk:
                break
            chunks.append(chunk)
    except OSError:
        return None
    finally:
        os.close(fd)
    try:
        text = b"".join(chunks).decode("utf-8")
    except UnicodeDecodeError:
        return None
    return text, (opened.st_dev, opened.st_ino)


def is_same_regular_file(path: os.PathLike | str, identity: FileIdentity) -> bool:
    """Whether *path* is, now, the regular file :func:`read_regular_text` read."""
    try:
        st = os.lstat(path)
    except OSError:
        return False
    return stat.S_ISREG(st.st_mode) and (st.st_dev, st.st_ino) == tuple(identity)


def _is_result_list(path: str) -> bool:
    """A regular file (not a link, not a FIFO) holding one JSON array."""
    read = read_regular_text(path)
    if read is None:
        return False
    try:
        return isinstance(json.loads(read[0]), list)
    except (ValueError, RecursionError):
        # Nested deeper than the decoder's stack: not a list it can read.
        return False


def set_aside_unrecorded_results(
    phase_dir: os.PathLike | str, result_files: Sequence[str]
) -> List[str]:
    """The files of *result_files* a recorded model owns; set the rest aside.

    With no recorded model (no ``.status.json``, or one with none of the
    fields) every file is kept: nothing says which models ran, and a hand-copied
    dir keeps its old stem-as-identity reading. Otherwise a file whose stem is
    no recorded spec's anchored or pre-anchor stem is never read: a JSON list is
    renamed ``<name>.set-aside`` (``.<stamp>`` appended on a collision) and
    noted; anything else is left where it is and named. A set-aside stem that an
    earlier reaggregate appended to ``models_completed`` is taken back out.
    """
    phase_dir = str(phase_dir)
    recorded = recorded_model_specs(phase_dir)
    if not recorded:
        return list(result_files)
    claimed = _claimed_stems(recorded)
    kept: List[str] = []
    set_aside_stems: List[str] = []
    for path in result_files:
        name = os.path.basename(path)
        stem = name[: -len(".json")] if name.endswith(".json") else name
        if stem in claimed:
            kept.append(path)
            continue
        if not _is_result_list(path):
            print(
                f"[RESULT_NOT_READ] {name} is not a result file of any model this "
                f"review ran ({', '.join(recorded)}); left where it is and not read"
            )
            continue
        target = f"{path}.{SET_ASIDE_SUFFIX}"
        if os.path.exists(target):
            target = f"{target}.{datetime.now().strftime('%Y%m%dT%H%M%S%f')}"
        rename_failed: Optional[str] = None
        try:
            os.replace(path, target)
        except OSError as exc:
            print(
                f"Warning: could not set {name} aside ({exc}); it is still in "
                f"{phase_dir} but is not read as a model's result",
                file=sys.stderr,
            )
            rename_failed = exc.strerror or str(exc) or type(exc).__name__
        note = set_aside_note(
            name, os.path.basename(target), recorded, rename_failed=rename_failed,
        )
        print(f"[RESULT_SET_ASIDE] {note}")
        append_result_note(phase_dir, note)
        set_aside_stems.append(stem)
    if set_aside_stems:
        _forget_completed(phase_dir, set_aside_stems, recorded)
    return kept


def _forget_completed(phase_dir: str, stems: Sequence[str], recorded: Sequence[str]) -> None:
    """Drop set-aside stems an earlier reaggregate recorded as completed models.

    Everywhere ``status`` reads a model from: ``models_completed``, the stem's
    ``progress.models`` row, and the two counters derived from them. A
    pre-round-24 ``--reaggregate`` wrote ``models_succeeded`` as the length of
    ``models_completed`` with the stem in it, and a foreground reaggregate keeps
    ``progress`` (only a detached one's claim drops it), so ``status`` read
    "3 ok" beside a report of two models (review of fix round 24). With the
    per-model map, both counters are re-derived from it as the fan-out derives
    them (a terminal row is done, a ``done`` row succeeded); without one,
    ``models_succeeded`` is recounted by the rule that wrote it.
    """
    forget = {stem for stem in stems if stem not in recorded}
    with _status_file.checkpoint_lock(phase_dir):
        status = _status_file.read_status(phase_dir)
        completed = status.get("models_completed")
        dropped = False
        if isinstance(completed, list):
            kept = [m for m in completed if m not in forget]
            if kept != completed:
                _status_file.update_status(phase_dir, {"models_completed": kept})
                dropped = True
        progress = status.get("progress")
        if not isinstance(progress, dict):
            return
        models_map = progress.get("models")
        if isinstance(models_map, dict):
            rows = {k: v for k, v in models_map.items() if k not in forget}
            if len(rows) == len(models_map) and not dropped:
                return
            entries = [e for e in rows.values() if isinstance(e, dict)]
            _status_file.update_progress(phase_dir, {
                "models": rows,
                "models_done": sum(
                    1 for e in entries if e.get("state") in _status_file.TERMINAL_STATES
                ),
                "models_succeeded": sum(
                    1 for e in entries if e.get("state") == _status_file.STATE_DONE
                ),
            })
        elif dropped and progress.get("models_total") and isinstance(
            progress.get("models_succeeded"), int
        ):
            _status_file.update_progress(phase_dir, {"models_succeeded": len(kept)})
