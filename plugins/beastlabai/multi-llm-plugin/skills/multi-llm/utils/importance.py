"""Shared utility for importance level calculations."""

from typing import Any, Dict, List

# Importance level ordering (highest to lowest)
IMPORTANCE_ORDER = ["HIGH", "MEDIUM", "LOW"]


def get_highest_importance(group: Dict[str, Any]) -> str:
    """
    Get the highest importance level from a group's suggestions/issues.

    Args:
        group: A group dictionary containing either 'suggestions' or 'issues' list,
               where each item may have an 'importance' field.

    Returns:
        The highest importance level found ("HIGH", "MEDIUM", or "LOW").
        Defaults to "MEDIUM" if no importance is specified.
    """
    items = group.get("suggestions", group.get("issues", []))
    importances = [item.get("importance", "MEDIUM").upper() for item in items]

    for level in IMPORTANCE_ORDER:
        if level in importances:
            return level
    return "MEDIUM"


def filter_by_importance(
    items: List[Dict[str, Any]],
    min_importance: str = "LOW"
) -> List[Dict[str, Any]]:
    """
    Filter items to include only those at or above a minimum importance level.

    Args:
        items: List of items with 'importance' field
        min_importance: Minimum importance level to include

    Returns:
        Filtered list of items
    """
    min_idx = IMPORTANCE_ORDER.index(min_importance.upper())
    return [
        item for item in items
        if IMPORTANCE_ORDER.index(item.get("importance", "MEDIUM").upper()) <= min_idx
    ]


def compare_importance(item1: Dict[str, Any], item2: Dict[str, Any]) -> int:
    """
    Compare two items by importance for sorting.

    Args:
        item1: First item with 'importance' field
        item2: Second item with 'importance' field

    Returns:
        -1 if item1 is more important, 1 if item2 is more important, 0 if equal
    """
    imp1 = item1.get("importance", "MEDIUM").upper()
    imp2 = item2.get("importance", "MEDIUM").upper()

    idx1 = IMPORTANCE_ORDER.index(imp1) if imp1 in IMPORTANCE_ORDER else 1
    idx2 = IMPORTANCE_ORDER.index(imp2) if imp2 in IMPORTANCE_ORDER else 1

    if idx1 < idx2:
        return -1
    elif idx1 > idx2:
        return 1
    return 0


def normalize_importance(level: str) -> str:
    """
    Normalize an importance level string.

    Args:
        level: Importance level (case-insensitive)

    Returns:
        Normalized importance level ("HIGH", "MEDIUM", or "LOW")
    """
    normalized = level.upper().strip()
    if normalized in IMPORTANCE_ORDER:
        return normalized
    return "MEDIUM"
