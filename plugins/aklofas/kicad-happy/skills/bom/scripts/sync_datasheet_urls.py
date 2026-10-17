#!/usr/bin/env python3
"""Sync datasheet URLs from datasheets/manifest.json back into KiCad schematic properties.

After running datasheet sync scripts (DigiKey, LCSC, element14), this script
reads the datasheets/manifest.json file (legacy name index.json still supported)
and writes the discovered datasheet URLs back into the schematic's Datasheet
properties.

Opportunistic: only fills in missing/empty URLs by default. Warns about
mismatched URLs without overwriting unless --overwrite is specified.

Usage:
    # Preview changes (dry run)
    python3 sync_datasheet_urls.py path/to/schematic.kicad_sch --dry-run

    # Apply — fill empty Datasheet fields, warn about mismatches
    python3 sync_datasheet_urls.py path/to/schematic.kicad_sch

    # Also overwrite mismatched URLs (after reviewing warnings)
    python3 sync_datasheet_urls.py path/to/schematic.kicad_sch --overwrite

    # Recursive (include sub-sheets)
    python3 sync_datasheet_urls.py path/to/schematic.kicad_sch --recursive

    # Custom datasheets directory
    python3 sync_datasheet_urls.py path/to/schematic.kicad_sch --datasheets ./datasheets
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent))
from edit_properties import apply_updates
from kicad_sexp import collect_schematic_files, find_matching_paren


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def is_empty_datasheet(value: str) -> bool:
    """Return True if the Datasheet property is effectively empty."""
    v = value.strip()
    return not v or v == "~"


def normalize_url(url: str) -> str:
    """Normalize a URL for comparison purposes."""
    url = url.strip().rstrip("/")
    parsed = urlparse(url)
    # Normalize scheme to https for comparison
    scheme = "https" if parsed.scheme in ("http", "https") else parsed.scheme
    # Lowercase the netloc (domain)
    netloc = parsed.netloc.lower()
    # Keep path and query as-is (case-sensitive on most servers, query
    # params like ?v=2 can distinguish datasheet versions)
    path = parsed.path.rstrip("/")
    result = f"{scheme}://{netloc}{path}"
    if parsed.query:
        result += f"?{parsed.query}"
    return result


def urls_match(a: str, b: str) -> bool:
    """Compare two URLs, ignoring trivial differences."""
    return normalize_url(a) == normalize_url(b)


# ---------------------------------------------------------------------------
# Schematic parsing (lightweight — only extracts Reference + Datasheet)
# ---------------------------------------------------------------------------

def extract_ref_datasheets(text: str) -> dict[str, str]:
    """Extract {reference: datasheet_url} from placed symbols in a schematic."""
    result = {}

    # Skip lib_symbols section
    lib_match = re.search(r'\(lib_symbols\b', text)
    search_start = 0
    if lib_match:
        lib_end = find_matching_paren(text, lib_match.start())
        search_start = lib_end + 1

    # Find placed symbols
    pattern = re.compile(r'\(symbol\s*\n?\s*\(lib_id\s+')
    for match in pattern.finditer(text, search_start):
        sym_start = match.start()
        sym_end = find_matching_paren(text, sym_start)
        block = text[sym_start:sym_end + 1]

        ref_match = re.search(
            r'\(property\s+"Reference"\s+"((?:[^"\\]|\\.)*)"', block
        )
        if not ref_match:
            continue
        ref = ref_match.group(1)
        if ref.startswith("#"):
            continue

        ds_match = re.search(
            r'\(property\s+"Datasheet"\s+"((?:[^"\\]|\\.)*)"', block
        )
        ds = ds_match.group(1) if ds_match else ""
        result[ref] = ds

    return result


# ---------------------------------------------------------------------------
# Index loading
# ---------------------------------------------------------------------------

def build_ref_url_map(index: dict) -> dict[str, dict]:
    """Build {reference: {url, mpn, source, verification}} from index.json.

    Only includes parts with status=ok and a valid datasheet_url.
    Skips parts flagged as wrong datasheets by the verification step.
    """
    ref_map = {}
    for part_key, entry in index.get("parts", {}).items():
        if entry.get("status") != "ok":
            continue
        url = entry.get("datasheet_url", "").strip()
        if not url:
            continue
        # Don't propagate URLs that verification flagged as wrong
        if entry.get("verification") == "wrong":
            continue
        for ref in entry.get("references", []):
            ref_map[ref] = {
                "url": url,
                "mpn": part_key,
                "source": entry.get("source", ""),
                "verification": entry.get("verification", ""),
            }
    return ref_map


# ---------------------------------------------------------------------------
# Main sync logic
# ---------------------------------------------------------------------------

def sync_datasheet_urls(
    schematic_path: str,
    datasheets_dir: str | None = None,
    recursive: bool = False,
    overwrite: bool = False,
    dry_run: bool = False,
    backup: bool = False,
) -> dict:
    """Sync datasheet URLs from index.json into schematic Datasheet properties.

    Returns summary dict with counts and mismatch details.
    """
    schematic_path = Path(schematic_path).resolve()
    if not schematic_path.exists():
        print(f"Error: {schematic_path} not found", file=sys.stderr)
        return {"error": "schematic not found"}

    # Find datasheets directory
    if datasheets_dir:
        ds_dir = Path(datasheets_dir).resolve()
    else:
        ds_dir = schematic_path.parent / "datasheets"
    if not ds_dir.exists():
        print(f"Error: datasheets directory not found at {ds_dir}", file=sys.stderr)
        print("  Run a datasheet sync first (DigiKey, LCSC, or element14).", file=sys.stderr)
        return {"error": "no datasheets directory"}

    index_path = ds_dir / "manifest.json"
    if not index_path.exists():
        index_path = ds_dir / "index.json"
    if not index_path.exists():
        print(f"Error: {ds_dir / 'manifest.json'} not found", file=sys.stderr)
        print("  Run a datasheet sync first to generate the manifest.", file=sys.stderr)
        return {"error": "no manifest"}

    with open(index_path, "r") as f:
        index = json.load(f)

    # Build ref→url mapping from manifest
    ref_url_map = build_ref_url_map(index)
    if not ref_url_map:
        print("No datasheet URLs available in manifest (no parts with status=ok).",
              file=sys.stderr)
        return {"error": "no urls in manifest"}

    # Collect schematic files
    sch_files = collect_schematic_files(schematic_path, recursive)
    print(f"Processing {len(sch_files)} schematic file(s)...", file=sys.stderr)

    # Track results
    total_filled = 0
    total_skipped = 0
    total_already_correct = 0
    total_mismatched = 0
    total_overwritten = 0
    mismatches = []
    fills = []
    files_modified = 0

    for sch_file in sch_files:
        text = sch_file.read_text(encoding="utf-8")
        current = extract_ref_datasheets(text)

        updates = {}
        for ref, current_ds in current.items():
            if ref not in ref_url_map:
                total_skipped += 1
                continue

            info = ref_url_map[ref]
            new_url = info["url"]

            if is_empty_datasheet(current_ds):
                # Fill in the missing URL
                updates[ref] = {"Datasheet": new_url}
                fills.append({
                    "reference": ref,
                    "mpn": info["mpn"],
                    "url": new_url,
                    "file": sch_file.name,
                })
                total_filled += 1
            elif urls_match(current_ds, new_url):
                total_already_correct += 1
            else:
                # Mismatch — current URL differs from index URL
                mismatches.append({
                    "reference": ref,
                    "mpn": info["mpn"],
                    "current": current_ds,
                    "index": new_url,
                    "source": info["source"],
                    "file": sch_file.name,
                })
                total_mismatched += 1
                if overwrite:
                    updates[ref] = {"Datasheet": new_url}
                    total_overwritten += 1

        if not updates:
            continue

        if dry_run:
            for ref, props in sorted(updates.items()):
                info = ref_url_map[ref]
                action = "overwrite" if ref in [m["reference"] for m in mismatches] else "fill"
                print(f"  [{sch_file.name}] {ref} ({info['mpn']}): "
                      f"would {action} Datasheet", file=sys.stderr)
        else:
            modified_text, change_log = apply_updates(text, updates)

            # Backup if requested
            if backup:
                from datetime import datetime
                import shutil
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = sch_file.with_suffix(f".{timestamp}.bak")
                shutil.copy2(sch_file, backup_path)
                print(f"  Backup: {backup_path}", file=sys.stderr)

            sch_file.write_text(modified_text, encoding="utf-8")
            files_modified += 1

    # Report fills
    if fills:
        label = "Would fill" if dry_run else "Filled"
        print(f"\n{label} {len(fills)} empty Datasheet field(s):", file=sys.stderr)
        for f in fills:
            print(f"  {f['reference']} ({f['mpn']}): {f['url'][:80]}",
                  file=sys.stderr)

    # Report mismatches
    if mismatches:
        print(f"\nMismatched datasheet URLs ({len(mismatches)}):", file=sys.stderr)
        for m in mismatches:
            if overwrite:
                action = "OVERWRITTEN" if not dry_run else "would overwrite"
            else:
                action = "kept existing (use --overwrite to replace)"
            print(f"  {m['reference']} ({m['mpn']}) [{m['file']}]:", file=sys.stderr)
            print(f"    Schematic: {m['current']}", file=sys.stderr)
            print(f"    Index:     {m['index']} (from {m['source']})", file=sys.stderr)
            print(f"    Action:    {action}", file=sys.stderr)

    # Summary
    summary = {
        "filled": total_filled,
        "already_correct": total_already_correct,
        "mismatched": total_mismatched,
        "overwritten": total_overwritten,
        "skipped_no_index_entry": total_skipped,
        "files_modified": files_modified if not dry_run else 0,
        "mismatches": mismatches,
    }

    if dry_run:
        changes = total_filled + total_overwritten
        print(f"\nDry run: {changes} change(s) would be made.", file=sys.stderr)
    else:
        changes = total_filled + total_overwritten
        if changes:
            print(f"\nDone: {changes} Datasheet properties updated across "
                  f"{files_modified} file(s).", file=sys.stderr)
        else:
            print("\nNo changes needed.", file=sys.stderr)

    if total_already_correct:
        print(f"Already correct: {total_already_correct}", file=sys.stderr)

    # Lock file warning (same as edit_properties.py)
    if not dry_run and files_modified:
        for sch_file in sch_files:
            lock_path = sch_file.parent / f"{sch_file.name}.lck"
            if lock_path.exists():
                print(
                    f"\nWARNING: KiCad lock file detected for {sch_file.name}.\n"
                    f"Close and reopen the schematic (File > Open Recent) to see changes.\n"
                    f"Don't save from KiCad first — it will overwrite these changes.",
                    file=sys.stderr,
                )
                break  # One warning is enough

    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Sync datasheet URLs from index.json into KiCad schematic Datasheet properties",
    )
    parser.add_argument(
        "schematic",
        help="Path to root .kicad_sch file",
    )
    parser.add_argument(
        "--datasheets", "-d",
        help="Path to datasheets directory (default: datasheets/ next to schematic)",
    )
    parser.add_argument(
        "--recursive", "-r", action="store_true",
        help="Include hierarchical sub-sheets",
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Overwrite mismatched Datasheet URLs (default: warn only)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would change without modifying files",
    )
    parser.add_argument(
        "--backup", action="store_true",
        help="Create .bak backup files before writing (default: no backup, use git)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output summary as JSON to stdout",
    )
    args = parser.parse_args()

    result = sync_datasheet_urls(
        schematic_path=args.schematic,
        datasheets_dir=args.datasheets,
        recursive=args.recursive,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
        backup=args.backup,
    )

    if args.json:
        json.dump(result, sys.stdout, indent=2)
        print()

    if "error" in result:
        sys.exit(1)
    if result.get("mismatched", 0) > 0 and not args.overwrite:
        sys.exit(2)  # Signal mismatches need attention
    sys.exit(0)


if __name__ == "__main__":
    main()
