"""Schematic hierarchy: sheet traversal and the Altium top-level-sheets merge.

parse_all_sheets is a verbatim move from analyze_schematic.py; merge_top_level_sheets
is the top_level_sheets block of analyze_schematic() extracted (body unchanged modulo
de-indent); no behaviour change.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from kicad_core.diagnostics import record
from kicad_core.sexp import find_first, get_value, parse_file
from kicad_core.project import empty_input_error, load_kicad_pro
from schematic.reader import (
    extract_power_symbols,
    extract_symbol_instances,
    parse_single_sheet,
)


def parse_all_sheets(root_path: str, root_tree: list | None = None,
                     symbol_instances_override: dict | None = None, *,
                     diagnostics: list | None = None):
    """Parse a root schematic and all sub-sheets recursively.

    Performs Phase A of schematic analysis: recursive sheet traversal,
    component extraction with reference remapping, hierarchical label
    namespacing, and sheet coordinate isolation.

    Args:
        root_path: Path to the root .kicad_sch file.
        root_tree: Pre-parsed S-expression tree (avoids re-parsing if caller
            already has it). Parsed from root_path if None.
        symbol_instances_override: If provided, use these symbol_instances
            instead of extracting from root_tree. Required when parsing a
            sub-sheet that lacks (symbol_instances) — pass the root's
            symbol_instances collected during the peer-sheet traversal.
        diagnostics: list sink for skipped sheets (a sheet that includes one of
            its own ancestors, or an empty sub-sheet file).

    Returns:
        dict with keys:
            components, wires, labels, junctions, no_connects, lib_symbols,
            text_annotations, bus_elements, title_block, sheets_parsed,
            power_symbols, root_symbol_instances, generator_version,
            file_version
    """
    if root_tree is None:
        root_tree = parse_file(root_path)

    if symbol_instances_override is not None:
        root_symbol_instances = symbol_instances_override
    else:
        root_symbol_instances = extract_symbol_instances(root_tree)

    generator_version = get_value(root_tree, "generator_version") or "unknown"
    file_version = get_value(root_tree, "version") or "unknown"

    all_components = []
    all_wires = []
    all_labels = []
    all_junctions = []
    all_no_connects = []
    all_lib_symbols = {}
    all_text_annotations = []
    all_bus_elements = []
    root_title_block = {}
    sheets_parsed = []

    # Each queue entry carries the chain of sheet files above it: a sheet that
    # names one of its own ancestors would otherwise expand forever.
    to_parse = [(str(Path(root_path).resolve()), "", ())]
    parsed = set()
    skipped = set()

    while to_parse:
        sheet_path, inst_path, ancestors = to_parse.pop(0)
        parse_key = (sheet_path, inst_path)
        if parse_key in parsed:
            continue
        parsed.add(parse_key)
        if ancestors and empty_input_error(sheet_path, 'kicad_sch'):
            if sheet_path not in skipped:
                skipped.add(sheet_path)
                record(diagnostics, "schematic.hierarchy.parse_all_sheets",
                       ValueError(f"sheet file {os.path.basename(sheet_path)} is empty"),
                       "empty sheet skipped")
            continue

        sd = parse_single_sheet(sheet_path, instance_uuid=inst_path,
                                symbol_instances=root_symbol_instances)
        (root, components, wires, labels, junctions, no_connects,
         sub_sheets, lib_symbols, text_annotations, bus_elements, title_block) = (
            sd.root, sd.components, sd.wires, sd.labels, sd.junctions, sd.no_connects,
            sd.sub_sheet_paths, sd.lib_symbols, sd.text_annotations, sd.bus_elements, sd.title_block)

        sheet_idx = len(sheets_parsed)
        for c in components:
            c["_sheet"] = sheet_idx
        for w in wires:
            w["_sheet"] = sheet_idx
        for l in labels:
            l["_sheet"] = sheet_idx
        for j in junctions:
            j["_sheet"] = sheet_idx
        for nc in no_connects:
            nc["_sheet"] = sheet_idx
        for be in bus_elements.get("bus_wires", []):
            be["_sheet"] = sheet_idx
        for be in bus_elements.get("bus_entries", []):
            be["_sheet"] = sheet_idx

        # Namespace hierarchical labels, but retain the bare identity and
        # namespace on internal fields so the bus pass (GH #25) can pair
        # parent sheet-pin ports with child hier-label ports positionally.
        # Name-mangling must reproduce the pre-#25 values exactly.
        for lbl in labels:
            if lbl["type"] == "hierarchical_label":
                suuid = lbl.pop("_sheet_uuid", None)
                lbl["_bare_name"] = lbl["name"]
                if suuid:
                    lbl["_is_sheet_pin"] = True
                    lbl["_hier_ns"] = ((inst_path + "/" + suuid)
                                       if inst_path else ("/" + suuid))
                    lbl["name"] = lbl["_hier_ns"] + "/" + lbl["name"]
                else:
                    lbl["_hier_ns"] = inst_path
                    if inst_path:
                        lbl["name"] = inst_path + "/" + lbl["name"]

        all_components.extend(components)
        all_wires.extend(wires)
        all_labels.extend(labels)
        all_junctions.extend(junctions)
        all_no_connects.extend(no_connects)
        all_lib_symbols.update(lib_symbols)
        all_text_annotations.extend(text_annotations)
        all_bus_elements.append(bus_elements)
        if sheet_idx == 0:
            root_title_block = title_block
        sheets_parsed.append(sheet_path)

        chain = ancestors + (sheet_path,)
        for sub_path, sub_uuid in sub_sheets:
            sub_resolved = str(Path(sub_path).resolve())
            if sub_resolved in chain:
                if sub_resolved not in skipped:
                    skipped.add(sub_resolved)
                    record(diagnostics, "schematic.hierarchy.parse_all_sheets",
                           ValueError(f"sheet file {os.path.basename(sheet_path)} includes its own "
                                      f"ancestor {os.path.basename(sub_resolved)}"),
                           "recursive sheet skipped")
                continue
            child_path = inst_path + "/" + sub_uuid if sub_uuid else inst_path
            if (sub_resolved, child_path) not in parsed:
                to_parse.append((sub_resolved, child_path, chain))

    merged_bus = {"bus_wires": [], "bus_entries": [], "bus_aliases": []}
    for be in all_bus_elements:
        merged_bus["bus_wires"].extend(be.get("bus_wires", []))
        merged_bus["bus_entries"].extend(be.get("bus_entries", []))
        merged_bus["bus_aliases"].extend(be.get("bus_aliases", []))

    power_symbols = extract_power_symbols(all_components)

    return {
        "components": all_components,
        "wires": all_wires,
        "labels": all_labels,
        "junctions": all_junctions,
        "no_connects": all_no_connects,
        "lib_symbols": all_lib_symbols,
        "text_annotations": all_text_annotations,
        "bus_elements": merged_bus,
        "title_block": root_title_block,
        "sheets_parsed": sheets_parsed,
        "power_symbols": power_symbols,
        "root_symbol_instances": root_symbol_instances,
        "generator_version": generator_version,
        "file_version": file_version,
    }


def merge_top_level_sheets(parsed: dict, path: str, root_tree: list, *,
                           diagnostics: list | None = None) -> None:
    """Altium flat multi-page imports: fold .kicad_pro top_level_sheets peers (and their
    sub-sheets) into *parsed* in place. Inert when the root has (sheet ...) nodes or the
    project lists at most one top-level sheet. Moved verbatim from analyze_schematic()."""
    # --- top_level_sheets support (Altium flat multi-page imports) ---
    # KiCad's Altium importer registers all pages as top_level_sheets in
    # .kicad_pro instead of creating (sheet ...) hierarchy references.
    # Trigger only when the root has zero (sheet ...) nodes — checking
    # len(sheets_parsed) alone is fragile because parse_all_sheets silently
    # drops (sheet ...) refs whose files are missing, which would otherwise
    # cause us to mix in unrelated top_level_sheets. Runs regardless of
    # no_hierarchy so the sub-sheet redirect path still picks up peers.
    if (len(parsed.get("sheets_parsed", [])) <= 1
            and find_first(root_tree, "sheet") is None):
        pro = load_kicad_pro(path)
        if pro:
            tls = pro.get("schematic", {}).get("top_level_sheets", [])
            if len(tls) > 1:
                root_abs = str(Path(path).resolve())
                extra_sheets = []
                seen = {root_abs}
                for entry in tls:
                    fn = entry.get("filename", "")
                    if not fn:
                        continue
                    sheet_path = os.path.join(os.path.dirname(path), fn)
                    if not os.path.isfile(sheet_path):
                        continue
                    abs_path = str(Path(sheet_path).resolve())
                    if abs_path in seen:
                        continue
                    seen.add(abs_path)
                    extra_sheets.append(abs_path)

                if extra_sheets:
                    print(f"Note: discovered {len(extra_sheets)} additional "
                          f"top-level sheets from .kicad_pro",
                          file=sys.stderr)
                    sym_inst = parsed.get("root_symbol_instances", {})
                    base_idx = len(parsed["sheets_parsed"])
                    # Queue-based walk so peers with their own inner
                    # (sheet ...) references — the "hybrid" Altium-flat
                    # shape, flat top + sub-hierarchy beneath one or more
                    # peers — get their child sheets merged in too. Pure
                    # Altium-flat imports (no inner refs) walk this loop
                    # exactly once per peer with no recursion. PR #19
                    # follow-up #14 (Copilot review 3221428004).
                    to_parse = list(extra_sheets)
                    while to_parse:
                        sheet_path = to_parse.pop(0)
                        try:
                            sd = parse_single_sheet(
                                sheet_path,
                                symbol_instances=sym_inst)
                            (_, comps, wires, labels, junctions,
                             no_connects, sub_sheet_paths, lib_syms,
                             text_annot, bus_elems, title_blk) = (
                                sd.root, sd.components, sd.wires, sd.labels, sd.junctions,
                                sd.no_connects, sd.sub_sheet_paths, sd.lib_symbols,
                                sd.text_annotations, sd.bus_elements, sd.title_block)
                        except Exception as exc:
                            record(diagnostics, "schematic.hierarchy.merge_top_level_sheets", exc,
                                   f"sheet {os.path.basename(sheet_path)} skipped (parse failed)")
                            continue
                        sheet_idx = base_idx
                        base_idx += 1
                        for c in comps:
                            c["_sheet"] = sheet_idx
                        for w in wires:
                            w["_sheet"] = sheet_idx
                        for lb in labels:
                            lb["_sheet"] = sheet_idx
                        for j in junctions:
                            j["_sheet"] = sheet_idx
                        for nc in no_connects:
                            nc["_sheet"] = sheet_idx
                        # KH-409: untagged peer bus_wires/bus_entries made
                        # build_net_map's wires_by_sheet/entries_by_sheet
                        # (~line 1457) file every peer's bus geometry under
                        # sheet 0 with the root's -- one shared BusGraph
                        # instead of one per sheet, bogusly flagging a valid
                        # peer tap "unlabeled_entry_tap".
                        for be in bus_elems.get("bus_wires", []):
                            be["_sheet"] = sheet_idx
                        for be in bus_elems.get("bus_entries", []):
                            be["_sheet"] = sheet_idx
                        parsed["components"].extend(comps)
                        parsed["wires"].extend(wires)
                        parsed["labels"].extend(labels)
                        parsed["junctions"].extend(junctions)
                        parsed["no_connects"].extend(no_connects)
                        parsed["lib_symbols"].update(lib_syms)
                        parsed["text_annotations"].extend(text_annot)
                        for bk, bv in bus_elems.items():
                            if isinstance(bv, list):
                                parsed["bus_elements"].setdefault(bk, []).extend(bv)
                            elif isinstance(bv, dict):
                                parsed["bus_elements"].setdefault(bk, {}).update(bv)
                        parsed["sheets_parsed"].append(sheet_path)
                        # Enqueue any sub-sheet references from THIS peer
                        # for the hybrid case. `seen` is the cycle guard:
                        # it already has root + every peer; we add each
                        # sub-sheet on first sighting.
                        for sub_path, _sheet_uuid in sub_sheet_paths:
                            abs_sub = str(Path(sub_path).resolve())
                            if abs_sub not in seen:
                                seen.add(abs_sub)
                                to_parse.append(abs_sub)
                    # Power symbols were extracted from root-sheet components
                    # only; refresh from the merged list so peer-sheet ones are
                    # included.
                    parsed["power_symbols"] = extract_power_symbols(
                        parsed["components"])
