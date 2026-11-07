"""PCB result assembly: turns the board read by pcb.pipeline.read_board and the
intermediates computed by pcb.pipeline.run_analyses into the analyzer output dict.
"""

import math
import re

from kicad_core.diagnostics import record
from kicad_core.netnames import is_ground_name, is_power_net_name
from pcb.connectivity import build_connectivity_graph
from pcb.routing import analyze_trace_proximity, board_pin_signals
from pcb.dfm import analyze_design_rule_compliance
from pcb.assembly import (
    _compute_switching_loop_areas,
)
from finding_schema import compute_trust_summary, show_decoded_names, sort_findings


def group_components(footprints: list[dict]) -> dict:
    """Group components by reference prefix for cross-referencing with schematic."""
    groups: dict[str, list[str]] = {}
    for fp in footprints:
        ref = fp.get("reference", "")
        if not ref:
            continue
        m = re.match(r'^([A-Za-z]+)', ref)
        prefix = m.group(1) if m else ref
        groups.setdefault(prefix, []).append(ref)

    return {prefix: {"count": len(refs), "references": sorted(refs)}
            for prefix, refs in sorted(groups.items())}


def compute_statistics(footprints: list[dict], tracks: dict, vias: dict,
                       zones: list[dict], outline: dict, connectivity: dict,
                       net_names: dict[int, str] | None = None,
                       layers: list[dict] | None = None) -> dict:
    """Compute summary statistics."""
    # EQ-059: d = √(w²+h²) (board diagonal)
    # Resolve copper layer names from declarations
    if layers:
        copper_layer_names = {l["name"] for l in layers if "Cu" in l["name"]}
    else:
        copper_layer_names = None
    # F.Cu/B.Cu names are invariant across all KiCad versions (5-9)
    front_copper, back_copper = "F.Cu", "B.Cu"

    # Component side distribution
    front = sum(1 for fp in footprints if fp["layer"] == front_copper)
    back = sum(1 for fp in footprints if fp["layer"] == back_copper)

    # SMD vs through-hole
    smd = sum(1 for fp in footprints if fp["type"] == "smd")
    tht = sum(1 for fp in footprints if fp["type"] == "through_hole")

    # Total track length
    total_length = 0
    for seg in tracks.get("segments", []):
        dx = seg["x2"] - seg["x1"]
        dy = seg["y2"] - seg["y1"]
        total_length += math.sqrt(dx * dx + dy * dy)

    # Copper layer count — tracks, vias, and zones
    all_used_layers = set()
    for seg in tracks.get("segments", []):
        all_used_layers.add(seg.get("layer", ""))
    for via in vias.get("vias", []):
        for l in via.get("layers", []):
            all_used_layers.add(l)
    for zone in zones:
        for l in zone.get("layers", []):
            all_used_layers.add(l)
    if copper_layer_names:
        copper_layers = all_used_layers & copper_layer_names
    else:
        copper_layers = {l for l in all_used_layers if "Cu" in l}

    return {
        "footprint_count": len(footprints),
        "front_side": front,
        "back_side": back,
        "smd_count": smd,
        "tht_count": tht,
        "copper_layers_used": len(copper_layers),
        "copper_layer_names": sorted(copper_layers),
        "track_segments": tracks["total_count"],
        "via_count": vias["count"],
        "zone_count": len(zones),
        "total_track_length_mm": round(total_length, 2),
        "board_width_mm": outline["bounding_box"]["width"] if outline.get("bounding_box") else None,
        "board_height_mm": outline["bounding_box"]["height"] if outline.get("bounding_box") else None,
        "board_area_mm2": round(outline["bounding_box"]["width"] * outline["bounding_box"]["height"], 1) if outline.get("bounding_box") else None,
        "net_count": sum(1 for v in (net_names or {}).values() if v),
        "routing_complete": connectivity.get("routing_complete", False),
        "unrouted_net_count": connectivity.get("unrouted_count", 0),
    }


def _routing_from_graph(connectivity: dict, graph: dict, *,
                        net_ids: dict[str, int] | None = None) -> dict:
    """A copy of *connectivity* whose unrouted nets are those with pads on more than one
    copper island of *graph*. A net without copper keeps its entry; pads the graph joins
    (overlapping copper, KiCad jumper pads) do not make a net unrouted. `routed_nets`
    counts the multi-pad nets that are not unrouted."""
    kept = {u["net_name"]: u for u in connectivity.get("unrouted", [])}
    unrouted = [u for name, u in kept.items() if name not in graph]
    multi_pad = len(unrouted)
    for net in sorted(graph):
        comps = graph[net].get("components", {})
        pads = sorted(k for k in comps if not k.startswith("via_"))
        if len(pads) > 1:
            multi_pad += 1
        islands = len({comps[k] for k in pads})
        if islands < 2:
            continue
        if net in kept:
            unrouted.append(kept[net])
            continue
        # graph keys are REF:NUMBER, later pads with the same pair add #n
        names = [re.sub(r"#\d+$", "", k).replace(":", ".", 1) for k in pads]
        unrouted.append({
            "net_number": (net_ids or {}).get(net, 0),
            "net_name": net,
            "pad_count": len(pads),
            "pads": names,
            "detector": "analyze_connectivity",
            "rule_id": "RT-001",
            "category": "connectivity",
            "severity": "error",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": f"Incompletely routed net {net} ({islands} copper islands hold its {len(pads)} pads)",
            "description": f"Net {net} has {len(pads)} pads on {islands} separate copper islands.",
            "components": sorted({n.split(".", 1)[0] for n in names}),
            "nets": [net],
            "pins": [],
            "recommendation": f"Connect the {islands} copper islands of net {net}",
            "report_context": {"section": "Connectivity", "impact": "functionality", "standard_ref": ""},
        })
    out = dict(connectivity)
    out["routed_nets"] = multi_pad - len(unrouted)
    out["unrouted_count"] = len(unrouted)
    out["routing_complete"] = not unrouted
    out["unrouted"] = sorted(unrouted, key=lambda u: u["net_name"])
    return out


def assemble_result(board: "BoardData", analyses: "PcbAnalyses", *, proximity: bool,
                    include_trace_segments: bool, schematic_data: dict | None,
                    resolved_power_rails: set[str] | None,
                    power_rails_source: str) -> dict:
    """Phase 4: build the PCB analyzer result dict (stable output key order).

    Mutates nothing caller-owned except two late writes to the facts (it pops `unrouted`
    out of `connectivity` and `_ignored_drc_checks` out of `project_settings`) and the
    sections it pops back out of `result`; the late checks run in pcb.pipeline.run_checks
    and only their result writes happen here. *board* is a pcb.pipeline.BoardData and
    *analyses* a pcb.pipeline.PcbAnalyses.
    """
    facts, checks = analyses.facts, analyses.checks
    diagnostics: list = list(board.diagnostics)
    layers = board.layers
    setup = board.setup
    net_names = board.net_names
    footprints = board.footprints
    tracks = board.tracks
    vias = board.vias
    zones = board.zones
    zone_fills = board.zone_fills
    outline = board.outline
    connectivity = facts.connectivity
    stats = facts.stats
    version = facts.version
    generator_version = facts.generator_version
    format_newer_note = facts.format_newer_note
    component_groups = facts.component_groups
    net_lengths = facts.net_lengths
    power_routing = facts.power_routing
    pad_distances = facts.pad_distances
    decoupling = checks.decoupling
    ground_domains = facts.ground_domains
    current_capacity = facts.current_capacity
    via_analysis = checks.via_analysis
    thermal = checks.thermal
    layer_transitions = facts.layer_transitions
    placement = checks.placement
    silkscreen = facts.silkscreen
    metadata = facts.metadata
    dimensions = facts.dimensions
    groups = facts.groups
    net_classes = facts.net_classes
    project_settings = facts.project_settings
    dfm = checks.dfm
    tombstoning = checks.tombstoning
    thermal_pad_vias = checks.thermal_pad_vias
    copper_presence = checks.copper_presence
    return_path = facts.return_path
    gp001_samples = facts.gp001_samples
    _resolved_power_rails = resolved_power_rails
    pin_signals = board_pin_signals(board.footprints, _resolved_power_rails)
    _power_rails_source = power_rails_source

    # Compact footprint output — include pad-to-net mapping but omit pad geometry
    footprint_summary = []
    for fp in footprints:
        fp_summary = {k: v for k, v in fp.items() if k not in ("pads", "_courtyard_poly", "_courtyard_sides", "_duplicate_pad_jumpers", "_jumper_pad_groups")}
        # Alias: 'footprint' mirrors 'library' for cross-analyzer consistency
        # (schematic analyzer uses 'footprint', PCB uses 'library' for same data)
        if "library" in fp_summary and "footprint" not in fp_summary:
            fp_summary["footprint"] = fp_summary["library"]
        # Per-pad net mapping (pad number → net name + pin function)
        pad_nets = {}
        fp_nets = set()
        for pad in fp["pads"]:
            nn = pad.get("net_name", "")
            if nn:
                fp_nets.add(nn)
                entry = {"net": nn}
                pf = pad.get("pinfunction")
                if pf:
                    entry["pin"] = pf
                pad_nets[pad["number"]] = entry
        fp_summary["pad_nets"] = pad_nets
        fp_summary["connected_nets"] = sorted(fp_nets)
        footprint_summary.append(fp_summary)

    result = {
        "analyzer_type": "pcb",
        "schema_version": "1.4.0",
        "kicad_version": generator_version,
        "file_version": version,
        "statistics": stats,
        "layers": layers,
        "setup": setup,
        "nets": {str(k): v for k, v in net_names.items() if v},  # net_id -> net_name
        "net_name_to_id": {v: k for k, v in net_names.items() if v},  # net_name -> net_id
        "board_outline": outline,
        "component_groups": component_groups,
        "footprints": footprint_summary,
        "tracks": {
            "segment_count": tracks["segment_count"],
            "arc_count": tracks["arc_count"],
            "width_distribution": tracks["width_distribution"],
            "layer_distribution": tracks["layer_distribution"],
            # Omit individual segments — too large. Use --full for that.
        },
        "vias": {
            "count": vias["count"],
            "size_distribution": vias["size_distribution"],
            **({"via_analysis": via_analysis} if via_analysis else {}),
        },
        "zones": zones,
        "keepout_zones": facts.keepout_zones,
        "connectivity": connectivity,
        "net_lengths": net_lengths,
    }

    if pad_distances:
        result["pad_to_pad_distances"] = pad_distances
    # Always emit (schema-required); empty list when no power routing.
    result["power_net_routing"] = power_routing if power_routing else []

    # Record which nets classified as power/ground under the
    # resolution actually used, and where that resolution came from.
    result["power_net_resolution"] = {
        "power": sorted({n for n in net_names.values()
                         if n and n not in pin_signals
                         and is_power_net_name(n, _resolved_power_rails)}),
        "ground": sorted({n for n in net_names.values()
                          if n and is_ground_name(n)}),
        "source": _power_rails_source,
    }
    if decoupling:
        result["decoupling_placement"] = decoupling
        # Flat decoupling proximity matrix for EMC/cross-verify consumers
        decoupling_proximity = []
        for entry in decoupling:
            ic_ref = entry["ic"]
            for cap in entry.get("nearby_caps", []):
                decoupling_proximity.append({
                    "ic_ref": ic_ref,
                    "cap_ref": cap["cap"],
                    "distance_mm": cap["distance_mm"],
                    "cap_value": cap.get("value", ""),
                    "same_side": cap.get("same_side", True),
                    "shared_nets": cap.get("shared_nets", []),
                })
        if decoupling_proximity:
            result["decoupling_proximity"] = decoupling_proximity
    if schematic_data:
        loop_areas = _compute_switching_loop_areas(footprints, schematic_data)
        if loop_areas:
            result["switching_loop_areas"] = loop_areas

    # Always emit (schema-required); domain_count=0 is meaningful info.
    result["ground_domains"] = ground_domains
    if current_capacity["power_ground_nets"] or current_capacity["narrow_signal_nets"]:
        result["current_capacity"] = current_capacity
    if thermal["zone_stitching"] or thermal["thermal_pads"]:
        result["thermal_analysis"] = thermal
    if layer_transitions:
        result["layer_transitions"] = layer_transitions
    if placement.get("courtyard_overlaps") or placement.get("edge_clearance_warnings"):
        result["placement_analysis"] = placement
    elif placement.get("density"):
        result["placement_analysis"] = {"density": placement["density"]}
    result["silkscreen"] = silkscreen
    if proximity:
        result["trace_proximity"] = analyze_trace_proximity(
            tracks, net_names, power_rails=_resolved_power_rails, pin_signals=pin_signals)

    # board_metadata + design_rule_compliance are required envelope keys
    # (schema declares them dict not Optional[dict]). Always emit, even
    # when empty, so schema-vs-emit drift can't surface.
    result["board_metadata"] = metadata or {}
    if dimensions:
        result["dimensions"] = dimensions
    if groups:
        result["groups"] = groups
    if net_classes:
        result["net_classes"] = net_classes
    ignored_checks = (project_settings or {}).pop('_ignored_drc_checks', frozenset())
    if project_settings:
        result["project_settings"] = project_settings

    # Design rule compliance (board minima and project rules vs actual layout); every board
    # has minima, so the schema-required key always carries a result.
    design_compliance = analyze_design_rule_compliance(
        tracks, vias, project_settings or {}, footprints=footprints,
        minima=facts.board_minima, board_layers=[l["name"] for l in layers or []],
        ignored_checks=ignored_checks, microvia_minima=facts.microvia_minima)
    result["design_rule_compliance"] = design_compliance or {}

    # Manufacturing and assembly analysis
    if dfm:
        result["dfm"] = dfm
    if tombstoning:
        result["tombstoning_risk"] = tombstoning
    if thermal_pad_vias:
        result["thermal_pad_vias"] = thermal_pad_vias
    if copper_presence:
        result["copper_presence"] = copper_presence
    if return_path is not None:  # [] = checked, no gaps; absent = not run
        result["return_path_continuity"] = return_path
        result["reference_plane_changes"] = facts.reference_changes
    if gp001_samples is not None:
        result["_gp001_debug_samples"] = gp001_samples

    # New assembly/DFM checks
    fiducial_check = checks.fiducial_check
    if fiducial_check.get("findings"):
        result["fiducial_check"] = fiducial_check

    test_point_cov = checks.test_point_coverage
    result["test_point_coverage"] = test_point_cov

    orientation = checks.orientation
    if orientation:
        result["orientation_consistency"] = orientation

    silkscreen_overlaps = checks.silkscreen_overlaps
    if silkscreen_overlaps:
        result["silkscreen_pad_overlaps"] = silkscreen_overlaps

    keepout_violations = checks.keepout_violations
    if keepout_violations:
        result["keepout_violations"] = keepout_violations

    conn_graph = None
    if include_trace_segments:
        via_in_pad = checks.via_in_pad
        if via_in_pad:
            result["via_in_pad_issues"] = via_in_pad

        edge_via = checks.edge_via
        if edge_via:
            result["board_edge_via_clearance"] = edge_via

        result["tracks"]["segments"] = tracks.get("segments", [])
        result["tracks"]["arcs"] = tracks.get("arcs", [])
        result["vias"]["vias"] = vias.get("vias", [])

        # Build copper connectivity graph (requires full track/via data)
        try:
            conn_graph = build_connectivity_graph(
                footprints, tracks, vias, zone_fills, zones, net_names,
                board_layers=layers, graphics=board.graphics)
            if conn_graph:
                result["connectivity_graph"] = conn_graph
        except Exception as e:
            conn_graph = None
            err_str = str(e)[:200]
            result["connectivity_graph_error"] = (
                f"connectivity graph unavailable: {type(e).__name__}: {err_str}")
            record(diagnostics, "pcb.presentation.assemble_result", e, "connectivity_graph omitted")
        if conn_graph is not None:
            routing = _routing_from_graph(connectivity, conn_graph,
                                          net_ids=result["net_name_to_id"])
            result["connectivity"] = routing
            result["statistics"] = {**stats, "routing_complete": routing["routing_complete"],
                                    "unrouted_net_count": routing["unrouted_count"]}

    # --- Harmonization: collect all findings into top-level list ---
    findings = []

    # Simple list sections (entries have a rule_id)
    _FINDING_LIST_KEYS = [
        'tombstoning_risk', 'thermal_pad_vias', 'orientation_consistency',
        'silkscreen_pad_overlaps', 'via_in_pad_issues',
        'board_edge_via_clearance', 'keepout_violations',
    ]
    for key in _FINDING_LIST_KEYS:
        data = result.pop(key, None)
        if isinstance(data, list):
            findings.extend(data)

    # Dict sections with findings sub-key
    fiducial = result.pop('fiducial_check', None)
    if fiducial and isinstance(fiducial, dict):
        findings.extend(fiducial.get('findings', []))

    test_point = result.pop('test_point_coverage', None)
    if test_point and isinstance(test_point, dict) and 'rule_id' in test_point:
        findings.append(test_point)

    # Nested sections: extract findings, keep summary data
    dfm_data = result.pop('dfm', None)
    if dfm_data:
        findings.extend(dfm_data.get('violations', []))
        ipc = dfm_data.get('ipc_class_compliance', {})
        findings.extend(ipc.get('violations', []))
        # Keep non-finding DFM data
        result['dfm_summary'] = {
            'dfm_tier': dfm_data.get('dfm_tier', ''),
            'metrics': dfm_data.get('metrics', {}),
            'violation_count': dfm_data.get('violation_count', 0),
        }
        if ipc:
            result['dfm_summary']['ipc_class_compliance'] = {
                'detected_class': ipc.get('detected_class'),
                'detection_source': ipc.get('detection_source', ''),
            }

    placement = result.pop('placement_analysis', None)
    if placement:
        findings.extend(placement.get('courtyard_overlaps', []))
        findings.extend(placement.get('edge_clearance_warnings', []))
    # Always emit (schema-required); empty dict when placement/density missing.
    result['placement_density'] = (placement or {}).get('density') or {}

    thermal_sec = result.pop('thermal_analysis', None)
    if thermal_sec:
        findings.extend(thermal_sec.get('zone_stitching', []))
        # TP-DET (per-pad "nearby vias" count) is superseded by TV-001
        # which copper-verifies the same vias through zone fills. Emitting
        # both produced conflicting counts on the same pad and confused
        # reviewers. Keep the raw thermal_pads data accessible for manual
        # inspection but don't surface it as findings.
        if thermal_sec.get('thermal_pads'):
            result['thermal_pad_scan'] = thermal_sec['thermal_pads']

    current_cap = result.pop('current_capacity', None)
    if current_cap:
        findings.extend(current_cap.get('power_ground_nets', []))
        findings.extend(current_cap.get('narrow_signal_nets', []))
        if 'board_thickness_mm' in current_cap:
            result['board_thickness_mm'] = current_cap['board_thickness_mm']

    unrouted = connectivity.pop('unrouted', None)
    if result['connectivity'] is not connectivity:
        unrouted = result['connectivity'].pop('unrouted', None)
    if unrouted and 'unconnected_items' not in ignored_checks:
        findings.extend(unrouted)

    copper = result.pop('copper_presence', None)
    if copper:
        findings.extend(copper.get('same_layer_foreign_zones', []))
        findings.extend(copper.get('no_opposite_layer_copper_findings', []))
        findings.extend(copper.get('touch_pad_gnd_clearance', []))
        if copper.get('opposite_layer_summary'):
            result['copper_presence_summary'] = copper['opposite_layer_summary']

    if format_newer_note:
        findings.append({
            "detector": "format_version_gate",
            "rule_id": "FV-001",
            "category": "file_format",
            "severity": "info",
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": format_newer_note,
            "description": format_newer_note,
            "components": [],
            "nets": [],
            "pins": [],
            "recommendation": "",
            "report_context": {"section": "File Format", "impact": "", "standard_ref": ""},
        })

    show_decoded_names(findings)
    # Deterministic order for byte-identical repeated runs.
    sort_findings(findings)

    result['findings'] = findings
    result['assessments'] = []
    result['trust_summary'] = compute_trust_summary(findings)

    # Build summary
    sev_counts = {"error": 0, "warning": 0, "info": 0}
    for f in findings:
        sev = f.get("severity", "info").lower()
        if sev in sev_counts:
            sev_counts[sev] += 1
    result['summary'] = {
        'total_findings': len(findings),
        'by_severity': sev_counts,
    }

    result["diagnostics"] = diagnostics
    return result
