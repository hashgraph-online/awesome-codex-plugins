#!/usr/bin/env python3
"""
Validation batching utility for minimizing context rot.

Groups validation items into batches to allow sequential subagent processing,
where each subagent gets a fresh context window for better accuracy.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# Configuration constants
MAX_GROUPS_PER_BATCH = 4
HIGH_THRESHOLD_FOR_PAIRING = 5  # If >5 HIGH items, pair them instead of isolating


@dataclass
class ValidationBatch:
    """A batch of groups to validate together."""
    groups: List[Dict[str, Any]]
    group_indices: List[int]  # Original indices for merging results
    batch_index: int
    is_high_priority: bool = False

    @property
    def size(self) -> int:
        """Number of groups in this batch."""
        return len(self.groups)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "groups": self.groups,
            "group_indices": self.group_indices,
            "batch_index": self.batch_index,
            "is_high_priority": self.is_high_priority,
            "size": self.size,
        }


def _get_group_importance(group: Dict[str, Any]) -> str:
    """Extract the highest importance level from a group."""
    # Check group-level importance first
    if "importance" in group:
        return str(group["importance"]).upper()

    # Check suggestions within the group
    suggestions = group.get("suggestions", [])
    if not suggestions:
        return "MEDIUM"

    importance_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    highest = 1
    for s in suggestions:
        imp = str(s.get("importance", "MEDIUM")).upper()
        highest = max(highest, importance_order.get(imp, 1))

    for imp, score in importance_order.items():
        if score == highest:
            return imp
    return "MEDIUM"


def batch_validation_groups(
    groups: List[Dict[str, Any]],
    max_per_batch: int = MAX_GROUPS_PER_BATCH,
    isolate_high: bool = True
) -> List[ValidationBatch]:
    """
    Batch validation groups intelligently.

    Batching heuristics:
    1. HIGH importance groups are isolated (1 per batch) unless >HIGH_THRESHOLD_FOR_PAIRING
    2. If many HIGH items (>5), pair them (2 per batch) instead of isolating
    3. Normal groups (MEDIUM/LOW) batched up to max_per_batch
    4. If isolate_high=False, HIGH groups are batched with normal groups

    Args:
        groups: List of group dictionaries to batch
        max_per_batch: Maximum groups per batch for normal items (default: 4)
        isolate_high: Whether to isolate HIGH importance items (default: True)

    Returns:
        List of ValidationBatch objects
    """
    if not groups:
        return []

    # If not isolating HIGH, treat all groups as normal
    if not isolate_high:
        all_groups = [(i, group) for i, group in enumerate(groups)]
        batches: List[ValidationBatch] = []
        batch_index = 0

        for i in range(0, len(all_groups), max_per_batch):
            batch_items = all_groups[i:i + max_per_batch]
            batches.append(ValidationBatch(
                groups=[g for _, g in batch_items],
                group_indices=[idx for idx, _ in batch_items],
                batch_index=batch_index,
                is_high_priority=False,
            ))
            batch_index += 1

        return batches

    # Separate HIGH from normal groups
    high_groups: List[tuple[int, Dict[str, Any]]] = []
    normal_groups: List[tuple[int, Dict[str, Any]]] = []

    for i, group in enumerate(groups):
        importance = _get_group_importance(group)
        if importance == "HIGH":
            high_groups.append((i, group))
        else:
            normal_groups.append((i, group))

    batches: List[ValidationBatch] = []
    batch_index = 0

    # Handle HIGH importance groups
    if high_groups:
        if len(high_groups) <= HIGH_THRESHOLD_FOR_PAIRING:
            # Isolate each HIGH group in its own batch
            for idx, group in high_groups:
                batches.append(ValidationBatch(
                    groups=[group],
                    group_indices=[idx],
                    batch_index=batch_index,
                    is_high_priority=True,
                ))
                batch_index += 1
        else:
            # Too many HIGH items - pair them (2 per batch) to avoid too many batches
            pair_size = 2
            for i in range(0, len(high_groups), pair_size):
                batch_items = high_groups[i:i + pair_size]
                batches.append(ValidationBatch(
                    groups=[g for _, g in batch_items],
                    group_indices=[idx for idx, _ in batch_items],
                    batch_index=batch_index,
                    is_high_priority=True,
                ))
                batch_index += 1

    # Handle normal groups - batch up to max_per_batch
    for i in range(0, len(normal_groups), max_per_batch):
        batch_items = normal_groups[i:i + max_per_batch]
        batches.append(ValidationBatch(
            groups=[g for _, g in batch_items],
            group_indices=[idx for idx, _ in batch_items],
            batch_index=batch_index,
            is_high_priority=False,
        ))
        batch_index += 1

    return batches


def estimate_validation_batching_stats(
    groups: List[Dict[str, Any]],
    max_per_batch: int = MAX_GROUPS_PER_BATCH
) -> Dict[str, Any]:
    """
    Estimate batching statistics without creating actual batches.

    Useful for previewing what batching will do.

    Args:
        groups: List of group dictionaries
        max_per_batch: Maximum groups per batch

    Returns:
        Dict with statistics:
        - total_groups: int
        - high_count: int
        - normal_count: int
        - estimated_batches: int
        - subagent_calls_saved: int
        - efficiency_gain_percent: float
    """
    if not groups:
        return {
            "total_groups": 0,
            "high_count": 0,
            "normal_count": 0,
            "estimated_batches": 0,
            "subagent_calls_saved": 0,
            "efficiency_gain_percent": 0.0,
        }

    high_count = sum(1 for g in groups if _get_group_importance(g) == "HIGH")
    normal_count = len(groups) - high_count

    # Calculate estimated batches
    if high_count <= HIGH_THRESHOLD_FOR_PAIRING:
        high_batches = high_count  # One per HIGH item
    else:
        high_batches = (high_count + 1) // 2  # Paired

    normal_batches = (normal_count + max_per_batch - 1) // max_per_batch if normal_count > 0 else 0

    estimated_batches = high_batches + normal_batches

    # Without batching, we'd need one subagent per group
    subagent_calls_saved = len(groups) - estimated_batches
    efficiency_gain = (subagent_calls_saved / len(groups) * 100) if groups else 0.0

    return {
        "total_groups": len(groups),
        "high_count": high_count,
        "normal_count": normal_count,
        "estimated_batches": estimated_batches,
        "subagent_calls_saved": subagent_calls_saved,
        "efficiency_gain_percent": round(efficiency_gain, 1),
    }
