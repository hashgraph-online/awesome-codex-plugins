"""
Suggestion batcher module for grouping suggestions into efficient subagent batches.

This module takes validated suggestions and groups them intelligently for processing
by fewer subagents, reducing API calls while maintaining edit safety.

Grouping Heuristics:
1. Reference/Section Proximity - Group suggestions targeting the same section
2. Type Compatibility - Don't mix deletions with other types
3. Batch Size Limits - Prevent context rot with max suggestions per batch
4. Dependency Ordering - Process deletions first, then modifications, then additions
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from . import importance as _importance
from .prior_changes import entry_id, stable_key


# Configuration constants
MAX_SUGGESTIONS_PER_BATCH = 4  # Hard limit to prevent context overload
MAX_DESCRIPTION_CHARS = 2500  # Total description length limit per batch
FILE_PATTERN = re.compile(
    r'(?:File|Path|Location):\s*([^\s,]+)',
    re.IGNORECASE
)


def suggestion_member_ids(suggestions: List[Dict[str, Any]]) -> List[str]:
    """The batch's suggestions as stable member ids, in order.

    Serves both suggestion phases (apply-suggestions and apply-task-suggestions
    batch with this same class), and is the list
    ``utils/write_phase_bridge`` carries as ``expected_ids`` and digests into
    :func:`utils.prior_changes.entry_id`.

    A suggestion carrying none of ``group_id``/``id``/``title`` falls back to its
    position within its own batch — see the same note on
    ``code_fix_batcher.fix_member_ids``.
    """
    return [
        stable_key(
            [s.get("group_id"), s.get("id"), s.get("title")], f"s{n}"
        )
        for n, s in enumerate(suggestions)
    ]


@dataclass
class SuggestionBatch:
    """A batch of suggestions to be processed by a single subagent."""

    suggestions: List[Dict[str, Any]] = field(default_factory=list)
    section_key: str = ""
    batch_type: str = "mixed"  # "deletion", "addition", "modification", "mixed"
    total_chars: int = 0

    @property
    def size(self) -> int:
        return len(self.suggestions)

    @property
    def is_full(self) -> bool:
        return self.size >= MAX_SUGGESTIONS_PER_BATCH

    @property
    def priority_score(self) -> float:
        """Calculate batch priority based on contained suggestions."""
        return float(sum(_importance.weight(s.get("importance")) for s in self.suggestions))

    def can_add(self, suggestion: Dict[str, Any]) -> bool:
        """Check if a suggestion can be added to this batch."""
        if not isinstance(suggestion, dict):
            return False

        if self.is_full:
            return False

        desc_len = len(suggestion.get("description", ""))
        if self.total_chars + desc_len > MAX_DESCRIPTION_CHARS:
            return False

        return True

    def add(self, suggestion: Dict[str, Any]) -> None:
        """Add a suggestion to this batch."""
        self.suggestions.append(suggestion)
        self.total_chars += len(suggestion.get("description", ""))

        # Update batch type
        types = set(s.get("type", "modification") for s in self.suggestions)
        if len(types) == 1:
            self.batch_type = types.pop()
        else:
            self.batch_type = "mixed"

    @property
    def prior_changes_id(self) -> str:
        """The stable, per-batch ``--id`` for the prior-changes append.

        NOT ``section_key``: a section that overflows the batch size or the char
        cap starts a NEW batch under the SAME key, and ``prior_changes.append``
        keeps one entry per ``(id, phase)`` (the newest, since fix round 14) — so
        a section-keyed id keeps only the last batch of that section and silently
        drops the rest. Computed here so a
        native invoker reads it off the serialized batch instead of picking a key,
        and byte-identical to what ``utils/write_phase_bridge`` derives for the
        same batch.
        """
        return entry_id(
            self.section_key, suggestion_member_ids(self.suggestions),
            fallback="batch",
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert batch to dictionary for JSON serialization."""
        return {
            "suggestions": self.suggestions,
            "section_key": self.section_key,
            "prior_changes_id": self.prior_changes_id,
            "batch_type": self.batch_type,
            "suggestion_count": self.size,
            "total_chars": self.total_chars,
            "priority_score": self.priority_score,
        }


_WHITESPACE = re.compile(r"\s*")
_STEP_WORD = re.compile(r"step", re.IGNORECASE)
_DIGITS = re.compile(r"\d*")
_SEPARATORS = re.compile(r"[:\s.-]*")


def _section_parts(reference: str) -> Optional[Tuple[Optional[str], str]]:
    """``(step number or None, section name)`` of a section reference, or None.

    Exactly the groups of ``re.match(r'(?:###?\\s*)?(?:Step\\s*)?(\\d+)?[:\\s.-]*(.+?)(?:\\s*$)',
    reference, re.IGNORECASE)``, computed in linear time. The regex itself is
    polynomial on a reviewer's ``reference``: every way to share one whitespace
    run between its three ``\\s`` quantifiers and the lazy name is tried before
    a later line makes it fail (185 s for ``## `` + 1,000 spaces + ``x\\ny``).

    The same search, with its order kept: each optional piece is tried taken
    (longest first) before skipped, and the first parse whose separators can
    end where the name may start wins. The name may start at *e* when it can
    run to the end on one line: ``.`` stops at a newline, and the closing
    ``\\s*$`` only matches all of the remaining whitespace. So *e* is past the
    last newline before the trailing whitespace (or a non-newline inside it),
    the name runs to that trailing whitespace (at least one character), and the
    separators take the largest such *e* they can reach.
    """
    text = reference
    size = len(text)
    trailing = len(text.rstrip())  # where the closing \s*$ may begin
    last_newline = text.rfind("\n", 0, trailing)
    tail_start = next(
        (e for e in range(size - 1, trailing - 1, -1) if text[e] != "\n"), None)
    separators_end: Dict[int, int] = {}

    def run_of_separators(c: int) -> int:
        if c not in separators_end:
            if c + 1 in separators_end and c < size and (
                    text[c] in ":.-" or text[c].isspace()):
                separators_end[c] = separators_end[c + 1]
            else:
                separators_end[c] = _SEPARATORS.match(text, c).end()
        return separators_end[c]

    def name_start(c: int) -> Optional[int]:
        """The largest start the separators from *c* can leave the name."""
        reach = min(run_of_separators(c), size - 1)
        if tail_start is not None and c <= tail_start <= reach:
            return tail_start
        e = min(reach, trailing - 1)
        return e if e >= c and e > last_newline else None

    def after_step(b: int) -> Optional[Tuple[Optional[str], int]]:
        for c in range(_DIGITS.match(text, b).end(), b, -1):
            e = name_start(c)
            if e is not None:
                return text[b:c], e
        e = name_start(b)
        return None if e is None else (None, e)

    def after_heading(a: int) -> Optional[Tuple[Optional[str], int]]:
        step = _STEP_WORD.match(text, a)
        if step:
            for b in range(_WHITESPACE.match(text, step.end()).end(), step.end() - 1, -1):
                found = after_step(b)
                if found:
                    return found
        return after_step(a)

    heading_ends: List[int] = []
    if text.startswith("##"):
        if text.startswith("###"):
            heading_ends.extend(range(_WHITESPACE.match(text, 3).end(), 2, -1))
        heading_ends.extend(range(_WHITESPACE.match(text, 2).end(), 1, -1))
    heading_ends.append(0)
    for a in heading_ends:
        found = after_heading(a)
        if found:
            step_num, e = found
            return step_num, text[e:max(e + 1, trailing)]
    return None


def normalize_section_reference(reference: str) -> str:
    """
    Normalize a section reference to a canonical key for grouping.

    Examples:
        "### Step 3: Create Server Action" -> "step_3"
        "File: src/api.ts, Line 45" -> "file:src/api.ts"
        "Database Schema" -> "section:database_schema"
    """
    if not reference:
        return "unknown"

    reference = reference.strip()

    # Try to extract file path first
    file_match = FILE_PATTERN.search(reference)
    if file_match:
        return f"file:{file_match.group(1).lower()}"

    # Try to extract step number
    section = _section_parts(reference)
    if section:
        step_num = section[0]
        section_name = section[1].strip().lower()

        if step_num:
            return f"step_{step_num}"
        else:
            # Normalize section name
            normalized = re.sub(r'[^\w\s]', '', section_name)
            normalized = re.sub(r'\s+', '_', normalized)
            return f"section:{normalized[:30]}"

    # Fallback: normalize the whole string
    normalized = re.sub(r'[^\w\s]', '', reference.lower())
    normalized = re.sub(r'\s+', '_', normalized)
    return f"ref:{normalized[:30]}"


def extract_section_order(reference: str) -> int:
    """
    Extract a numeric ordering from a reference for sorting.

    Returns step/section number if found, or 999 for unknown.
    """
    if not reference:
        return 999

    # Look for step numbers
    step_match = re.search(r'step\s*(\d+)', reference, re.IGNORECASE)
    if step_match:
        return int(step_match.group(1))

    # Look for any leading number
    num_match = re.search(r'^[#\s]*(\d+)', reference)
    if num_match:
        return int(num_match.group(1))

    return 999


def are_types_compatible(type1: str, type2: str) -> bool:
    """
    Check if two suggestion types can be safely batched together.

    Deletions should NOT be batched with other types because they
    change the structure that other suggestions might reference.
    """
    type1 = type1.lower() if type1 else "modification"
    type2 = type2.lower() if type2 else "modification"

    # Deletions are always isolated
    if type1 == "deletion" or type2 == "deletion":
        return type1 == type2

    # Clarifications can go with anything except deletions
    if type1 == "clarification" or type2 == "clarification":
        return True

    # Additions and modifications can be batched together
    # (they're both "additive" in nature)
    compatible_types = {"addition", "modification", "improvement"}
    return type1 in compatible_types and type2 in compatible_types


def group_suggestions_for_subagents(
    suggestions: List[Dict[str, Any]],
    max_per_batch: int = MAX_SUGGESTIONS_PER_BATCH,
    max_chars: int = MAX_DESCRIPTION_CHARS,
    group_by_section: bool = True,
) -> List[SuggestionBatch]:
    """
    Group validated suggestions into batches for efficient subagent processing.

    Heuristics applied (in priority order):
    1. Same section/reference → group together
    2. Compatible types → can be batched
    3. Size limits → split if too large
    4. Type ordering → deletions first, then modifications, then additions

    Args:
        suggestions: List of validated suggestion dicts from the orchestrator
        max_per_batch: Maximum suggestions per batch (default: 4)
        max_chars: Maximum total description chars per batch (default: 2500)
        group_by_section: Whether to group by section reference (default: True)

    Returns:
        List of SuggestionBatch objects ready for subagent processing
    """
    if not suggestions:
        return []

    batches: List[SuggestionBatch] = []

    # Step 1: Separate deletions - they always go in their own batches
    deletions = [s for s in suggestions if s.get("type", "").lower() == "deletion"]
    others = [s for s in suggestions if s.get("type", "").lower() != "deletion"]

    # Process deletions first (each in its own batch for safety)
    for deletion in deletions:
        batch = SuggestionBatch(section_key=normalize_section_reference(deletion.get("reference", "")))
        batch.add(deletion)
        batches.append(batch)

    if not others:
        return batches

    # Step 2: Group non-deletions by section if enabled
    if group_by_section:
        section_clusters: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for suggestion in others:
            section_key = normalize_section_reference(suggestion.get("reference", ""))
            section_clusters[section_key].append(suggestion)

        # Sort clusters by section order (step 1 before step 2, etc.)
        sorted_sections = sorted(
            section_clusters.items(),
            key=lambda x: min(
                (extract_section_order(s.get("reference", "")) for s in x[1]),
                default=999  # Fallback for empty clusters
            )
        )
    else:
        # No section grouping - treat all as one cluster
        sorted_sections = [("all", others)]

    # Step 3: Within each section, create batches respecting limits
    for section_key, cluster in sorted_sections:
        # Sort by importance within cluster (HIGH first)
        cluster.sort(key=lambda s: _importance.rank(s.get("importance")))

        current_batch = SuggestionBatch(section_key=section_key)

        for suggestion in cluster:
            # Check if we can add to current batch
            if current_batch.can_add(suggestion):
                # Check type compatibility with existing suggestions
                if current_batch.size == 0:
                    current_batch.add(suggestion)
                else:
                    existing_type = current_batch.suggestions[0].get("type", "modification")
                    new_type = suggestion.get("type", "modification")

                    if are_types_compatible(existing_type, new_type):
                        current_batch.add(suggestion)
                    else:
                        # Type mismatch - start new batch
                        if current_batch.size > 0:
                            batches.append(current_batch)
                        current_batch = SuggestionBatch(section_key=section_key)
                        current_batch.add(suggestion)
            else:
                # Batch is full or would exceed limits - start new batch
                if current_batch.size > 0:
                    batches.append(current_batch)
                current_batch = SuggestionBatch(section_key=section_key)
                current_batch.add(suggestion)

        # Don't forget the last batch
        if current_batch.size > 0:
            batches.append(current_batch)

    # Step 4: Sort final batches by priority (higher priority first)
    # But keep section order as primary sort key
    batches.sort(key=lambda b: (-b.priority_score,))

    return batches


#: A multi-suggestion prompt's section on the batches before it: the
#: ``{prior_changes_context}`` token is filled at dispatch time.
PRIOR_BATCHES_SECTION = """## Changes Applied in Prior Batches
(Review these to avoid redoing work — do NOT re-apply these changes)

{prior_changes_context}
"""


def format_suggestion_block(number: int, suggestion: Dict[str, Any], reference_label: str) -> str:
    """One suggestion of a multi-suggestion prompt, its reference under
    *reference_label* (the plan's ``Section``, the task list's ``Task reference``)."""
    s = suggestion
    return f"""---
### Suggestion {number}: {s.get('title', 'Untitled')}
- **Type**: {s.get('type', 'modification')}
- **{reference_label}**: {s.get('reference', 'N/A')}
- **Importance**: {s.get('importance', 'MEDIUM')}

**Details**:
{s.get('description', 'No description provided.')}
"""


def format_batch_for_prompt(batch: SuggestionBatch, plan_path: str) -> str:
    """
    Format a batch of suggestions into a prompt for a subagent.

    Returns a well-structured prompt that clearly describes all suggestions
    in the batch and how to apply them.

    Raises:
        ValueError: If the batch contains no suggestions.
    """
    suggestions = batch.suggestions

    if not suggestions:
        raise ValueError("Cannot format prompt for empty batch")

    if len(suggestions) == 1:
        # Single suggestion - use the original format
        s = suggestions[0]
        return f"""Apply the following suggestion to the plan file:

**Plan file**: {plan_path}
**Suggestion**: {s.get('title', 'Untitled')}
**Type**: {s.get('type', 'modification')}
**Section**: {s.get('reference', 'N/A')}
**Importance**: {s.get('importance', 'MEDIUM')}

**Details**:
{s.get('description', 'No description provided.')}

## Changes Applied in Prior Batches
(Review these to avoid redoing work — do NOT re-apply these changes)

{{prior_changes_context}}

Instructions:
1. Read the current plan file
2. Locate the section mentioned in the reference
3. Apply the suggested change appropriately:
   - For "addition": Add new content in the appropriate location
   - For "modification": Update existing content as described
   - For "deletion": Remove the specified content
   - For "clarification": Rewrite for clarity while preserving meaning
4. Ensure the change integrates smoothly with surrounding content
5. Check if the plan already contains a similar change (from a previously applied suggestion). If so, skip this suggestion or merge it with the existing content rather than duplicating
6. Do NOT make any other changes beyond this specific suggestion

Return a brief summary of what was changed."""

    # Multiple suggestions - batch format
    section_info = f" (Section: {batch.section_key})" if batch.section_key != "unknown" else ""

    prompt_parts = [
        f"Apply the following {len(suggestions)} related suggestions to the plan file{section_info}:",
        f"\n**Plan file**: {plan_path}",
        f"**Batch type**: {batch.batch_type}",
        f"**Suggestions in this batch**: {len(suggestions)}\n",
    ]

    for i, s in enumerate(suggestions, 1):
        prompt_parts.append(format_suggestion_block(i, s, "Section"))

    prompt_parts.append(PRIOR_BATCHES_SECTION)

    prompt_parts.append("""---

## Instructions

1. Read the current plan file first
2. Apply ALL suggestions in this batch, processing them in order
3. For each suggestion:
   - Locate the referenced section
   - Apply the change according to its type (addition/modification/deletion/clarification)
   - Ensure changes integrate smoothly with surrounding content
4. Do NOT make any changes beyond these specific suggestions
5. If suggestions affect the same area, apply them intelligently to avoid conflicts
6. Before applying each suggestion, check if the plan already reflects a similar change (from a previously applied batch). If a suggestion is already addressed, note it as "already applied" in the summary and move on

## Return Format

Return a brief summary for EACH suggestion applied:
```
Suggestion 1: [What was changed]
Suggestion 2: [What was changed]
Suggestion N: Already addressed by prior changes - skipped
...
```""")

    return "\n".join(prompt_parts)


def estimate_batch_processing_stats(batches: List[SuggestionBatch]) -> Dict[str, Any]:
    """
    Calculate statistics about the batching result.

    Useful for reporting efficiency gains.
    """
    total_suggestions = sum(b.size for b in batches)
    total_batches = len(batches)

    # Without batching, each suggestion would be 1 subagent call
    subagent_calls_saved = total_suggestions - total_batches
    efficiency_gain = (subagent_calls_saved / total_suggestions * 100) if total_suggestions > 0 else 0

    batch_sizes = [b.size for b in batches]
    avg_batch_size = sum(batch_sizes) / len(batch_sizes) if batch_sizes else 0

    type_distribution = defaultdict(int)
    for b in batches:
        type_distribution[b.batch_type] += 1

    return {
        "total_suggestions": total_suggestions,
        "total_batches": total_batches,
        "subagent_calls_saved": subagent_calls_saved,
        "efficiency_gain_percent": round(efficiency_gain, 1),
        "average_batch_size": round(avg_batch_size, 2),
        "max_batch_size": max(batch_sizes) if batch_sizes else 0,
        "single_suggestion_batches": sum(1 for b in batches if b.size == 1),
        "multi_suggestion_batches": sum(1 for b in batches if b.size > 1),
        "batch_type_distribution": dict(type_distribution),
    }
