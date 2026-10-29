#!/usr/bin/env python3
"""Finalize file tracking after implementation completes.

Usage:
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util finalize-tracking --state-file <path_to_state.json>

This script:
1. Gets all currently modified files (using shared git utils)
2. Subtracts pre_existing_changes recorded at start
3. Stores the result in state.tracked_files

With ``--only-touched`` it skips all of that and stores exactly the
``--touched`` paths: the route for an implementer that ran outside
``/multi-llm implement`` and so recorded no baseline to subtract.

This approach is more reliable than parsing subagent output because:
- Git utilities always capture all changes consistently
- Subagents may not report all files they touch
- Files created then modified only appear once
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.stream_bootstrap import bootstrap_streams
from utils import get_modified_files as utils_get_modified_files
from utils import (
    baseline_covers,
    get_staged_files,
    list_untracked_files,
    subtract_baseline,
)
from utils.commit_review import commit_review_artifact, commit_reviews_folder_rel
from utils.git_utils import (
    GitError,
    get_project_root_from_dir,
    head_or_empty_tree,
    ignored_paths,
    paths_in_commit,
)
from utils.metrics import StateLockTimeout, state_file_lock
from utils.output_handler import workflow_file_entries
from utils.state_manager import compute_plan_hash, mark_phase_completed_in_state

# A tracked-file dump is a reference list, not a reading; state.json holds all
# of it. Measured 2026-09-16: a run that tracked 1 511 files spent 1 512 of its
# 1 585 log lines on this list, burying the batch outcomes either side of it.
MAX_LISTED_PATHS = 20

#: The phases that change code, and the ``task_id`` each one's entries carry
#: in ``tracked_files``. Only these record it: apply-suggestions and
#: apply-task-suggestions edit the plan and the task list, which are never code
#: under review. ``implementation`` is the label every entry carried before
#: apply-code-fixes had its own, so implement's entries read as before.
TRACKING_LABELS = {"implement": "implementation", "apply-code-fixes": "apply-code-fixes"}


def get_all_modified_files() -> Set[str]:
    """
    Get all currently modified files (staged and unstaged).

    Uses the same git utilities as implement_orchestrator.py for consistency.
    """
    modified = set()

    try:
        # Use consistent utils from git_utils.py
        unstaged = set(f for f in utils_get_modified_files() if f)
        staged = set(f for f in get_staged_files() if f)
        modified = unstaged | staged
    except Exception as e:
        print(f"Warning: Failed to get modified files: {e}", file=sys.stderr)

    return modified


def _expand_uncovered_directories(entries: Set[str]) -> Set[str]:
    """Replace each surviving ``dir/`` entry with the files inside it.

    The census is deliberately directory-granular (see
    ``git_utils.get_modified_files``), which is what lets the stored baselines
    subtract a whole pre-existing tree. What survives that subtraction is a
    directory the *phase itself* created, and a directory path is useless to
    every consumer: `capture_diff_hunks` finds no per-file diff for it and
    skips it silently, so on the native leg (no ``--touched``) `review-code`
    reports the entry and reviews none of the new module's files (F2,
    2026-09-16).

    Only the survivors are expanded, so a baseline-covered ``plans/`` with
    1 511 files under it is never listed — that expansion is the regression
    6260c9e reverted, and it must not come back. An entry git can no longer
    list is kept as-is rather than silently dropped.
    """
    expanded: Set[str] = set()
    for entry in entries:
        if not entry.endswith("/"):
            expanded.add(entry)
            continue
        files = list_untracked_files(entry)
        expanded.update(files or {entry})
    return expanded


def _write_state_atomic(state_path: Path, state: dict) -> None:
    """Keep the previous state intact if either finalization write fails."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(
        dir=str(state_path.parent), suffix=".tmp", prefix=".tracking_",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)
        os.replace(temp_path, str(state_path))
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def _restamp_plan_hash(state_path: Path, plan_path: Path) -> None:
    """Re-stamp ``plan_hash`` after this command's own edit to the plan.

    ``--plan-file`` makes this a plan writer, and it writes after the state
    file above. Left alone, the next ``StateManager`` built on this plan hashes
    content the stored ``plan_hash`` no longer matches, records
    ``plan_changed`` and ``implement --resume`` reports "Plan has changed since
    last session" about the plugin's own back-reference insertion. The executor
    leg re-stamps at exactly this point (``WriteBatchScheduler._finalize``,
    after ``_insert_plan_reference``); this is the native leg's counterpart.

    Best-effort and never fatal: a failure here costs a spurious warning, and
    the census — this command's actual job — is already on disk.
    """
    try:
        with state_file_lock(state_path):
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if not isinstance(state, dict) or "plan_hash" not in state:
                # No hash recorded means nothing reads one; do not invent a field.
                return
            state["plan_hash"] = compute_plan_hash(plan_path)
            state.pop("plan_changed", None)
            _write_state_atomic(state_path, state)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Warning: could not re-stamp plan_hash: {e}", file=sys.stderr)


def _print_path_list(entries) -> None:
    """Print at most ``MAX_LISTED_PATHS`` of the tracked entries."""
    for entry in entries[:MAX_LISTED_PATHS]:
        print(f"  - {entry['path']}")
    remaining = len(entries) - MAX_LISTED_PATHS
    if remaining > 0:
        print(f"  … and {remaining} more (see state.json.tracked_files)")


def main(argv=None) -> int:
    """Main entry point."""
    bootstrap_streams()
    parser = argparse.ArgumentParser(
        description="Finalize file tracking after implementation"
    )
    parser.add_argument(
        "--state-file",
        required=True,
        help="Path to state JSON file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be tracked without updating state"
    )
    # The write executor verifies every batch by a pre-batch snapshot
    # comparison, so it knows which files a batch changed better than a git
    # diff does. A file that was already modified before the phase started
    # sits in pre_existing_changes and would be subtracted below along with
    # the genuinely unrelated ones — measured 2026-09-16, a nine-batch run that
    # edited only an already-dirty index.html tracked one stray file and the
    # code review that followed would have reviewed that file instead.
    parser.add_argument(
        "--touched",
        action="append",
        default=[],
        metavar="PATH",
        help="A repo-relative file the implementation changed; kept in "
             "tracked_files even when it was modified before the phase started "
             "(repeatable). It only ADDS paths and never removes a dirty one: "
             "without --only-touched the whole dirty census minus "
             "pre_existing_changes is still tracked beside it",
    )
    # The exact-scope route for an implementer that ran outside `/multi-llm
    # implement` and so recorded no `pre_existing_changes` baseline (review-scope
    # plan §2 D2.6). Plain `--touched` only unions its paths into the census, so
    # with no baseline every unrelated dirty or untracked path stays in — and a
    # non-empty `tracked_files` silences review-code's `[SCOPE_FALLBACK]` and is
    # labelled as the phase's own scope, so the over-wide list goes unnoticed.
    parser.add_argument(
        "--only-touched",
        action="store_true",
        help="Make tracked_files exactly the --touched paths (de-duplicated, "
             "sorted): the git census, the pre_existing_changes subtraction and "
             "the directory expansion are skipped, and pre_existing_changes is "
             "neither read nor written. Requires at least one --touched",
    )
    # The implementation summary's back-reference used to be an inline `python -c`
    # in instructions/implement.md that put the skill dir on sys.path by hand. That
    # made the instruction core carry a second skill-dir substitution site and a
    # block of Python for an agent to retype; the insertion is deterministic, so it
    # belongs behind the same command that finalizes tracking.
    parser.add_argument(
        "--plan-file",
        help="Plan file to insert the implementation-summary reference into "
             "(requires --summary-file-relative)"
    )
    parser.add_argument(
        "--summary-file-relative",
        help="Summary path, relative to the plan's parent directory, as printed "
             "by the orchestrator's summary_file_relative field"
    )
    # The native leg's completion write, the counterpart of
    # `WriteBatchScheduler._finalize`'s `mark_phase_completed("implement")`.
    # The orchestrator records the phase *started* when it emits the task
    # JSON; this flag, on the instruction's closing call (after every task,
    # the verify step and the summary), is the only place the native path
    # records it completed, so a host that stopped early leaves it
    # `in_progress` and `--resume` is offered.
    parser.add_argument(
        "--mark-completed",
        action="store_true",
        help="Record the implement phase completed in state.json (the "
             "instruction's closing step; never before every task has run and "
             "the repository's own check passed)",
    )
    # Which code phase this census belongs to. Its entries are replaced; the
    # other code phase's entries are kept as that phase recorded them, so
    # apply-code-fixes never re-labels a file implement created and a resumed
    # implement never takes over a file apply-code-fixes created.
    parser.add_argument(
        "--phase",
        choices=sorted(TRACKING_LABELS),
        default="implement",
        help="The code phase whose changes this records (default: implement). "
             "Entries another code phase recorded are kept as they are",
    )
    args = parser.parse_args(argv)

    if bool(args.plan_file) != bool(args.summary_file_relative):
        print(
            "ERROR: --plan-file and --summary-file-relative are used together: "
            "one names the plan to update, the other the reference to insert.",
            file=sys.stderr,
        )
        return 1

    given = sorted({f.strip() for f in args.touched if f and f.strip()})
    args.touched = _drop_ignored(args.touched)
    explicit_scope = sorted({f.strip() for f in args.touched if f and f.strip()})
    if args.only_touched and not explicit_scope:
        # Refused before the state file is even read: an empty explicit list
        # would empty `tracked_files`, and review-code would then quietly fall
        # back to the whole `git diff` — the scope this flag exists to replace.
        # Said honestly when paths WERE given and every one was gitignored
        # (adversarial review, 2026-10-02): "needs at least one --touched"
        # beside a command that passed three sent the reader to the wrong fix.
        if given:
            print(
                f"ERROR: --only-touched was given {len(given)} --touched path(s) "
                f"and every one is gitignored ({', '.join(given[:5])}"
                f"{', …' if len(given) > 5 else ''}), so there is nothing to "
                f"track: tracked_files would be empty, which would send "
                f"review-code back to its git-diff fallback.",
                file=sys.stderr,
            )
        else:
            print(
                "ERROR: --only-touched needs at least one --touched <path>: it "
                "makes tracked_files exactly those paths, and an empty list "
                "would send review-code back to its git-diff fallback.",
                file=sys.stderr,
            )
        return 1

    state_path = Path(args.state_file)

    if not state_path.exists():
        print(f"ERROR: State file not found: {state_path}", file=sys.stderr)
        return 1

    # One lock from the read to the write (fix round 8): `util batch-done`,
    # `util metrics` and this command are separate processes a host may run
    # side by side, and each rewrites the whole file.
    try:
        with state_file_lock(state_path):
            outcome = _record_tracked_files(args, state_path, explicit_scope)
            if outcome == 3 and args.phase == "implement":
                # Refused because a check holds tasks: the run still ends
                # here, so its own edits after the check are stamped as part
                # of the check's tree, or the next `--resume` reads them as
                # a change and hands the check out again (fix round 15).
                _restamp_check_trees(state_path)
    except StateLockTimeout as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    if isinstance(outcome, int):
        return outcome
    tracked_files = outcome

    print(f"\nTracked {len(tracked_files)} implementation files:")
    _print_path_list(tracked_files)

    print(f"\nState file updated: {state_path}")
    if args.mark_completed:
        print("Phase implement marked completed")

    if args.plan_file:
        code = _insert_summary_reference(args.plan_file, args.summary_file_relative)
        if code:
            return code
        _restamp_plan_hash(state_path, Path(args.plan_file))
    if args.phase == "implement":
        # Last, after this command's own edit to the plan: the tree the run
        # ends on is the one a `--resume` compares against.
        _restamp_check_trees(state_path)
    return 0


def _restamp_check_trees(state_path: Path) -> None:
    """Stamp each check whose findings hold tasks with the tree as the run
    leaves it (fix round 14, the native counterpart of the executor's
    ``WriteBatchScheduler._restamp_check_trees``).

    ``util batch-done --check findings`` stamps the tree when the check is
    recorded, and the tasks that do not depend on it go on and edit files
    after it, so a ``--resume`` the user changed nothing for would read "the
    files changed" and hand the check out again: on the stop fixture's
    resume with nothing changed, Claude Code re-ran T002 (a new subagent,
    ~23k tokens) for the same findings. The run's own edits are not a change
    the user made, so this command — the native run's closing call — re-stamps
    every stamp still standing; a stamp on a check that passed, failed or was
    accepted is dropped. Only a check stamped before keeps one: one the emit
    handed out again and nobody re-ran has none, and runs on the next resume.
    Best-effort and silent: a check with no stamp is run again.
    """
    try:
        from utils.state_manager import (
            TASK_CHECK_TREES_KEY,
            set_task_check_tree_in_state,
        )
        from utils.write_batch_scheduler import rerunnable_checks
        from utils.write_prompt import check_tree_fingerprint
    except ImportError:  # pragma: no cover - the skill is always on the path
        return
    try:
        with state_file_lock(state_path):
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if not isinstance(state, dict):
                return
            stamped = state.get(TASK_CHECK_TREES_KEY)
            if not isinstance(stamped, dict) or not stamped:
                return
            held = set(rerunnable_checks(state))
            current = check_tree_fingerprint(state_path.parent / "implement")
            changed = False
            for task_id in sorted(stamped):
                if task_id not in held:
                    set_task_check_tree_in_state(state, task_id, None)
                    changed = True
                elif current is not None and stamped[task_id] != current:
                    set_task_check_tree_in_state(state, task_id, current)
                    changed = True
            if changed:
                _write_state_atomic(state_path, state)
    except (StateLockTimeout, OSError, ValueError):
        return


def _record_tracked_files(args, state_path: Path, explicit_scope: List[str]):
    """Read *state_path*, record its ``tracked_files`` and write it back.

    ``main``'s read-modify-write, run under ``metrics.state_file_lock``.
    Returns the entries written, or an exit code: ``1`` for an unreadable
    or failed write, ``0`` for a ``--dry-run`` (which writes nothing).
    """
    # Load state
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse state file: {e}", file=sys.stderr)
        return 1

    # Validate state structure
    if not isinstance(state, dict):
        print("ERROR: State file is not a JSON object", file=sys.stderr)
        return 1

    label = TRACKING_LABELS[args.phase]
    if args.only_touched:
        explicit_scope = _drop_workflow_files(
            explicit_scope, _workflow_entries(state, state_path), print,
        )
        if not explicit_scope:
            print(
                "ERROR: --only-touched was given only the workflow's own files "
                "(the plan, its task list, its output folder or commit "
                "reviews), so there is nothing to track: they are never code "
                "under review.",
                file=sys.stderr,
            )
            return 1
        # No baseline on this route: a path is `created` when the base tree
        # lacks it (`_file_actions`), never because of pre_existing_changes.
        tracked_files = _tracked_entries(
            explicit_scope,
            _file_actions(explicit_scope, base_ref=state.get("head_before_implement")),
            label,
        )
        print(
            f"Explicit scope (--only-touched): {len(tracked_files)} files "
            f"(the git census and pre_existing_changes were not consulted)"
        )
    else:
        tracked_files = phase_tracked_files(
            state, args.touched, state_path=state_path, phase=args.phase,
            drop_ignored=False,
        )

    if args.dry_run:
        print("\nDry run - would track these files:")
        _print_path_list(tracked_files)
        return 0

    if args.mark_completed:
        held = _held_by_a_check(state, state_path)
        if held:
            # Fix round 11: a task a check with findings holds back never
            # ran, so the phase is not complete — the native leg's
            # counterpart of the executor ending needs-human.
            named = ", ".join(f"{task_id} (waits for {check_id})" for task_id, check_id in held)
            print(
                f"ERROR: implement is not complete: {named} did not run, "
                f"because a check it depends on reported problems, so "
                f"implement stays in progress and tracked_files was not "
                f"recorded. Run this command again without "
                f"--mark-completed, and report "
                f"the way forward: fix what the check reported and re-run "
                f"implement with --resume, or accept its findings with "
                f"--resume --human-task <check id>=done (the held tasks then "
                f"run, told that the findings were accepted).",
                file=sys.stderr,
            )
            return 3

    # Update state
    state["tracked_files"] = tracked_files
    state["updated_at"] = datetime.now().isoformat()
    if args.mark_completed and not _completion_stands(state):
        mark_phase_completed_in_state(state, "implement")

    try:
        _write_state_atomic(state_path, state)
    except OSError as e:
        print(f"ERROR: Failed to write state file: {e}", file=sys.stderr)
        return 1

    return tracked_files


def _completion_stands(state: dict) -> bool:
    """Whether implement's completion is on record and no run reopened it.

    ``--mark-completed`` closes the run an emit started (``phases_started``);
    with no start newer than the completion there is no run to close, so the
    completion keeps its date (fix round 14: a native resume that only
    recorded ``--human-task T007=done`` for a deferred manual task re-stamped
    implement, and review-code and apply-code-fixes read stale for no code
    change). The ``StateManager.is_phase_started`` rule, on the raw dict.
    """
    from utils.state_manager import _parse_completion_time

    completed = _parse_completion_time(
        (state.get("phases_completed") or {}).get("implement")
    )
    if completed is None:
        return False
    started = _parse_completion_time(
        (state.get("phases_started") or {}).get("implement")
        if isinstance(state.get("phases_started"), dict) else None
    )
    return started is None or started <= completed


def _held_by_a_check(
    state: dict, state_path: Optional[Path] = None,
) -> List[Tuple[str, str]]:
    """``(task id, check id)`` for each implement task still held back.

    Computed the way ``util write-prompt`` decides
    (``write_batch_scheduler.held_back_by_checks``): every task that has not
    run (neither ``completed`` nor ``skipped``) with a check whose findings
    hold (``rerunnable_checks``) upstream of it in the whole decomposition —
    ``state.json``'s recorded graph plus the phase's ``write_tasks.json``
    beside it. Fix round 12: this used to read the hold off the recorded
    reason alone, and with two checks holding one task, recording the first
    passed cleared the reason while the second's findings stood, so
    ``--mark-completed`` completed implement with that task unrun. A task
    still ``pending`` with a ``not run — upstream check <id> reported
    problems`` reason is held too (a state with no graph on record), scoped
    to the decomposition implement ran last when it is on record.
    """
    try:
        from utils.write_batch_scheduler import (
            BLOCKED_BY_CHECK_PREFIX,
            held_back_by_checks,
        )
        from utils.write_phase_bridge import WRITE_TASK_FILENAME
    except ImportError:  # pragma: no cover - the skill is always on the path
        return []
    tasks: list = []
    if state_path is not None:
        try:
            document = json.loads(
                (Path(state_path).parent / "implement" / WRITE_TASK_FILENAME)
                .read_text(encoding="utf-8")
            )
            if isinstance(document, dict):
                found = document.get("batches") or document.get("tasks") or []
                tasks = found if isinstance(found, list) else []
        except (OSError, ValueError):
            tasks = []
    held: Dict[str, str] = dict(held_back_by_checks(tasks, state))
    statuses = state.get("task_status") or {}
    reasons = state.get("task_status_reasons") or {}
    scope = state.get("implement_task_ids")
    for task_id, status in sorted(statuses.items()):
        if status != "pending" or task_id in held:
            continue
        if isinstance(scope, list) and task_id not in scope:
            continue
        reason = str(reasons.get(task_id) or "")
        if reason.startswith(BLOCKED_BY_CHECK_PREFIX):
            check_id = reason[len(BLOCKED_BY_CHECK_PREFIX):].split(" ", 1)[0]
            held[str(task_id)] = check_id
    return sorted(held.items())


def _drop_ignored(paths, say=print) -> List[str]:
    """``paths`` without the ones git ignores (a transcript, a build cache).

    An ignored path is not a change to the repository, and ``tracked_files``
    becomes ``review-code``'s scope: the host's own ``logs/*.jsonl`` reached it
    through ``--touched`` (2026-10-02, Codex run). Said once, naming what went.
    """
    named = [p.strip() for p in paths if p and p.strip()]
    ignored = ignored_paths(named)
    if ignored:
        say(
            f"Left out {len(ignored)} gitignored path(s): "
            f"{', '.join(sorted(ignored)[:5])}"
            f"{', …' if len(ignored) > 5 else ''}"
        )
    return [p for p in paths if p.strip() not in ignored]


def _workflow_entries(state: dict, state_path: Path) -> List[str]:
    """The workflow's own files for this state (``workflow_file_entries``).

    The plan named by ``plan_path``, the output folder the state file lives in
    and the task list the plan's ``TASKS_FILE`` marker names, relative to the
    repository the census runs in. Empty outside a repository.
    """
    root = get_project_root_from_dir()
    if root is None:
        return []
    entries = workflow_file_entries(
        state.get("plan_path"), root=root, output_dirs=[state_path.parent],
    )
    # The plan beside its output folder (`plans/x.md` for `plans/x/state.json`)
    # too: `plan_path` is stored absolute, so a repository that was moved or
    # copied names a plan outside it, and the plan would read as code.
    sibling = state_path.parent.parent / f"{state_path.parent.name}.md"
    if sibling.is_file():
        for entry in workflow_file_entries(sibling, root=root):
            if entry not in entries:
                entries.append(entry)
    return entries


def _drop_workflow_files(paths, workflow: List[str], say=print) -> List[str]:
    """*paths* without the workflow's own files, saying once what went.

    The plan, its task list and the output folder are what the planning
    phases edit; a census that kept them handed review-code the plan and
    ``tasks.md`` as code (2026-10-05, Codex racing run 3). Every commit
    review's brief and report folder goes too, as a class
    (``commit_review.commit_review_artifact``, plans/review-commits.md §2.4),
    whatever plan this state has and whether or not a committed review sits
    in an un-ignored folder; the folder is read for the repository the census
    runs in, and when the accessor refuses it nothing extra is dropped.
    """
    kept = subtract_baseline(paths, workflow) if workflow else list(paths)
    root = get_project_root_from_dir() if kept else None
    folder = commit_reviews_folder_rel(root) if root else None
    if folder:
        kept = [p for p in kept if not commit_review_artifact(p.strip(), folder)]
    kept_set = set(kept)
    dropped = sorted({p for p in paths if p not in kept_set})
    if dropped:
        say(
            f"Left out {len(dropped)} of the workflow's own file(s) (the plan, "
            f"its task list, its output folder and commit reviews are never "
            f"code under review): "
            f"{', '.join(dropped[:5])}{', …' if len(dropped) > 5 else ''}"
        )
    return kept


def _tracked_entries(
    paths, actions: Dict[str, str], label: str = TRACKING_LABELS["implement"],
) -> List[Dict[str, str]]:
    """``tracked_files`` entries for *paths*, in the order given."""
    return [
        {"path": f, "action": actions.get(f, "modified"), "task_id": label}
        for f in paths
    ]


def phase_tracked_files(
    state: dict,
    touched: List[str],
    *,
    state_path: Path,
    phase: str = "implement",
    say=print,
    drop_ignored: bool = True,
) -> List[Dict[str, str]]:
    """The whole ``tracked_files`` list after *phase* recorded its changes.

    *phase*'s own entries are the census (:func:`_census_paths`, the
    workflow's own files left out); every entry the OTHER code phase recorded
    keeps that phase's label, and a path it already holds is not claimed
    again. So a file implement created stays ``created`` by
    ``implementation`` after apply-code-fixes edits it, and nothing an
    earlier phase changed is attributed to a later one. Entries with any
    other label (the planning phases' plan and ``tasks.md`` entries an older
    run left, a hand-written list) are replaced, as before.

    Every entry's ``action`` — a kept one's too — is read off the tree as it
    is now (:func:`_path_states`), never copied from the record: after
    apply-code-fixes deleted the ``index.html`` implement created, the kept
    entry still read ``created`` and review-code was sent to a file that no
    longer exists (fix round 8). A recorded path — a kept entry, or a
    ``--touched`` file — that is neither on disk nor in the base commit is
    left out, whichever phase recorded it: a file the code phases created
    and later removed leaves no change behind, so there is nothing of it to
    review. The drop is said once, naming each file and the phase that
    recorded it. A path git's own census names is kept: git sees a change
    there. Not on disk, it reads ``deleted`` and carries *phase*'s label,
    even when the other phase recorded it: implement created
    ``index.html``, the user committed it and apply-code-fixes deleted it,
    so the change left in the tree is this phase's deletion, and the
    kept entry used to be dropped before the census could keep it (fix
    round 9).

    The write executor calls this after every batch with ``say`` silenced,
    so a run that stops part-way has still recorded what its finished
    batches changed; ``main`` calls it once with the census printed.
    """
    label = TRACKING_LABELS[phase]
    if drop_ignored:
        touched = _drop_ignored(touched, say)
    workflow = _workflow_entries(state, state_path)
    own, census = _census_paths(state, touched, workflow=workflow, say=say)
    others = set(TRACKING_LABELS.values()) - {label}
    kept = [
        dict(entry) for entry in (state.get("tracked_files") or [])
        if isinstance(entry, dict) and entry.get("path")
        and entry.get("task_id") in others
        and not (workflow and baseline_covers(entry["path"], workflow))
    ]
    held = {entry["path"] for entry in kept}
    states = _path_states(
        sorted(held | set(own)),
        base_ref=state.get("head_before_implement"),
        baseline=state.get("pre_existing_changes") or [],
    ) or {}
    # A held path the other phase's record would leave out as gone, but that
    # git's census names, is this phase's: the change git sees there is the
    # deletion made since the file was committed, not the other phase's
    # creation (which is in that commit). Read before `own` is filtered by
    # `held`, or the kept entry's verdict drops it (fix round 9).
    reclaimed = {
        path for path in held if states.get(path) == GONE and path in census
    }
    own = [path for path in own if path not in held or path in reclaimed]

    merged: List[Dict[str, str]] = []
    gone: List[Dict[str, str]] = []
    for entry in kept:
        if entry["path"] in reclaimed:
            continue
        action = states.get(entry["path"])
        if action == GONE:
            gone.append(entry)
            continue
        if action:
            entry["action"] = action
        merged.append(entry)
    for path in own:
        action = states.get(path, "modified")
        if action == GONE and path in census:
            # Git's own census named it, so git sees a change there: a file
            # committed after the base and now on no disk. Only a record
            # (`--touched`, a kept entry) can name a file that has since gone
            # and left nothing for git to see.
            action = "deleted"
        entry = {"path": path, "action": action, "task_id": label}
        (gone if action == GONE else merged).append(entry)

    kept_now = [entry for entry in merged if entry["task_id"] != label]
    if kept_now:
        say(
            f"Kept {len(kept_now)} file(s) another phase recorded: "
            + ", ".join(f"{e['path']} ({e['task_id']})" for e in kept_now[:5])
            + (", …" if len(kept_now) > 5 else "")
        )
    if gone:
        say(
            f"Left out {len(gone)} file(s) that no longer exist and are not in "
            f"the base commit (created, then removed: nothing is left to "
            f"review): "
            + ", ".join(f"{e['path']} ({e['task_id']})" for e in gone[:5])
            + (", …" if len(gone) > 5 else "")
        )
    return sorted(merged, key=lambda entry: entry["path"])


#: :func:`_path_states`' word for a path that is neither on disk nor in the
#: base commit, and that the baseline does not name: created after the base,
#: then removed. Never a ``tracked_files`` action.
GONE = "gone"


def _path_states(paths, *, base_ref=None, baseline=()) -> Optional[Dict[str, str]]:
    """What each repo-relative path is now, against the implement baseline.

    * in the base tree (``head_before_implement``, else ``HEAD``, else the
      empty tree when HEAD has no commit yet) — still on disk ``modified``,
      gone ``deleted``;
    * not in it and on disk — ``created`` unless ``pre_existing_changes``
      covers it (it existed before the phase began: ``modified``);
    * not in it and not on disk — ``deleted`` when the baseline names the
      path itself (an untracked or staged file that existed before the phase
      and is gone now), else :data:`GONE`: nothing the base or the disk holds,
      so nothing to review. A path covered only by a baseline *directory*
      entry (``plans/``) is :data:`GONE` too: that entry says the directory
      existed, not that this file did.

    ``None`` when no base tree is readable, or there is no repository at
    all: nothing here can be told apart then.
    """
    paths = [p for p in paths if p]
    toplevel = get_project_root_from_dir() if paths else None
    if toplevel is None:
        return None
    in_base = None
    try:
        # Before the first commit there is no `HEAD` tree to ask, but the
        # answer is not unknown: nothing is committed, so every path is new.
        head = head_or_empty_tree()
    except GitError:
        head = "HEAD"
    for ref in (base_ref, head):
        if ref:
            in_base = paths_in_commit(str(ref), paths)
            if in_base is not None:
                break
    if in_base is None:
        return None
    baseline = list(baseline or ())
    named = set(baseline)
    states: Dict[str, str] = {}
    for path in paths:
        exists = os.path.lexists(os.path.join(toplevel, path))
        if path in in_base:
            states[path] = "modified" if exists else "deleted"
        elif exists:
            states[path] = "modified" if baseline_covers(path, baseline) else "created"
        else:
            states[path] = "deleted" if path in named else GONE
    return states


def _file_actions(paths, *, base_ref=None, baseline=()) -> Dict[str, str]:
    """``created`` / ``modified`` / ``deleted`` for each repo-relative path.

    Every entry used to say ``modified`` whatever the run did, so a file
    ``implement`` created read as an edit (2026-10-04, Claude Code racing
    re-run: ``index.html``). Read off the implement baseline instead
    (:func:`_path_states`). This is ``--only-touched``'s reading, which
    tracks exactly the paths it was given: a :data:`GONE` path stays
    ``modified`` there, as it always read. No readable base tree, or no
    repository at all, keeps ``modified`` for every path rather than
    guessing ``created``.
    """
    paths = [p for p in paths if p]
    states = _path_states(paths, base_ref=base_ref, baseline=baseline)
    if states is None:
        return {p: "modified" for p in paths}
    return {p: ("modified" if s == GONE else s) for p, s in states.items()}


def _census_paths(
    state: dict,
    touched: List[str],
    *,
    workflow: List[str] = (),
    say=print,
) -> Tuple[List[str], Set[str]]:
    """The default scope's paths: the dirty census, minus the baseline, plus ``--touched``.

    The workflow's own files (*workflow*, :func:`_workflow_entries`) are left
    out of both halves. Prints the census counts through *say*. May rewrite a
    malformed ``pre_existing_changes`` on *state* to ``[]`` (warned), which
    the caller then persists. Sorted; the caller reads each path's action.
    The second value is the set of those paths git's own census named (the
    rest came from ``--touched`` alone).
    """
    # Ensure pre_existing_changes is a list
    pre_existing_raw = state.get("pre_existing_changes")
    if pre_existing_raw is not None and not isinstance(pre_existing_raw, list):
        print("WARNING: pre_existing_changes is not a list, treating as empty", file=sys.stderr)
        state["pre_existing_changes"] = []

    # Get current modified files (using shared utilities for consistency)
    current_modified = get_all_modified_files()

    # Subtract pre-existing changes. Prefix-aware, because a baseline entry is
    # whatever `git status --porcelain` printed, and an untracked *directory* is
    # one `plans/` line standing for every path beneath it: a plain set
    # difference subtracts none of them.
    pre_existing = list(state.get("pre_existing_changes", []))
    implementation_changes = set(subtract_baseline(current_modified, pre_existing))

    # The workflow's own folder goes before the expansion below, so an
    # untracked output folder is never listed file by file only to be dropped
    # (it is named once in the drop line further down).
    surviving = set(subtract_baseline(implementation_changes, workflow))
    workflow_entries = implementation_changes - surviving
    implementation_changes = surviving

    # A directory that survived the subtraction is one this phase created:
    # expand it to the files inside it, which is what every consumer needs.
    implementation_changes = _expand_uncovered_directories(implementation_changes)
    census = set(implementation_changes)

    # ...except for the files the executor verified it changed: those are
    # implementation changes whether or not they were dirty at the start.
    verified = [f for f in touched if f and f.strip()]
    kept_pre_existing = sorted(
        f for f in verified
        if baseline_covers(f, pre_existing) and f not in implementation_changes
    )
    implementation_changes |= set(verified)
    # The plan, its task list and the output folder are never a phase's code
    # change, whichever half named them (an expanded `plans/`, a `--touched`).
    implementation_changes = set(_drop_workflow_files(
        sorted(implementation_changes | workflow_entries), list(workflow), say,
    ))
    kept_pre_existing = [f for f in kept_pre_existing if f in implementation_changes]

    say(f"Current modified files: {len(current_modified)}")
    say(f"Pre-existing changes: {len(pre_existing)}")
    if verified:
        say(
            f"Verified by the write executor: {len(verified)}"
            + (
                f" ({len(kept_pre_existing)} kept although modified before the "
                f"phase started: {', '.join(kept_pre_existing)})"
                if kept_pre_existing else ""
            )
        )
    say(f"Implementation changes: {len(implementation_changes)}")
    return sorted(implementation_changes), census & implementation_changes


def _insert_summary_reference(plan_file: str, summary_relative: str) -> int:
    """Idempotently add the implementation-summary link to the plan."""
    from utils import insert_implementation_summary_reference

    plan_path = Path(plan_file)
    if not plan_path.exists():
        print(f"ERROR: Plan file not found: {plan_path}", file=sys.stderr)
        return 1
    content = plan_path.read_text(encoding="utf-8")
    updated = insert_implementation_summary_reference(content, summary_relative)
    if updated != content:
        plan_path.write_text(updated, encoding="utf-8")
        print(f"Updated {plan_path} with a reference to {summary_relative}")
    else:
        print(f"{plan_path} already references {summary_relative}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
