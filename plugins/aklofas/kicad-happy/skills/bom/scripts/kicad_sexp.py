"""Shared utilities for parsing KiCad S-expression (.kicad_sch) files.

Provides low-level helpers used by bom_manager.py, edit_properties.py,
and sync_datasheet_urls.py.
"""

from __future__ import annotations

import re
from pathlib import Path


def find_matching_paren(text: str, start: int) -> int:
    """Find the index of the closing paren matching the open paren at `start`.

    Raises ValueError if the parentheses are unbalanced (truncated or
    corrupted file).
    """
    depth = 1
    i = start + 1
    in_string = False
    while i < len(text) and depth > 0:
        c = text[i]
        if in_string:
            if c == '\\':
                i += 2
                continue
            elif c == '"':
                in_string = False
        else:
            if c == '"':
                in_string = True
            elif c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
        i += 1
    if depth > 0:
        raise ValueError(
            f"Unbalanced parentheses at position {start} "
            f"(reached end of text with depth {depth})"
        )
    return i - 1


def iter_placed_symbol_blocks(text: str) -> list[tuple[int, int, str]]:
    """Find all placed symbol blocks (not lib_symbols) in a .kicad_sch file.

    Returns list of (start_pos, end_pos, block_text) tuples, in file order.
    """
    symbols = []

    # Find end of lib_symbols section to skip it
    lib_match = re.search(r'\(lib_symbols\b', text)
    search_start = 0
    if lib_match:
        lib_end = find_matching_paren(text, lib_match.start())
        search_start = lib_end + 1

    # Placed symbols have (lib_id ...) as first child; lib symbols have a
    # quoted name string instead. We look for the pattern:
    #   (symbol\n\t\t(lib_id   or   (symbol (lib_id
    pattern = re.compile(r'\(symbol\s*\n?\s*\(lib_id\s+')
    for match in pattern.finditer(text, search_start):
        sym_start = match.start()
        sym_end = find_matching_paren(text, sym_start)
        block = text[sym_start:sym_end + 1]
        symbols.append((sym_start, sym_end, block))

    return symbols


def escape_kicad_string(s: str) -> str:
    """Escape a string for use in a KiCad S-expression property value."""
    return s.replace('\\', '\\\\').replace('"', '\\"')


def find_sub_sheets(text: str, base_dir: Path) -> list[Path]:
    """Find hierarchical sub-sheet files referenced in a .kicad_sch."""
    sheets = []
    for match in re.finditer(r'\(sheet\b', text):
        sheet_start = match.start()
        sheet_end = find_matching_paren(text, sheet_start)
        block = text[sheet_start:sheet_end + 1]
        file_match = re.search(
            r'\(property\s+"Sheetfile"\s+"((?:[^"\\]|\\.)*)"', block
        )
        if file_match:
            filepath = base_dir / file_match.group(1)
            if filepath.exists():
                sheets.append(filepath)
    return sheets


def collect_schematic_files(root: Path, recursive: bool) -> list[Path]:
    """Collect root schematic and optionally all sub-sheets recursively."""
    files = [root.resolve()]
    if not recursive:
        return files

    visited = {root.resolve()}
    queue = [root.resolve()]
    while queue:
        current = queue.pop(0)
        text = current.read_text(encoding="utf-8")
        for sub in find_sub_sheets(text, current.parent):
            sub = sub.resolve()
            if sub not in visited:
                visited.add(sub)
                files.append(sub)
                queue.append(sub)
    return files
