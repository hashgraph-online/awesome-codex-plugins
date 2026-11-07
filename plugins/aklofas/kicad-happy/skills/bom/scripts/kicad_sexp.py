"""Shared utilities for parsing KiCad S-expression (.kicad_sch) files.

Provides low-level helpers used by bom_manager.py, edit_properties.py,
and sync_datasheet_urls.py.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

import _core_path  # noqa: F401
from kicad_core.fileio import atomic_write_text  # noqa: F401  (bom scripts import it from here)
from kicad_core.instances import (inline_instances, instance_variants, resolve_instance,
                                  variant_overrides)
from kicad_core.sexp import parse


def kicad_lock_path(sch: Path) -> Path:
    """The lock file KiCad keeps next to an open schematic: ``~name.kicad_sch.lck``."""
    return sch.with_name(f"~{sch.name}.lck")


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

    # Placed symbols start with (lib_id ...), or with (lib_name ...) then (lib_id ...) when
    # their local name differs from the library's; lib symbols have a quoted name instead.
    pattern = re.compile(r'\(symbol\s*(?:\(lib_name\s+"(?:[^"\\]|\\.)*"\)\s*)?\(lib_id\s+')
    for match in pattern.finditer(text, search_start):
        sym_start = match.start()
        sym_end = find_matching_paren(text, sym_start)
        block = text[sym_start:sym_end + 1]
        symbols.append((sym_start, sym_end, block))

    return symbols


_SCH_VERSION_RE = re.compile(r'\A\s*\(kicad_sch\s+\(version\s+(\d+)\)')


def sch_file_version(text: str) -> int | None:
    """The `(version N)` of a `.kicad_sch` text, or None when it has no such header."""
    m = _SCH_VERSION_RE.match(text)
    return int(m.group(1)) if m else None


def escape_kicad_string(s: str) -> str:
    """Escape a string for use in a KiCad S-expression property value."""
    return (s.replace('\\', '\\\\').replace('"', '\\"')
             .replace('\n', '\\n').replace('\r', '\\r'))


def direct_children(block: str):
    """Yield the text of each list that is a direct child of the s-expression *block*."""
    i = 1
    while i < len(block) - 1:
        c = block[i]
        if c == '"':
            i += 1
            while i < len(block) and block[i] != '"':
                i += 2 if block[i] == '\\' else 1
        elif c == '(':
            end = find_matching_paren(block, i)
            yield block[i:end + 1]
            i = end
        i += 1


def direct_value(block: str, token: str) -> str | None:
    """The text of the first direct child ``(token value)`` of *block* (quoted or not)."""
    pattern = re.compile(r'\(' + re.escape(token) + r'\s+(?:"((?:[^"\\]|\\.)*)"|([^\s()"]+))\s*\)$')
    for child in direct_children(block):
        m = pattern.match(child)
        if m:
            return m.group(1) if m.group(1) is not None else m.group(2)
    return None


def direct_child(block: str, token: str) -> str | None:
    """The text of the first direct child list of *block* that starts with *token*."""
    head = re.compile(r'\(' + re.escape(token) + r'[\s)]')
    for child in direct_children(block):
        if head.match(child):
            return child
    return None


# KiCad reads the sheet file property under its canonical and its KiCad 6 name, in any case.
_SHEET_FILE = re.compile(r'\(property\s+"(?i:sheetfile|sheet file)"\s+"((?:[^"\\]|\\.)*)"')
_AT = re.compile(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)')


class SubSheet(NamedTuple):
    path: Path
    uuid: str
    at: tuple[float, float]
    in_bom: bool
    dnp: bool
    block: str = ""


def find_sub_sheet_entries(text: str, base_dir: Path) -> list[SubSheet]:
    """Each ``(sheet ...)`` of a .kicad_sch whose file exists, in file order.

    ``in_bom`` / ``dnp`` are the sheet's own attributes (KiCad 9+; direct children only, so a
    variant's ``(dnp ...)`` inside the sheet's instances does not count).
    """
    sheets = []
    for match in re.finditer(r'\(sheet\b', text):
        sheet_start = match.start()
        sheet_end = find_matching_paren(text, sheet_start)
        block = text[sheet_start:sheet_end + 1]
        file_match = _SHEET_FILE.search(block)
        if not file_match:
            continue
        filepath = base_dir / file_match.group(1)
        if not filepath.exists():
            continue
        at = _AT.match(direct_child(block, "at") or "")
        sheets.append(SubSheet(
            path=filepath,
            uuid=direct_value(block, "uuid") or "",
            at=(float(at.group(1)), float(at.group(2))) if at else (0.0, 0.0),
            in_bom=direct_value(block, "in_bom") != "no",
            dnp=direct_value(block, "dnp") == "yes",
            block=block,
        ))
    return sheets


def find_sub_sheets(text: str, base_dir: Path) -> list[Path]:
    """Find hierarchical sub-sheet files referenced in a .kicad_sch."""
    return [entry.path for entry in find_sub_sheet_entries(text, base_dir)]


def symbol_instances_of(symbol_block: str, tilde_empty: bool = True) -> list[dict]:
    """The ``(instances (project P (path X ...)))`` entries of a placed symbol block, in file
    order (see kicad_core.instances.inline_instances)."""
    node = direct_child(symbol_block, "instances")
    if node is None:
        return []
    return inline_instances(["symbol", parse(node)], tilde_empty)


def resolved_instance(symbol_block: str, sheet_path: str, *, project_name: str = "",
                      candidates: list[dict] | None = None) -> dict | None:
    """The instance KiCad uses for the placed symbol on *sheet_path* (the full KIID path, root
    sheet uuid first): the instance with that exact path, else the first instance of
    *project_name*, else the first instance (kicad_core.instances.resolve_instance).
    *candidates* are instances known from elsewhere (a KiCad 6 root's symbol_instances),
    tried before the block's own.  None when the symbol has no instance at all."""
    return resolve_instance(list(candidates or ()) + symbol_instances_of(symbol_block),
                            sheet_path, project_name)


def instance_of(symbol_block: str, sheet_path: str, *, project_name: str = "",
                candidates: list[dict] | None = None) -> tuple[str, int | None] | None:
    """(reference, unit) of resolved_instance; None when the symbol has no instance at all."""
    hit = resolved_instance(symbol_block, sheet_path, project_name=project_name,
                            candidates=candidates)
    if hit is None:
        return None
    return hit["reference"], hit["unit"]


def sheet_variant(sheet_block: str, parent_path: str, variant: str | None,
                  file_version) -> dict:
    """What design variant *variant* changes on a ``(sheet ...)`` block placed on the sheet
    whose full KIID path is *parent_path* (kicad_core.instances.variant_overrides)."""
    if variant is None:
        return {}
    node = direct_child(sheet_block, "instances")
    if node is None:
        return {}
    return variant_overrides(instance_variants(["sheet", parse(node)], parent_path), variant,
                             file_version)


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
