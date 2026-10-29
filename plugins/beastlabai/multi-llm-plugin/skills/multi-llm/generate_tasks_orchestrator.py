#!/usr/bin/env python3
"""generate-tasks, in Python: gate -> decomposition -> update_plan_tasks (D1a/D2i/D3).

Standalone ``--generate-tasks`` used to emit no task file at all: the instruction
markdown asked the driving agent to read the plan, explore the repo with
Claude-only tools, Write a JSON document into
``{PROJECT_ROOT}/.multi-llm/tmp/generated_tasks_{plan_stem}.json`` and then shell
out to ``update_plan_tasks.py``. Nothing about that sequence was runnable by a
single-shot host, and ``--full`` Phase 3 duplicated it one level down as an
inlined Task prompt. This module is that sequence as code, so both entry points
share one implementation and every host can reach it:

1. **The gate is not reimplemented.** ``check_workflow_prerequisites``
   (D6a) owns rows 5/6; this calls :func:`ensure_prerequisites` and prints what it
   decides. Nothing is produced before it — no phase dir, no task file, no
   ``state.json`` mutation.
2. **The work is a materialized task like any other** (D2/D2i): a *one-task* file
   with the same shape every other kind uses, so the executor needs no special
   case. It is the standing consumer of ``context_mode: workspace-read`` — its
   prompt names exactly one path (the pinned repo root) and requires **both**
   ``supports_workspace_reads`` and the ``agent-readonly`` profile. A runner with
   neither is refused *before dispatch*, exit 3 with the reason named: a
   non-agentic runner does not fail on this prompt, it confidently invents a task
   list from the plan's prose, and every later phase would treat that as ground
   truth.
3. **Either invoker persists the same document** (D3a): under
   ``--exec-subagents`` the executor dispatches and writes
   ``task_generation_result.json``; on a native-subagent host the driving agent
   runs ``task.prompt`` and *it* writes the same file, then re-invokes with
   ``--reaggregate``. The callee only ever prints. The old temp-file channel —
   and with it the ``.gitignore`` bootstrap and the "re-resolve the git root in a
   second Bash call" hazard — is gone, not ported.
4. **The document is validated before it touches the plan**:
   ``schemas/generated_tasks.schema.json`` plus the semantic rules
   ``utils/task_decomposer.py`` owns (unique ``T###`` ids, ``depends_on`` naming
   only declared ids, acyclic, at least one dependency-free task). A failure is
   D3k rung 6 (``schema_invalid``) and nothing is written. On the executor lane
   a reply that fails the schema first gets **one** schema-repair re-ask on the
   same runner (the retry ladder's rule 7, ``SCHEMA_REPAIRS_BY_KIND``); nothing
   else retries it.
5. **The consumer is ``update_plan_tasks.py``, invoked in-process**, and the
   *outcome* is verified rather than the subagent's claim: a fresh
   ``<!-- TASKS_FILE: … -->`` marker, a rendered tasks file that exists and
   parses, and a task count that matches the document. If any of those is missing
   the plan and ``state.json`` are restored to their pre-consume bytes and the run
   exits 3 — a half-populated plan nobody reviewed is worse than no plan update.

Usage::

    uv run --project <skill-dir> -- python <skill-dir>/multi_llm.py \\
        generate-tasks <plan> [--yes] [--exec-subagents] [--force] [--reaggregate]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

# Absolute, symlinks preserved — see utils/cli_common.py.
sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

from check_workflow_prerequisites import ensure_prerequisites
from utils import cli_common
from utils.cli_common import (
    EXIT_ERROR,
    EXIT_NEEDS_HUMAN,
    EXIT_OK,
    build_parent_parser,
    record_artifact,
    record_next,
)
from utils.git_utils import get_project_root
from utils.output_handler import archive_file, get_output_paths, get_phase_dir
from utils.plan_updater import TASKS_FILE_REFERENCE_PATTERN
from utils.provider_registry import set_run_anchor
from utils.stream_bootstrap import bootstrap_streams
from utils.subagent_prompts import build_task_generation_prompt
from utils.subagent_tasks import (
    TaskFileError,
    build_inputs,
    make_task,
    make_task_file,
    tasks_of,
    write_task_file,
)
from utils.task_decomposer import TaskDecomposer
from utils import unattended as unattended_mod

#: The ``state.json`` phase / phase-dir name.
PHASE_NAME = "generate-tasks"

#: The mode word every printed follow-up command uses (never a script path).
MODE_NAME = "generate-tasks"

#: The one materialized kind whose context is the repository (D2i).
TASK_KIND = "task_generation"

#: Stable, path-free task id. Named in every refusal and in the retry hint.
TASK_ID = "task_generation"

#: The one-task file, and the document the invoker persists beside it (D3a/D3f).
TASK_FILE_NAME = "task_generation_tasks.json"
RESULT_NAME = "task_generation_result.json"

#: Beside the task file, exactly the bytes of its one ``prompt``
#: (``validation.PROMPT_SIDECAR_TEMPLATE``'s rule), for a native host to hand
#: its subagent as a file. Live run 8, Claude Code racing 03: with none, the
#: host read the 21 KB prompt into its own context and pasted it whole into
#: the subagent call.
PROMPT_FILE_NAME = "task_generation.prompt.txt"

#: Printed when a native-subagent host must run the prompt itself. Informational
#: under ``--exec-subagents`` (the run continues in-process past it, D3b).
PENDING_MARKER = "[TASK_GENERATION_PENDING]"


# ---------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="generate_tasks_orchestrator.py",
        description=(
            "Decompose a plan into an implementable task list: prerequisite gate, "
            "one materialized task_generation subagent, then update_plan_tasks "
            "in-process with the TASKS_FILE marker verified from the artifact."
        ),
        parents=[build_parent_parser()],
    )
    parser.add_argument(
        "--plan-file", required=True, help="Path to the plan markdown file"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-materialize the task prompt and re-dispatch even when a result "
             "file from an earlier run is already present.",
    )
    parser.add_argument(
        "--reaggregate",
        action="store_true",
        help="Consume a task_generation_result.json a native invoker already "
             "persisted: validate it, run update_plan_tasks in-process and verify "
             "the TASKS_FILE marker. The single follow-up a native-subagent host "
             "is ever handed.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


# ---------------------------------------------------------------------------
# The prerequisite gate (D6a) — called, never reimplemented
# ---------------------------------------------------------------------------

def _run_gate(
    plan_path: Path,
    args: argparse.Namespace,
    *,
    in_workflow: bool,
    apply_runner: Optional[Callable[[str], int]],
) -> Optional[int]:
    """``None`` to proceed, else the exit code this run must return.

    The three D6a branches belong to ``check_workflow_prerequisites``; the only
    decision made here is that an unmet gate is **exit 3 regardless of ``--yes``**.
    A rendered question was the attended branch's *only* other ending, and this
    orchestrator has no channel to render one — proceeding would generate tasks
    from unapplied review output and returning 0 would be a silent no-op. The
    message names the same three endings a question would have offered, as D5a
    flags.
    """
    unattended = bool(getattr(args, "yes", False))
    outcome = ensure_prerequisites(
        plan_path,
        PHASE_NAME,
        unattended=unattended,
        in_workflow=in_workflow,
        skip_prerequisites=bool(getattr(args, "skip_prerequisites", False)),
        apply_runner=apply_runner,
    )
    for notice in outcome.notices:
        print(notice)
    if outcome.met:
        return None
    if outcome.message:
        print(outcome.message, file=sys.stderr)
    if not unattended:
        print(
            "       Pass --skip-prerequisites to proceed on unapplied review "
            "output (recorded), or apply them first and re-run.",
            file=sys.stderr,
        )
    unattended_mod.mark_needs_human(MODE_NAME)
    return EXIT_NEEDS_HUMAN


# ---------------------------------------------------------------------------
# Materialization (D2c/D2i)
# ---------------------------------------------------------------------------

def _resolve_repo_root(plan_path: Path) -> str:
    """The single path the task-generation prompt names (D3e ``cwd``).

    The git root when there is one. A plan outside a repository falls back to the
    plan's own directory *and says so*: the fallback narrows the exploration
    surface rather than widening it, and the reason the old markdown hard-stopped
    here — it needed a git-ignored temp dir to write the JSON into — no longer
    exists, because the document is a printed reply the invoker persists.
    """
    root = get_project_root(str(plan_path))
    if root:
        return root
    fallback = str(plan_path.parent)
    print(
        f"multi-llm warning: {plan_path} is not inside a git repository, so "
        f"repository exploration is pinned to {fallback} instead of a git root.",
        file=sys.stderr,
    )
    return fallback


def materialize_task_file(
    plan_path: Path, phase_dir: str, *, repo_root: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """Write the one-task ``task_generation`` file and return ``(path, document)``.

    One task, in the same envelope every other kind uses — that is what lets the
    executor, the dry-run preflight, the resume-by-artifact rule and the native
    invoker all treat it as an ordinary batch of size one.
    """
    plan_text = plan_path.read_text(encoding="utf-8")
    root = repo_root or _resolve_repo_root(plan_path)
    inputs = build_inputs(plan_file=str(plan_path))
    prompt = build_task_generation_prompt(
        plan_text=plan_text, repo_root=root, plan_name=plan_path.name
    )
    task = make_task(
        kind=TASK_KIND,
        task_id=TASK_ID,
        prompt=prompt,
        output_name=RESULT_NAME,
        inputs=inputs,
        phase_dir=phase_dir,
        prompt_path=os.path.join(os.path.abspath(phase_dir), PROMPT_FILE_NAME),
        prompt_lines=prompt.count("\n") + 1,
        # The one kind that must see the repository, so the one materialized as
        # workspace-read (D2c). Both halves of the requirement — the capability
        # and the read-only profile — are checked before dispatch.
        context_mode="workspace-read",
        capability_tier="full",
        executor_role="agent",
        extra={"phase": PHASE_NAME, "repo_root": root, "plan_file": str(plan_path)},
    )
    from utils.validation import write_prompt_sidecars

    # All or none, as for validation: on a write failure the key is dropped
    # and the host runs `prompt` itself.
    write_prompt_sidecars([task], phase_dir, stale_glob=PROMPT_FILE_NAME)
    document = make_task_file(kind=TASK_KIND, tasks=[task], inputs=inputs)
    task_file = os.path.join(phase_dir, TASK_FILE_NAME)
    write_task_file(task_file, document)
    return task_file, document


# ---------------------------------------------------------------------------
# The pre-dispatch runner refusal (D2c/D3e)
# ---------------------------------------------------------------------------

def preflight_workspace_runner(task: Dict[str, Any], *, anchor: Optional[str]) -> None:
    """Refuse a runner that cannot serve this task **before** anything is spawned.

    Two requirements, and a runner that meets neither is not "degraded" but
    *wrong*: ``supports_workspace_reads`` (D2c — without it the prompt's one path
    is unreadable and the reply is invented from the plan's prose) and the
    ``agent-readonly`` profile (D3e — a read/analyze task is never downgraded to a
    write-capable invocation). Both are properties of the *adapter*, so this asks
    the registry rather than the task JSON, which embeds untrusted plan text.

    Raises:
        RunnerRejected: exit 3, with the runner spec and the missing capability
            named.
    """
    from utils.provider_registry import SESSION_LAYER, get_provider, parse_model_spec
    from utils.subagent_executor import (
        PROFILE_AGENT_READONLY,
        RunnerRejected,
        eligible_runners,
        preflight_runner,
        _resolve_task_source,
    )

    # The key carries the ladder's layer word (`driver.subagent_runner
    # (session)`), so a refusal or a warning here names the rung that supplied
    # the spec, the way the executor's own preflight does.
    spec, key, layer = _resolve_task_source(task, anchor=anchor)
    provider_name, _model = parse_model_spec(spec, anchor=anchor)
    provider = get_provider(provider_name)
    if provider is not None and not provider.supports_workspace_reads:
        candidates = eligible_runners(PROFILE_AGENT_READONLY)
        raise RunnerRejected(
            f"Refusing to dispatch task {TASK_ID}: driver.subagent_runner is "
            f"{spec!r}, which declares no workspace-read capability, and task "
            f"generation is the one kind whose context is the repository "
            f"(context_mode: workspace-read). A runner that cannot read the "
            f"workspace does not fail on this prompt — it invents a task list "
            f"from the plan's prose, which every later phase then treats as "
            f"ground truth. "
            + (
                f"Runners on this host that can serve it: {', '.join(candidates)}."
                if candidates
                else "No runner on this host can serve it — install and "
                     "authenticate one of the agentic CLIs (claude, codex, "
                     "opencode)."
            )
            + " Nothing was dispatched.",
            key="driver.subagent_runner",
            spec=spec,
            reason_code="missing_capability",
        )
    # Adapter present, model spec parseable, `agent-readonly` implemented, binary
    # on PATH, version within the supported window — one shared formatter, so this
    # refusal reads like every other runner refusal.
    # The executor owns fallback from an implicit session selection to the
    # host's default runner. Refusing that selection here would prevent its
    # fallback from ever running. Explicit selections still fail immediately;
    # session selections receive the same full preflight inside run_tasks.
    if layer != SESSION_LAYER:
        preflight_runner(
            spec, profile=PROFILE_AGENT_READONLY, anchor=anchor, key=key, layer=layer
        )


# ---------------------------------------------------------------------------
# Validation of the returned document (D2i)
# ---------------------------------------------------------------------------

def validate_document(data: Any) -> List[str]:
    """Schema errors **plus** the semantic rules, in that order.

    The schema pins the shape; ``utils/task_decomposer.validate_generated_tasks``
    owns the four rules the *graph* has to satisfy for every later phase (batching,
    dependency walks, the human-task strategies) to mean anything. Both run before
    a byte reaches the plan — and both are the executor's own verdict for this
    kind (``subagent_executor.validate_result``), so a document that fails either
    gets the executor lane's schema-repair re-ask and is never persisted.
    """
    from utils.subagent_executor import validate_result

    return list(validate_result(TASK_KIND, data))


def stale_result_problems(result_path: str) -> List[str]:
    """Why the result file on disk may not be resumed from, or ``[]``.

    The same verdict ``consume_document`` would reach, taken on a completed
    *copy* (the omitted list keys it would supply), so asking changes nothing
    on disk.
    """
    import copy

    from utils.subagent_executor import normalize_result, supply_result_version

    try:
        data = json.loads(Path(result_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [f"it could not be read as JSON ({exc})"]
    data = copy.deepcopy(data)
    normalize_result(TASK_KIND, data)
    supply_result_version(TASK_KIND, data)
    return validate_document(data)


# ---------------------------------------------------------------------------
# The consumer, and the outcome check (D2i)
# ---------------------------------------------------------------------------

class _Snapshot:
    """Pre-consume bytes of everything ``update_plan_tasks`` may touch.

    The consumer marks the phase completed and rewrites the plan before this
    orchestrator can verify the outcome, so the only way to keep "nothing is
    written to the plan" literally true on the failure path is to be able to put
    the bytes back. Cheap (three small files) and strictly local: this runs
    single-threaded between the dispatch and the summary.
    """

    def __init__(self, plan_path: Path, state_file: Path, tasks_file: Path):
        self._targets = (plan_path, state_file, tasks_file)
        self._before = {
            path: (path.read_bytes() if path.exists() else None)
            for path in self._targets
        }

    def restore(self) -> None:
        for path, before in self._before.items():
            try:
                if before is None:
                    if path.exists():
                        path.unlink()
                else:
                    path.write_bytes(before)
            except OSError as exc:  # pragma: no cover - best effort
                print(
                    f"multi-llm warning: could not restore {path}: {exc}",
                    file=sys.stderr,
                )


def _tasks_marker(plan_text: str) -> Optional[str]:
    """The path a plan's ``<!-- TASKS_FILE: … -->`` marker names, if it has one."""
    match = re.search(TASKS_FILE_REFERENCE_PATTERN, plan_text)
    return match.group(1).strip() if match else None


def verify_outcome(plan_path: Path, expected_count: int) -> List[str]:
    """What the plan and the rendered tasks file must show, or the reasons why not.

    This is the check ``instructions/full-workflow.md`` performed by hand after its
    Task subagent returned, moved into Python so it runs on every host and under
    both invokers — and it reads the *artifacts*, never the reply.
    """
    problems: List[str] = []
    plan_text = plan_path.read_text(encoding="utf-8")
    marker = _tasks_marker(plan_text)
    if not marker:
        problems.append(
            "the plan carries no <!-- TASKS_FILE: … --> marker, so no later phase "
            "can find a task list"
        )
    tasks_path = get_output_paths(plan_path, "tasks", phase="tasks")
    if not tasks_path.exists():
        problems.append(f"the rendered tasks file {tasks_path} does not exist")
        return problems
    tasks_text = tasks_path.read_text(encoding="utf-8")
    parsed = TaskDecomposer().parse_plan(tasks_text)
    if not parsed:
        problems.append(
            f"{tasks_path} exists but parses to zero tasks, so `--implement` "
            f"would report it as having no task list"
        )
    elif len(parsed) != expected_count:
        problems.append(
            f"{tasks_path} parses to {len(parsed)} task(s) but the validated "
            f"document declared {expected_count}"
        )
    if marker:
        resolved = (plan_path.parent / marker).resolve()
        if resolved != tasks_path.resolve():
            problems.append(
                f"the TASKS_FILE marker points at {resolved}, not at the rendered "
                f"{tasks_path}"
            )
    return problems


def consume_document(plan_path: Path, result_path: str) -> int:
    """Validate, run ``update_plan_tasks`` in-process, verify, or restore and fail."""
    try:
        data = json.loads(Path(result_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        return _fail(
            f"ERROR: {result_path} could not be read as JSON ({exc}).\n"
            f"       Re-run with --force to re-dispatch task {TASK_ID}; nothing "
            f"was written to the plan."
        )

    # The native host writes the reply itself, so the executor's completion of
    # an omitted-but-empty list key has not happened yet on this path. It runs
    # here, and the completed document goes back to disk before validation:
    # `update_plan_tasks` reads the *file*, and a later `task_is_complete`
    # re-validates the file, so what was validated is what is on disk.
    from utils.schema_validator import schema_version_supplied
    from utils.subagent_executor import normalize_result, supply_result_version

    notes = normalize_result(TASK_KIND, data)
    # Fix round 28 (live run 12, Claude Code racing 03): the host's copy of
    # the subagent's reply left out "schema_version", which has one value,
    # and this run failed schema validation on it.
    version = supply_result_version(TASK_KIND, data)
    if version:
        print(
            "[generate-tasks] "
            + schema_version_supplied(RESULT_NAME, version)
            + ", and the key was written into the file before validating."
        )
    if notes:
        print(
            f"[generate-tasks] {RESULT_NAME} omitted {', '.join(notes)}; "
            f"supplied [] before validating (absent and empty mean the same "
            f"thing to every consumer of this document)."
        )
    if notes or version:
        try:
            Path(result_path).write_text(
                json.dumps(data, indent=2) + "\n", encoding="utf-8"
            )
        except OSError as exc:
            return _fail(
                f"ERROR: {result_path} could not be rewritten with the completed "
                f"document ({exc}). Nothing was written to the plan."
            )

    errors = validate_document(data)
    if errors:
        # Reached with a document the executor did not write: the executor
        # validates the same rules before it persists anything, and re-asks
        # its runner once first. A `--reaggregate` only consumes the reply on
        # disk, so nothing here re-asks it.
        return _fail(
            f"ERROR: the task-generation document in {result_path} is invalid "
            f"(schema_invalid, D3k rung 6):\n"
            + "\n".join(f"  - {problem}" for problem in errors[:10])
            + "\n       Nothing was written to the plan. This run only consumes "
            f"the reply on disk, so nothing re-asked it (with --exec-subagents "
            f"the executor re-asks its runner once with these errors before it "
            f"fails). Re-ask the subagent once with these errors and write its "
            f"reply over this file, or re-invoke the phase without --reaggregate: "
            f"that archives this document and re-dispatches task {TASK_ID}."
        )

    tasks = data.get("tasks") or []
    snapshot = _Snapshot(
        plan_path,
        _state_file_for(plan_path),
        get_output_paths(plan_path, "tasks", phase="tasks"),
    )

    import update_plan_tasks

    try:
        code = update_plan_tasks.main(
            ["--plan-file", str(plan_path), "--tasks-file", str(result_path)]
        )
    except SystemExit as exc:  # argparse or an explicit sys.exit inside the script
        code = EXIT_OK if exc.code is None else exc.code
    except Exception as exc:  # noqa: BLE001 - a crashed consumer must not leave
        snapshot.restore()     # the plan half-written; the bytes go back first
        return _fail(
            f"ERROR: update_plan_tasks raised {type(exc).__name__}: {exc}. The "
            f"plan and state.json are back to their pre-run bytes."
        )
    if code not in (EXIT_OK, None):
        snapshot.restore()
        return _fail(
            f"ERROR: update_plan_tasks exited {code}, so the plan was not "
            f"updated. The plan and state.json are back to their pre-run bytes."
        )

    problems = verify_outcome(plan_path, len(tasks))
    if problems:
        snapshot.restore()
        return _fail(
            "ERROR: the task-generation consumer reported success but the "
            "artifacts do not agree, so the run failed:\n"
            + "\n".join(f"  - {problem}" for problem in problems)
            + "\n       The plan and state.json are back to their pre-run bytes; "
            "nothing downstream may treat this plan as having tasks."
        )

    tasks_path = get_output_paths(plan_path, "tasks", phase="tasks")
    record_artifact(tasks_path)
    record_artifact(plan_path)
    # The phase machine's terminal word, exactly where the review phases write
    # theirs. Without it `.status.json`'s top-level `state` keeps whatever the
    # last *failed* attempt left (`subagents_failed`), and `status` renders a
    # `done` run beside `phase state: subagents_failed` — measured 2026-09-14,
    # on the successful retry the opencode plugin then showed the session model.
    from utils import detach as _detach
    from utils.status_file import update_status as _update_status

    phase_dir = str(get_phase_dir(plan_path, PHASE_NAME))
    # The host-visible half of the same two channels the apply/review bases
    # write: `status --view run` reads `output_files` off `.status.json` and
    # repeats it in `MULTI_LLM_RESULT.artifacts`, and that poll — not this
    # worker's log — is all a detached caller ever sees. Without it the one file
    # this phase exists to produce was unnamed, and it does not even live in the
    # phase dir (it lands in the sibling `tasks/`), so globbing could not find
    # it either: measured 2026-09-16, an opencode host reported the four
    # intermediate JSON blobs under `generate-tasks/` and never mentioned
    # `tasks.md`, the plan edit or the task count.
    _detach.record_output_files(
        phase_dir, tasks=str(tasks_path), plan=str(plan_path)
    )
    _update_status(phase_dir, {"state": "complete"})
    # The count is this phase's whole output, so report it: a step-only report
    # left `status` printing the one subagent that produced the list
    # (`task_generation 1/1 ok`) as the only number on screen. It is what this
    # run PRODUCED (`generated N tasks`), never a done/total pair: the
    # `tasks 10/10` that pair rendered read as a live count of tasks.md, and
    # stayed 10/10 after apply-task-suggestions split two tasks into four
    # (2026-10-04, Claude Code racing re-run).
    _detach.report_progress(phase_dir, step="complete", tasks_generated=len(tasks))
    print(f"\nTask generation complete: {len(tasks)} task(s) in {tasks_path}")
    # No "Next: uv run … review-tasks" line here (issue #17, 2026-10-02): it sat
    # beside `[NEXT_COMMAND]` in the log, and a dispatcher command is not a
    # command for the user. The next step, `review-tasks` included as the
    # optional one, is the `[NEXT_COMMAND]` block `multi_llm.main` prints in the
    # host's own spelling (`utils/next_phase.py`).
    return EXIT_OK


def _state_file_for(plan_path: Path) -> Path:
    """Where ``StateManager`` keeps this plan's ``state.json``.

    Computed from the same output-dir helper ``StateManager`` uses rather than by
    constructing one, so taking a snapshot never touches git or the clock.
    """
    from utils.output_handler import get_output_dir

    return get_output_dir(Path(plan_path)) / "state.json"


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    unattended_mod.mark_needs_human(MODE_NAME)
    return EXIT_NEEDS_HUMAN


# ---------------------------------------------------------------------------
# The phase
# ---------------------------------------------------------------------------

def run_generate_tasks(
    args: argparse.Namespace,
    *,
    in_workflow: bool = False,
    apply_runner: Optional[Callable[[str], int]] = None,
) -> int:
    """The whole sequence. ``full`` calls this directly to inject ``apply_runner``."""
    from utils.review_orchestrator_base import (
        dispatch_subagent_tasks,
        exec_subagents_requested,
        maybe_detach,
        update_status,
    )

    plan_path = Path(os.path.abspath(args.plan_file))
    if not plan_path.is_file():
        print(f"ERROR: Plan file not found: {args.plan_file}", file=sys.stderr)
        print(f"       Resolved path: {plan_path}", file=sys.stderr)
        return EXIT_ERROR

    # §9.3.a/b: the anchor capture point — absolute, before anything can chdir
    # and before any provider read that decides routing. Ahead of `_run_gate`,
    # which is the first thing on this path that can read config.
    set_run_anchor(str(plan_path))

    # Nothing is produced before the gate: no phase dir, no task file, no state
    # mutation (D6a).
    gated = _run_gate(
        plan_path, args, in_workflow=in_workflow, apply_runner=apply_runner
    )
    if gated is not None:
        return gated

    phase_dir = str(get_phase_dir(plan_path, PHASE_NAME))
    result_path = os.path.join(phase_dir, RESULT_NAME)

    # The detach boundary sits here: after every pre-flight (plan readable, gate
    # satisfied, phase dir created) and before any child runs, so a bad flag or an
    # unmet gate fails on the caller's terminal with no child and no log.
    detached = maybe_detach(
        args=args,
        mode=MODE_NAME,
        phase_dir=phase_dir,
        plan_file=str(plan_path),
        phase=PHASE_NAME,
    )
    if detached is not None:
        return detached

    if args.reaggregate:
        if not os.path.exists(result_path):
            return _fail(
                f"ERROR: --reaggregate found no {RESULT_NAME} in {phase_dir}.\n"
                f"       The invoker persists the subagent's reply there before "
                f"re-invoking; run the phase without --reaggregate to "
                f"(re-)materialize task {TASK_ID}."
            )
        return consume_document(plan_path, result_path)

    # Resume is defined by artifacts (D3i): a completed dispatch left a valid
    # result file, so re-invoking the phase consumes it instead of paying for a
    # second dispatch. `--force` is the way to override that. Only a VALID one:
    # a document that fails the schema or the graph rules (a native host's
    # reply `--reaggregate` refused, or one an older build persisted) would fail
    # the consumer identically on every re-invoke, so it is archived and the
    # task re-dispatched — the executor's own resume rule (`task_is_complete`)
    # reads it the same way (fix round 6).
    if os.path.exists(result_path) and not args.force:
        problems = stale_result_problems(result_path)
        if not problems:
            print(
                f"[resume] {RESULT_NAME} already exists in {phase_dir}; consuming "
                f"it instead of re-dispatching (pass --force to re-dispatch)."
            )
            return consume_document(plan_path, result_path)
        summary = problems[0] + (
            f" (+{len(problems) - 1} more)" if len(problems) > 1 else ""
        )
        if getattr(args, "dry_run_subagents", False):
            print(
                f"[dry-run-subagents] the existing {RESULT_NAME} is invalid "
                f"({summary}); keeping it, since no child is started to replace "
                f"it. The real run archives it and re-dispatches task {TASK_ID}."
            )
        else:
            try:
                archived = archive_file(Path(result_path))
            except OSError as exc:
                return _fail(
                    f"ERROR: the existing {RESULT_NAME} in {phase_dir} is invalid "
                    f"({summary}) and could not be moved aside: {exc}\n"
                    f"       Remove or rename it by hand, then re-run."
                )
            print(
                f"[resume] the existing {RESULT_NAME} is invalid ({summary}); "
                f"archived it as {archived} and re-dispatching task {TASK_ID} "
                f"instead of consuming it."
            )

    if args.force and os.path.exists(result_path):
        # Skipping the branch above is not enough: the executor's resume rule is
        # defined by the same artifact (D3i — a task is done iff its result file
        # exists, parses and validates), so leaving the old file in place makes
        # the dispatch below a no-op and the consumer ingests exactly the stale
        # document `--force` was invoked to replace. Move it aside *before*
        # materialization, and archive rather than delete: a result that cost a
        # dispatch is never thrown away silently.
        if getattr(args, "dry_run_subagents", False):
            # D3l: this run starts no child, so there is nothing to replace the
            # old result with — archiving it here would change the phase dir
            # under a flag whose promise is that nothing else changes.
            print(
                f"[dry-run-subagents] keeping the existing {RESULT_NAME}: no child "
                f"is started, so nothing would replace it. The real --force run "
                f"archives it."
            )
        else:
            try:
                archived = archive_file(Path(result_path))
            except OSError as exc:
                return _fail(
                    f"ERROR: --force could not move the existing {RESULT_NAME} in "
                    f"{phase_dir} aside: {exc}\n"
                    f"       Leaving it would make the re-dispatch a no-op and this "
                    f"phase would consume the stale document instead. Remove or "
                    f"rename it by hand, then re-run."
                )
            print(f"[force] archived the previous {RESULT_NAME} as {archived}")

    try:
        task_file, document = materialize_task_file(plan_path, phase_dir)
    except TaskFileError as exc:
        return _fail(f"ERROR: {exc.message}")
    record_artifact(task_file)
    task = tasks_of(document)[0]
    print(f"Materialized 1 {TASK_KIND} task: {task_file}")

    if exec_subagents_requested(args) and not getattr(
        args, "dry_run_subagents", False
    ):
        from utils.subagent_executor import ExecutorError

        try:
            preflight_workspace_runner(task, anchor=str(plan_path))
        except ExecutorError as exc:
            return _fail(f"ERROR: {exc.message}")

    print(f"\n{PENDING_MARKER} {task_file}")
    if dispatch_subagent_tasks(
        args,
        task_file=task_file,
        phase_dir=phase_dir,
        phase=PHASE_NAME,
        document=document,
        plan_path=str(plan_path),
        label="task generation",
        retry_command=cli_common.retry_command(
            MODE_NAME, plan_path, "--yes",
            flags=cli_common.current_replay_flags(mode=MODE_NAME),
        ),
    ):
        # D3b: same process, straight on to the consumer.
        return consume_document(plan_path, result_path)

    # Native-subagent host: run `task.prompt`, write the reply to the task's
    # output_path, then hand back exactly one follow-up command (D1c).
    # The plan as the user typed it (fix round 14: the host ran and quoted
    # the absolute path).
    follow_up = cli_common.retry_command(
        MODE_NAME, cli_common.typed_plan_for(plan_path), "--reaggregate",
        flags=cli_common.current_replay_flags(mode=MODE_NAME),
    )
    prompt_file = task.get("prompt_path")
    if prompt_file:
        print(
            f"\nRun the prompt in {prompt_file} (the task's `prompt` in "
            f"{task_file}, byte for byte), write the reply to {result_path},"
        )
    else:
        print(f"\nRun the prompt in {task_file}, write the reply to {result_path},")
    print("then continue with:")
    print(f"  {follow_up}")
    record_next(follow_up)
    update_status(
        phase_dir,
        {
            "state": "task_generation_pending",
            "stdout_markers": [PENDING_MARKER.strip("[]")],
            "task_file": task_file,
            "reaggregate_mode": MODE_NAME,
            "plan_file": str(plan_path),
            # The durable triple's third element (D2): the flag list, never a
            # resolved command.
            "replay_flags": cli_common.current_replay_flags(mode=MODE_NAME),
        },
    )
    return EXIT_OK


def main(argv: Optional[Sequence[str]] = None) -> int:
    bootstrap_streams()
    args = parse_args(argv)
    return run_generate_tasks(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
