"""PCB DFM: fab-capability scoring, drill measurement, project design-rule compliance.
Fab tables at module level; analyze_dfm composes the _measure_* scans and the _emit_* builders."""

import math


# KH-412: drills below this are file artefacts (e.g. `(drill 0.00001)` pads
# in HamedMasafi/MeloCar remote_3.kicad_pcb), not holes a fab will drill.
# They are excluded from every minimum and listed in
# via_analysis.degenerate_drills so nothing is silently dropped.
MIN_REAL_DRILL_MM = 0.05


def _is_real_drill(d) -> bool:
    return isinstance(d, (int, float)) and d >= MIN_REAL_DRILL_MM


def _degenerate_drills(footprints: list[dict], all_vias: list[dict]) -> list[dict]:
    """Pad and via drills in (0, MIN_REAL_DRILL_MM), sorted by (kind, ref, pad)."""
    out: list[dict] = []
    for fp in footprints or []:
        for pad in fp.get("pads", []):
            if pad.get("type") not in ("thru_hole", "np_thru_hole"):
                continue
            d = _pad_effective_drill(pad)
            if d and 0 < d < MIN_REAL_DRILL_MM:
                out.append({"kind": "pad", "ref": fp.get("reference", ""),
                            "pad": str(pad.get("number", "")), "drill_mm": d})
    for via in all_vias or []:
        d = via.get("drill", 0) or 0
        if 0 < d < MIN_REAL_DRILL_MM:
            out.append({"kind": "via", "ref": None, "pad": None, "drill_mm": d,
                        "x": via.get("x"), "y": via.get("y")})
    return sorted(out, key=lambda e: (e["kind"], e["ref"] or "", e["pad"] or "",
                                      e.get("x") or 0, e.get("y") or 0))


def _pad_effective_drill(pad: dict) -> float:
    """Effective drill diameter (mm) for one pad, oval-drill aware.

    An oval drill stores its two dimensions separately: `drill` (first,
    "width") and `drill_h` (second, "height") — see the parser around
    `pad_info["drill_h"]`. Whichever dimension is smaller is what actually
    determines the smallest hole a fab has to drill (e.g. a polarized
    connector's slotted mounting hole), so use the smaller of the two.
    """
    d = pad.get("drill", 0) or 0
    h = pad.get("drill_h")
    if isinstance(h, (int, float)) and h > 0 and (d <= 0 or h < d):
        return h
    return d


def _pad_drills(footprints: list[dict]) -> list[float]:
    """Drill diameters (mm) of thru_hole/np_thru_hole pads across footprints.

    Plated (thru_hole) and non-plated (np_thru_hole) through-hole pads
    both go through a mechanical drill step, so both count toward the
    board's smallest drill. SMD pads have no drill and are skipped.
    """
    drills: list[float] = []
    for fp in footprints:
        for pad in fp.get("pads", []):
            if pad.get("type") not in ("thru_hole", "np_thru_hole"):
                continue
            d = _pad_effective_drill(pad)
            if _is_real_drill(d):
                drills.append(d)
    return drills


def _min_drill_with_source(
        via_drills: list[float],
        footprints: list[dict] | None) -> tuple[float | None, str]:
    """Smallest drill (mm) across via drills and footprint pad drills.

    Board vias aren't the only mechanically-drilled holes — a footprint's
    own thru_hole/np_thru_hole pads (e.g. a thermal via pattern baked into
    a QFN footprint) are drilled too, and can be smaller than any via on
    the board. Returns (None, "") when there are no drills at all,
    (min, "via") when the minimum comes from a via, or (min, "pad <ref>")
    when a footprint pad drill is the smallest.
    """
    min_via = (min(v for v in via_drills if _is_real_drill(v))
               if any(_is_real_drill(v) for v in via_drills) else None)

    min_pad = None
    min_pad_ref = ""
    for fp in (footprints or []):
        ref = fp.get("reference", "")
        for pad in fp.get("pads", []):
            if pad.get("type") not in ("thru_hole", "np_thru_hole"):
                continue
            d = _pad_effective_drill(pad)
            if _is_real_drill(d) and (min_pad is None or d < min_pad):
                min_pad = d
                min_pad_ref = ref

    if min_pad is not None and (min_via is None or min_pad < min_via):
        return min_pad, f"pad {min_pad_ref}"
    if min_via is not None:
        return min_via, "via"
    return None, ""


# JLCPCB standard process limits (mm)
# Source: JLCPCB capabilities page, verified 2025-01.
# Canonical table in references/standards-compliance.md "Fab House Capabilities"
JLCPCB_LIMITS_STANDARD = {
    "min_track_width": 0.127,      # 5 mil — JLCPCB standard tier
    "min_track_spacing": 0.127,     # 5 mil — JLCPCB standard tier
    "min_drill": 0.2,              # PTH drill — JLCPCB standard tier
    "min_annular_ring": 0.125,     # via annular ring — JLCPCB standard tier
    "max_board_width": 100.0,      # pricing threshold (>100mm costs more)
    "max_board_height": 100.0,
    "min_board_dim": 10.0,         # handling minimum
}
# JLCPCB advanced process limits (mm)
JLCPCB_LIMITS_ADVANCED = {
    "min_track_width": 0.1,        # 4 mil — JLCPCB advanced tier
    "min_track_spacing": 0.1,      # 4 mil — JLCPCB advanced tier
    "min_drill": 0.15,             # JLCPCB advanced tier
    "min_annular_ring": 0.1,       # JLCPCB advanced tier
}

# IPC class thresholds (design quality ceiling)
# Source: IPC-6012 Rev E, verified against industry guidelines
IPC_CLASS_LIMITS = {
    1: {
        'min_annular_ring_via': 0.10,    # mm
        'min_annular_ring_pth': 0.10,    # mm
        'via_in_pad_fill_required': False,
    },
    2: {
        'min_annular_ring_via': 0.125,   # mm
        'min_annular_ring_pth': 0.175,   # mm
        'via_in_pad_fill_required': False,
    },
    3: {
        'min_annular_ring_via': 0.15,    # mm
        'min_annular_ring_pth': 0.25,    # mm
        'via_in_pad_fill_required': True,
        'annular_ring_breakout_allowed': False,
    },
}


def _build_net_class_lookup(net_classes: list[dict] | None) -> dict[str, dict]:
    # Build net name -> net class lookup for net-class-aware checks
    _net_class_lookup: dict[str, dict] = {}  # net_name -> class constraints
    if net_classes:
        for nc in net_classes:
            nc_name = nc.get('name', '')
            if nc_name == 'Default':
                continue
            constraints = {
                'name': nc_name,
                'trace_width': nc.get('track_width'),
                'clearance': nc.get('clearance'),
                'diff_pair_width': nc.get('diff_pair_width'),
                'diff_pair_gap': nc.get('diff_pair_gap'),
            }
            for net_name in nc.get('nets', []):
                _net_class_lookup[net_name] = constraints
    return _net_class_lookup


def _measure_track_widths(tracks: dict, net_class_lookup: dict[str, dict]) -> dict:
    _net_class_lookup = net_class_lookup
    LIMITS_ADV = JLCPCB_LIMITS_ADVANCED
    # --- Track width analysis (net-class-aware) ---
    all_widths = []
    narrowest_non_class = float('inf')  # narrowest trace NOT covered by net class
    for seg in tracks.get("segments", []):
        w = seg["width"]
        all_widths.append(w)
        seg_net_name = seg.get("net_name", "")
        nc = _net_class_lookup.get(seg_net_name)
        if nc and nc.get('trace_width') is not None:
            if w < LIMITS_ADV["min_track_width"]:
                narrowest_non_class = min(narrowest_non_class, w)
        else:
            narrowest_non_class = min(narrowest_non_class, w)

    for arc in tracks.get("arcs", []):
        w = arc["width"]
        all_widths.append(w)
        arc_net_name = arc.get("net_name", "")
        nc = _net_class_lookup.get(arc_net_name)
        if nc and nc.get('trace_width') is not None:
            if w < LIMITS_ADV["min_track_width"]:
                narrowest_non_class = min(narrowest_non_class, w)
        else:
            narrowest_non_class = min(narrowest_non_class, w)

    min_width = None
    check_width = None
    if all_widths:
        min_width = min(all_widths)

        check_width = (narrowest_non_class
                       if narrowest_non_class < float('inf')
                       else min_width)
    return {"all_widths": all_widths, "narrowest_non_class": narrowest_non_class,
            "min_width": min_width, "check_width": check_width}


def _emit_track_width_violations(m: dict, limits_std: dict, limits_adv: dict) -> list[dict]:
    LIMITS_STD = limits_std
    LIMITS_ADV = limits_adv
    violations = []
    if m["all_widths"]:
        check_width = m["check_width"]
        if check_width < LIMITS_ADV["min_track_width"]:
            violations.append({
                "parameter": "track_width",
                "actual_mm": check_width,
                "standard_limit_mm": LIMITS_STD["min_track_width"],
                "advanced_limit_mm": LIMITS_ADV["min_track_width"],
                "tier_required": "challenging",
                "message": f"Track width {check_width}mm is below advanced "
                           f"process minimum "
                           f"({LIMITS_ADV['min_track_width']}mm)",
                "detector": "analyze_dfm",
                "rule_id": "DFM-001",
                "category": "dfm",
                "severity": "error",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Track width {check_width}mm below advanced minimum ({LIMITS_ADV['min_track_width']}mm)",
                "description": f"Track width {check_width}mm is below the advanced process minimum of {LIMITS_ADV['min_track_width']}mm, requiring a challenging fab tier.",
                "components": [],
                "nets": [],
                "pins": [],
                "recommendation": f"Track width {check_width}mm is below advanced process minimum ({LIMITS_ADV['min_track_width']}mm)",
                "report_context": {"section": "DFM", "impact": "manufacturability", "standard_ref": ""},
            })
        elif check_width < LIMITS_STD["min_track_width"]:
            violations.append({
                "parameter": "track_width",
                "actual_mm": check_width,
                "standard_limit_mm": LIMITS_STD["min_track_width"],
                "advanced_limit_mm": LIMITS_ADV["min_track_width"],
                "tier_required": "advanced",
                "message": f"Track width {check_width}mm requires advanced "
                           f"process (standard minimum: "
                           f"{LIMITS_STD['min_track_width']}mm)",
                "detector": "analyze_dfm",
                "rule_id": "DFM-001",
                "category": "dfm",
                "severity": "warning",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Track width {check_width}mm requires advanced process (standard: {LIMITS_STD['min_track_width']}mm)",
                "description": f"Track width {check_width}mm is below the standard process minimum of {LIMITS_STD['min_track_width']}mm, requiring an advanced fab tier.",
                "components": [],
                "nets": [],
                "pins": [],
                "recommendation": f"Track width {check_width}mm requires advanced process (standard minimum: {LIMITS_STD['min_track_width']}mm)",
                "report_context": {"section": "DFM", "impact": "manufacturability", "standard_ref": ""},
            })
    return violations


def _measure_track_spacing(tracks: dict) -> dict:
    # --- Track spacing analysis (approximate from segment proximity) ---
    # Build spatial grid to find close tracks on the same layer
    segments = tracks.get("segments", [])
    min_spacing = float("inf")
    if len(segments) > 1:
        # Sample endpoints and check distances between different-net segments on same layer
        # Group by layer for efficiency
        layer_segs: dict[str, list] = {}
        for seg in segments:
            layer_segs.setdefault(seg["layer"], []).append(seg)

        for layer, segs in layer_segs.items():
            if len(segs) < 2:
                continue
            # For large designs, limit sampling to keep runtime reasonable
            sample = segs if len(segs) <= 2000 else segs[:2000]
            for i in range(len(sample)):
                si = sample[i]
                for j in range(i + 1, min(i + 50, len(sample))):
                    sj = sample[j]
                    if si["net"] == sj["net"] or si["net"] == 0 or sj["net"] == 0:
                        continue
                    # Check endpoint-to-segment distance (simplified: endpoint-to-endpoint)
                    for (x1, y1) in [(si["x1"], si["y1"]), (si["x2"], si["y2"])]:
                        for (x2, y2) in [(sj["x1"], sj["y1"]), (sj["x2"], sj["y2"])]:
                            center_dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
                            # Edge-to-edge spacing = center distance - half widths
                            spacing = center_dist - (si["width"] + sj["width"]) / 2.0
                            if 0 <= spacing < min_spacing:
                                min_spacing = spacing
    return {"min_spacing": min_spacing}


def _emit_track_spacing_violations(m: dict, limits_std: dict, limits_adv: dict) -> list[dict]:
    LIMITS_STD = limits_std
    LIMITS_ADV = limits_adv
    violations = []
    min_spacing = m["min_spacing"]
    if min_spacing < float("inf"):
        if min_spacing < LIMITS_ADV["min_track_spacing"]:
            violations.append({
                "parameter": "track_spacing",
                "actual_mm": round(min_spacing, 4),
                "standard_limit_mm": LIMITS_STD["min_track_spacing"],
                "advanced_limit_mm": LIMITS_ADV["min_track_spacing"],
                "tier_required": "challenging",
                "message": f"Approximate track spacing {round(min_spacing, 4)}mm is below "
                           f"advanced process minimum ({LIMITS_ADV['min_track_spacing']}mm)",
                "note": "Spacing is approximate (endpoint-to-endpoint, not full segment geometry)",
                "detector": "analyze_dfm",
                "rule_id": "DFM-001",
                "category": "dfm",
                "severity": "error",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Track spacing {round(min_spacing, 4)}mm below advanced minimum ({LIMITS_ADV['min_track_spacing']}mm)",
                "description": f"Approximate track spacing {round(min_spacing, 4)}mm is below the advanced process minimum of {LIMITS_ADV['min_track_spacing']}mm.",
                "components": [],
                "nets": [],
                "pins": [],
                "recommendation": f"Approximate track spacing {round(min_spacing, 4)}mm is below advanced process minimum ({LIMITS_ADV['min_track_spacing']}mm)",
                "report_context": {"section": "DFM", "impact": "manufacturability", "standard_ref": ""},
            })
        elif min_spacing < LIMITS_STD["min_track_spacing"]:
            violations.append({
                "parameter": "track_spacing",
                "actual_mm": round(min_spacing, 4),
                "standard_limit_mm": LIMITS_STD["min_track_spacing"],
                "advanced_limit_mm": LIMITS_ADV["min_track_spacing"],
                "tier_required": "advanced",
                "message": f"Approximate track spacing {round(min_spacing, 4)}mm requires "
                           f"advanced process (standard: {LIMITS_STD['min_track_spacing']}mm)",
                "note": "Spacing is approximate (endpoint-to-endpoint, not full segment geometry)",
                "detector": "analyze_dfm",
                "rule_id": "DFM-001",
                "category": "dfm",
                "severity": "warning",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Track spacing {round(min_spacing, 4)}mm requires advanced process (standard: {LIMITS_STD['min_track_spacing']}mm)",
                "description": f"Approximate track spacing {round(min_spacing, 4)}mm requires an advanced fab tier (standard minimum: {LIMITS_STD['min_track_spacing']}mm).",
                "components": [],
                "nets": [],
                "pins": [],
                "recommendation": f"Approximate track spacing {round(min_spacing, 4)}mm requires advanced process (standard: {LIMITS_STD['min_track_spacing']}mm)",
                "report_context": {"section": "DFM", "impact": "manufacturability", "standard_ref": ""},
            })
    return violations


def _measure_drills(vias: dict, footprints: list[dict]) -> dict:
    # --- Drill analysis (via drills + footprint pad drills, KH-383) ---
    all_vias = vias.get("vias", [])
    via_drills = [v["drill"] for v in all_vias if _is_real_drill(v.get("drill", 0))]
    min_drill, drill_source = _min_drill_with_source(via_drills, footprints)
    label = None
    pad_ref = None
    ref_suffix = None
    if min_drill is not None:
        # A pad-sourced minimum is reported generically ("Drill") rather than
        # "Via drill" — the smallest drilled hole isn't necessarily a via.
        label = "Via drill" if drill_source == "via" else "Drill"
        # KH-412: attribute pad-sourced violations to their pad (parameter +
        # the ref in the message) instead of mislabeling them "via_drill".
        pad_ref = drill_source[4:] if drill_source.startswith("pad ") else ""
        ref_suffix = f" on {pad_ref}" if pad_ref else ""
    return {"all_vias": all_vias, "via_drills": via_drills, "min_drill": min_drill,
            "drill_source": drill_source, "label": label, "pad_ref": pad_ref,
            "ref_suffix": ref_suffix}


def _emit_drill_violations(m: dict, limits_std: dict, limits_adv: dict) -> list[dict]:
    LIMITS_STD = limits_std
    LIMITS_ADV = limits_adv
    violations = []
    min_drill = m["min_drill"]
    drill_source = m["drill_source"]
    label = m["label"]
    ref_suffix = m["ref_suffix"]
    if min_drill is not None:
        if min_drill < LIMITS_ADV["min_drill"]:
            violations.append({
                "parameter": "via_drill" if drill_source == "via" else "pad_drill",
                "actual_mm": min_drill,
                "standard_limit_mm": LIMITS_STD["min_drill"],
                "advanced_limit_mm": LIMITS_ADV["min_drill"],
                "tier_required": "challenging",
                "message": f"{label} {min_drill}mm{ref_suffix} is below advanced process "
                           f"minimum ({LIMITS_ADV['min_drill']}mm)",
                "detector": "analyze_dfm",
                "rule_id": "DFM-001",
                "category": "dfm",
                "severity": "error",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"{label} {min_drill}mm below advanced minimum ({LIMITS_ADV['min_drill']}mm)",
                "description": f"{label} {min_drill}mm{ref_suffix} is below the advanced process minimum of {LIMITS_ADV['min_drill']}mm, requiring a challenging fab tier.",
                "components": [],
                "nets": [],
                "pins": [],
                "recommendation": f"{label} {min_drill}mm is below advanced process minimum ({LIMITS_ADV['min_drill']}mm)",
                "report_context": {"section": "DFM", "impact": "manufacturability", "standard_ref": ""},
            })
        elif min_drill < LIMITS_STD["min_drill"]:
            violations.append({
                "parameter": "via_drill" if drill_source == "via" else "pad_drill",
                "actual_mm": min_drill,
                "standard_limit_mm": LIMITS_STD["min_drill"],
                "advanced_limit_mm": LIMITS_ADV["min_drill"],
                "tier_required": "advanced",
                "message": f"{label} {min_drill}mm{ref_suffix} requires advanced process "
                           f"(standard: {LIMITS_STD['min_drill']}mm)",
                "detector": "analyze_dfm",
                "rule_id": "DFM-001",
                "category": "dfm",
                "severity": "warning",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"{label} {min_drill}mm requires advanced process (standard: {LIMITS_STD['min_drill']}mm)",
                "description": f"{label} {min_drill}mm{ref_suffix} is below the standard process minimum of {LIMITS_STD['min_drill']}mm, requiring an advanced fab tier.",
                "components": [],
                "nets": [],
                "pins": [],
                "recommendation": f"{label} {min_drill}mm requires advanced process (standard: {LIMITS_STD['min_drill']}mm)",
                "report_context": {"section": "DFM", "impact": "manufacturability", "standard_ref": ""},
            })
    return violations


def _measure_annular_rings(all_vias: list[dict]) -> dict:
    # --- Annular ring analysis ---
    rings = []
    min_ring = None
    if all_vias:
        for v in all_vias:
            size = v.get("size", 0)
            drill = v.get("drill", 0)
            if size > 0 and drill > 0:
                rings.append(round((size - drill) / 2.0, 3))
        if rings:
            min_ring = min(rings)
    return {"rings": rings, "min_ring": min_ring}


def _emit_annular_ring_violations(m: dict, limits_std: dict, limits_adv: dict) -> list[dict]:
    LIMITS_STD = limits_std
    LIMITS_ADV = limits_adv
    violations = []
    rings = m["rings"]
    min_ring = m["min_ring"]
    if rings:
        if min_ring < LIMITS_ADV["min_annular_ring"]:
            violations.append({
                "parameter": "annular_ring",
                "actual_mm": min_ring,
                "standard_limit_mm": LIMITS_STD["min_annular_ring"],
                "advanced_limit_mm": LIMITS_ADV["min_annular_ring"],
                "tier_required": "challenging",
                "message": f"Annular ring {min_ring}mm is below advanced process "
                           f"minimum ({LIMITS_ADV['min_annular_ring']}mm)",
                "detector": "analyze_dfm",
                "rule_id": "DFM-001",
                "category": "dfm",
                "severity": "error",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Annular ring {min_ring}mm below advanced minimum ({LIMITS_ADV['min_annular_ring']}mm)",
                "description": f"Annular ring {min_ring}mm is below the advanced process minimum of {LIMITS_ADV['min_annular_ring']}mm, requiring a challenging fab tier.",
                "components": [],
                "nets": [],
                "pins": [],
                "recommendation": f"Annular ring {min_ring}mm is below advanced process minimum ({LIMITS_ADV['min_annular_ring']}mm)",
                "report_context": {"section": "DFM", "impact": "manufacturability", "standard_ref": ""},
            })
        elif min_ring < LIMITS_STD["min_annular_ring"]:
            violations.append({
                "parameter": "annular_ring",
                "actual_mm": min_ring,
                "standard_limit_mm": LIMITS_STD["min_annular_ring"],
                "advanced_limit_mm": LIMITS_ADV["min_annular_ring"],
                "tier_required": "advanced",
                "message": f"Annular ring {min_ring}mm requires advanced process "
                           f"(standard: {LIMITS_STD['min_annular_ring']}mm)",
                "detector": "analyze_dfm",
                "rule_id": "DFM-001",
                "category": "dfm",
                "severity": "warning",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Annular ring {min_ring}mm requires advanced process (standard: {LIMITS_STD['min_annular_ring']}mm)",
                "description": f"Annular ring {min_ring}mm is below the standard process minimum of {LIMITS_STD['min_annular_ring']}mm, requiring an advanced fab tier.",
                "components": [],
                "nets": [],
                "pins": [],
                "recommendation": f"Annular ring {min_ring}mm requires advanced process (standard: {LIMITS_STD['min_annular_ring']}mm)",
                "report_context": {"section": "DFM", "impact": "manufacturability", "standard_ref": ""},
            })
    return violations


def _emit_ipc_class_violations(m_rings: dict, m_drills: dict, ipc_class: int,
                               ipc_limits: dict) -> list[dict]:
    rings = m_rings["rings"]
    min_ring = m_rings["min_ring"]
    all_vias = m_drills["all_vias"]
    # --- IPC class annular ring compliance ---
    ipc_violations = []
    if rings:
        ipc_min_via = ipc_limits['min_annular_ring_via']
        if min_ring < ipc_min_via:
            ipc_violations.append({
                'parameter': 'annular_ring_via',
                'actual_mm': min_ring,
                'class_minimum_mm': ipc_min_via,
                'ipc_class': ipc_class,
                'message': (f'Via annular ring {min_ring}mm below '
                            f'IPC Class {ipc_class} minimum '
                            f'{ipc_min_via}mm'),
                "detector": "analyze_dfm",
                "rule_id": "DFM-002",
                "category": "dfm",
                "severity": "warning",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Via annular ring {min_ring}mm below IPC Class {ipc_class} minimum {ipc_min_via}mm",
                "description": f"Via annular ring {min_ring}mm does not meet IPC Class {ipc_class} minimum of {ipc_min_via}mm.",
                "components": [],
                "nets": [],
                "pins": [],
                "recommendation": f"Increase via annular ring to at least {ipc_min_via}mm to meet IPC Class {ipc_class} requirements",
                "report_context": {"section": "DFM", "impact": "compliance", "standard_ref": f"IPC-6012 Class {ipc_class}"},
            })

    # Class 3: check for breakout (annular ring <= 0 means breakout)
    if ipc_class == 3 and rings:
        breakout_count = sum(1 for r in rings if r <= 0.001)
        if breakout_count > 0:
            ipc_violations.append({
                'parameter': 'annular_ring_breakout',
                'count': breakout_count,
                'ipc_class': 3,
                'message': (f'{breakout_count} vias with annular ring '
                            f'breakout — not allowed for IPC Class 3'),
                "detector": "analyze_dfm",
                "rule_id": "DFM-002",
                "category": "dfm",
                "severity": "warning",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"{breakout_count} vias with annular ring breakout (IPC Class 3 violation)",
                "description": f"{breakout_count} vias have annular ring breakout, which is not allowed for IPC Class 3.",
                "components": [],
                "nets": [],
                "pins": [],
                "recommendation": "Increase via annular ring to eliminate breakout for IPC Class 3 compliance",
                "report_context": {"section": "DFM", "impact": "compliance", "standard_ref": "IPC-6012 Class 3"},
            })

    # Class 3: via-in-pad fill requirement
    if ipc_class == 3 and ipc_limits.get('via_in_pad_fill_required'):
        vip_vias = [v for v in all_vias if v.get('in_pad', False)]
        if vip_vias:
            ipc_violations.append({
                'parameter': 'via_in_pad_fill',
                'count': len(vip_vias),
                'ipc_class': 3,
                'message': (f'{len(vip_vias)} via-in-pad instances — '
                            f'IPC Class 3 requires filled and '
                            f'plated-over via-in-pad'),
                "detector": "analyze_dfm",
                "rule_id": "DFM-002",
                "category": "dfm",
                "severity": "warning",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"{len(vip_vias)} via-in-pad instances require fill for IPC Class 3",
                "description": f"{len(vip_vias)} via-in-pad instances detected; IPC Class 3 requires filled and plated-over via-in-pad.",
                "components": [],
                "nets": [],
                "pins": [],
                "recommendation": "Ensure via-in-pad instances are filled and plated-over for IPC Class 3 compliance",
                "report_context": {"section": "DFM", "impact": "compliance", "standard_ref": "IPC-6012 Class 3"},
            })
    return ipc_violations


def _measure_board_size(board_outline: dict) -> dict:
    # --- Board dimensions assessment ---
    bbox = board_outline.get("bounding_box")
    width = None
    height = None
    if bbox:
        width = bbox.get("width", 0)
        height = bbox.get("height", 0)
    return {"bbox": bbox, "width": width, "height": height}


def _emit_board_size_findings(m: dict, limits_std: dict) -> list[dict]:
    LIMITS_STD = limits_std
    violations = []
    bbox = m["bbox"]
    width = m["width"]
    height = m["height"]
    if bbox:
        if width > LIMITS_STD["max_board_width"] or height > LIMITS_STD["max_board_height"]:
            violations.append({
                "parameter": "board_size",
                "actual_mm": [width, height],
                "threshold_mm": [LIMITS_STD["max_board_width"],
                                 LIMITS_STD["max_board_height"]],
                "tier_required": "standard",
                "message": f"Board size {width}x{height}mm exceeds 100x100mm — "
                           f"higher fabrication pricing tier at JLCPCB",
                "detector": "analyze_dfm",
                "rule_id": "DFM-001",
                "category": "dfm",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Board size {width}x{height}mm exceeds 100x100mm pricing threshold",
                "description": f"Board size {width}x{height}mm exceeds the 100x100mm threshold, resulting in higher fabrication pricing at JLCPCB.",
                "components": [],
                "nets": [],
                "pins": [],
                "recommendation": f"Board size {width}x{height}mm exceeds 100x100mm — higher fabrication pricing tier at JLCPCB",
                "report_context": {"section": "DFM", "impact": "cost", "standard_ref": ""},
            })

        if width < LIMITS_STD["min_board_dim"] and height < LIMITS_STD["min_board_dim"]:
            violations.append({
                "parameter": "board_size_small",
                "actual_mm": [width, height],
                "threshold_mm": LIMITS_STD["min_board_dim"],
                "tier_required": "standard",
                "message": f"Board size {width}x{height}mm is very small — "
                           f"may have handling concerns during fabrication",
                "detector": "analyze_dfm",
                "rule_id": "DFM-001",
                "category": "dfm",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Board size {width}x{height}mm is very small — handling concerns",
                "description": f"Board size {width}x{height}mm is below the minimum dimension threshold, which may cause handling issues during fabrication.",
                "components": [],
                "nets": [],
                "pins": [],
                "recommendation": f"Board size {width}x{height}mm is very small — may have handling concerns during fabrication",
                "report_context": {"section": "DFM", "impact": "manufacturability", "standard_ref": ""},
            })
    return violations


def _dfm_tier(violations: list[dict]) -> str:
    # --- Determine overall DFM tier ---
    tier = "standard"
    for v in violations:
        req = v.get("tier_required", "standard")
        if req == "challenging":
            tier = "challenging"
            break
        elif req == "advanced" and tier != "challenging":
            tier = "advanced"
    return tier


def analyze_dfm(footprints: list[dict], tracks: dict, vias: dict,
                board_outline: dict, design_rules: dict | None = None,
                net_classes: list[dict] | None = None,
                design_intent: dict | None = None) -> dict:
    """Design for Manufacturing scoring against common fab capabilities.

    Compares actual design parameters against JLCPCB standard and advanced
    process limits. Reports a DFM tier ("standard", "advanced", or
    "challenging"), all violations with actual vs limit values, and key
    manufacturing metrics.

    Args:
        footprints: Extracted footprint list.
        tracks: Extracted track data (with segments, arcs, width_distribution).
        vias: Extracted via data.
        board_outline: Board outline with bounding_box.
        design_rules: Optional design rules from setup extraction.
        net_classes: Optional net class definitions for class-aware DFM checks.
        design_intent: Optional resolved design intent (product_class, ipc_class,
            etc.) for intent-aware limit selection.
    """
    # EQ-049: d = √(Δx²+Δy²) (DFM clearance measurement)
    LIMITS_STD = JLCPCB_LIMITS_STANDARD
    LIMITS_ADV = JLCPCB_LIMITS_ADVANCED

    # Determine active IPC class
    ipc_class = 2  # default
    if design_intent and design_intent.get('ipc_class') in (1, 2, 3):
        ipc_class = design_intent['ipc_class']
    ipc_limits = IPC_CLASS_LIMITS[ipc_class]

    _net_class_lookup = _build_net_class_lookup(net_classes)

    violations = []
    metrics: dict = {}

    m_widths = _measure_track_widths(tracks, _net_class_lookup)
    m_spacing = _measure_track_spacing(tracks)
    m_drills = _measure_drills(vias, footprints)
    m_rings = _measure_annular_rings(m_drills["all_vias"])
    m_board = _measure_board_size(board_outline)

    if m_widths["all_widths"]:
        metrics["min_track_width_mm"] = m_widths["min_width"]
    if m_spacing["min_spacing"] < float("inf"):
        metrics["approx_min_spacing_mm"] = round(m_spacing["min_spacing"], 4)
    if m_drills["min_drill"] is not None:
        metrics["min_drill_mm"] = m_drills["min_drill"]
    if m_rings["rings"]:
        metrics["min_annular_ring_mm"] = m_rings["min_ring"]
    if m_board["bbox"]:
        metrics["board_width_mm"] = m_board["width"]
        metrics["board_height_mm"] = m_board["height"]

    violations.extend(_emit_track_width_violations(m_widths, LIMITS_STD, LIMITS_ADV))
    violations.extend(_emit_track_spacing_violations(m_spacing, LIMITS_STD, LIMITS_ADV))
    violations.extend(_emit_drill_violations(m_drills, LIMITS_STD, LIMITS_ADV))
    violations.extend(_emit_annular_ring_violations(m_rings, LIMITS_STD, LIMITS_ADV))
    ipc_violations = _emit_ipc_class_violations(m_rings, m_drills, ipc_class, ipc_limits)
    violations.extend(_emit_board_size_findings(m_board, LIMITS_STD))

    tier = _dfm_tier(violations)

    result: dict = {
        "dfm_tier": tier,
        "metrics": metrics,
    }
    if violations:
        result["violations"] = violations
        result["violation_count"] = len(violations)
    else:
        result["violation_count"] = 0

    if ipc_violations:
        result['ipc_class_compliance'] = {
            'detected_class': ipc_class,
            'detection_source': (design_intent or {}).get(
                'source', {}).get('ipc_class', 'default'),
            'violations': ipc_violations,
        }
    elif ipc_class != 2:  # Report class even if no violations
        result['ipc_class_compliance'] = {
            'detected_class': ipc_class,
            'detection_source': (design_intent or {}).get(
                'source', {}).get('ipc_class', 'default'),
            'violations': [],
        }

    return result


def analyze_design_rule_compliance(
    tracks: dict, vias: dict,
    project_settings: dict,
    footprints: list[dict] | None = None,
) -> dict | None:
    """Check layout against project-defined design rules.

    Compares actual track widths, via sizes, and drill diameters against
    the designer's own rules from ``.kicad_pro`` (global minimums) and
    ``.kicad_dru`` (per-context constraints).  Returns None if no
    project rules are available.

    This is separate from DFM analysis — DFM checks fab capabilities
    (can this be manufactured?), while this checks design intent
    (did I follow my own rules?).

    ``footprints`` (KH-383) lets the min-drill check also see
    thru_hole/np_thru_hole pad drills, not just board vias — optional so
    existing callers keep working unchanged.
    """
    design_rules = project_settings.get('design_rules', {})
    custom_rules = project_settings.get('custom_rules', [])
    net_classes = project_settings.get('net_classes', [])

    if not design_rules and not custom_rules and not net_classes:
        return None

    violations = []
    rules_checked = 0

    # --- Compute actual layout metrics ---
    all_widths = []
    for seg in tracks.get("segments", []):
        all_widths.append(seg["width"])
    for arc in tracks.get("arcs", []):
        all_widths.append(arc["width"])
    min_track_width = min(all_widths) if all_widths else None

    all_vias = vias.get("vias", [])
    via_diameters = [v["size"] for v in all_vias if v.get("size", 0) > 0]
    via_drills = [v["drill"] for v in all_vias if _is_real_drill(v.get("drill", 0))]
    min_via_diameter = min(via_diameters) if via_diameters else None
    # KH-383: the smallest drilled hole may be a footprint pad, not a via.
    min_drill, drill_source = _min_drill_with_source(via_drills, footprints)

    # --- Check .kicad_pro global minimums ---
    checks = [
        ('min_track_width', min_track_width, design_rules.get('min_track_width')),
        ('min_via_diameter', min_via_diameter, design_rules.get('min_via_diameter')),
        ('min_via_drill', min_drill,
         design_rules.get('min_through_hole_diameter')
         or design_rules.get('min_via_drill')),
    ]
    for rule_name, actual, required in checks:
        if actual is None or required is None:
            continue
        rules_checked += 1
        if actual < required - 0.001:  # 1µm tolerance for float comparison
            message = (f"{rule_name.replace('_', ' ').title()} "
                       f"{actual:.3f}mm violates project minimum "
                       f"({required:.3f}mm)")
            if rule_name == 'min_via_drill' and drill_source.startswith('pad '):
                message += (f" (smallest: pad drill {actual:.3f}mm on "
                            f"{drill_source[4:]})")
            v = {
                'rule': rule_name,
                'source': 'project',
                'required_mm': round(required, 4),
                'actual_mm': round(actual, 4),
                'message': message,
                # KH-412: attribute a pad-sourced min_via_drill minimum to its pad.
                'drill_source': ('pad' if rule_name == 'min_via_drill' and drill_source.startswith('pad ')
                                 else 'via') if rule_name == 'min_via_drill' else None,
            }
            if v['drill_source'] is None:
                del v['drill_source']
            elif v['drill_source'] == 'pad':
                v['source_ref'] = drill_source[4:]
            violations.append(v)

    # --- Net class summary (informational) ---
    net_class_summary = []
    for nc in net_classes:
        name = nc.get('name', '')
        if not name or name == 'Default':
            continue
        entry = {'name': name}
        if nc.get('track_width') is not None:
            entry['track_width_mm'] = nc['track_width']
        if nc.get('clearance') is not None:
            entry['clearance_mm'] = nc['clearance']
        if nc.get('diff_pair_width') is not None:
            entry['diff_pair_width_mm'] = nc['diff_pair_width']
        if nc.get('diff_pair_gap') is not None:
            entry['diff_pair_gap_mm'] = nc['diff_pair_gap']
        nets = nc.get('nets', [])
        if nets:
            entry['nets_matched'] = len(nets)
        net_class_summary.append(entry)

    # --- Net class compliance validation ---
    # Check that traces on nets in each class meet class constraints
    net_class_violations = []
    if net_classes:
        # Build net name -> class lookup
        nc_by_net: dict[str, dict] = {}
        for nc in net_classes:
            nc_name = nc.get('name', '')
            if nc_name == 'Default':
                continue
            for net_name in nc.get('nets', []):
                nc_by_net[net_name] = nc

        # Check trace widths per net class
        for seg in tracks.get('segments', []):
            net_name = seg.get('net_name', '')
            nc = nc_by_net.get(net_name)
            if not nc:
                continue
            required_width = nc.get('track_width')
            if required_width is None:
                continue
            actual_width = seg['width']
            if actual_width < required_width - 0.001:
                net_class_violations.append({
                    'net_class': nc['name'],
                    'parameter': 'trace_width',
                    'net': net_name,
                    'actual_mm': round(actual_width, 4),
                    'class_minimum_mm': round(required_width, 4),
                    'message': (f'Trace on {net_name} is '
                                f'{actual_width:.3f}mm, net class '
                                f'{nc["name"]} requires '
                                f'{required_width:.3f}mm'),
                })

        # Check via sizes per net class
        for v in vias.get('vias', []):
            net_name = v.get('net_name', '')
            nc = nc_by_net.get(net_name)
            if not nc:
                continue
            required_dia = nc.get('via_diameter')
            if required_dia is not None:
                actual_dia = v.get('size', 0)
                if actual_dia > 0 and actual_dia < required_dia - 0.001:
                    net_class_violations.append({
                        'net_class': nc['name'],
                        'parameter': 'via_diameter',
                        'net': net_name,
                        'actual_mm': round(actual_dia, 4),
                        'class_minimum_mm': round(required_dia, 4),
                        'message': (f'Via on {net_name} is '
                                    f'{actual_dia:.3f}mm, net class '
                                    f'{nc["name"]} requires '
                                    f'{required_dia:.3f}mm'),
                    })

    # Deduplicate: keep one violation per (net_class, parameter, net)
    seen_nc_violations: set[tuple] = set()
    unique_nc_violations = []
    for v in net_class_violations:
        key = (v['net_class'], v['parameter'], v['net'])
        if key not in seen_nc_violations:
            seen_nc_violations.add(key)
            unique_nc_violations.append(v)
            rules_checked += 1
            violations.append({
                'rule': f"net_class:{v['net_class']}:{v['parameter']}",
                'source': 'net_class',
                'required_mm': v['class_minimum_mm'],
                'actual_mm': v['actual_mm'],
                'message': v['message'],
            })

    # --- Custom rules summary (advisory) ---
    # We don't evaluate condition expressions, so conditional rules are
    # skipped entirely rather than applied as board-wide minimums
    # (KH-361) — only unconditional global constraints from .kicad_dru
    # are checked.
    conditional_rules_skipped = []
    if custom_rules:
        for rule in custom_rules:
            if rule.get('condition'):
                conditional_rules_skipped.append(rule.get('name', ''))
                continue
            for constraint in rule.get('constraints', []):
                ctype = constraint.get('type', '')
                cmin = constraint.get('min')
                if cmin is None:
                    continue
                if not isinstance(cmin, (int, float)):
                    continue

                # Only check constraints we can verify globally
                actual = None
                if ctype == 'track_width' and min_track_width is not None:
                    actual = min_track_width
                elif ctype == 'hole_size' and min_drill is not None:
                    actual = min_drill
                elif ctype == 'annular_width':
                    # Compute from via data
                    if all_vias:
                        rings = [(v.get("size", 0) - v.get("drill", 0)) / 2.0
                                 for v in all_vias
                                 if v.get("size", 0) > 0 and v.get("drill", 0) > 0]
                        if rings:
                            actual = min(rings)

                if actual is not None:
                    rules_checked += 1
                    if actual < cmin - 0.001:
                        v = {
                            'rule': f"custom:{rule.get('name', ctype)}",
                            'source': 'kicad_dru',
                            'required_mm': round(cmin, 4),
                            'actual_mm': round(actual, 4),
                            'constraint_type': ctype,
                            'message': (f"Custom rule \"{rule.get('name', '')}\" "
                                        f"requires {ctype} >= {cmin:.3f}mm, "
                                        f"actual {actual:.3f}mm"),
                            # KH-412: attribute a pad-sourced hole_size minimum to its pad.
                            'drill_source': ('pad' if ctype == 'hole_size' and drill_source.startswith('pad ')
                                             else 'via') if ctype == 'hole_size' else None,
                        }
                        if v['drill_source'] is None:
                            del v['drill_source']
                        elif v['drill_source'] == 'pad':
                            v['source_ref'] = drill_source[4:]
                        violations.append(v)

    result: dict = {
        'compliant': len(violations) == 0,
        'rules_checked': rules_checked,
    }
    if project_settings.get('source'):
        result['rules_source'] = project_settings['source']
    if violations:
        result['violations'] = violations
    if net_class_summary:
        result['net_class_summary'] = net_class_summary
    if unique_nc_violations:
        result['net_class_violations'] = unique_nc_violations
    if custom_rules:
        result['custom_rules_count'] = len(custom_rules)
    if conditional_rules_skipped:
        skipped_sorted = sorted(conditional_rules_skipped)
        result['conditional_rules_skipped'] = skipped_sorted
        result['conditional_rules_skipped_count'] = len(skipped_sorted)
        rule_word = "rule" if len(skipped_sorted) == 1 else "rules"
        result['conditional_rules_note'] = (
            f"{len(skipped_sorted)} conditional {rule_word} not evaluated "
            f"(condition support: none) — not applied board-wide")

    return result
