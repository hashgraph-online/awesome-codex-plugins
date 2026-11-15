"""A cascade's forward ledger: what earlier rounds rejected and what they changed.

``--cascade`` (``utils/improve_cascade.py``) runs one review-then-apply round
per model. From the second round on, the reviewers, the validators and the
judge are told what earlier rounds rejected or held back (so they do not raise
it again without a new argument) and what earlier rounds changed (so they
check those edits instead of taking them for the author's intent).

The ledger is built from the **archived** stages only
(``stage-<j>/artifacts/``, published once at close-out by
``utils/cascade_archive.py`` and sealed by its ``.complete.json``). Never from
the live phase dirs, which the next round's ``--force --rerun-all`` replaces,
and never from ``state.json``, whose per-phase maps keep one record per group
id, so a later write overwrites an earlier round's. Each stage's archive holds
its own ``records.json``, extracted at close-out before anything later could
overwrite it.

:func:`freeze_inputs` writes a stage's ledger files under
``stage-<k>/inputs/`` at the stage's start, with the manifest
(``cascade_provenance.write_manifest``) **last**: once the manifest exists
nothing in ``inputs/`` is rewritten, so every call of the stage's rounds, and
the archive, read the same bytes. Rendering is pure and deterministic: the
same archives give the same bytes.

This module also owns the reading of a published stage (:func:`read_complete`,
:func:`load_stage`), which ``cascade_archive`` imports, and the contained
writes under a cascade dir (:func:`write_file`, :func:`remove_tree`), which go
through the plan-output containment helpers ``status_file.write_status`` uses
(``held_folder``), never a raw join.

The developer contract: docs/development/workflows.md, "A cascade
(``--cascade``)".
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union

import modes as mode_table

from . import cascade_provenance as provenance
from . import importance as _importance
from .held_folder import OutsidePlanDir, anchor_plan_dir, plan_dir_of, remove_in_plan_dir
from .held_folder import write_in_plan_dir
from .judge_vocab import canonical_value
from .output_handler import PHASE_DIRECTORIES, output_dir_path
from .text_clip import clip

PathLike = Union[str, "os.PathLike[str]"]

#: The most characters an inline ledger block (the reviewer's, the
#: validator's, the judge's) may hold, its fixed wording and overflow line
#: included. Over it, the most important entries are kept
#: (:func:`_select`) and a line counts the rest.
LEDGER_INLINE_MAX_CHARS = 8000

#: What one entry's fields are cut to (``text_clip.clip``: at a word, marked).
TITLE_LIMIT = 120
DESCRIPTION_LIMIT = 240
REASON_LIMIT = 200
LOCATION_LIMIT = 200

#: A stage's directories under the cascade dir.
INPUTS = "inputs"
ARTIFACTS = "artifacts"
PARTIAL = "artifacts.partial"

#: The publication mark, written last inside ``artifacts.partial/``.
COMPLETE_NAME = ".complete.json"
COMPLETE_SCHEMA_VERSION = 1

#: The derived files a close-out writes beside the copied phase dirs.
RECORDS_NAME = "records.json"
RECORDS_SCHEMA_VERSION = 1
PLAN_AFTER = "plan.after.md"
STAGE_DIFF = "stage.diff"
FILES_TOUCHED = "files-touched.txt"

#: The cascade dir's own files this module reads.
START_PLAN = "start.md"
RECORD_NAME = "record.json"

#: The two composites a cascade runs on.
MODES = ("improve-plan", "improve-code")

#: The label a scope deferral's reason carries in the rejected-or-held-back
#: list. A deferral is a valid finding the ``preserve`` scope policy kept out
#: of the apply, not a rejection, so the label says so, and when it may be
#: raised again, for every reviewer, validator and judge that reads it.
SCOPE_LABEL = ("held back by the scope policy (valid, not applied; raise it again "
               "only if the scope now allows it)")

#: The judge's ``batch_context.decision_source`` values (legacy spellings are
#: folded by ``judge_vocab.canonical_value``).
JUDGE_SOURCE = "judge_auto_decide"
JUDGE_SALVAGE_SOURCE = "judge_auto_decide_salvage"


class ArchiveRefusal(Exception):
    """A cascade archive or input that cannot be trusted or written; exit 3.

    ``message`` is the whole text to print on stderr. Re-exported as
    ``cascade_archive.ArchiveRefusal``, the name the cascade core catches.
    """

    code = 3

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


# ---------------------------------------------------------------------------
# The mode's phase dirs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Phases:
    """A composite's review and apply phase words and their dir names."""

    mode: str
    run_phase: str
    review_phase: str
    apply_phase: str
    review_dir: str
    apply_dir: str


def phases(mode: str) -> Phases:
    """The review and apply of *mode* (``improve-plan`` or ``improve-code``).

    Read off the modes table (``sequence_phases``) and mapped through
    ``output_handler.PHASE_DIRECTORIES`` (``apply-code-fixes`` lives in
    ``apply-fixes/``), so the pair is never typed a second time.
    """
    row = mode_table.resolve(str(mode))
    if row is None or row.name not in MODES:
        raise ValueError(f"{mode!r} is not a mode a cascade runs on")
    review_phase, apply_phase = row.sequence_phases
    return Phases(
        mode=row.name,
        run_phase=row.phase,
        review_phase=review_phase,
        apply_phase=apply_phase,
        review_dir=PHASE_DIRECTORIES.get(review_phase, review_phase),
        apply_dir=PHASE_DIRECTORIES.get(apply_phase, apply_phase),
    )


def stage_dir(cascade_dir: PathLike, stage: int) -> Path:
    """``<cascade_dir>/stage-<stage>``: named by index, not model, to keep
    archived paths short (Windows path length)."""
    return Path(os.path.abspath(str(cascade_dir))) / f"stage-{int(stage)}"


# ---------------------------------------------------------------------------
# Small readers
# ---------------------------------------------------------------------------

def read_json(path: PathLike) -> Any:
    """*path*'s JSON value, or ``None`` when it is missing or unreadable."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def _dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def sha256_file(path: PathLike) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def grouped_hash(path: PathLike) -> str:
    """The review stamp of a ``grouped.json``: the 16-hex content hash an apply
    batch records as ``inputs.grouped_sha256`` and every processed record as
    ``details.grouped_sha256`` (``subagent_tasks.file_content_hash``, the same
    function, so the two always compare); ``""`` when there is no file."""
    # Imported here: subagent_tasks is a heavy module the renderers never need.
    from .subagent_tasks import file_content_hash

    return file_content_hash(str(path))


# ---------------------------------------------------------------------------
# Contained writes below the plan's directory
# ---------------------------------------------------------------------------

def anchor_cascade_dir(cascade_dir: PathLike) -> None:
    """Anchor the plan directory *cascade_dir* lives below, for the writes.

    A cascade dir is ``<plan dir>/<stem>/<composite>/cascades/<name>``, and
    ``output_handler.output_dir_path`` anchors ``<plan dir>`` (the plan's own
    folder) as the root every plan-output write is held from. A caller handed
    only the cascade dir (``render_summary``) anchors the same folder here;
    one whose layout is not that one (a tool, a test) is written by path, as
    ``held_folder.write_in_plan_dir`` writes any file below no anchored root.
    """
    path = Path(os.path.abspath(str(cascade_dir)))
    if path.parent.name == "cascades" and len(path.parents) >= 4:
        anchor_plan_dir(path.parents[3])


def write_file(path: PathLike, data: Union[bytes, str], *, mode: Optional[int] = None,
               fsync: bool = True) -> None:
    """Write *path* atomically through its folder held below the plan's
    directory (``held_folder.write_in_plan_dir``, the containment
    ``status_file.write_status`` uses): a link swapped in for a folder on the
    way is refused, never written through. Missing folders are made."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    write_in_plan_dir(path, data, make=True, mode=mode, keep_mode=mode is None,
                      fsync=fsync)


def _check_contained(path: Path) -> None:
    """Refuse a folder below an anchored plan directory that resolves outside
    it (``held_folder.OutsidePlanDir``), as the held writes refuse a file's."""
    root = plan_dir_of(path)
    if root is None:
        return
    resolved = os.path.realpath(str(path))
    if not Path(resolved).is_relative_to(root):
        raise OutsidePlanDir(
            f"Refusing to remove {path}: it resolves to {resolved}, outside the "
            f"plan's directory {root}, so nothing was removed: a symlink in the "
            "plan's output folder leads out of it. Remove the link and re-run.")


def remove_tree(path: PathLike) -> None:
    """Remove the directory *path* and everything in it, never through a link.

    Files and links are unlinked through their folder held below the plan's
    directory (``held_folder.remove_in_plan_dir``); a link to a folder is
    unlinked, never descended into; each folder is removed once empty, after
    a containment check. A missing *path* is nothing to remove.
    """
    top = Path(os.path.abspath(str(path)))
    if not os.path.lexists(top):
        return
    if os.path.islink(top) or not top.is_dir():
        remove_in_plan_dir(top)
        return
    for folder, dirnames, filenames in os.walk(top, topdown=False, followlinks=False):
        for name in filenames:
            remove_in_plan_dir(Path(folder) / name)
        for name in dirnames:
            child = Path(folder) / name
            if os.path.islink(child):
                remove_in_plan_dir(child)
        _check_contained(Path(folder))
        os.rmdir(folder)


# ---------------------------------------------------------------------------
# A published stage
# ---------------------------------------------------------------------------

def hash_tree(directory: PathLike) -> Dict[str, str]:
    """``{relative posix path: sha256}`` of every regular file below
    *directory*, the publication mark excluded; links are not followed."""
    root = Path(os.path.abspath(str(directory)))
    files: Dict[str, str] = {}
    for folder, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        for name in sorted(filenames):
            path = Path(folder) / name
            relative = path.relative_to(root).as_posix()
            if relative == COMPLETE_NAME:
                continue
            if not stat.S_ISREG(os.lstat(path).st_mode):
                continue
            files[relative] = sha256_file(path)
    return files


def read_complete(artifacts_dir: PathLike, *, cascade_id: Optional[str],
                  stage: int) -> Dict[str, Any]:
    """The publication mark of *artifacts_dir*, checked; else :class:`ArchiveRefusal`.

    Valid when ``.complete.json`` is a JSON object of this schema whose
    ``stage`` is *stage* and, when *cascade_id* is given, whose
    ``cascade_id`` is it, and every file it lists still hashes to the
    recorded value. A missing, unreadable, mismatched or stale mark is a
    stop (exit 3) naming the directory: a stage dir from another cascade, or
    an archive edited after publication, is never read as this stage's.
    """
    directory = Path(os.path.abspath(str(artifacts_dir)))
    path = directory / COMPLETE_NAME

    def refuse(detail: str) -> ArchiveRefusal:
        # Never "move the directory aside": a stage already closed would then
        # drop out of the ledger silently, and the live dirs it would be
        # archived from again may already hold a later stage's round.
        return ArchiveRefusal(
            f"ERROR: the cascade archive {directory} {detail}, so it cannot be read "
            "as this stage's. Nothing was changed. Restore the archive as it was "
            f"published (its {COMPLETE_NAME} lists every file's sha256), or start "
            "a new cascade with --force --cascade."
        )

    if not path.is_file():
        raise refuse(f"has no {COMPLETE_NAME}")
    mark = read_json(path)
    if not isinstance(mark, dict):
        raise refuse(f"has a {COMPLETE_NAME} that is not a JSON object")
    if mark.get("schema_version") != COMPLETE_SCHEMA_VERSION:
        raise refuse(f"has a {COMPLETE_NAME} of schema_version "
                     f"{mark.get('schema_version')!r}, not {COMPLETE_SCHEMA_VERSION}")
    if cascade_id is not None and mark.get("cascade_id") != cascade_id:
        raise refuse(f"belongs to cascade {mark.get('cascade_id')!r}, not {cascade_id!r}")
    if mark.get("stage") != int(stage):
        raise refuse(f"belongs to stage {mark.get('stage')!r}, not {int(stage)}")
    if mark.get("mode") not in MODES or not isinstance(mark.get("model"), str):
        raise refuse(f"has a {COMPLETE_NAME} with no mode or model")
    files = mark.get("files")
    if not isinstance(files, dict) or not files:
        raise refuse(f"has a {COMPLETE_NAME} that lists no file")
    for relative, digest in sorted(files.items()):
        target = directory.joinpath(*str(relative).split("/"))
        try:
            if os.path.islink(target) or sha256_file(target) != digest:
                raise refuse(f"holds {relative}, changed since it was published")
        except OSError:
            raise refuse(f"lacks {relative}, listed in its {COMPLETE_NAME}") from None
    return mark


@dataclass
class StageArchive:
    """One published stage, read: its mark and the files the ledger needs."""

    index: int
    model: str
    mode: str
    directory: Path
    groups: List[Dict[str, Any]]
    validation: List[Dict[str, Any]]
    records: Dict[str, Any]
    status: Dict[str, Any] = field(default_factory=dict)

    def validation_of(self, group: Mapping[str, Any], position: int) -> Dict[str, Any]:
        """The validator's record of *group*: by its stable id, else (a
        hash-less legacy record) by its position, as
        ``validation.apply_validation_to_groups`` joins them."""
        gid = group_id(group)
        by_index: Optional[Dict[str, Any]] = None
        for record in self.validation:
            if gid and record.get("group_id") == gid:
                return record
            if not record.get("group_id") and record.get("group_index") == position:
                by_index = by_index or record
        return by_index or {}


def group_id(group: Mapping[str, Any]) -> str:
    """A grouped record's stable id: its stamped ``group_hash``."""
    return str(group.get("group_hash") or group.get("group_id") or group.get("id") or "")


def load_stage(cascade_dir: PathLike, stage: int, mode: str, *,
               cascade_id: Optional[str]) -> Optional[StageArchive]:
    """Stage *stage*'s archive, or ``None`` when it published none.

    No ``artifacts/`` is a stage that contributed nothing (recorded skipped,
    or not closed). An ``artifacts/`` whose mark does not check out raises
    :class:`ArchiveRefusal` (:func:`read_complete`).
    """
    names = phases(mode)
    directory = stage_dir(cascade_dir, stage) / ARTIFACTS
    if not directory.is_dir():
        return None
    mark = read_complete(directory, cascade_id=cascade_id, stage=stage)
    grouped = _dict(read_json(directory / names.review_dir / "grouped.json"))
    validation = _dict(read_json(directory / names.review_dir / "validation.json"))
    return StageArchive(
        index=int(stage),
        model=str(mark.get("model")),
        mode=str(mark.get("mode")),
        directory=directory,
        groups=[g for g in _list(grouped.get("groups")) if isinstance(g, dict)],
        validation=[r for r in _list(validation.get("groups")) if isinstance(r, dict)],
        records=_dict(read_json(directory / RECORDS_NAME)),
        status=_dict(read_json(directory / names.review_dir / ".status.json")),
    )


# ---------------------------------------------------------------------------
# The entries
# ---------------------------------------------------------------------------

REJECTED = "rejected"
APPLIED = "applied"


@dataclass(frozen=True)
class LedgerEntry:
    """One ledger line: a stable id (``R<stage>-<n>`` or ``A<stage>-<n>``),
    the stage's model, the group's title and importance, and for a rejected
    entry its description and recorded reason, for an applied one where it
    landed. Every text field is already clipped."""

    id: str
    kind: str
    stage: int
    number: int
    model: str
    title: str
    importance: str
    description: str = ""
    reason: str = ""
    at: str = ""

    def line(self) -> str:
        head = f"- {self.id} [{self.importance}] ({self.model}) {self.title}"
        if self.kind == APPLIED:
            return f"{head} — at: {self.at or 'not recorded'}"
        description = f" — {self.description}" if self.description else ""
        return f"{head}{description} — reason: {self.reason or 'not recorded'}"


@dataclass(frozen=True)
class Ledger:
    """Every entry of the stages archived up to a stage, in natural order
    (stage, then number). ``stages`` lists the stages that published an
    archive; an empty one renders empty files."""

    mode: str
    upto_stage: int
    stages: Tuple[int, ...]
    rejected: Tuple[LedgerEntry, ...]
    applied: Tuple[LedgerEntry, ...]

    @property
    def empty(self) -> bool:
        return not self.stages

    @property
    def entries(self) -> Tuple[LedgerEntry, ...]:
        return self.rejected + self.applied


def _members(group: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    return [m for m in _importance.group_members(dict(group)) if isinstance(m, Mapping)]


def _title(group: Mapping[str, Any], fallback: str) -> str:
    members = _members(group)
    if members and members[0].get("title"):
        return str(members[0]["title"])
    return str(group.get("theme") or fallback or "untitled")


def _description(group: Mapping[str, Any]) -> str:
    for member in _members(group):
        for key in ("desc", "description", "details"):
            if member.get(key):
                return str(member[key])
    return ""


def _plan_location(group: Mapping[str, Any]) -> str:
    """improve-plan: where a suggestion landed, its ``reference`` (the section
    the reviewer named), else a ``section`` or ``location`` field."""
    for member in _members(group):
        for key in ("reference", "section", "location"):
            if member.get(key):
                return str(member[key])
    return ""


def _code_files(group: Mapping[str, Any]) -> List[str]:
    files: List[str] = []
    for member in _members(group):
        value = member.get("file")
        if isinstance(value, str) and value and value not in files:
            files.append(value)
    return files


def _batch_files(records: Mapping[str, Any], item: str, entry: Mapping[str, Any]) -> List[str]:
    """improve-code: the files the batch that applied *item* changed: its row
    of ``write_batch_report.json`` (``files_by_task``), else the batch's
    declared files, from the stage's ``records.json``."""
    details = _dict(entry.get("details"))
    task_id = str(details.get("task_id") or "")
    batches = [b for b in _list(records.get("batches")) if isinstance(b, dict)]
    if not task_id:
        task_id = next((str(b.get("task_id") or "") for b in batches
                        if item in [str(i) for i in _list(b.get("expected_ids"))]), "")
    touched = _list(_dict(records.get("files_by_task")).get(task_id))
    if touched:
        return [str(p) for p in touched if str(p)]
    for batch in batches:
        if str(batch.get("task_id") or "") == task_id:
            return [str(p) for p in _list(batch.get("declared_files")) if str(p)]
    return []


def _judge_skipped(decision: Mapping[str, Any]) -> bool:
    return canonical_value(decision.get("decision")) == "skipped"


def reused_items(records: Mapping[str, Any]) -> Set[str]:
    """The ``records.json`` items whose batch the stage's apply reused, not dispatched.

    A stage whose findings repeat an earlier stage's word for word has the
    same group ids and the same batches, so the write scheduler's resume
    finds each batch's result file of the earlier stage, skips it
    (``already complete — skipping``) and stamps the items ``processed``
    again, inside this stage's time window. Nothing was applied by this
    stage: they count as No-op (already addressed) and get no ``A<k>-<n>``
    ledger entry.
    """
    return {str(item) for item in _list(records.get("reused_items")) if str(item)}


def stage_entries(archive: StageArchive) -> Tuple[List[LedgerEntry], List[LedgerEntry]]:
    """``(rejected, applied)`` of one archived stage, numbered from 1.

    Rejected or held back, one entry per group, the first source that names
    it: a group validated ``invalid`` (the validator's reason), a
    needs-human-decision item the judge skipped (the decision's reason), an
    item its batch declined (the record's ``details.reason``), a scope
    deferral of a ``preserve`` round (labelled :data:`SCOPE_LABEL`, with the
    deferral's reason: held back, valid and not applied, never worded as a
    rejection). ``validation_failed`` groups (never judged) and
    ``no-op`` items (already addressed) are left out. Applied: every item
    recorded ``applied`` whose batch this stage's apply dispatched (not one
    it reused from an earlier stage: :func:`reused_items`), with its section
    (improve-plan) or the files its batch changed (improve-code). Numbering
    follows ``grouped.json``'s order, then ids no group carries, sorted, so
    the same archive always gives the same ids.
    """
    records = archive.records
    processed = _dict(records.get("processed"))
    decisions = _dict(records.get("human_decisions"))
    deferrals = {
        str(d.get("group_id")): d
        for d in _list(_dict(records.get("scope_policy")).get("deferrals"))
        if isinstance(d, dict) and d.get("group_id")
    }
    by_id: Dict[str, Tuple[int, Mapping[str, Any]]] = {}
    for position, group in enumerate(archive.groups):
        gid = group_id(group)
        if gid and gid not in by_id:
            by_id[gid] = (position, group)

    rejected_raw: Dict[str, Tuple[str, str, Mapping[str, Any]]] = {}
    for position, group in enumerate(archive.groups):
        gid = group_id(group)
        verdict = archive.validation_of(group, position)
        if verdict.get("status") == "invalid":
            rejected_raw[gid or f"#{position}"] = (str(verdict.get("reason") or ""), "", group)
    for gid, decision in sorted(decisions.items()):
        if isinstance(decision, dict) and _judge_skipped(decision) and gid not in rejected_raw:
            rejected_raw[gid] = (str(decision.get("reason") or ""), "",
                                 by_id.get(gid, (0, {}))[1])
    for gid, entry in sorted(processed.items()):
        if (isinstance(entry, dict) and entry.get("status") == "declined"
                and gid not in rejected_raw):
            reason = str(_dict(entry.get("details")).get("reason") or "")
            rejected_raw[gid] = (reason, "", by_id.get(gid, (0, {}))[1])
    for gid, deferral in sorted(deferrals.items()):
        if gid not in rejected_raw:
            group = by_id.get(gid, (0, {}))[1] or {
                "theme": deferral.get("title") or deferral.get("theme"),
                "suggestions": [{"importance": deferral.get("importance")}],
            }
            reason = str(deferral.get("reason") or "")
            rejected_raw[gid] = (reason, SCOPE_LABEL, group)

    def ordered(ids: Iterable[str]) -> List[str]:
        known = [i for i in ids if i in by_id]
        known.sort(key=lambda i: by_id[i][0])
        return known + sorted(i for i in ids if i not in by_id)

    rejected: List[LedgerEntry] = []
    for number, gid in enumerate(ordered(list(rejected_raw)), start=1):
        reason, label, group = rejected_raw[gid]
        if label:
            reason = f"{label}: {reason}" if reason else label
        rejected.append(LedgerEntry(
            id=f"R{archive.index}-{number}", kind=REJECTED, stage=archive.index,
            number=number, model=archive.model,
            title=clip(_title(group, gid), TITLE_LIMIT),
            importance=_importance.group_importance(dict(group)),
            description=clip(_description(group), DESCRIPTION_LIMIT),
            reason=clip(reason, REASON_LIMIT),
        ))

    reused = reused_items(records)
    applied_ids = [gid for gid, entry in processed.items()
                   if isinstance(entry, dict) and entry.get("status") == "applied"
                   and gid not in reused]
    applied: List[LedgerEntry] = []
    for number, gid in enumerate(ordered(applied_ids), start=1):
        group = by_id.get(gid, (0, {}))[1]
        if archive.mode == "improve-code":
            files = _batch_files(records, gid, processed[gid]) or _code_files(group)
            at = ", ".join(files)
        else:
            at = _plan_location(group)
        applied.append(LedgerEntry(
            id=f"A{archive.index}-{number}", kind=APPLIED, stage=archive.index,
            number=number, model=archive.model,
            title=clip(_title(group, gid), TITLE_LIMIT),
            importance=_importance.group_importance(dict(group)),
            at=clip(at, LOCATION_LIMIT),
        ))
    return rejected, applied


def _record_cascade_id(cascade_dir: PathLike) -> Optional[str]:
    record = read_json(Path(os.path.abspath(str(cascade_dir))) / RECORD_NAME)
    value = record.get("cascade_id") if isinstance(record, dict) else None
    return value if isinstance(value, str) and value else None


def build_ledger(cascade_dir: PathLike, upto_stage: int, mode: str, *,
                 cascade_id: Optional[str] = None) -> Ledger:
    """The ledger of the archived stages ``1..upto_stage`` (inclusive).

    Reads only ``stage-<j>/artifacts/`` with a valid ``.complete.json``; a
    stage with no ``artifacts/`` (recorded skipped) contributes nothing, and
    one whose mark does not check out raises :class:`ArchiveRefusal`.
    *cascade_id*, when given, must be every mark's; else the cascade dir's
    ``record.json`` names it, and a dir with no record checks the stage alone.
    A stage's ledger is ``build_ledger(cascade_dir, k - 1, mode)``.
    """
    names = phases(mode)
    if cascade_id is None:
        cascade_id = _record_cascade_id(cascade_dir)
    stages: List[int] = []
    rejected: List[LedgerEntry] = []
    applied: List[LedgerEntry] = []
    for index in range(1, int(upto_stage) + 1):
        archive = load_stage(cascade_dir, index, names.mode, cascade_id=cascade_id)
        if archive is None:
            continue
        stages.append(index)
        found_rejected, found_applied = stage_entries(archive)
        rejected += found_rejected
        applied += found_applied
    return Ledger(mode=names.mode, upto_stage=int(upto_stage), stages=tuple(stages),
                  rejected=tuple(rejected), applied=tuple(applied))


# ---------------------------------------------------------------------------
# Rendering (pure: the same ledger gives the same bytes)
# ---------------------------------------------------------------------------

_REJECTED_RULE = (
    "Rejected or held back in earlier rounds. Do not raise these again unless you\n"
    "have an argument the recorded reason does not answer; if you do, start the\n"
    "finding's description with \"Re-raises R<n>-<m>:\" and say what is new."
)
_APPLIED_RULE = (
    "Changed by earlier rounds. These edits were made by other models, not by the\n"
    "author. Review them as you review the rest of the work: they can be wrong, and\n"
    "you may propose correcting or reverting them."
)
REJECTED_HEADING = "Rejected or held back in earlier rounds:"
APPLIED_HEADING = "Changed by earlier rounds:"
_NONE = "- (none)"


def _rejected_priority(entry: LedgerEntry) -> Tuple[int, int, int]:
    """HIGH before MEDIUM before LOW, the latest stage first within a level."""
    return (_importance.rank(entry.importance), -entry.stage, entry.number)


def _applied_priority(entry: LedgerEntry) -> Tuple[int, int]:
    """The latest stage first."""
    return (-entry.stage, entry.number)


def _select(rejected: Sequence[LedgerEntry], applied: Sequence[LedgerEntry],
            fits) -> Tuple[List[LedgerEntry], List[LedgerEntry], int]:
    """The entries an inline block keeps, each list in priority order, and the
    number left out.

    Entries are taken in one order (every rejected entry by
    :func:`_rejected_priority`, then every applied one by
    :func:`_applied_priority`) while ``fits(kept_rejected, kept_applied,
    left_out)`` holds; the first that does not fit ends the take, so a block
    never shows a less important entry in place of a more important one.
    """
    order_r = sorted(rejected, key=_rejected_priority)
    order_a = sorted(applied, key=_applied_priority)
    total = len(order_r) + len(order_a)
    kept_r: List[LedgerEntry] = []
    kept_a: List[LedgerEntry] = []
    if fits(order_r, order_a, 0):
        return order_r, order_a, 0
    for entry in order_r + order_a:
        trial_r = kept_r + [entry] if entry.kind == REJECTED else kept_r
        trial_a = kept_a + [entry] if entry.kind == APPLIED else kept_a
        left = total - len(trial_r) - len(trial_a)
        if not fits(trial_r, trial_a, left):
            break
        kept_r, kept_a = trial_r, trial_a
    return kept_r, kept_a, total - len(kept_r) - len(kept_a)


def _lines(entries: Sequence[LedgerEntry]) -> str:
    return "\n".join(e.line() for e in entries) if entries else _NONE


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}{'' if count == 1 else 's'}"


def _left_out_line(count: int) -> str:
    if count == 1:
        return "1 more entry is left out here to keep this block short."
    return f"{count} more entries are left out here to keep this block short."


def _capped(build, rejected, applied, limit: int) -> str:
    def fits(kept_r, kept_a, left):
        return len(build(kept_r, kept_a, left)) <= limit

    kept_r, kept_a, left = _select(rejected, applied, fits)
    return build(kept_r, kept_a, left)


def render_reviewer(ledger: Ledger, *, full_path: PathLike,
                    changes_path: Optional[PathLike] = None,
                    limit: int = LEDGER_INLINE_MAX_CHARS) -> str:
    """``ledger.md``: the reviewer's whole "Earlier review rounds" block.

    Both lists in priority order, capped at *limit* characters. Reviewers
    read files themselves, so its last lines may point at the stage's frozen
    files by absolute path: *full_path* (``ledger-full.md``) when entries were
    left out, and on improve-plan *changes_path* (``changes-so-far.diff``),
    always. ``""`` for a ledger with no archived stage.
    """
    if ledger.empty:
        return ""
    subject = "code" if ledger.mode == "improve-code" else "plan"
    rounds = _plural(len(ledger.stages), "automated review round")

    def build(kept_r, kept_a, left) -> str:
        parts = [
            "## Earlier review rounds",
            "",
            f"This {subject} has already been through {rounds} by\n"
            "other models. Their results are below.",
            "",
            _REJECTED_RULE,
            _lines(kept_r),
            "",
            _APPLIED_RULE,
            _lines(kept_a),
        ]
        tail = []
        if left:
            tail.append(f"{_left_out_line(left)[:-1]}; every entry is in "
                        f"{os.path.abspath(str(full_path))}.")
        if changes_path is not None:
            tail.append("Every change earlier rounds made to the plan, as a unified diff "
                        "against the plan before the first round: "
                        f"{os.path.abspath(str(changes_path))}")
        if tail:
            parts += [""] + tail
        return "\n".join(parts) + "\n"

    return _capped(build, ledger.rejected, ledger.applied, limit)


def render_validator(ledger: Ledger, *, limit: int = LEDGER_INLINE_MAX_CHARS) -> str:
    """``ledger-validator.md``: the same two lists, inline only.

    Validators get no file pointer (the materialized-task contract allows no
    bare path), so the overflow line gives a count alone. No rule text: the
    validator prompt adds its own. ``""`` for a ledger with no archived stage.
    """
    if ledger.empty:
        return ""

    def build(kept_r, kept_a, left) -> str:
        parts = [REJECTED_HEADING, _lines(kept_r), "", APPLIED_HEADING, _lines(kept_a)]
        if left:
            parts += ["", _left_out_line(left)]
        return "\n".join(parts) + "\n"

    return _capped(build, ledger.rejected, ledger.applied, limit)


def render_judge(ledger: Ledger, *, limit: int = LEDGER_INLINE_MAX_CHARS) -> str:
    """``ledger-judge.md``: the rejected-or-held-back list alone, inline,
    capped like the validator's. ``""`` for a ledger with no archived stage."""
    if ledger.empty:
        return ""

    def build(kept_r, _kept_a, left) -> str:
        parts = [REJECTED_HEADING, _lines(kept_r)]
        if left:
            parts += ["", _left_out_line(left)]
        return "\n".join(parts) + "\n"

    return _capped(build, ledger.rejected, (), limit)


def render_full(ledger: Ledger) -> str:
    """``ledger-full.md`` and the cascade dir's ``ledger.md`` view: every
    entry, uncapped, in natural order (stage, then number). ``""`` for a
    ledger with no archived stage."""
    if ledger.empty:
        return ""
    shown = ", ".join(str(s) for s in ledger.stages)
    parts = [
        "# Cascade ledger",
        "",
        f"Archived rounds: {shown}.",
        "",
        "## " + REJECTED_HEADING[:-1],
        "",
        _lines(ledger.rejected),
        "",
        "## " + APPLIED_HEADING[:-1],
        "",
        _lines(ledger.applied),
    ]
    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------------------
# Freezing a stage's inputs
# ---------------------------------------------------------------------------

def unified_diff(before: str, after: str, *, before_name: str, after_name: str) -> str:
    """A unified diff of two texts, ``""`` when they are equal; a last line
    with no newline is marked as ``diff`` marks it."""
    if before == after:
        return ""
    out: List[str] = []
    for line in difflib.unified_diff(before.splitlines(keepends=True),
                                     after.splitlines(keepends=True),
                                     fromfile=before_name, tofile=after_name):
        if line.endswith("\n"):
            out.append(line)
        else:
            out.append(line + "\n\\ No newline at end of file\n")
    return "".join(out)


def _decode(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def freeze_inputs(*, cascade_dir: Path, cascade_id: str, mode: str, stage: int,
                  of: int, model: str, plan_path: Path) -> Path:
    """Write ``cascade_dir/stage-<stage>/inputs/`` and return its manifest path.

    Idempotent: a manifest already there is verified
    (``cascade_provenance.load_manifest``, which raises
    ``CascadeProvenanceError`` for a changed file, exit 3) and returned
    untouched; an ``inputs/`` without a manifest is a crash mid-write, removed
    and rebuilt. Built from the archived stages ``1..stage-1`` only
    (:func:`build_ledger`). Writes the four ledger files (empty when no
    earlier stage published an archive), and on improve-plan
    ``plan.before.md`` (the plan's bytes now) and ``changes-so-far.diff``
    (``cascade_dir/start.md`` against ``plan.before.md``; empty at stage 1),
    then the manifest, last. Refuses (:class:`ArchiveRefusal`) a later
    improve-plan stage whose ``start.md`` is missing.
    """
    names = phases(mode)
    plan = Path(os.path.abspath(str(plan_path)))
    output_dir_path(plan)  # anchors the plan's directory for the writes
    cascade_dir = Path(os.path.abspath(str(cascade_dir)))
    anchor_cascade_dir(cascade_dir)
    directory = stage_dir(cascade_dir, stage) / INPUTS
    manifest_path = directory / provenance.MANIFEST_NAME
    if manifest_path.is_file():
        manifest = provenance.load_manifest(manifest_path)
        if manifest.get("cascade_id") != str(cascade_id) or manifest.get("stage") != int(stage):
            raise provenance.CascadeProvenanceError(
                manifest_path,
                f"names cascade {manifest.get('cascade_id')} stage {manifest.get('stage')}, "
                f"not cascade {cascade_id} stage {int(stage)}")
        return manifest_path
    if os.path.lexists(directory):
        try:
            remove_tree(directory)
        except OSError as exc:
            raise ArchiveRefusal(
                f"ERROR: cascade stage {int(stage)}'s unfinished inputs in {directory} "
                f"could not be removed ({exc}); nothing was run.") from exc

    ledger = build_ledger(cascade_dir, int(stage) - 1, names.mode, cascade_id=str(cascade_id))
    full_path = directory / provenance.FULL_LEDGER
    changes_path = directory / provenance.CHANGES_SO_FAR
    is_plan = names.mode == "improve-plan"
    files: Dict[str, bytes] = {
        provenance.REVIEWER_LEDGER: render_reviewer(
            ledger, full_path=full_path,
            changes_path=changes_path if is_plan else None).encode("utf-8"),
        provenance.VALIDATOR_LEDGER: render_validator(ledger).encode("utf-8"),
        provenance.JUDGE_LEDGER: render_judge(ledger).encode("utf-8"),
        provenance.FULL_LEDGER: render_full(ledger).encode("utf-8"),
    }
    if is_plan:
        try:
            plan_bytes = plan.read_bytes()
        except OSError as exc:
            raise ArchiveRefusal(
                f"ERROR: cannot read the plan {plan} ({exc.strerror or exc}) to freeze "
                f"cascade stage {int(stage)}'s inputs; nothing was run.") from exc
        files[provenance.PLAN_BEFORE] = plan_bytes
        diff = ""
        if int(stage) > 1:
            start = cascade_dir / START_PLAN
            try:
                start_bytes = start.read_bytes()
            except OSError as exc:
                raise ArchiveRefusal(
                    f"ERROR: the cascade's {start} cannot be read "
                    f"({exc.strerror or exc}), so stage {int(stage)}'s changes so far "
                    "cannot be frozen; nothing was run. Start a new cascade with "
                    "--force --cascade.") from exc
            diff = unified_diff(_decode(start_bytes), _decode(plan_bytes),
                                before_name=f"a/{plan.name} (cascade start)",
                                after_name=f"b/{plan.name} (stage {int(stage)} start)")
        files[provenance.CHANGES_SO_FAR] = diff.encode("utf-8")
    try:
        for name, data in files.items():
            write_file(directory / name, data)
        return provenance.write_manifest(
            directory, cascade_id=str(cascade_id), mode=names.mode, stage=int(stage),
            of=int(of), model=str(model), names=list(files))
    except OSError as exc:
        # A refused containment check is an OSError too; with no manifest the
        # next run rebuilds inputs/ from scratch.
        raise ArchiveRefusal(
            f"ERROR: cascade stage {int(stage)}'s inputs could not be written in "
            f"{directory} ({exc}); nothing was run.") from exc
