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
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from . import progress_tracker as _progress
from . import status_file as _status_file
from .json_extractor import sanitize_model_name
from .text_clip import plain_line

#: Basenames that are never a per-model result file: every artifact a phase dir
#: holds that is also a ``*.json``. The union of what the two reaggregate globs
#: exclude, so a retire-by-selection can never rename a file those would not
#: have read as a model. (Re-exported by ``review_orchestrator_base``.)
NON_MODEL_JSON_MARKERS = (
    'grouped', 'validation', 'salvage', 'revalidation', 'consolidated',
    'consolidation', 'issues', 'fix_tasks', 'report_data', 'subagent_batch_report',
    'subagent_dry_run', 'write_batch_report', 'write_tasks',
)

#: Suffix a result file no recorded model owns is renamed with.
SET_ASIDE_SUFFIX = "set-aside"

#: Suffix the previous round's ``<stem>.json`` is renamed with when a slot found
#: it there, unchanged since the slot started (:func:`set_aside_stale_result`).
#: The name no longer ends in ``.json``, so no reader of a phase dir's results
#: matches it: neither reaggregate's ``*.json`` glob (and so neither
#: :func:`set_aside_unrecorded_results`), nor :func:`snapshot_candidates`, nor
#: the salvage recovery loop's ``exists(<stem>.json)``, nor a resume's skip.
STALE_RESULT_SUFFIX = "stale-earlier-run"

#: ``.status.json`` key holding the phase's notes about its result files.
RESULT_NOTES_KEY = "result_notes"

#: ``{name: (mtime_ns, size)}`` of a phase dir's candidate files.
Snapshot = Dict[str, Tuple[int, int]]


def _is_candidate_name(name: str) -> bool:
    return (
        name.endswith(".json")
        and not name.startswith(".")
        and not any(marker in name for marker in NON_MODEL_JSON_MARKERS)
    )


def snapshot_candidates(phase_dir: os.PathLike | str) -> Snapshot:
    """What could be a result file in *phase_dir* now, with its mtime and size."""
    snapshot: Snapshot = {}
    try:
        entries = list(os.scandir(phase_dir))
    except OSError:
        return snapshot
    for entry in entries:
        if not _is_candidate_name(entry.name):
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


def set_aside_stale_result(path: os.PathLike | str) -> Optional[Path]:
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
    print(
        f"[RESULT_STALE] {source.name} was there before this slot started and "
        f"is unchanged, an earlier run's answer: set aside as {target.name} so "
        f"nothing reads it as this run's (nothing was deleted)"
    )
    return target


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
        from . import detach as _detach
        _detach.report_progress(phase_dir, notes=list(notes))
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
    except ValueError:
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
                    1 for e in entries if e.get("state") in _progress.TERMINAL_STATES
                ),
                "models_succeeded": sum(
                    1 for e in entries if e.get("state") == _progress.STATE_DONE
                ),
            })
        elif dropped and progress.get("models_total") and isinstance(
            progress.get("models_succeeded"), int
        ):
            _status_file.update_progress(phase_dir, {"models_succeeded": len(kept)})
