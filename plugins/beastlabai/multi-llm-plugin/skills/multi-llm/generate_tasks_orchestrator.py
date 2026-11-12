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
import copy
import json
import os
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
    add_scope_policy_argument,
    build_parent_parser,
    record_artifact,
    record_next,
)
from utils.git_utils import get_project_root
from utils.output_handler import (
    archive_name,
    get_output_paths,
    get_phase_dir,
    output_file_path,
    phase_dir_path,
    output_dir_path,
)
from utils.tasks_file import TasksFileRefused, resolve_tasks_marker
from utils.provider_registry import set_run_anchor, SESSION_LAYER
from utils.stream_bootstrap import bootstrap_streams
from utils.subagent_prompts import build_task_generation_prompt
from utils.subagent_tasks import (
    TaskFileError,
    build_inputs,
    make_task,
    make_task_file,
    task_file_text,
    tasks_of,
)
from utils.task_decomposer import TaskDecomposer
from utils import scope_policy_runs
from utils import unattended as unattended_mod
from utils import validation
import update_plan_tasks
from utils import provider_registry
from utils import runner_selection
from utils import runner_preflight
from utils import detach as _detach
from utils import run_record as _run_record
from utils import status_file
from utils import review_orchestrator_base
from utils.providers.types import PROFILE_AGENT_READONLY
from utils.task_outcome import RunnerRejected, ExecutorError
from utils.runner_selection import eligible_runners
from utils.task_result import validate_result, normalize_result, supply_result_version
from update_plan_tasks import replace_file
from utils.held_folder import remove_in_plan_dir, write_in_plan_dir
from utils.write_safety import remove_below_root, write_below_root, rename_below_root
from utils.schema_validator import schema_version_supplied
from utils.failure_capture import FAILED_CAPTURE_DIRNAME
from utils.state_manager import StateManager
from utils.review_orchestrator_base import update_status

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
    add_scope_policy_argument(parser, role="generate-tasks")
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
    plan_path: Path,
    phase_dir: str,
    *,
    repo_root: Optional[str] = None,
    scope_policy: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """Write the one-task ``task_generation`` file and return ``(path, document)``.

    One task, in the same envelope every other kind uses — that is what lets the
    executor, the dry-run preflight, the resume-by-artifact rule and the native
    invoker all treat it as an ordinary batch of size one.

    *scope_policy* ``preserve`` adds the block that keeps the task list to the
    plan (``scope_policy_runs.generation_guidance``) ahead of the reply
    section; ``expand`` or ``None`` leaves the prompt byte for byte as it was.
    """
    plan_text = plan_path.read_text(encoding="utf-8")
    root = repo_root or _resolve_repo_root(plan_path)
    inputs = build_inputs(plan_file=str(plan_path))
    prompt = build_task_generation_prompt(
        plan_text=plan_text, repo_root=root, plan_name=plan_path.name
    )
    prompt = scope_policy_runs.with_guidance(
        prompt, scope_policy_runs.generation_guidance(scope_policy), before="## Reply\n",
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

    # All or none, as for validation: on a write failure the key is dropped
    # and the host runs `prompt` itself.
    validation.write_prompt_sidecars([task], phase_dir, stale_glob=PROMPT_FILE_NAME)
    document = make_task_file(kind=TASK_KIND, tasks=[task], inputs=inputs)
    task_file = os.path.join(phase_dir, TASK_FILE_NAME)
    text = task_file_text(task_file, document)
    # Checked, then written through its folder held below the plan's
    # directory, so a link swapped in after the check is never followed
    # (docs/development/write-safety.md#plan-output-containment).
    try:
        target = update_plan_tasks.contain_plan_output(
            plan_path, Path(task_file), what="task file")
        update_plan_tasks.write_plan_output(plan_path, target, text)
    except update_plan_tasks.TasksOutputEscape as exc:
        raise TaskFileError(str(exc)) from exc
    except OSError as exc:
        raise TaskFileError(
            f"Refusing the task file {task_file}: it was not written ({exc}). "
            f"Nothing was dispatched; re-run once the folder is as it was."
        ) from exc
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

    # The key carries the ladder's layer word (`driver.subagent_runner
    # (session)`), so a refusal or a warning here names the rung that supplied
    # the spec, the way the executor's own preflight does.
    spec, key, layer = runner_selection._resolve_task_source(task, anchor=anchor)
    provider_name, _model = provider_registry.parse_model_spec(spec, anchor=anchor)
    provider = provider_registry.get_provider(provider_name)
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
        runner_preflight.preflight_runner(
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
    kind (``task_result.validate_result``), so a document that fails either
    gets the executor lane's schema-repair re-ask and is never persisted.
    """

    return list(validate_result(TASK_KIND, data))


def stale_result_problems(result_path: str) -> List[str]:
    """Why the result file on disk may not be resumed from, or ``[]``.

    The same verdict ``consume_document`` would reach, taken on a completed
    *copy* (the omitted list keys it would supply), so asking changes nothing
    on disk.
    """

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

    Each file is put back the way its writer writes it, and only when its bytes
    changed: the plan through a symlink (a plan kept elsewhere and linked in),
    ``state.json`` over the entry (its writer replaces a link, never follows
    one), written or removed through its folder held below the plan's
    directory (``held_folder.write_in_plan_dir``, ``remove_in_plan_dir``), and
    the task list at the target ``contain_plan_output`` resolved, written or
    removed through its folder held there too (``write_safety.write_below_root``),
    so a restore never writes out of the plan's directory, nor through a link
    swapped in during the run.
    """

    def __init__(self, plan_path: Path, state_file: Path, tasks_target: Path):
        self._plan, self._tasks = plan_path, tasks_target
        self._root = update_plan_tasks.plan_output_root(plan_path)
        self._before = {
            path: self._read(path) for path in (plan_path, state_file, tasks_target)
        }

    @staticmethod
    def _read(path: Path) -> Optional[bytes]:
        return path.read_bytes() if path.exists() else None

    def _put_back(self, path: Path, before: Optional[bytes]) -> None:
        if path == self._tasks:
            if before is None:
                remove_below_root(self._root, path)
            else:
                write_below_root(self._root, path, before)
        elif before is None:
            if os.path.lexists(path):
                remove_in_plan_dir(path)
        elif path == self._plan:
            replace_file(path, before)
        else:
            write_in_plan_dir(path, before)

    def restore(self) -> None:
        for path, before in self._before.items():
            try:
                if self._read(path) != before:
                    self._put_back(path, before)
            except OSError as exc:  # pragma: no cover - best effort
                print(
                    f"multi-llm warning: could not restore {path}: {exc}",
                    file=sys.stderr,
                )


def verify_outcome(plan_path: Path, expected_count: int) -> List[str]:
    """What the plan and the rendered tasks file must show, or the reasons why not.

    This is the check ``instructions/full-workflow.md`` performed by hand after its
    Task subagent returned, moved into Python so it runs on every host and under
    both invokers — and it reads the *artifacts*, never the reply.
    """
    problems: List[str] = []
    plan_text = plan_path.read_text(encoding="utf-8")
    # The marker is checked the way implement follows it (`read_task_list`):
    # a path implement refuses is a failed generation, even one that leads
    # to the rendered file.
    resolved: Optional[Path] = None
    try:
        resolved = resolve_tasks_marker(plan_path, plan_text)
    except TasksFileRefused as refused:
        problems.append(
            f"implement would refuse the plan's TASKS_FILE marker "
            f"({refused.raw_path}): {refused.reason}"
        )
    else:
        if resolved is None:
            problems.append(
                "the plan carries no <!-- TASKS_FILE: … --> marker, so no later "
                "phase can find a task list"
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
    if resolved is not None and resolved != tasks_path.resolve():
        problems.append(
            f"the TASKS_FILE marker points at {resolved}, not at the rendered "
            f"{tasks_path}"
        )
    return problems


def consume_document(plan_path: Path, result_path: str) -> int:
    """Validate, run ``update_plan_tasks`` in-process, verify, or restore and fail."""

    # Both files this consumer writes beside the plan, checked before the
    # first byte and then written through their folder held below the plan's
    # directory: the task list (by `update_plan_tasks`) and the result
    # document (rewritten below when a key was supplied).
    try:
        tasks_target = update_plan_tasks.contain_plan_output(
            plan_path, output_file_path(plan_path, "tasks", phase="tasks"),
            what="task list")
        result_target = update_plan_tasks.contain_plan_output(
            plan_path, Path(result_path), what="result document")
    except update_plan_tasks.TasksOutputEscape as exc:
        return _fail(f"ERROR: {exc}")

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
    # a later `task_is_complete` re-validates the file, so what was validated
    # and applied is what is on disk.
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
            update_plan_tasks.write_plan_output(
                plan_path, result_target, json.dumps(data, indent=2) + "\n")
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
    snapshot = _Snapshot(plan_path, _state_file_for(plan_path), tasks_target)

    try:
        update_plan_tasks.apply_tasks_document(plan_path, data)
    except update_plan_tasks.TasksDocumentError as exc:
        snapshot.restore()
        return _fail(
            f"ERROR: update_plan_tasks refused the document ({exc}), so the plan "
            f"was not updated. The plan and state.json are back to their "
            f"pre-run bytes."
        )
    except Exception as exc:  # noqa: BLE001 - a crashed consumer must not leave
        snapshot.restore()     # the plan half-written; the bytes go back first
        return _fail(
            f"ERROR: update_plan_tasks raised {type(exc).__name__}: {exc}. The "
            f"plan and state.json are back to their pre-run bytes."
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
    status_file.update_status(phase_dir, {"state": "complete"})
    # The count is this phase's whole output, so report it: a step-only report
    # left `status` printing the one subagent that produced the list
    # (`task_generation 1/1 ok`) as the only number on screen. It is what this
    # run PRODUCED (`generated N tasks`), never a done/total pair: the
    # `tasks 10/10` that pair rendered read as a live count of tasks.md, and
    # stayed 10/10 after apply-task-suggestions split two tasks into four
    # (2026-10-04, Claude Code racing re-run).
    _run_record.report_progress(phase_dir, step="complete", tasks_generated=len(tasks))
    print(f"\nTask generation complete: {len(tasks)} task(s) in {tasks_path}")
    # No "Next: uv run … review-tasks" line here (issue #17, 2026-10-02): it sat
    # beside `[NEXT_COMMAND]` in the log, and a dispatcher command is not a
    # command for the user. The next step, `review-tasks` included as the
    # optional one, is the `[NEXT_COMMAND]` block `multi_llm.main` prints in the
    # host's own spelling (`utils/next_phase.py`).
    return EXIT_OK


def _state_file_for(plan_path: Path) -> Path:
    """Where ``StateManager`` keeps this plan's ``state.json``.

    Computed (never created) from the same output-dir helper ``StateManager``
    uses rather than by constructing one, so taking a snapshot never touches
    git or the clock, and from the plan resolved as ``StateManager`` resolves
    it: a plan linked in keeps its state beside the file the link leads to.
    """

    return output_dir_path(Path(plan_path).resolve()) / "state.json"


def _move_result_aside(
    plan_path: Path,
    result_path: str,
    dry_run: bool,
    *,
    kept: str,
    failed: Callable[[Exception], str],
    done: Callable[[Path], str],
) -> Optional[int]:
    """Archive the result file before a re-dispatch; ``None`` to go on, else the exit.

    Archived, never deleted: a result that cost a dispatch is never thrown away
    silently. Under ``--dry-run-subagents`` (D3l) it stays put — the run starts
    no child, so nothing would replace it, and the flag promises nothing else
    changes. A move that fails is exit 3: leaving the file would make the
    re-dispatch a no-op that consumes it again. So is a folder that resolves out
    of the plan's directory: the rename renames the entry, never a link's
    target, so its directory is what is contained, and the rename is made in
    that folder held below the plan's directory
    (``write_safety.rename_below_root``), never through a link swapped in
    after the check.
    """
    if dry_run:
        print(kept)
        return None

    result = Path(result_path)
    try:
        source = update_plan_tasks.contain_plan_output(
            plan_path, result, what="archived result", follow_final=False)
        name = archive_name(result)
        rename_below_root(update_plan_tasks.plan_output_root(plan_path), source, name)
    except (OSError, update_plan_tasks.TasksOutputEscape) as exc:
        return _fail(failed(exc))
    print(done(result.with_name(name)))
    return None


def _contain_phase_outputs(plan_path: Path) -> Optional[int]:
    """Refuse a run whose outputs a symlink would carry out of the plan's
    directory, before anything is written or dispatched; ``None`` to go on.

    Every destination the phase writes, checked ahead of the gate, the scope
    policy's record in ``state.json``, the prompt sidecar's cleanup and the
    task file: the phase's own folder (status, archive) and the failure
    captures' folder the executor writes in it, the task file, the prompt
    sidecar, the result document and the task list ``update_plan_tasks``
    writes. Refused here, a planted link costs no dispatch and changes
    nothing. Each writer checks its own file again and writes it through its
    folder held, so a link planted after this check is refused there.
    """

    phase_dir = phase_dir_path(plan_path, PHASE_NAME)
    try:
        for path, what in (
            (phase_dir, "generate-tasks folder"),
            (phase_dir / FAILED_CAPTURE_DIRNAME, "failure-capture folder"),
            (phase_dir / TASK_FILE_NAME, "task file"),
            (phase_dir / PROMPT_FILE_NAME, "prompt file"),
            (phase_dir / RESULT_NAME, "result document"),
            (output_file_path(plan_path, "tasks", phase="tasks"), "task list"),
        ):
            update_plan_tasks.contain_plan_output(plan_path, path, what=what)
    except update_plan_tasks.TasksOutputEscape as exc:
        return _fail(f"ERROR: {exc} Nothing was dispatched.")
    return None


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    unattended_mod.mark_needs_human(MODE_NAME)
    return EXIT_NEEDS_HUMAN


# ---------------------------------------------------------------------------
# The scope policy (D6 row 16)
# ---------------------------------------------------------------------------

def _resolve_scope_policy(
    args: argparse.Namespace, plan_path: Path, phase_dir: str
) -> str:
    """The policy this materialization renders, resolved past the detach boundary.

    The typed ``--scope-policy`` (``full`` hands its resolved one over the same
    way), else the live choice an earlier run of this phase recorded, else
    ``expand`` (plans/scope-policy-and-report-tags.md §4). A typed one is
    kept, so the plain re-run that recovers a failed dispatch renders the same
    prompt; a policy nobody typed is recorded as D6 row 16's resolution under
    ``--yes``.
    """

    state = StateManager(plan_path)
    # `--force` regenerates from scratch: a new run, which never inherits an
    # earlier run's recorded choice (as under `full --force`).
    choice = scope_policy_runs.resolve_run_choice(
        getattr(args, "scope_policy", None), state.state, MODE_NAME,
        new_run=bool(getattr(args, "force", False)))
    policy, _source, _decision = scope_policy_runs.open_run(
        None if getattr(args, "dry_run_subagents", False) else state,
        MODE_NAME, choice,
        phase_dir=phase_dir, unattended=bool(getattr(args, "yes", False)),
    )
    return policy


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

    plan_path = Path(os.path.abspath(args.plan_file))
    if not plan_path.is_file():
        print(f"ERROR: Plan file not found: {args.plan_file}", file=sys.stderr)
        print(f"       Resolved path: {plan_path}", file=sys.stderr)
        return EXIT_ERROR

    # §9.3.a/b: the anchor capture point — absolute, before anything can chdir
    # and before any provider read that decides routing. Ahead of `_run_gate`,
    # which is the first thing on this path that can read config.
    set_run_anchor(str(plan_path))

    # A check that produces nothing, ahead of the gate (which may run
    # apply-suggestions inside `full`) so a refused folder changes nothing.
    escaped = _contain_phase_outputs(plan_path)
    if escaped is not None:
        return escaped

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
    detached = review_orchestrator_base.maybe_detach(
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
        refused = _move_result_aside(
            plan_path,
            result_path,
            getattr(args, "dry_run_subagents", False),
            kept=(
                f"[dry-run-subagents] the existing {RESULT_NAME} is invalid "
                f"({summary}); keeping it, since no child is started to replace "
                f"it. The real run archives it and re-dispatches task {TASK_ID}."
            ),
            failed=lambda exc: (
                f"ERROR: the existing {RESULT_NAME} in {phase_dir} is invalid "
                f"({summary}) and could not be moved aside: {exc}\n"
                f"       Remove or rename it by hand, then re-run."
            ),
            done=lambda archived: (
                f"[resume] the existing {RESULT_NAME} is invalid ({summary}); "
                f"archived it as {archived} and re-dispatching task {TASK_ID} "
                f"instead of consuming it."
            ),
        )
        if refused is not None:
            return refused

    if args.force and os.path.exists(result_path):
        # Skipping the branch above is not enough: the executor's resume rule is
        # defined by the same artifact (D3i — a task is done iff its result file
        # exists, parses and validates), so leaving the old file in place makes
        # the dispatch below a no-op and the consumer ingests exactly the stale
        # document `--force` was invoked to replace. Move it aside *before*
        # materialization, and archive rather than delete: a result that cost a
        # dispatch is never thrown away silently.
        refused = _move_result_aside(
            plan_path,
            result_path,
            getattr(args, "dry_run_subagents", False),
            kept=(
                f"[dry-run-subagents] keeping the existing {RESULT_NAME}: no child "
                f"is started, so nothing would replace it. The real --force run "
                f"archives it."
            ),
            failed=lambda exc: (
                f"ERROR: --force could not move the existing {RESULT_NAME} in "
                f"{phase_dir} aside: {exc}\n"
                f"       Leaving it would make the re-dispatch a no-op and this "
                f"phase would consume the stale document instead. Remove or "
                f"rename it by hand, then re-run."
            ),
            done=lambda archived: (
                f"[force] archived the previous {RESULT_NAME} as {archived}"
            ),
        )
        if refused is not None:
            return refused

    policy = _resolve_scope_policy(args, plan_path, phase_dir)
    try:
        task_file, document = materialize_task_file(
            plan_path, phase_dir, scope_policy=policy)
    except TaskFileError as exc:
        return _fail(f"ERROR: {exc.message}")
    record_artifact(task_file)
    task = tasks_of(document)[0]
    print(f"Materialized 1 {TASK_KIND} task: {task_file}")

    if review_orchestrator_base.exec_subagents_requested(args) and not getattr(
        args, "dry_run_subagents", False
    ):
        try:
            preflight_workspace_runner(task, anchor=str(plan_path))
        except ExecutorError as exc:
            return _fail(f"ERROR: {exc.message}")

    print(f"\n{PENDING_MARKER} {task_file}")
    if review_orchestrator_base.dispatch_subagent_tasks(
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
    from utils import process_control

    # A process entry of its own: provider children must stay this process's.
    process_control.restore_sigchld_default()
    sys.exit(main(sys.argv[1:]))
