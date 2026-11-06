#!/usr/bin/env python3
"""Edit KiCad schematic symbol properties — add or update BOM fields.

Reads a .kicad_sch file, applies property updates to symbols identified by
reference designator, and writes the modified file back.

Updates are provided as JSON, either from a file or stdin.

Usage:
    # Apply updates from a JSON file
    python3 edit_properties.py path/to/schematic.kicad_sch --updates updates.json

    # Pipe updates from stdin
    echo '{"R1": {"MPN": "RC0805FR-0710KL"}}' | python3 edit_properties.py schematic.kicad_sch

    # Create a backup before writing
    python3 edit_properties.py schematic.kicad_sch --updates updates.json --backup

    # Dry run — show what would change without writing
    python3 edit_properties.py schematic.kicad_sch --updates updates.json --dry-run

Update JSON format:
    {
        "R1": {
            "MPN": "RC0805FR-0710KL",
            "Manufacturer": "Yageo",
            "DigiKey": "311-10.0KCRCT-ND"
        },
        "C1": {
            "MPN": "GRM155R71C104KA88D",
            "Datasheet": "https://example.com/datasheet.pdf"
        }
    }

Each key is a reference designator. The value is a dict of property name -> value.
Properties that already exist are updated; new properties are added (hidden).
To clear a property value, set it to an empty string "".
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from kicad_sexp import escape_kicad_string, find_matching_paren, iter_placed_symbol_blocks


# ---------------------------------------------------------------------------
# Symbol finder
# ---------------------------------------------------------------------------

def find_placed_symbols(text: str) -> list[tuple[int, int, str]]:
    """Find all placed symbol blocks and their positions in the text.

    Returns list of (start_pos, end_pos, reference) tuples.
    """
    symbols = []

    for sym_start, sym_end, block in iter_placed_symbol_blocks(text):
        # Extract reference
        ref_match = re.search(
            r'\(property\s+"Reference"\s+"((?:[^"\\]|\\.)*)"', block
        )
        ref = ref_match.group(1) if ref_match else ""
        symbols.append((sym_start, sym_end, ref))

    return symbols


# ---------------------------------------------------------------------------
# Property editor
# ---------------------------------------------------------------------------

def find_property_in_block(text: str, sym_start: int, sym_end: int, prop_name: str) -> tuple[int, int] | None:
    """Find a property entry within a symbol block.

    Returns (start, end) positions of the entire (property ...) block, or None.
    """
    block = text[sym_start:sym_end + 1]
    escaped_name = re.escape(prop_name)
    pattern = re.compile(rf'\(property\s+"{escaped_name}"\s+"')

    match = pattern.search(block)
    if not match:
        return None

    prop_start = sym_start + match.start()
    prop_end = find_matching_paren(text, prop_start)
    return (prop_start, prop_end)


def find_last_property_end(text: str, sym_start: int, sym_end: int) -> int:
    """Find the end position of the last property block in a symbol.

    Returns the position right after the closing paren of the last property.
    """
    block = text[sym_start:sym_end + 1]
    last_prop_end = sym_start  # fallback

    for match in re.finditer(r'\(property\s+"', block):
        prop_start = sym_start + match.start()
        prop_end = find_matching_paren(text, prop_start)
        if prop_end > last_prop_end:
            last_prop_end = prop_end

    return last_prop_end


def detect_indentation(text: str, sym_start: int, sym_end: int) -> str:
    """Detect the indentation used for properties in this symbol."""
    block = text[sym_start:sym_end + 1]
    match = re.search(r'\n(\s+)\(property\s+"', block)
    if match:
        return match.group(1)
    return "\t\t"  # default to 2 tabs


def build_new_property(
    prop_name: str,
    prop_value: str,
    indent: str,
) -> str:
    """Build a new (property ...) block for insertion."""
    escaped_value = escape_kicad_string(prop_value)
    inner = indent + "\t"
    return (
        f'\n{indent}(property "{prop_name}" "{escaped_value}" (at 0 0 0)\n'
        f'{inner}(effects\n'
        f'{inner}\t(font\n'
        f'{inner}\t\t(size 1.27 1.27)\n'
        f'{inner}\t)\n'
        f'{inner}\t(hide yes)\n'
        f'{inner})\n'
        f'{indent})'
    )


def update_property_value(
    text: str,
    prop_start: int,
    prop_end: int,
    prop_name: str,
    new_value: str,
) -> str:
    """Replace the value of an existing property, preserving all formatting."""
    old_block = text[prop_start:prop_end + 1]
    escaped_value = escape_kicad_string(new_value)

    # Replace just the value string after the property name
    escaped_name = re.escape(prop_name)
    new_block = re.sub(
        rf'(\(property\s+"{escaped_name}"\s+)"(?:[^"\\]|\\.)*"',
        lambda m: f'{m.group(1)}"{escaped_value}"',
        old_block,
        count=1,
    )

    return text[:prop_start] + new_block + text[prop_end + 1:]


# ---------------------------------------------------------------------------
# Main edit logic
# ---------------------------------------------------------------------------

def apply_updates(
    text: str,
    updates: dict[str, dict[str, str]],
    dry_run: bool = False,
) -> tuple[str, list[dict]]:
    """Apply property updates to schematic text.

    Args:
        text: Full .kicad_sch file contents
        updates: {reference: {prop_name: value, ...}, ...}
        dry_run: If True, compute changes but don't modify text

    Returns:
        (modified_text, change_log)
    """
    change_log = []

    # Find all placed symbols
    symbols = find_placed_symbols(text)
    ref_to_symbols = {}
    for start, end, ref in symbols:
        ref_to_symbols.setdefault(ref, []).append((start, end))

    # Check for missing references
    for ref in updates:
        if ref not in ref_to_symbols:
            change_log.append({
                "reference": ref,
                "action": "error",
                "message": f"Reference '{ref}' not found in schematic",
            })

    # Apply updates in reverse file order so positions don't shift
    # for changes we haven't made yet
    all_edits = []  # (position, reference, prop_name, action, old_value, new_value)

    for ref, props in updates.items():
        if ref not in ref_to_symbols:
            continue

        # A reference can appear multiple times (multi-unit symbols).
        # Update all instances.
        for sym_start, sym_end in ref_to_symbols[ref]:
            indent = detect_indentation(text, sym_start, sym_end)

            for prop_name, new_value in props.items():
                existing = find_property_in_block(text, sym_start, sym_end, prop_name)

                if existing:
                    prop_start, prop_end = existing
                    # Extract current value
                    old_block = text[prop_start:prop_end + 1]
                    old_match = re.search(
                        rf'\(property\s+"{re.escape(prop_name)}"\s+"((?:[^"\\]|\\.)*)"',
                        old_block,
                    )
                    old_value = old_match.group(1) if old_match else ""

                    if old_value == new_value:
                        change_log.append({
                            "reference": ref,
                            "property": prop_name,
                            "action": "unchanged",
                            "value": new_value,
                        })
                        continue

                    all_edits.append({
                        "type": "update",
                        "position": prop_start,
                        "sym_start": sym_start,
                        "sym_end": sym_end,
                        "prop_start": prop_start,
                        "prop_end": prop_end,
                        "prop_name": prop_name,
                        "old_value": old_value,
                        "new_value": new_value,
                        "reference": ref,
                    })
                else:
                    # New property — insert after last existing property
                    insert_pos = find_last_property_end(text, sym_start, sym_end)
                    all_edits.append({
                        "type": "insert",
                        "position": insert_pos,
                        "insert_after": insert_pos,
                        "prop_name": prop_name,
                        "new_value": new_value,
                        "reference": ref,
                        "indent": indent,
                    })

    if dry_run:
        for edit in all_edits:
            change_log.append({
                "reference": edit["reference"],
                "property": edit["prop_name"],
                "action": "would_" + edit["type"],
                "old_value": edit.get("old_value", "(new)"),
                "new_value": edit["new_value"],
            })
        return text, change_log

    # Apply edits in reverse position order so earlier edits don't
    # invalidate later positions. For multiple inserts in the same symbol,
    # they all share the same insert_after position (end of last property),
    # so reverse order stacks them correctly. Updates within the same symbol
    # are safe because each update preserves the block length of other
    # properties. Mixing updates + inserts in the same symbol works because
    # inserts go after all properties (higher position) and are applied first.
    all_edits.sort(key=lambda e: e["position"], reverse=True)

    for edit in all_edits:
        if edit["type"] == "update":
            text = update_property_value(
                text,
                edit["prop_start"],
                edit["prop_end"],
                edit["prop_name"],
                edit["new_value"],
            )
            change_log.append({
                "reference": edit["reference"],
                "property": edit["prop_name"],
                "action": "updated",
                "old_value": edit["old_value"],
                "new_value": edit["new_value"],
            })
        elif edit["type"] == "insert":
            new_prop = build_new_property(
                edit["prop_name"],
                edit["new_value"],
                edit["indent"],
            )
            pos = edit["insert_after"] + 1
            text = text[:pos] + new_prop + text[pos:]
            change_log.append({
                "reference": edit["reference"],
                "property": edit["prop_name"],
                "action": "added",
                "new_value": edit["new_value"],
            })

    return text, change_log


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Edit KiCad schematic symbol properties"
    )
    parser.add_argument("schematic", type=Path, help="Path to .kicad_sch file")
    parser.add_argument(
        "--updates", type=Path,
        help="Path to JSON file with updates (or pipe via stdin)",
    )
    parser.add_argument(
        "--backup", action="store_true",
        help="Create a .bak backup file before writing changes",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would change without writing",
    )
    args = parser.parse_args()

    if not args.schematic.exists():
        print(f"Error: {args.schematic} not found", file=sys.stderr)
        sys.exit(1)

    # Check for KiCad lock file — indicates schematic is open in KiCad
    lock_path = args.schematic.parent / f"{args.schematic.name}.lck"
    if lock_path.exists() and not args.dry_run:
        print(
            f"WARNING: KiCad lock file detected ({lock_path.name}).\n"
            f"The schematic appears to be open in KiCad. Changes will be\n"
            f"written to disk, but KiCad won't see them until you close and\n"
            f"reopen the schematic (File > Open Recent). If you save from\n"
            f"KiCad without reopening first, KiCad will overwrite these changes.",
            file=sys.stderr,
        )

    # Read updates
    if args.updates:
        updates = json.loads(args.updates.read_text(encoding="utf-8"))
    elif not sys.stdin.isatty():
        updates = json.load(sys.stdin)
    else:
        print("Error: provide updates via --updates file or stdin", file=sys.stderr)
        sys.exit(1)

    if not isinstance(updates, dict):
        print("Error: updates must be a JSON object {reference: {prop: value}}", file=sys.stderr)
        sys.exit(1)

    # Read schematic
    text = args.schematic.read_text(encoding="utf-8")

    # Apply updates
    modified_text, change_log = apply_updates(text, updates, dry_run=args.dry_run)

    # Report changes
    actions = {}
    for entry in change_log:
        action = entry["action"]
        actions[action] = actions.get(action, 0) + 1
        if action == "error":
            print(f"  ERROR: {entry['message']}", file=sys.stderr)
        elif action in ("updated", "would_update"):
            print(
                f"  {entry['reference']}.{entry['property']}: "
                f"'{entry['old_value']}' -> '{entry['new_value']}'",
                file=sys.stderr,
            )
        elif action in ("added", "would_insert"):
            print(
                f"  {entry['reference']}.{entry['property']}: "
                f"(new) = '{entry['new_value']}'",
                file=sys.stderr,
            )

    total_changes = actions.get("updated", 0) + actions.get("added", 0)
    total_would = actions.get("would_update", 0) + actions.get("would_insert", 0)

    if args.dry_run:
        print(f"\nDry run: {total_would} changes would be made.", file=sys.stderr)
        # Output the change log as JSON for programmatic use
        json.dump(change_log, sys.stdout, indent=2)
        print()
        return

    if total_changes == 0:
        print("No changes needed.", file=sys.stderr)
        return

    # Create backup if requested
    if args.backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = args.schematic.with_suffix(f".{timestamp}.bak")
        shutil.copy2(args.schematic, backup_path)
        print(f"Backup: {backup_path}", file=sys.stderr)

    # Write modified file
    args.schematic.write_text(modified_text, encoding="utf-8")
    print(
        f"\nDone: {total_changes} properties changed "
        f"({actions.get('updated', 0)} updated, {actions.get('added', 0)} added).",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
