"""Task decomposition module for breaking plans into executable tasks."""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pathlib import Path

try:
    from .subagent_tasks import derive_executor_role, subagent_type_for_role
except ImportError:
    from utils.subagent_tasks import derive_executor_role, subagent_type_for_role


class TaskStatus(Enum):
    """Status of a task in the decomposition."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    """Represents a single task extracted from a plan."""
    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    depends_on: List[str] = field(default_factory=list)
    files_to_modify: List[str] = field(default_factory=list)
    files_to_create: List[str] = field(default_factory=list)
    estimated_complexity: str = "medium"  # low, medium, high
    # Host-neutral routing field (D2h). "human" means no invoker ever dispatches
    # this task — it is a manual step. Every reader branches on this;
    # `subagent_type` is optional Claude-only metadata derived from it.
    executor_role: str = "agent"
    subagent_type: str = "general-purpose"
    acceptance_criteria: List[str] = field(default_factory=list)
    batch_group: Optional[int] = None
    error_message: Optional[str] = None

    def __post_init__(self) -> None:
        """Keep ``executor_role`` and the legacy ``subagent_type`` in agreement.

        The task schema rejects a task whose ``subagent_type`` disagrees with its
        ``executor_role``, so the two can never drift while the legacy field
        lasts. ``human`` wins in either direction: it is the marker that no
        invoker may dispatch this task, and erring toward "do not dispatch" is
        the only safe reconciliation.
        """
        if self.subagent_type == "human" or self.executor_role == "human":
            self.executor_role = "human"
            self.subagent_type = "human"
        elif self.executor_role != "human":
            self.executor_role = "agent"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "depends_on": self.depends_on,
            "files_to_modify": self.files_to_modify,
            "files_to_create": self.files_to_create,
            "estimated_complexity": self.estimated_complexity,
            "executor_role": self.executor_role,
            "subagent_type": self.subagent_type,
            "acceptance_criteria": self.acceptance_criteria,
            "batch_group": self.batch_group,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create from dictionary."""
        # Normalize acceptance_criteria: must be a list of non-empty strings.
        # Reject the entire list if any entry is invalid (non-string or empty).
        raw_criteria = data.get("acceptance_criteria", [])
        if (
            isinstance(raw_criteria, list)
            and raw_criteria
            and all(isinstance(entry, str) and entry.strip() for entry in raw_criteria)
        ):
            acceptance_criteria = raw_criteria
        else:
            acceptance_criteria = []

        # executor_role is authoritative when present; otherwise it is derived
        # from the legacy subagent_type, so a task file written before the D2h
        # rename still routes its human tasks correctly on resume.
        executor_role = data.get("executor_role")
        if executor_role not in ("agent", "human"):
            executor_role = derive_executor_role(data.get("subagent_type"))

        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            status=TaskStatus(data.get("status", "pending")),
            depends_on=data.get("depends_on", []),
            files_to_modify=data.get("files_to_modify", []),
            files_to_create=data.get("files_to_create", []),
            estimated_complexity=data.get("estimated_complexity", "medium"),
            executor_role=executor_role,
            # A generated task carries an explicit null (the schema's
            # required-but-nullable spelling of "none"), which `.get`'s default
            # does not cover.
            subagent_type=(
                data.get("subagent_type")
                or subagent_type_for_role(executor_role)
            ),
            acceptance_criteria=acceptance_criteria,
            batch_group=data.get("batch_group"),
            error_message=data.get("error_message"),
        )


#: The rendered forms that mean "no invoker ever dispatches this task" (D2h).
#: ``update_plan_tasks.generate_tasks_markdown`` writes the first one for every
#: ``executor_role == "human"`` record, and ``tasks.md`` is the only thing
#: :meth:`TaskDecomposer.parse_plan` ever sees — a marker missed here turns a
#: manual step into a subagent dispatch and leaves the D6 rows 8/9 machinery
#: (``--force-strategy``, ``--human-task``, ``skip-dependents``) with an empty
#: human-task set to work on. The second and third forms are the executor line a
#: hand-written plan may carry and the pre-D2h ``subagent_type`` rendering that
#: files already on disk still use.
HUMAN_TASK_PATTERNS = (
    # **Type**: Manual (user action required)
    re.compile(
        r'(?:^|\n)\s*(?:[-*]\s+)?\*{0,2}type\*{0,2}\s*:\s*\*{0,2}manual\b',
        re.IGNORECASE,
    ),
    # **Executor**: human  /  **Executor role**: human
    re.compile(
        r'(?:^|\n)\s*(?:[-*]\s+)?\*{0,2}executor(?:\s+role)?\*{0,2}\s*:\s*'
        r'\*{0,2}human\b',
        re.IGNORECASE,
    ),
    # **Subagent**: human  /  **Subagent type**: human  (legacy renderings)
    re.compile(
        r'(?:^|\n)\s*(?:[-*]\s+)?\*{0,2}subagent(?:\s+type)?\*{0,2}\s*:\s*'
        r'\*{0,2}human\b',
        re.IGNORECASE,
    ),
)


_DEPENDENCY_LABEL = r"(?:dependenc(?:y|ies)|depends?\s+on)"

#: A task's dependency declaration: a whole metadata line, label and colon,
#: never a sentence. The label is bold — ``**Dependencies**: T001, T002``, the
#: line ``update_plan_tasks.generate_tasks_markdown`` renders for every task
#: (``None`` when it has none), and the ``**Depends on**:`` /
#: ``**Dependencies:**`` an edit batch may write — or plain —
#: ``- Depends on: T001``, the hand-written plan format the fixtures use —
#: either one optionally bulleted. ``**Requires**:`` / ``**After**:``, which
#: the old reader also took, appear in no template, renderer or fixture.
DEPENDENCIES_LINE = re.compile(
    r"^\s*(?:[-*]\s+)?"
    r"(?:\*{2}\s*" + _DEPENDENCY_LABEL + r"\s*(?::\s*\*{2}|\*{2}\s*:)"
    r"|" + _DEPENDENCY_LABEL + r"\s*:)"
    r"(?P<ids>[^\n]*)$",
    re.IGNORECASE | re.MULTILINE,
)


#: Where the ids on a dependency line end and prose begins: the first ``(``,
#: ``—``, ``;`` or ``:`` after the label. ``T001 (see Step 2)``, ``T001 — must
#: land before 3 PM`` and ``T003 at runtime (0 otherwise)`` each declared the
#: number in their prose as a task (adversarial review, 2026-10-02).
_DEPENDENCY_PROSE = re.compile(r"[(—;:]")
#: A line that declares no dependency at all, however it goes on: ``None``,
#: ``N/A``, ``-`` — ``None (T001 is optional)`` declared ``T001``.
_NO_DEPENDENCY = re.compile(r"^\s*(?:none|n/?a|-|—|–)(?![\w/])", re.IGNORECASE)
#: One id, or a range of ids (``T001-T003`` names every id in it).
_DEPENDENCY_ID = re.compile(r"\b(T?\d+)(?:\s*-\s*(T?\d+))?\b")
#: A bullet under an empty label line (``**Dependencies**:`` then ``- T001``).
_DEPENDENCY_BULLET = re.compile(r"^\s*[-*]\s+(?P<ids>.*)$")
#: The most ids one range may expand to; a wider one is a typo, not a graph.
_MAX_RANGE = 50


def _ids_in(chunk: str, *, bare_numbers: bool) -> List[str]:
    """The ids one dependency chunk (a line, or one bullet of a list) names."""
    if _NO_DEPENDENCY.match(chunk):
        return []
    ids_only = _DEPENDENCY_PROSE.split(chunk, maxsplit=1)[0]
    found: List[str] = []
    for start, end in _DEPENDENCY_ID.findall(ids_only):
        if not start.startswith("T") and not bare_numbers:
            continue
        if end and not end.startswith("T") and not bare_numbers:
            end = None
        digits_from, digits_to = start.lstrip("T"), (end or start).lstrip("T")
        low, high = int(digits_from), int(digits_to)
        if high < low or high - low >= _MAX_RANGE:
            high = low
        width = len(digits_from)
        for number in range(low, high + 1):
            found.append(f"T{number:0{width}d}")
    return found


def _bullets_after(text: str, position: int) -> List[str]:
    """The id-only bullets right under an empty label line, as chunks.

    Stops at the first line that is neither blank nor a bullet made of ids
    (``- Files to modify: a.py`` ends the list; ``- T002 (optional)`` is in
    it, its prose cut like a line's).
    """
    chunks: List[str] = []
    for line in text[position:].split("\n")[1:]:
        if not line.strip():
            if chunks:
                break
            continue
        bullet = _DEPENDENCY_BULLET.match(line)
        if bullet is None:
            break
        ids_only = _DEPENDENCY_PROSE.split(bullet.group("ids"), maxsplit=1)[0]
        if not re.fullmatch(r"\s*T?\d+(?:\s*-\s*T?\d+)?(?:\s*,\s*T?\d+(?:\s*-\s*T?\d+)?)*\s*,?\s*", ids_only):
            break
        chunks.append(bullet.group("ids"))
    return chunks


def declared_dependencies(text: str, *, bare_numbers: bool = False) -> List[str]:
    """The task ids a task's dependency lines declare, in order, no repeats.

    The one dependency reader: ``implement`` (``TaskDecomposer.parse_plan``)
    and ``util check-tasks`` both call it, so they cannot disagree. Only
    :data:`DEPENDENCIES_LINE` counts. The reader it replaced also matched
    "after", "requires" and "depends on" anywhere in the narrative, so
    "ticks after 3 frames" declared ``T3`` and "run it after T002 has warmed
    the cache" an edge to ``T002`` that implement batches by and
    ``skip-dependents`` walks (three-host racing run, 2026-10-01).

    On the line, the ids end at the first ``(``, ``—``, ``;`` or ``:``
    (:data:`_DEPENDENCY_PROSE`), a leading ``None``/``N/A``/``-`` declares
    none whatever follows it, ``T001-T003`` is every id in the range, and a
    label with nothing after it reads the id-only bullets right under it. A
    bare ``1`` is an id only when ``bare_numbers`` says the document's own
    ids are bare (a ``### Step 1`` plan, whose ``T1`` is how ``parse_plan``
    names that step); in a ``T001``-numbered document it is prose — ``T001,
    2 passes`` used to declare ``T2``.
    """
    deps: List[str] = []
    for line in DEPENDENCIES_LINE.finditer(text):
        rest = line.group("ids")
        chunks = [rest] if rest.strip() else _bullets_after(text, line.end())
        for chunk in chunks:
            for normalized in _ids_in(chunk, bare_numbers=bare_numbers):
                if normalized not in deps:
                    deps.append(normalized)
    return deps


class TaskDecomposer:
    """Decomposes plans into executable tasks with dependency management."""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.execution_order: List[str] = []

    def parse_plan(self, plan_content: str) -> List[Task]:
        """
        Parse a plan document and extract tasks.

        Args:
            plan_content: Markdown content of the plan

        Returns:
            List of Task objects
        """
        tasks = []

        # Look for task sections with various formats:
        # - "### Step 1: Title" or "## Step 1: Title"
        # - "### Task 1: Title" or "## Task 1: Title"
        # - "### T1: Title" or "## 1: Title"
        task_pattern = r'(?:#{2,3})\s*(?:Step|Task)?\s*([T]?\d+):?\s*(.+?)(?=\n#{2,3}\s*(?:Step|Task)?\s*[T]?\d|\n## |\Z)'
        matches = re.findall(task_pattern, plan_content, re.DOTALL | re.IGNORECASE)
        # A bare number names a task only in a document whose own ids are
        # bare (`### Step 1`); in a `T001`-numbered one it is prose.
        bare_numbers = any(
            not raw.strip().upper().startswith("T") for raw, _ in matches
        )

        for task_id, content in matches:
            task_id = task_id.strip()
            lines = content.strip().split('\n')
            title = lines[0].strip() if lines else f"Task {task_id}"
            description = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""

            # Normalize task ID
            normalized_id = f"T{task_id}" if not task_id.startswith('T') else task_id

            # Handle duplicate IDs by appending a suffix
            if normalized_id in self.tasks:
                suffix = 1
                while f"{normalized_id}_{suffix}" in self.tasks:
                    suffix += 1
                normalized_id = f"{normalized_id}_{suffix}"

            # Extract acceptance criteria before stripping metadata
            acceptance_criteria = self._extract_acceptance_criteria(description)

            # Extract structured metadata before stripping
            depends_on = self._extract_dependencies(
                description, bare_numbers=bare_numbers
            )
            files_to_modify = self._extract_files(description, "modify")
            files_to_create = self._extract_files(description, "create")
            estimated_complexity = self._extract_complexity(description)
            executor_role = self._extract_executor_role(description)

            # Strip metadata sections to keep only narrative content
            clean_description = self._strip_metadata_sections(description)

            task = Task(
                id=normalized_id,
                title=title,
                description=clean_description,
                depends_on=depends_on,
                files_to_modify=files_to_modify,
                files_to_create=files_to_create,
                estimated_complexity=estimated_complexity,
                acceptance_criteria=acceptance_criteria,
                # Recovered from the rendered manual marker; everything else is
                # an "agent" task any invoker may dispatch.
                executor_role=executor_role,
            )
            tasks.append(task)
            self.tasks[task.id] = task

        self._compute_execution_order()
        return tasks

    def parse_from_json(self, json_data: List[Dict[str, Any]]) -> List[Task]:
        """
        Parse tasks from JSON format (e.g., from LLM output).

        Args:
            json_data: List of task dictionaries

        Returns:
            List of Task objects
        """
        tasks = []
        for data in json_data:
            task = Task.from_dict(data)
            tasks.append(task)
            self.tasks[task.id] = task

        self._compute_execution_order()
        return tasks

    def _extract_dependencies(
        self, description: str, *, bare_numbers: bool = False
    ) -> List[str]:
        """The task's declared dependencies: :func:`declared_dependencies`."""
        return declared_dependencies(description, bare_numbers=bare_numbers)

    #: The metadata lines ``plan_updater`` renders for every generated task.
    _FILES_LINE = re.compile(
        r'^\s*(?:\*{2}\s*files?\s+to\s+(modify|create)\s*\*{2}'
        r'|[-*]\s+files?\s+to\s+(modify|create))\s*:\s*(?P<paths>[^\n]*)$',
        re.IGNORECASE | re.MULTILINE,
    )

    def _explicit_files(self, description: str) -> Optional[Dict[str, List[str]]]:
        """The ``**Files to modify**:`` / ``**Files to create**:`` lines, when
        the task carries any — ``None`` when it carries neither.

        These lines are what ``plan_updater`` writes for every generated task,
        so when they are present they are the declared file set and the
        keyword heuristic below must not add to them: measured 2026-09-16, a
        task whose narrative mapped plan sections to ``CONFIG.boost``,
        ``Camera.update`` and ``HUD.update`` had every one of those dotted
        identifiers declared as a file to *create*, so the executor
        snapshotted, swept and reported on four files that do not exist.
        """
        found: Dict[str, List[str]] = {}
        for match in self._FILES_LINE.finditer(description):
            action = (match.group(1) or match.group(2) or "").lower()
            paths: List[str] = found.setdefault(action, [])
            for raw in match.group("paths").split(","):
                item = raw.strip().strip("`\"'").strip()
                if not item or item.lower().strip("()") in ("none", "n/a", "-", "—"):
                    continue
                if item not in paths:
                    paths.append(item)
        return found or None

    def _extract_files(self, description: str, action: str) -> List[str]:
        """Extract file paths from description based on action type.

        An explicit metadata line wins outright; the keyword heuristic is only
        for a hand-written task that has none.
        """
        explicit = self._explicit_files(description)
        if explicit is not None:
            return list(explicit.get(action, []))

        files = []

        # Look for file paths
        path_pattern = r'[`"]?([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)[`"]?'
        all_paths = re.findall(path_pattern, description)

        # Filter by action keywords near the path
        for path in all_paths:
            context_start = max(0, description.find(path) - 50)
            context = description[context_start:description.find(path) + len(path) + 50].lower()

            if action == "create" and any(w in context for w in ["create", "new", "add", "write"]):
                if path not in files:
                    files.append(path)
            elif action == "modify" and any(w in context for w in ["modify", "update", "edit", "change"]):
                if path not in files:
                    files.append(path)

        return files

    #: The ``**Complexity**`` line ``update_plan_tasks`` renders for every
    #: generated task, in the same two spellings ``_FILES_LINE`` accepts.
    _COMPLEXITY_LINE = re.compile(
        r'^\s*(?:\*{2}\s*complexity\s*\*{2}|[-*]\s+complexity)\s*:\s*'
        r'\**\s*(?P<level>low|medium|high)\b',
        re.IGNORECASE | re.MULTILINE,
    )

    def _explicit_complexity(self, description: str) -> Optional[str]:
        """The declared ``**Complexity**:`` level, or ``None`` when absent.

        Same rule as ``_explicit_files``: the renderer writes this line for
        every generated task, so when it is there it is the answer and the
        keyword heuristic must not overrule it. It was the only field of the
        JSON → markdown → JSON round-trip that did not survive — measured
        2026-09-16, all 14 tasks of a rendered ``tasks.md`` (declared low and
        medium, and coloured by that in the file's own mermaid graph) parsed
        back as ``high``, because their descriptions say "integration" and
        "architecture".
        """
        match = self._COMPLEXITY_LINE.search(description)
        return match.group("level").lower() if match else None

    def _extract_complexity(self, description: str) -> str:
        """The declared complexity, else the heuristic's guess at the narrative.

        The fallback reads the *stripped* description because the metadata
        labels are not the task's content: the word "Complexity" contains
        "complex", the heuristic's first high indicator, so any task carrying
        the line at all scored `high` on the strength of the label. A
        hand-written task with no metadata strips to itself, so its guess is
        unchanged.
        """
        return self._explicit_complexity(description) or self._estimate_complexity(
            self._strip_metadata_sections(description)
        )

    def _estimate_complexity(self, description: str) -> str:
        """Estimate task complexity based on description.

        The fallback for a hand-written task carrying no ``**Complexity**``
        line; ``_extract_complexity`` prefers the declared value.
        """
        desc_lower = description.lower()

        high_indicators = ["complex", "refactor", "architecture", "multiple files", "integration"]
        low_indicators = ["simple", "minor", "typo", "rename", "comment"]

        for indicator in high_indicators:
            if indicator in desc_lower:
                return "high"

        for indicator in low_indicators:
            if indicator in desc_lower:
                return "low"

        return "medium"

    def _extract_executor_role(self, description: str) -> str:
        """Recover a rendered task's executor role from its markdown (D2h).

        ``tasks.md`` is the round trip: ``update_plan_tasks`` renders a human
        task as ``**Type**: Manual (user action required)`` and this is the only
        path that reads it back, so the marker has to survive the round trip or
        the manual step is dispatched to a subagent like any other.

        Args:
            description: Raw task description markdown, before metadata sections
                are stripped.

        Returns:
            ``"human"`` when a manual marker is present, ``"agent"`` otherwise.
        """
        for pattern in HUMAN_TASK_PATTERNS:
            if pattern.search(description):
                return "human"
        return "agent"

    def _extract_acceptance_criteria(self, description: str) -> List[str]:
        """Extract acceptance criteria items from a task description.

        Looks for an **Acceptance Criteria** section (case-insensitive, with or
        without colon) and extracts bullet items (- item, - [ ] item) and
        numbered items (1. item).

        Args:
            description: Raw task description markdown

        Returns:
            List of acceptance criteria strings, empty if no section found.
        """
        # Match an Acceptance Criteria heading: **Acceptance Criteria**: or **Acceptance Criteria**
        # Case-insensitive, optional colon, optional bold markers
        heading_pattern = r'(?:^|\n)\s*\*{0,2}acceptance\s+criteria\*{0,2}\s*:?\s*\n'
        match = re.search(heading_pattern, description, re.IGNORECASE)
        if not match:
            return []

        # Extract the content after the heading until the next metadata section
        # heading or end of string
        rest = description[match.end():]
        # Stop at the next bold metadata heading or end of string
        next_section = re.search(r'\n\s*\*{2}[A-Za-z]', rest)
        if next_section:
            rest = rest[:next_section.start()]

        criteria = []
        for line in rest.split('\n'):
            stripped = line.strip()
            if not stripped:
                continue

            # Match bullet items: - [ ] item, - [x] item, - item, * item
            bullet_match = re.match(r'^[-*]\s+(?:\[.\]\s+)?(.+)$', stripped)
            if bullet_match:
                item = bullet_match.group(1).strip()
                if item:
                    criteria.append(item)
                continue

            # Match numbered items: 1. item, 1) item
            numbered_match = re.match(r'^\d+[.)]\s+(.+)$', stripped)
            if numbered_match:
                item = numbered_match.group(1).strip()
                if item:
                    criteria.append(item)
                continue

        return criteria

    def _strip_metadata_sections(self, description: str) -> str:
        """Remove known metadata sections from a task description.

        Strips sections that start with **Section Name**: (or similar) on their
        own line, preserving only narrative text. Removed sections:
        - Files to modify
        - Files to create
        - Dependencies
        - Complexity
        - Subagent
        - Executor
        - Acceptance Criteria

        ``**Executor**: {role}`` is what ``update_plan_tasks.py`` renders for every
        non-human task (the D2h `subagent_type` -> `executor_role` rename was not
        carried into this stripper), so every generated task's description used to
        begin with that literal line. Cosmetic in the Task section a subagent reads
        directly, but load-bearing in ``implement_orchestrator._build_dependency_section``,
        which renders "title + first line of description" as a later task's *only*
        inter-task context — so every dependency summary read `**Executor**: agent`
        instead of the predecessor's actual work (F6, 2026-09-16). The role itself is
        read off the *raw* description by :meth:`_extract_executor_role` before this
        method ever runs, so stripping the line here cannot affect routing.

        Args:
            description: Raw task description markdown

        Returns:
            Description with metadata sections removed and whitespace cleaned up.
        """
        section_names = [
            r'files?\s+to\s+modify',
            r'files?\s+to\s+create',
            r'dependenc(?:y|ies)',
            r'depends?\s+on',
            r'complexity',
            r'subagent(?:\s+type)?',
            r'executor(?:\s+role)?',
            r'acceptance\s+criteria',
        ]

        result = description
        for name in section_names:
            # Match the section heading and everything until the next bold
            # heading or end of string. The heading can be:
            # **Section Name**: content  (single line)
            # **Section Name**:\n- item\n- item  (multi-line with list items)
            # - Section Name: content (as a list item)
            pattern = (
                r'(?:(?<=\n)|(?:^))\s*'             # line start (zero-width)
                r'(?:\*{2}' + name + r'\*{2}'       # **Section Name**
                r'|[-*]\s+' + name + r')'           # or - Section Name
                r'\s*:?\s*'                         # optional colon
                r'[^\n]*'                           # rest of heading line
                r'(?:\n(?!\s*\n)(?!\s*\*{2}[A-Za-z])(?!\s*#{2,})[^\n]*)*'  # continuation lines
            )
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)

        # Clean up excessive blank lines left by removals
        result = re.sub(r'\n{3,}', '\n\n', result)
        return result.strip()

    def _compute_execution_order(self) -> None:
        """Compute topological order for task execution."""
        # Kahn's algorithm for topological sort
        in_degree = {tid: 0 for tid in self.tasks}
        adj = {tid: [] for tid in self.tasks}

        for tid, task in self.tasks.items():
            for dep in task.depends_on:
                if dep in self.tasks:
                    adj[dep].append(tid)
                    in_degree[tid] += 1

        queue = [tid for tid, degree in in_degree.items() if degree == 0]
        self.execution_order = []

        while queue:
            # Sort queue to ensure deterministic order
            queue.sort()
            tid = queue.pop(0)
            self.execution_order.append(tid)

            for neighbor in adj[tid]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Handle cycles (tasks not in execution_order)
        remaining = [tid for tid in self.tasks if tid not in self.execution_order]
        self.execution_order.extend(sorted(remaining))

    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute (no pending dependencies)."""
        ready = []
        completed_ids = {
            tid for tid, task in self.tasks.items()
            if task.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED)
        }

        for tid in self.execution_order:
            task = self.tasks[tid]
            if task.status != TaskStatus.PENDING:
                continue

            deps_satisfied = all(dep in completed_ids for dep in task.depends_on if dep in self.tasks)
            if deps_satisfied:
                ready.append(task)

        return ready

    def get_parallel_batches(self) -> List[List[Task]]:
        """
        Organize tasks into batches that can run in parallel.

        Uses a two-phase approach per iteration:
        1. Find all dependency-satisfied candidates
        2. Greedily assign candidates to the batch, skipping any whose
           files_to_modify + files_to_create overlap with already-batched tasks.
           Deferred candidates stay in remaining for a later batch.

        Tasks with empty file lists have no overlap and are always parallelizable.

        Returns:
            List of task batches, each batch can run in parallel
        """
        batches = []
        completed_ids: Set[str] = set()
        remaining = set(self.tasks.keys())

        batch_num = 0
        while remaining:
            # Phase 1: collect all dependency-satisfied candidates
            candidates = []
            for tid in sorted(remaining):
                task = self.tasks[tid]
                deps_satisfied = all(
                    dep in completed_ids
                    for dep in task.depends_on
                    if dep in self.tasks
                )
                if deps_satisfied:
                    candidates.append(task)

            if not candidates:
                # Remaining tasks have unsatisfied dependencies (cycle or missing)
                batch = []
                for tid in remaining:
                    task = self.tasks[tid]
                    task.batch_group = batch_num
                    batch.append(task)
                batches.append(batch)
                break

            # Phase 2: greedily assign candidates, checking file overlap
            batch = []
            batch_files: Set[str] = set()
            for task in candidates:
                task_files = set(task.files_to_modify + task.files_to_create)
                if task_files and task_files & batch_files:
                    # Overlapping files — defer to a later batch
                    continue
                task.batch_group = batch_num
                batch.append(task)
                batch_files.update(task_files)

            batches.append(batch)
            for task in batch:
                completed_ids.add(task.id)
                remaining.discard(task.id)
            batch_num += 1

        return batches

    def update_task_status(self, task_id: str, status: TaskStatus, error: Optional[str] = None) -> None:
        """Update the status of a task."""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            if error:
                self.tasks[task_id].error_message = error

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def to_json(self) -> str:
        """Export all tasks to JSON."""
        return json.dumps([task.to_dict() for task in self.tasks.values()], indent=2)

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get a summary of task progress."""
        status_counts = {status.value: 0 for status in TaskStatus}
        for task in self.tasks.values():
            status_counts[task.status.value] += 1

        return {
            "total": len(self.tasks),
            "by_status": status_counts,
            "completion_rate": status_counts["completed"] / len(self.tasks) if self.tasks else 0,
        }


#: The id shape every generated task carries. Pinned by
#: ``schemas/generated_tasks.schema.json`` too; restated here because the
#: uniqueness rule below is meaningless without it and this module is the one that
#: owns the *semantics* of a task graph.
TASK_ID_PATTERN = re.compile(r"^T[0-9]{3}$")


def validate_generated_tasks(tasks: List[Dict[str, Any]]) -> List[str]:
    """The semantic rules a generated task list must satisfy, or why it does not.

    JSON Schema pins the *shape* of ``task_generation_result.json``; these are the
    four rules the *graph* has to satisfy for anything downstream to mean
    anything, and they live here because this module owns task graphs (batching,
    ready-set computation, dependency walks):

    1. ids are unique and ``T###``;
    2. every ``depends_on`` entry names an id declared in this same document;
    3. the graph is acyclic — otherwise :meth:`TaskDecomposer.get_parallel_batches`
       silently emits a final batch whose dependencies were never satisfied;
    4. at least one task has an empty ``depends_on``, or nothing is ever ready to
       start.

    Run immediately after schema validation and before a byte reaches the plan: a
    document failing either check is a ``schema_invalid`` failure (D3k rung 6) that
    is never retried.

    Args:
        tasks: The ``tasks`` array of a task-generation document.

    Returns:
        Human-readable problems, empty when the list is valid.
    """
    problems: List[str] = []
    if not isinstance(tasks, list) or not tasks:
        return ["`tasks` must be a non-empty array"]

    ids: List[str] = []
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            problems.append(f"tasks[{index}]: expected an object")
            continue
        task_id = task.get("id")
        if not isinstance(task_id, str) or not TASK_ID_PATTERN.match(task_id):
            problems.append(
                f"tasks[{index}]: id {task_id!r} is not a zero-padded T### id"
            )
            continue
        ids.append(task_id)
    if problems:
        return problems

    # `subagent_type` is optional Claude-only metadata (null = none), but when a
    # reply does name one it must agree with `executor_role`. The schema used to
    # say so with an allOf/if/then; OpenAI's strict structured-output subset
    # does not list those keywords, so the rule moved here.
    for task in tasks:
        legacy = task.get("subagent_type")
        role = task.get("executor_role")
        if legacy is not None and role in ("agent", "human"):
            if legacy != subagent_type_for_role(role):
                problems.append(
                    f"{task.get('id')}: subagent_type {legacy!r} disagrees with "
                    f"executor_role {role!r}"
                )
    if problems:
        return problems

    seen: Set[str] = set()
    duplicates: Set[str] = set()
    for task_id in ids:
        if task_id in seen:
            duplicates.add(task_id)
        seen.add(task_id)
    if duplicates:
        problems.append(f"duplicate task id(s): {', '.join(sorted(duplicates))}")

    declared = set(ids)
    edges: Dict[str, List[str]] = {}
    for task in tasks:
        task_id = str(task.get("id"))
        depends_on = task.get("depends_on") or []
        if not isinstance(depends_on, list):
            problems.append(f"{task_id}: depends_on must be an array")
            continue
        unknown = [dep for dep in depends_on if dep not in declared]
        if unknown:
            problems.append(
                f"{task_id}: depends_on names id(s) this document never declares: "
                f"{', '.join(str(dep) for dep in unknown)}"
            )
        self_edge = [dep for dep in depends_on if dep == task_id]
        if self_edge:
            problems.append(f"{task_id}: depends on itself")
        edges[task_id] = [dep for dep in depends_on if dep in declared]

    if problems:
        return problems

    if not any(not edges.get(tid) for tid in ids):
        problems.append(
            "no task has an empty depends_on, so no task is ever ready to start"
        )

    # Kahn's algorithm over the declared edges: what is left when no node has an
    # in-degree of zero is exactly the cycle.
    in_degree = {tid: len(edges.get(tid, [])) for tid in ids}
    dependents: Dict[str, List[str]] = {tid: [] for tid in ids}
    for tid, deps in edges.items():
        for dep in deps:
            dependents[dep].append(tid)
    queue = sorted(tid for tid, degree in in_degree.items() if degree == 0)
    ordered = 0
    while queue:
        tid = queue.pop(0)
        ordered += 1
        for dependent in dependents[tid]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
        queue.sort()
    if ordered != len(ids):
        cyclic = sorted(tid for tid in ids if in_degree[tid] > 0)
        problems.append(
            "depends_on forms a cycle involving: " + ", ".join(cyclic)
        )
    return problems


def decompose_plan_file(plan_path: Path) -> TaskDecomposer:
    """
    Convenience function to decompose a plan file.

    Args:
        plan_path: Path to the plan markdown file

    Returns:
        TaskDecomposer instance with parsed tasks
    """
    decomposer = TaskDecomposer()
    plan_content = plan_path.read_text(encoding="utf-8")
    decomposer.parse_plan(plan_content)
    return decomposer
