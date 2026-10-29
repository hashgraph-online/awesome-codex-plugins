#!/usr/bin/env python3
"""Update plan file with generated tasks.

Usage:
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util update-tasks --plan-file <plan_path> --tasks-file <tasks_json_path>

This script:
1. Reads the tasks JSON file
2. Creates the tasks markdown file in {plan}/tasks/tasks.md
3. Updates the plan file with a reference to the tasks file
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.stream_bootstrap import bootstrap_streams
from utils.output_handler import get_output_paths, get_relative_output_path
from utils.plan_updater import insert_tasks_file_reference
from utils.state_manager import get_or_create_state
from utils.subagent_tasks import derive_executor_role


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


def validate_tasks_json(data: Any) -> tuple[bool, str]:
    """
    Validate the tasks JSON structure.

    Args:
        data: Parsed JSON data

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Root must be an object with 'tasks' array"

    if "tasks" not in data:
        return False, "Missing 'tasks' field"

    tasks = data["tasks"]
    if not isinstance(tasks, list):
        return False, "'tasks' must be an array"

    if len(tasks) == 0:
        return False, "'tasks' array is empty"

    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            return False, f"Task {i} is not an object"
        if "id" not in task:
            return False, f"Task {i} missing 'id' field"
        if "title" not in task:
            return False, f"Task {i} missing 'title' field"

    return True, ""


def main(argv=None) -> int:
    """Main entry point."""
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

    # Validate inputs
    if not plan_path.exists():
        print(f"ERROR: Plan file not found: {plan_path}", file=sys.stderr)
        return 1

    if not tasks_json_path.exists():
        print(f"ERROR: Tasks JSON file not found: {tasks_json_path}", file=sys.stderr)
        return 1

    # Read and parse tasks JSON
    try:
        tasks_data = json.loads(tasks_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse tasks JSON: {e}", file=sys.stderr)
        return 1

    # Validate structure
    is_valid, error_msg = validate_tasks_json(tasks_data)
    if not is_valid:
        print(f"ERROR: Invalid tasks JSON: {error_msg}", file=sys.stderr)
        return 1

    tasks = tasks_data["tasks"]
    preamble = tasks_data.get("plan_preamble", "")

    # Generate tasks markdown
    plan_name = plan_path.name
    try:
        tasks_markdown = generate_tasks_markdown(tasks, plan_name)
    except ValueError as e:  # a malformed SOURCE_DATE_EPOCH; nothing written yet
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Get output path for tasks file
    tasks_output_path = get_output_paths(plan_path, "tasks", phase="tasks")
    tasks_relative_path = get_relative_output_path(plan_path, "tasks", phase="tasks")

    # Read plan content
    plan_content = plan_path.read_text(encoding="utf-8")

    # Update plan with tasks file reference
    updated_plan = insert_tasks_file_reference(plan_content, tasks_relative_path)

    if args.dry_run:
        print("Dry run - would perform these actions:")
        print(f"\n1. Create tasks file: {tasks_output_path}")
        print(f"   ({len(tasks)} tasks)")
        print(f"\n2. Update plan file: {plan_path}")
        print(f"   Add reference: <!-- TASKS_FILE: {tasks_relative_path} -->")
        return 0

    # Create tasks directory and file
    tasks_output_path.parent.mkdir(parents=True, exist_ok=True)
    tasks_output_path.write_text(tasks_markdown, encoding="utf-8")
    print(f"Created tasks file: {tasks_output_path}")

    # Update plan file
    plan_path.write_text(updated_plan, encoding="utf-8")
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

    # Re-stamp the hash over the plan *this script just rewrote*. The
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

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
