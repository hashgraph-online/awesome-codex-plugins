"""Schematic hierarchy: sheet traversal and the merge of a KiCad 10 project's other
top-level sheets.

parse_all_sheets walks one top-level sheet's hierarchy; merge_top_level_sheets folds in the
other declared top-level sheets of a multi-root project, each walked by parse_all_sheets.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from kicad_core.diagnostics import record
from kicad_core.sexp import find_all, get_at, get_value, net_name_escape, parse_file
from kicad_core.project import (declared_top_level_sheets, empty_input_error, expand_sheet_file,
                                 find_project_settings_file, load_kicad_pro)
from schematic.reader import (
    TextVarRegistry,
    extract_components,
    extract_power_symbols,
    extract_symbol_instances,
    parse_single_sheet,
    rename_legacy_power_symbols,
    sheet_property,
    sheet_chain_node,
    text_context,
)

# KiCad renames legacy power symbols on load when the root file predates this version.
_POWER_RENAME_BEFORE = 20230221
# KiCad applies the root's (symbol_instances) only when the root file predates this version.
_SYMBOL_INSTANCES_BEFORE = 20221002


def _renames_legacy_power_symbols(file_version) -> bool:
    """True when the root schematic's version is older than 20230221."""
    try:
        return int(file_version) < _POWER_RENAME_BEFORE
    except (TypeError, ValueError):
        return False


def _applies_symbol_instances(file_version) -> bool:
    """True when the root schematic's version is older than 20221002 (unreadable: True)."""
    try:
        return int(file_version) < _SYMBOL_INSTANCES_BEFORE
    except (TypeError, ValueError):
        return True


def _sheet_list(root_path: str, root_tree: list) -> dict:
    """Sheet path (below the root, lowercase) -> (index, sheet file) in KiCad's sheet list as
    built when KiCad 6 instance data is applied: depth first, child sheets sorted by position,
    then uuid (SCH_SHEET_LIST::BuildSheetList, SCH_SCREEN::GetSheets); page numbers are not
    set yet."""
    order: dict = {}
    trees = {}

    def walk(tree, file_path, path, ancestors):
        order.setdefault(path.lower(), (len(order), file_path))
        kids = []
        for sheet in find_all(tree, "sheet"):
            fname = sheet_property(sheet, "SHEETFILE")
            at = get_at(sheet) or (0, 0, 0)
            kids.append((at[0], at[1], (get_value(sheet, "uuid") or "").lower(), fname))
        for _x, _y, suuid, fname in sorted(kids, key=lambda k: k[:3]):
            if not fname:
                continue
            sub = str((Path(file_path).parent / expand_sheet_file(fname, file_path)).resolve())
            if sub in ancestors or not os.path.isfile(sub):
                continue
            if sub not in trees:
                try:
                    trees[sub] = parse_file(sub)
                except Exception:
                    continue
            walk(trees[sub], sub, path + "/" + suuid, ancestors | {sub})

    root_abs = str(Path(root_path).resolve())
    walk(root_tree, root_abs, "", {root_abs})
    return order


def _settle_kicad6_values(symbol_instances: dict, root_path: str, root_tree: list) -> dict:
    """KiCad 6 entries as KiCad applies them.  Each entry's non-empty value / footprint
    overwrites the field of the one symbol it names, sheet by sheet in sheet-list order, so a
    symbol on a repeated sheet shows the last sheet's value on every sheet: entries are put in
    that order and each takes the last non-empty value / footprint of its (sheet file, uuid)
    group."""
    sheets = _sheet_list(root_path, root_tree)
    last = (len(sheets), None)
    ordered = sorted(symbol_instances.items(),
                     key=lambda kv: sheets.get(kv[0].rpartition("/")[0].lower(), last)[0])
    winners: dict = {}
    for si_path, entry in ordered:
        sheet_path, _, sym_uuid = si_path.rpartition("/")
        win = winners.setdefault((sheets.get(sheet_path.lower(), last)[1], sym_uuid.lower()),
                                 {"value": "", "footprint": ""})
        for key in ("value", "footprint"):
            if entry.get(key):
                win[key] = entry[key]
    settled = {}
    for si_path, entry in ordered:
        sheet_path, _, sym_uuid = si_path.rpartition("/")
        settled[si_path] = dict(entry, **winners[(sheets.get(sheet_path.lower(), last)[1],
                                                  sym_uuid.lower())])
    return settled


def _top_sheet_node(sheet_path: str, uuid: str, pro: dict | None, default_name: str) -> dict:
    """A top-level sheet of the text-variable chain: named by its .kicad_pro top_level_sheets
    entry, else *default_name* (as kicad-cli names a lone root: the project name, or "Root"
    when there is no .kicad_pro)."""
    name = default_name
    tls = ((pro or {}).get("schematic") or {}).get("top_level_sheets") or []
    for entry in tls if isinstance(tls, list) else ():
        fn = entry.get("filename") if isinstance(entry, dict) else None
        if fn and entry.get("name") and str(
                (Path(sheet_path).parent / fn).resolve()) == str(Path(sheet_path).resolve()):
            name = entry["name"]
            break
    return sheet_chain_node(uuid, {"fields": [("SHEETNAME", name),
                                              ("SHEETFILE", os.path.basename(sheet_path))],
                                   "in_bom": True, "on_board": True, "dnp": False,
                                   "exclude_from_sim": False})


def apply_sheet_flags(components: list[dict], sheet_chain: list[dict]) -> None:
    """Sheet attributes reach every symbol below the sheet, in place: a symbol is out of the
    BOM, DNP or off the board when it or any sheet on its path says so (KiCad 9+
    SCH_SHEET_PATH flags OR over the path; a nested sheet cannot re-include)."""
    ex_bom = any(not node["in_bom"] for node in sheet_chain)
    dnp = any(node["dnp"] for node in sheet_chain)
    ex_board = any(not node["on_board"] for node in sheet_chain)
    for c in components:
        if ex_bom:
            c["in_bom"] = False
        if dnp:
            c["dnp"] = True
        if ex_board:
            c["on_board"] = False


def set_instance_paths(components: list[dict], inst_path: str) -> None:
    """Give each placed unit the path a board footprint carries for it, in place: the sheet
    uuids below the root, then the symbol uuid (KiCad's SCH_SHEET_PATH::PathAsString)."""
    for c in components:
        if c.get("uuid"):
            c["instance_path"] = inst_path + "/" + c["uuid"]


def namespace_hierarchical_labels(labels: list[dict], inst_path: str) -> None:
    """Prefix each hierarchical label and sheet pin with its sheet instance path, in place.

    A child's hierarchical label becomes ``<inst_path>/NAME``; a sheet pin (a label
    carrying ``_sheet_uuid``) becomes ``<inst_path>/<sheet_uuid>/NAME``, the name the
    child instance gives its label, so the two meet by name.  A sheet pin whose sheet
    has no uuid keeps the parent's namespace but is still a sheet pin.  The bare name
    and the namespace stay on internal fields so the bus pass (GH #25) can pair parent
    sheet-pin ports with child hier-label ports positionally.
    """
    for lbl in labels:
        if lbl["type"] == "hierarchical_label":
            lbl["_bare_name"] = lbl["name"]
            if "_sheet_uuid" in lbl:
                suuid = lbl.pop("_sheet_uuid")
                lbl["_is_sheet_pin"] = True
                if suuid:
                    lbl["_hier_ns"] = ((inst_path + "/" + suuid)
                                       if inst_path else ("/" + suuid))
                else:
                    lbl["_hier_ns"] = inst_path
                if lbl["_hier_ns"]:
                    lbl["name"] = lbl["_hier_ns"] + "/" + lbl["name"]
            else:
                lbl["_hier_ns"] = inst_path
                if inst_path:
                    lbl["name"] = inst_path + "/" + lbl["name"]


def parse_all_sheets(root_path: str, root_tree: list | None = None,
                     symbol_instances_override: dict | None = None, *,
                     diagnostics: list | None = None, project_path: str | None = None,
                     variant: str | None = None):
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
        project_path: the schematic whose project this sheet belongs to (names the
            project and finds its .kicad_pro); defaults to root_path.  Set when
            root_path is another top-level sheet of that project.
        variant: a KiCad 10 design variant name (see extract_components); None is the
            default variant.

    Returns:
        dict with keys:
            components, wires, labels, junctions, no_connects, lib_symbols,
            text_annotations, bus_elements, title_block, sheets_parsed,
            sheet_paths (each sheet's human path, "/" for the root),
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
    if not _applies_symbol_instances(file_version):
        root_symbol_instances = {}
    elif root_symbol_instances:
        root_symbol_instances = _settle_kicad6_values(root_symbol_instances, root_path,
                                                      root_tree)
    project_path = project_path or root_path
    project_name = Path(project_path).stem
    pro = load_kicad_pro(project_path)
    # Instance paths start with the root sheet's uuid: the file's (uuid), or the uuid a
    # multi-root project declares for this top-level sheet unless that is nil.
    root_uuid = get_value(root_tree, "uuid") or ""
    me = str(Path(root_path).resolve())
    for top in multi_root_sheets(project_path, pro):
        if top["uuid"] and str(Path(top["path"]).resolve()) == me:
            root_uuid = top["uuid"]
    root_kiid = "/" + root_uuid if root_uuid else ""
    # Without a .kicad_pro KiCad has no project: ${PROJECTNAME} is empty and the root sheet is
    # "Root". Instance selection still prefers the file stem.
    has_pro = Path(project_path).with_suffix(".kicad_pro").exists()
    registry = TextVarRegistry()
    text_shared = text_context(pro, project_name if has_pro else "",
                               os.path.basename(root_path), registry)
    pending = []

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
    sheet_paths = []

    # Each queue entry carries the chain of sheet files above it: a sheet that
    # names one of its own ancestors would otherwise expand forever.
    to_parse = [(str(Path(root_path).resolve()), "", (),
                 (_top_sheet_node(root_path, root_uuid, pro,
                                  project_name if has_pro else "Root"),))]
    parsed = set()
    skipped = set()

    while to_parse:
        sheet_path, inst_path, ancestors, text_chain = to_parse.pop(0)
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

        text_ctx = dict(text_shared, sheet_chain=list(text_chain))
        pending_before = registry.pending
        sheet_kwargs = dict(instance_uuid=inst_path, symbol_instances=root_symbol_instances,
                            instance_path=root_kiid + inst_path, root_kiid=root_kiid,
                            project_name=project_name, text_ctx=text_ctx, variant=variant)
        sd = parse_single_sheet(sheet_path, **sheet_kwargs)
        (root, components, wires, labels, junctions, no_connects,
         sub_sheets, lib_symbols, text_annotations, bus_elements, title_block) = (
            sd.root, sd.components, sd.wires, sd.labels, sd.junctions, sd.no_connects,
            sd.sub_sheet_paths, sd.lib_symbols, sd.text_annotations, sd.bus_elements, sd.title_block)
        apply_sheet_flags(components, text_chain)
        set_instance_paths(components, inst_path)

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

        namespace_hierarchical_labels(labels, inst_path)

        if registry.pending != pending_before:
            pending.append((sheet_idx, len(all_components), sd.root, lib_symbols, sheet_kwargs))
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
        # KiCad's human sheet path ("/", "/Power/"): the sheet names below the root,
        # each escaped as a net name (B/C is B{slash}C), between plain separators
        sheet_paths.append("/" + "".join(net_name_escape(node["name"]) + "/"
                                         for node in reversed(text_chain[:-1])))

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
                child_chain = (sheet_chain_node(sub_uuid, sd.sheet_fields.get(sub_uuid)),) + text_chain
                registry.add_sheet(sub_uuid, dict(text_shared, sheet_chain=list(child_chain)))
                to_parse.append((sub_resolved, child_path, chain, child_chain))

    # ${REF:FIELD} needs every symbol: sheets that met one are read again now
    registry.ready = True
    for sheet_idx, start, root, lib_symbols, sheet_kwargs in pending:
        components = extract_components(root, lib_symbols, **sheet_kwargs)
        apply_sheet_flags(components, sheet_kwargs["text_ctx"]["sheet_chain"])
        set_instance_paths(components, sheet_kwargs["instance_uuid"])
        for c in components:
            c["_sheet"] = sheet_idx
        all_components[start:start + len(components)] = components

    merged_bus = {"bus_wires": [], "bus_entries": [], "bus_aliases": []}
    for be in all_bus_elements:
        merged_bus["bus_wires"].extend(be.get("bus_wires", []))
        merged_bus["bus_entries"].extend(be.get("bus_entries", []))
        merged_bus["bus_aliases"].extend(be.get("bus_aliases", []))

    if _renames_legacy_power_symbols(file_version):
        rename_legacy_power_symbols(all_components)
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
        "sheet_paths": sheet_paths,
        "power_symbols": power_symbols,
        "root_symbol_instances": root_symbol_instances,
        "generator_version": generator_version,
        "file_version": file_version,
    }


def multi_root_sheets(path: str, pro: dict | None) -> list[dict]:
    """The top-level sheets KiCad 10 loads with *path* (kicad_core.project
    declared_top_level_sheets): every declared one when the project declares more than one
    and *path* is among them, else []."""
    sch = pro.get("schematic") if isinstance(pro, dict) else None
    tls = sch.get("top_level_sheets") if isinstance(sch, dict) else None
    if not isinstance(tls, list) or len(tls) < 2:
        return []
    declared = declared_top_level_sheets(find_project_settings_file(path, ".kicad_pro"), pro)
    me = str(Path(path).resolve())
    if len(declared) < 2 or all(str(Path(d["path"]).resolve()) != me for d in declared):
        return []
    return declared


def merge_top_level_sheets(parsed: dict, path: str, *,
                           diagnostics: list | None = None, variant: str | None = None) -> None:
    """Fold the other top-level sheets of a KiCad 10 multi-root project (each with its
    sub-sheets, see parse_all_sheets) into *parsed*, the analysis of the declared sheet
    *path*, in place.  A peer that fails to parse is skipped with one diagnostic."""
    me = str(Path(path).resolve())
    peers = [d["path"] for d in multi_root_sheets(path, load_kicad_pro(path))
             if str(Path(d["path"]).resolve()) != me]
    if not peers:
        return
    print(f"Note: discovered {len(peers)} additional top-level sheets from .kicad_pro",
          file=sys.stderr)
    for peer in peers:
        try:
            sub = parse_all_sheets(peer, project_path=path, diagnostics=diagnostics,
                                   variant=variant)
        except Exception as exc:
            record(diagnostics, "schematic.hierarchy.merge_top_level_sheets", exc,
                   f"sheet {os.path.basename(peer)} skipped (parse failed)")
            continue
        offset = len(parsed["sheets_parsed"])
        bus = sub["bus_elements"]
        for items in (sub["components"], sub["wires"], sub["labels"], sub["junctions"],
                      sub["no_connects"], bus["bus_wires"], bus["bus_entries"]):
            for item in items:
                item["_sheet"] = item.get("_sheet", 0) + offset
        for key in ("components", "wires", "labels", "junctions", "no_connects",
                    "text_annotations", "sheets_parsed", "sheet_paths"):
            parsed[key].extend(sub[key])
        for key, items in bus.items():
            parsed["bus_elements"].setdefault(key, []).extend(items)
        parsed["lib_symbols"].update(sub["lib_symbols"])
    parsed["power_symbols"] = extract_power_symbols(parsed["components"])
