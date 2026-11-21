"""Which instance data KiCad 10 uses for a placed symbol on one sheet path.

A placed symbol carries one instance (reference, unit) per sheet path it appears on.  KiCad
looks the sheet's full path up exactly (the root sheet uuid first, then the sheet uuids); with
no instance for that path it copies the first instance of the current project, else the first
instance (``SCH_SHEET_PATH::CheckForMissingSymbolInstances``).
"""
from __future__ import annotations

from kicad_core.fields import MANDATORY_STRIP
from kicad_core.sexp import find_first, get_value


def tilde_is_empty(file_version) -> bool:
    """True when a ``"~"`` field text means empty: files older than 20250318 (unreadable
    versions count as old)."""
    try:
        return int(file_version) < 20250318
    except (TypeError, ValueError):
        return True


def _norm_path(path: str) -> str:
    return path.rstrip("/").lower()


def resolve_instance(candidates: list[dict], instance_path: str,
                     project_name: str) -> dict | None:
    """Pick the instance KiCad uses on *instance_path*.

    *candidates* are dicts with ``path`` (full KIID path), ``project``, ``reference`` and
    ``unit``, in load order.  An exact path match wins, the last duplicate replacing earlier
    ones; otherwise the first candidate of *project_name*, else the first candidate; None when
    there are no candidates (the caller keeps the Reference field).
    """
    want = _norm_path(instance_path)
    hit = None
    for cand in candidates:
        if _norm_path(cand.get("path") or "") == want:
            hit = cand
    if hit is not None or not candidates:
        return hit
    for cand in candidates:
        if cand.get("project") == project_name:
            return cand
    return candidates[0]


def inline_instances(sym: list, tilde_empty: bool) -> list[dict]:
    """The ``(instances (project P (path X ...)))`` entries of a placed symbol, in file order.

    Each entry has ``project``, ``path``, ``reference`` and ``unit`` (None when absent), plus
    ``value`` / ``footprint`` when the path carries them.
    """
    out = []
    node = find_first(sym, "instances")
    if not node:
        return out
    for proj in node[1:]:
        if not isinstance(proj, list) or len(proj) < 2 or proj[0] != "project":
            continue
        for path_node in proj[2:]:
            if not isinstance(path_node, list) or not path_node or path_node[0] != "path":
                continue
            try:
                unit = int(get_value(path_node, "unit") or 0) or None
            except (TypeError, ValueError):
                unit = None
            entry = {"project": proj[1] if isinstance(proj[1], str) else "",
                     "path": path_node[1] if len(path_node) > 1 else "",
                     "reference": get_value(path_node, "reference") or "",
                     "unit": unit}
            for key in ("value", "footprint"):
                text = get_value(path_node, key)
                if text is not None:
                    entry[key] = ("" if (tilde_empty and text == "~") else text).strip(MANDATORY_STRIP)
            variants = variant_blocks(path_node)
            if variants:
                entry["variants"] = variants
            out.append(entry)
    return out


_VARIANT_FLAGS = ("dnp", "in_bom", "on_board", "exclude_from_sim")
# Before this file version KiCad stored a variant's in_bom with the inverted meaning.
_VARIANT_IN_BOM_FIXED = 20260306


def variant_blocks(path_node: list) -> dict:
    """The ``(variant (name N) ...)`` blocks of one instance path, by name (a later block of a
    name replaces an earlier one): each flag token as written ("yes" / "no") and ``fields``
    (name -> text, as written)."""
    out = {}
    for node in path_node:
        if not isinstance(node, list) or not node or node[0] != "variant":
            continue
        block = {"fields": {}}
        for child in node[1:]:
            if not isinstance(child, list) or len(child) < 2:
                continue
            if child[0] == "name":
                block["name"] = str(child[1])
            elif child[0] in _VARIANT_FLAGS:
                block[child[0]] = str(child[1])
            elif child[0] == "field":
                name = get_value(child, "name")
                if name is not None:
                    block["fields"][name] = get_value(child, "value") or ""
        out[block.pop("name", "")] = block
    return out


def variant_overrides(variants: dict | None, name: str | None, file_version) -> dict:
    """What design variant *name* changes on one symbol or sheet instance, as KiCad 10 reads it:
    each of dnp / in_bom / on_board / exclude_from_sim the variant sets (a bool), and
    ``fields`` (name -> text).  Empty when *name* is None or the instance has no such variant
    (the default variant: the symbol's own attributes and fields)."""
    block = (variants or {}).get(name) if name is not None else None
    if not block:
        return {}
    out = {flag: block[flag] == "yes" for flag in _VARIANT_FLAGS if flag in block}
    if "in_bom" in out:
        try:
            fixed = int(file_version) >= _VARIANT_IN_BOM_FIXED
        except (TypeError, ValueError):
            fixed = False
        if not fixed:
            out["in_bom"] = not out["in_bom"]
    if block["fields"]:
        out["fields"] = dict(block["fields"])
    return out


def instance_variants(node: list, path: str) -> dict | None:
    """The variant blocks of the instance of a sheet (or symbol) *node* whose path is exactly
    *path*; the last such instance wins.  None when there is none."""
    want = _norm_path(path)
    hit = None
    for entry in inline_instances(node, False):
        if _norm_path(entry["path"]) == want:
            hit = entry
    return hit.get("variants") if hit else None
