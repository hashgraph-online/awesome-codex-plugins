"""Migration utilities for converting v1 positional-ID selections to v2 hash-based selections."""

import logging
import re
import sys
from typing import Any, Dict, List, Tuple

from .state_manager import stamp_stable_ids, CURRENT_FORMAT_VERSION

logger = logging.getLogger(__name__)


def _build_positional_to_hash_map(
    groups: List[Dict[str, Any]],
) -> Tuple[Dict[int, str], Dict[str, str], Dict[str, str]]:
    """Build positional-to-hash mapping from stamped groups.

    Args:
        groups: Stamped groups list (must have group_hash, suggestion_hash).

    Returns:
        Tuple of:
        - group_index_to_hash: {1-based index -> group_hash}
        - suggestion_id_to_hash: {"G{N}S{M}" -> suggestion_hash}
        - labels_map: {hash -> display_label} for debugging
    """
    group_index_to_hash: Dict[int, str] = {}
    suggestion_id_to_hash: Dict[str, str] = {}
    labels_map: Dict[str, str] = {}

    for g_idx, group in enumerate(groups):
        g_num = g_idx + 1
        ghash = group.get("group_hash", "")
        if ghash:
            group_index_to_hash[g_num] = ghash
            labels_map[ghash] = group.get("display_label", f"G{g_num}")

        suggestions = group.get("suggestions", group.get("issues", []))
        for s_idx, sugg in enumerate(suggestions):
            s_num = s_idx + 1
            shash = sugg.get("suggestion_hash", "")
            positional_id = f"G{g_num}S{s_num}"
            if shash:
                suggestion_id_to_hash[positional_id] = shash
                labels_map[shash] = sugg.get("display_label", positional_id)

    return group_index_to_hash, suggestion_id_to_hash, labels_map


def _migrate_v1_selections(
    selections_data: Dict[str, Any],
    groups: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Migrate v1 user_selections.json to v2 hash-based format.

    Takes a v1 selections dict (integer skipped_groups, G{N}S{M} suggestion IDs)
    and the raw groups list (from grouped.json). Stamps stable IDs on groups
    (idempotent), builds positional-to-hash mapping, converts all keys,
    and returns a v2-format dict.

    Args:
        selections_data: v1 user_selections.json dict
        groups: Raw groups list from grouped.json

    Returns:
        v2-format selections dict with hash-based keys
    """
    # Ensure hashes are stamped (idempotent)
    stamp_stable_ids(groups)

    group_idx_to_hash, sugg_id_to_hash, labels_map = _build_positional_to_hash_map(groups)

    # Detect if data already uses hash-based IDs (no migration needed)
    old_skipped_groups = selections_data.get("skipped_groups", [])
    if old_skipped_groups and all(
        isinstance(x, str) and re.fullmatch(r"[0-9a-f]{8,16}", x)
        for x in old_skipped_groups
    ):
        # Already hash-based — just add format_version and return
        migrated = dict(selections_data)
        migrated["format_version"] = CURRENT_FORMAT_VERSION
        return migrated

    migrated = dict(selections_data)
    total_selections = 0
    migrated_count = 0
    dropped_count = 0

    # Migrate skipped_groups: v1 uses 1-based integers
    new_skipped_groups = []
    for idx in old_skipped_groups:
        total_selections += 1
        if isinstance(idx, int) and idx in group_idx_to_hash:
            new_skipped_groups.append(group_idx_to_hash[idx])
            migrated_count += 1
        else:
            dropped_count += 1
            print(
                f"WARNING: Migration dropped skipped_groups entry {idx!r} "
                f"(out of range or invalid type, {len(groups)} groups available)",
                file=sys.stderr,
            )
    migrated["skipped_groups"] = new_skipped_groups

    # Migrate skipped_suggestions: v1 uses "G{N}S{M}" strings
    old_skipped_suggestions = selections_data.get("skipped_suggestions", [])
    new_skipped_suggestions = []
    for sid in old_skipped_suggestions:
        total_selections += 1
        sid_upper = str(sid).upper()
        if sid_upper in sugg_id_to_hash:
            new_skipped_suggestions.append(sugg_id_to_hash[sid_upper])
            migrated_count += 1
        else:
            dropped_count += 1
            print(
                f"WARNING: Migration dropped skipped_suggestions entry {sid!r} "
                f"(no matching suggestion found)",
                file=sys.stderr,
            )
    migrated["skipped_suggestions"] = new_skipped_suggestions

    # Migrate edited_descriptions: v1 keys are "G{N}S{M}"
    old_edited = selections_data.get("edited_descriptions", {})
    new_edited = {}
    for sid, desc in old_edited.items():
        total_selections += 1
        sid_upper = str(sid).upper()
        if sid_upper in sugg_id_to_hash:
            new_edited[sugg_id_to_hash[sid_upper]] = desc
            migrated_count += 1
        else:
            dropped_count += 1
            print(
                f"WARNING: Migration dropped edited_descriptions entry {sid!r} "
                f"(no matching suggestion found)",
                file=sys.stderr,
            )
    migrated["edited_descriptions"] = new_edited

    # Migrate validation_overrides: v1 keys are group indices (int or str) or "G{N}S{M}"
    old_overrides = selections_data.get("validation_overrides", {})
    new_overrides = {}
    for key, value in old_overrides.items():
        total_selections += 1
        key_str = str(key)
        # Check if it's a suggestion-level override (G{N}S{M})
        sugg_match = re.match(r"G(\d+)S(\d+)", key_str, re.IGNORECASE)
        if sugg_match:
            key_upper = key_str.upper()
            if key_upper in sugg_id_to_hash:
                new_overrides[sugg_id_to_hash[key_upper]] = value
                migrated_count += 1
            else:
                dropped_count += 1
                print(
                    f"WARNING: Migration dropped validation_overrides entry {key!r} "
                    f"(no matching suggestion found)",
                    file=sys.stderr,
                )
        else:
            # Group-level override (integer key)
            try:
                idx = int(key)
                if idx in group_idx_to_hash:
                    new_overrides[group_idx_to_hash[idx]] = value
                    migrated_count += 1
                else:
                    dropped_count += 1
                    print(
                        f"WARNING: Migration dropped validation_overrides entry {key!r} "
                        f"(group index out of range)",
                        file=sys.stderr,
                    )
            except (ValueError, TypeError):
                dropped_count += 1
                print(
                    f"WARNING: Migration dropped validation_overrides entry {key!r} "
                    f"(unrecognized key format)",
                    file=sys.stderr,
                )
    migrated["validation_overrides"] = new_overrides

    # Add labels map and set format version
    migrated["_labels"] = labels_map
    migrated["format_version"] = CURRENT_FORMAT_VERSION

    print(
        f"Migrated {migrated_count} of {total_selections} selections; "
        f"{dropped_count} dropped (out-of-range)",
        file=sys.stderr,
    )

    return migrated


def _migrate_v1_html_selections(
    html_selections: Dict[str, Any],
    groups: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Migrate v1 HTML-exported selections to v2 hash-based format.

    Same approach as _migrate_v1_selections but for HTML-exported selections.

    Args:
        html_selections: v1 HTML selections dict
        groups: Raw groups list from grouped.json

    Returns:
        v2-format selections dict with hash-based keys
    """
    # Reuse the same migration logic
    return _migrate_v1_selections(html_selections, groups)
