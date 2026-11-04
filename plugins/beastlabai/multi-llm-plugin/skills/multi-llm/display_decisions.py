#!/usr/bin/env python3
"""
Display a formatted summary of suggestion/fix decisions from orchestrator output.

Reads orchestrator_output.json and shows which items will be applied, skipped,
need human review, etc., with their titles.

Usage:
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util decisions \
        --output-file plans/my-feature/apply-suggestions/orchestrator_output.json

    # Or auto-detect from plan path + phase:
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util decisions \
        --plan-file plans/my-feature.md --phase apply-suggestions
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.stream_bootstrap import bootstrap_streams
from utils.human_decisions import judge_source_label
from utils.judge_vocab import JUDGE_SKIPPED, upgrade_legacy
from utils.output_handler import sanitize_prefix, get_phase_dir


def load_output(path: str) -> dict:
    # An output written before the judge rename says `claude_skipped`.
    with open(path, "r", encoding="utf-8") as f:
        return upgrade_legacy(json.load(f))


def get_title(item: dict) -> str:
    return item.get("title") or item.get("theme") or "Untitled"


def get_importance(item: dict) -> str:
    return (item.get("importance") or "MEDIUM").upper()


def importance_badge(imp: str) -> str:
    return {"HIGH": "HIGH", "MEDIUM": "MED", "LOW": "LOW"}.get(imp, imp)


def format_item_line(item: dict, index: int) -> str:
    title = get_title(item)
    imp = importance_badge(get_importance(item))
    parts = [f"  {index}. [{imp}] {title}"]
    if item.get("auto_approved"):
        parts[0] += f"  (auto-approved: {item.get('auto_approval_reason', '')})"
    if item.get("edited"):
        parts[0] += "  (description edited)"
    return parts[0]


def display(data: dict, phase: str) -> None:
    is_task_suggestions = phase == "apply-task-suggestions"
    is_code_fixes = "fix" in phase
    if is_task_suggestions:
        item_noun = "task suggestion"
        item_noun_plural = "task suggestions"
    elif is_code_fixes:
        item_noun = "fix"
        item_noun_plural = "fixes"
    else:
        item_noun = "suggestion"
        item_noun_plural = "suggestions"

    to_apply = data.get("to_apply", [])
    needs_human = data.get("needs_human_review", [])
    skipped_items = data.get("skipped_items", [])
    user_skipped_items = data.get("user_skipped_items", [])
    edited_descriptions = data.get("edited_descriptions", [])
    summary = data.get("summary", {})

    # Build set of edited item IDs for marking in the apply list
    edited_ids = set()
    for ed in edited_descriptions:
        edited_ids.add(ed.get("id", ""))
        edited_ids.add(ed.get("title", ""))

    # Mark edited items in to_apply
    for item in to_apply:
        if item.get("title") in edited_ids:
            item["edited"] = True

    total_groups = summary.get("total_groups", summary.get("total_issues", 0))
    valid_count = len(to_apply)
    human_count = len(needs_human)
    skipped_count = len(skipped_items)
    user_skipped_count = len(user_skipped_items)

    # Header
    if is_task_suggestions:
        header = "Task Suggestion Decision Summary"
    elif is_code_fixes:
        header = "Code Fix Decision Summary"
    else:
        header = "Suggestion Decision Summary"
    print(f"\n{'=' * 60}")
    print(f"  {header}")
    print(f"{'=' * 60}")
    print(f"  Total groups: {total_groups}")
    print()

    counter = 1

    # Will Apply
    auto_count = sum(1 for i in to_apply if i.get("auto_approved"))
    label = f"WILL APPLY ({valid_count} {item_noun_plural})"
    if auto_count:
        label += f"  [{auto_count} auto-approved]"
    print(f"  + {label}")
    if to_apply:
        for item in to_apply:
            print(format_item_line(item, counter))
            counter += 1
    else:
        print(f"    (none)")
    print()

    # Needs Human Review
    if needs_human:
        print(f"  ? NEEDS HUMAN REVIEW ({human_count} {item_noun_plural})")
        for item in needs_human:
            title = get_title(item)
            imp = importance_badge(get_importance(item))
            reason = item.get("validation_reason", "")
            line = f"  {counter}. [{imp}] {title}"
            if reason:
                line += f"  -- {reason}"
            print(line)
            counter += 1
        print()

    # Invalid / Validation Skipped
    invalid_items = [i for i in skipped_items if i.get("status") == "invalid"]
    bulk_skipped = [i for i in skipped_items if i.get("status") == "bulk_skipped"]
    priority_filtered = [i for i in skipped_items if i.get("status") == "below_priority"]
    # The judge's own skips. Bucketed apart from `invalid` because they are the
    # opposite kind of outcome: validation said the item was wrong, whereas this
    # is a decision the judge agent made on the user's behalf about an item
    # validation could not settle — and this command is the one surface whose
    # whole job is to say what was decided.
    judge_skipped = [i for i in skipped_items if i.get("status") == JUDGE_SKIPPED]
    other_skipped = [i for i in skipped_items
                     if i.get("status") not in ("invalid", "bulk_skipped",
                                                "below_priority", JUDGE_SKIPPED)]

    if invalid_items:
        print(f"  x INVALID ({len(invalid_items)} {item_noun_plural})")
        for item in invalid_items:
            title = get_title(item)
            imp = importance_badge(get_importance(item))
            reason = item.get("reason", "")
            line = f"  {counter}. [{imp}] {title}"
            if reason:
                line += f"  -- {reason}"
            print(line)
            counter += 1
        print()

    if bulk_skipped:
        print(f"  - BULK SKIPPED ({len(bulk_skipped)} {item_noun_plural})")
        for item in bulk_skipped:
            title = get_title(item)
            imp = importance_badge(get_importance(item))
            reason = item.get("reason", "")
            line = f"  {counter}. [{imp}] {title}"
            if reason:
                line += f"  -- {reason}"
            print(line)
            counter += 1
        print()

    if judge_skipped:
        print(f"  ! SKIPPED BY THE JUDGE AGENT ({len(judge_skipped)} {item_noun_plural})")
        for item in judge_skipped:
            title = get_title(item)
            imp = importance_badge(get_importance(item))
            reason = item.get("reason", "")
            source = item.get("decision_source", "")
            line = f"  {counter}. [{imp}] {title}"
            if source:
                line += f"  ({judge_source_label(source)})"
            if reason:
                line += f"  -- {reason}"
            print(line)
            counter += 1
        print()

    if priority_filtered:
        print(f"  - BELOW PRIORITY ({len(priority_filtered)} {item_noun_plural})")
        for item in priority_filtered:
            title = get_title(item)
            imp = importance_badge(get_importance(item))
            print(f"  {counter}. [{imp}] {title}")
            counter += 1
        print()

    if other_skipped:
        print(f"  - SKIPPED ({len(other_skipped)} {item_noun_plural})")
        for item in other_skipped:
            title = get_title(item)
            imp = importance_badge(get_importance(item))
            reason = item.get("reason", "")
            line = f"  {counter}. [{imp}] {title}"
            if reason:
                line += f"  -- {reason}"
            print(line)
            counter += 1
        print()

    # User Skipped
    if user_skipped_items:
        print(f"  ~ USER SKIPPED ({user_skipped_count} {item_noun_plural})")
        for item in user_skipped_items:
            title = get_title(item)
            imp = importance_badge(get_importance(item))
            print(f"  {counter}. [{imp}] {title}")
            counter += 1
        print()

    # Edited descriptions note
    edited_in_apply = [i for i in to_apply if i.get("edited")]
    if edited_in_apply:
        print(f"  * {len(edited_in_apply)} {item_noun_plural} have user-edited descriptions")
        print()

    print(f"{'=' * 60}")
    print()


def resolve_output_file(args: argparse.Namespace) -> str:
    if args.output_file:
        return args.output_file

    if not args.plan_file or not args.phase:
        print("ERROR: Provide --output-file or both --plan-file and --phase", file=sys.stderr)
        sys.exit(1)

    phase_map = {
        "apply-suggestions": "apply-suggestions",
        "apply-code-fixes": "apply-fixes",
        "apply-fixes": "apply-fixes",
        "apply-task-suggestions": "apply-task-suggestions",
    }
    phase_dir_name = phase_map.get(args.phase, args.phase)
    phase_dir = get_phase_dir(Path(args.plan_file), phase_dir_name)
    return str(phase_dir / "orchestrator_output.json")


def main(argv=None) -> int:
    bootstrap_streams()
    parser = argparse.ArgumentParser(description="Display decision summary from orchestrator output")
    parser.add_argument("--output-file", help="Path to orchestrator_output.json")
    parser.add_argument("--plan-file", help="Path to plan file (used with --phase)")
    parser.add_argument(
        "--phase",
        choices=["apply-suggestions", "apply-code-fixes", "apply-task-suggestions"],
        help="Phase name: apply-suggestions, apply-code-fixes, or apply-task-suggestions",
    )
    args = parser.parse_args(argv)

    output_path = resolve_output_file(args)
    if args.phase:
        phase = args.phase
    elif "task-suggestions" in output_path:
        phase = "apply-task-suggestions"
    elif "fix" in output_path:
        phase = "apply-code-fixes"
    else:
        phase = "apply-suggestions"

    if not Path(output_path).exists():
        print(f"ERROR: Output file not found: {output_path}", file=sys.stderr)
        sys.exit(1)

    data = load_output(output_path)
    display(data, phase)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
