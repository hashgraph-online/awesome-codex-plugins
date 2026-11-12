#!/usr/bin/env python3
"""
Consolidation utility for clustering related suggestion groups.

Provides core functions for the post-validation consolidation step that
clusters related suggestion groups by plan section and generates
consolidated suggestions preserving nuance from all underlying suggestions.
"""

import copy
import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Import state_manager's generate_group_id for reference (both coexist)
# Also import CURRENT_FORMAT_VERSION and load_groups_payload for v2 envelope support
from .state_manager import (
    stamped_group_id as _stamped_group_id,
    CURRENT_FORMAT_VERSION,
)

# Import report_parser functions for consolidated decision loading
from . import report_markdown as _rm
from .report_parser import (
    parse_consolidated_skipped_groups,
    parse_consolidated_validation_overrides,
    load_consolidated_html_selections,
    merge_consolidated_selections,
)

from . import cli_common
from .prompt_loader import load_prompt
from .schema_validator import load_schema, validate_against_schema
from .subagent_prompts import build_consolidation_prompt
from .subagent_tasks import PromptBudget, build_inputs, make_task, make_task_file

logger = logging.getLogger(__name__)

from . import scope_report as _scope_report
# Whether the consolidation is current, and the file hash it compares, live in
# output_handler, where the run record reads them; re-exported for reading.
from .output_handler import _compute_file_hash, consolidation_is_current  # noqa: F401
from . import importance as _importance
from . import validation
from .validation import host_views_lock, invalidate_host_index, refresh_host_index
from .html_report_generator import (
    derive_aggregate_validation_status,
    build_report_notices,
    CONSOLIDATED_REPORT_DATA,
    build_sort_config,
    embed_report_data,
    load_report_template,
    sidecar_json,
    sum_usage,
)
from .review_orchestrator_base import remaining_failed_models, salvage_requested_models
from .metrics import describe_usage
from .report_view import build_model_metadata, plan_title, read_plan


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

# Character budget for one group's content (theme + suggestion texts): a solo
# batch's group above it has its suggestion texts truncated in the prompt.
CONSOLIDATION_CHAR_BUDGET = 12000

#: The content budget batch formation applies: none, so batches are cut by
#: count alone, in priority order, as every recorded consolidation ran.
#: Splitting on ``CONSOLIDATION_CHAR_BUDGET`` (or by section) gives more,
#: smaller batches and fewer merges, and waits on the decision in
#: docs/development/review-results.md ("Consolidation batches").
CONSOLIDATION_BATCH_CHAR_BUDGET: Optional[int] = None


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
    is used by the consolidation pipeline for group identity tracking. Same-
    content groups share it, so ids are assigned through
    :func:`consolidation_group_ids`, never by calling this per group.

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


def consolidation_group_ids(groups: List[Dict[str, Any]]) -> List[str]:
    """Each group's consolidation id, one per group and no two alike.

    The first group with a given :func:`generate_group_id` keeps it, so an
    ordinary group's id is that content hash. Same-content groups (the hash
    reads only the theme and the titles) each get their own: one derived from
    the group's stamped ``group_hash`` (``state_manager.stamped_group_id``).
    Every writer and reader of consolidation ids goes through this, never
    through :func:`generate_group_id` alone (docs/development/review-results.md,
    "Consolidation batches").
    """
    ids: List[str] = []
    taken: Set[str] = set()
    for group in groups:
        gid = generate_group_id(group)
        if gid in taken:
            seed = f"{gid}\x00{_stamped_group_id(group)}"
            for n in range(len(taken) + 1):
                gid = hashlib.sha256(f"{seed}\x00{n}".encode()).hexdigest()[:12]
                if gid not in taken:
                    break
            else:  # pragma: no cover - the truncated hash itself repeated
                raise ValueError(f"Cannot give group {len(ids) + 1} a consolidation id")
        taken.add(gid)
        ids.append(gid)
    return ids


#: ``consolidated.json``'s ``group_id_format``: every ``underlying_group_ids``
#: entry is one group's own id (:func:`consolidation_group_ids`). A file
#: without it was written when same-content groups shared one id
#: (:func:`_decision_join`).
GROUP_ID_FORMAT = "distinct"


def _batch_id_map(
    batch_info: Dict[str, Any],
    ids: List[str],
    plain_ids: List[str],
    id_to_index: Dict[str, int],
) -> Dict[str, List[str]]:
    """A batch's ids as its prompt gave them -> the own ids of the groups
    each names: the only ids a reply to that batch may name.

    The task file is the trusted source: each listed id is read through the
    ``group_indices`` entry beside it. A task file written before same-content
    groups had ids of their own listed each copy under the plain id, so that
    id names the copies the batch was given, never a copy it was not. A
    listed id its index does not match (``grouped.json`` changed since) names
    the group it is the id of.
    """
    listed = batch_info.get("group_ids") or []
    indices = batch_info.get("group_indices") or []
    mapping: Dict[str, List[str]] = {}
    for position, gid in enumerate(listed):
        if not isinstance(gid, str):
            continue
        idx = indices[position] if position < len(indices) else None
        if (isinstance(idx, int) and not isinstance(idx, bool)
                and 0 <= idx < len(ids) and gid in (ids[idx], plain_ids[idx])):
            own = ids[idx]
        elif gid in id_to_index:
            own = gid
        else:
            continue
        named = mapping.setdefault(gid, [])
        if own not in named:
            named.append(own)
    return mapping


def _decision_join(
    groups: List[Dict[str, Any]], distinct: bool,
) -> Dict[str, List[int]]:
    """Consolidation id -> the group indices a decision filed under it covers.

    A ``consolidated.json`` that records :data:`GROUP_ID_FORMAT` (*distinct*)
    names each group by its own id. One without it was written when
    same-content groups shared the plain :func:`generate_group_id`, so that
    id covers every copy, as it did when the decision was made.
    """
    ids = (consolidation_group_ids(groups) if distinct
           else [generate_group_id(group) for group in groups])
    join: Dict[str, List[int]] = {}
    for idx, gid in enumerate(ids):
        join.setdefault(gid, []).append(idx)
    return join


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
        # A group record carries no ``reference`` (``SuggestionGroup.to_dict``
        # writes none), so every group lands in ``_uncategorized``: one
        # section. Deriving sections from the members is an open decision
        # (docs/development/review-results.md, "Consolidation batches").
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

def _suggestion_text_key(suggestion: Dict[str, Any]) -> str:
    """The key a suggestion's text is under: ``desc``, the field reviewers
    answer in (``schemas/review_suggestions.schema.json``), else the older
    ``description``."""
    return "desc" if suggestion.get("desc") else "description"


def _suggestion_text(suggestion: Dict[str, Any]) -> str:
    """A suggestion's text (:func:`_suggestion_text_key`), ``""`` when absent."""
    return str(suggestion.get(_suggestion_text_key(suggestion)) or "")


def _measure_group_content_length(group: Dict[str, Any]) -> int:
    """
    Measure the character length of a group's content for budget purposes.

    Counts the theme length plus all suggestion text lengths within
    the group. This corresponds to the content that will appear in the
    consolidation prompt for this group.

    Args:
        group: A suggestion group dict with ``theme`` and ``suggestions``.

    Returns:
        Total character count of theme + all suggestion texts.
    """
    length = len(group.get("theme", ""))
    for suggestion in group.get("suggestions", []):
        length += len(_suggestion_text(suggestion))
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

    truncated = copy.deepcopy(group)
    # Truncate each suggestion text proportionally, under the key it came from
    for suggestion in truncated.get("suggestions", []):
        key = _suggestion_text_key(suggestion)
        desc = _suggestion_text(suggestion)
        if len(desc) <= 100:
            # Too short to meaningfully truncate
            continue
        # Keep first 20% and last 20%, replace middle with marker
        keep_chars = max(20, int(len(desc) * 0.2))
        suggestion[key] = (
            desc[:keep_chars] + " [...truncated...] " + desc[-keep_chars:]
        )
    return truncated


def _split_into_budget_batches(
    group_indices: List[int],
    groups: List[Dict[str, Any]],
    max_per_batch: int,
    char_budget: Optional[int],
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
        char_budget: Maximum combined content characters per batch; ``None``
            cuts by count alone (``CONSOLIDATION_BATCH_CHAR_BUDGET``).

    Returns:
        A list of sub-batches, where each sub-batch is a list of group indices.
    """
    if char_budget is None:
        step = max(1, max_per_batch)
        return [
            list(group_indices[start:start + step])
            for start in range(0, len(group_indices), step)
        ]

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
            # A group has no importance field: its members' highest
            # (docs/development/review-results.md, "Importance levels").
            "importance": _importance.group_importance(group),
            # Neither is a group field either; both stay inert with the
            # sections (docs/development/review-results.md, "Consolidation
            # batches").
            "type": group.get("type", "unknown"),
            "reference": group.get("reference", ""),
            "suggestions": [
                {
                    "title": s.get("title", ""),
                    "description": _suggestion_text(s),
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
    follows the same structural pattern as ``materialize_validation_round()``
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

    # One views transaction: the old index goes, the sidecars and the task file
    # are written, and the index is rebuilt from that file
    # (docs/development/delegation.md#the-host-index). The lock file lives in
    # the phase dir, so the dir exists first.
    Path(phase_dir).mkdir(parents=True, exist_ok=True)
    with host_views_lock(phase_dir):
        return _prepare_consolidation_tasks(
            groups, section_groups, phase_dir, plan_file, prompt_budget,
        )


def _prepare_consolidation_tasks(
    groups: List[Dict[str, Any]],
    section_groups: Dict[str, List[int]],
    phase_dir: str,
    plan_file: str,
    prompt_budget: Optional[PromptBudget],
) -> Dict[str, Any]:
    """:func:`prepare_consolidation_tasks`, inside the phase's views lock."""

    phase_path = Path(phase_dir)
    tasks_path = phase_path / "consolidation_tasks.json"
    # The host index describes the task file this call replaces: it goes before
    # a sidecar changes, and is rebuilt from the file once that is written
    # (docs/development/delegation.md#the-host-index).
    invalidate_host_index(str(tasks_path))

    # Pre-compute group_ids for all groups
    group_ids = consolidation_group_ids(groups)

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
            # Section fits in one batch (a content budget would split it)
            sub_batches = _split_into_budget_batches(
                indices, groups, len(indices), CONSOLIDATION_BATCH_CHAR_BUDGET
            )
        else:
            # Large section — split into sub-batches
            sub_batches = _split_into_budget_batches(
                indices,
                groups,
                MAX_GROUPS_PER_CONSOLIDATION_BATCH,
                CONSOLIDATION_BATCH_CHAR_BUDGET,
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
                # (and CONSOLIDATION_BATCH_CHAR_BUDGET, when set), so an
                # over-budget prompt here means the runner's transport is the
                # constraint. Fail loudly with the fix; never truncate the
                # instruction tail.
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
    validation.write_prompt_sidecars(
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
    tasks_path.parent.mkdir(parents=True, exist_ok=True)
    with open(tasks_path, "w", encoding="utf-8") as f:
        json.dump(tasks_metadata, f, indent=2)
    refresh_host_index(str(tasks_path))

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

    HIGH > MEDIUM > LOW, in either case (``utils/importance.py``).
    Unrecognized values are treated as lowest priority.

    Args:
        *importance_values: One or more importance level strings.

    Returns:
        The highest importance level string.
    """
    return _importance.highest(importance_values, default="LOW")


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


def _consolidated_entry(
    underlying_ids: List[str],
    underlying_indices: List[int],
    *,
    title: Any,
    description: Any,
    importance: Any,
    reference: Any,
    type_: Any,
    model_count: int,
    suggestion_count: int,
    is_singleton: bool,
    reasoning: Any,
) -> Dict[str, Any]:
    """One ``consolidated.json`` entry; ``display_index`` is set by the merge."""
    return {
        "consolidated_id": generate_consolidated_id(underlying_ids),
        "display_index": 0,
        "title": title,
        "description": description,
        "importance": importance,
        "reference": reference,
        "type": type_,
        "underlying_group_indices": underlying_indices,
        "underlying_group_ids": underlying_ids,
        "model_count": model_count,
        "original_suggestion_count": suggestion_count,
        "is_singleton": is_singleton,
        "reasoning": reasoning,
    }


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

    return _consolidated_entry(
        [group_id], [group_index],
        title=group.get("theme", "Untitled"),
        description=group.get("theme", ""),
        # A group has no importance field: its members' highest
        # (docs/development/review-results.md, "Importance levels").
        importance=_importance.group_importance(group),
        reference=group.get("reference", ""),
        type_=group_type,
        model_count=len(group.get("models", [])) or 1,
        suggestion_count=len(group.get("suggestions", [])) or 1,
        is_singleton=True,
        reasoning=reasoning or "Singleton group — no related groups to merge.",
    )


def _reply_group_ids(
    batch_map: Dict[str, List[str]], reply_id: Any, batch_index: Any,
) -> List[str]:
    """The batch's groups a reply's id names (:func:`_batch_id_map`); none
    for an id the batch was not given: a guess, a typo, another batch's
    group, or not a string at all."""
    named = batch_map.get(reply_id) if isinstance(reply_id, str) else None
    if not named:
        logger.warning(
            "Consolidation batch %s names group_id %r, which is not one of "
            "its groups — ignored",
            batch_index, reply_id,
        )
        return []
    return named


@dataclass(frozen=True)
class _BatchFailure:
    """A batch reply the merge cannot read; *reason* starts its groups'
    singleton reasoning."""

    reason: str


def _read_batch(
    batch_file: Path, batch_index: int, assigned: int,
) -> Union[Tuple[List[Any], List[Any]], _BatchFailure]:
    """A batch reply's ``(clusters, singletons)`` lists, or why it is unusable.

    Unusable: no file, not JSON, not an object, an ``error`` reply (its own
    ``groups`` list is never read), or neither list present. Each is logged
    with the number of *assigned* groups that become singletons.
    """
    if not batch_file.exists():
        logger.warning(
            "Consolidation batch file not found: %s — treating %d "
            "groups as singletons",
            batch_file, assigned,
        )
        return _BatchFailure(f"Batch {batch_index} file missing")
    try:
        with open(batch_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as exc:
        logger.warning(
            "Consolidation batch %d has invalid JSON (%s) — treating "
            "%d groups as singletons",
            batch_index, exc, assigned,
        )
        return _BatchFailure(f"Batch {batch_index} invalid JSON")
    if not isinstance(data, dict):
        logger.warning(
            "Consolidation batch %d is not a JSON object — treating "
            "%d groups as singletons",
            batch_index, assigned,
        )
        return _BatchFailure(f"Batch {batch_index} unexpected format")
    if "error" in data:
        logger.warning(
            "Consolidation batch %d reported error '%s' — treating "
            "%d groups as singletons",
            batch_index, data.get("error", "unknown"), assigned,
        )
        return _BatchFailure(f"Batch {batch_index} error fallback")
    clusters, singletons = data.get("clusters"), data.get("singletons")
    if not isinstance(clusters, list) and not isinstance(singletons, list):
        logger.warning(
            "Consolidation batch %d missing both 'clusters' and "
            "'singletons' keys — treating %d groups as singletons. "
            "Errors: missing required keys",
            batch_index, assigned,
        )
        return _BatchFailure(f"Batch {batch_index} schema validation failed")
    return (
        clusters if isinstance(clusters, list) else [],
        singletons if isinstance(singletons, list) else [],
    )


def _fill_cluster_defaults(cluster: Dict[str, Any]) -> None:
    """Give a reply's cluster the optional fields it left out, in place."""
    cluster.setdefault("reasoning", "")
    cluster.setdefault("description", cluster.get("title", ""))
    cluster["importance"] = _importance.normalize(cluster.get("importance"))
    cluster.setdefault("type", "clarification")
    cluster.setdefault("title", "Untitled cluster")


def _warn_duplicate(gid: str) -> None:
    logger.warning(
        "Duplicate group_id %s found across batches — assigned to first "
        "occurrence",
        gid,
    )


class _Claims:
    """Which groups an entry already shows, and the singleton entries made.

    Every index comes from a group's own id, never from a reply's
    ``underlying_group_indices`` or ``group_index``, so the decision join
    (ids) and the pages (indices) show the same groups.
    """

    def __init__(self, groups: List[Dict[str, Any]]) -> None:
        self.groups = groups
        self.ids = consolidation_group_ids(groups)
        self.index: Dict[str, int] = {gid: idx for idx, gid in enumerate(self.ids)}
        self.claimed: Set[str] = set()
        self.singletons: List[Dict[str, Any]] = []

    def singleton(self, gid: str, reasoning: str) -> None:
        """Show *gid* alone, unless an entry already shows it."""
        if gid in self.claimed:
            return
        self.claimed.add(gid)
        idx = self.index[gid]
        self.singletons.append(
            _make_singleton_consolidated(gid, idx, self.groups[idx], reasoning=reasoning)
        )

    def cluster_ids(
        self, cluster: Dict[str, Any], batch_map: Dict[str, List[str]], batch_index: Any,
    ) -> Optional[List[str]]:
        """The batch's groups *cluster* names that no earlier entry shows
        (first cluster wins); ``None`` when its ids are not a list. Claims
        nothing."""
        reply_ids = cluster.get("underlying_group_ids", [])
        if not isinstance(reply_ids, list):
            return None
        kept: List[str] = []
        for reply_id in reply_ids:
            for gid in _reply_group_ids(batch_map, reply_id, batch_index):
                if gid in self.claimed:
                    _warn_duplicate(gid)
                elif gid not in kept:
                    kept.append(gid)
        return kept


def _merge_batch(
    claims: _Claims,
    batch_index: Any,
    batch_map: Dict[str, List[str]],
    clusters: List[Any],
    singletons: List[Any],
) -> List[Dict[str, Any]]:
    """Claim one batch reply's groups; return its clusters of two or more.

    A cluster is what is left of it after the id checks: nothing, one group
    (shown as a singleton with the cluster's reasoning) or a cluster. A
    reply singleton is read by its id; its ``group_index`` is a position the
    model copied and may get wrong.
    """
    for cluster in clusters:
        if isinstance(cluster, dict):
            _fill_cluster_defaults(cluster)
    kept_clusters: List[Dict[str, Any]] = []
    for cluster in clusters:
        if not isinstance(cluster, dict):
            continue
        ids = claims.cluster_ids(cluster, batch_map, batch_index)
        if not ids:
            continue
        if len(ids) == 1:
            claims.singleton(ids[0], cluster.get("reasoning", ""))
            continue
        claims.claimed.update(ids)
        cluster["underlying_group_ids"] = ids
        kept_clusters.append(cluster)
    for singleton in singletons:
        if not isinstance(singleton, dict) or not singleton.get("group_id", ""):
            continue
        for gid in _reply_group_ids(batch_map, singleton["group_id"], batch_index):
            if gid in claims.claimed:
                _warn_duplicate(gid)
            else:
                claims.singleton(gid, singleton.get("reasoning", ""))
    return kept_clusters


def _merge_similar_clusters(
    section_clusters: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """One section's clusters (from any of its batches) whose titles overlap
    by 80% or more, merged into the first of them; every other cluster kept.

    The merged cluster takes the higher importance and the union of the
    groups, and appends the other's description and reasoning when new.
    """
    merged: List[Dict[str, Any]] = []
    for section_key, clusters in section_clusters.items():
        consumed: Set[int] = set()
        for i, cluster in enumerate(clusters):
            if i in consumed:
                continue
            for j in range(i + 1, len(clusters)):
                if j in consumed:
                    continue
                other = clusters[j]
                title_i, title_j = cluster.get("title", ""), other.get("title", "")
                ratio = _word_overlap_ratio(title_i, title_j)
                if ratio < 0.8:
                    continue
                logger.info(
                    "Cross-batch dedup: merging '%s' and '%s' "
                    "(overlap=%.2f) in section '%s'",
                    title_i, title_j, ratio, section_key,
                )
                cluster["importance"] = _highest_importance(
                    cluster.get("importance", "LOW"), other.get("importance", "LOW"),
                )
                cluster["underlying_group_ids"] = list(dict.fromkeys(
                    cluster.get("underlying_group_ids", [])
                    + other.get("underlying_group_ids", [])
                ))
                desc_i, desc_j = cluster.get("description", ""), other.get("description", "")
                if desc_j and desc_j not in desc_i:
                    cluster["description"] = f"{desc_i} Additionally: {desc_j}"
                reason_i, reason_j = cluster.get("reasoning", ""), other.get("reasoning", "")
                if reason_j and reason_j not in reason_i:
                    cluster["reasoning"] = f"{reason_i} {reason_j}".strip()
                consumed.add(j)
            merged.append(cluster)
    return merged


def _cluster_entry(cluster: Dict[str, Any], claims: _Claims) -> Dict[str, Any]:
    """A merged cluster's ``consolidated.json`` entry.

    Its type is raised to its groups' highest-priority type when the model's
    is lower, and its importance is never below its most important group's,
    the level the prompt asks for.
    """
    groups, index = claims.groups, claims.index
    ids = cluster.get("underlying_group_ids", [])
    type_ = cluster.get("type", "clarification")
    expected_type = _resolve_type_for_group_ids(ids, groups, index)
    if TYPE_PRIORITY.get(type_.lower(), 0) < TYPE_PRIORITY.get(expected_type, 0):
        type_ = expected_type
    members = [groups[index[gid]] for gid in ids if gid in index]
    importance = _importance.highest([
        cluster.get("importance"), *(_importance.group_importance(g) for g in members),
    ])
    models: Set[str] = {m for g in members for m in g.get("models", [])}
    suggestion_count = sum(len(g.get("suggestions", [])) for g in members)
    return _consolidated_entry(
        ids,
        list(dict.fromkeys(index[gid] for gid in ids if gid in index)),
        title=cluster.get("title", "Untitled"),
        description=cluster.get("description", ""),
        importance=importance,
        reference=_get_reference_for_cluster(ids, groups, index),
        type_=type_,
        model_count=len(models) or 1,
        suggestion_count=suggestion_count or 1,
        is_singleton=False,
        reasoning=cluster.get("reasoning", ""),
    )


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

    Each ``consolidation_batch_N.json`` in *phase_dir* is read through its
    own batch's ids (:func:`_batch_id_map`), so a reply can name only the
    groups the task file gave it (docs/development/review-results.md,
    "Consolidation batches"). Every assigned group appears in exactly one
    entry: the first cluster naming it, else a singleton (a reply that
    cannot be read, a group the reply left out, a one-group section).
    Similar clusters of a section are merged across batches.

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
          and ``reasoning``. Clusters come first, then singletons.
        - ``partial_failures_metadata`` is a dict with ``count``,
          ``batches`` (list of failed batch indices), and ``fallback``
          (always ``"all_singletons"``).
    """
    claims = _Claims(groups)
    plain_ids = [generate_group_id(group) for group in groups]
    failed_batch_indices: List[int] = []
    section_clusters: Dict[str, List[Dict[str, Any]]] = {}

    for batch_info in tasks_metadata.get("batches", []):
        batch_index = batch_info["batch_index"]
        batch_map = _batch_id_map(batch_info, claims.ids, plain_ids, claims.index)
        assigned = list(dict.fromkeys(gid for own in batch_map.values() for gid in own))
        reply = _read_batch(
            Path(phase_dir) / f"consolidation_batch_{batch_index}.json",
            batch_index, len(assigned),
        )
        if isinstance(reply, _BatchFailure):
            failed_batch_indices.append(batch_index)
            for gid in assigned:
                claims.singleton(gid, f"{reply.reason} — treated as singleton.")
            continue
        kept = _merge_batch(claims, batch_index, batch_map, *reply)
        if kept:
            section_clusters.setdefault(
                batch_info.get("section_key", "_uncategorized"), [],
            ).extend(kept)
        for gid in assigned:
            claims.singleton(
                gid, f"Missing from batch {batch_index} output — added as singleton.",
            )

    for indices in tasks_metadata.get("singleton_sections", {}).values():
        for idx in indices:
            if 0 <= idx < len(groups):
                claims.singleton(
                    claims.ids[idx], "Singleton section — only group in this section.",
                )

    consolidated_groups = [
        _cluster_entry(cluster, claims)
        for cluster in _merge_similar_clusters(section_clusters)
    ] + claims.singletons
    for i, cg in enumerate(consolidated_groups, start=1):
        cg["display_index"] = i

    return consolidated_groups, {
        "count": len(failed_batch_indices),
        "batches": failed_batch_indices,
        "fallback": "all_singletons",
    }


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
        # Which ids ``underlying_group_ids`` holds (load_merged_suggestions)
        "group_id_format": GROUP_ID_FORMAT,
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


def _scope_context(
    groups: List[Dict[str, Any]],
    validation: Optional[List[Dict[str, Any]]],
    phase_dir: Any,
    phase_name: str,
    scope_state: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]]]:
    """The underlying groups with their verdicts, the round, and one scope entry per group.

    A group's verdict is the one ``grouped.json`` carries, else the stamped
    validation record joined by its stable hash (never by index). The round
    is ``state.json``'s record beside the phase dir (*scope_state* overrides).
    """
    scoped = _scope_report.with_verdicts(groups, validation)
    state = scope_state if scope_state is not None else _scope_report.read_state(phase_dir)
    info = _scope_report.round_info(state, phase_name, scoped)
    entries = [_scope_report.group_scope(g, info) for g in scoped]
    return scoped, info, entries


def _distinct_underlying(
    consolidated_groups: List[Dict[str, Any]],
    groups: List[Dict[str, Any]],
    entries: List[Dict[str, Any]],
) -> List[Tuple[str, Dict[str, Any]]]:
    """``(group id, entry)`` for every underlying group an umbrella covers."""
    out: List[Tuple[str, Dict[str, Any]]] = []
    for cg in consolidated_groups:
        for idx in cg.get("underlying_group_indices", []):
            if 0 <= idx < len(groups):
                out.append((str(groups[idx].get("group_hash") or f"index:{idx}"), entries[idx]))
    return out


def _umbrella_entry(
    underlying_indices: List[int],
    groups: List[Dict[str, Any]],
    entries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """An umbrella's derived scope (``scope_report.umbrella_scope``)."""
    members = [
        (str(groups[idx].get("display_label") or f"G{idx + 1}"), entries[idx])
        for idx in underlying_indices if 0 <= idx < len(groups)
    ]
    return _scope_report.umbrella_scope(members)


def consolidated_importance(
    entry: Dict[str, Any], groups: List[Dict[str, Any]],
) -> str:
    """The level a consolidated entry shows: the highest of its own (a value
    naming no level reads as MEDIUM) and each underlying group's
    ``importance.group_importance``, the rule the flat and PR pages use."""
    return _importance.highest([
        entry.get("importance"),
        *(
            _importance.group_importance(groups[idx])
            for idx in entry.get("underlying_group_indices", [])
            if isinstance(idx, int) and 0 <= idx < len(groups)
        ),
    ])


def generate_consolidated_report(
    consolidated_groups: List[Dict[str, Any]],
    groups: List[Dict[str, Any]],
    phase_dir: str,
    prefix: str,
    validation: Optional[List[Dict[str, Any]]] = None,
    phase_name: str = "review-plan",
    scope_state: Optional[Dict[str, Any]] = None,
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
        scope_state: The ``state.json`` dict with the round's
            ``scope_policy`` record; ``None`` reads the one beside
            *phase_dir*. Each umbrella shows a tag derived from its
            underlying groups, each underlying group its validated tag and
            each suggestion its provisional one (plan scope-policy §6).

    Returns:
        The path (as a string) of the written ``consolidated-report.md``.
    """

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
    # Scope tags (plans/scope-policy-and-report-tags.md §6): consolidation is
    # presentation over the underlying groups, so every tag here is theirs —
    # an umbrella's is derived from its members and counts are per distinct
    # underlying group.
    scope_groups, scope_round, scope_entries = _scope_context(
        groups, validation, phase_dir, phase_name, scope_state)
    lines.extend(_scope_report.md_header_lines(
        scope_round,
        _scope_report.count_entries(_distinct_underlying(consolidated_groups, scope_groups,
                                                         scope_entries)),
        noun="underlying groups",
    ))
    lines.append("")
    lines.append(
        "> This report consolidates related suggestion groups for faster review."
    )
    lines.append("> For the full per-suggestion view, see `report.md`.")
    lines.append(
        "> Skip decisions from both reports are combined when applying suggestions."
    )
    lines.append(_scope_report.md_legend_line())
    lines.append("")

    # --- Build validation lookups for per-group aggregate status ---
    # Mirrors the HTML consolidated path so the "Let the agent decide" checkbox can
    # be gated on a needs-human-decision aggregate status.
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
        importance = consolidated_importance(cg, groups)
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

        # Section heading. Title, metadata fields, descriptions and themes
        # are model text: one line each, or escaped line by line
        # (`report_markdown`), so none of it can pass for a header or a box.
        lines.append(_rm.consolidated_header(display_index, consolidated_id, title))

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
        lines.append(_rm.checkbox_line(_rm.SKIP_GROUP))
        lines.append(_rm.checkbox_line(_rm.MARK_VALID))
        lines.append(_rm.checkbox_line(_rm.MARK_INVALID))
        lines.append(_rm.checkbox_line(_rm.NEEDS_HUMAN))
        # "Let the agent decide" routes the consolidated group to the per-item
        # judge at apply time. Scoped to needs-human-decision only.
        if agg_status == "needs-human-decision":
            lines.append(_rm.checkbox_line(_rm.LET_AGENT_DECIDE))

        # The umbrella's derived scope tag (any extension member makes it an
        # extension, "contains extension"); no authority of its own.
        lines.extend(_scope_report.md_umbrella_lines(_umbrella_entry(
            underlying_indices, groups, scope_entries)))

        # Metadata line
        lines.append(
            f"**Importance:** {_rm.inline_text(importance)} | "
            f"**Section:** {_rm.inline_text(reference)} "
            f"| **Models:** {model_count} | **Covers:** {_rm.inline_text(covers_list)}"
        )
        lines.append("")

        # Consolidated description
        lines.append(_rm.neutralize_model_text(description))
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
            lines.append(
                f"**{g_label}: {_rm.inline_text(theme)}** ({_rm.inline_text(models_str)})"
            )
            # Each member keeps its own validated tag in a mixed umbrella.
            lines.extend(_scope_report.md_group_lines(scope_entries[u_idx]))
            lines.append("")

            for sugg in orig_group.get("suggestions", []):
                sugg_desc = _suggestion_text(sugg)
                lines.append(_scope_report.md_member_line(sugg))
                lines.append(f"> {_rm.neutralize_model_text(sugg_desc)}")
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


def _failure_report_fields(phase_dir: str,
                           served_models: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """``failedModels``, ``requestedModels`` and ``notices`` for the consolidated page.

    The phase report's failure fields, read the same way a reaggregate reads
    them: the checkpoint's failures plus any requested model with neither a
    result nor a recorded failure (``remaining_failed_models``, against the
    ``models_completed`` a reaggregate reconciled with the files), the recorded
    requested set as the denominator, and the one warning notice whose
    ``message`` is ``report.md``'s ``**Models failed:**`` line without its bold
    markers. ``failedModels`` is always a dict (the template iterates it with
    ``Object.keys``); ``requestedModels`` is left out when the checkpoint
    records no requested set. *served_models* gives a jail-denied slot its
    label in the notice, as on the phase report.
    """

    failures, requested = remaining_failed_models(str(phase_dir))
    requested_count = len(requested) if requested is not None else None
    fields: Dict[str, Any] = {
        "failedModels": failures,
        "notices": build_report_notices(
            [], failures, requested_count,
            salvage_requested_models(str(phase_dir), list(failures)),
            served_models=served_models,
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
    scope_state: Optional[Dict[str, Any]] = None,
    served_models: Optional[Dict[str, Dict[str, Any]]] = None,
) -> str:
    """
    Write ``consolidated-report.html`` to *phase_dir*, and its payload to
    ``consolidated_report_data.json`` beside it.

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
        scope_state: As for :func:`generate_consolidated_report`. The payload
            gains ``scopePolicy`` and a ``scope`` entry per umbrella,
            underlying group and suggestion, and is persisted as
            ``consolidated_report_data.json`` for decision regeneration.
        served_models: ``models_served`` as the fan-out recorded it
            (``recorded_served_models``). The badges then name a fallback
            that served a slot and a slot's sandbox rung exactly as
            ``report.html``'s do (``report_view.build_model_metadata``), and
            the failure notice leads a jail-denied slot's entry with its
            label. ``None`` (a default run) leaves the payload as it was.

    Returns:
        The path (as a string) of the written ``consolidated-report.html``.

    Raises:
        FileNotFoundError: If the consolidated report template is missing.
        ValueError: If the template does not contain the data placeholder.
    """

    # The report page's own helpers: one template loader, one embedder, one
    # badge builder and one title rule for every page.
    phase_path = Path(phase_dir)
    plan_file = Path(plan_path)

    # --- Load template (FileNotFoundError when it is missing) ---
    template = load_report_template("consolidated")

    title = plan_title(read_plan(plan_file), plan_file.stem)

    # --- Badges: served model, sandbox rung and usage, as report.html says them ---
    model_metadata = build_model_metadata(models, served_models, usage)

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

    # --- Scope tags (plan §6): each underlying group's validated entry, each
    # member's provisional one, each umbrella's derived one ---
    _scope_groups, scope_round, scope_entries = _scope_context(
        groups, validation, phase_dir, phase_name, scope_state)

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
                    "description": _suggestion_text(sugg),
                    # The page shows the level Python sends, by the flat
                    # page's rule (utils/importance.py).
                    "importance": _importance.normalize(sugg.get("importance")),
                    "model": sugg.get("source_model", "unknown"),
                    "scope": _scope_report.member_scope(sugg),
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
                "scope": scope_entries[u_idx],
            }
            if orig_group.get("display_label"):
                ug_entry["displayLabel"] = orig_group["display_label"]
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
            "importance": consolidated_importance(cg, groups),
            "reference": cg.get("reference", ""),
            "type": cg.get("type", "modification"),
            "isSingleton": cg.get("is_singleton", True),
            "modelCount": cg.get("model_count", 1),
            "coversList": covers_list,
            "reasoning": cg.get("reasoning", ""),
            "underlyingGroups": underlying_groups_data,
            "scope": _umbrella_entry(underlying_indices, groups, scope_entries),
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
        "planTitle": title,
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
    report_data.update(_failure_report_fields(phase_dir, served_models))

    # The round's policy line, legend and tag counts over distinct groups.
    report_data[_scope_report.REPORT_KEY] = _scope_report.report_block(
        scope_round,
        _scope_report.count_entries(
            _distinct_underlying(consolidated_groups, groups, scope_entries)),
    )

    # --- Inject data into template (the flat/PR report's escaping) ---
    html = embed_report_data(report_data, template)

    # --- Write ---
    phase_path.mkdir(parents=True, exist_ok=True)
    output_path = phase_path / "consolidated-report.html"
    output_path.write_text(html, encoding="utf-8")
    # The persisted payload decision regeneration overlays onto
    # (`html_report_generator.regenerate_consolidated_with_human_decisions`),
    # as `report_data.json` is for report.html. Its name holds `consolidated`
    # and `report_data`, which every reaggregation scan excludes.
    try:
        (phase_path / CONSOLIDATED_REPORT_DATA).write_text(
            sidecar_json(report_data), encoding="utf-8")
    except OSError:
        pass

    return str(output_path)


# ---------------------------------------------------------------------------
# File hashing helpers
# ---------------------------------------------------------------------------

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
    # First, build a group_id → group index (0-based) mapping: each id names
    # its own group in a file that says so, every same-content copy in one
    # from before (_decision_join).
    consolidated_groups_list = consolidated_data.get("consolidated_groups", [])
    group_id_to_indices = _decision_join(
        groups,
        distinct=consolidated_data.get("group_id_format") == GROUP_ID_FORMAT,
    )

    # Build consolidated_id → list of 0-based group indices
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
