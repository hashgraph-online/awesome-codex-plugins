"""PCB analysis pipeline: the analysis phases as named functions with their
prerequisites passed explicitly.

Phase 1 read_board        — parse + extract (pcb.reader) + the KiCad-10 synthetic net map applied
                            through a per-call PcbReaderState (nothing module-level)
Phase 2 run_facts         — the board facts (connectivity … return path, incl. the
                            .kicad_pro/.kicad_dru/lib-table loads, keepout zones)
Phase 3 run_checks        — every check over the board + facts;
                            run_analyses composes 2 + 3
Phase 4 assemble_result   — pcb.presentation: the result dict in the stable output key order
Phase 5 finalize_for_cli  — command-specific annotation (GP-001 debug file, project summary, design
                            intent, stage/audience filters, finding_id)
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from kicad_core.sexp import get_value, parse_file
from kicad_core.project import (load_kicad_pro, extract_pro_net_classes,
                                extract_pro_design_rules, extract_pro_text_variables,
                                load_kicad_dru_checked, load_lib_tables,
                                find_project_settings_file, ignored_drc_checks)
from kicad_core.diagnostics import record
from kicad_core.model import PcbReaderState
from pcb import reader
from pcb.geometry import ZoneFills, outline_loops
from pcb.reader import (
    _extract_keepout_zones,
    extract_silkscreen,
    extract_board_metadata,
    extract_dimensions,
    extract_groups,
    extract_net_classes,
)
from pcb.routing import (
    analyze_connectivity,
    board_pin_signals,
    analyze_power_nets,
    analyze_pad_to_pad_distances,
    analyze_return_path_continuity,
    _build_reference_layer_map,
    _copper_order_from_stackup,
    analyze_net_lengths,
    analyze_ground_domains,
    analyze_current_capacity,
    analyze_layer_transitions,
)
from pcb.copper import (
    analyze_thermal_vias,
    analyze_vias,
    analyze_thermal_pad_vias,
    analyze_copper_presence,
    analyze_via_in_pad,
    analyze_board_edge_via_clearance,
)
from pcb.dfm import (analyze_dfm, effective_board_minima, has_legacy_design_settings,
                     microvia_class_minima)
from pcb.assembly import (
    analyze_decoupling_placement,
    analyze_placement,
    analyze_tombstoning_risk,
    analyze_fiducials,
    analyze_test_point_coverage,
    analyze_orientation_consistency,
    analyze_silkscreen_pad_overlaps,
    analyze_keepout_violations,
)
from pcb.presentation import assemble_result, group_components, compute_statistics
from finding_schema import assign_finding_ids


ANALYZER_SOURCE = "pcb"

MAX_TESTED_FORMAT_VERSION = 20260206  # bump when a newer corpus era is adopted


def _power_rails_from_schematic(schematic_data: dict | None) -> set[str]:
    """Extract power rail net names from a schematic analysis JSON.

    Reads `statistics.power_rails` — the shape analyze_schematic.py actually
    emits (list of {name, voltage} dicts) — not a top-level key.
    """
    stats = (schematic_data or {}).get("statistics") or {}
    return {r["name"] for r in stats.get("power_rails", [])
            if isinstance(r, dict) and r.get("name")}


def resolve_power_rails(power_rails: set[str] | None,
                        schematic_data: dict | None) -> tuple[set[str] | None, str]:
    """Return ``(resolved, source)`` with source in ``"cli" | "schematic" | "heuristic"``."""
    # Resolve which power-rail override (if any) net classification
    # should use — explicit power_rails > rails auto-read from schematic
    # analysis > name heuristics alone.
    if power_rails:
        _resolved_power_rails, _power_rails_source = power_rails, "cli"
    else:
        _sch_rails = _power_rails_from_schematic(schematic_data)
        if _sch_rails:
            _resolved_power_rails, _power_rails_source = _sch_rails, "schematic"
        else:
            _resolved_power_rails, _power_rails_source = None, "heuristic"
    return _resolved_power_rails, _power_rails_source


_INNER_CU = re.compile(r"In(\d+)\.Cu")


def _infer_stackup(copper_layers: list[str], board_thickness_mm: float | None,
                   mask_layers: int = 2) -> list[dict]:
    """The stackup KiCad builds for a board whose file has none
    (BOARD_STACKUP::BuildDefaultStackupList, board_stackup.cpp:678-770): copper 0.035 mm,
    each dielectric (thickness - 0.035 per copper - 0.01 per mask layer) / (copper - 1) in
    whole nm, FR4 epsilon_r 4.5, core and prepreg alternating from the top."""
    inner = sorted((int(m.group(1)), n) for n in copper_layers
                   if (m := _INNER_CU.fullmatch(n)))
    order = (["F.Cu"] if "F.Cu" in copper_layers else []) + [n for _, n in inner] \
        + (["B.Cu"] if "B.Cu" in copper_layers else [])
    if not order:
        order = ["F.Cu", "B.Cu"]
    thickness_nm = round((board_thickness_mm if board_thickness_mm is not None else 1.6) * 1e6)
    diel_nm = int((thickness_nm - 35000 * len(order) - 10000 * mask_layers)
                  / max(1, len(order) - 1))
    stackup = []
    for i, name in enumerate(order):
        stackup.append({"name": name, "type": "copper", "thickness": 0.035})
        if name == "B.Cu":
            break
        stackup.append({"name": f"dielectric {i + 1}", "type": "core" if i % 2 == 0 else "prepreg",
                        "thickness": diel_nm / 1e6, "epsilon_r": 4.5, "material": "FR4"})
    return stackup


def _board_stackup(layers: list[dict], setup: dict) -> list[dict]:
    """The file's stackup, else the one KiCad infers from the copper and mask layers."""
    if setup.get("stackup"):
        return setup["stackup"]
    names = [l.get("name") for l in layers]
    return _infer_stackup(names, setup.get("board_thickness_mm"),
                          mask_layers=sum(1 for n in names if n in ("F.Mask", "B.Mask")))


@dataclass
class BoardData:
    """Phase-1 output: the parsed board and everything the extractors pulled from it."""
    path: str
    root: list
    layers: list[dict]
    setup: dict
    net_names: dict[int, str]
    footprints: list[dict]
    tracks: dict
    vias: dict
    zones: list[dict]
    zone_fills: ZoneFills
    outline: dict
    state: PcbReaderState
    diagnostics: list = field(default_factory=list)
    graphics: list = field(default_factory=list)


def read_board(path: str, *, state: PcbReaderState | None = None) -> BoardData:
    """Phase 1: parse + extract + the KiCad-10 synthetic net map (via *state*)."""
    state = state if state is not None else PcbReaderState()

    root = parse_file(path)
    reader.canonicalize_copper_layers(root)

    # module attribute on purpose: the harness patches pcb.reader.<name> (ARCHITECTURE.md facade register)
    layers = reader.extract_layers(root)
    setup = reader.extract_setup(root)
    if not setup.get("stackup"):
        setup["stackup_source"] = "inferred"
    net_names = reader.extract_nets(root)
    diagnostics: list = []
    footprints = reader.extract_footprints(root, diagnostics)
    tracks = reader.extract_tracks(root)
    vias = reader.extract_vias(root)
    zones, zone_fills = reader.extract_zones(root)
    outline = reader.extract_board_outline(root)
    if outline.get("edges") and outline_loops(outline["edges"]) is None:
        record(diagnostics, "pcb.pipeline.read_board",
               ValueError("board outline (Edge.Cuts) does not close or is drawn twice"),
               "edge clearance measured to the outline's bounding box")
    graphics = reader.extract_copper_graphics(root)

    # KiCad 10: no net declarations — build synthetic mapping from content
    if not net_names:
        net_names = reader._build_net_mapping(footprints, tracks, vias, zones, state, graphics)
        # Backfill net IDs now that the mapping is built
        for seg in tracks.get("segments", []):
            if "_net_name" in seg:
                seg["net"] = state.net_id(seg.pop("_net_name"))
        for arc in tracks.get("arcs", []):
            if "_net_name" in arc:
                arc["net"] = state.net_id(arc.pop("_net_name"))
        for v in vias.get("vias", []):
            if "_net_name" in v:
                v["net"] = state.net_id(v.pop("_net_name"))
        for z in zones:
            z["net"] = state.net_id(z.get("net_name", ""))
        for g in graphics:
            if "_net_name" in g:
                g["net"] = state.net_id(g.pop("_net_name"))
        for fp in footprints:
            for pad in fp.get("pads", []):
                if pad.get("net_name") and pad.get("net_number", 0) == 0:
                    pad["net_number"] = state.net_id(pad["net_name"])

    return BoardData(path=path, root=root, layers=layers, setup=setup, net_names=net_names,
                     footprints=footprints, tracks=tracks, vias=vias, zones=zones,
                     zone_fills=zone_fills, outline=outline, state=state,
                     diagnostics=diagnostics, graphics=graphics)


@dataclass
class PcbFacts:
    """Phase-2 output: the measured board facts, in call order."""
    connectivity: Any
    stats: Any
    version: Any
    generator_version: Any
    format_newer_note: Any
    component_groups: Any
    net_lengths: Any
    power_routing: Any
    pad_distances: Any
    ground_domains: Any
    current_capacity: Any
    layer_transitions: Any
    silkscreen: Any
    metadata: Any
    dimensions: Any
    groups: Any
    net_classes: Any
    project_settings: Any
    board_minima: Any
    microvia_minima: Any
    ref_layer_map: Any
    return_path: Any
    gp001_samples: Any
    keepout_zones: Any
    reference_changes: Any = None
    power_rails: Any = None
    pin_signals: Any = frozenset()


@dataclass
class PcbChecks:
    """Phase-3 output: the checks over the board and its facts, in call order."""
    decoupling: Any
    via_analysis: Any
    thermal: Any
    placement: Any
    dfm: Any
    tombstoning: Any
    thermal_pad_vias: Any
    copper_presence: Any
    fiducial_check: Any
    test_point_coverage: Any
    orientation: Any
    silkscreen_overlaps: Any
    keepout_violations: Any
    via_in_pad: Any
    edge_via: Any


@dataclass
class PcbAnalyses:
    """Phases 2–3 output: every intermediate analyze_pcb() computed between the board and
    the result dict."""
    facts: PcbFacts
    checks: PcbChecks


def run_facts(board: BoardData, *, include_trace_segments: bool, return_path_radius_mm: float,
              gp001_debug: bool, resolved_power_rails: set[str] | None) -> PcbFacts:
    """Phase 2: the board facts in call order (incl. the .kicad_pro/.kicad_dru/
    lib-table loads). Passes the board's containers by reference; no analysis mutates them
    (tools/tests/test_pcb_phase_purity.py)."""
    path = board.path
    root = board.root
    layers = board.layers
    setup = board.setup
    net_names = board.net_names
    footprints = board.footprints
    tracks = board.tracks
    vias = board.vias
    zones = board.zones
    zone_fills = board.zone_fills
    outline = board.outline
    _resolved_power_rails = resolved_power_rails
    pin_signals = board_pin_signals(footprints, _resolved_power_rails)

    # Connectivity analysis (zone-aware)
    connectivity = analyze_connectivity(footprints, tracks, vias, net_names, zones,
                                        graphics=board.graphics)

    stats = compute_statistics(footprints, tracks, vias, zones, outline, connectivity, net_names, layers=layers)

    version = get_value(root, "version") or "unknown"
    generator_version = get_value(root, "generator_version") or "unknown"

    try:
        _v = int(version)
    except (TypeError, ValueError):
        _v = None
    format_newer_note = None
    if _v is not None and _v > MAX_TESTED_FORMAT_VERSION:
        format_newer_note = (
            f"file format version {_v} is newer than the max tested "
            f"({MAX_TESTED_FORMAT_VERSION}); analysis is best-effort")

    # Component grouping by reference prefix
    component_groups = group_components(footprints)

    # Per-net trace length measurement
    _stackup = _board_stackup(layers, setup)
    net_lengths = analyze_net_lengths(tracks, vias, net_names,
                                      include_segments=include_trace_segments,
                                      stackup=_stackup if include_trace_segments else None)

    # Power net routing analysis
    power_routing = analyze_power_nets(footprints, tracks, net_names,
                                       power_rails=_resolved_power_rails, pin_signals=pin_signals)

    # Pad-to-pad routed distance analysis (only with --full, needs segment data)
    pad_distances = None
    if include_trace_segments:
        pad_distances = analyze_pad_to_pad_distances(
            footprints, tracks, vias, net_names)

    # Ground domain identification
    ground_domains = analyze_ground_domains(footprints, net_names, zones,
                                            power_rails=_resolved_power_rails)

    # Current capacity facts
    current_capacity = analyze_current_capacity(tracks, vias, zones, net_names, setup,
                                                power_rails=_resolved_power_rails,
                                                pin_signals=pin_signals)

    # Layer transitions for ground return path analysis
    layer_transitions = analyze_layer_transitions(tracks, vias, net_names,
                                                  power_rails=_resolved_power_rails,
                                                  pin_signals=pin_signals)

    # Silkscreen text extraction
    silkscreen = extract_silkscreen(root, footprints)

    # Board metadata (title block, properties, paper size)
    metadata = extract_board_metadata(root)

    # Dimension annotations
    dimensions = extract_dimensions(root)

    # Groups (designer-defined component/routing groupings)
    groups = extract_groups(root)

    # Net classes — try .kicad_pro first (KiCad 6+), fall back to PCB file (KiCad 5)
    pro = load_kicad_pro(str(path), exact=True)
    project_settings = {}
    if pro:
        pro_net_classes = extract_pro_net_classes(pro)
        if pro_net_classes:
            net_classes = pro_net_classes
        else:
            net_classes = extract_net_classes(root)
        pro_rules = extract_pro_design_rules(pro)
        pro_text_vars = extract_pro_text_variables(pro)
        # Name the file that was actually loaded above, not an
        # independent rescan.
        project_settings = {
            'source': os.path.basename(
                find_project_settings_file(str(path), '.kicad_pro', exact=True) or ''),
        }
        if pro_net_classes:
            project_settings['net_classes'] = pro_net_classes
        if pro_rules:
            project_settings['design_rules'] = pro_rules
        if pro_text_vars:
            project_settings['text_variables'] = pro_text_vars
    else:
        net_classes = extract_net_classes(root)
    board_minima = effective_board_minima(root, pro)
    microvia_minima = microvia_class_minima(root, pro, vias, net_names)
    ignored = ignored_drc_checks(None if has_legacy_design_settings(root) else pro)
    if ignored:
        project_settings['_ignored_drc_checks'] = ignored

    # Custom design rules (.kicad_dru)
    custom_rules, dru_error = load_kicad_dru_checked(str(path))
    if custom_rules:
        project_settings['custom_rules'] = custom_rules
    if dru_error:
        project_settings['custom_rules_error'] = dru_error

    # Library tables
    lib_tables = load_lib_tables(str(path))
    if lib_tables.get('footprint_libs'):
        project_settings['footprint_libs'] = lib_tables['footprint_libs']

    ref_layer_map = _build_reference_layer_map(_stackup)

    # Return path continuity (only with --full, expensive)
    return_path = None
    gp001_samples = [] if gp001_debug else None
    reference_changes = None
    if include_trace_segments and zone_fills.has_data:
        reference_changes = []
        return_path = analyze_return_path_continuity(
            tracks, net_names, zones, zone_fills,
            ref_layer_map=ref_layer_map,
            footprints=footprints,
            radius_mm=return_path_radius_mm,
            debug_samples=gp001_samples,
            vias=vias,
            power_rails=_resolved_power_rails,
            copper_order=_copper_order_from_stackup(_stackup),
            pin_signals=pin_signals,
            stackup=_stackup,
            reference_changes=reference_changes)

    keepout_zones = _extract_keepout_zones(zones, footprints)

    return PcbFacts(
        connectivity=connectivity,
        stats=stats,
        version=version,
        generator_version=generator_version,
        format_newer_note=format_newer_note,
        component_groups=component_groups,
        net_lengths=net_lengths,
        power_routing=power_routing,
        pad_distances=pad_distances,
        ground_domains=ground_domains,
        current_capacity=current_capacity,
        layer_transitions=layer_transitions,
        silkscreen=silkscreen,
        metadata=metadata,
        dimensions=dimensions,
        groups=groups,
        net_classes=net_classes,
        project_settings=project_settings,
        board_minima=board_minima,
        microvia_minima=microvia_minima,
        ref_layer_map=ref_layer_map,
        return_path=return_path,
        gp001_samples=gp001_samples,
        keepout_zones=keepout_zones,
        reference_changes=reference_changes,
        power_rails=_resolved_power_rails,
        pin_signals=pin_signals,
    )


def _dfm_design_intent(config: dict | None, silkscreen: dict, metadata: dict | None) -> dict | None:
    """The design intent DFM judges against: the IPC class the project config, the fab notes or
    the title block name, as the ``design_intent`` block reports it. None when none names one
    (DFM then uses IPC Class 2)."""
    try:
        from design_intent import resolve_design_intent
    except ImportError:
        return None
    intent = resolve_design_intent(config or {}, pcb_data={
        'text_items': (silkscreen or {}).get('fab_texts', []), 'metadata': metadata or {}})
    return None if intent['source']['ipc_class'] == 'auto' else intent


def run_checks(board: BoardData, facts: PcbFacts, *, include_trace_segments: bool,
               config: dict | None = None) -> PcbChecks:
    """Phase 3: the checks in call order. assemble_result writes the results of the last
    seven (fiducials through board-edge vias). Reads the board and *facts*;
    mutates neither (tools/tests/test_pcb_phase_purity.py)."""
    setup = board.setup
    net_names = board.net_names
    footprints = board.footprints
    tracks = board.tracks
    vias = board.vias
    zones = board.zones
    zone_fills = board.zone_fills
    outline = board.outline
    silkscreen = facts.silkscreen
    net_classes = facts.net_classes
    project_settings = facts.project_settings
    ref_layer_map = facts.ref_layer_map

    # Decoupling placement analysis
    decoupling = analyze_decoupling_placement(footprints, facts.power_rails, facts.pin_signals)

    # Via analysis (types, annular ring, via-in-pad, fanout, current)
    via_analysis = analyze_vias(vias, footprints, net_names)

    # Thermal / via stitching analysis
    thermal = analyze_thermal_vias(footprints, vias, zones)

    # Placement analysis (courtyard overlaps, edge clearance, density)
    ignored_checks = project_settings.get('_ignored_drc_checks', frozenset())
    placement = analyze_placement(footprints, outline,
                                  check_overlaps='courtyards_overlap' not in ignored_checks)

    # DFM (Design for Manufacturing) scoring
    design_rules = (project_settings.get('design_rules')
                    or setup.get("design_rules"))
    dfm = analyze_dfm(footprints, tracks, vias, outline, design_rules,
                       net_classes=net_classes,
                       design_intent=_dfm_design_intent(config, silkscreen, facts.metadata))

    # Tombstoning risk assessment for small passives
    tombstoning = analyze_tombstoning_risk(footprints, tracks, vias, zones)

    # Thermal pad via adequacy for QFN/BGA packages
    thermal_pad_vias = analyze_thermal_pad_vias(footprints, vias, zones, zone_fills)

    # Copper presence analysis (cross-layer zone fill at pad locations)
    copper_presence = analyze_copper_presence(footprints, zones, zone_fills,
                                              ref_layer_map=ref_layer_map)

    # New assembly/DFM checks
    fiducial_check = analyze_fiducials(footprints)

    test_point_cov = analyze_test_point_coverage(footprints, net_names)

    orientation = analyze_orientation_consistency(footprints)

    silkscreen_overlaps = analyze_silkscreen_pad_overlaps(
        footprints, silkscreen.get("board_texts", []))

    keepout_list = facts.keepout_zones
    keepout_violations = ([] if 'items_not_allowed' in ignored_checks
                          else analyze_keepout_violations(footprints, vias, keepout_list))

    via_in_pad = None
    edge_via = None
    if include_trace_segments:
        via_in_pad = analyze_via_in_pad(
            footprints, vias,
            {(e.get("component", ""), str(e.get("pad_number", "")))
             for e in (thermal_pad_vias or [])})

        if 'copper_edge_clearance' not in ignored_checks:
            edge_via = analyze_board_edge_via_clearance(vias, outline)

    return PcbChecks(
        decoupling=decoupling,
        via_analysis=via_analysis,
        thermal=thermal,
        placement=placement,
        dfm=dfm,
        tombstoning=tombstoning,
        thermal_pad_vias=thermal_pad_vias,
        copper_presence=copper_presence,
        fiducial_check=fiducial_check,
        test_point_coverage=test_point_cov,
        orientation=orientation,
        silkscreen_overlaps=silkscreen_overlaps,
        keepout_violations=keepout_violations,
        via_in_pad=via_in_pad,
        edge_via=edge_via,
    )


def run_analyses(board: BoardData, *, include_trace_segments: bool, return_path_radius_mm: float,
                 gp001_debug: bool, resolved_power_rails: set[str] | None,
                 config: dict | None = None) -> PcbAnalyses:
    """Phases 2–3: run_facts then run_checks, composed into one PcbAnalyses."""
    facts = run_facts(board, include_trace_segments=include_trace_segments,
                      return_path_radius_mm=return_path_radius_mm,
                      gp001_debug=gp001_debug,
                      resolved_power_rails=resolved_power_rails)
    checks = run_checks(board, facts, include_trace_segments=include_trace_segments,
                        config=config)
    return PcbAnalyses(facts=facts, checks=checks)


def analyze_pcb(path: str, *, proximity: bool = False,
                include_trace_segments: bool = False,
                schematic_data: dict = None,
                return_path_radius_mm: float = 0.5,
                gp001_debug: bool = False,
                power_rails: set[str] | None = None,
                config: dict | None = None) -> dict:
    """Main analysis function.

    Args:
        path: Path to .kicad_pcb file.
        proximity: If True, run trace proximity analysis (spatial grid scan
            for signal nets running close together — useful for crosstalk
            assessment but adds computation time).
        return_path_radius_mm: Radius (mm) for copper-presence search in
            return-path analysis (default 0.5).
        gp001_debug: If True, emit per-sample diagnostic JSON to the
            analysis output directory.
        power_rails: Optional explicit set of net names to treat as power
            rails (overrides name heuristics). Takes priority over rails
            auto-read from `schematic_data`; when neither is given, net
            classification falls back to name-based heuristics alone.
        config: Optional loaded ``.kicad-happy.json``; its ``design_intent.ipc_class``
            sets the IPC class DFM judges against (else the fab notes or title block, else 2).
    """
    # One reader state per call — nothing survives into the next analyze_pcb()
    # in the same process (a stale mapping could leak a wrong non-zero net_number).
    state = PcbReaderState()

    _resolved_power_rails, _power_rails_source = resolve_power_rails(power_rails, schematic_data)
    board = read_board(path, state=state)
    analyses = run_analyses(board, include_trace_segments=include_trace_segments,
                            return_path_radius_mm=return_path_radius_mm,
                            gp001_debug=gp001_debug,
                            resolved_power_rails=_resolved_power_rails,
                            config=config)
    return assemble_result(board, analyses, proximity=proximity,
                           include_trace_segments=include_trace_segments,
                           schematic_data=schematic_data,
                           resolved_power_rails=_resolved_power_rails,
                           power_rails_source=_power_rails_source)


def finalize_for_cli(result: dict, config: dict, *, pcb_path: str, analysis_dir_arg: str | None,
                     return_path_radius_mm: float, stage: str | None,
                     output_arg: str | None = None) -> None:
    """Phase 5: command-specific annotation; mutates *result*."""
    # GP-001 debug: write per-sample diagnostics to disk and strip from output
    gp001_debug_data = result.pop("_gp001_debug_samples", None)
    if gp001_debug_data is not None:
        # The analysis dir when given (as for every other file), else beside --output,
        # else the board's directory
        if analysis_dir_arg:
            debug_dir = analysis_dir_arg
        elif output_arg:
            debug_dir = str(Path(output_arg).parent)
        else:
            debug_dir = str(Path(pcb_path).parent)
        debug_path = os.path.join(debug_dir, "gp001_debug.json")
        try:
            if os.path.islink(debug_path):
                raise OSError("target is a symlink")
            os.makedirs(debug_dir, exist_ok=True)
            from kicad_core.fileio import atomic_write_text
            atomic_write_text(debug_path, json.dumps({
                "description": "GP-001 return-path per-sample diagnostics",
                "radius_mm": return_path_radius_mm,
                "total_samples": len(gp001_debug_data),
                "hits": sum(1 for s in gp001_debug_data if s["hit"]),
                "misses": sum(1 for s in gp001_debug_data if not s["hit"]),
                "samples": gp001_debug_data,
            }, indent=2), follow_symlinks=False)
            print(f"GP-001 debug: {len(gp001_debug_data)} samples written to {debug_path}",
                  file=sys.stderr)
        except OSError as e:
            print(f"GP-001 debug write failed: {e}", file=sys.stderr)

    # Attach project config summary to output for downstream consumers
    project = config.get("project", {})
    if project:
        result["project_config"] = project

    # Resolve and attach design intent
    try:
        from design_intent import resolve_design_intent
        pcb_data_for_intent = {}
        if 'silkscreen' in result:
            pcb_data_for_intent['text_items'] = result['silkscreen'].get(
                'fab_texts', [])
        if 'layers' in result:
            pcb_data_for_intent['layers'] = result['layers']
        pcb_data_for_intent['net_classes'] = result.get('net_classes', [])
        pcb_data_for_intent['footprints'] = result.get('footprints', [])
        pcb_data_for_intent['metadata'] = result.get('board_metadata', {})
        # Build net_names from net_name_to_id if available
        net_names_dict = {}
        if 'net_name_to_id' in result:
            for name, nid in result['net_name_to_id'].items():
                net_names_dict[nid] = name
        pcb_data_for_intent['net_names'] = net_names_dict
        bbox = result.get('board_outline', {}).get('bounding_box')
        if bbox:
            pcb_data_for_intent['board_area_mm2'] = (
                bbox.get('width', 0) * bbox.get('height', 0))
        intent = resolve_design_intent(config, pcb_data=pcb_data_for_intent)
        result['design_intent'] = intent
    except ImportError:
        pass

    from output_filters import apply_output_filters
    apply_output_filters(result, stage)

    # Guarantee every finding carries a stable finding_id (Layer 2 merge keys
    # on it). Runs after all filtering; before any output branch.
    assign_finding_ids(result.get('findings', []), 'pcb')
