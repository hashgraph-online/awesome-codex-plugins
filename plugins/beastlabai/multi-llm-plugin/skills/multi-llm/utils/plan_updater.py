"""Plan updater module for marking implementation status in plans."""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# HTML comment markers for idempotent updates
IMPL_START_MARKER = "<!-- IMPLEMENTATION_STATUS_START -->"
IMPL_END_MARKER = "<!-- IMPLEMENTATION_STATUS_END -->"
TASK_STATUS_PATTERN = r'<!-- TASK_STATUS:(\w+):(\w+) -->'

# Markers for generated tasks section (legacy - tasks embedded in plan)
GENERATED_TASKS_START = "<!-- GENERATED_TASKS_START -->"
GENERATED_TASKS_END = "<!-- GENERATED_TASKS_END -->"

# Marker for external tasks file reference (new - tasks in separate file)
TASKS_FILE_REFERENCE_PATTERN = r'<!-- TASKS_FILE:\s*(.+?)\s*-->'
TASKS_FILE_REFERENCE_TEMPLATE = "<!-- TASKS_FILE: {tasks_file} -->"

# Marker for implementation summary file reference
IMPL_SUMMARY_REFERENCE_PATTERN = r'<!-- IMPL_SUMMARY:\s*(.+?)\s*-->'
IMPL_SUMMARY_REFERENCE_TEMPLATE = "<!-- IMPL_SUMMARY: {summary_file} -->"


class PlanUpdater:
    """Updates plan files with implementation status markers."""

    def __init__(self, plan_path: Path):
        """
        Initialize plan updater.

        Args:
            plan_path: Path to the plan markdown file
        """
        self.plan_path = Path(plan_path)
        self.content = ""
        self.task_statuses: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """Load plan content from file."""
        if self.plan_path.exists():
            self.content = self.plan_path.read_text(encoding="utf-8")
            self._parse_existing_statuses()

    def _parse_existing_statuses(self) -> None:
        """Parse existing task status markers from content."""
        matches = re.findall(TASK_STATUS_PATTERN, self.content)
        for task_id, status in matches:
            self.task_statuses[task_id] = status

    def update_task_status(self, task_id: str, status: str) -> None:
        """
        Update status for a specific task.

        Args:
            task_id: Task identifier (e.g., "T001")
            status: Status string (e.g., "completed", "in_progress", "pending")
        """
        self.task_statuses[task_id] = status

    def mark_task_completed(self, task_id: str) -> None:
        """Mark a task as completed."""
        self.update_task_status(task_id, "completed")

    def mark_task_in_progress(self, task_id: str) -> None:
        """Mark a task as in progress."""
        self.update_task_status(task_id, "in_progress")

    def mark_task_failed(self, task_id: str) -> None:
        """Mark a task as failed."""
        self.update_task_status(task_id, "failed")

    def _find_task_section(self, task_id: str) -> Optional[Tuple[int, int]]:
        """
        Find the start and end positions of a task section.

        Args:
            task_id: Task identifier

        Returns:
            Tuple of (start_pos, end_pos) or None if not found
        """
        # Match task headers like "## Task T001:" or "### T001:"
        task_num = task_id.replace("T", "")
        patterns = [
            r'(#{2,3})\s*(?:Task\s+)?' + re.escape(task_id) + r'[:\s]',
            r'(#{2,3})\s*(?:Task\s+)?' + re.escape(task_num) + r'[:\s]',
        ]

        for pattern in patterns:
            match = re.search(pattern, self.content, re.IGNORECASE)
            if match:
                start = match.start()
                # Find end (next heading of same or higher level, or end of file)
                header_level = len(match.group(1))
                end_pattern = r'\n#{1,' + str(header_level) + r'}\s'
                end_match = re.search(end_pattern, self.content[match.end():])
                if end_match:
                    end = match.end() + end_match.start()
                else:
                    end = len(self.content)
                return (start, end)

        return None

    def _insert_status_marker(self, task_id: str, status: str) -> None:
        """Insert or update status marker for a task in the content."""
        marker = f"<!-- TASK_STATUS:{task_id}:{status} -->"
        existing_pattern = rf'<!-- TASK_STATUS:{re.escape(task_id)}:\w+ -->'

        # Check if marker already exists
        if re.search(existing_pattern, self.content):
            # Update existing marker
            self.content = re.sub(existing_pattern, marker, self.content)
        else:
            # Find task section and insert marker after the header
            section = self._find_task_section(task_id)
            if section:
                start, _ = section
                # Find end of header line
                newline_pos = self.content.find('\n', start)
                if newline_pos != -1:
                    self.content = (
                        self.content[:newline_pos + 1] +
                        marker + '\n' +
                        self.content[newline_pos + 1:]
                    )

    def _generate_status_section(self) -> str:
        """Generate the implementation status summary section."""
        lines = [
            IMPL_START_MARKER,
            "",
            "## Implementation Status",
            "",
            f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
        ]

        # Group by status
        by_status: Dict[str, List[str]] = {
            "completed": [],
            "in_progress": [],
            "pending": [],
            "failed": [],
        }

        for task_id, status in sorted(self.task_statuses.items()):
            if status in by_status:
                by_status[status].append(task_id)
            else:
                by_status.setdefault("other", []).append(task_id)

        # Completed tasks
        if by_status["completed"]:
            lines.append("### Completed")
            for task_id in by_status["completed"]:
                lines.append(f"- [x] {task_id}")
            lines.append("")

        # In progress
        if by_status["in_progress"]:
            lines.append("### In Progress")
            for task_id in by_status["in_progress"]:
                lines.append(f"- [ ] {task_id} *(in progress)*")
            lines.append("")

        # Pending
        if by_status["pending"]:
            lines.append("### Pending")
            for task_id in by_status["pending"]:
                lines.append(f"- [ ] {task_id}")
            lines.append("")

        # Failed
        if by_status["failed"]:
            lines.append("### Failed")
            for task_id in by_status["failed"]:
                lines.append(f"- [ ] {task_id} *(failed)*")
            lines.append("")

        # Summary
        total = len(self.task_statuses)
        completed = len(by_status["completed"])
        if total > 0:
            pct = (completed / total) * 100
            lines.append(f"**Progress: {completed}/{total} tasks ({pct:.0f}%)**")
            lines.append("")

        lines.append(IMPL_END_MARKER)

        return '\n'.join(lines)

    def _update_status_section(self) -> None:
        """Update or insert the implementation status section."""
        status_section = self._generate_status_section()

        # Check if section already exists
        start_idx = self.content.find(IMPL_START_MARKER)
        end_idx = self.content.find(IMPL_END_MARKER)

        if start_idx != -1 and end_idx != -1:
            # Replace existing section
            self.content = (
                self.content[:start_idx] +
                status_section +
                self.content[end_idx + len(IMPL_END_MARKER):]
            )
        else:
            # Append new section at the end
            self.content = self.content.rstrip() + "\n\n" + status_section + "\n"

    def apply_updates(self) -> None:
        """Apply all pending updates to the content."""
        # Insert individual task markers
        for task_id, status in self.task_statuses.items():
            self._insert_status_marker(task_id, status)

        # Update summary section
        self._update_status_section()

    def save(self) -> None:
        """Save updated content back to file."""
        self.plan_path.write_text(self.content, encoding="utf-8")

    def get_content(self) -> str:
        """Get the current content."""
        return self.content

    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get status of a specific task."""
        return self.task_statuses.get(task_id)

    def get_all_statuses(self) -> Dict[str, str]:
        """Get all task statuses."""
        return self.task_statuses.copy()


def update_plan_status(
    plan_path: Path,
    task_statuses: Dict[str, str],
    save: bool = True
) -> str:
    """
    Convenience function to update plan with task statuses.

    Args:
        plan_path: Path to the plan file
        task_statuses: Dictionary mapping task IDs to statuses
        save: Whether to save changes to file

    Returns:
        Updated plan content
    """
    updater = PlanUpdater(plan_path)

    for task_id, status in task_statuses.items():
        updater.update_task_status(task_id, status)

    updater.apply_updates()

    if save:
        updater.save()

    return updater.get_content()


def extract_task_list(plan_content: str) -> List[Dict[str, str]]:
    """
    Extract task list from plan content.

    Args:
        plan_content: Markdown content of the plan

    Returns:
        List of task dictionaries with id, title, and status
    """
    tasks = []

    # Match task headers
    task_pattern = r'(?:#{2,3})\s*(?:Task\s+)?([T]?\d+):?\s*(.+?)(?=\n)'
    matches = re.findall(task_pattern, plan_content, re.IGNORECASE)

    # Also get any status markers
    status_markers = dict(re.findall(TASK_STATUS_PATTERN, plan_content))

    for task_id, title in matches:
        normalized_id = f"T{task_id}" if not task_id.startswith('T') else task_id
        tasks.append({
            "id": normalized_id,
            "title": title.strip(),
            "status": status_markers.get(normalized_id, "pending"),
        })

    return tasks


def has_implementation_tasks(content: str) -> bool:
    """
    Check if plan content already has implementation tasks.

    Checks for:
    1. External tasks file reference (<!-- TASKS_FILE: path -->)
    2. Generated tasks section markers (GENERATED_TASKS_START) - legacy
    3. Existing task patterns (## Task N:, ### Step N:, etc.)

    Args:
        content: Plan markdown content

    Returns:
        True if tasks exist, False otherwise
    """
    # Check for external tasks file reference
    if re.search(TASKS_FILE_REFERENCE_PATTERN, content):
        return True

    # Check for generated tasks section (legacy embedded tasks)
    if GENERATED_TASKS_START in content:
        return True

    # Check for existing task patterns using same regex as TaskDecomposer
    task_pattern = r'(?:#{2,3})\s*(?:Step|Task)?\s*([T]?\d+):?\s*(.+?)(?=\n#{2,3}\s*(?:Step|Task)?\s*[T]?\d|\n## |\Z)'
    matches = re.findall(task_pattern, content, re.DOTALL | re.IGNORECASE)

    return len(matches) > 0


def get_tasks_file_path(content: str) -> Optional[str]:
    """
    Extract the tasks file path from plan content if present.

    Args:
        content: Plan markdown content

    Returns:
        Path to tasks file, or None if not found
    """
    match = re.search(TASKS_FILE_REFERENCE_PATTERN, content)
    if match:
        return match.group(1).strip()
    return None


def insert_tasks_file_reference(content: str, tasks_file: str) -> str:
    """
    Insert or update a reference to an external tasks file in plan content.

    Args:
        content: Original plan markdown content
        tasks_file: Relative path to the tasks file

    Returns:
        Updated plan content with tasks file reference
    """
    reference = TASKS_FILE_REFERENCE_TEMPLATE.format(tasks_file=tasks_file)
    reference_section = f"""
## Implementation Tasks

See [{tasks_file}]({tasks_file}) for the detailed task breakdown.

{reference}
"""

    # Check if reference already exists
    existing_match = re.search(TASKS_FILE_REFERENCE_PATTERN, content)
    if existing_match:
        # Replace existing reference section
        # Find the section boundaries (## Implementation Tasks ... <!-- TASKS_FILE -->)
        section_pattern = r'## Implementation Tasks\s*\n.*?' + TASKS_FILE_REFERENCE_PATTERN
        # A function replacement: a template string would read the path's
        # backslashes (a Windows spelling) as escapes and raise `bad escape`.
        replacement = reference_section.strip()
        content = re.sub(section_pattern, lambda _m: replacement, content, flags=re.DOTALL)
        return content

    # Check for legacy embedded tasks and remove them
    if GENERATED_TASKS_START in content:
        start_idx = content.find(GENERATED_TASKS_START)
        end_idx = content.find(GENERATED_TASKS_END)
        if start_idx != -1 and end_idx != -1:
            content = content[:start_idx] + content[end_idx + len(GENERATED_TASKS_END):]
            content = content.rstrip()

    # Append new reference section at the end
    return content.rstrip() + "\n" + reference_section


def insert_generated_tasks(content: str, tasks_markdown: str) -> str:
    """
    Insert or replace the generated tasks section in plan content.

    Uses HTML comment markers for idempotent updates.

    Args:
        content: Original plan markdown content
        tasks_markdown: Formatted markdown for tasks section

    Returns:
        Updated plan content with tasks section
    """
    tasks_section = f"{GENERATED_TASKS_START}\n{tasks_markdown}\n{GENERATED_TASKS_END}"

    # Check if section already exists
    start_idx = content.find(GENERATED_TASKS_START)
    end_idx = content.find(GENERATED_TASKS_END)

    if start_idx != -1 and end_idx != -1:
        # Replace existing section
        return (
            content[:start_idx] +
            tasks_section +
            content[end_idx + len(GENERATED_TASKS_END):]
        )
    else:
        # Append new section at the end
        return content.rstrip() + "\n\n" + tasks_section + "\n"


def get_implementation_summary_path(content: str) -> Optional[str]:
    """
    Extract the implementation summary file path from plan content if present.

    Args:
        content: Plan markdown content

    Returns:
        Path to implementation summary file, or None if not found
    """
    match = re.search(IMPL_SUMMARY_REFERENCE_PATTERN, content)
    if match:
        return match.group(1).strip()
    return None


def insert_implementation_summary_reference(content: str, summary_file: str) -> str:
    """
    Insert or update a reference to the implementation summary file in plan content.

    Args:
        content: Original plan markdown content
        summary_file: Relative path to the implementation summary file

    Returns:
        Updated plan content with implementation summary reference
    """
    reference = IMPL_SUMMARY_REFERENCE_TEMPLATE.format(summary_file=summary_file)
    reference_section = f"""
## Implementation Summary

See [{summary_file}]({summary_file}) for the implementation summary including files modified and any deviations from the plan.

{reference}
"""

    # Check if reference already exists
    existing_match = re.search(IMPL_SUMMARY_REFERENCE_PATTERN, content)
    if existing_match:
        # Replace existing reference section
        section_pattern = r'## Implementation Summary\s*\n.*?' + IMPL_SUMMARY_REFERENCE_PATTERN
        # Literal, as in insert_tasks_file_reference: `..\.multi-llm\p\...`
        # was `bad escape \p` (Windows CI, 2026-10-23).
        replacement = reference_section.strip()
        content = re.sub(section_pattern, lambda _m: replacement, content, flags=re.DOTALL)
        return content

    # Append new reference section at the end
    return content.rstrip() + "\n" + reference_section
