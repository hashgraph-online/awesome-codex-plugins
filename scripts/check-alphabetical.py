#!/usr/bin/env python3
"""Verify that README list entries do not introduce alphabetical regressions.

Supports pinned entries: any list item preceded by `<!-- pinned -->` is treated as
always-first and excluded from alphabetical checking. With ``--base-ref``, existing
inversions in the base revision are treated as baseline debt while new inversions fail.
"""

import argparse
from collections import Counter
import re
import subprocess
import sys
from pathlib import Path


Inversion = tuple[str, str, str]


def extract_sections_from_text(content: str) -> list[tuple[str, list[str]]]:
    """Extract sections and their list items from a markdown file.

    Returns ``(section_heading, items)`` pairs where items are normalized display text.
    """
    lines = content.split("\n")

    sections = []
    current_heading = None
    current_items: list[tuple[str, int]] = []  # (display_text, line_number)

    # Regex for markdown list items with links: "- [Display Text](url) - description"
    # Also handles plain list items: "- Display Text - description"
    item_re = re.compile(r"^- \[([^\]]+)\]\([^)]+\)", re.IGNORECASE)

    for i, line in enumerate(lines, 1):
        # Detect section headers (## or ###)
        heading_match = re.match(r"^(#{2,3})\s+(.+)", line)
        # Also detect <summary> tags as section boundaries inside <details>
        summary_match = re.match(r"<summary>(.+)</summary>", line.strip())

        if heading_match:
            # Save previous section if it has items
            if current_heading and current_items:
                sections.append((current_heading, [t for t, _ in current_items]))
            current_heading = heading_match.group(2).strip()
            current_items = []
        elif summary_match:
            if current_heading and current_items:
                sections.append((current_heading, [t for t, _ in current_items]))
            current_heading = f"[{summary_match.group(1).strip()}]"
            current_items = []
        elif item_re.match(line):
            display_text = item_re.match(line).group(1)
            # Skip pinned entries
            if i > 1 and re.search(r"<!--\s*pinned\s*-->", lines[i - 2]):
                continue
            current_items.append((display_text.lower(), i))

    # Don't forget the last section
    if current_heading and current_items:
        sections.append((current_heading, [t for t, _ in current_items]))

    return sections


def extract_sections(filepath: str) -> list[tuple[str, list[str]]]:
    """Extract sections from a UTF-8 markdown file."""

    return extract_sections_from_text(Path(filepath).read_text(encoding="utf-8"))


def inversion_counts(sections: list[tuple[str, list[str]]]) -> Counter[Inversion]:
    """Return every out-of-order item pair, grouped by section."""

    inversions: Counter[Inversion] = Counter()
    for heading, items in sections:
        if heading == "Contents":
            continue
        for index, left in enumerate(items):
            for right in items[index + 1 :]:
                if left > right:
                    inversions[(heading, left, right)] += 1
    return inversions


def new_inversion_counts(
    head_sections: list[tuple[str, list[str]]],
    base_sections: list[tuple[str, list[str]]] | None = None,
) -> tuple[Counter[Inversion], Counter[Inversion]]:
    """Return newly introduced inversions and all inversions in the head."""

    head = inversion_counts(head_sections)
    base = inversion_counts(base_sections or [])
    return head - base, head


def read_base_sections(base_ref: str, filepath: str) -> list[tuple[str, list[str]]]:
    """Read the markdown file from a git revision and extract its sections."""

    path = Path(filepath)
    try:
        repo_path = path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        repo_path = path.as_posix()
    result = subprocess.run(
        ["git", "show", f"{base_ref}:{repo_path}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or "git show returned no content"
        raise RuntimeError(f"could not read {repo_path} from {base_ref}: {detail}")
    return extract_sections_from_text(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("readme", nargs="?", default="README.md")
    parser.add_argument(
        "--base-ref",
        help="Allow inversions already present in this git revision while rejecting new ones.",
    )
    args = parser.parse_args()
    readme = args.readme

    if not Path(readme).exists():
        print(f"ERROR: {readme} not found")
        sys.exit(1)

    sections = extract_sections(readme)
    try:
        base_sections = read_base_sections(args.base_ref, readme) if args.base_ref else None
    except RuntimeError as error:
        print(f"ERROR: {error}")
        sys.exit(1)

    new_inversions, all_inversions = new_inversion_counts(sections, base_sections)
    errors = 0

    for heading, items in sections:
        if not items or heading == "Contents":
            continue
        section_new = [
            (left, right, count)
            for (section, left, right), count in new_inversions.items()
            if section == heading
        ]
        section_all = sum(
            count
            for (section, _left, _right), count in all_inversions.items()
            if section == heading
        )
        if section_new:
            print(f"FAIL: Section '{heading}' is not alphabetically sorted.")
            for left, right, count in section_new[:5]:
                suffix = f" ({count} occurrences)" if count > 1 else ""
                print(f"  New inversion: {left} appears before {right}{suffix}")
            errors += 1
        elif section_all:
            print(
                f"OK:   '{heading}' ({len(items)} items; "
                f"{section_all} baseline inversion(s) unchanged)"
            )
        else:
            print(f"OK:   '{heading}' ({len(items)} items)")

    if errors:
        print(f"\n{errors} section(s) introduced alphabetical regressions.")
        sys.exit(1)
    else:
        if args.base_ref:
            print("\nNo new alphabetical inversions were introduced.")
        else:
            print("\nAll sections are alphabetically sorted.")
        sys.exit(0)


if __name__ == "__main__":
    main()
