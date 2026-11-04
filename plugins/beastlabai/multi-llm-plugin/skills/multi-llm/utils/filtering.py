"""Shared filtering logic for suggestions and code fixes."""

import copy
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

from .human_decisions import is_judge_source
from .judge_vocab import JUDGE_DECIDE, JUDGE_DECIDE_ITEM_IDS, upgrade_legacy
from .importance import get_highest_importance

# Import error type constants (will be added to validation.py)
try:
    from .validation import ERROR_TYPE_AMBIGUOUS, RECOVERABLE_ERROR_TYPES
except ImportError:
    # Fallback if validation module not yet updated
    ERROR_TYPE_AMBIGUOUS = "real_ambiguity"
    RECOVERABLE_ERROR_TYPES = frozenset({"parsing_error", "timeout", "rate_limited"})


def resolve_bulk_option_conflicts(
    skip_all_human: bool = False,
    approve_all_human: bool = False,
    approve_all_low: bool = False,
    approve_importance_levels: Optional[List[str]] = None,
    approve_validation_failed: bool = False
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Resolve conflicts between bulk approval options.

    Priority order (highest to lowest):
    1. skip_all_human (highest priority - safety first)
    2. approve_all_human (explicit full approval overrides selective)
    3. approve_importance_levels (explicit importance levels)
    4. approve_all_low (convenience shorthand)
    5. approve_validation_failed (lowest priority - only affects validation failures)

    Returns:
        Tuple of (effective_settings, warnings)
    """
    warnings = []
    effective = {
        "skip_all": False,
        "approve_all": False,
        "approve_importance_levels": [],
        "approve_validation_failed": False
    }

    # Priority 1: skip_all_human overrides everything
    if skip_all_human:
        effective["skip_all"] = True
        if approve_all_human or approve_all_low or approve_importance_levels:
            warnings.append(
                "WARNING: --skip-all-human overrides all approval options. "
                "All needs-human-decision items will be SKIPPED, not approved."
            )
        return effective, warnings

    # Priority 2: approve_all_human overrides selective options
    if approve_all_human:
        effective["approve_all"] = True
        if approve_all_low or approve_importance_levels:
            warnings.append(
                "WARNING: --approve-all overrides --approve-all-low and "
                "--approve-importance. ALL needs-human-decision items will be approved."
            )
        return effective, warnings

    # Priority 3: approve_importance_levels (explicit levels)
    if approve_importance_levels:
        effective["approve_importance_levels"] = [
            level.upper() for level in approve_importance_levels
        ]
        if approve_all_low and "LOW" not in effective["approve_importance_levels"]:
            warnings.append(
                "WARNING: --approve-importance does not include LOW but "
                "--approve-all-low was specified. Using --approve-importance levels only."
            )

    # Priority 4: approve_all_low (only if not superseded)
    elif approve_all_low:
        effective["approve_importance_levels"] = ["LOW"]

    # Priority 5: approve_validation_failed (additive, always applies)
    effective["approve_validation_failed"] = approve_validation_failed

    return effective, warnings


def should_bypass_no_selection_confirmation(
    no_confirm: bool = False,
    yes: bool = False,
    force: bool = False,
    approve_all: bool = False,
    skip_all_human: bool = False,
    approve_all_low: bool = False,
    approve_importance: Optional[List[str]] = None,
    approve_validation_failed: bool = False,
    dry_run: bool = False,
) -> bool:
    """Check if any flag implies deliberate user intent, bypassing the
    no-selections confirmation prompt."""
    return (
        no_confirm or yes or force or approve_all or skip_all_human
        or approve_all_low or bool(approve_importance)
        or approve_validation_failed or dry_run
    )


def filter_items(
    groups: List[Dict[str, Any]],
    min_priority: str = "low",
    skip_human_review: bool = False,
    approve_all_human: bool = False,
    approve_low_human: bool = False,
    approve_importance_levels: Optional[List[str]] = None,
    approve_validation_failed: bool = False,
    skip_all_human: bool = False,
    dry_run: bool = False
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Filter groups by validation status and importance.

    This shared function is used by both apply_suggestions_orchestrator.py
    and apply_code_fixes_orchestrator.py to avoid code duplication.

    Args:
        groups: List of grouped suggestions or issues
        min_priority: Minimum importance level to include (low, medium, high). Default: low (all valid items)
        skip_human_review: Skip all needs-human-decision items (legacy, prefer skip_all_human)
        approve_all_human: Auto-approve all needs-human-decision items
        approve_low_human: Auto-approve LOW importance needs-human-decision items
        approve_importance_levels: Auto-approve items at these importance levels
        approve_validation_failed: Auto-approve items with recoverable validation failures
        skip_all_human: Skip all needs-human-decision and validation_failed items
        dry_run: If True, don't modify groups, just report what would happen

    Returns:
        Tuple of (valid, needs_human, skipped, dry_run_report) lists
    """
    # Resolve conflicts first
    effective, warnings = resolve_bulk_option_conflicts(
        skip_all_human=skip_all_human,
        approve_all_human=approve_all_human,
        approve_all_low=approve_low_human,
        approve_importance_levels=approve_importance_levels,
        approve_validation_failed=approve_validation_failed
    )

    # Print warnings to stderr
    for warning in warnings:
        print(warning, file=sys.stderr)

    # Priority levels for filtering
    priority_levels = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    min_level = priority_levels.get(min_priority.upper(), 0)

    valid = []
    needs_human = []
    skipped = []
    dry_run_report = {
        "would_auto_approve": [],
        "would_skip": [],
        "warnings": warnings
    }

    for group in groups:
        status = group.get("validation_status", "needs-human-decision")
        importance = get_highest_importance(group)
        group["_importance"] = importance

        # Get error type for validation_failed items
        error_type = group.get("validation_error_type", group.get("error_type", "unknown"))

        if status == "invalid":
            skipped.append(group)
            continue

        # A "Let the agent decide" marker is an affirmative "route to the judge"
        # request and must never be auto-approved, regardless of the underlying
        # validation_status. This guards against conflicting overrides (e.g. a
        # group marked judge_decide that also got promoted to "valid", or a
        # group-level "valid" override alongside a per-suggestion judge_decide)
        # where the marker would otherwise fall through the status-specific
        # branches below. An explicit bulk *skip* still wins, matching the
        # needs-human-decision branch.
        if group.get(JUDGE_DECIDE) and not (
            effective["skip_all"] or skip_human_review
        ):
            needs_human.append(group)
            continue

        # Determine if this item should be auto-approved or skipped
        should_auto_approve = False
        should_skip = False
        approval_reason = None

        if status == "validation_failed":
            # Recoverable validation errors - can be revalidated or bulk approved
            if effective["skip_all"]:
                should_skip = True
            elif effective["approve_all"]:
                should_auto_approve = True
                approval_reason = "--approve-all"
            elif effective["approve_validation_failed"] and error_type != ERROR_TYPE_AMBIGUOUS:
                should_auto_approve = True
                approval_reason = "--approve-validation-failed"
            elif importance in effective["approve_importance_levels"]:
                should_auto_approve = True
                approval_reason = f"--approve-importance {importance}"

        elif status == "needs-human-decision":
            # Per-item "Let the agent decide" beats bulk *approval*: a marked item
            # is an affirmative "route to the judge" request, so keep it in
            # needs_human (never auto-approved/flipped to valid). Bulk *skip*
            # (--skip-all-human) is still honoured below — an explicit skip is a
            # safety choice, not a default-skip candidate.
            # NOTE: judge_decide is also handled by the status-agnostic guard
            # at the top of the loop; this branch-local check is a redundant
            # safety net kept for self-documentation.
            if group.get(JUDGE_DECIDE) and not (
                effective["skip_all"] or skip_human_review
            ):
                needs_human.append(group)
                continue
            # Check bulk approval options
            if effective["skip_all"]:
                should_skip = True
            elif skip_human_review:  # Legacy flag
                should_skip = True
            elif effective["approve_all"]:
                should_auto_approve = True
                approval_reason = "--approve-all"
            elif importance in effective["approve_importance_levels"]:
                should_auto_approve = True
                approval_reason = f"--approve-importance {importance}"

        elif status == "valid":
            importance_level = priority_levels.get(importance, 0)
            if importance_level < min_level:
                skipped.append(group)
                continue
            else:
                valid.append(group)
                continue
        else:
            # Unknown status
            needs_human.append(group)
            continue

        # Apply the decision
        if should_auto_approve:
            if dry_run:
                dry_run_report["would_auto_approve"].append({
                    "group_index": group.get("group_index"),
                    "theme": group.get("theme", ""),
                    "importance": importance,
                    "original_status": status,
                    "reason": f"Would be auto-approved via {approval_reason}"
                })
                needs_human.append(group)  # Keep in needs_human for dry-run
            else:
                group["validation_status"] = "valid"
                group["validation_reason"] = f"Auto-approved (was {status}, importance={importance})"
                group["auto_approved"] = True
                group["auto_approval_reason"] = approval_reason
                valid.append(group)
        elif should_skip:
            if dry_run:
                dry_run_report["would_skip"].append({
                    "group_index": group.get("group_index"),
                    "theme": group.get("theme", ""),
                    "importance": importance,
                    "original_status": status,
                    "reason": "Would be skipped via --skip-all-human"
                })
            skipped.append(group)
        else:
            needs_human.append(group)

    return valid, needs_human, skipped, dry_run_report


def validate_batch_mode_honored(
    human_review_config: Dict[str, Any],
    recorded_decisions: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Verify that batch mode was respected based on recorded decisions.

    When batch mode is enabled, decisions should be recorded with batch_context.
    This function validates that per-item prompting did not occur despite
    batch mode being enabled.

    Args:
        human_review_config: The human_review_config from orchestrator output
        recorded_decisions: The recorded decisions from state (group_id -> decision)

    Returns:
        Tuple of (is_valid, warnings)
        - is_valid: True if batch mode was honored
        - warnings: List of warning messages if batch mode was not honored
    """
    warnings = []

    if not human_review_config.get("batch_enabled", False):
        return True, []  # Batch mode not enabled, no validation needed

    if not recorded_decisions:
        return True, []  # No decisions recorded yet

    # Check if decisions have batch_context
    batch_ids = set()
    non_batch_decisions = []

    for group_id, decision in recorded_decisions.items():
        batch_ctx = decision.get("batch_context")
        if batch_ctx:
            batch_ids.add(batch_ctx.get("batch_id"))
        else:
            non_batch_decisions.append(group_id)

    is_valid = True

    if non_batch_decisions:
        is_valid = False
        warnings.append(
            f"WARNING: {len(non_batch_decisions)} decisions were recorded without "
            f"batch_context despite batch_enabled=True. This suggests per-item "
            f"prompting occurred instead of batch prompting."
        )

    if len(batch_ids) > 2:  # Allow at most 2 batches (e.g., one approve, one skip)
        warnings.append(
            f"WARNING: {len(batch_ids)} different batch_ids found. Expected 1-2 "
            f"batches for efficient batch mode. Multiple batches may indicate "
            f"suboptimal prompting strategy."
        )

    return is_valid, warnings


def validate_judge_decide_items_honored(
    human_review_config: Dict[str, Any],
    recorded_decisions: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    """Verify every report-pre-marked "Let the agent decide" item reached the judge.

    The per-item routing decision (judge-without-prompting vs. prompt) is made
    by the host agent following the prose in the apply instructions; this is a
    post-hoc audit (a sibling of :func:`validate_batch_mode_honored`), not a
    hard pre-flight gate. For every id in
    ``human_review_config["judge_decide_item_ids"]`` it checks that a decision
    was recorded and that the decision's ``batch_context.decision_source`` is
    ``judge_auto_decide`` or ``judge_auto_decide_salvage`` (i.e. it was
    actually routed to the judge, not prompted or skipped). A config or a
    record in the ``claude_*`` spelling an earlier version wrote reads the same.

    Args:
        human_review_config: The human_review_config from orchestrator output.
        recorded_decisions: The recorded decisions from state
            (group_id -> decision).

    Returns:
        Tuple of (is_valid, warnings).
        - is_valid: True if every pre-marked id was routed to the judge.
        - warnings: List of warning messages for any id that is missing a
          decision or whose decision carries a different source.
    """
    warnings: List[str] = []

    config = upgrade_legacy(copy.deepcopy(dict(human_review_config or {})))
    item_ids = [gid for gid in config.get(JUDGE_DECIDE_ITEM_IDS, []) if gid]
    if not item_ids:
        return True, []  # Nothing pre-marked, nothing to audit.

    is_valid = True

    for gid in item_ids:
        decision = recorded_decisions.get(gid)
        if not decision:
            is_valid = False
            warnings.append(
                f"WARNING: report-pre-marked 'Let the agent decide' item {gid} has "
                f"no recorded decision. It may have been prompted interactively "
                f"or dropped instead of routed to the judge."
            )
            continue
        batch_ctx = decision.get("batch_context") or {}
        source = batch_ctx.get("decision_source")
        if not is_judge_source(source):
            is_valid = False
            warnings.append(
                f"WARNING: report-pre-marked 'Let the agent decide' item {gid} was "
                f"recorded with decision_source {source!r}, not a judge-agent "
                f"source (judge_auto_decide / judge_auto_decide_salvage). It may have "
                f"been prompted instead of auto-decided."
            )

    return is_valid, warnings


def generate_batch_id() -> str:
    """Generate a unique batch ID for recording batch decisions."""
    from datetime import datetime
    return f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def filter_user_skipped_groups(
    groups: List[Dict[str, Any]],
    skipped_group_hashes: Set[str],
    skipped_suggestion_hashes: Set[str],
    old_skipped_ids: Set[str],
) -> Tuple[List[Dict[str, Any]], int]:
    """Filter out skipped groups and remove skipped suggestions from remaining groups.

    Groups are matched by their ``group_hash`` field against *skipped_group_hashes*.
    Individual suggestions are matched by their ``suggestion_hash`` field against
    *skipped_suggestion_hashes*, or their legacy ID (e.g. ``S001``) against
    *old_skipped_ids*. Groups left with zero suggestions after individual
    filtering are dropped entirely.

    Unmatched hashes in the skip sets produce a warning on stderr rather than
    being silently ignored.

    Args:
        groups: List of group dicts, each containing a ``suggestions`` list.
            Each group should have a ``group_hash`` field, and each suggestion
            should have a ``suggestion_hash`` field (stamped by stamp_stable_ids).
        skipped_group_hashes: Group hash strings to skip entirely.
        skipped_suggestion_hashes: Suggestion hash strings to skip.
        old_skipped_ids: Legacy IDs (e.g. ``S001``) to skip.

    Returns:
        Tuple of (filtered_groups, user_skipped_count)
    """
    import re

    # --- Sanitize skipped_group_hashes: filter out non-str elements ---
    sanitized_group_hashes: Set[str] = set()
    for h in skipped_group_hashes:
        if not isinstance(h, str):
            print(
                f"WARNING: Skipped group hash {h!r} is not a string. "
                f"Ignoring.",
                file=sys.stderr,
            )
        else:
            sanitized_group_hashes.add(h)
    skipped_group_hashes = sanitized_group_hashes

    # --- Build set of known group hashes for validation ---
    known_group_hashes: Set[str] = set()
    known_suggestion_hashes: Set[str] = set()
    for group in groups:
        ghash = group.get("group_hash", "")
        if ghash:
            known_group_hashes.add(ghash)
        for sugg in group.get("suggestions", []):
            shash = sugg.get("suggestion_hash", "")
            if shash:
                known_suggestion_hashes.add(shash)

    # --- Warn about unmatched group hashes ---
    hex_re = re.compile(r'^[0-9a-f]{8,16}$')
    for h in sorted(skipped_group_hashes):
        if not hex_re.match(h):
            print(
                f"WARNING: Skipped group hash '{h}' is malformed "
                f"(expected 8-16 char hex string). Ignoring.",
                file=sys.stderr,
            )
        elif h not in known_group_hashes:
            # Check prefix match (display hash may be 8 chars of 16-char canonical)
            prefix_matches = [kh for kh in known_group_hashes if kh.startswith(h)]
            if prefix_matches:
                # Use the prefix match (should be exactly one)
                if len(prefix_matches) == 1:
                    skipped_group_hashes = (skipped_group_hashes - {h}) | {prefix_matches[0]}
                else:
                    print(
                        f"WARNING: Skipped group hash '{h}' matches multiple "
                        f"groups ({len(prefix_matches)} matches). Ignoring.",
                        file=sys.stderr,
                    )
            else:
                print(
                    f"WARNING: Skipped group hash '{h}' does not match any "
                    f"group in the current groups. Ignoring.",
                    file=sys.stderr,
                )

    # --- Sanitize skipped_suggestion_hashes ---
    sanitized_suggestion_hashes: Set[str] = set()
    for h in skipped_suggestion_hashes:
        if not isinstance(h, str):
            print(
                f"WARNING: Skipped suggestion hash {h!r} is not a string. "
                f"Ignoring.",
                file=sys.stderr,
            )
        else:
            sanitized_suggestion_hashes.add(h)
    skipped_suggestion_hashes = sanitized_suggestion_hashes

    # --- Resolve prefix matches for suggestion hashes ---
    resolved_suggestion_hashes: Set[str] = set()
    for h in skipped_suggestion_hashes:
        if h in known_suggestion_hashes:
            resolved_suggestion_hashes.add(h)
        else:
            # Check prefix match
            prefix_matches = [kh for kh in known_suggestion_hashes if kh.startswith(h)]
            if len(prefix_matches) == 1:
                resolved_suggestion_hashes.add(prefix_matches[0])
            elif len(prefix_matches) > 1:
                print(
                    f"WARNING: Skipped suggestion hash '{h}' matches multiple "
                    f"suggestions ({len(prefix_matches)} matches). Ignoring.",
                    file=sys.stderr,
                )
            else:
                if hex_re.match(h):
                    print(
                        f"WARNING: Skipped suggestion hash '{h}' does not match "
                        f"any suggestion in the current groups. Ignoring.",
                        file=sys.stderr,
                    )
                # If not hex, it might be a legacy G-format ID; skip silently
    skipped_suggestion_hashes = resolved_suggestion_hashes

    # --- Filter groups and suggestions ---
    result = []
    user_skipped_count = 0
    for group in groups:
        group_hash = group.get("group_hash", "")

        # Skip entire group if its hash is in the skip set
        if group_hash and group_hash in skipped_group_hashes:
            user_skipped_count += len(group.get("suggestions", []))
            continue

        # Filter individual suggestions within the group
        original_suggestions = group.get("suggestions", [])
        filtered_suggestions = []
        for sugg in original_suggestions:
            sugg_hash = sugg.get("suggestion_hash", "")
            old_id = sugg.get("id", "")  # Old format ID like "S001"

            # Skip if hash matches
            if sugg_hash and sugg_hash in skipped_suggestion_hashes:
                user_skipped_count += 1
                continue
            # Skip if legacy ID matches
            if old_id and old_id in old_skipped_ids:
                user_skipped_count += 1
                continue

            filtered_suggestions.append(sugg)

        # Only include group if it has remaining suggestions
        if filtered_suggestions:
            group_copy = dict(group)
            group_copy["suggestions"] = filtered_suggestions
            result.append(group_copy)
        elif original_suggestions:
            # Group had suggestions but all were skipped
            pass  # Already counted individually

    return result, user_skipped_count
