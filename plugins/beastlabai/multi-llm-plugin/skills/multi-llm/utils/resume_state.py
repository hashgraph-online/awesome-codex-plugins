"""``util resume-state <mode> <plan>``: which resume case a review phase is in.

A review core's resume step checks the phase dir for leftover work before it
launches an expensive fan-out. This command does that check with the helpers
the orchestrators' own guards use, and prints the answer as one line:

    [RESUME_STATE] case=d action=rerun models=codex:m1,pi:m2 batches=- flags=--force ownership=-

``case`` is a letter of :data:`CASES`, ``action`` a word of :data:`ACTIONS`;
``models`` is the full ``--models`` set a ``rerun`` launches, ``batches`` the
validation batch numbers a ``validate`` still owes, ``flags`` what a ``rerun``
adds, and ``ownership`` says why case c chose a re-run over the validation
files on disk: ``stale`` when one records another review round, ``uncertain``
when nothing ties them to the run the checkpoint records. ``-`` means none.
It never answers ``--rerun-all``.

Only the orchestrator's primary guard (``state.json``) completes a phase: no
file on disk does. Which round wrote a validation file is read from the round
id the fan-out stamps into ``.status.json`` and every file of its round
records (``utils/review_round.py``), never from a file date (a clock set back,
a copy that kept its dates or a coarse file system all defeat one). A file
written before round ids keeps the older proof, the checkpoint word; when
neither settles it, the answer is the one that can cost a re-run but never a
wrong result.

Read-only: it creates nothing, the plan's output folder included. The case
list in ``references/resume-detection.md`` is rendered from :data:`CASES` and
:data:`ACTIONS` (``tests/tools/render_resume_cases.py``; ``--check`` in the
tests keeps the two equal).
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import modes as mode_table

from . import result_files, review_round, status_file
from .cli_common import EXIT_NEEDS_HUMAN, EXIT_OK
from .json_extractor import sanitize_model_name
from .output_handler import output_dir_path, phase_dir_path

#: The line this command prints.
MARKER = "[RESUME_STATE]"

#: The phases with a resume step, and the mode words the help names for them.
REVIEW_PHASES: Tuple[str, ...] = ("review-plan", "review-tasks", "code-review")


@dataclass(frozen=True)
class Case:
    """One row of the case table: when it applies and what the host does."""

    letter: str
    when: str
    then: str


#: The cases, in the order they are read; the first that matches is the
#: answer (c names the b and f situations it leaves to them). Markdown,
#: rendered into references/resume-detection.md as is.
CASES: Tuple[Case, ...] = (
    Case(
        "a",
        "`state.json` records the phase complete: the orchestrator's own "
        "completed-phase guard. Files on disk never make a phase complete: a "
        "`--force` re-run leaves the previous round's `validation.json` and "
        "`report.md` in place until it regroups",
        "The phase is complete. Report results from `{plan}/{phase}/report.md` (or "
        "`report.html`) and skip (`report`). While `.status.json` records "
        "`checkpoint_recovered`, a note on stderr says so: the report was built from "
        "the answers the run that completed it checked, and a later run of the phase "
        "reuses no file in the folder.",
    ),
    Case(
        "b",
        "`{plan}/{phase}/validation_tasks.json` is this round's and lists its "
        "batches, no validation file is another round's (c), and "
        "`validation_batch_*.json` files exist (a retired round's `*.stale.json` "
        "does not count). This round's: the task file records the `round_id` "
        "`.status.json` beside it records (a fan-out stamps a fresh one there "
        "before it replaces any file); where either records none (written "
        "before round ids), when `.status.json` reads `state: "
        "\"validation_pending\"` (a run writes that word right after the task "
        "file, and the next fan-out's first write replaces it)",
        "Validation ran partially or fully. If every batch the task file lists has its "
        "`validation_batch_<N>.json`: run `--reaggregate` to finalize (`reaggregate`). "
        "If some are missing: run only the validation tasks of the missing batches "
        "(`batches=` names them), then reaggregate (`validate`).",
    ),
    Case(
        "c",
        "`validation.json`, `validation_tasks.json` or a `validation_batch_*.json` "
        "exists in `{plan}/{phase}/`, but nothing proves them this round's as in "
        "b and f: the task file or `validation.json` records a `round_id` other "
        "than the one `.status.json` records (`ownership=stale`: an earlier "
        "round's file a re-run stopped before replacing), or, where either "
        "records no round id, the checkpoint reads another state (a re-run's "
        "`models_running`, `models_complete` or `grouping_complete`, or a "
        "`complete` that `state.json` no longer records), or there is no "
        "checkpoint, no readable task file, or validation files without a task "
        "file (`ownership=uncertain`). No file date settles it",
        "Reporting, reaggregating or validating them could finish the phase on "
        "an earlier round's verdicts. Run the orchestrator again with `--force` "
        "(every phase) and the models `models_requested` records (`rerun`, "
        "`ownership=stale` or `ownership=uncertain`; `models=-` when none is "
        "recorded: launch with the selection the core would make). It keeps "
        "each reusable model result (`[SKIP]`), regroups, retires the verdicts "
        "its grouping does not bind and validates again. Never `--rerun-all`.",
    ),
    Case(
        "d",
        "no validation file (as in c), but per-model `*.json` result "
        "files (or a `grouped.json`) exist in `{plan}/{phase}/`, or `.status.json` "
        "reads a fan-out stage (`models_running`, `models_complete`, "
        "`grouping_complete`) and lists `models_requested`; or `.status.json` "
        "records `checkpoint_recovered` and `state.json` records the phase neither "
        "complete (a) nor stale (e), whatever files are there (checked right "
        "after a: an earlier run replaced the phase's damaged checkpoint, so no "
        "file in the folder counts, validation files included, and a "
        "`--reaggregate` refuses it); or `.status.json` exists but cannot be read "
        "(checked right after a too: a `--reaggregate` refuses it, and only a "
        "fresh run recovers a damaged one)",
        "The fan-out stopped before validation. Compare the files with "
        "`models_requested` in `{plan}/{phase}/.status.json`; a file counts when the "
        "fan-out would keep it (non-empty, a JSON list, and on review-code tied by "
        "the scope ledger `.review-scope.json` to the scope `review-scope.md` "
        "records). If every requested model has its file: run `--reaggregate`. If "
        "some have none: run the orchestrator again with the same models. With no "
        "file at all that is still the original run's whole selection. It keeps "
        "each file (`[SKIP]`) and runs only the missing ones; a `--reaggregate` "
        "would report without them. On review-code add `--force`, which a dir "
        "holding results "
        "or an earlier round's files needs (exit 3 otherwise); a composite's flags "
        "line already carries it. Never `--rerun-all`. Left out, `--scope-policy` "
        "stays the one the kept files were requested under (one `Scope policy "
        "notice:` line says so); a different one typed stops at exit 3 with "
        "`[SCOPE_POLICY_CONFLICT]`. The first answer is `reaggregate`; the second is "
        "`rerun`, its `models=` listing every requested model. Over a checkpoint "
        "that cannot be read the answer is `rerun` with `models=-`: nothing records "
        "the selection, so launch with the one the core would make; the fresh run "
        "recovers a damaged checkpoint, reusing no file in the folder, and a note on "
        "stderr says what to do when it cannot.",
    ),
    Case(
        "e",
        "none of the other cases; or `state.json` records a code review completed "
        "before the latest implement (checked first: its files are out of date)",
        "Nothing to resume: run the orchestrator as planned (`run`). A code review "
        "older than the latest implement is re-run as `--force` by the orchestrator "
        "itself; while its `.status.json` records `checkpoint_recovered`, a note on "
        "stderr says the run reuses no file in the folder.",
    ),
    Case(
        "f",
        "`validation_tasks.json` is this round's and lists its batches, no "
        "validation file is another round's (both as in b), and NO "
        "`validation_batch_*.json` exists",
        "The orchestrator handed validation over and none has run. Skip to "
        "Validation Handling: run every validation task, then reaggregate "
        "(`validate`).",
    ),
)

#: The action words, and what each tells the host to do.
ACTIONS: Dict[str, str] = {
    "report": "the phase is complete: report its results and run no orchestrator.",
    "reaggregate": "run the orchestrator's `--reaggregate`; no model runs.",
    "validate": "go to the validation step: run the validation tasks (only the "
                "batches `batches=` names, when it names any), then `--reaggregate`.",
    "rerun": "launch the orchestrator again with `--models` exactly as `models=` lists "
             "them (`-`: none recorded, so the selection the core would make) and the "
             "`flags=` added; models with a result keep it (`[SKIP]`).",
    "run": "nothing to resume: launch the orchestrator as planned.",
}

#: The ``ownership=`` values of case c, and what they tell a reader.
OWNERSHIP_UNCERTAIN = "uncertain"
OWNERSHIP_STALE = "stale"
OWNERSHIP_NOTE = (
    "`ownership=` says why case c chose a `rerun` over the validation files on "
    "disk: `stale` when one records a review round other than the one "
    "`.status.json` records, `uncertain` when nothing recorded ties them to "
    "that run. Every other answer prints `ownership=-`."
)

#: Where the rendered case list sits in references/resume-detection.md.
DOC_BEGIN = "<!-- BEGIN GENERATED: resume cases (utils/resume_state.py) -->"
DOC_END = "<!-- END GENERATED: resume cases -->"


@dataclass(frozen=True)
class ResumeState:
    """The answer: a case letter, an action word and what the action needs.

    ``note`` is for a person, printed on stderr: never part of the line.
    """

    case: str
    action: str
    models: Tuple[str, ...] = ()
    batches: Tuple[int, ...] = ()
    flags: Tuple[str, ...] = ()
    ownership: str = "-"
    note: str = ""

    def line(self) -> str:
        def joined(values: Sequence[Any]) -> str:
            return ",".join(str(value) for value in values) or "-"

        return (f"{MARKER} case={self.case} action={self.action} "
                f"models={joined(self.models)} batches={joined(self.batches)} "
                f"flags={' '.join(self.flags) or '-'} ownership={self.ownership or '-'}")


def _state_facts(plan: Path, phase: str) -> Tuple[bool, bool]:
    """``(completed, stale)`` from ``state.json``, as the orchestrator's primary
    guard reads it (``is_phase_completed``, ``phase_completion_is_stale``).

    No file is no record. ``StateManager`` creates the output folder, so it is
    built only over a file that exists; one it cannot read records nothing.
    """
    if not (output_dir_path(plan) / "state.json").is_file():
        return False, False
    # Imported here to keep resume_state light.
    from .state_manager import StateManager

    try:
        state = StateManager(plan, read_only=True)
        return state.is_phase_completed(phase), state.phase_completion_is_stale(phase)
    except Exception as exc:  # noqa: BLE001 - the files decide instead
        print(f"multi-llm: state.json could not be read ({exc}); "
              "judging from the phase folder alone.", file=sys.stderr)
        return False, False


def _batch_files(phase_dir: Path) -> List[str]:
    """The validation batch files, as code-review's partial-completion guard
    counts them: a retired round's ``*.stale.json`` is not one."""
    return [
        path for path in glob.glob(str(phase_dir / "validation_batch_*.json"))
        if not path.endswith(".stale.json")
    ]


def _listed_batches(tasks_path: Path) -> Optional[List[int]]:
    """The batch numbers ``validation_tasks.json`` lists, or ``None`` when it
    cannot be read, lists none, or lists a count other than its own
    ``total_batches`` (the reaggregate's completeness test compares the two)."""
    try:
        with open(tasks_path, encoding="utf-8") as handle:
            document = json.load(handle)
        listed = [int(batch["batch_index"]) for batch in document["batches"]]
        total = document.get("total_batches", len(listed))
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return None
    if not listed or total != len(listed) or len(set(listed)) != len(listed):
        return None
    return listed


def _missing_batches(phase_dir: Path, listed: Optional[List[int]]) -> List[int]:
    """Of *listed*, the batches with no ``validation_batch_<N>.json`` (the
    merge's own test, ``merge_batched_validation_results``)."""
    return [index for index in listed or []
            if not (phase_dir / f"validation_batch_{index}.json").exists()]


def _has_result_files(phase_dir: Path, phase: str) -> bool:
    """Whether per-model result files are on disk: review-code's
    partial-completion guard's reader there, the round's reader elsewhere."""
    if phase == "code-review":
        # Imported here to keep resume_state light.
        import code_review_orchestrator as review_code

        return bool(review_code.leftover_model_results(phase_dir))
    return bool(result_files.snapshot_candidates(phase_dir))


def _requested_models(status: Dict[str, Any]) -> List[str]:
    """``models_requested`` from ``.status.json``, in order; ``[]`` for none."""
    recorded = status.get("models_requested")
    if isinstance(recorded, dict):
        recorded = list(recorded)
    if not isinstance(recorded, list):
        return []
    return [str(spec) for spec in recorded if isinstance(spec, str) and spec]


#: The ``.status.json`` states of a fan-out that stopped before it handed
#: validation over (``references/interrupted-run-recovery.md``, step 2).
FANOUT_STATES = frozenset({"models_running", "models_complete", "grouping_complete"})


#: The ``.status.json`` state that proves a ``validation_tasks.json`` *with no
#: round id* (written before round ids) is the round's own. Every writer of the
#: task file writes it next (the fan-out's hand-off, a ``--reaggregate`` that
#: materializes or reopens a round: ``reopen_phase_for_validation``), and every
#: fan-out's opening write replaces it with ``models_running``. A task file with
#: a round id is judged by that id instead (``utils/review_round.py``). Nothing
#: else proves either: a file date cannot (see the module docstring), and
#: ``progress`` is display only (``utils/status_file``).
VALIDATION_STATE = review_round.VALIDATION_PENDING


def _validation_files(phase_dir: Path) -> List[str]:
    """The validation files a reaggregate or a validation step would reuse:
    ``validation.json``, ``validation_tasks.json`` and the batch files."""
    names = [name for name in ("validation.json", "validation_tasks.json")
             if (phase_dir / name).is_file()]
    return names + sorted(Path(path).name for path in _batch_files(phase_dir))


def _this_round_s_batches(phase_dir: Path, status: Dict[str, Any],
                          rounds: "review_round.RoundFiles") -> Optional[List[int]]:
    """The batches of ``validation_tasks.json`` when it is this round's (its
    round id, or for a file without one :data:`VALIDATION_STATE`:
    ``review_round.tasks_file_is_this_rounds``); ``None`` when it is not."""
    if not review_round.tasks_file_is_this_rounds(rounds, status):
        return None
    return _listed_batches(phase_dir / review_round.TASKS_NAME)


_RERUN_SENTENCE = ("Re-running with --force keeps every reusable model result, "
                   "regroups and retires the verdicts its grouping does not bind.")


def _uncertain_note(phase_dir: Path, status: Dict[str, Any], files: Sequence[str]) -> str:
    recorded = status.get("state")
    reads = f"reads `{recorded}`" if isinstance(recorded, str) and recorded else "records no state"
    return (f"multi-llm: {', '.join(files)} in {phase_dir} may be an earlier round's: "
            f".status.json {reads}, and only a matching round id, or for a task file "
            f"without one `{VALIDATION_STATE}` beside it, ties them to this run. "
            + _RERUN_SENTENCE)


def _stale_note(phase_dir: Path, rounds: "review_round.RoundFiles",
                stale: Sequence[str], status: Dict[str, Any]) -> str:
    return (f"multi-llm: {', '.join(stale)} in {phase_dir} belong to an earlier "
            f"review round ({review_round.evidence(rounds, tuple(stale), status)}): "
            "a re-run stopped before replacing them. " + _RERUN_SENTENCE)


def _recovered_note(phase_dir: Path, action: str = "rerun") -> str:
    """The note of a phase whose checkpoint records ``RECOVERED_KEY``, for the
    *action* its case answers: ``rerun`` (no file there counts), ``report``
    (the phase completed after the recovery) or ``run`` (a stale completion)."""
    head = f"multi-llm: an earlier run replaced the damaged checkpoint of {phase_dir}"
    tail = "Move the whole phase folder aside to start clean."
    if action == "report":
        return (f"{head}; its report was built from the answers that run checked, "
                "never from the files there, and a later run of the phase reuses no "
                "result or validation file there (its --reaggregate refuses). " + tail)
    if action == "run":
        return (f"{head}, so the run reuses no result or validation file there: every "
                "selected model runs again. " + tail)
    return (f"{head}, so no result or validation file there is reused: every requested "
            "model runs again. " + tail)


def _unreadable_note(phase_dir: Path, phase: str) -> str:
    """The note of a phase whose ``.status.json`` cannot be read: a
    ``--reaggregate`` refuses it, so the answer is a fresh run, which
    recovers a damaged one."""
    return (f"multi-llm: {status_file.status_path(str(phase_dir))} cannot be read, so "
            f"a --reaggregate would refuse it and nothing records the models to "
            f"re-run: launch the phase with the selection the core would make. "
            f"{status_file.unreadable_checkpoint_advice(str(phase_dir), phase=phase)}")


def _with_recovery_note(answer: ResumeState, phase_dir: Path) -> ResumeState:
    """*answer*, with the recovery note while the phase's checkpoint records
    ``RECOVERED_KEY``: a completed or stale phase keeps its case, and the note
    says no file in the folder is reused."""
    if not result_files.phase_recovered(phase_dir):
        return answer
    return ResumeState(answer.case, answer.action, models=answer.models,
                       batches=answer.batches, flags=answer.flags,
                       ownership=answer.ownership,
                       note=_recovered_note(phase_dir, answer.action))


def _recorded_scope(phase_dir: Path) -> Optional[str]:
    """The scope id of the review set on disk, the one a ``--reaggregate``
    reports and an unchanged change's fan-out recomputes; ``None`` when the
    ``review-scope.md`` + ``diff/`` pair is missing or incomplete."""
    # Imported here to keep resume_state light.
    from .git_utils import load_review_scope

    header = load_review_scope(phase_dir)
    return header.scope_id if header is not None else None


def _kept_on_rerun(phase_dir: Path, phase: str, spec: str) -> bool:
    """Whether a re-run keeps *spec*'s result: the fan-out's own ``[SKIP]`` test.

    review-plan and review-tasks keep a non-empty ``<sanitized spec>.json``
    holding a JSON list. review-code also needs the scope ledger to tie it to
    the scope the re-run reviews (``existing_result_reuse``, the predicate
    ``run_all_reviews`` calls); the re-run always computes one, so with no
    review set on disk nothing counts as kept. Neither keeps the file of a
    model the phase withholds (``result_files.withheld_models``: a slot that
    failed its safety checks or ended before they passed).
    """
    stem = sanitize_model_name(spec)
    if phase == "code-review":
        # Imported here to keep resume_state light.
        import code_review_orchestrator as review_code

        scope_id = _recorded_scope(phase_dir)
        if scope_id is None:
            return False
        return review_code.existing_result_reuse(phase_dir, stem, scope_id).verdict == "reuse"
    if spec in result_files.withheld_models(phase_dir):
        return False
    path = phase_dir / f"{stem}.json"
    try:
        if not path.is_file() or path.stat().st_size == 0:
            return False
        with open(path, encoding="utf-8") as handle:
            return isinstance(json.load(handle), list)
    except (OSError, ValueError):
        return False


def _rerun(phase: str, requested: Sequence[str]) -> ResumeState:
    """Case d's ``rerun`` with the original run's full selection. review-code
    adds ``--force``: its partial-completion guard refuses a plain run over a
    dir holding results or an earlier round's files."""
    flags = ("--force",) if phase == "code-review" else ()
    return ResumeState("d", "rerun", models=tuple(requested), flags=flags)


def classify(plan: Path, phase: str) -> ResumeState:
    """The resume case of *phase* for *plan* (:data:`CASES`)."""
    phase_dir = phase_dir_path(plan, phase)
    completed, stale = _state_facts(plan, phase)
    # state.json decides first, a recovery record or not: a phase completed
    # after its recovery reported the answers that run checked in memory
    # (docs/development/review-results.md, "Recovering a damaged one").
    if stale:
        return _with_recovery_note(ResumeState("e", "run"), phase_dir)
    if completed:
        return _with_recovery_note(ResumeState("a", "report"), phase_dir)
    try:
        status = status_file.load_status(
            str(phase_dir), attempts=status_file.CHECKPOINT_READ_ATTEMPTS) or {}
    except status_file.CheckpointUnreadable:
        # A --reaggregate refuses a checkpoint it cannot read, and only a fresh
        # run recovers a damaged one (docs/development/review-results.md,
        # "Recovering a damaged one"); nothing in it names the selection.
        rerun = _rerun(phase, ())
        return ResumeState(rerun.case, rerun.action, flags=rerun.flags,
                           note=_unreadable_note(phase_dir, phase))
    rounds = review_round.round_files(phase_dir, status)
    requested = _requested_models(status)
    if result_files.RECOVERED_KEY in status:
        # A recovered phase trusts no file on disk: nothing is reusable, and
        # its --reaggregate refuses (utils/result_files.py, RECOVERED_KEY).
        rerun = _rerun(phase, requested)
        return ResumeState(rerun.case, rerun.action, models=rerun.models,
                           flags=rerun.flags, note=_recovered_note(phase_dir))
    earlier = rounds.stale()
    if earlier:
        # Proven another round's by the ids, so neither b nor f may read them.
        return ResumeState("c", "rerun", models=tuple(requested), flags=("--force",),
                           ownership=OWNERSHIP_STALE,
                           note=_stale_note(phase_dir, rounds, earlier, status))
    listed = _this_round_s_batches(phase_dir, status, rounds)
    if listed is not None:
        if _batch_files(phase_dir):
            missing = _missing_batches(phase_dir, listed)
            if missing:
                return ResumeState("b", "validate", batches=tuple(missing))
            return ResumeState("b", "reaggregate")
        return ResumeState("f", "validate", batches=tuple(listed))
    files = _validation_files(phase_dir)
    if files:
        # Every phase takes --force here: it is the command that started the
        # round now in doubt, and review-code's partial-completion guard needs it.
        return ResumeState("c", "rerun", models=tuple(requested), flags=("--force",),
                           ownership=OWNERSHIP_UNCERTAIN,
                           note=_uncertain_note(phase_dir, status, files))
    if (phase_dir / "grouped.json").is_file() or _has_result_files(phase_dir, phase):
        if any(not _kept_on_rerun(phase_dir, phase, spec) for spec in requested):
            return _rerun(phase, requested)
        return ResumeState("d", "reaggregate")
    if requested and status.get("state") in FANOUT_STATES:
        # Interrupted before any model wrote a result: the checkpoint still
        # names the selection, which the resume keeps whole (U30's unattended
        # rule, references/interrupted-run-recovery.md step 4).
        return _rerun(phase, requested)
    return ResumeState("e", "run")


# ---------------------------------------------------------------------------
# references/resume-detection.md
# ---------------------------------------------------------------------------

def render_cases() -> str:
    """The generated block of ``references/resume-detection.md``, markers included."""
    lines = [
        DOC_BEGIN,
        "Check in this order; the first case that matches is the answer. "
        "`util resume-state` prints it as "
        "`[RESUME_STATE] case=<a-f> action=<word> models=<…> batches=<…> flags=<…> "
        "ownership=<…>`.",
        "",
    ]
    for case in CASES:
        lines.append(f"{case.letter}. If {case.when}:")
        lines.append(f"   -> {case.then}")
        lines.append("")
    lines.append("The action words:")
    lines.append("")
    for word, meaning in ACTIONS.items():
        lines.append(f"- `{word}`: {meaning}")
    lines.append("")
    lines.append(OWNERSHIP_NOTE)
    lines.append(DOC_END)
    return "\n".join(lines)


def splice_cases(document: str) -> str:
    """*document* with its generated block replaced by :func:`render_cases`.
    Raises ``ValueError`` when the markers are missing."""
    start = document.index(DOC_BEGIN)
    end = document.index(DOC_END, start) + len(DOC_END)
    return document[:start] + render_cases() + document[end:]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="multi_llm.py util resume-state",
        description=("Print a review phase's resume case and what to do about it "
                     "(read-only; references/resume-detection.md lists the cases)."),
    )
    parser.add_argument("mode", help="review-plan, review-tasks or review-code "
                                     "(review-commits reads review-code's phase)")
    parser.add_argument("plan", help="the plan path (a commit mode's brief)")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    mode = mode_table.resolve(args.mode)
    if mode is None or mode.phase not in REVIEW_PHASES:
        print(f"ERROR: util resume-state: '{args.mode}' has no resume step; it "
              "reads review-plan, review-tasks and review-code (review-commits "
              "too).", file=sys.stderr)
        return EXIT_NEEDS_HUMAN
    plan = Path(os.path.abspath(args.plan))
    if not plan.is_file():
        print(f"ERROR: util resume-state: plan not found: {args.plan}", file=sys.stderr)
        return EXIT_NEEDS_HUMAN
    answer = classify(plan.resolve(), mode.phase)
    if answer.note:
        print(answer.note, file=sys.stderr)
    print(answer.line())
    return EXIT_OK
