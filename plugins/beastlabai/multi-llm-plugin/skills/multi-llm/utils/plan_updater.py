"""Plan updater module for marking implementation status in plans."""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .tasks_marker import (
    TASKS_FILE_MARKER_PATTERN,
    markdown_code_ranges,
    tasks_marker,
    tasks_marker_spans,
)


# HTML comment markers for idempotent updates
IMPL_START_MARKER = "<!-- IMPLEMENTATION_STATUS_START -->"
IMPL_END_MARKER = "<!-- IMPLEMENTATION_STATUS_END -->"
TASK_STATUS_PATTERN = r'<!-- TASK_STATUS:(\w+):(\w+) -->'

# Markers for generated tasks section (legacy - tasks embedded in plan)
GENERATED_TASKS_START = "<!-- GENERATED_TASKS_START -->"
GENERATED_TASKS_END = "<!-- GENERATED_TASKS_END -->"

# Marker for external tasks file reference (new - tasks in separate file).
# The pattern is `tasks_marker`'s, the one every phase reads the marker with.
TASKS_FILE_REFERENCE_PATTERN = TASKS_FILE_MARKER_PATTERN
TASKS_FILE_REFERENCE_TEMPLATE = "<!-- TASKS_FILE: {tasks_file} -->"

# Marker for implementation summary file reference. The pattern is the
# marker's grammar; the readers below match it with `_ImplSummaryMarkers`
# rather than `re`, because the regex is cubic on whitespace.
IMPL_SUMMARY_REFERENCE_PATTERN = r'<!-- IMPL_SUMMARY:\s*(.+?)\s*-->'
IMPL_SUMMARY_REFERENCE_TEMPLATE = "<!-- IMPL_SUMMARY: {summary_file} -->"
_IMPL_SUMMARY_OPEN = "<!-- IMPL_SUMMARY:"
_IMPL_SUMMARY_HEADING = "## Implementation Summary"
_WHITESPACE = re.compile(r"\s*")


class _NextOccurrence:
    """``text.find(needle, start)``, remembered: for starts that only grow,
    each stretch of the text is searched once."""

    def __init__(self, text: str, needle: str):
        self._text, self._needle = text, needle
        self._from, self._at = -1, -1

    def __call__(self, start: int) -> int:
        if self._from < 0 or start < self._from or 0 <= self._at < start:
            self._from, self._at = start, self._text.find(self._needle, start)
        return self._at


class _ImplSummaryMarkers:
    """Matches of :data:`IMPL_SUMMARY_REFERENCE_PATTERN` in one text, in O(n).

    The regex is cubic (97 s for 8 KB of spaces after the colon): its
    ``\\s*``, its lazy group and its closing ``\\s*`` share one whitespace run
    every possible way before the match fails. Its result is simpler than its
    search. After the opening ``\\s*`` takes the whole run, the group starts at
    the first non-blank character and ends where the whitespace before the
    first ``-->`` after that character begins, unless the group would then
    cross a newline (``.``), in which case no match starts at this marker,
    with one exception the backtracking finds: a marker whose run is followed
    directly by ``-->`` still matches with the run's last non-newline
    character as the group. Under ``re.DOTALL`` there is no newline rule.
    Positions only grow, so each search here reads each character once.
    """

    def __init__(self, text: str):
        self.text = text
        self._close = _NextOccurrence(text, "-->")
        self._newline = _NextOccurrence(text, "\n")
        self._blank_before: Dict[int, int] = {}

    def _blank_run_start(self, at: int) -> int:
        """Where the whitespace run that ends at *at* starts."""
        if at not in self._blank_before:
            start = at
            while start > 0 and self.text[start - 1].isspace():
                start -= 1
            self._blank_before[at] = start
        return self._blank_before[at]

    def at(self, start: int, dotall: bool = False) -> Optional[Tuple[int, int, int]]:
        """``(end, group start, group end)`` of the match at *start*, where the
        text has the opening marker, or None."""
        text = self.text
        opened = start + len(_IMPL_SUMMARY_OPEN)
        first = _WHITESPACE.match(text, opened).end()
        if first < len(text):
            close = self._close(first + 1)
            if close >= 0:
                # `first` is not blank, so this run starts after it.
                group_end = self._blank_run_start(close)
                newline = self._newline(first)
                if dotall or newline < 0 or newline >= group_end:
                    return close + 3, first, group_end
        if first > opened and text.startswith("-->", first):
            last = first - 1
            while not dotall and last >= opened and text[last] == "\n":
                last -= 1
            if last >= opened:
                return first + 3, last, last + 1
        return None

    def search(self) -> Optional[Tuple[int, int, int, int]]:
        """``(start, end, group start, group end)`` of
        ``re.search(IMPL_SUMMARY_REFERENCE_PATTERN, text)``, or None."""
        start = self.text.find(_IMPL_SUMMARY_OPEN)
        while start >= 0:
            found = self.at(start)
            if found:
                return (start,) + found
            start = self.text.find(_IMPL_SUMMARY_OPEN, start + 1)
        return None

    def sections(self) -> List[Tuple[int, int]]:
        """The spans ``re.sub`` replaces for
        ``'## Implementation Summary\\s*\\n.*?' + IMPL_SUMMARY_REFERENCE_PATTERN``
        under ``re.DOTALL``: a heading whose following whitespace holds a
        newline, through the first marker after that run's last newline.
        When that marker has no match, no later one has (nothing closes
        after it), so the scan ends there."""
        text = self.text
        spans: List[Tuple[int, int]] = []
        markers = _NextOccurrence(text, _IMPL_SUMMARY_OPEN)
        position = 0
        while True:
            heading = text.find(_IMPL_SUMMARY_HEADING, position)
            if heading < 0:
                return spans
            after = heading + len(_IMPL_SUMMARY_HEADING)
            newline = text.rfind("\n", after, _WHITESPACE.match(text, after).end())
            if newline < 0:
                position = heading + 1
                continue
            marker = markers(newline + 1)
            found = self.at(marker, dotall=True) if marker >= 0 else None
            if found is None:
                return spans
            spans.append((heading, found[0]))
            position = found[0]


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


def get_tasks_file_path(content: str) -> Optional[str]:
    """
    Extract the tasks file path from plan content if present.

    Args:
        content: Plan markdown content

    Returns:
        Path to tasks file as written, or None if not found. A caller that
        reads the task list uses ``tasks_file.read_task_list``, which also
        keeps the path inside the plan's directory.
    """
    return tasks_marker(content)


_REFERENCE_SECTION_HEADING = "## Implementation Tasks"
_HEADING_LINE_RE = re.compile(r"^#{1,6}[ \t].*$", re.MULTILINE)


def _reference_section_start(content: str, marker_start: int, code) -> Optional[int]:
    """Where the ``## Implementation Tasks`` section holding a marker starts.

    ``None`` unless the nearest heading before *marker_start* that is not
    inside code (*code*, ``tasks_marker.markdown_code_ranges``) is that heading.
    """
    nearest = None
    for heading in _HEADING_LINE_RE.finditer(content, 0, marker_start):
        if not any(start <= heading.start() < end for start, end in code):
            nearest = heading
    if nearest is not None and nearest.group(0).rstrip() == _REFERENCE_SECTION_HEADING:
        return nearest.start()
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

    # Every marker that counts (`tasks_marker.tasks_marker_spans`: not one quoted
    # as code) now names the new list, so none is left for implement to refuse
    # or follow: the marker of this function's own section is rewritten with
    # its heading and link, any other in place. Spliced, not `re.sub`: a
    # template would read a Windows path's backslashes as escapes.
    spans = tasks_marker_spans(content)
    if spans:
        code = markdown_code_ranges(content)
        for start, end, _raw in reversed(spans):
            heading = _reference_section_start(content, start, code)
            if heading is None:
                content = content[:start] + reference + content[end:]
            else:
                content = content[:heading] + reference_section.strip() + content[end:]
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
    markers = _ImplSummaryMarkers(content)
    if markers.search():
        # Replace each existing reference section: the matches of
        # `## Implementation Summary\s*\n.*?` + IMPL_SUMMARY_REFERENCE_PATTERN
        # under re.DOTALL. Spliced literally, as in insert_tasks_file_reference:
        # `..\.multi-llm\p\...` was `bad escape \p` (Windows CI, 2026-10-23).
        replacement = reference_section.strip()
        pieces: List[str] = []
        position = 0
        for start, end in markers.sections():
            pieces.extend((content[position:start], replacement))
            position = end
        pieces.append(content[position:])
        return "".join(pieces)

    # Append new reference section at the end
    return content.rstrip() + "\n" + reference_section
