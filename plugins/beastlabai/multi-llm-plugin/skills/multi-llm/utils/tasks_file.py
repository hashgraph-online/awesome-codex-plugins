"""Utility for locating and validating task files associated with a plan.

Follows the plan's task-list marker, ``<!-- TASKS_FILE: tasks/tasks.md -->``,
which ``tasks_marker`` reads (:data:`TASKS_FILE_MARKER_PATTERN`,
:func:`tasks_marker_spans`, :func:`tasks_marker`, all re-exported here):
:func:`resolve_tasks_marker` follows it inside the plan's directory, and
:func:`read_task_list` gives the text a phase parses tasks from.
Both fall back to the default location, ``{plan}/tasks/tasks.md``, for a plan
with no marker (:func:`default_tasks_path`); find_tasks_file() adds staleness
warnings and file validation for review-tasks, apply-task-suggestions and
code-review.
See docs/development/workflows.md ("Task generation").
"""

import os
import re
import sys
from pathlib import Path
from typing import NamedTuple, Optional, Sequence, Union

from .clock import parse_iso
from .output_handler import sanitize_prefix
from .tasks_marker import (  # noqa: F401 - the marker's reader, re-exported
    TASKS_FILE_MARKER_PATTERN,
    TASKS_FILE_MARKER_RE,
    _BACKTICK_RUN_RE,
    _FENCE_OPEN_RE,
    _inline_code_ranges,
    _opens_fence,
    markdown_code_ranges,
    tasks_marker,
    tasks_marker_spans,
)

class TasksFileRefused(ValueError):
    """The plan's ``TASKS_FILE`` marker names a path outside the plan's directory.

    ``str(exc)`` is the message :func:`find_tasks_file` prints; ``raw_path`` is
    the marker's value as written and ``reason`` says what is wrong with it.
    """

    def __init__(self, message: str, raw_path: str, reason: str) -> None:
        super().__init__(message)
        self.raw_path = raw_path
        self.reason = reason


class TasksFileAmbiguous(TasksFileRefused):
    """The plan carries ``TASKS_FILE`` markers that name different task lists.

    ``raw_paths`` holds every marker's value as written, in plan order.
    """

    def __init__(self, raw_paths: Sequence[str]) -> None:
        listed = ", ".join(raw_paths)
        super().__init__(
            f"ERROR: the plan carries TASKS_FILE comments naming different task "
            f"lists: {listed}. Keep exactly one (a marker quoted as code does not "
            f"count), or re-run '--generate-tasks' to rewrite them.",
            raw_paths[0],
            f"it carries {len(raw_paths)} markers naming different task lists: {listed}",
        )
        self.raw_paths = list(raw_paths)


class TasksFileMissing(FileNotFoundError):
    """The plan's ``TASKS_FILE`` marker names a task list that is not a file."""

    def __init__(self, path: Path, raw_path: str) -> None:
        super().__init__(f"Tasks file referenced in plan not found: {path}")
        self.path = path
        self.raw_path = raw_path


class TaskList(NamedTuple):
    """The text a phase parses tasks from, and the file it came from.

    ``path`` is ``None`` for a plan with no marker (the legacy format that
    embeds its tasks in the plan), whose ``text`` is the plan itself.
    """

    text: str
    path: Optional[Path]


def _resolve_one(plan_dir: str, raw_path: str) -> str:
    if os.path.isabs(raw_path):
        raise TasksFileRefused(
            f"ERROR: TASKS_FILE comment contains an absolute path: {raw_path}. "
            f"Only relative paths within the plan directory are allowed.",
            raw_path,
            "it is an absolute path",
        )
    if ".." in raw_path.split(os.sep) or ".." in raw_path.split("/"):
        raise TasksFileRefused(
            f"ERROR: TASKS_FILE comment contains path traversal (..): {raw_path}. "
            f"Only paths within the plan directory are allowed.",
            raw_path,
            "it climbs out with ..",
        )

    workspace_root = os.path.realpath(plan_dir)
    resolved = os.path.realpath(os.path.join(plan_dir, raw_path))
    if not resolved.startswith(workspace_root + os.sep) and resolved != workspace_root:
        raise TasksFileRefused(
            f"ERROR: TASKS_FILE path resolves outside the plan directory: {resolved}. "
            f"Must be within: {workspace_root}",
            raw_path,
            f"it resolves to {resolved}",
        )
    return resolved


def resolve_tasks_marker(
    plan_path: Union[str, "os.PathLike[str]"], plan_text: Optional[str] = None
) -> Optional[Path]:
    """The real path of the task list the plan's marker names, or ``None`` without one.

    Each marker must name a relative path that stays inside the plan's
    directory: an absolute path, a ``..`` part, or a symlink that leads out
    raises :class:`TasksFileRefused`. Markers that lead to different files
    raise :class:`TasksFileAmbiguous`: which one is current is the plan
    author's call, and following the first would implement a stale or
    pasted list. Whether the file exists is the caller's question.
    *plan_text* is read from *plan_path* when omitted.
    """
    plan_path_abs = os.path.abspath(str(plan_path))
    plan_dir = os.path.dirname(plan_path_abs)
    if plan_text is None:
        with open(plan_path_abs, "r", encoding="utf-8") as handle:
            plan_text = handle.read()
    raw_paths = [raw for _, _, raw in tasks_marker_spans(plan_text)]
    if not raw_paths:
        return None
    resolved = [_resolve_one(plan_dir, raw) for raw in raw_paths]
    if len(set(resolved)) > 1:
        raise TasksFileAmbiguous(raw_paths)
    return Path(resolved[0])


def default_tasks_path(plan_path: Union[str, "os.PathLike[str]"]) -> str:
    """Where generate-tasks writes a plan's task list when no marker says
    otherwise: ``{plan_dir}/{sanitized plan name}/tasks/tasks.md``, as a
    path relative to the plan's directory."""
    prefix = sanitize_prefix(os.path.basename(os.path.abspath(str(plan_path))))
    return os.path.join(prefix, "tasks", "tasks.md")


def read_task_list(
    plan_path: Union[str, "os.PathLike[str]"], plan_text: Optional[str] = None
) -> TaskList:
    """The task list a phase parses: the file the plan's marker names, the
    default task list, or the plan.

    The same resolution :func:`find_tasks_file` makes, so every phase reads
    one task list: a plan with no marker reads the default task list
    (:func:`default_tasks_path`, the workflow's own output folder, which no
    plan text names) when that is a file, and is its own task list only when
    it is not. A plan whose marker is refused raises
    :class:`TasksFileRefused`, and one whose marker names no file raises
    :class:`TasksFileMissing`: parsing the plan instead would turn its prose
    into tasks.
    """
    if plan_text is None:
        plan_text = Path(plan_path).read_text(encoding="utf-8")
    resolved = resolve_tasks_marker(plan_path, plan_text)
    if resolved is None:
        plan_dir = os.path.dirname(os.path.abspath(str(plan_path)))
        default = os.path.realpath(os.path.join(plan_dir, default_tasks_path(plan_path)))
        if not os.path.isfile(default):
            return TaskList(plan_text, None)
        return TaskList(Path(default).read_text(encoding="utf-8"), Path(default))
    if not resolved.is_file():
        raise TasksFileMissing(resolved, tasks_marker(plan_text) or "")
    return TaskList(resolved.read_text(encoding="utf-8"), resolved)

#: `update_plan_tasks.py` writes tasks.md and then the plan itself,
#: microseconds apart, so "older" only counts a gap past filesystem clock
#: granularity (some filesystems round mtimes to the second) as a real
#: staleness signal rather than write order within one burst (F3).
STALENESS_TOLERANCE_S = 1.0


def _plan_edited_after_generate_tasks(
    plan_path_abs: str, plan_mtime: float, tasks_mtime: float
) -> bool:
    """Decide whether the tasks-older-than-plan warning describes a human edit.

    Compares the fact actually being asked about — did anything touch the
    plan *after* `generate-tasks` last rewrote it? — rather than raw mtime
    order, which a `generate-tasks` run itself can never satisfy: it writes
    tasks.md and then the plan, then stamps
    `state.json.phases_completed["generate-tasks"]`, so on that very run the
    plan's mtime is always at or before its own completion timestamp.
    Falls back to a tolerant mtime comparison when no such record exists
    (no state.json, or the tasks file predates the generate-tasks map).
    """
    try:
        # Imported here to keep batch_reply, which loads this module, light.
        from .state_manager import StateManager

        state = StateManager(plan_path_abs, read_only=True)
        completed_at = state.get("phases_completed", {}).get("generate-tasks")
        if completed_at:
            completed_ts = parse_iso(completed_at).timestamp()
            return plan_mtime > completed_ts + STALENESS_TOLERANCE_S
    except Exception:
        pass  # No usable state record — fall back to the raw mtime comparison.

    return plan_mtime - tasks_mtime > STALENESS_TOLERANCE_S


def find_tasks_file(plan_path: str) -> str:
    """Locate the tasks file for the given plan.

    Discovery logic:
    1. Read the plan file and check for a <!-- TASKS_FILE: path/to/tasks.md --> comment.
       If found, extract and resolve the path relative to the plan directory.
    2. If no comment found, fall back to {plan_dir}/tasks/tasks.md (using the
       sanitized plan name directory structure).
    3. If neither location exists, raise FileNotFoundError.
    4. After resolving, validate the file is parseable (non-empty, has task headers).

    Path safety: Resolved path must stay within the plan workspace directory.

    Error handling for edge cases:
    - TASKS_FILE comment points to nonexistent file: specific error message
    - Both TASKS_FILE comment and default location exist but differ: prefer comment, log warning
    - Stale tasks file (plan genuinely edited after generate-tasks last ran):
      log warning but proceed. See `_plan_edited_after_generate_tasks` — a
      bare mtime comparison flags every run's own back-to-back tasks.md/plan
      writes, so this checks `state.json.phases_completed["generate-tasks"]`
      first and only falls back to mtimes (with a tolerance) when that
      record is absent.

    Args:
        plan_path: Absolute path to the plan file

    Returns:
        Absolute path to the tasks file

    Raises:
        FileNotFoundError: If no tasks file can be found
        ValueError: If the tasks file is malformed
    """
    plan_path_abs = os.path.abspath(plan_path)
    plan_dir = os.path.dirname(plan_path_abs)

    # 1. The plan's <!-- TASKS_FILE: path/to/tasks.md --> marker, followed only
    # inside the plan's directory. A refusal is exit 1 here, as it always was.
    try:
        resolved = resolve_tasks_marker(plan_path_abs)
    except TasksFileRefused as refused:
        print(str(refused), file=sys.stderr)
        sys.exit(1)
    comment_path = str(resolved) if resolved is not None else None

    # 2. Determine default tasks file location
    # Uses the plan's output directory structure: {plan_dir}/{sanitized_name}/tasks/tasks.md
    default_path = os.path.realpath(os.path.join(plan_dir, default_tasks_path(plan_path_abs)))

    # 3. Resolve which file to use
    tasks_path = None

    if comment_path:
        # TASKS_FILE comment found
        if not os.path.isfile(comment_path):
            raise FileNotFoundError(
                f"Tasks file referenced in plan not found: {comment_path}. "
                f"Re-run '--generate-tasks' or correct the TASKS_FILE comment."
            )

        # Check if default also exists and differs
        if (os.path.isfile(default_path)
                and os.path.realpath(comment_path) != os.path.realpath(default_path)):
            print(
                f"Note: Using tasks file from TASKS_FILE comment ({comment_path}), "
                f"ignoring default tasks/tasks.md.",
                file=sys.stderr,
            )

        tasks_path = comment_path
    elif os.path.isfile(default_path):
        tasks_path = default_path
    else:
        raise FileNotFoundError(
            "No tasks file found. Run '--generate-tasks' first, then retry."
        )

    # 4. Check for staleness (tasks file older than plan)
    try:
        tasks_mtime = os.path.getmtime(tasks_path)
        plan_mtime = os.path.getmtime(plan_path_abs)
        if _plan_edited_after_generate_tasks(plan_path_abs, plan_mtime, tasks_mtime):
            print(
                "Warning: Tasks file is older than the plan file. "
                "Consider re-running '--generate-tasks' to pick up plan changes.",
                file=sys.stderr,
            )
    except OSError:
        pass  # If we can't stat, skip staleness check

    # 5. Validate the file is parseable
    try:
        with open(tasks_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (IOError, OSError) as e:
        raise ValueError(f"Cannot read tasks file {tasks_path}: {e}") from e

    if not content.strip():
        raise ValueError(
            f"Tasks file is empty: {tasks_path}. "
            f"Re-run '--generate-tasks' to generate tasks."
        )

    # Check for at least one task header (e.g., ## T001, ### Task T001:)
    task_header_pattern = re.compile(r'^#{2,3}\s+(?:Task\s+)?T\d+', re.MULTILINE)
    if not task_header_pattern.search(content):
        raise ValueError(
            f"Tasks file appears malformed (no task headers like '## T001' found): "
            f"{tasks_path}. Re-run '--generate-tasks' to regenerate."
        )

    return tasks_path
