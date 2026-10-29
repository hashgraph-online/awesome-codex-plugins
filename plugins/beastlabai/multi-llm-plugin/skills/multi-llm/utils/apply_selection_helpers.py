"""Selection helper utilities for apply orchestrators.

Provides shared functions for checking user-skipped items, merging
validation with groups, resolving priority arguments, and merging
user-edited descriptions. Extracted from the three apply orchestrators.
"""

import copy
import sys
from typing import Any, Dict, List, Set, Tuple

try:
    from .state_manager import generate_group_id
except ImportError:
    from utils.state_manager import generate_group_id


def _is_user_skipped(group: Dict[str, Any], skipped_ids: Set[str]) -> bool:
    """Check if a group corresponds to a user-skipped suggestion ID."""
    # Check suggestions within the group for matching IDs
    for s in group.get("suggestions", []):
        if s.get("id") in skipped_ids:
            return True
    # Also check group-level id if present
    if group.get("id") in skipped_ids:
        return True
    return False


def merge_validation_with_groups(
    groups: List[Dict[str, Any]],
    validation: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Merge validation results into grouped suggestions.

    Joins by stable content hash (validation ``group_id`` == group
    ``group_hash``) when available, falling back to positional
    ``group_index`` for legacy data that predates group_id.

    Hash-based matching is required because validation results are not
    guaranteed to be in the same order as the groups array — reaggregation
    and priority sorting can reorder one but not the other. A pure
    positional join silently attaches each validation status/reason to the
    wrong group, dropping genuinely-valid fixes into needs-human and
    force-routing needs-human items into to-apply. Mirrors the logic in
    ``validation.apply_validation_to_groups`` used by the review path.
    """
    # Primary lookup: stable content hash -> validation record
    validation_by_id = {
        v.get("group_id"): v for v in validation if v.get("group_id")
    }
    # Fallback lookup: positional index -> validation record (legacy data)
    validation_by_index = {
        v.get("group_index", i): v for i, v in enumerate(validation)
    }

    merged = []
    for i, group in enumerate(groups):
        group_copy = dict(group)
        group_copy["group_index"] = i  # Track original index
        # Prefer the stamped group_hash; compute it if absent so groups that
        # were never stamped still match by content.
        ghash = group.get("group_hash") or generate_group_id(group)
        val = (
            validation_by_id.get(ghash)
            or validation_by_index.get(i)
            or {}
        )
        group_copy["validation_status"] = val.get("status", "needs-human-decision")
        group_copy["validation_reason"] = val.get("reason", "No validation result")
        group_copy["validation_confidence"] = val.get("confidence", 0.0)
        # Copy error_type and recoverable fields
        if "error_type" in val:
            group_copy["validation_error_type"] = val.get("error_type")
        if "recoverable" in val:
            group_copy["validation_recoverable"] = val.get("recoverable")
        merged.append(group_copy)

    return merged


def resolve_priority_args(args) -> str:
    """Resolve --include-low and --min-priority to a single min_priority value.

    Handles both the legacy --include-low flag (deprecated) and the
    current --min-priority argument. If the args namespace does not
    have an ``include_low`` attribute (e.g. apply_task_suggestions),
    only --min-priority is checked.
    """
    include_low = getattr(args, 'include_low', False)
    min_priority = getattr(args, 'min_priority', None)

    if include_low and min_priority:
        print("WARNING: --include-low and --min-priority both set; using --min-priority=%s (--include-low ignored)" % min_priority, file=sys.stderr)
        return min_priority
    if include_low:
        print("WARNING: --include-low is deprecated (low is now default). Use --min-priority to filter.", file=sys.stderr)
        return "low"
    return min_priority or "low"


def merge_edited_descriptions(
    groups: List[Dict[str, Any]],
    edited_descriptions: Dict[str, Tuple[str, str]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Replace desc fields with user edits, return updated groups and edit log.

    Shared implementation used by all three apply orchestrators.

    Args:
        groups: List of group dicts with 'suggestions' arrays.
        edited_descriptions: Dict mapping ID (G1S1 or suggestion_hash) to
            (original, edited) tuple.

    Returns:
        Tuple of (updated_groups, edit_log).
        edit_log is list of dicts with {id, title, original_len, edited_len}.
    """
    updated_groups = copy.deepcopy(groups)
    edit_log: List[Dict[str, Any]] = []

    # Build hash->location lookup for hash-based matching
    hash_lookup: Dict[str, Tuple[int, int]] = {}
    for group_idx, group in enumerate(updated_groups):
        for sugg_idx, suggestion in enumerate(group.get("suggestions", [])):
            shash = suggestion.get("suggestion_hash")
            if shash:
                hash_lookup[shash] = (group_idx, sugg_idx)

    for group_idx, group in enumerate(updated_groups, start=1):
        for sugg_idx, suggestion in enumerate(group.get("suggestions", []), start=1):
            shash = suggestion.get("suggestion_hash", "")
            positional_id = f"G{group_idx}S{sugg_idx}"

            matched_key = None
            if shash and shash in edited_descriptions:
                matched_key = shash
            elif positional_id in edited_descriptions:
                matched_key = positional_id

            if matched_key is not None:
                original_desc, edited_desc = edited_descriptions[matched_key]
                suggestion["_original_desc"] = suggestion.get("desc", "")
                suggestion["desc"] = edited_desc
                suggestion["_description_edited"] = True
                edit_log.append({
                    "id": shash or positional_id,
                    "title": suggestion.get("title", "Unknown"),
                    "original_len": len(original_desc),
                    "edited_len": len(edited_desc),
                })

    return updated_groups, edit_log
