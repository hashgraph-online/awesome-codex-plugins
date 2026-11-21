"""A cascade stage's provenance: its frozen inputs manifest and the review round's ``cascade`` block.

``--cascade`` (``utils/improve_cascade.py``) runs one review-then-apply round
per model. Each stage freezes its inputs (the forward ledger, and on
improve-plan the plan at the stage's start) under
``cascades/<stamp>-<id8>/stage-<k>/inputs/`` and writes ``manifest.json``
**last**, naming each file with its sha256. The stage's review gets the hidden
``--cascade-stage-file <manifest>`` flag (:data:`HIDDEN_FLAG`), verifies the
manifest and records it as the ``cascade`` block of its round's
``.status.json`` (:data:`STATUS_KEY`). Every later reader of the ledger (the
reviewer prompt, validation materialization, the judge prompt) reads the block
from the review round's ``.status.json`` and verifies the file's hash before it
renders a byte of it, so every call of a stage sees the same ledger and a file
changed under it stops the call (fail closed, exit 3).

This module is the one owner of that format: the cascade writes manifests
through :func:`write_manifest`, the review records :func:`block_from_manifest`
and carries it across fan-outs with :func:`next_block`, and the renderers read
:func:`read_block` and :func:`ledger_text`. It imports nothing from the
orchestrators, so any of them can import it.

The developer contract is ``docs/development/workflows.md``, "A cascade
(``--cascade``)".
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Union

from . import status_file
from .held_folder import write_in_plan_dir

PathLike = Union[str, "os.PathLike[str]"]

#: Version of :data:`MANIFEST_NAME` and of the ``cascade`` block.
SCHEMA_VERSION = 1

#: The hidden review-plan / review-code flag naming a stage's manifest
#: (argparse help suppressed; dropped from replay flags).
HIDDEN_FLAG = "--cascade-stage-file"
#: Its argparse ``dest``.
FLAG_DEST = "cascade_stage_file"

#: The key of the block in a review round's ``.status.json``.
STATUS_KEY = "cascade"

#: The manifest's file name inside a stage's ``inputs/``.
MANIFEST_NAME = "manifest.json"

#: The frozen inputs a stage may hold, by file name. Stage 1's ledger files
#: exist and are empty. The two plan files exist on improve-plan only.
#:
#: * :data:`REVIEWER_LEDGER`: the reviewer's whole "Earlier review rounds"
#:   block, capped, whose overflow line may name :data:`FULL_LEDGER` and
#:   :data:`CHANGES_SO_FAR` by absolute path (reviewers read files).
#: * :data:`VALIDATOR_LEDGER`: the same lists for validators, inline only:
#:   its overflow line gives a count and no path (the materialized-task
#:   contract allows no bare file pointer).
#: * :data:`JUDGE_LEDGER`: the rejected-or-held-back list alone, for the judge.
#: * :data:`FULL_LEDGER`: every entry, uncapped.
#: * :data:`PLAN_BEFORE`: improve-plan, the plan at this stage's start.
#: * :data:`CHANGES_SO_FAR`: improve-plan, a unified diff of the plan at the
#:   cascade's start against :data:`PLAN_BEFORE`.
REVIEWER_LEDGER = "ledger.md"
VALIDATOR_LEDGER = "ledger-validator.md"
JUDGE_LEDGER = "ledger-judge.md"
FULL_LEDGER = "ledger-full.md"
PLAN_BEFORE = "plan.before.md"
CHANGES_SO_FAR = "changes-so-far.diff"

LEDGER_NAMES = (REVIEWER_LEDGER, VALIDATOR_LEDGER, JUDGE_LEDGER, FULL_LEDGER)
INPUT_NAMES = LEDGER_NAMES + (PLAN_BEFORE, CHANGES_SO_FAR)

_BLOCK_KEYS = ("schema_version", "cascade_id", "mode", "stage", "of", "model",
               "manifest", "manifest_sha256", "files")


class CascadeProvenanceError(Exception):
    """A manifest, block or frozen input that cannot be trusted; always exit 3.

    Attributes:
        path: The file it is about.
        detail: What is wrong with it, one clause.
    """

    def __init__(self, path: PathLike, detail: str):
        self.path = str(path)
        self.detail = detail
        super().__init__(f"{self.path}: {detail}")


class StaleHandoff(CascadeProvenanceError):
    """A stage's handoff whose cascade is no longer the composite's current, running one.

    Raised by :func:`check_current`; :func:`error_line` words it as a handoff
    to drop, not as a frozen input to restore.
    """


def error_line(exc: CascadeProvenanceError) -> str:
    """The one ``ERROR:`` line a refusal prints (callers pass it to ``fail_closed``)."""
    if isinstance(exc, StaleHandoff):
        return (
            f"ERROR: cascade stage handoff refused: {exc.path}: {exc.detail}; nothing "
            "was run. Run the composite's command again with --cascade to see where "
            "the cascade stands and get the command for its current stage."
        )
    return (
        f"ERROR: cascade stage input {exc.path}: {exc.detail}; nothing was run. "
        "A cascade stage's frozen inputs and its review round must match: restore "
        "the file, or start a new cascade with --force --cascade."
    )


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: PathLike) -> str:
    """The sha256 of *path*'s bytes; raises :class:`CascadeProvenanceError` when unreadable."""
    try:
        with open(path, "rb") as handle:
            return sha256_bytes(handle.read())
    except OSError as exc:
        raise CascadeProvenanceError(path, f"cannot be read ({exc.strerror or exc})") from exc


# ---------------------------------------------------------------------------
# The manifest (written by the cascade, read by the review)
# ---------------------------------------------------------------------------

def write_manifest(
    inputs_dir: PathLike,
    *,
    cascade_id: str,
    mode: str,
    stage: int,
    of: int,
    model: str,
    names: Iterable[str],
) -> Path:
    """Hash each of *names* in *inputs_dir* and write ``manifest.json`` there, atomically.

    The write goes through the plan-output containment helper
    (``held_folder.write_in_plan_dir``): below an anchored plan directory a
    link swapped in for a folder on the way is refused, never written
    through; anywhere else (a test's folder) the file is written by its path.

    Call it after every input file is written and closed: the manifest is the
    stage's "inputs complete" mark, and an ``inputs/`` without one is rebuilt.
    Returns the manifest's absolute path.
    """
    directory = Path(os.path.abspath(str(inputs_dir)))
    files: Dict[str, Dict[str, Any]] = {}
    for name in names:
        if name not in INPUT_NAMES:
            raise ValueError(f"{name!r} is not a cascade input name")
        target = directory / name
        data = target.read_bytes()
        files[name] = {"sha256": sha256_bytes(data), "bytes": len(data)}
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "cascade_id": str(cascade_id),
        "mode": str(mode),
        "stage": int(stage),
        "of": int(of),
        "model": str(model),
        "files": files,
    }
    path = directory / MANIFEST_NAME
    # Through its folder held below the plan's directory, as the stage's
    # other inputs are written (``cascade_ledger.write_file``).
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    write_in_plan_dir(path, text.encode("utf-8"))
    return path


def _require(condition: bool, path: PathLike, detail: str) -> None:
    if not condition:
        raise CascadeProvenanceError(path, detail)


def _check_identity(doc: Mapping[str, Any], path: PathLike) -> None:
    _require(doc.get("schema_version") == SCHEMA_VERSION, path,
             f"schema_version is not {SCHEMA_VERSION}")
    _require(isinstance(doc.get("cascade_id"), str) and bool(doc.get("cascade_id")),
             path, "cascade_id is missing")
    _require(isinstance(doc.get("mode"), str) and bool(doc.get("mode")), path,
             "mode is missing")
    for key in ("stage", "of"):
        value = doc.get(key)
        _require(isinstance(value, int) and not isinstance(value, bool) and value >= 1,
                 path, f"{key} is not a positive integer")
    _require(doc["stage"] <= doc["of"], path, "stage is greater than of")
    _require(isinstance(doc.get("model"), str) and bool(doc.get("model")), path,
             "model is missing")
    files = doc.get("files")
    _require(isinstance(files, dict), path, "files is not an object")
    for name, entry in files.items():
        _require(name in INPUT_NAMES, path, f"files names an unknown input {name!r}")
        _require(isinstance(entry, dict) and isinstance(entry.get("sha256"), str), path,
                 f"files[{name!r}] has no sha256")


def load_manifest(path: PathLike) -> Dict[str, Any]:
    """The manifest at *path*, its shape checked and every file's hash verified.

    Raises :class:`CascadeProvenanceError` (exit 3) for a missing or
    unparsable manifest, a bad shape, or a listed file whose bytes no longer
    hash to the recorded value.
    """
    path = Path(os.path.abspath(str(path)))
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CascadeProvenanceError(path, "does not exist") from exc
    except (OSError, ValueError) as exc:
        raise CascadeProvenanceError(path, f"cannot be read as JSON ({exc})") from exc
    _require(isinstance(doc, dict), path, "is not a JSON object")
    _check_identity(doc, path)
    for name, entry in doc["files"].items():
        actual = file_sha256(path.parent / name)
        _require(actual == entry["sha256"], path.parent / name,
                 "changed since the stage's manifest was written")
    return doc


def block_from_manifest(path: PathLike) -> Dict[str, Any]:
    """The ``cascade`` block a review records for the manifest at *path* (verified first)."""
    path = Path(os.path.abspath(str(path)))
    manifest = load_manifest(path)
    return {
        "schema_version": SCHEMA_VERSION,
        "cascade_id": manifest["cascade_id"],
        "mode": manifest["mode"],
        "stage": manifest["stage"],
        "of": manifest["of"],
        "model": manifest["model"],
        "manifest": str(path),
        "manifest_sha256": file_sha256(path),
        "files": {name: entry["sha256"] for name, entry in sorted(manifest["files"].items())},
    }


# ---------------------------------------------------------------------------
# The block (recorded by the review, read by every ledger renderer)
# ---------------------------------------------------------------------------

def check_block(block: Any, where: PathLike) -> Dict[str, Any]:
    """*block* when it has the block's shape; raises :class:`CascadeProvenanceError` otherwise."""
    _require(isinstance(block, dict), where, f"its {STATUS_KEY!r} block is not an object")
    missing = [key for key in _BLOCK_KEYS if key not in block]
    _require(not missing, where, f"its {STATUS_KEY!r} block lacks {', '.join(missing)}")
    _check_identity({**block, "files": {
        name: {"sha256": sha} for name, sha in (block.get("files") or {}).items()
    } if isinstance(block.get("files"), dict) else None}, where)
    _require(isinstance(block.get("manifest"), str) and os.path.isabs(block["manifest"]),
             where, f"its {STATUS_KEY!r} block's manifest is not an absolute path")
    return block


def read_block(review_dir: PathLike) -> Optional[Dict[str, Any]]:
    """The ``cascade`` block of *review_dir*'s ``.status.json``, or ``None`` when it holds none.

    Read-only. A missing or unreadable checkpoint holds none (``read_status``
    folds both into ``{}``). A block that is present but malformed raises
    :class:`CascadeProvenanceError`: a renderer must not take it for "no
    cascade" and render today's prompt.
    """
    data = status_file.read_status(str(review_dir))
    if STATUS_KEY not in data or data.get(STATUS_KEY) is None:
        return None
    return check_block(data[STATUS_KEY], status_file.status_path(str(review_dir)))


def same_stage(first: Optional[Mapping[str, Any]], second: Optional[Mapping[str, Any]]) -> bool:
    """Whether two blocks name the same cascade and stage."""
    if not first or not second:
        return False
    return (first.get("cascade_id") == second.get("cascade_id")
            and first.get("stage") == second.get("stage"))


def resumes_stage(previous: Optional[Mapping[str, Any]], models: Sequence[str], *,
                  rerun_all: bool) -> bool:
    """Whether a fan-out without the hidden flag resumes the stage round *previous* records.

    Only a fan-out that keeps the round's results (no ``--rerun-all``) for
    exactly the stage's one model (*models*, the canonical specs it
    requested, is ``[previous["model"]]``) continues that round: the
    cascade's own retry, a ``--force`` resume that reuses the model's result
    or dispatches it again. Any other model list, a second model beside it
    included, is a round started by hand, which is not the cascade's.
    """
    if not previous or rerun_all:
        return False
    return [str(spec) for spec in models] == [str(previous.get("model"))]


def next_block(
    previous: Optional[Dict[str, Any]],
    given: Optional[Dict[str, Any]],
    *,
    rerun_all: bool,
    models: Sequence[str],
    where: PathLike = ".status.json",
) -> Optional[Dict[str, Any]]:
    """The block a new fan-out records, from the one on record and the one its flag gave.

    The three carry-over rules of the opening checkpoint (*models* is the
    fan-out's requested specs):

    * flag given: record it; but over a different stage's block on a fan-out
      that keeps results (not ``--rerun-all``), raise (exit 3), since two
      stages' results would share one round;
    * flag absent, the stage's round resumed (:func:`resumes_stage`: no
      ``--rerun-all``, and *models* is exactly the block's one model): carry
      the previous block over, so a printed retry, which never replays the
      flag but names the stage's one model (:func:`retry_flags`), stays the
      stage's round;
    * flag absent otherwise (``--rerun-all``, or any other model list): none;
      a round started by hand is not the cascade's, so the cascade's binding
      reads it as foreign and no prompt renders the stage's ledger in it.
    """
    if given is not None:
        if previous is not None and not same_stage(previous, given) and not rerun_all:
            raise CascadeProvenanceError(
                where,
                f"the round on record belongs to cascade {previous.get('cascade_id')} stage "
                f"{previous.get('stage')}, and this fan-out (cascade {given.get('cascade_id')} "
                f"stage {given.get('stage')}) would keep its results",
            )
        return given
    if resumes_stage(previous, models, rerun_all=rerun_all):
        return previous
    return None


# ---------------------------------------------------------------------------
# The composite's current cascade (read by the review, before it dispatches)
# ---------------------------------------------------------------------------

#: The composite run dir's pointer to its current cascade, and the record in
#: the cascade dir it names (``utils/improve_cascade.py`` writes both, and
#: checks them against ``schemas/cascade_record.schema.json``).
POINTER_NAME = "cascade-current.json"
RECORD_NAME = "record.json"

#: The record's ``state`` of a cascade still under way, and the stage states
#: of a stage already closed (done, or skipped for a review with no result).
_RUNNING = "running"
_CLOSED_STAGES = ("done", "skipped")


def _stale(condition: bool, path: PathLike, detail: str) -> None:
    if not condition:
        raise StaleHandoff(path, detail)


def _read_object(path: Path) -> Dict[str, Any]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise StaleHandoff(path, "does not exist, so no cascade of this plan is "
                                 "running") from exc
    except (OSError, ValueError) as exc:
        raise StaleHandoff(path, f"cannot be read as JSON ({exc})") from exc
    _stale(isinstance(doc, dict), path, "is not a JSON object")
    return doc


def check_current(block: Mapping[str, Any], review_dir: PathLike) -> None:
    """Refuse a stage's handoff that is not the composite's current, running cascade's.

    *block* is the one the hidden flag's manifest gives (:func:`block_from_manifest`),
    *review_dir* the review phase dir of the plan it runs for. The composite's
    run dir is *review_dir*'s sibling named by the block's mode
    (``improve-plan/``, ``improve-code/``); its :data:`POINTER_NAME` must name
    the block's cascade, the record there must be ``running``, and the
    block's stage must not be closed in it. Anything else is a handoff
    printed for a cascade that was superseded (``--force --cascade``, or a
    second planner that started its own), abandoned or finished since, or for
    a stage already closed out: dispatching it would start a paid review no
    cascade will bind. Raises :class:`StaleHandoff` (a
    :class:`CascadeProvenanceError`, exit 3), naming the pointer or record. Read-only, and takes no lock: the planner writes
    both files atomically, the pointer last.
    """
    mode = str(block.get("mode") or "")
    _stale(bool(mode) and os.path.basename(mode) == mode and mode not in (".", ".."),
           review_dir, f"its {STATUS_KEY!r} block names no composite ({mode!r})")
    run_dir = Path(os.path.abspath(str(review_dir))).parent / mode
    pointer = run_dir / POINTER_NAME
    doc = _read_object(pointer)
    cascade_id = block.get("cascade_id")
    _stale(doc.get("cascade_id") == cascade_id, pointer,
           f"it names cascade {str(doc.get('cascade_id'))[:8]}, not {str(cascade_id)[:8]}, "
           "the one this stage's handoff belongs to: that cascade was superseded")
    relative = doc.get("dir")
    _stale(isinstance(relative, str) and bool(relative) and not os.path.isabs(relative)
           and os.pardir not in Path(relative).parts, pointer,
           "its dir is not a path inside the run dir")
    record_path = run_dir / relative / RECORD_NAME
    record = _read_object(record_path)
    _stale(record.get("cascade_id") == cascade_id, record_path,
           "its cascade_id is not the one the pointer names")
    state = record.get("state")
    _stale(state == _RUNNING, record_path,
           f"cascade {str(cascade_id)[:8]} is {state}, not running")
    stages = record.get("stages")
    stage = block.get("stage")
    if isinstance(stages, list) and isinstance(stage, int) and 1 <= stage <= len(stages):
        entry = stages[stage - 1]
        closed = entry.get("state") if isinstance(entry, dict) else None
        _stale(closed not in _CLOSED_STAGES, record_path,
               f"stage {stage} of cascade {str(cascade_id)[:8]} is already {closed}")


#: The model selectors a stage's printed retry replaces with ``--models <model>``.
_MODEL_FLAGS = ("--models", "--quick")


def _stage_model(review_dir: PathLike, stage_file: Optional[PathLike]) -> Optional[str]:
    """The model of the stage whose round is on record, else of the manifest the run was given."""
    try:
        block = read_block(review_dir)
        if block is None and stage_file:
            block = load_manifest(stage_file)
    except CascadeProvenanceError:
        return None
    return str(block["model"]) if block else None


def retry_flags(
    review_dir: PathLike, flags: Sequence[str], *, stage_file: Optional[PathLike] = None,
) -> List[str]:
    """*flags* for a printed retry that runs *review_dir*'s review again (``--force``).

    When the round on record carries a ``cascade`` block (or, before it
    records one, the run was given *stage_file*, its hidden flag's
    manifest), the retry is the stage's own: every model selector in
    *flags* (``--models`` with its values, ``--quick``) gives way to
    ``--models <the stage's model>``. The carry rule keeps the block only on
    a fan-out of exactly that one model (:func:`resumes_stage`), and the
    replay flags of a review the composite ran in its own process are empty,
    so without this the retry fans out to the default list and the stage's
    round is discarded. Anything else, or a block that cannot be read (the
    run itself refuses that one), leaves *flags* as they are: a printed line
    never stops a run.
    """
    model = _stage_model(review_dir, stage_file)
    if model is None:
        return list(flags)
    kept: List[str] = []
    in_models = False
    for token in (str(flag) for flag in flags):
        head = token.split("=", 1)[0]
        if in_models and not token.startswith("-"):
            continue
        in_models = head == "--models" and "=" not in token
        if head in _MODEL_FLAGS:
            continue
        kept.append(token)
    return kept + ["--models", model]


def inputs_dir(block: Mapping[str, Any]) -> Path:
    """The stage's ``inputs/`` directory: the manifest's own."""
    return Path(str(block["manifest"])).parent


def input_path(block: Mapping[str, Any], name: str) -> Path:
    """The absolute path of the frozen input *name* of the block's stage."""
    if name not in INPUT_NAMES:
        raise ValueError(f"{name!r} is not a cascade input name")
    return inputs_dir(block) / name


def ledger_text(block: Optional[Mapping[str, Any]], name: str = REVIEWER_LEDGER) -> str:
    """The frozen input *name* of the block's stage, its hash verified; ``""`` without one.

    ``""`` when *block* is ``None`` (no cascade: today's bytes) or does not
    list *name* (an improve-code stage has no plan files). Raises
    :class:`CascadeProvenanceError` (exit 3) when the file is missing or its
    bytes no longer hash to the block's value.
    """
    if not block:
        return ""
    files = block.get("files") or {}
    if name not in files:
        return ""
    path = input_path(block, name)
    try:
        data = path.read_bytes()
    except FileNotFoundError as exc:
        raise CascadeProvenanceError(path, "does not exist") from exc
    except OSError as exc:
        raise CascadeProvenanceError(path, f"cannot be read ({exc.strerror or exc})") from exc
    if sha256_bytes(data) != files[name]:
        raise CascadeProvenanceError(path, "changed since the stage's manifest was written")
    return data.decode("utf-8")
