"""PCB result assembly: turns the board read by pcb.pipeline.read_board and the
intermediates computed by pcb.pipeline.run_analyses into the analyzer output dict.
Bodies are verbatim from analyze_pcb.py; only the signatures and the input
unpacking are new.
"""

import math
import re

from kicad_core.diagnostics import record
from kicad_core.netnames import is_ground_name, is_power_net_name
from pcb.connectivity import build_connectivity_graph
from pcb.routing import analyze_trace_proximity
from pcb.dfm import analyze_design_rule_compliance
from pcb.assembly import (
    _compute_switching_loop_areas,
)
from finding_schema import compute_trust_summary, sort_findings


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


def assemble_result(board: "BoardData", analyses: "PcbAnalyses", *, proximity: bool,
                    include_trace_segments: bool, schematic_data: dict | None,
                    resolved_power_rails: set[str] | None,
                    power_rails_source: str) -> dict:
    """Phase 4: build the PCB analyzer result dict (historical key order).

    Mutates nothing caller-owned except `connectivity` (pops `unrouted`) and the
    sections it pops back out of `result`; the late checks ran in pcb.pipeline.run_checks
    and only their result writes stay here. *board* is a pcb.pipeline.BoardData and
    *analyses* a pcb.pipeline.PcbAnalyses.
    """
    diagnostics: list = []
    layers = board.layers
    setup = board.setup
    net_names = board.net_names
    footprints = board.footprints
    tracks = board.tracks
    vias = board.vias
    zones = board.zones
    zone_fills = board.zone_fills
    outline = board.outline
    connectivity = analyses.connectivity
    stats = analyses.stats
    version = analyses.version
    generator_version = analyses.generator_version
    format_newer_note = analyses.format_newer_note
    component_groups = analyses.component_groups
    net_lengths = analyses.net_lengths
    power_routing = analyses.power_routing
    pad_distances = analyses.pad_distances
    decoupling = analyses.decoupling
    ground_domains = analyses.ground_domains
    current_capacity = analyses.current_capacity
    via_analysis = analyses.via_analysis
    thermal = analyses.thermal
    layer_transitions = analyses.layer_transitions
    placement = analyses.placement
    silkscreen = analyses.silkscreen
    metadata = analyses.metadata
    dimensions = analyses.dimensions
    groups = analyses.groups
    net_classes = analyses.net_classes
    project_settings = analyses.project_settings
    dfm = analyses.dfm
    tombstoning = analyses.tombstoning
    thermal_pad_vias = analyses.thermal_pad_vias
    copper_presence = analyses.copper_presence
    return_path = analyses.return_path
    gp001_samples = analyses.gp001_samples
    _resolved_power_rails = resolved_power_rails
    _power_rails_source = power_rails_source

    # Compact footprint output — include pad-to-net mapping but omit pad geometry
    footprint_summary = []
    for fp in footprints:
        fp_summary = {k: v for k, v in fp.items() if k != "pads"}
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
        "keepout_zones": analyses.keepout_zones,
        "connectivity": connectivity,
        "net_lengths": net_lengths,
    }

    if pad_distances:
        result["pad_to_pad_distances"] = pad_distances
    # TH-043-residual: always emit (schema-required); empty list when no power routing.
    result["power_net_routing"] = power_routing if power_routing else []

    # KH-393: record which nets classified as power/ground under the
    # resolution actually used, and where that resolution came from.
    result["power_net_resolution"] = {
        "power": sorted({n for n in net_names.values()
                         if n and is_power_net_name(n, _resolved_power_rails)}),
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

    # TH-043-residual: always emit (schema-required); domain_count=0 is meaningful info.
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
            tracks, net_names, power_rails=_resolved_power_rails)

    # board_metadata + design_rule_compliance are required envelope keys
    # (schema declares them dict not Optional[dict]). Always emit, even
    # when empty, so schema-vs-emit drift can't surface (TH-043).
    result["board_metadata"] = metadata or {}
    if dimensions:
        result["dimensions"] = dimensions
    if groups:
        result["groups"] = groups
    if net_classes:
        result["net_classes"] = net_classes
    if project_settings:
        result["project_settings"] = project_settings

    # Design rule compliance (project rules vs actual layout) — always emit
    # at least an empty dict so the schema-required key is present.
    if project_settings:
        design_compliance = analyze_design_rule_compliance(
            tracks, vias, project_settings, footprints=footprints)
        result["design_rule_compliance"] = design_compliance or {}
    else:
        result["design_rule_compliance"] = {}

    # Manufacturing and assembly analysis
    if dfm:
        result["dfm"] = dfm
    if tombstoning:
        result["tombstoning_risk"] = tombstoning
    if thermal_pad_vias:
        result["thermal_pad_vias"] = thermal_pad_vias
    if copper_presence:
        result["copper_presence"] = copper_presence
    if return_path:
        result["return_path_continuity"] = return_path
    if gp001_samples is not None:
        result["_gp001_debug_samples"] = gp001_samples

    # New assembly/DFM checks
    fiducial_check = analyses.fiducial_check
    if fiducial_check.get("findings"):
        result["fiducial_check"] = fiducial_check

    test_point_cov = analyses.test_point_coverage
    result["test_point_coverage"] = test_point_cov

    orientation = analyses.orientation
    if orientation:
        result["orientation_consistency"] = orientation

    silkscreen_overlaps = analyses.silkscreen_overlaps
    if silkscreen_overlaps:
        result["silkscreen_pad_overlaps"] = silkscreen_overlaps

    keepout_violations = analyses.keepout_violations
    if keepout_violations:
        result["keepout_violations"] = keepout_violations

    if include_trace_segments:
        via_in_pad = analyses.via_in_pad
        if via_in_pad:
            result["via_in_pad_issues"] = via_in_pad

        edge_via = analyses.edge_via
        if edge_via:
            result["board_edge_via_clearance"] = edge_via

        result["tracks"]["segments"] = tracks.get("segments", [])
        result["tracks"]["arcs"] = tracks.get("arcs", [])
        result["vias"]["vias"] = vias.get("vias", [])

        # Build copper connectivity graph (requires full track/via data)
        try:
            conn_graph = build_connectivity_graph(
                footprints, tracks, vias, zone_fills, zones, net_names)
            if conn_graph:
                result["connectivity_graph"] = conn_graph
        except Exception as e:
            err_str = str(e)[:200]
            result["connectivity_graph_error"] = (
                f"connectivity graph unavailable: {type(e).__name__}: {err_str}")
            record(diagnostics, "pcb.presentation.assemble_result", e, "connectivity_graph omitted")

    # --- Harmonization: collect all findings into top-level list ---
    findings = []

    # Simple list sections (entries have rule_id from Batch 7 migration)
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
    # TH-043-residual: always emit (schema-required); empty dict when placement/density missing.
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

    connectivity_dict = result.get('connectivity', {})
    if isinstance(connectivity_dict, dict):
        unrouted = connectivity_dict.pop('unrouted', None)
        if unrouted:
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

    # Deterministic order for byte-identical repeated runs (KH-316).
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
