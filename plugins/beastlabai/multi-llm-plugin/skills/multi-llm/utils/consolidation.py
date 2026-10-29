#!/usr/bin/env python3
"""
Consolidation utility for clustering related suggestion groups.

Provides core functions for the post-validation consolidation step that
clusters related suggestion groups by plan section and generates
consolidated suggestions preserving nuance from all underlying suggestions.
"""

import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Import state_manager's generate_group_id for reference (both coexist)
# Also import CURRENT_FORMAT_VERSION and load_groups_payload for v2 envelope support
try:
    from .state_manager import (
        generate_group_id as _state_generate_group_id,
        CURRENT_FORMAT_VERSION,
        load_groups_payload,
    )
except ImportError:
    from utils.state_manager import (
        generate_group_id as _state_generate_group_id,
        CURRENT_FORMAT_VERSION,
        load_groups_payload,
    )

# Import report_parser functions for consolidated decision loading
try:
    from .report_parser import (
        parse_consolidated_skipped_groups,
        parse_consolidated_validation_overrides,
        load_consolidated_html_selections,
        merge_consolidated_selections,
    )
except ImportError:
    from utils.report_parser import (
        parse_consolidated_skipped_groups,
        parse_consolidated_validation_overrides,
        load_consolidated_html_selections,
        merge_consolidated_selections,
    )

try:
    from . import cli_common
    from .prompt_loader import load_prompt
    from .subagent_prompts import build_consolidation_prompt
    from .subagent_tasks import PromptBudget, build_inputs, make_task, make_task_file
except ImportError:
    from utils import cli_common
    from utils.prompt_loader import load_prompt
    from utils.subagent_prompts import build_consolidation_prompt
    from utils.subagent_tasks import (
        PromptBudget,
        build_inputs,
        make_task,
        make_task_file,
    )

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Named constants
# ---------------------------------------------------------------------------

# Sections with more groups than this are split into sub-batches.
# Higher than validation's threshold (4) because consolidation groups are
# pre-filtered (valid/needs-human-decision only) and the LLM clustering task
# benefits from seeing more groups at once to identify cross-group relationships.
CONSOLIDATION_SPLIT_THRESHOLD = 8

# Maximum groups per sub-batch. Larger than validation batches (4) because
# consolidation prompts are simpler (cluster, don't evaluate) and each group's
# representation in the prompt is smaller (theme + importance, not full context).
MAX_GROUPS_PER_CONSOLIDATION_BATCH = 6

# Timeout in seconds per consolidation subagent call. On timeout, the subagent
# is retried once; if the retry also times out, all groups in that batch fall
# back to singletons.
CONSOLIDATION_SUBAGENT_TIMEOUT = 90

# Minimum number of valid groups before the orchestrator prints
# [CONSOLIDATION_RECOMMENDED]. Configurable via --consolidation-threshold.
CONSOLIDATION_RECOMMENDED_THRESHOLD = 15

#: Beside ``consolidation_batch_{N}.json``, exactly the bytes of that batch's
#: ``prompt`` (``validation.PROMPT_SIDECAR_TEMPLATE``'s rule; ``.txt``, so the
#: ``*.json`` reaggregation globs never read it). Live run 8, Claude Code
#: racing 01: with no ``prompt_path`` on the batches the host wrote each prompt
#: to a temp file of its own, outside the repository, to hand its subagents
#: a file.
CONSOLIDATION_PROMPT_TEMPLATE = "consolidation_batch_{index}.prompt.txt"

# Character budget for combined suggestion content per batch (themes +
# descriptions). Batches exceeding this limit are split further.
CONSOLIDATION_CHAR_BUDGET = 12000


# ---------------------------------------------------------------------------
# Type priority for merged groups
# ---------------------------------------------------------------------------

# Priority order: addition > modification > deletion > clarification.
# Higher value = higher priority / more actionable type.
TYPE_PRIORITY: Dict[str, int] = {
    "addition": 4,
    "modification": 3,
    "deletion": 2,
    "clarification": 1,
}


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def generate_group_id(group: Dict[str, Any]) -> str:
    """
    Compute a stable 12-char hex hash for a suggestion group.

    This is DIFFERENT from state_manager.py's generate_group_id() which uses
    a 16-char hex hash and different input fields. Both coexist — this version
    is used by the consolidation pipeline for group identity tracking.

    Algorithm:
        canonical_string = theme + "\\x00" + "\\x00".join(sorted_titles)
        hash = sha256(canonical_string)[:12]

    Args:
        group: A group dictionary containing ``theme`` and ``suggestions``
            (each suggestion having a ``title`` field).

    Returns:
        A 12-character hex string identifier.
    """
    theme = group.get("theme", "")
    suggestions = group.get("suggestions", [])
    sorted_titles = sorted(s.get("title", "") for s in suggestions)
    canonical_string = theme + "\x00" + "\x00".join(sorted_titles)
    return hashlib.sha256(canonical_string.encode()).hexdigest()[:12]


def generate_consolidated_id(underlying_group_ids: List[str]) -> str:
    """
    Compute a stable 12-char hex hash from sorted underlying group IDs.

    For singletons (single underlying group), returns the underlying group's
    ``group_id`` directly — no additional hashing.

    Args:
        underlying_group_ids: List of group_id strings from the underlying
            groups that form this consolidated group.

    Returns:
        A 12-character hex string identifier.
    """
    if len(underlying_group_ids) == 1:
        return underlying_group_ids[0]

    canonical = "\x00".join(sorted(underlying_group_ids))
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


def normalize_reference(reference: Optional[str]) -> str:
    """
    Normalize a suggestion group's ``reference`` field for section grouping.

    Normalization rules (applied in order):
        1. Strip leading ``#`` characters and whitespace.
        2. Lowercase.
        3. Strip trailing description after colon
           (e.g. ``task 3: api integration`` -> ``task 3``).
        4. Normalize numbering: strip leading zeros in numbers
           (e.g. ``task 01`` -> ``task 1``).
        5. Collapse whitespace.
        6. Return ``"_uncategorized"`` for empty/missing/whitespace-only refs.

    Args:
        reference: The raw reference string (may be ``None``).

    Returns:
        The normalized section key, or ``"_uncategorized"``.
    """
    if reference is None:
        return "_uncategorized"

    # 1. Strip leading '#' chars and whitespace
    #    Handle mixed leading whitespace and '#' (e.g. "  ## Task 3")
    normalized = reference.strip()
    normalized = normalized.lstrip("#").strip()

    # 2. Lowercase
    normalized = normalized.lower()

    # 3. Strip trailing description after colon
    colon_idx = normalized.find(":")
    if colon_idx != -1:
        normalized = normalized[:colon_idx].strip()

    # 4. Normalize numbering — strip leading zeros in numbers
    #    e.g. "task 01" -> "task 1", "section 007" -> "section 7"
    normalized = re.sub(r"\b0+(\d)", r"\1", normalized)

    # 5. Collapse whitespace
    normalized = re.sub(r"\s+", " ", normalized).strip()

    # 6. Fallback for empty/missing
    if not normalized:
        return "_uncategorized"

    return normalized


def pre_group_by_section(
    groups: List[Dict[str, Any]],
    validation: List[Dict[str, Any]],
) -> Dict[str, List[int]]:
    """
    Filter to valid + needs-human-decision groups and group indices by section.

    Groups are filtered using the ``validation`` list (each entry has ``status``
    and ``group_index``). Only groups with status ``"valid"`` or
    ``"needs-human-decision"`` are retained. Indices are then grouped by the
    normalized ``reference`` field of each group.

    All-invalid sections (every group filtered out) are omitted from the
    returned dict and a debug-level log is emitted for each.

    Args:
        groups: The full list of suggestion group dicts (from grouped.json).
        validation: The validation results list (from validation.json), where
            each entry has at minimum ``status`` and ``group_index`` fields.

    Returns:
        A mapping of normalized section key to a list of group indices that
        passed the validation filter. Sections with no passing groups are
        excluded.
    """
    # Build a set of group indices that passed validation
    accepted_statuses = {"valid", "needs-human-decision"}
    valid_indices: Set[int] = set()
    for entry in validation:
        status = entry.get("status", "")
        group_index = entry.get("group_index")
        if group_index is not None and status in accepted_statuses:
            valid_indices.add(group_index)

    # Group valid indices by normalized reference
    section_groups: Dict[str, List[int]] = {}
    # Track total groups per section (before filtering) for debug logging
    section_total: Dict[str, int] = {}

    for idx, group in enumerate(groups):
        reference = group.get("reference", None)
        section_key = normalize_reference(reference)

        if section_key not in section_total:
            section_total[section_key] = 0
        section_total[section_key] += 1

        if idx in valid_indices:
            if section_key not in section_groups:
                section_groups[section_key] = []
            section_groups[section_key].append(idx)

    # Log omitted sections (all groups invalid)
    for section_key, total in section_total.items():
        if section_key not in section_groups:
            logger.debug(
                "Section '%s' skipped: all %d groups invalid",
                section_key,
                total,
            )

    return section_groups


# ---------------------------------------------------------------------------
# Batch preparation helpers
# ---------------------------------------------------------------------------

def _measure_group_content_length(group: Dict[str, Any]) -> int:
    """
    Measure the character length of a group's content for budget purposes.

    Counts the theme length plus all suggestion description lengths within
    the group. This corresponds to the content that will appear in the
    consolidation prompt for this group.

    Args:
        group: A suggestion group dict with ``theme`` and ``suggestions``.

    Returns:
        Total character count of theme + all suggestion descriptions.
    """
    length = len(group.get("theme", ""))
    for suggestion in group.get("suggestions", []):
        length += len(suggestion.get("description", ""))
    return length


def _truncate_group_content(group: Dict[str, Any], budget: int) -> Dict[str, Any]:
    """
    Create a truncated copy of a group whose content fits within budget.

    Preserves the first and last 20% of each suggestion's description with
    a ``[...truncated...]`` marker in the middle. The group dict is deep-copied
    so the original is not mutated.

    Args:
        group: The original group dict.
        budget: Maximum character budget for the truncated group.

    Returns:
        A new group dict with truncated suggestion descriptions.
    """
    import copy

    truncated = copy.deepcopy(group)
    # Truncate each suggestion description proportionally
    for suggestion in truncated.get("suggestions", []):
        desc = suggestion.get("description", "")
        if len(desc) <= 100:
            # Too short to meaningfully truncate
            continue
        # Keep first 20% and last 20%, replace middle with marker
        keep_chars = max(20, int(len(desc) * 0.2))
        suggestion["description"] = (
            desc[:keep_chars] + " [...truncated...] " + desc[-keep_chars:]
        )
    return truncated


def _split_into_budget_batches(
    group_indices: List[int],
    groups: List[Dict[str, Any]],
    max_per_batch: int,
    char_budget: int,
) -> List[List[int]]:
    """
    Split group indices into sub-batches respecting both size and char budget.

    Iterates through ``group_indices``, accumulating groups into the current
    batch until either ``max_per_batch`` is reached or adding the next group
    would exceed ``char_budget``. Groups that individually exceed the budget
    are placed in a solo batch (they will be truncated at prompt-build time).

    Args:
        group_indices: Indices into ``groups`` to be batched.
        groups: The full list of suggestion group dicts.
        max_per_batch: Maximum number of groups per batch.
        char_budget: Maximum combined content characters per batch.

    Returns:
        A list of sub-batches, where each sub-batch is a list of group indices.
    """
    batches: List[List[int]] = []
    current_batch: List[int] = []
    current_chars = 0

    for idx in group_indices:
        group_len = _measure_group_content_length(groups[idx])

        # If a single group exceeds the budget, it gets a solo batch
        if group_len >= char_budget and not current_batch:
            batches.append([idx])
            continue

        # If adding this group would exceed limits, close the current batch
        if current_batch and (
            len(current_batch) >= max_per_batch
            or current_chars + group_len > char_budget
        ):
            batches.append(current_batch)
            current_batch = []
            current_chars = 0

        # If this single group exceeds budget and current_batch is non-empty,
        # first flush current batch, then give this group a solo batch
        if group_len >= char_budget:
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_chars = 0
            batches.append([idx])
            continue

        current_batch.append(idx)
        current_chars += group_len

    # Don't forget the last batch
    if current_batch:
        batches.append(current_batch)

    return batches


def build_consolidation_group_records(
    groups: List[Dict[str, Any]],
    group_indices: List[int],
    group_ids: List[str],
    char_budget: int = CONSOLIDATION_CHAR_BUDGET,
) -> List[Dict[str, Any]]:
    """Build the group records one consolidation batch embeds in its prompt.

    A solo group whose content exceeds ``char_budget`` is content-truncated by
    ``_truncate_group_content`` — the truncation the batcher always deferred to
    "prompt-build time", which is here now that prompt assembly lives in Python.
    That is a *content* reduction with an explicit marker, not the silent
    instruction-tail truncation D2d forbids.

    Args:
        groups: All groups for the phase.
        group_indices: This batch's indices into ``groups``.
        group_ids: ``group_ids[i]`` is the stable id of ``groups[i]``.

    Returns:
        One record per group in the batch.
    """
    records: List[Dict[str, Any]] = []
    solo = len(group_indices) == 1
    for idx in group_indices:
        group = groups[idx]
        if solo and _measure_group_content_length(group) > char_budget:
            group = _truncate_group_content(group, char_budget)
        records.append({
            "index": idx,
            "group_id": group_ids[idx],
            "theme": group.get("theme", "Unknown"),
            "importance": group.get("importance", "MEDIUM"),
            "type": group.get("type", "unknown"),
            "reference": group.get("reference", ""),
            "suggestions": [
                {
                    "title": s.get("title", ""),
                    "description": s.get("description", s.get("desc", "")),
                }
                for s in group.get("suggestions", [])
            ],
        })
    return records


def prepare_consolidation_tasks(
    groups: List[Dict[str, Any]],
    section_groups: Dict[str, List[int]],
    phase_dir: str,
    plan_file: str,
    prompt_budget: Optional[PromptBudget] = None,
) -> Dict[str, Any]:
    """
    Prepare consolidation batch tasks for subagent processing.

    For each section with 2+ groups, creates consolidation batches. Sections
    with more than ``CONSOLIDATION_SPLIT_THRESHOLD`` groups are split into
    sub-batches of at most ``MAX_GROUPS_PER_CONSOLIDATION_BATCH``, subject to
    ``CONSOLIDATION_CHAR_BUDGET`` per batch. Sections with exactly 1 group are
    recorded as singletons (pass-through, no batch needed).

    Batch numbering is global and sequential across all sections
    (``consolidation_batch_0.json``, ``consolidation_batch_1.json``, ...).

    The output is written to ``consolidation_tasks.json`` in ``phase_dir`` and
    follows the same structural pattern as ``prepare_batched_validation_tasks()``
    in ``utils/validation.py``.

    Args:
        groups: The full list of suggestion group dicts (from grouped.json).
        section_groups: Mapping of section_key to list of group indices, as
            returned by ``pre_group_by_section()``.
        phase_dir: Path to the review-plan phase directory.
        plan_file: Path to the original plan file.

    Returns:
        A dict with the structure::

            {
                "batches": [
                    {
                        "batch_index": 0,
                        "section_key": "task 3",
                        "group_indices": [2, 5, 8],
                        "group_ids": ["abc...", "def...", "ghi..."],
                        "groups_count": 3,
                        "output_path": ".../consolidation_batch_0.json"
                    },
                    ...
                ],
                "singleton_sections": {"section_key": [group_indices]},
                "total_batches": N,
                "phase_dir": "...",
                "plan_file": "...",
                "grouped_file": "grouped.json",
                "reaggregate_command": "--reaggregate-consolidation",
                "replay_flags": ["--quick"]
            }

    ``reaggregate_command`` is the bare verb, not a command; the reader
    (``review_plan_orchestrator.consolidate_mode``) composes the runnable
    string through ``cli_common.retry_command`` from mode ``review-plan``,
    this document's ``plan_file``, that verb and ``replay_flags`` — the
    writing invocation's own selection flags (D2), so the merge is retried
    under the panel the caller asked for.
    """
    phase_path = Path(phase_dir)

    # Pre-compute group_ids for all groups
    group_ids: List[str] = []
    for group in groups:
        group_ids.append(generate_group_id(group))

    # Read once, embed per batch: the template is I/O, the generator is pure.
    template = load_prompt("consolidate_suggestions.txt")
    inputs = build_inputs(
        plan_file=plan_file,
        grouped_file=str(phase_path / "grouped.json"),
    )
    budget = prompt_budget or PromptBudget(None)

    batches: List[Dict[str, Any]] = []
    singleton_sections: Dict[str, List[int]] = {}
    batch_counter = 0

    # Process sections in sorted order for deterministic output
    for section_key in sorted(section_groups.keys()):
        indices = section_groups[section_key]

        # Singletons: sections with exactly 1 group — pass-through
        if len(indices) < 2:
            singleton_sections[section_key] = indices
            continue

        # Determine batching strategy
        if len(indices) <= CONSOLIDATION_SPLIT_THRESHOLD:
            # Section fits in one batch — but still check char budget
            sub_batches = _split_into_budget_batches(
                indices, groups, len(indices), CONSOLIDATION_CHAR_BUDGET
            )
        else:
            # Large section — split into sub-batches
            sub_batches = _split_into_budget_batches(
                indices,
                groups,
                MAX_GROUPS_PER_CONSOLIDATION_BATCH,
                CONSOLIDATION_CHAR_BUDGET,
            )

        # Create batch entries with global sequential numbering
        for sub_batch_indices in sub_batches:
            output_name = f"consolidation_batch_{batch_counter}.json"
            output_path = phase_path / output_name
            batch_group_ids = [group_ids[idx] for idx in sub_batch_indices]

            # The prompt embeds the filled prompts/consolidate_suggestions.txt
            # plus this batch's group records — the values, not a path to
            # grouped.json.
            prompt = build_consolidation_prompt(
                template=template,
                group_records=build_consolidation_group_records(
                    groups, sub_batch_indices, group_ids
                ),
            )
            if not budget.fits(prompt):
                # Sections are already split by MAX_GROUPS_PER_CONSOLIDATION_BATCH
                # and CONSOLIDATION_CHAR_BUDGET, so an over-budget prompt here
                # means the runner's transport is the constraint. Fail loudly with
                # the fix; never truncate the instruction tail.
                budget.resolution(prompt, splittable=False)

            batches.append(make_task(
                kind="consolidation",
                task_id=f"consolidation-batch-{batch_counter}",
                prompt=prompt,
                output_name=output_name,
                inputs=inputs,
                output_path=str(output_path),
                prompt_path=str(
                    phase_path / CONSOLIDATION_PROMPT_TEMPLATE.format(index=batch_counter)
                ),
                prompt_lines=prompt.count("\n") + 1,
                extra={
                    "batch_index": batch_counter,
                    "section_key": section_key,
                    "group_indices": sub_batch_indices,
                    "group_ids": batch_group_ids,
                    "groups_count": len(sub_batch_indices),
                    "plan_file": plan_file,
                    "grouped_file": str(phase_path / "grouped.json"),
                },
            ))
            batch_counter += 1

    # The prompt files a native host hands its subagents, written beside the
    # batches (validation's sidecar rule: all or none, `prompt` stays the source).
    try:
        from .validation import write_prompt_sidecars
    except ImportError:  # pragma: no cover - direct script runs
        from utils.validation import write_prompt_sidecars  # type: ignore
    write_prompt_sidecars(
        batches, str(phase_path),
        stale_glob=CONSOLIDATION_PROMPT_TEMPLATE.format(index="*"),
    )

    # Build the tasks metadata
    tasks_metadata: Dict[str, Any] = make_task_file(
        kind="consolidation",
        tasks=batches,
        inputs=inputs,
        task_list_key="batches",
        extra={
            "format_version": CURRENT_FORMAT_VERSION,
            "singleton_sections": singleton_sections,
            "total_batches": len(batches),
            "phase_dir": phase_dir,
            "plan_file": plan_file,
            "grouped_file": "grouped.json",
            "reaggregate_command": "--reaggregate-consolidation",
            "replay_flags": cli_common.current_replay_flags(mode="review-plan"),
        },
    )

    # Write consolidation_tasks.json
    tasks_path = phase_path / "consolidation_tasks.json"
    tasks_path.parent.mkdir(parents=True, exist_ok=True)
    with open(tasks_path, "w", encoding="utf-8") as f:
        json.dump(tasks_metadata, f, indent=2)

    logger.info(
        "Prepared %d consolidation batches across %d sections "
        "(%d singleton sections)",
        len(batches),
        len(section_groups) - len(singleton_sections),
        len(singleton_sections),
    )

    return tasks_metadata


# ---------------------------------------------------------------------------
# Merge helpers
# ---------------------------------------------------------------------------

# Importance priority for choosing the higher importance level.
_IMPORTANCE_PRIORITY: Dict[str, int] = {
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}


def _word_overlap_ratio(title_a: str, title_b: str) -> float:
    """
    Compute word-overlap ratio between two titles.

    Both titles are normalized (lowercased, split on whitespace) and the
    ratio is computed as ``|intersection| / |union|`` (Jaccard similarity).
    Returns 0.0 when both titles are empty.

    Args:
        title_a: First title string.
        title_b: Second title string.

    Returns:
        A float between 0.0 and 1.0 representing the word overlap ratio.
    """
    words_a = set(title_a.lower().split())
    words_b = set(title_b.lower().split())
    if not words_a and not words_b:
        return 0.0
    union = words_a | words_b
    if not union:
        return 0.0
    intersection = words_a & words_b
    return len(intersection) / len(union)


def _highest_importance(*importance_values: str) -> str:
    """
    Return the highest importance level among the given values.

    Uses ``_IMPORTANCE_PRIORITY`` ordering: HIGH > MEDIUM > LOW.
    Unrecognized values are treated as lowest priority.

    Args:
        *importance_values: One or more importance level strings.

    Returns:
        The highest importance level string.
    """
    best = "LOW"
    best_rank = _IMPORTANCE_PRIORITY.get(best, 0)
    for val in importance_values:
        normalized = val.upper() if isinstance(val, str) else ""
        rank = _IMPORTANCE_PRIORITY.get(normalized, 0)
        if rank > best_rank:
            best = normalized
            best_rank = rank
    return best


def _resolve_type_for_group_ids(
    group_id_list: List[str],
    groups: List[Dict[str, Any]],
    group_id_to_index: Dict[str, int],
) -> str:
    """
    Determine the highest-priority type for a set of underlying group IDs.

    Uses ``TYPE_PRIORITY`` ordering: addition > modification > deletion >
    clarification. Examines each underlying group's ``type``/``category``
    field and its suggestion-level ``type`` fields.

    Args:
        group_id_list: List of group_id strings.
        groups: The full list of suggestion group dicts.
        group_id_to_index: Mapping from group_id to index in ``groups``.

    Returns:
        The highest-priority type string found, or ``"clarification"``
        as the fallback.
    """
    best_type = "clarification"
    best_priority = TYPE_PRIORITY.get(best_type, 0)

    for gid in group_id_list:
        idx = group_id_to_index.get(gid)
        if idx is None or idx >= len(groups):
            continue
        group = groups[idx]
        # Check group-level type
        group_type = group.get("type", "")
        if group_type:
            p = TYPE_PRIORITY.get(group_type.lower(), 0)
            if p > best_priority:
                best_type = group_type.lower()
                best_priority = p
        # Check category (some groups use 'category' instead of 'type')
        category = group.get("category", "")
        if category:
            p = TYPE_PRIORITY.get(category.lower(), 0)
            if p > best_priority:
                best_type = category.lower()
                best_priority = p
        # Check suggestion-level types
        for suggestion in group.get("suggestions", []):
            s_type = suggestion.get("type", "")
            if s_type:
                p = TYPE_PRIORITY.get(s_type.lower(), 0)
                if p > best_priority:
                    best_type = s_type.lower()
                    best_priority = p

    return best_type


def _get_reference_for_cluster(
    underlying_group_ids: List[str],
    groups: List[Dict[str, Any]],
    group_id_to_index: Dict[str, int],
) -> str:
    """
    Get the reference string for a cluster from its underlying groups.

    Returns the reference from the first underlying group that has a
    non-empty reference field. Falls back to empty string if none found.

    Args:
        underlying_group_ids: List of group_id strings.
        groups: The full list of suggestion group dicts.
        group_id_to_index: Mapping from group_id to index in ``groups``.

    Returns:
        The reference string, or empty string.
    """
    for gid in underlying_group_ids:
        idx = group_id_to_index.get(gid)
        if idx is not None and idx < len(groups):
            ref = groups[idx].get("reference", "")
            if ref:
                return ref
    return ""


def _make_singleton_consolidated(
    group_id: str,
    group_index: int,
    group: Dict[str, Any],
    reasoning: str = "",
) -> Dict[str, Any]:
    """
    Build a consolidated group entry for a singleton (pass-through) group.

    Args:
        group_id: The group's stable ID.
        group_index: The group's index in the full groups list.
        group: The original suggestion group dict.
        reasoning: Optional reasoning string for why this is a singleton.

    Returns:
        A consolidated group dict ready for inclusion in the output list.
    """
    # Determine type from group
    group_type = (
        group.get("type", "")
        or group.get("category", "")
        or "clarification"
    ).lower()
    if group_type not in TYPE_PRIORITY:
        group_type = "clarification"

    # Determine importance
    importance = group.get("importance", "LOW")
    if isinstance(importance, str):
        importance = importance.upper()
    if importance not in _IMPORTANCE_PRIORITY:
        importance = "LOW"

    return {
        "title": group.get("theme", "Untitled"),
        "description": group.get("theme", ""),
        "importance": importance,
        "reference": group.get("reference", ""),
        "type": group_type,
        "underlying_group_indices": [group_index],
        "underlying_group_ids": [group_id],
        "model_count": len(group.get("models", [])) or 1,
        "original_suggestion_count": len(group.get("suggestions", [])) or 1,
        "is_singleton": True,
        "reasoning": reasoning or "Singleton group — no related groups to merge.",
    }


# ---------------------------------------------------------------------------
# Main merge function
# ---------------------------------------------------------------------------


def merge_consolidation_results(
    phase_dir: str,
    tasks_metadata: Dict[str, Any],
    groups: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Read consolidation batch files and merge into final consolidated groups.

    Reads each ``consolidation_batch_N.json`` from *phase_dir*, validates
    structure, handles errors gracefully, performs duplicate/missing group
    detection, cross-batch deduplication, type validation, and produces the
    final list of consolidated groups with stable IDs and display indices.

    Args:
        phase_dir: Path to the review-plan phase directory containing
            the ``consolidation_batch_N.json`` files.
        tasks_metadata: The loaded ``consolidation_tasks.json`` dict, as
            returned by ``prepare_consolidation_tasks()``. Contains
            ``batches`` (list of batch descriptors) and
            ``singleton_sections`` (dict of section_key to group indices).
        groups: The full list of suggestion group dicts from
            ``grouped.json``.

    Returns:
        A tuple of ``(consolidated_groups_list, partial_failures_metadata)``
        where:

        - ``consolidated_groups_list`` is a list of consolidated group dicts,
          each containing ``consolidated_id``, ``display_index``, ``title``,
          ``description``, ``importance``, ``reference``, ``type``,
          ``underlying_group_indices``, ``underlying_group_ids``,
          ``model_count``, ``original_suggestion_count``, ``is_singleton``,
          and ``reasoning``.
        - ``partial_failures_metadata`` is a dict with ``count``,
          ``batches`` (list of failed batch indices), and ``fallback``
          (always ``"all_singletons"``).
    """
    phase_path = Path(phase_dir)

    # Build group_id lookup: group_id -> index in groups list
    group_id_to_index: Dict[str, int] = {}
    for idx, group in enumerate(groups):
        gid = generate_group_id(group)
        group_id_to_index[gid] = idx

    # Collect all group_ids assigned to batches for completeness check later
    all_batch_group_ids: Set[str] = set()
    for batch_info in tasks_metadata.get("batches", []):
        for gid in batch_info.get("group_ids", []):
            all_batch_group_ids.add(gid)

    # Also collect singleton section group IDs
    all_singleton_group_ids: Set[str] = set()
    singleton_sections = tasks_metadata.get("singleton_sections", {})
    for _section_key, indices in singleton_sections.items():
        for idx in indices:
            if idx < len(groups):
                gid = generate_group_id(groups[idx])
                all_singleton_group_ids.add(gid)

    # The full set of input group_ids we expect to cover
    all_input_group_ids = all_batch_group_ids | all_singleton_group_ids

    # Track partial failures
    failed_batch_indices: List[int] = []

    # Track which group_ids have been claimed by a cluster (for dedup)
    claimed_group_ids: Set[str] = set()

    # Collect clusters and singletons per section for cross-batch dedup
    # Structure: section_key -> list of (cluster_dict, batch_index)
    section_clusters: Dict[str, List[Tuple[Dict[str, Any], int]]] = {}
    # Singletons from batch outputs (separate from singleton_sections)
    batch_singletons: List[Dict[str, Any]] = []

    # -------------------------------------------------------------------
    # Helper to emit all assigned groups as singletons for a failed batch
    # -------------------------------------------------------------------
    def _emit_as_singletons(
        assigned_gids: Set[str], reason: str,
    ) -> None:
        """Emit all assigned group_ids as singletons into batch_singletons."""
        for gid in assigned_gids:
            if gid not in claimed_group_ids:
                idx = group_id_to_index.get(gid)
                if idx is not None and idx < len(groups):
                    batch_singletons.append(
                        _make_singleton_consolidated(
                            gid, idx, groups[idx], reasoning=reason,
                        )
                    )
                    claimed_group_ids.add(gid)

    # -------------------------------------------------------------------
    # Steps 1-6: Read each batch file, validate, handle errors, dedup
    # -------------------------------------------------------------------
    batches = tasks_metadata.get("batches", [])
    for batch_info in batches:
        batch_index = batch_info["batch_index"]
        section_key = batch_info.get("section_key", "_uncategorized")
        assigned_group_ids = set(batch_info.get("group_ids", []))
        batch_file = phase_path / f"consolidation_batch_{batch_index}.json"

        # --- Read and parse ---
        batch_data = None
        if not batch_file.exists():
            logger.warning(
                "Consolidation batch file not found: %s — treating %d "
                "groups as singletons",
                batch_file,
                len(assigned_group_ids),
            )
            failed_batch_indices.append(batch_index)
            _emit_as_singletons(
                assigned_group_ids,
                f"Batch {batch_index} file missing — treated as singleton.",
            )
            continue

        try:
            with open(batch_file, "r", encoding="utf-8") as f:
                batch_data = json.load(f)
        except (json.JSONDecodeError, IOError) as exc:
            logger.warning(
                "Consolidation batch %d has invalid JSON (%s) — treating "
                "%d groups as singletons",
                batch_index,
                exc,
                len(assigned_group_ids),
            )
            failed_batch_indices.append(batch_index)
            _emit_as_singletons(
                assigned_group_ids,
                f"Batch {batch_index} invalid JSON — treated as singleton.",
            )
            continue

        if not isinstance(batch_data, dict):
            logger.warning(
                "Consolidation batch %d is not a JSON object — treating "
                "%d groups as singletons",
                batch_index,
                len(assigned_group_ids),
            )
            failed_batch_indices.append(batch_index)
            _emit_as_singletons(
                assigned_group_ids,
                f"Batch {batch_index} unexpected format — "
                "treated as singleton.",
            )
            continue

        # --- Step 3: Handle error batch files ---
        if "error" in batch_data:
            logger.warning(
                "Consolidation batch %d reported error '%s' — treating "
                "%d groups as singletons",
                batch_index,
                batch_data.get("error", "unknown"),
                len(assigned_group_ids),
            )
            failed_batch_indices.append(batch_index)
            # Error batches may include a 'groups' array of group_ids
            error_gids = batch_data.get("groups", [])
            fallback_gids = set(error_gids) if error_gids else set()
            _emit_as_singletons(
                fallback_gids,
                f"Batch {batch_index} error fallback — treated as singleton.",
            )
            # Also cover any assigned IDs not in the error groups list
            _emit_as_singletons(
                assigned_group_ids,
                f"Batch {batch_index} error fallback — treated as singleton.",
            )
            continue

        # --- Step 4: Validate structure (clusters/singletons keys) ---
        clusters_data = batch_data.get("clusters")
        singletons_data = batch_data.get("singletons")

        if (
            not isinstance(clusters_data, list)
            and not isinstance(singletons_data, list)
        ):
            logger.warning(
                "Consolidation batch %d missing both 'clusters' and "
                "'singletons' keys — treating %d groups as singletons. "
                "Errors: missing required keys",
                batch_index,
                len(assigned_group_ids),
            )
            failed_batch_indices.append(batch_index)
            _emit_as_singletons(
                assigned_group_ids,
                f"Batch {batch_index} schema validation failed — "
                "treated as singleton.",
            )
            continue

        # Ensure both are lists (one may be missing but that's ok)
        if not isinstance(clusters_data, list):
            clusters_data = []
        if not isinstance(singletons_data, list):
            singletons_data = []

        # --- Step 5: Field-level salvage for clusters ---
        for cluster in clusters_data:
            if not isinstance(cluster, dict):
                continue
            # Fill default for missing optional fields
            if "reasoning" not in cluster:
                cluster["reasoning"] = ""
            if "description" not in cluster:
                cluster["description"] = cluster.get("title", "")
            if "importance" not in cluster:
                cluster["importance"] = "MEDIUM"
            if "type" not in cluster:
                cluster["type"] = "clarification"
            if "title" not in cluster:
                cluster["title"] = "Untitled cluster"
            # Ensure underlying_group_ids exists
            if "underlying_group_ids" not in cluster:
                cluster["underlying_group_ids"] = []
            if "underlying_group_indices" not in cluster:
                cluster["underlying_group_indices"] = []

        # --- Step 6: Duplicate detection (first-cluster-wins) ---
        for cluster in clusters_data:
            if not isinstance(cluster, dict):
                continue
            underlying_ids = cluster.get("underlying_group_ids", [])
            if not isinstance(underlying_ids, list):
                continue

            # Remove any group_ids already claimed by an earlier cluster
            deduped_ids: List[str] = []
            deduped_indices: List[int] = []
            original_indices = cluster.get("underlying_group_indices", [])
            for i, gid in enumerate(underlying_ids):
                if gid in claimed_group_ids:
                    logger.warning(
                        "Duplicate group_id %s found across batches — "
                        "assigned to first occurrence",
                        gid,
                    )
                else:
                    deduped_ids.append(gid)
                    if i < len(original_indices):
                        deduped_indices.append(original_indices[i])
                    claimed_group_ids.add(gid)

            cluster["underlying_group_ids"] = deduped_ids
            cluster["underlying_group_indices"] = deduped_indices

            # If cluster was reduced to 0 or 1 group after dedup
            if len(deduped_ids) == 0:
                continue  # Skip empty cluster
            elif len(deduped_ids) == 1:
                # Demote to singleton
                gid = deduped_ids[0]
                idx = group_id_to_index.get(gid)
                if idx is not None and idx < len(groups):
                    batch_singletons.append(
                        _make_singleton_consolidated(
                            gid, idx, groups[idx],
                            reasoning=cluster.get("reasoning", ""),
                        )
                    )
                continue

            # Add to section clusters for cross-batch dedup later
            if section_key not in section_clusters:
                section_clusters[section_key] = []
            section_clusters[section_key].append((cluster, batch_index))

        # Process batch singletons
        for singleton in singletons_data:
            if not isinstance(singleton, dict):
                continue
            gid = singleton.get("group_id", "")
            if not gid:
                continue
            if gid in claimed_group_ids:
                logger.warning(
                    "Duplicate group_id %s found across batches — "
                    "assigned to first occurrence",
                    gid,
                )
                continue
            claimed_group_ids.add(gid)
            idx = group_id_to_index.get(gid)
            g_index = singleton.get(
                "group_index", idx if idx is not None else -1
            )
            if idx is not None and idx < len(groups):
                batch_singletons.append(
                    _make_singleton_consolidated(
                        gid, g_index, groups[idx],
                        reasoning=singleton.get("reasoning", ""),
                    )
                )

        # --- Missing group detection within this batch ---
        for gid in assigned_group_ids:
            if gid not in claimed_group_ids:
                idx = group_id_to_index.get(gid)
                if idx is not None and idx < len(groups):
                    batch_singletons.append(
                        _make_singleton_consolidated(
                            gid, idx, groups[idx],
                            reasoning=f"Missing from batch {batch_index} "
                            "output — added as singleton.",
                        )
                    )
                    claimed_group_ids.add(gid)

    # -------------------------------------------------------------------
    # Step 7 (global): Check that every input group_id is covered
    # -------------------------------------------------------------------
    uncovered = all_input_group_ids - claimed_group_ids
    if uncovered:
        logger.warning(
            "%d group(s) not covered by any consolidation batch — "
            "added as singletons",
            len(uncovered),
        )
        for gid in uncovered:
            idx = group_id_to_index.get(gid)
            if idx is not None and idx < len(groups):
                batch_singletons.append(
                    _make_singleton_consolidated(
                        gid, idx, groups[idx],
                        reasoning="Not covered by any consolidation batch "
                        "— added as singleton.",
                    )
                )
                claimed_group_ids.add(gid)

    # -------------------------------------------------------------------
    # Step 8: Cross-batch deduplication within each section
    # -------------------------------------------------------------------
    merged_clusters: List[Dict[str, Any]] = []

    for section_key, cluster_list in section_clusters.items():
        if len(cluster_list) <= 1:
            # Single cluster in section — no cross-batch dedup needed
            for cluster, _bi in cluster_list:
                merged_clusters.append(cluster)
            continue

        # Compare titles across all clusters in this section.
        # Track which list-positions have been merged into others.
        consumed: Set[int] = set()

        for i in range(len(cluster_list)):
            if i in consumed:
                continue
            cluster_i, _bi_i = cluster_list[i]

            for j in range(i + 1, len(cluster_list)):
                if j in consumed:
                    continue
                cluster_j, _bi_j = cluster_list[j]

                title_i = cluster_i.get("title", "")
                title_j = cluster_j.get("title", "")
                ratio = _word_overlap_ratio(title_i, title_j)

                if ratio >= 0.8:
                    # Merge cluster_j into cluster_i
                    logger.info(
                        "Cross-batch dedup: merging '%s' and '%s' "
                        "(overlap=%.2f) in section '%s'",
                        title_i,
                        title_j,
                        ratio,
                        section_key,
                    )
                    # Higher importance
                    cluster_i["importance"] = _highest_importance(
                        cluster_i.get("importance", "LOW"),
                        cluster_j.get("importance", "LOW"),
                    )
                    # Union of group_ids (preserving order, deduped)
                    ids_i = cluster_i.get("underlying_group_ids", [])
                    ids_j = cluster_j.get("underlying_group_ids", [])
                    merged_ids = list(dict.fromkeys(ids_i + ids_j))
                    cluster_i["underlying_group_ids"] = merged_ids

                    indices_i = cluster_i.get(
                        "underlying_group_indices", []
                    )
                    indices_j = cluster_j.get(
                        "underlying_group_indices", []
                    )
                    merged_indices = list(
                        dict.fromkeys(indices_i + indices_j)
                    )
                    cluster_i["underlying_group_indices"] = merged_indices

                    # Combined description
                    desc_i = cluster_i.get("description", "")
                    desc_j = cluster_j.get("description", "")
                    if desc_j and desc_j not in desc_i:
                        cluster_i["description"] = (
                            f"{desc_i} Additionally: {desc_j}"
                        )

                    # Combined reasoning
                    reason_i = cluster_i.get("reasoning", "")
                    reason_j = cluster_j.get("reasoning", "")
                    if reason_j and reason_j not in reason_i:
                        cluster_i["reasoning"] = (
                            f"{reason_i} {reason_j}".strip()
                        )

                    consumed.add(j)

            merged_clusters.append(cluster_i)

    # -------------------------------------------------------------------
    # Step 9: Type field validation for each merged cluster
    # -------------------------------------------------------------------
    for cluster in merged_clusters:
        underlying_ids = cluster.get("underlying_group_ids", [])
        expected_type = _resolve_type_for_group_ids(
            underlying_ids, groups, group_id_to_index
        )
        current_type = cluster.get("type", "clarification").lower()
        if TYPE_PRIORITY.get(current_type, 0) < TYPE_PRIORITY.get(
            expected_type, 0
        ):
            cluster["type"] = expected_type

    # -------------------------------------------------------------------
    # Step 10: Build partial_failures metadata
    # -------------------------------------------------------------------
    partial_failures: Dict[str, Any] = {
        "count": len(failed_batch_indices),
        "batches": failed_batch_indices,
        "fallback": "all_singletons",
    }

    # -------------------------------------------------------------------
    # Step 11: Add singleton sections from tasks_metadata
    # -------------------------------------------------------------------
    for section_key, indices in singleton_sections.items():
        for idx in indices:
            if idx < len(groups):
                gid = generate_group_id(groups[idx])
                # Only add if not already claimed (edge case safety)
                if gid not in claimed_group_ids:
                    batch_singletons.append(
                        _make_singleton_consolidated(
                            gid, idx, groups[idx],
                            reasoning="Singleton section — only group in "
                            "this section.",
                        )
                    )
                    claimed_group_ids.add(gid)

    # -------------------------------------------------------------------
    # Step 12: Build final consolidated groups list with IDs and indices
    # -------------------------------------------------------------------
    consolidated_groups: List[Dict[str, Any]] = []

    # Add merged clusters (non-singleton)
    for cluster in merged_clusters:
        underlying_ids = cluster.get("underlying_group_ids", [])
        underlying_indices = cluster.get("underlying_group_indices", [])

        # Compute model count and suggestion count from underlying groups
        model_set: Set[str] = set()
        suggestion_count = 0
        for gid in underlying_ids:
            idx = group_id_to_index.get(gid)
            if idx is not None and idx < len(groups):
                g = groups[idx]
                for m in g.get("models", []):
                    model_set.add(m)
                suggestion_count += len(g.get("suggestions", []))

        consolidated_groups.append({
            "consolidated_id": generate_consolidated_id(underlying_ids),
            "display_index": 0,  # Will be set below
            "title": cluster.get("title", "Untitled"),
            "description": cluster.get("description", ""),
            "importance": cluster.get("importance", "MEDIUM"),
            "reference": _get_reference_for_cluster(
                underlying_ids, groups, group_id_to_index
            ),
            "type": cluster.get("type", "clarification"),
            "underlying_group_indices": underlying_indices,
            "underlying_group_ids": underlying_ids,
            "model_count": len(model_set) or 1,
            "original_suggestion_count": suggestion_count or 1,
            "is_singleton": False,
            "reasoning": cluster.get("reasoning", ""),
        })

    # Add all singletons
    for singleton in batch_singletons:
        underlying_ids = singleton.get("underlying_group_ids", [])
        consolidated_groups.append({
            "consolidated_id": generate_consolidated_id(underlying_ids),
            "display_index": 0,  # Will be set below
            "title": singleton.get("title", "Untitled"),
            "description": singleton.get("description", ""),
            "importance": singleton.get("importance", "LOW"),
            "reference": singleton.get("reference", ""),
            "type": singleton.get("type", "clarification"),
            "underlying_group_indices": singleton.get(
                "underlying_group_indices", []
            ),
            "underlying_group_ids": underlying_ids,
            "model_count": singleton.get("model_count", 1),
            "original_suggestion_count": singleton.get(
                "original_suggestion_count", 1
            ),
            "is_singleton": True,
            "reasoning": singleton.get("reasoning", ""),
        })

    # Assign sequential display_index (1-based)
    for i, cg in enumerate(consolidated_groups, start=1):
        cg["display_index"] = i

    return consolidated_groups, partial_failures


# ---------------------------------------------------------------------------
# Output generation functions
# ---------------------------------------------------------------------------

def generate_consolidated_json(
    consolidated_groups: List[Dict[str, Any]],
    metadata: Dict[str, Any],
    phase_dir: str,
) -> str:
    """
    Write ``consolidated.json`` to *phase_dir* after schema validation.

    Handles the **<10% reduction** edge case: when
    ``(total_original - total_consolidated) / total_original < 0.1``,
    the ``skipped_report`` metadata flag is set to ``True``, any existing
    ``consolidated-report.md`` and ``consolidated-report.html`` are deleted,
    and an informational message is printed.

    Args:
        consolidated_groups: List of consolidated group dicts, each with
            ``consolidated_id``, ``display_index``, ``title``, etc.
        metadata: Metadata dict with ``schema_version``,
            ``total_original_groups``, ``total_consolidated``, and other
            fields required by the ``consolidated.schema.json`` schema.
        phase_dir: Path to the review-plan phase directory.

    Returns:
        The path (as a string) of the written ``consolidated.json`` file.

    Raises:
        ValueError: If the output fails schema validation.
    """
    # Lazy import to avoid circular imports at module level
    try:
        from .schema_validator import load_schema, validate_against_schema
    except ImportError:
        from utils.schema_validator import load_schema, validate_against_schema

    phase_path = Path(phase_dir)

    # --- <10% reduction check ---
    total_original = metadata.get("total_original_groups", 0)
    total_consolidated = metadata.get("total_consolidated", 0)

    if total_original > 0:
        reduction = (total_original - total_consolidated) / total_original
    else:
        reduction = 0.0

    if reduction < 0.1:
        metadata["skipped_report"] = True
        # Remove any stale consolidated reports from a previous run
        for report_name in ("consolidated-report.md", "consolidated-report.html"):
            report_file = phase_path / report_name
            if report_file.exists():
                report_file.unlink()
        print(
            "Consolidation found minimal overlap \u2014 report.md is already "
            "well-grouped."
        )
        print(
            "[CONSOLIDATION_SKIPPED] <10% reduction \u2014 previous "
            "consolidated reports removed."
        )

    # --- Build the output payload ---
    payload: Dict[str, Any] = {
        "format_version": CURRENT_FORMAT_VERSION,
        "consolidated_groups": consolidated_groups,
        "metadata": metadata,
    }

    # --- Validate against schema ---
    schema = load_schema("consolidated.schema.json")
    errors = validate_against_schema(payload, schema)
    if errors:
        raise ValueError(
            "consolidated.json failed schema validation:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )

    # --- Write ---
    phase_path.mkdir(parents=True, exist_ok=True)
    output_path = phase_path / "consolidated.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return str(output_path)


def generate_consolidated_report(
    consolidated_groups: List[Dict[str, Any]],
    groups: List[Dict[str, Any]],
    phase_dir: str,
    prefix: str,
    validation: Optional[List[Dict[str, Any]]] = None,
    phase_name: str = "review-plan",
) -> str:
    """
    Write ``consolidated-report.md`` to *phase_dir*.

    The report contains a header with consolidation statistics followed by
    one section per consolidated group. Each section includes skip/validation
    checkboxes, a metadata line, the consolidated description, and an
    expandable ``<details>`` block showing the original underlying
    suggestions.

    Args:
        consolidated_groups: List of consolidated group dicts (each with
            ``consolidated_id``, ``display_index``, ``title``, ``description``,
            ``importance``, ``reference``, ``underlying_group_indices``,
            ``underlying_group_ids``, ``model_count``, ``is_singleton``,
            ``original_suggestion_count``, ``reasoning``).
        groups: The original groups list from ``grouped.json``, used to
            look up underlying suggestion details.
        phase_dir: Path to the review-plan phase directory.
        prefix: The plan name / prefix used in the report header
            (e.g. ``my-feature``).

    Returns:
        The path (as a string) of the written ``consolidated-report.md``.
    """
    from datetime import datetime

    phase_path = Path(phase_dir)

    # --- Compute stats ---
    total_original = 0
    for cg in consolidated_groups:
        total_original += len(cg.get("underlying_group_indices", []))
    total_consolidated = len(consolidated_groups)
    merged_count = sum(
        1 for cg in consolidated_groups if not cg.get("is_singleton", True)
    )
    singleton_count = total_consolidated - merged_count

    if total_original > 0:
        reduction_pct = round(
            (total_original - total_consolidated) / total_original * 100, 1
        )
    else:
        reduction_pct = 0.0

    timestamp = datetime.now().isoformat()

    # --- Header ---
    phase_labels = {
        "review-plan": "Plan Review",
        "review-tasks": "Task Review",
        "code-review": "Code Review",
    }
    phase_label = phase_labels.get(phase_name, "Plan Review")

    lines: List[str] = []
    lines.append(f"# Consolidated {phase_label} Report: {prefix}")
    lines.append("")
    lines.append(f"**Original plan:** {prefix}.md")
    lines.append(f"**Generated:** {timestamp}")
    lines.append(
        f"**Consolidation:** {total_original} groups \u2192 "
        f"{total_consolidated} consolidated ({reduction_pct}% reduction)"
    )
    lines.append(
        f"**Breakdown:** {merged_count} merged + {singleton_count} singletons"
    )
    lines.append("")
    lines.append(
        "> This report consolidates related suggestion groups for faster review."
    )
    lines.append("> For the full per-suggestion view, see `report.md`.")
    lines.append(
        "> Skip decisions from both reports are combined when applying suggestions."
    )
    lines.append("")

    # --- Build validation lookups for per-group aggregate status ---
    # Mirrors the HTML consolidated path so the "Let the agent decide" checkbox can
    # be gated on a needs-human-decision aggregate status.
    from .html_report_generator import derive_aggregate_validation_status

    validation_by_hash: Dict[str, str] = {}
    validation_by_index: Dict[int, str] = {}
    if validation:
        for entry in validation:
            g_hash = entry.get("group_id") or entry.get("group_hash")
            if g_hash:
                validation_by_hash[g_hash] = entry.get("status", "")
            g_idx = entry.get("group_index")
            if g_idx is not None:
                validation_by_index[g_idx] = entry.get("status", "")

    # --- Per-group sections ---
    for cg in consolidated_groups:
        display_index = cg.get("display_index", 0)
        consolidated_id = cg.get("consolidated_id", "")
        title = cg.get("title", "Untitled")
        description = cg.get("description", "")
        importance = cg.get("importance", "MEDIUM")
        reference = cg.get("reference", "")
        model_count = cg.get("model_count", 1)
        underlying_indices = cg.get("underlying_group_indices", [])
        original_suggestion_count = cg.get("original_suggestion_count", 0)

        # Covers list — use display_label from stamped groups, fall back to positional
        covers_list = ", ".join(
            groups[idx].get("display_label", f"G{idx + 1}")
            if idx < len(groups) else f"G{idx + 1}"
            for idx in underlying_indices
        )

        # Section heading
        lines.append(
            f"## CG{display_index} [{consolidated_id}]: {title}"
        )

        # Aggregate validation status across the underlying groups (used to
        # gate the needs-human-decision-only "Let the agent decide" checkbox).
        underlying_statuses: List[str] = []
        for u_idx in underlying_indices:
            if u_idx < 0 or u_idx >= len(groups):
                continue
            g_hash = groups[u_idx].get("group_hash")
            status = (
                validation_by_hash.get(g_hash, "") if g_hash else ""
            ) or validation_by_index.get(u_idx, "")
            if status:
                underlying_statuses.append(status)
        agg_status = derive_aggregate_validation_status(underlying_statuses)

        # Checkboxes
        lines.append("- [ ] Skip this group")
        lines.append("- [ ] Mark valid")
        lines.append("- [ ] Mark invalid")
        lines.append("- [ ] Needs human attention")
        # "Let the agent decide" routes the consolidated group to the per-item
        # judge at apply time. Scoped to needs-human-decision only.
        if agg_status == "needs-human-decision":
            lines.append("- [ ] Let the agent decide")

        # Metadata line
        lines.append(
            f"**Importance:** {importance} | **Section:** {reference} "
            f"| **Models:** {model_count} | **Covers:** {covers_list}"
        )
        lines.append("")

        # Consolidated description
        lines.append(description)
        lines.append("")

        # --- Original suggestions details block ---
        underlying_group_count = len(underlying_indices)
        lines.append(
            f"<details>"
            f"<summary>Original suggestions "
            f"({original_suggestion_count} from "
            f"{underlying_group_count} groups)</summary>"
        )
        lines.append("")

        for u_idx in underlying_indices:
            if u_idx < 0 or u_idx >= len(groups):
                continue
            orig_group = groups[u_idx]
            theme = orig_group.get("theme", "Unknown")
            models_list = orig_group.get("models", [])
            models_str = ", ".join(models_list) if models_list else "unknown"

            g_label = orig_group.get("display_label", f"G{u_idx + 1}")
            lines.append(f"**{g_label}: {theme}** ({models_str})")

            for sugg in orig_group.get("suggestions", []):
                sugg_desc = sugg.get(
                    "description", sugg.get("desc", "")
                )
                lines.append(f"> {sugg_desc}")
                lines.append("")

        lines.append("</details>")
        lines.append("")
        lines.append("---")
        lines.append("")

    # --- Write ---
    phase_path.mkdir(parents=True, exist_ok=True)
    output_path = phase_path / "consolidated-report.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")

    return str(output_path)


def _failure_report_fields(phase_dir: str) -> Dict[str, Any]:
    """``failedModels``, ``requestedModels`` and ``notices`` for the consolidated page.

    The phase report's failure fields, read the same way a reaggregate reads
    them: the checkpoint's failures plus any requested model with neither a
    result nor a recorded failure (``remaining_failed_models``, against the
    ``models_completed`` a reaggregate reconciled with the files), the recorded
    requested set as the denominator, and the one warning notice whose
    ``message`` is ``report.md``'s ``**Models failed:**`` line without its bold
    markers. ``failedModels`` is always a dict (the template iterates it with
    ``Object.keys``); ``requestedModels`` is left out when the checkpoint
    records no requested set.

    Imported here rather than at module level: ``review_orchestrator_base``
    imports this package, and the consolidated page is generated long after
    both are loaded.
    """
    try:
        from .html_report_generator import build_report_notices
        from .review_orchestrator_base import (
            remaining_failed_models,
            salvage_requested_models,
        )
    except ImportError:
        from utils.html_report_generator import build_report_notices
        from utils.review_orchestrator_base import (
            remaining_failed_models,
            salvage_requested_models,
        )

    failures, requested = remaining_failed_models(str(phase_dir))
    requested_count = len(requested) if requested is not None else None
    fields: Dict[str, Any] = {
        "failedModels": failures,
        "notices": build_report_notices(
            [], failures, requested_count,
            salvage_requested_models(str(phase_dir), list(failures)),
        ),
    }
    if requested_count is not None:
        fields["requestedModels"] = requested_count
    return fields


def generate_consolidated_html(
    consolidated_groups: List[Dict[str, Any]],
    groups: List[Dict[str, Any]],
    phase_dir: str,
    plan_path: str,
    models: List[str],
    validation: Optional[List[Dict[str, Any]]] = None,
    phase_name: str = "review-plan",
    usage: Optional[Dict[str, Dict[str, Any]]] = None,
) -> str:
    """
    Write ``consolidated-report.html`` to *phase_dir*.

    Loads the template from ``templates/consolidated_report_template.html``,
    injects a JSON data payload via the ``REPORT_DATA_PLACEHOLDER`` pattern
    (replacing ``/* REPORT_DATA_PLACEHOLDER */null`` with the actual data),
    and writes the result.

    Args:
        consolidated_groups: List of consolidated group dicts.
        groups: The original groups list from ``grouped.json`` (for
            building the ``underlyingGroups`` array in the data payload).
        phase_dir: Path to the review-plan phase directory.
        plan_path: Path to the original plan file (used for title
            extraction and ``planPath`` in the data).
        models: List of model identifier strings that contributed
            suggestions.
        validation: Optional validation results list (from validation.json).
            When provided, validation status badges are shown for each
            underlying group and an aggregate status is computed for each
            consolidated group.
        usage: Optional per-model usage, ``{model_spec: {"input_tokens", ...,
            "cost_usd", "tool_uses"}}``, as the fan-out recorded it in
            ``.status.json`` and as ``recorded_usage()`` reads it back.  Stage
            U: the consolidated report is a second front page for the same run,
            so it names what the run spent the way the full report does — a
            clause on the badge of every model that reported, and the
            column-wise total in the header.  Omitted, or empty (the case for a
            fan-out of duration-only adapters), leaves both out of the payload
            entirely, which is what keeps the header from claiming a free run.

    Returns:
        The path (as a string) of the written ``consolidated-report.html``.

    Raises:
        FileNotFoundError: If the consolidated report template is missing.
        ValueError: If the template does not contain the data placeholder.
    """
    from datetime import datetime

    # Reuse helpers from html_report_generator
    try:
        from .html_report_generator import (
            get_model_metadata,
            derive_aggregate_validation_status,
            build_sort_config,
            sum_usage,
        )
        from .metrics import describe_usage
    except ImportError:
        from utils.html_report_generator import (
            get_model_metadata,
            derive_aggregate_validation_status,
            build_sort_config,
            sum_usage,
        )
        from utils.metrics import describe_usage

    phase_path = Path(phase_dir)
    plan_file = Path(plan_path)

    # --- Load template ---
    template_path = (
        Path(__file__).parent.parent
        / "templates"
        / "consolidated_report_template.html"
    )
    if not template_path.exists():
        raise FileNotFoundError(
            f"Consolidated report template not found at: {template_path}"
        )
    template = template_path.read_text(encoding="utf-8")

    # --- Extract plan title ---
    plan_title = ""
    if plan_file.exists():
        try:
            plan_content = plan_file.read_text(encoding="utf-8")
            for line in plan_content.splitlines():
                stripped = line.strip()
                if stripped.startswith("# "):
                    plan_title = stripped[2:].strip()
                    break
        except OSError:
            pass
    if not plan_title:
        plan_title = plan_file.stem

    # --- Build model metadata ---
    model_metadata: Dict[str, Any] = {}
    for model in models:
        model_metadata[model] = get_model_metadata(model)
        # Stage U, the shape `generate_html_report` builds: the numbers for
        # anything that wants to compute, and beside them the one clause
        # `describe_usage` renders, because the *text* is settled server-side
        # rather than separately in each template. A model the fan-out recorded
        # nothing for gets no key and no badge — never `$0.00`, which would
        # claim a free run.
        model_usage = (usage or {}).get(model)
        if isinstance(model_usage, dict) and model_usage:
            model_metadata[model]["usage"] = model_usage
            label = describe_usage(model_usage)
            if label:
                model_metadata[model]["usage_label"] = label

    # --- Build validation lookups ---
    # Primary: hash-based lookup (group_id/group_hash -> status info)
    # Fallback: index-based lookup (group_index -> status info)
    validation_by_hash: Dict[str, Dict[str, Any]] = {}
    validation_by_index: Dict[int, Dict[str, Any]] = {}
    if validation:
        for entry in validation:
            v_info = {
                "status": entry.get("status", ""),
                "reason": entry.get("reason", ""),
                "confidence": entry.get("confidence", 0.0),
            }
            # Hash-based key (primary)
            g_hash = entry.get("group_id") or entry.get("group_hash")
            if g_hash:
                validation_by_hash[g_hash] = v_info
            # Index-based key (fallback)
            g_idx = entry.get("group_index")
            if g_idx is not None:
                validation_by_index[g_idx] = v_info

    # --- Build consolidatedGroups payload ---
    cg_data: List[Dict[str, Any]] = []
    for cg in consolidated_groups:
        underlying_indices = cg.get("underlying_group_indices", [])
        # Covers list — use display_label from stamped groups, fall back to positional
        covers_list = ", ".join(
            groups[idx].get("display_label", f"G{idx + 1}")
            if idx < len(groups) else f"G{idx + 1}"
            for idx in underlying_indices
        )

        # Build underlyingGroups array
        underlying_groups_data: List[Dict[str, Any]] = []
        underlying_statuses: List[str] = []
        for u_idx in underlying_indices:
            if u_idx < 0 or u_idx >= len(groups):
                continue
            orig_group = groups[u_idx]
            suggs: List[Dict[str, Any]] = []
            for s_idx, sugg in enumerate(
                orig_group.get("suggestions", []), start=1
            ):
                # Use suggestion_hash as primary ID, fall back to positional
                sugg_id = sugg.get(
                    "suggestion_hash", f"G{u_idx + 1}S{s_idx}"
                )
                suggs.append({
                    "id": sugg_id,
                    "title": sugg.get("title", "Untitled"),
                    "description": sugg.get(
                        "description", sugg.get("desc", "")
                    ),
                    "importance": sugg.get(
                        "importance", "MEDIUM"
                    ).upper(),
                    "model": sugg.get("source_model", "unknown"),
                })

            # Attach validation info — hash-based lookup primary, index fallback
            g_hash = orig_group.get("group_hash")
            v_info = (
                validation_by_hash.get(g_hash, {}) if g_hash
                else {}
            ) or validation_by_index.get(u_idx, {})
            ug_entry: Dict[str, Any] = {
                "groupIndex": u_idx + 1,
                "groupHash": orig_group.get("group_hash"),
                "theme": orig_group.get("theme", "Unknown"),
                "models": orig_group.get("models", []),
                "suggestions": suggs,
            }
            if v_info:
                ug_entry["validationStatus"] = v_info["status"]
                ug_entry["validationReason"] = v_info["reason"]
                ug_entry["validationConfidence"] = v_info["confidence"]
                underlying_statuses.append(v_info["status"])

            underlying_groups_data.append(ug_entry)

        # Compute aggregate validation status using canonical VALIDATION_ORDER
        agg_status = derive_aggregate_validation_status(underlying_statuses)

        cg_entry: Dict[str, Any] = {
            "consolidatedId": cg.get("consolidated_id", ""),
            "displayIndex": cg.get("display_index", 0),
            "title": cg.get("title", ""),
            "description": cg.get("description", ""),
            "importance": cg.get("importance", "MEDIUM"),
            "reference": cg.get("reference", ""),
            "type": cg.get("type", "modification"),
            "isSingleton": cg.get("is_singleton", True),
            "modelCount": cg.get("model_count", 1),
            "coversList": covers_list,
            "reasoning": cg.get("reasoning", ""),
            "underlyingGroups": underlying_groups_data,
        }
        if agg_status:
            cg_entry["validationStatus"] = agg_status
        cg_data.append(cg_entry)

    # --- Compute summary stats ---
    total_original = sum(
        len(cg.get("underlying_group_indices", []))
        for cg in consolidated_groups
    )
    total_consolidated = len(consolidated_groups)
    merged_count = sum(
        1 for cg in consolidated_groups
        if not cg.get("is_singleton", True)
    )
    singleton_count = total_consolidated - merged_count

    # --- Assemble full report data ---
    report_data: Dict[str, Any] = {
        "planPath": str(plan_path),
        "planTitle": plan_title,
        "phase": phase_name,
        "generatedAt": datetime.now().isoformat(),
        "models": models,
        "modelMetadata": model_metadata,
        "consolidatedGroups": cg_data,
        "sortConfig": build_sort_config(),
        "fullReportPath": "report.html",
        "summary": {
            "totalOriginal": total_original,
            "totalConsolidated": total_consolidated,
            "mergedCount": merged_count,
            "singletonCount": singleton_count,
        },
    }

    # Stage U: the run total, added only when some adapter reported
    # something. `sum_usage` totals whichever models reported, including slots
    # that failed and so carry no badge here — the header answers "what did
    # this run cost", not "what do these badges add up to".
    usage_total = sum_usage(usage)
    if usage_total:
        report_data["usageTotal"] = usage_total
        total_label = describe_usage(usage_total)
        if total_label:
            report_data["usageTotalLabel"] = total_label

    # Decision 11.12: the consolidated page is a second front page for the
    # same run, so a reviewer that produced nothing is named here as it is on
    # report.html — the same failure map, denominator and warning notice.
    report_data.update(_failure_report_fields(phase_dir))

    # --- Inject data into template ---
    json_payload = json.dumps(report_data, indent=2)

    # Escape </script> sequences to prevent premature script tag closure
    json_payload = json_payload.replace("</", "<\\/")

    if "/* REPORT_DATA_PLACEHOLDER */null" in template:
        html = template.replace(
            "/* REPORT_DATA_PLACEHOLDER */null", json_payload
        )
    elif "/* REPORT_DATA_PLACEHOLDER */" in template:
        html = template.replace(
            "/* REPORT_DATA_PLACEHOLDER */", json_payload
        )
    elif "REPORT_DATA_PLACEHOLDER" in template:
        html = template.replace("REPORT_DATA_PLACEHOLDER", json_payload)
    else:
        raise ValueError(
            "Template does not contain REPORT_DATA_PLACEHOLDER \u2014 "
            "cannot inject report data."
        )

    # --- Write ---
    phase_path.mkdir(parents=True, exist_ok=True)
    output_path = phase_path / "consolidated-report.html"
    output_path.write_text(html, encoding="utf-8")

    return str(output_path)


# ---------------------------------------------------------------------------
# File hashing helpers
# ---------------------------------------------------------------------------

def _compute_file_hash(file_path: str) -> str:
    """
    Compute a SHA-256 hash of a file's contents for staleness detection.

    Reads the file as UTF-8 text and returns the full hex digest.
    Returns an empty string if the file does not exist or cannot be read.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Full SHA-256 hex digest string, or empty string on error.
    """
    try:
        content = Path(file_path).read_text(encoding="utf-8")
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return ""


def consolidation_is_current(phase_dir: str) -> bool:
    """Whether ``consolidated.json`` in *phase_dir* was built from today's
    ``grouped.json``: the consolidation already ran on these groups.

    The staleness rule :func:`load_merged_suggestions` applies, read the
    same way: the file's ``metadata.grouped_hash`` against the hash of the
    ``grouped.json`` beside it. A minimal-reduction pass
    (``skipped_report``) counts too: it ran, and found little to merge.
    ``False`` when the file is missing, unreadable, carries no hash, or the
    groups changed since (a later review round rewrote ``grouped.json``).

    Live run 8 (Claude Code racing 01): ``status`` and its result line still
    said "consolidation recommended: 17 valid groups >= 15 — run
    --consolidate" after the same run had consolidated them, so every
    reader of the recommendation asks this first.
    """
    path = Path(phase_dir) / "consolidated.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    metadata = data.get("metadata") if isinstance(data, dict) else None
    stored = metadata.get("grouped_hash") if isinstance(metadata, dict) else None
    if not isinstance(stored, str) or not stored:
        return False
    return stored == _compute_file_hash(str(Path(phase_dir) / "grouped.json"))


# ---------------------------------------------------------------------------
# Consolidated decision loading for apply-suggestions
# ---------------------------------------------------------------------------

def load_merged_suggestions(
    phase_dir: str,
    groups: List[Dict[str, Any]],
    plan_file: str,
    accept_stale: bool = False,
) -> Tuple[Set[int], Dict[int, str]]:
    """
    Load consolidated decisions and map them to group-level indices.

    Reads consolidated.json, consolidated-report.md, and
    consolidated_user_selections.json from the phase directory. Validates
    staleness via plan_hash and grouped_hash, then merges C-level skip and
    validation override decisions from both markdown and HTML sources.
    Returns the decisions mapped to 0-based group indices for the caller
    (apply_suggestions_orchestrator) to merge with G-level decisions.

    Args:
        phase_dir: Path to the review-plan directory (contains consolidated.json).
        groups: Full list of suggestion group dicts from grouped.json.
        plan_file: Path to the plan file.
        accept_stale: If True, downgrade grouped_hash mismatch from
            fail-closed to warn-and-apply.

    Returns:
        A tuple of:
        - skipped_group_indices: Set of 0-based group indices to skip
          (from C-level decisions).
        - validation_overrides: Dict mapping 0-based group index to
          override status string (from C-level decisions).
    """
    phase_path = Path(phase_dir)
    empty_result: Tuple[Set[int], Dict[int, str]] = (set(), {})

    # ------------------------------------------------------------------
    # Step 0: Check if consolidated.json exists; load it
    # ------------------------------------------------------------------
    consolidated_path = phase_path / "consolidated.json"
    if not consolidated_path.exists():
        return empty_result

    try:
        consolidated_data = json.loads(
            consolidated_path.read_text(encoding="utf-8")
        )
    except (json.JSONDecodeError, OSError) as exc:
        logger.error(
            "Failed to load consolidated.json: %s", exc,
        )
        return empty_result

    metadata = consolidated_data.get("metadata", {})

    # If consolidation ran but found minimal benefit, nothing to apply
    if metadata.get("skipped_report", False):
        return empty_result

    # ------------------------------------------------------------------
    # Step 1: Staleness validation
    # ------------------------------------------------------------------
    stored_plan_hash = metadata.get("plan_hash")
    stored_grouped_hash = metadata.get("grouped_hash")

    current_plan_hash = _compute_file_hash(plan_file)
    grouped_json_path = phase_path / "grouped.json"
    current_grouped_hash = _compute_file_hash(str(grouped_json_path))

    # Check if hash fields are present (backward compat)
    if stored_plan_hash is None or stored_grouped_hash is None:
        logger.warning(
            "Consolidated data missing hash fields — staleness cannot be "
            "verified. Consider re-running --consolidate."
        )
        # Continue with decisions applied (backward compatibility)
    else:
        grouped_mismatch = stored_grouped_hash != current_grouped_hash
        plan_mismatch = stored_plan_hash != current_plan_hash

        if grouped_mismatch and not accept_stale:
            logger.error(
                "Consolidated decisions are stale (grouped.json has changed "
                "since consolidation). Ignoring all consolidated decisions. "
                "Run --consolidate to refresh, or pass "
                "--accept-stale-consolidation to override."
            )
            return empty_result

        if grouped_mismatch and accept_stale:
            logger.warning(
                "Consolidated decisions are stale (grouped.json has changed "
                "since consolidation). Applying anyway due to "
                "--accept-stale-consolidation."
            )

        if plan_mismatch and not grouped_mismatch:
            logger.warning(
                "Consolidated decisions may be stale (plan has changed since "
                "consolidation). Run --consolidate to refresh."
            )

    # ------------------------------------------------------------------
    # Step 2: Load C-level decisions from both sources
    # ------------------------------------------------------------------
    report_path = phase_path / "consolidated-report.md"
    md_skipped: Set[str] = parse_consolidated_skipped_groups(str(report_path))
    md_overrides: Dict[str, str] = parse_consolidated_validation_overrides(
        str(report_path)
    )

    html_selections = load_consolidated_html_selections(phase_path, groups=groups, plan_path=plan_file)

    merged_skipped_cids, merged_override_cids = merge_consolidated_selections(
        html_selections, md_skipped, md_overrides
    )

    # If no C-level decisions at all, short-circuit
    if not merged_skipped_cids and not merged_override_cids:
        return empty_result

    # ------------------------------------------------------------------
    # Step 3: Build consolidated_id → list of underlying group indices
    # ------------------------------------------------------------------
    # First, build a group_id → group index (0-based) mapping
    group_id_to_indices: Dict[str, List[int]] = {}
    for idx, group in enumerate(groups):
        gid = generate_group_id(group)
        if gid not in group_id_to_indices:
            group_id_to_indices[gid] = []
        group_id_to_indices[gid].append(idx)

    # Build consolidated_id → list of 0-based group indices
    consolidated_groups_list = consolidated_data.get("consolidated_groups", [])
    cid_to_group_indices: Dict[str, List[int]] = {}

    for cgroup in consolidated_groups_list:
        cid = cgroup.get("consolidated_id", "")
        underlying_gids = cgroup.get("underlying_group_ids", [])
        resolved_indices: List[int] = []
        for gid in underlying_gids:
            if gid in group_id_to_indices:
                resolved_indices.extend(group_id_to_indices[gid])
            else:
                logger.warning(
                    "Consolidated group %s references underlying group_id %s "
                    "which could not be resolved to a current group index.",
                    cid, gid,
                )
        if resolved_indices:
            cid_to_group_indices[cid] = resolved_indices

    # Log summary of unresolvable IDs
    unresolvable_count = 0
    for cgroup in consolidated_groups_list:
        cid = cgroup.get("consolidated_id", "")
        for gid in cgroup.get("underlying_group_ids", []):
            if gid not in group_id_to_indices:
                unresolvable_count += 1
    if unresolvable_count > 0:
        logger.warning(
            "%d consolidated decision(s) could not be mapped to current "
            "groups (stale consolidation?). Run --consolidate to refresh.",
            unresolvable_count,
        )

    # ------------------------------------------------------------------
    # Step 3 (cont.): Map C-level skips to G-level group indices
    # ------------------------------------------------------------------
    skipped_group_indices: Set[int] = set()
    for cid in merged_skipped_cids:
        if cid in cid_to_group_indices:
            skipped_group_indices.update(cid_to_group_indices[cid])
        else:
            logger.warning(
                "Skipped consolidated_id %s could not be resolved to any "
                "group indices.",
                cid,
            )

    # ------------------------------------------------------------------
    # Step 4: Map C-level validation overrides to G-level
    # ------------------------------------------------------------------
    validation_overrides: Dict[int, str] = {}
    for cid, override_status in merged_override_cids.items():
        if cid in cid_to_group_indices:
            for group_idx in cid_to_group_indices[cid]:
                # Only apply if the group index doesn't already have a
                # C-level override from an earlier consolidated group
                # (first-cluster-wins for the edge case of duplicate
                # assignment).
                if group_idx not in validation_overrides:
                    validation_overrides[group_idx] = override_status
        else:
            logger.warning(
                "Override for consolidated_id %s could not be resolved to "
                "any group indices.",
                cid,
            )

    # ------------------------------------------------------------------
    # Step 5: Return
    # ------------------------------------------------------------------
    return (skipped_group_indices, validation_overrides)
