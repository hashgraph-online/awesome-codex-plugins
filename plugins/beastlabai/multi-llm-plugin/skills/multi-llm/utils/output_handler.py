"""Output file handling utilities for managing files on rerun."""

import hashlib
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Phase-to-subdirectory mapping (kebab-case for on-disk directories)
PHASE_DIRECTORIES = {
    'review-plan': 'review-plan',
    'apply-suggestions': 'apply-suggestions',
    'tasks': 'tasks',
    'review-tasks': 'review-tasks',
    'implement': 'implement',
    'code-review': 'code-review',
    'apply-fixes': 'apply-fixes',
    # apply-code-fixes is the one mode whose phase name (modes.py) and on-disk
    # directory word differ; without this entry the identity fallback below
    # looks for a directory that never gets created (see
    # full_workflow_orchestrator.WRITE_PHASE_DIRS / html_report_generator's
    # _APPLY_PHASE_STATE_KEYS, which already carry this same mapping).
    'apply-code-fixes': 'apply-fixes',
    'apply-task-suggestions': 'apply-task-suggestions',
}

# Map output_type to phase for get_output_paths() backward compat
# NOTE: For ambiguous types (grouped, validation), callers in
# code_review_orchestrator.py MUST pass explicit phase='code-review'
OUTPUT_TYPE_TO_PHASE = {
    'reviews': 'review-plan',
    'grouped': 'review-plan',           # Ambiguous - prefer explicit phase
    'validation': 'review-plan',        # Ambiguous - prefer explicit phase
    'backup': 'review-plan',
    'changes': 'review-plan',
    'applied_suggestions': 'apply-suggestions',
    'tasks': 'tasks',
    'implementation_summary': 'implement',
    'code_review': 'code-review',
    'code_review_issues': 'code-review',
    'code_review_grouped': 'code-review',
    'code_review_validation': 'code-review',
    'task_review': 'review-tasks',
    'task_review_grouped': 'review-tasks',
    'task_review_validation': 'review-tasks',
    'applied_fixes': 'apply-fixes',
    'applied_task_suggestions': 'apply-task-suggestions',
}

# Map output_type to actual filename (directory provides context)
OUTPUT_TYPE_TO_FILENAME = {
    'reviews': 'report.md',
    'implementation_summary': 'summary.md',
    'code_review': 'report.md',
    'tasks': 'tasks.md',
    'applied_suggestions': 'results.json',
    'applied_fixes': 'summary.md',
    'backup': 'backup.md',
    'changes': 'changes.md',
    'grouped': 'grouped.json',
    'validation': 'validation.json',
    'code_review_issues': 'issues.json',
    'code_review_grouped': 'grouped.json',
    'code_review_validation': 'validation.json',
    'task_review': 'report.md',
    'task_review_grouped': 'grouped.json',
    'task_review_validation': 'validation.json',
    'applied_task_suggestions': 'results.json',
}

def archive_file(path: Path) -> Path:
    """Archive an existing file by renaming it with a timestamp."""
    if not path.exists():
        return path

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = path.stem
    suffix = path.suffix
    archived_path = path.parent / f"{stem}_{timestamp}{suffix}"

    path.rename(archived_path)
    return archived_path

def prepare_output_file(path: Path, mode: str = "rename") -> Path:
    """
    Prepare output file path, handling existing files.

    Args:
        path: Target output file path
        mode: "rename" (archive old file), "append", or "keep_first"

    Returns:
        Path to write to
    """
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    if mode == "append":
        return path

    if mode == "keep_first":
        return path

    archived = archive_file(path)
    print(f"Archived existing file: {archived}")
    return path

def append_to_changelog(path: Path, content: str, section_title: Optional[str] = None) -> None:
    """Append content to a changelog file with timestamp header."""
    if section_title is None:
        section_title = "Changes Applied"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = f"""
---

## Run: {timestamp}

### {section_title}
{content}
"""

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'a', encoding='utf-8') as f:
        f.write(entry)

def sanitize_prefix(name: str) -> str:
    """Sanitize a plan name for use as a directory/file prefix.

    This matches the derive_prefix() logic in orchestrators to ensure consistency.
    - Removes .md extension if present
    - Replaces non-alphanumeric characters (except - and _) with underscores
    - Removes consecutive underscores
    - Strips leading/trailing underscores
    """
    # Remove .md extension
    if name.endswith('.md'):
        name = name[:-3]
    # Replace invalid characters with underscore
    sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '_', name)
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Strip leading/trailing underscores
    return sanitized.strip('_')


def slugify_question(question: str) -> str:
    """Slugify a free-text question into a stable, collision-resistant dir name.

    This is intentionally distinct from :func:`sanitize_prefix` (which keeps
    case, uses underscores, and never truncates). The ``ask`` mode needs a
    short, lowercase, hyphenated slug with a hash suffix so that two *different*
    questions can never map to the same directory.

    Algorithm:
    - lowercase the question;
    - replace every run of non-alphanumeric characters with a single ``-``;
    - strip leading/trailing ``-``;
    - truncate to 50 chars (then strip a trailing ``-`` if truncation left one);
    - append ``-<hash8>`` where ``<hash8>`` is the first 8 hex chars of
      ``sha1`` over the **full, original** question text (utf-8).

    The hash suffix is mandatory: it disambiguates two different questions that
    normalize/truncate to the same 50-char prefix (or differ only in
    punctuation), so distinct questions never silently share a directory.
    Identical question text deliberately produces an identical slug (the
    legitimate resume case).

    Args:
        question: The verbatim, original free-text question.

    Returns:
        A slug of the form ``<normalized-prefix>-<hash8>``.
    """
    hash8 = hashlib.sha1(question.encode("utf-8")).hexdigest()[:8]
    normalized = re.sub(r'[^a-z0-9]+', '-', question.lower()).strip('-')
    if len(normalized) > 50:
        normalized = normalized[:50].rstrip('-')
    if not normalized:
        # All-punctuation / empty-after-normalization questions still get a
        # readable, unique dir via the (distinct) hash suffix.
        normalized = "question"
    return f"{normalized}-{hash8}"


def derive_prefix(plan_file: str) -> str:
    """Derive output prefix from a plan file path.

    Convenience wrapper around :func:`sanitize_prefix` that extracts
    the basename first.  This is the canonical implementation —
    orchestrators should delegate here instead of reimplementing.

    Args:
        plan_file: Path (string) to the plan file.

    Returns:
        Sanitized prefix string suitable for directory names.
    """
    basename = os.path.basename(plan_file)
    return sanitize_prefix(basename)


def find_output_dir(plan_file: str, *, guard_double_nesting: bool = True) -> str:
    """Find the output directory for a plan file.

    Canonical implementation of the pattern used by all three apply
    orchestrators.

    Args:
        plan_file: Path (string) to the plan file.
        guard_double_nesting: When ``True`` (default), if the parent
            directory already matches the derived prefix the parent is
            returned directly, preventing double-nesting.  The
            apply-code-fixes orchestrator relies on this guard; the
            apply-suggestions and apply-task-suggestions orchestrators
            originally did **not** have it, so they pass ``False``.

    Returns:
        String path to the output directory.
    """
    prefix = derive_prefix(plan_file)
    base_dir = os.path.dirname(plan_file) or "."

    # Guard against double-nesting if parent already is the prefix
    if guard_double_nesting and os.path.basename(base_dir) == prefix:
        return base_dir

    out_dir = os.path.join(base_dir, prefix)
    return out_dir


def output_dir_path(plan_path: Path) -> Path:
    """Where a plan's generated files live — **computed, never created**.

    :func:`get_output_dir` is the same computation plus ``mkdir``. Readers that
    must not write (``status``, which is polled while another run owns the dir)
    use this one; producers keep using ``get_output_dir``.
    """
    plan_path = Path(plan_path)
    return plan_path.parent / sanitize_prefix(plan_path.stem)


def phase_dir_path(plan_path: Path, phase: str) -> Path:
    """A phase's output directory — computed, never created (see above)."""
    return output_dir_path(plan_path) / PHASE_DIRECTORIES.get(phase, phase)


#: The files the workflow itself writes at the top of a plan's output folder,
#: beside the phase folders (:data:`PHASE_DIR_NAMES`): the state file and the
#: prior-changes log every write phase shares (``prior_changes.FILENAME``).
WORKFLOW_ROOT_FILES = ("state.json", "prior_changes.jsonl")

#: The suffixes of the workflow's own dot-files there: an atomic write's temp
#: file (``.state_*.tmp``, ``.metrics_*.tmp``, ``.tracking_*.tmp``) and a
#: lock file (``.state.lock``).
_WORKFLOW_DOTFILE_SUFFIXES = (".tmp", ".lock")

#: A task list is a Markdown document: generate-tasks writes
#: ``<output folder>/tasks/tasks.md`` and implement parses the file the
#: ``TASKS_FILE`` marker names as Markdown. A marker naming anything else names
#: no task list, and following it left out real code (fix round 8).
_TASK_LIST_SUFFIXES = (".md", ".markdown")


def _is_workflow_part(entry: "os.DirEntry") -> bool:
    """Whether *entry*, a child of an output folder, is one the workflow writes."""
    name = entry.name
    try:
        is_dir = entry.is_dir(follow_symlinks=False)
    except OSError:
        return False
    if is_dir:
        return name in PHASE_DIR_NAMES
    if name in WORKFLOW_ROOT_FILES:
        return True
    return name.startswith(".") and name.endswith(_WORKFLOW_DOTFILE_SUFFIXES)


def _output_folder_entries(folder, rel: str) -> list:
    """What of *folder*, a plan's output folder, is the workflow's: entries under *rel*.

    * everything in it is the workflow's (the state file, the prior-changes
      log, the phase folders, its own temp and lock files): ``[rel]``, the
      whole folder, so an untracked output folder is never listed file by
      file;
    * it also holds anything else — a code folder that shares the plan's
      name (``src/feature.md`` beside ``src/feature/``), where the workflow
      puts its state too: only the workflow's own entries, so the code
      beside them stays in ``tracked_files`` and in review-code's scope;
    * none of it is the workflow's, or there is no such folder: nothing. The
      folder's name alone says nothing about whose it is.

    *rel* ends in ``/``.
    """
    try:
        with os.scandir(str(folder)) as children:
            children = list(children)
    except OSError:
        return []
    ours = [child for child in children if _is_workflow_part(child)]
    if not ours:
        return []
    if len(ours) == len(children):
        return [rel]
    return sorted(
        rel + child.name + ("/" if child.is_dir(follow_symlinks=False) else "")
        for child in ours
    )


def workflow_file_entries(plan_path, *, root, output_dirs=()) -> list:
    """The workflow's own files for *plan_path*, relative to the repository *root*.

    The plan, what of its output folder is the workflow's (``state.json``,
    the prior-changes log, every phase folder, the generated task list) and
    the task list the plan's ``TASKS_FILE`` marker names. None of them is
    code: ``tracked_files`` must never record them and ``review-code`` must
    never review them. Measured 2026-10-05 (Codex racing run 3):
    apply-task-suggestions recorded the plan and ``tasks.md`` as tracked
    files, implement stopped part-way without recording anything, and
    review-code reviewed ``tasks.md`` as code — two duplicate findings —
    while the ``index.html`` implement created was not in its scope at all.

    A folder entry ends in ``/``, the shape ``git_utils.subtract_baseline``
    reads as "this folder and everything beneath it". *output_dirs* adds
    folders the caller knows hold the run's files (the state file's folder);
    the computed output folder is always considered (a ``None`` *plan_path*
    leaves only *output_dirs*). Each folder is read the same way
    (:func:`_output_folder_entries`): left out whole only when everything in
    it is the workflow's, and beside code only the workflow's own entries —
    until fix round 8 the computed folder was left out whatever it held, so a
    plan kept beside code of the same name took that code out of review. The
    ``TASKS_FILE`` target counts only when it is a Markdown file
    (:data:`_TASK_LIST_SUFFIXES`): a marker naming a code file is not
    followed. A path outside *root*, or *root* itself, is never an entry:
    excluding the whole repository would empty every scope.
    """
    if not root:
        return []
    try:
        real_root = os.path.realpath(str(root))
        plan = Path(os.path.realpath(str(plan_path))) if plan_path else None
    except (OSError, ValueError):
        return []

    def relative(path, folder: bool):
        try:
            rel = os.path.relpath(os.path.realpath(str(path)), real_root)
        except (OSError, ValueError):
            return None
        if rel == "." or rel == ".." or rel.startswith(".." + os.sep):
            return None
        rel = rel.replace(os.sep, "/")
        return rel + "/" if folder else rel

    folders = [Path(folder) for folder in output_dirs if folder]
    files = []
    if plan is not None:
        folders.insert(0, output_dir_path(plan))
        files.append(plan)
        try:
            from .plan_updater import get_tasks_file_path
        except ImportError:  # pragma: no cover - direct-script import shim
            from utils.plan_updater import get_tasks_file_path  # type: ignore
        try:
            named = get_tasks_file_path(plan.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            named = None
        if named and Path(named).suffix.lower() in _TASK_LIST_SUFFIXES:
            files.append(plan.parent / named)

    candidates = [relative(path, False) for path in files[:1]]
    for folder in folders:
        rel = relative(folder, True)
        if rel:
            candidates.extend(_output_folder_entries(folder, rel))
    candidates.extend(relative(path, False) for path in files[1:])

    entries = []
    for entry in candidates:
        if entry and entry not in entries:
            entries.append(entry)
    return entries


def _mode_phase_names() -> tuple:
    """``modes.phase_names()``, importable from ``utils/`` and from a script run."""
    try:
        import modes  # type: ignore
    except ImportError:  # pragma: no cover - only when utils/ is sys.path[0]
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        import modes  # type: ignore
    return tuple(modes.phase_names())


def _phase_dir_names() -> tuple:
    names: dict = {}
    phases = _mode_phase_names()
    # Every phase a mode owns, as its on-disk directory word
    # (`apply-code-fixes` -> `apply-fixes`), `full` and `ask` included.
    for phase in phases:
        names.setdefault(PHASE_DIRECTORIES.get(phase, phase), None)
    # Then the legacy directory words no mode owns any more (today `tasks`).
    for key, directory in PHASE_DIRECTORIES.items():
        if key not in phases:
            names.setdefault(directory, None)
    names.setdefault('ask', None)
    return tuple(names)


#: The single source of truth for "which child directories of a plan's output
#: dir are phase dirs" (plan §7.4a). Built from the complete mode registry, not
#: from ``PHASE_DIRECTORIES`` (which omits ``full`` and ``generate-tasks``), so a
#: new phase cannot become invisible to ``status``. ``status``'s discovery and its
#: ``--phase`` valid list both read it; any other child (a hand-made backup that
#: copied a ``.status.json``, say) is not a phase.
PHASE_DIR_NAMES: tuple = _phase_dir_names()


def get_phase_dir(plan_path: Path, phase: str) -> Path:
    """Get the output directory for a specific phase.

    Args:
        plan_path: Path to the plan file
        phase: Phase name (review-plan, tasks, implement, etc.)

    Returns:
        Path to the phase subdirectory
    """
    plan_dir = get_output_dir(plan_path)  # e.g., plans/my-feature/
    phase_dir = plan_dir / PHASE_DIRECTORIES.get(phase, phase)
    phase_dir.mkdir(parents=True, exist_ok=True)
    return phase_dir


def get_output_paths(plan_path: Path, output_type: str, phase: Optional[str] = None) -> Path:
    """Get the output file path for a given plan and output type.

    Creates a phase subdirectory within the plan's output folder.
    Files use simplified names since the directory provides context.

    Args:
        plan_path: Path to the plan file (e.g., /path/to/my-plan.md)
        output_type: Type of output file (e.g., "backup", "grouped", "report")
        phase: Optional phase name. If not provided, inferred from output_type.

    Returns:
        Path to the output file in the phase subdirectory
        (e.g., /path/to/my-plan/review-plan/report.md)
    """
    if phase is None:
        phase = OUTPUT_TYPE_TO_PHASE.get(output_type, 'misc')

    phase_dir = get_phase_dir(plan_path, phase)

    # Use mapped filename if available, otherwise construct from output_type
    if output_type in OUTPUT_TYPE_TO_FILENAME:
        filename = OUTPUT_TYPE_TO_FILENAME[output_type]
    else:
        suffix_map = {
            "backup": ".md",
            "changes": ".md",
            "grouped": ".json",
            "validation": ".json",
            "reviews": ".md",
            "code_review": ".md",
            "code_review_issues": ".json",
            "code_review_grouped": ".json",
            "code_review_validation": ".json",
            "tasks": ".md",
            "implementation_summary": ".md",
            "applied_suggestions": ".json",
            "applied_fixes": ".md",
        }
        suffix = suffix_map.get(output_type, ".json")
        filename = f"{output_type}{suffix}"

    return phase_dir / filename

def get_relative_output_path(plan_path: Path, output_type: str, phase: Optional[str] = None) -> str:
    """Get the relative path from the plan file to an output file in the phase subfolder.

    This is used for references in the plan file that link to generated files.

    Args:
        plan_path: Path to the plan file (e.g., /path/to/my-plan.md)
        output_type: Type of output file (e.g., "tasks", "implementation_summary")
        phase: Optional phase name. If not provided, inferred from output_type.

    Returns:
        Relative path from plan to output file (e.g., "my-plan/tasks/tasks.md")
    """
    output_path = get_output_paths(plan_path, output_type, phase)
    # Return relative path from plan's parent directory to the output file.
    # POSIX form: it is a markdown link and a marker other phases read back, in
    # a plan file that may be committed and opened on another OS.
    return output_path.relative_to(plan_path.parent).as_posix()


def get_output_dir(plan_path: Path) -> Path:
    """Get the output directory for a plan's generated files.

    Args:
        plan_path: Path to the plan file

    Returns:
        Path to the output subfolder
    """
    output_dir = output_dir_path(plan_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def cleanup_old_archives(directory: Path, max_age_days: int = 7) -> int:
    """Remove archived files older than specified days."""
    removed = 0
    now = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60

    archive_pattern = re.compile(r'.*_\d{8}_\d{6}\.\w+$')

    for file_path in directory.iterdir():
        if not file_path.is_file():
            continue

        if not archive_pattern.match(file_path.name):
            continue

        file_age = now - file_path.stat().st_mtime
        if file_age > max_age_seconds:
            try:
                file_path.unlink()
                removed += 1
            except Exception:
                pass

    return removed
