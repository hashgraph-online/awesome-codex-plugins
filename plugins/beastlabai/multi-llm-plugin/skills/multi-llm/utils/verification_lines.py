"""The tests line: what a code phase says about the repository's tests.

:func:`unverified_line` when no ``driver.verify_command`` ran them, its
native twins (:func:`native_stop_unverified_line`,
:func:`native_apply_fixes_unverified_line`), the checks an implement run's
tasks ran (:func:`implement_checks_ran`), the repository's own test
command as a candidate (:func:`verify_command_candidate`, which
``known_checks`` lists too) and the line a recorded verification prints
(:func:`verification_line`).

``utils.write_batch_scheduler`` re-exports every name defined here for
reading only: patch one here, never through the scheduler
(docs/development/write-scheduler.md#where-the-schedulers-helpers-live).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Collection, Dict, List, Optional, Set, Tuple, Union

from . import check_records as _check_records
from . import known_checks as _known_checks
from .task_ledger import COMPLETED_MANUAL_REASON
from .text_clip import plain_line
from .provider_registry import get_verify_command
from .batch_reply import batch_check_could_not_run
from .write_phase_bridge import WRITE_TASK_FILENAME
from .write_safety import resolve_repo_root
from .state_manager import (
    TASK_BATCH_CHECK_ACCEPTED_KEY,
    TASK_BATCH_CHECK_KEY,
    TASK_BATCH_CHECK_REPEATS_KEY,
    TASK_CHECK_FINDINGS_KEY,
    TASK_OWN_CHECK_RAN_KEY,
)
from .output_handler import output_dir_path
from .task_decomposer import TaskDecomposer
from .tasks_file import read_task_list


#: npm's own placeholder ``scripts.test``: a test script that runs nothing.
_NPM_PLACEHOLDER_TEST = "no test specified"


def verify_command_candidate(repo_root: Optional[str]) -> Optional[Tuple[str, str]]:
    """``(command, why)`` for the repository's obvious test command, or ``None``.

    Read from the files that declare one — a ``package.json`` ``scripts.test``
    (not npm's placeholder; the package manager named by its lockfile), a
    ``Makefile`` ``test:`` target, a ``Cargo.toml``, a ``go.mod``, a pytest
    configuration — and never run, never written anywhere: it is what the
    line saying nothing ran the tests names as the setting to add (fix round
    14). Each read is bounded and any error is no candidate.
    """
    if not repo_root:
        return None
    root = Path(repo_root)

    def read(name: str, limit: int = 256 * 1024) -> Optional[str]:
        path = root / name
        try:
            if not path.is_file() or path.is_symlink():
                return None
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                return handle.read(limit)
        except OSError:
            return None

    package = read("package.json")
    if package is not None:
        try:
            scripts = (json.loads(package) or {}).get("scripts") or {}
        except (ValueError, AttributeError):
            scripts = {}
        test = scripts.get("test") if isinstance(scripts, dict) else None
        if isinstance(test, str) and test.strip() and _NPM_PLACEHOLDER_TEST not in test:
            runner = (
                "pnpm" if (root / "pnpm-lock.yaml").is_file()
                else "yarn" if (root / "yarn.lock").is_file()
                else "bun" if (root / "bun.lockb").is_file() or (root / "bun.lock").is_file()
                else "npm"
            )
            return f"{runner} test", "package.json defines scripts.test"
    makefile = read("Makefile")
    if makefile is not None and re.search(r"(?m)^test\s*:", makefile):
        return "make test", "the Makefile has a test target"
    if read("Cargo.toml") is not None:
        return "cargo test", "the repository has a Cargo.toml"
    if read("go.mod") is not None:
        return "go test ./...", "the repository has a go.mod"
    pyproject = read("pyproject.toml") or ""
    if (
        "[tool.pytest" in pyproject or read("pytest.ini") is not None
        or "[tool:pytest]" in (read("setup.cfg") or "")
    ):
        return "python -m pytest", "the repository configures pytest"
    return None


#: How the tests line opens when nothing ran a check (fix round 14).
NOTHING_RAN_TESTS = "Nothing ran this repository's tests"
#: What follows the checks that did run (fix round 24): the plugin's own part.
PLUGIN_RAN_NO_TESTS = "The plugin itself ran no tests"
#: The known checks' tally on a stop's tests line (fix round 24): the line
#: ends the bounded ``error`` whole, so its tally is cut shorter than a
#: finished run's (``known_checks.TALLY_MAX_CHARS``).
STOP_TALLY_MAX_CHARS = 300
#: How many task ids a bucket of :func:`implement_checks_ran` names before
#: "and N more", so the stop's tests line stays short enough to stay whole.
CHECKS_RAN_MAX_IDS = 8


def unverified_line(repo_root: Optional[str], ran: Optional[str] = None) -> str:
    """The one plain line a code phase's result carries when no
    ``driver.verify_command`` is set (fix round 14): nothing ran the
    repository's tests, and the setting that would, naming an obvious
    command when the repository declares one.

    Fix round 24 (live run 10, Codex and OpenCode racing 06 and 08): every
    task had run ``npm test`` as its own check and passed, and the line
    still opened "Nothing ran this repository's tests" — at 08 beside a
    tally saying ``npm test`` passed in every batch. With *ran*, the
    sentence saying what did run (:func:`implement_checks_ran`, or
    :func:`known_checks.checks_report`'s), the line leads with it and says
    the plugin itself ran none; "Nothing ran" only when nothing did."""
    candidate = verify_command_candidate(repo_root)
    where = "under driver: in .multi-llm/providers.yaml"
    lead = (
        f"{plain_line(ran)} {PLUGIN_RAN_NO_TESTS}" if ran and plain_line(ran)
        else NOTHING_RAN_TESTS
    )
    if candidate:
        command, why = candidate
        return (
            f"{lead}: driver.verify_command is "
            f"not set. To have every code phase run them, add "
            f"verify_command: \"{command}\" {where} ({why})."
        )
    return (
        f"{lead}: driver.verify_command is not "
        f"set. To have every code phase run them, add verify_command {where}, "
        f"set to the command that runs your tests or checks your build."
    )


def unverified_with_report(
    repo_root: Optional[str], report: Optional[Tuple[str, bool]],
) -> str:
    """:func:`unverified_line` for apply-code-fixes, with what its batches
    reported about the known checks (:func:`known_checks.checks_report`):
    led by the tally when a batch ran one of them, else "Nothing ran …"
    followed by it (fix round 24); the bare line without a tally."""
    if not report:
        return unverified_line(repo_root)
    text, ran = report
    if ran:
        return unverified_line(repo_root, ran=text)
    return f"{unverified_line(repo_root)} {text}"


def implement_checks_ran(
    state: Any, check_ids: Collection[str] = (),
) -> Optional[str]:
    """What ran a check in implement, as recorded, or ``None`` when nothing
    did (fix round 24): ``The tasks ran checks: passed in T001 and T003;
    reported problems in T002.``

    Counted: each code task recorded ``completed`` whose own check reported
    (:data:`state_manager.TASK_OWN_CHECK_RAN_KEY`) — failing when
    ``task_batch_check`` holds it, never when its only finding says the
    check could not run — and each check task of *check_ids* recorded
    ``completed`` (its check is its job), failing when
    ``task_check_findings`` holds it. Manual tasks and tasks outside the
    decomposition implement ran last are not. Only task ids (held to
    ``T###``) and counts: no model text.

    Fix round 25 (review of round 24, stops #1): a code task whose own check
    reported again only what the user accepted for a check
    (``task_batch_check_accepted``, nothing in ``task_batch_check``) is
    never "reported problems" — the ``[BATCH_CHECK_ACCEPTED]`` line beside
    it says it is not the task's own failure. It has its own clause:
    ``repeated the accepted findings of T002 in T007``, the checks named
    once for all such tasks, each list cut at :data:`CHECKS_RAN_MAX_IDS`.
    Fix round 28: one whose own check reported only what a check task of
    the run reported (``task_batch_check_repeats``) has its own clause too,
    ``repeated the findings of T002 in T001``."""
    if not hasattr(state, "get"):
        return None

    def mapping(key: str) -> Dict[str, Any]:
        value = state.get(key)
        return value if isinstance(value, dict) else {}

    statuses = mapping("task_status")
    reasons = mapping("task_status_reasons")
    scope = state.get("implement_task_ids")
    human = {str(t) for t in (state.get("implement_human_task_ids") or [])}

    def counted(task_id: str) -> bool:
        return (
            bool(_check_records._IMPLEMENT_TASK_ID.match(task_id))
            and statuses.get(task_id) == "completed"
            and (not isinstance(scope, list) or task_id in scope)
            and task_id not in human
            and str(reasons.get(task_id) or "") != COMPLETED_MANUAL_REASON
        )

    own = state.get(TASK_OWN_CHECK_RAN_KEY)
    own_ids = {str(t) for t in own} if isinstance(own, list) else set()
    failing_own = mapping(TASK_BATCH_CHECK_KEY)
    accepted = mapping(TASK_BATCH_CHECK_ACCEPTED_KEY)
    repeats = mapping(TASK_BATCH_CHECK_REPEATS_KEY)
    check_findings = mapping(TASK_CHECK_FINDINGS_KEY)
    passed: List[str] = []
    problems: List[str] = []
    repeated: List[str] = []
    repeated_of: Set[str] = set()
    # Fix round 28: a code task whose own check reported only what a check
    # task of the run reported, never "reported problems" or "passed".
    echoed: List[str] = []
    echoed_of: Set[str] = set()
    for task_id in sorted(own_ids | {str(t) for t in check_ids}):
        if not counted(task_id):
            continue
        if task_id in own_ids and task_id not in check_ids:
            findings = failing_own.get(task_id)
            if isinstance(findings, list) and findings and batch_check_could_not_run(
                    [str(item) for item in findings]):
                continue
            again = accepted.get(task_id)
            if not findings and again:
                repeated.append(task_id)
                if isinstance(again, dict):
                    repeated_of.update(
                        str(check) for check in again
                        if _check_records._IMPLEMENT_TASK_ID.match(str(check)))
                continue
            same = repeats.get(task_id)
            if not findings and same:
                echoed.append(task_id)
                if isinstance(same, dict):
                    echoed_of.update(
                        str(check) for check in same
                        if _check_records._IMPLEMENT_TASK_ID.match(str(check)))
                continue
            failed = bool(findings)
        else:
            failed = bool(check_findings.get(task_id))
        (problems if failed else passed).append(task_id)
    if not passed and not problems and not repeated and not echoed:
        return None

    def named(ids: List[str]) -> str:
        shown = ids[:CHECKS_RAN_MAX_IDS]
        rest = len(ids) - len(shown)
        if rest:
            return ", ".join(shown) + f" and {rest} more"
        return shown[0] if len(shown) == 1 else ", ".join(shown[:-1]) + f" and {shown[-1]}"

    said = []
    if passed:
        said.append(f"passed in {named(passed)}")
    if problems:
        said.append(f"reported problems in {named(problems)}")
    if repeated:
        of = f" of {named(sorted(repeated_of))}" if repeated_of else ""
        said.append(f"repeated the accepted findings{of} in {named(repeated)}")
    if echoed:
        of = f" of {named(sorted(echoed_of))}" if echoed_of else ""
        said.append(f"repeated the findings{of} in {named(echoed)}")
    return "The tasks ran checks: " + "; ".join(said) + "."


def native_stop_unverified_line(plan_path: Union[str, Path]) -> Optional[str]:
    """The :func:`unverified_line` a stopped native implement owes, or ``None``.

    Fix round 18 (live run 7, Claude Code stop 01): the native leg's stop
    printed no "Nothing ran this repository's tests" line at all — the
    executor leg's stop says it (``write_verify.VerifyStep.note_unverified_on_stop``),
    and the Claude Code host wrote its own from the instructions. ``util
    next-command`` prints this one as ``[TESTS_NOT_RUN]`` beside a stopped
    implement's ``--resume``. The executor's rule, read from ``state.json``
    as recorded: owed when no ``driver.verify_command`` is set and a code
    task of the decomposition implement ran last is recorded ``completed`` —
    not a manual task, and not a check task (an agent task declaring no files,
    read off the plan's task list). The native leg keeps no audit log, so a
    completed code task counts as an edit, as the executor's conservative
    reading counts one with no completion on record. Never fatal: any read
    that fails answers ``None``.
    """
    try:
        plan = Path(plan_path).resolve()
        state = json.loads((output_dir_path(plan) / "state.json").read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            return None
        if get_verify_command(anchor=str(plan)):
            return None
        statuses = state.get("task_status") or {}
        reasons = state.get("task_status_reasons") or {}
        scope = state.get("implement_task_ids")
        human = {str(t) for t in (state.get("implement_human_task_ids") or [])}
        completed = [
            str(task_id) for task_id, status in statuses.items()
            if status == "completed" and _check_records._IMPLEMENT_TASK_ID.match(str(task_id))
            and (not isinstance(scope, list) or task_id in scope)
            and str(task_id) not in human
            and str(reasons.get(task_id) or "") != COMPLETED_MANUAL_REASON
        ]
        if not completed:
            return None
        checks = _check_task_ids_of_plan(plan)
        if not [task_id for task_id in completed if task_id not in checks]:
            return None
        try:
            root = resolve_repo_root(str(plan))
        except Exception:  # noqa: BLE001 - the line still stands without a candidate
            root = None
        # Fix round 24: led by the checks the tasks ran, as the executor's.
        return unverified_line(root, ran=implement_checks_ran(state, checks))
    except Exception:  # noqa: BLE001 - advisory: never fails the lookup
        return None


def native_apply_fixes_unverified_line(plan_path: Union[str, Path]) -> Optional[str]:
    """The :func:`unverified_line` a finished native apply-code-fixes owes,
    with what its batches reported about the known checks, or ``None``.

    Fix round 20 (live run 8, Codex racing 08): the executor's line also
    names the checks the batches were asked to run and what each batch
    reported (:func:`known_checks.checks_tally`); on the native leg the host
    wrote its own "nothing ran the tests" line from the instructions.
    ``apply-code-fixes --mark-completed`` prints this one as
    ``[TESTS_NOT_RUN]``. Owed when no ``driver.verify_command`` is set and a
    batch of the phase's ``write_tasks.json`` is recorded ``completed`` (the
    native leg keeps no audit log, so a completed batch counts as an edit).
    Never fatal: any read that fails answers ``None``.
    """
    try:
        plan = Path(plan_path).resolve()
        out = output_dir_path(plan)
        if get_verify_command(anchor=str(plan)):
            return None
        document = json.loads(
            (out / "apply-fixes" / WRITE_TASK_FILENAME).read_text(encoding="utf-8")
        )
        tasks = [
            task for task in (document.get("batches") or document.get("tasks") or [])
            if isinstance(task, dict)
        ]
        state = _known_checks.read_state(out)
        statuses = state.get("task_status") or {}
        if not any(statuses.get(str(task.get("task_id"))) == "completed" for task in tasks):
            return None
        try:
            root = resolve_repo_root(str(plan))
        except Exception:  # noqa: BLE001 - the line still stands without a candidate
            root = None
        # Fix round 24: led by the tally when a batch ran a known check.
        return unverified_with_report(root, _known_checks.checks_report(
            _known_checks.known_check_commands(
                out, plan_file=str(plan), repo_root=root, state=state,
            ),
            state, tasks,
        ))
    except Exception:  # noqa: BLE001 - advisory
        return None


def _check_task_ids_of_plan(plan: Path) -> set:
    """The ids of the agent tasks in *plan*'s task list that declare no files
    (check tasks), parsed as implement parses it; empty when it cannot be read,
    which counts every completed task as code — the conservative reading."""
    try:
        tasks = TaskDecomposer().parse_plan(read_task_list(plan).text)
    except Exception:  # noqa: BLE001 - conservative: no check known
        return set()
    return {
        str(task.id) for task in tasks
        if getattr(task, "executor_role", "") != "human"
        and not (list(task.files_to_modify or []) or list(task.files_to_create or []))
    }


def verification_line(result: Any) -> str:
    """One line describing what `driver.verify_command` did, for a report (F4).

    Shared by the scheduler's own summary and
    ``apply_orchestrator_base.write_apply_summary_report`` so the two documents a
    code-fix run leaves behind cannot describe the same check differently. Takes
    anything carrying a ``verification`` attribute, so a caller holding only the
    orchestrator's ``write_result`` needs no import of its own.
    """
    record = getattr(result, "verification", None)
    if not isinstance(record, dict):
        unverified = getattr(result, "unverified", None)
        return "not configured (`driver.verify_command` is unset)" + (
            f". {unverified}" if unverified else ""
        )
    verdict = "pass" if record.get("exit_code") == 0 else (
        f"FAIL (exit {record.get('exit_code')})"
    )
    return (
        f"`{record.get('command', '')}` — {verdict}, "
        f"{record.get('duration_seconds')}s"
    )
