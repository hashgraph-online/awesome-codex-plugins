#!/usr/bin/env python3
"""Update plan file with generated tasks.

Usage:
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util update-tasks --plan-file <plan_path> --tasks-file <tasks_json_path>

This script:
1. Reads the tasks JSON file and validates it as a task-generation result
2. Creates the tasks markdown file in {plan}/tasks/tasks.md
3. Updates the plan file with a reference to the tasks file

``apply_tasks_document`` does steps 2-3 for a parsed document; generate-tasks
calls it in-process, and ``main`` is the CLI wrapper around it.
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Union

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.atomic_io import atomic_write_bytes, atomic_write_text
from utils.stream_bootstrap import bootstrap_streams
from utils.output_handler import output_file_path
from utils.plan_updater import insert_tasks_file_reference
from utils.state_manager import get_or_create_state
from utils.subagent_tasks import derive_executor_role
from utils.write_safety import PathEscape, contain_local_path, write_below_root
from utils.task_result import normalize_result, supply_result_version, validate_result


COMPLEXITY_COLORS = {
    "low": "#90ee90",
    "medium": "#f4a460",
    "high": "#cd5c5c",
}


#: The one format the tasks file's ``*Generated: …*`` line is rendered in.
GENERATED_STAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def generated_stamp() -> str:
    """The instant the tasks file says it was generated, as rendered text.

    Local wall clock, exactly as it always was — unless ``SOURCE_DATE_EPOCH``
    is set, the reproducible-builds convention: then that instant, in UTC, so
    two runs pinned to the same epoch write byte-identical tasks files. The
    container rig pins it; without that the stamp made every digest of
    ``tasks.md`` a fresh number per run, and a golden baseline could not repeat.

    A malformed value raises rather than falling back: the variable is only ever
    set by something asking for determinism, and a silent wall-clock fallback
    would hand it a non-repeatable file with nothing to say why. Empty counts as
    unset, the way an env file spells "not configured".
    """
    raw = os.environ.get("SOURCE_DATE_EPOCH", "")
    if not raw:
        return datetime.now().strftime(GENERATED_STAMP_FORMAT)
    try:
        if not re.fullmatch(r"[0-9]+", raw):
            raise ValueError("not a non-negative integer")
        instant = datetime.fromtimestamp(int(raw), tz=timezone.utc)
    except (ValueError, OverflowError, OSError) as exc:  # out of range, too
        raise ValueError(
            f"SOURCE_DATE_EPOCH must be a non-negative integer count of seconds "
            f"since the Unix epoch, got {raw!r} ({exc})") from exc
    return instant.strftime(GENERATED_STAMP_FORMAT)


def task_executor_role(task: Dict[str, Any]) -> str:
    """Return a task record's executor role (D2h).

    ``executor_role`` is authoritative; a record written before the rename is
    read through its legacy ``subagent_type``, so no reader branches on the
    Claude-Code-only field any more.
    """
    role = task.get("executor_role")
    if role in ("agent", "human"):
        return role
    return derive_executor_role(task.get("subagent_type"))


def generate_dependency_diagram(tasks: List[Dict[str, Any]]) -> str:
    """
    Generate a Mermaid graph TD diagram showing task dependencies.

    Args:
        tasks: List of task dictionaries with id, title, depends_on, estimated_complexity

    Returns:
        Mermaid diagram wrapped in a fenced code block
    """
    lines = ["```mermaid", "graph TD"]

    # Node declarations
    for task in tasks:
        task_id = task.get("id", "T000")
        title = task.get("title", "Untitled")
        if len(title) > 40:
            title = title[:37] + "..."
        # Escape quotes in title for Mermaid
        title = title.replace('"', '#quot;')
        if task_executor_role(task) == "human":
            lines.append(f'    {task_id}(["{task_id}: {title}"])')
        else:
            lines.append(f'    {task_id}["{task_id}: {title}"]')

    lines.append("")

    # Edges from depends_on
    has_edges = False
    for task in tasks:
        task_id = task.get("id", "T000")
        for dep in task.get("depends_on", []):
            lines.append(f"    {dep} --> {task_id}")
            has_edges = True

    if has_edges:
        lines.append("")

    # Style nodes by complexity
    for task in tasks:
        task_id = task.get("id", "T000")
        if task_executor_role(task) == "human":
            color = "#87ceeb"  # Light blue for human/manual tasks
        else:
            complexity = task.get("estimated_complexity", "medium")
            color = COMPLEXITY_COLORS.get(complexity, COMPLEXITY_COLORS["medium"])
        lines.append(f"    style {task_id} fill:{color}")

    lines.append("```")
    return "\n".join(lines)


def generate_tasks_markdown(tasks: List[Dict[str, Any]], plan_name: str) -> str:
    """
    Generate markdown content for the tasks file.

    Args:
        tasks: List of task dictionaries
        plan_name: Name of the parent plan file

    Returns:
        Formatted markdown string
    """
    lines = [
        f"# Implementation Tasks for {plan_name}",
        "",
        f"*Generated: {generated_stamp()}*",
        "",
        f"**Parent Plan**: [{plan_name}](../{plan_name})",
        "",
        "---",
        "",
    ]

    # Dependency diagram
    if len(tasks) > 1:
        lines.append("## Dependency Graph")
        lines.append("")
        lines.append(generate_dependency_diagram(tasks))
        lines.append("")
        lines.append("---")
        lines.append("")

    for task in tasks:
        task_id = task.get("id", "T000")
        title = task.get("title", "Untitled Task")
        description = task.get("description", "")
        depends_on = task.get("depends_on", [])
        files_to_modify = task.get("files_to_modify", [])
        files_to_create = task.get("files_to_create", [])
        acceptance_criteria = task.get("acceptance_criteria", [])
        complexity = task.get("estimated_complexity", "medium")
        executor_role = task_executor_role(task)

        # Task header
        lines.append(f"### Task {task_id}: {title}")

        # Dependencies
        if depends_on:
            deps_str = ", ".join(depends_on)
            lines.append(f"**Dependencies**: {deps_str}")
        else:
            lines.append("**Dependencies**: None")

        # Files. BOTH lines are always rendered, `none` when the task declares
        # no files: `task_decomposer._explicit_files` reads "neither line
        # present" as "hand-written task, guess the files from the narrative",
        # so omitting them for an empty list handed the keyword heuristic the
        # one kind of task it must never see — a generated one. The parser
        # already discards `none`/`n/a`/`-`, so an empty declaration round-trips
        # as empty instead of as absent.
        modify_text = ', '.join(files_to_modify) if files_to_modify else "none"
        create_text = ', '.join(files_to_create) if files_to_create else "none"
        lines.append(f"**Files to modify**: {modify_text}")
        lines.append(f"**Files to create**: {create_text}")

        # Complexity and executor. tasks.md is read by every host and by humans,
        # so it names the host-neutral executor role, never a Claude Code agent
        # type. The human branch's wording is unchanged — it was already
        # host-neutral and users recognize it.
        lines.append(f"**Complexity**: {complexity}")
        if executor_role == "human":
            lines.append("**Type**: Manual (user action required)")
        else:
            lines.append(f"**Executor**: {executor_role}")
        lines.append("")

        # Description
        if description:
            lines.append(description)
            lines.append("")

        # Acceptance criteria
        if acceptance_criteria:
            lines.append("**Acceptance Criteria**:")
            for criterion in acceptance_criteria:
                lines.append(f"- [ ] {criterion}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return '\n'.join(lines)


#: A task list the plan already carries: a heading whose text is "Tasks" or
#: "<anything> tasks" (``### Tasks``, ``## Implementation tasks``, ``### Implementation
#: tasks with dependencies``). The pointer section this script itself writes is
#: told apart by the TASKS_FILE marker inside it.
_IN_PLAN_TASK_HEADING = re.compile(
    r"^#{2,4}[ \t]+(?:[\w-]+[ \t]+)?tasks\b[^\n]*$", re.IGNORECASE | re.MULTILINE
)


def find_in_plan_task_sections(plan_content: str) -> List[str]:
    """Headings of task lists the plan holds besides the generated pointer.

    The 2026-10-01 runs ended with two diverging task lists in one plan
    (`### Tasks`, `## Implementation tasks`, ... from apply-suggestions, then this
    script's pointer). Merging them is not this script's job, so it only names
    them: the caller prints a notice and the user decides which list stands.
    """
    found: List[str] = []
    for match in _IN_PLAN_TASK_HEADING.finditer(plan_content):
        rest = plan_content[match.end():]
        nxt = re.search(r"^#{1,4}[ \t]", rest, re.MULTILINE)
        body = rest[: nxt.start()] if nxt else rest
        if "TASKS_FILE" in body or "TASKS_FILE" in match.group(0):
            continue
        found.append(match.group(0).strip())
    return found


class TasksDocumentError(Exception):
    """A task-generation document was not applied.

    Raised before the first write for a missing plan, an invalid document, a
    malformed ``SOURCE_DATE_EPOCH`` or a task list that would resolve out of
    the plan's directory; an ``OSError`` from a write propagates as
    itself. Callers that must leave the plan untouched snapshot it first
    (``generate_tasks_orchestrator._Snapshot``).
    """


class TasksOutputEscape(TasksDocumentError):
    """A file in the plan's output folder resolves outside the plan's
    directory, so it is not written (:func:`contain_plan_output`)."""


class TasksDocumentInvalid(TasksDocumentError):
    """The document fails ``validate_result("task_generation", ...)``: the
    schema, then ``task_decomposer.validate_generated_tasks``' graph rules."""

    def __init__(self, errors: List[str]):
        self.errors = list(errors)
        super().__init__(
            "the document is not a valid task-generation result:\n"
            + "\n".join(f"  - {problem}" for problem in self.errors[:10])
        )


@dataclass(frozen=True)
class AppliedTasks:
    """What :func:`apply_tasks_document` wrote, or would write on a dry run."""

    tasks_path: Path
    tasks_relative_path: str
    task_count: int
    dry_run: bool


def plan_output_root(plan_path: Path) -> str:
    """The folder *plan_path*'s outputs stay in: the directory the plan is
    reached through. The plan file itself is not followed, so a plan kept
    elsewhere and linked in keeps its outputs beside the link."""
    return os.path.dirname(os.path.abspath(plan_path))


def contain_plan_output(
    plan_path: Path, path: Path, *, what: str, follow_final: bool = True
) -> Path:
    """Where *path*, a file in *plan_path*'s output folder, resolves;
    :class:`TasksOutputEscape` unless that stays inside the plan's directory
    (docs/development/write-safety.md#plan-output-containment).

    The boundary (:func:`plan_output_root`), resolved, is inside the plan's
    repository, and is where implement reads the task list from
    (``tasks_file.resolve_tasks_marker`` refuses a list that resolves
    anywhere else). A link that stays inside is resolved, so the write lands
    where it leads; *follow_final* off resolves the folder alone, for a
    rename of the entry itself. Pure: nothing is created. This is the check;
    the write is :func:`write_plan_output` (or ``write_safety``'s rename and
    removal), made through the resolved folder held, so a link swapped in
    after this check is never followed.
    """

    path = Path(path)
    plan_dir = plan_output_root(plan_path)
    try:
        if follow_final:
            return contain_local_path(path, plan_dir, what=what)
        return contain_local_path(path.parent, plan_dir, what=what) / path.name
    except PathEscape as escape:
        raise TasksOutputEscape(
            f"{escape.message} A symlink in the plan's output folder leads out of "
            f"the plan's directory, so nothing was written: the plan and its "
            f"state are unchanged. Remove the link, or point it inside "
            f"{plan_dir}, and re-run."
        ) from escape


def write_plan_output(plan_path: Path, target: Path, data: Union[str, bytes]) -> None:
    """Write *data* at *target*, a file in *plan_path*'s output folder as
    :func:`contain_plan_output` resolved it, through its folder held below
    the plan's directory and never through a link
    (``write_safety.write_below_root``). Text is written as
    :func:`replace_file` writes it (the platform's newlines); an existing
    file's mode carries over. ``OSError`` when it is not written: a link or
    a moved folder met on the way is refused, never followed."""

    if isinstance(data, str):
        data = data.replace("\n", os.linesep).encode("utf-8")
    write_below_root(plan_output_root(plan_path), target, data)


def replace_file(path: Path, data: Union[str, bytes]) -> None:
    """Write *data* to the plan at *path* by ``atomic_io``'s atomic write.

    A crash or a failed write leaves the old bytes in place, never a truncated
    file. Text is written the way ``Path.write_text(encoding="utf-8")`` writes
    it (the platform's newlines); bytes land exactly. A symlink is written
    through to its target, so the link survives: the plan is the user's own
    file, which they may keep elsewhere and link in on purpose, so it is the
    one file this flow follows a link for. Every output written beside it
    goes through :func:`write_plan_output`, which never does. An existing
    file's permission bits carry over to the replacement; a new file gets the
    process umask, as ``write_text`` would. The temp file is never readable
    more widely than the file it replaces, and a returned call survives a
    power loss.
    """
    if isinstance(data, bytes):
        atomic_write_bytes(path, data, follow_symlinks=True)
    else:
        atomic_write_text(path, data, newline=os.linesep, follow_symlinks=True)


def apply_tasks_document(
    plan_path: Path, data: Any, *, dry_run: bool = False
) -> AppliedTasks:
    """Render *data*'s tasks into ``tasks.md``, point the plan at it, record the phase.

    *data* is a parsed task-generation document. It is read the way every lane
    reads one — an omitted empty list, ``subagent_type`` or ``schema_version``
    is supplied in place (``task_result.normalize_result``,
    ``supply_result_version``) — then validated with the executor's own verdict
    for the kind, so nothing reaches the plan that the executor would have
    refused. Raises :class:`TasksDocumentError` (or an ``OSError`` from a
    write) on failure; prints what it did.
    """
    plan_path = Path(plan_path)
    if not plan_path.exists():
        raise TasksDocumentError(f"Plan file not found: {plan_path}")

    normalize_result("task_generation", data)
    supply_result_version("task_generation", data)
    errors = validate_result("task_generation", data)
    if errors:
        raise TasksDocumentInvalid(errors)

    tasks = data["tasks"]
    preamble = data.get("plan_preamble", "")

    try:
        tasks_markdown = generate_tasks_markdown(tasks, plan_path.name)
    except ValueError as e:  # a malformed SOURCE_DATE_EPOCH; nothing written yet
        raise TasksDocumentError(str(e)) from e

    # Computed, not created, then contained before anything is written: a
    # symlink named like the output (the list, its folder, the plan's output
    # folder) must not carry the write out of the plan's directory. A dry run
    # reports the same refusal.
    tasks_output_path = output_file_path(plan_path, "tasks", phase="tasks")
    tasks_target = contain_plan_output(plan_path, tasks_output_path, what="task list")
    tasks_relative_path = tasks_output_path.relative_to(plan_path.parent).as_posix()
    applied = AppliedTasks(
        tasks_path=tasks_output_path,
        tasks_relative_path=tasks_relative_path,
        task_count=len(tasks),
        dry_run=dry_run,
    )

    plan_content = plan_path.read_text(encoding="utf-8")
    updated_plan = insert_tasks_file_reference(plan_content, tasks_relative_path)

    if dry_run:
        print("Dry run - would perform these actions:")
        print(f"\n1. Create tasks file: {tasks_output_path}")
        print(f"   ({len(tasks)} tasks)")
        print(f"\n2. Update plan file: {plan_path}")
        print(f"   Add reference: <!-- TASKS_FILE: {tasks_relative_path} -->")
        return applied

    # Through its folder, held below the plan's directory: a link swapped in
    # after the check above, for the list or a folder above it, is refused.
    write_plan_output(plan_path, tasks_target, tasks_markdown)
    print(f"Created tasks file: {tasks_output_path}")

    # The plan alone is written through a symlink wherever it leads: the
    # user's own file, kept elsewhere and linked in on purpose (not an
    # output, so not contained).
    replace_file(plan_path, updated_plan)
    # Said what was written: a bare "Updated plan file" read as generate-tasks
    # rewriting the plan (OpenCode racing run 4). The section and its
    # TASKS_FILE marker are how every later phase finds the task list.
    print(
        f"Updated plan file: {plan_path} (its \"Implementation Tasks\" section "
        f"now links {tasks_relative_path}, the task list later phases read)"
    )
    existing = find_in_plan_task_sections(plan_content)
    if existing:
        print(
            "NOTICE: the plan already holds its own task list under "
            + ", ".join(f"'{heading}'" for heading in existing)
            + f". {tasks_relative_path} is the list implement follows; the plan's "
            "list is not updated to match it and may disagree. Delete it, or keep "
            "it as background only."
        )

    # Mark generate-tasks phase as completed in state
    state = get_or_create_state(plan_path)
    state.mark_phase_completed("generate-tasks")
    state.save()

    # Store plan preamble for use during implementation
    if preamble:
        state.set("plan_preamble", preamble)
        state.save()
        print(f"Stored plan preamble ({len(preamble)} chars)")

    # Re-stamp the hash over the plan *this function just rewrote*. The
    # StateManager above is constructed after the write, so `_load_or_create`
    # sees the marker insertion as drift and sets `plan_changed: True` — the
    # plugin flagging its own edit as a human's. Measured 2026-09-16: the next
    # `implement --resume` then printed "WARNING: Plan has changed since last
    # session" for a change generate-tasks had made one phase earlier.
    state.refresh_plan_hash()
    state.save()

    # Summary
    print(f"\nSuccessfully generated {len(tasks)} tasks:")
    for task in tasks:
        deps = task.get("depends_on", [])
        deps_str = f" (depends on: {', '.join(deps)})" if deps else ""
        print(f"  - {task['id']}: {task['title']}{deps_str}")

    return applied


def main(argv=None) -> int:
    """``util update-tasks``: read a tasks JSON file and apply it to a plan."""
    bootstrap_streams()
    parser = argparse.ArgumentParser(
        description="Update plan file with generated tasks"
    )
    parser.add_argument(
        "--plan-file",
        required=True,
        help="Path to the plan markdown file"
    )
    parser.add_argument(
        "--tasks-file",
        required=True,
        help="Path to the tasks JSON file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without modifying files"
    )
    args = parser.parse_args(argv)

    plan_path = Path(args.plan_file).resolve()
    tasks_json_path = Path(args.tasks_file).resolve()

    if not plan_path.exists():
        print(f"ERROR: Plan file not found: {plan_path}", file=sys.stderr)
        return 1

    if not tasks_json_path.exists():
        print(f"ERROR: Tasks JSON file not found: {tasks_json_path}", file=sys.stderr)
        return 1

    try:
        tasks_data = json.loads(tasks_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse tasks JSON: {e}", file=sys.stderr)
        return 1

    try:
        apply_tasks_document(plan_path, tasks_data, dry_run=args.dry_run)
    except TasksDocumentInvalid as invalid:
        print(f"ERROR: Invalid tasks JSON: {invalid}", file=sys.stderr)
        return 1
    except TasksDocumentError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
