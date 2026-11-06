"""PCB copper checks: via analysis, thermal vias and thermal-pad vias, copper presence,
via-in-pad, board-edge via clearance. Verbatim moves from analyze_pcb.py."""

import math
import re

from kicad_core.netnames import is_ground_name
from pcb.dfm import _degenerate_drills, _is_real_drill, _pad_drills
from pcb.geometry import ZoneFills, _pad_sample_points, _point_in_pad, copper_connected


def _find_thermal_pads(fp: dict) -> list[dict]:
    """Identify thermal/exposed pads on a footprint.

    Returns list of pad dicts that are likely thermal pads —
    large center pads on power/ground nets, typical of QFN/BGA packages.
    """
    pads = fp.get("pads", [])
    if len(pads) < 3:
        return []

    # Calculate SMD pad area statistics (skip paste-only pads)
    pad_areas: list[tuple[dict, float]] = []
    for p in pads:
        if p.get("type") != "smd":
            continue
        pad_layers = p.get("layers", [])
        if not any(l.endswith(".Cu") or l == "*.Cu" for l in pad_layers):
            continue
        w = p.get("width", p.get("size_x", 0))
        h = p.get("height", p.get("size_y", 0))
        area = w * h
        if area > 0:
            pad_areas.append((p, area))

    if not pad_areas:
        return []

    avg_area = sum(a for _, a in pad_areas) / len(pad_areas)
    all_areas_sorted = sorted(a for _, a in pad_areas)
    median_area = all_areas_sorted[len(all_areas_sorted) // 2]

    thermal = []
    for p, area in pad_areas:
        pad_num = str(p.get("number", ""))
        is_ep = pad_num in ("0", "EP", "")

        # DFN/QFN variants use highest-numbered pad as EP — detect by
        # area ratio (pad >= 3x the median signal pad area)
        if not is_ep and median_area > 0:
            other_areas = sorted(a for pad, a in pad_areas
                                 if str(pad.get("number", "")) != pad_num)
            if other_areas:
                median_signal = other_areas[len(other_areas) // 2]
                if median_signal > 0 and area >= median_signal * 3.0:
                    is_ep = True

        # Thermal pad: explicitly named EP/0 with area >= 2mm²,
        # or any pad with area > 6mm² (large enough to need thermal vias)
        if not ((is_ep and area >= 2.0) or area > 6.0):
            continue

        # Must be at least 2x the average pad area
        if avg_area > 0 and area < avg_area * 2.0:
            continue

        # Must have a net — structural/shield pads with no net are not thermal
        net_name = p.get("net_name", "")
        pad_net_num = p.get("net_number", -1)
        if not net_name or pad_net_num <= 0:
            continue

        # Must be on a ground or power net (thermal pads dissipate heat)
        net_upper = net_name.upper()
        is_power_or_gnd = (
            net_upper in ("GND", "VSS", "AGND", "DGND", "PGND", "VCC", "VDD",
                          "AVCC", "AVDD", "DVCC", "DVDD", "VBUS")
            or net_upper.startswith("+")
            or net_upper.startswith("V+")
            or "GND" in net_upper
            or "VCC" in net_upper
            or "VDD" in net_upper
        )
        if not is_power_or_gnd and not is_ep:
            continue

        thermal.append(p)

    return thermal


def analyze_thermal_vias(footprints: list[dict], vias: dict,
                         zones: list[dict]) -> dict:
    """Provide facts for thermal analysis — via stitching, thermal pads, via-in-pad.

    Reports:
    - Via density per zone (stitching vias for thermal/ground plane connectivity)
    - Exposed/thermal pad detection on QFN/BGA packages (pad connected to ground)
    - Via clusters near thermal pads (thermal via arrays)
    - Overall via distribution across layers
    """
    # EQ-055: density = count / area_cm² (thermal via density)
    zone_vias: dict[int, dict] = {}  # net_num -> via stats within zone
    # For each zone, count vias on the same net within the zone outline
    # (approximate: use bounding box of zone outline)
    zone_bounds: list[dict] = []
    for z in zones:
        zn = z.get("net", 0)
        if zn <= 0:
            continue
        # Use the outline_area as a proxy — if we had the actual outline
        # points we could do point-in-polygon, but for a first pass,
        # just count all vias on the same net
        zone_bounds.append({
            "net": zn,
            "net_name": z.get("net_name", ""),
            "layers": z.get("layers", []),
            "area_mm2": z.get("outline_area_mm2", 0),
            "filled_area_mm2": z.get("filled_area_mm2"),
        })

    # Count vias per net
    via_by_net: dict[int, list[dict]] = {}
    for via in vias.get("vias", []):
        net = via.get("net", 0)
        if net > 0:
            via_by_net.setdefault(net, []).append(via)

    # Aggregate zone polygons by net before computing stitching density
    net_zones: dict[int, dict] = {}
    for zb in zone_bounds:
        net = zb["net"]
        if net not in net_zones:
            net_zones[net] = {
                "net_name": zb["net_name"],
                "layers": set(),
                "total_area_mm2": 0,
            }
        net_zones[net]["layers"].update(zb["layers"])
        net_zones[net]["total_area_mm2"] += zb.get("area_mm2", 0)

    # Zone stitching analysis — one entry per net
    stitching = []
    for net, info in net_zones.items():
        net_vias = via_by_net.get(net, [])
        if not net_vias:
            continue
        area = info["total_area_mm2"]

        entry = {
            "net": info["net_name"],
            "zone_layers": sorted(info["layers"]),
            "zone_area_mm2": round(area, 1) if area else None,
            "via_count": len(net_vias),
        }
        if area > 0:
            entry["via_density_per_cm2"] = round(len(net_vias) / (area / 100.0), 1)

        # Check drill sizes
        drills = set()
        for v in net_vias:
            if v.get("drill"):
                drills.add(v["drill"])
        if drills:
            entry["drill_sizes_mm"] = sorted(drills)

        entry["detector"] = "analyze_thermal_vias"
        entry["rule_id"] = "TS-DET"
        entry["category"] = "thermal"
        entry["severity"] = "info"
        entry["confidence"] = "deterministic"
        entry["evidence_source"] = "topology"
        entry["summary"] = f"Zone stitching: {info['net_name']} {len(net_vias)} vias"
        entry["description"] = (
            f"Zone stitching on net {info['net_name']}: {len(net_vias)} vias "
            f"across layers {sorted(info['layers'])}."
        )
        entry["components"] = []
        entry["nets"] = [info["net_name"]]
        entry["pins"] = []
        entry["recommendation"] = ""
        entry["report_context"] = {
            "section": "Thermal",
            "impact": "Thermal/ground plane connectivity",
            "standard_ref": "",
        }
        stitching.append(entry)

    # Thermal pad detection — use shared helper for QFN/BGA/DFN packages
    thermal_pads = []
    for fp in footprints:
        ref = fp.get("reference", "")

        # Skip component types that don't have thermal pads
        ref_prefix = ""
        for c in ref:
            if c.isalpha():
                ref_prefix += c
            else:
                break
        if ref_prefix in ("BT", "TP", "J"):
            continue

        for pad in _find_thermal_pads(fp):
            pad_num = str(pad.get("number", ""))
            w = pad.get("width", 0)
            h = pad.get("height", 0)
            pad_area = w * h
            net_name = pad.get("net_name", "")

            ax = pad.get("abs_x", fp["x"])
            ay = pad.get("abs_y", fp["y"])

            # Count standalone vias near this thermal pad
            standalone_vias = 0
            for via in vias.get("vias", []):
                if via.get("net") == pad.get("net_number", -1):
                    dx = via["x"] - ax
                    dy = via["y"] - ay
                    if math.sqrt(dx * dx + dy * dy) < max(w, h) * 1.5:
                        standalone_vias += 1

            # Count thru_hole pads in the same footprint on the same
            # net — these are footprint-embedded thermal vias
            footprint_via_pads = 0
            pad_net = pad.get("net_number", -1)
            for other_pad in fp.get("pads", []):
                if other_pad is pad:
                    continue
                if (other_pad.get("type") == "thru_hole" and
                        other_pad.get("net_number", -2) == pad_net and
                        pad_net >= 0):
                    footprint_via_pads += 1

            nearby_vias = standalone_vias + footprint_via_pads
            thermal_pads.append({
                "component": ref,
                "pad": pad_num,
                "pad_size_mm": [round(w, 2), round(h, 2)],
                "pad_area_mm2": round(pad_area, 2),
                "net": net_name,
                "nearby_thermal_vias": nearby_vias,
                "standalone_vias": standalone_vias,
                "footprint_via_pads": footprint_via_pads,
                "layer": fp.get("layer", "F.Cu"),
                "detector": "analyze_thermal_vias",
                "rule_id": "TP-DET",
                "category": "thermal",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Thermal pad: {ref} pad {pad_num} {nearby_vias} nearby vias",
                "description": (
                    f"Thermal pad on {ref} pad {pad_num}: "
                    f"{nearby_vias} nearby vias ({standalone_vias} standalone, "
                    f"{footprint_via_pads} footprint)."
                ),
                "components": [ref],
                "nets": [net_name],
                "pins": [pad_num],
                "recommendation": "",
                "report_context": {
                    "section": "Thermal",
                    "impact": "Thermal dissipation",
                    "standard_ref": "",
                },
            })

    return {
        "zone_stitching": stitching,
        "thermal_pads": thermal_pads,
    }


def analyze_vias(vias: dict, footprints: list[dict],
                 net_names: dict[int, str]) -> dict:
    """Comprehensive via analysis — types, annular ring, via-in-pad, fanout, current.

    Reports:
    - Type breakdown: through-hole vs blind vs micro via counts and distributions
    - Annular ring: (pad_size - drill) / 2 per via, with min/max/distribution
    - Via-in-pad detection: vias located within footprint pad bounding boxes
    - Fanout pattern detection: clusters of vias near BGA/QFN pads
    - Current capacity facts: drill sizes mapped to IPC-2221 approximate ratings
    """
    # EQ-058: area = π(d/2)² (via annular ring)
    all_vias = vias.get("vias", [])
    if not all_vias:
        # KH-412: a via-less board can still have footprint pad drills
        # (including degenerate ones, e.g. HamedMasafi/MeloCar remote_3's
        # `(drill 0.00001)` pads) worth surfacing — don't drop them just
        # because there are no vias to analyze.
        novia_result: dict = {}
        pad_drills = _pad_drills(footprints)
        if pad_drills:
            novia_result["current_capacity"] = {"min_pad_drill_mm": min(pad_drills)}
        dd = _degenerate_drills(footprints, [])
        if dd:
            novia_result["degenerate_drills"] = dd
        return novia_result

    # --- Type breakdown ---
    type_counts: dict[str, int] = {"through": 0, "blind": 0, "buried": 0, "micro": 0}
    type_sizes: dict[str, dict[str, int]] = {
        "through": {}, "blind": {}, "buried": {}, "micro": {},
    }
    for v in all_vias:
        # extract_vias always emits `type` as one of through/blind/buried/micro (KH-318).
        vtype = v["type"]
        if vtype not in type_counts:
            vtype = "through"
        type_counts[vtype] += 1
        key = f"{v['size']}/{v['drill']}"
        type_sizes[vtype][key] = type_sizes[vtype].get(key, 0) + 1

    type_breakdown = {}
    for vtype, count in type_counts.items():
        if count > 0:
            type_breakdown[vtype] = {
                "count": count,
                "size_distribution": type_sizes[vtype],
            }

    # --- Annular ring analysis ---
    rings: list[float] = []
    ring_dist: dict[float, int] = {}
    for v in all_vias:
        size = v.get("size", 0)
        drill = v.get("drill", 0)
        if size > 0 and drill > 0:
            ring = round((size - drill) / 2.0, 3)
            rings.append(ring)
            ring_dist[ring] = ring_dist.get(ring, 0) + 1

    annular_ring: dict = {}
    if rings:
        min_ring = min(rings)
        annular_ring = {
            "min_mm": min_ring,
            "max_mm": max(rings),
            "distribution": {str(k): cnt for k, cnt in sorted(ring_dist.items())},
        }
        # Count vias below common manufacturer minimums
        violations_0125 = sum(1 for r in rings if r < 0.125)
        violations_0100 = sum(1 for r in rings if r < 0.100)
        if violations_0125 > 0:
            annular_ring["below_0.125mm"] = violations_0125
        if violations_0100 > 0:
            annular_ring["below_0.100mm"] = violations_0100

    # --- Via-in-pad detection ---
    # Build spatial index of pads for efficient lookup
    via_in_pad: list[dict] = []
    # Collect all SMD pads with bounding boxes
    pad_boxes: list[dict] = []
    for fp in footprints:
        ref = fp.get("reference", "")
        fp_layer = fp.get("layer", "F.Cu")
        for pad in fp.get("pads", []):
            if pad.get("type") != "smd":
                continue
            ax = pad.get("abs_x")
            ay = pad.get("abs_y")
            pw = pad.get("width", 0)
            ph = pad.get("height", 0)
            if ax is None or ay is None or pw <= 0 or ph <= 0:
                continue
            pad_boxes.append({
                "ref": ref,
                "pad": pad.get("number", ""),
                "cx": ax, "cy": ay,
                "hw": pw / 2.0, "hh": ph / 2.0,
                "net": pad.get("net_number", -1),
                "layer": fp_layer,
                "shape": pad.get("shape", ""),
                "angle": pad.get("angle", 0) or 0,
            })

    for v in all_vias:
        vx, vy = v["x"], v["y"]
        v_net = v.get("net", 0)
        v_layers = v.get("layers", ["F.Cu", "B.Cu"])
        for pb in pad_boxes:
            # Via must be on the same copper layer as the pad
            if pb["layer"] not in v_layers:
                continue
            if _point_in_pad(vx, vy, pb["cx"], pb["cy"], pb["hw"] * 2, pb["hh"] * 2, pb["shape"], pb["angle"]):
                same_net = v_net == pb["net"]
                via_in_pad.append({
                    "component": pb["ref"],
                    "pad": pb["pad"],
                    "via_x": round(vx, 3),
                    "via_y": round(vy, 3),
                    "via_drill": v.get("drill", 0),
                    "same_net": same_net,
                    "via_type": v["type"],
                })
                break  # Each via counted once

    # --- Fanout pattern detection ---
    # BGA/QFN packages with many pads often have fanout vias —
    # clusters of vias immediately outside the component footprint
    fanout_patterns: list[dict] = []
    for fp in footprints:
        pad_count = fp.get("pad_count", 0)
        if pad_count < 16:
            continue  # Only check multi-pad packages
        ref = fp.get("reference", "")
        lib = fp.get("library", "").lower()

        # Determine if this is a BGA/QFN/QFP-like package
        is_area_array = any(kw in lib for kw in
                           ("bga", "qfn", "dfn", "qfp", "lga", "wlcsp",
                            "son", "vson", "tqfp", "lqfp"))
        if not is_area_array and pad_count < 40:
            continue

        # Get component bounding box from courtyard or pad extents
        crtyd = fp.get("courtyard")
        if crtyd:
            cx_min, cy_min = crtyd["min_x"], crtyd["min_y"]
            cx_max, cy_max = crtyd["max_x"], crtyd["max_y"]
        else:
            # Fall back to pad extents
            pxs = [p.get("abs_x", fp["x"]) for p in fp.get("pads", [])]
            pys = [p.get("abs_y", fp["y"]) for p in fp.get("pads", [])]
            if not pxs:
                continue
            margin = 0.5
            cx_min, cx_max = min(pxs) - margin, max(pxs) + margin
            cy_min, cy_max = min(pys) - margin, max(pys) + margin

        # Expand by 2mm to catch fanout vias just outside the component
        expand = 2.0
        fx_min = cx_min - expand
        fx_max = cx_max + expand
        fy_min = cy_min - expand
        fy_max = cy_max + expand

        # Count vias in the expanded zone but outside the courtyard
        fanout_vias = 0
        fanout_nets: set[int] = set()
        for v in all_vias:
            vx, vy = v["x"], v["y"]
            if fx_min <= vx <= fx_max and fy_min <= vy <= fy_max:
                # Outside courtyard (actual fanout) or inside (via-in-pad)
                fanout_vias += 1
                if v.get("net", 0) > 0:
                    fanout_nets.add(v["net"])

        if fanout_vias >= 4:
            fanout_patterns.append({
                "component": ref,
                "pad_count": pad_count,
                "fanout_vias": fanout_vias,
                "unique_nets": len(fanout_nets),
                "package": fp.get("library", ""),
            })

    fanout_patterns.sort(key=lambda e: e["fanout_vias"], reverse=True)

    # --- Current capacity facts ---
    # IPC-2221 approximate via current capacity (1oz copper, 10°C rise)
    # Based on plated barrel: I ≈ k * d * t where d=drill, t=plating thickness
    # Typical 1oz plating ~25µm. These are conservative approximations.
    drill_sizes: dict[float, int] = {}
    for v in all_vias:
        d = v.get("drill", 0)
        # KH-412: degenerate drills (file artefacts) are excluded from
        # every minimum/rating, not just the DFM and design-rule checks —
        # they're reported separately via `degenerate_drills` instead.
        if _is_real_drill(d):
            drill_sizes[d] = drill_sizes.get(d, 0) + 1

    current_facts: dict = {}
    if drill_sizes:
        min_drill = min(drill_sizes.keys())
        max_drill = max(drill_sizes.keys())
        current_facts = {
            "drill_size_distribution": {str(k): cnt for k, cnt
                                        in sorted(drill_sizes.items())},
            "min_drill_mm": min_drill,
            "max_drill_mm": max_drill,
            "total_vias": len(all_vias),
        }
        # Approximate current ratings for common drill sizes (25µm plating)
        ratings = []
        for d in sorted(drill_sizes.keys()):
            # Barrel cross-section = π * d * t (thin-wall cylinder)
            # Current ≈ cross_section_area * current_density
            # For 25µm plating: area_mm2 = π * d * 0.025
            area_mm2 = math.pi * d * 0.025
            # Approximate 1A per 0.003 mm² (conservative for 10°C rise)
            approx_amps = round(area_mm2 / 0.003, 1)
            ratings.append({
                "drill_mm": d,
                "count": drill_sizes[d],
                "plating_area_mm2": round(area_mm2, 4),
                "approx_current_A": approx_amps,
            })
        current_facts["ratings"] = ratings

    # KH-383: footprint-embedded thru_hole/np_thru_hole pad drills (e.g. a
    # thermal via pattern baked into a QFN footprint) aren't board vias, but
    # can be smaller than any of them — surface separately as a fact.
    pad_drills = _pad_drills(footprints)
    if pad_drills:
        current_facts["min_pad_drill_mm"] = min(pad_drills)

    # KH-412: sub-0.05mm pad/via drills are file artefacts, not real holes —
    # list them separately instead of silently dropping them.
    degenerate = _degenerate_drills(footprints, all_vias)

    result: dict = {
        "type_breakdown": type_breakdown,
        **({"degenerate_drills": degenerate} if degenerate else {}),
    }
    if annular_ring:
        result["annular_ring"] = annular_ring
    if via_in_pad:
        result["via_in_pad"] = via_in_pad
    if fanout_patterns:
        result["fanout_patterns"] = fanout_patterns
    if current_facts:
        result["current_capacity"] = current_facts

    return result


def analyze_thermal_pad_vias(footprints: list[dict], vias: dict,
                             zones: list[dict],
                             zone_fills: "ZoneFills") -> list[dict]:
    """Thermal pad via adequacy assessment for QFN/BGA/DFN packages.

    For packages with exposed/thermal pads (large center pads), checks:
    - Tier 1: vias inside the rotated 1.5x pad bounding box (any net)
    - Tier 1b: footprint-embedded thru_hole pads on the pad's net
    - Tier 2: same-net vias outside the pad bbox but within an expanded
      search radius (max(w,h)*2.0 + 2.0 mm) whose copper continuity to
      the pad is verified via the copper_connected helper — catches
      fanout fillet, adjacent via cluster, and GND-flood-connected via
      patterns
    - Via density (vias per mm²)
    - Whether vias are tented (solder mask prevents solder wicking)
    - Recommendations based on pad size

    Adequacy is computed from the TOTAL verified thermal path
    (Tier 1 + Tier 1b + Tier 2), not just the in-bbox strict count.
    This eliminates the false-positive "no thermal vias" classification
    on designs that use fillet or flood connection patterns.

    When zone fill data is not available (zones weren't saved with
    Fill All Zones), the Tier 2 search falls through cleanly:
    copper_connected returns None for every candidate, so all
    nearby same-net vias land in `nearby_unverified_vias` and do
    not influence adequacy. In that case the function's behavior
    matches pre-Tier 2 semantics.

    Field relationships in each returned entry (important for
    consumers that read more than one count field):

    - `via_count` is the STRICT in-pad count only — preserved for
      backward compat with consumers that want the in-bbox breakdown.
      It counts `vias_in_pad + footprint_via_pads`, unchanged from
      the pre-Tier 2 meaning.
    - `effective_via_count` is the drill-weighted strict in-pad count,
      also preserved unchanged.
    - `total_verified_via_count` is `via_count + nearby_verified_vias`.
    - `total_effective_verified_vias` is the drill-weighted version
      including the nearby_verified contribution.
    - `adequacy` is derived from `total_effective_verified_vias`
      (drill-weighted total including Tier 2 contributions), NOT
      from `via_count` or `effective_via_count`.
    - `raw_adequacy` is derived from `total_verified_via_count`
      (raw count total including Tier 2 contributions).
    - A reader can see `via_count: 2` alongside
      `adequacy: "adequate"` when the extra contribution comes
      from fanout-fillet vias outside the strict pad bbox. That
      is intentional, not a bug — the `adequacy_source` field
      explains which tier drove the classification.
    - `adequacy_source` is ALWAYS present on every returned entry
      and takes one of four values: "in_pad" (Tier 1/1b only),
      "nearby_fillet" (Tier 2 only), "mixed" (both), or "none"
      (no vias at all). Consumers that check `adequacy` can rely
      on `adequacy_source` being present to explain the reasoning.

    Returns a list of per-component thermal pad assessments.
    """
    # EQ-054: effective = Σ(drill/0.3)² (drill-weighted via count)
    all_vias = vias.get("vias", [])
    results: list[dict] = []

    for fp in footprints:
        if fp.get("dnp") or fp.get("board_only"):
            continue
        ref = fp.get("reference", "")
        if not ref:
            continue

        # Skip component types that don't have thermal pads
        ref_prefix = ""
        for c in ref:
            if c.isalpha():
                ref_prefix += c
            else:
                break
        if ref_prefix in ("BT", "TP", "J"):
            continue

        thermal_pads_found = _find_thermal_pads(fp)
        if not thermal_pads_found:
            continue

        pads = fp.get("pads", [])
        for pad in thermal_pads_found:
            pad_num = str(pad.get("number", ""))
            w = pad.get("width", 0)
            h = pad.get("height", 0)
            pad_area = w * h
            ax = pad.get("abs_x", fp["x"])
            ay = pad.get("abs_y", fp["y"])
            net_num = pad.get("net_number", -1)

            # Rotate the via-to-pad offset back into the pad's local frame
            # for the rectangular containment check. KiCad writes a pad's
            # (at x y angle) orientation as the ABSOLUTE board orientation
            # -- it already includes the footprint's own rotation, so the
            # footprint angle must NOT be added again (KH-408; same fix as
            # CP-003's _pad_sample_points in v2.3.0). This check must undo
            # (not repeat) the local->board placement rotation that pad
            # corners/vias are given elsewhere (board placement uses -angle,
            # e.g. _pad_sample_points), so total_rad is NOT negated here --
            # see _point_in_pad's transposed-matrix form of the same inverse
            # (VP-001, KH-340) for the equivalent established precedent.
            total_angle = pad.get("angle", 0) or 0
            total_rad = math.radians(total_angle) if total_angle != 0 else 0.0
            cos_a = math.cos(total_rad) if total_angle != 0 else 1.0
            sin_a = math.sin(total_rad) if total_angle != 0 else 0.0

            half_w = w / 2.0
            half_h = h / 2.0
            vias_in_pad = 0
            effective_vias_in_pad = 0.0
            drill_sum = 0.0
            vias_tented = 0
            vias_untented = 0

            for via in all_vias:
                vx, vy = via["x"], via["y"]
                # Transform via position into pad-local coordinates
                dx, dy = vx - ax, vy - ay
                if total_angle != 0:
                    dx, dy = dx * cos_a - dy * sin_a, dx * sin_a + dy * cos_a
                # Check if via is within the pad area (with margin for
                # manufacturing grid offsets and vias placed just outside
                # the pad boundary — matches thermal_analysis 1.5x radius)
                if (abs(dx) <= half_w * 1.5 and
                        abs(dy) <= half_h * 1.5):
                    vias_in_pad += 1
                    # Weight by drill cross-section relative to 0.3mm standard
                    drill = via.get("drill", 0.3)
                    drill_sum += drill
                    effective_vias_in_pad += (drill / 0.3) ** 2
                    # Check tenting
                    tenting = via.get("tenting", [])
                    if len(tenting) > 0:
                        vias_tented += 1
                    else:
                        vias_untented += 1

            # Count thru_hole pads in the same footprint on the same net
            # — these are footprint-embedded thermal vias (common in
            # QFN/BGA footprints like ESP32-S3-WROOM-1)
            footprint_via_pads = 0
            effective_fp_vias = 0.0
            fp_drill_sum = 0.0
            for other_pad in pads:
                if other_pad is pad:
                    continue
                if (other_pad.get("type") == "thru_hole" and
                        other_pad.get("net_number", -2) == net_num and
                        net_num >= 0):
                    footprint_via_pads += 1
                    fp_drill = other_pad.get("drill", 0.3)
                    if isinstance(fp_drill, dict):
                        fp_drill = fp_drill.get("diameter", 0.3)
                    fp_drill_sum += fp_drill
                    effective_fp_vias += (fp_drill / 0.3) ** 2

            # Tier 2: nearby same-net vias verified copper-connected to the
            # pad via the ZoneFills index. Catches fanout-fillet, adjacent
            # via cluster, and GND-flood-connected patterns that sit past
            # the 1.5x pad bbox.
            pad_net_name = pad.get("net_name", "")
            pad_layer = fp.get("layer", "F.Cu")
            nearby_search_radius = max(w, h) * 2.0 + 2.0
            nearby_verified_vias = 0
            nearby_unverified_vias = 0
            effective_nearby_verified = 0.0
            for via in all_vias:
                vx, vy = via["x"], via["y"]
                # Skip vias already counted in Tier 1 (inside the 1.5x bbox).
                # Repeat the rotation-aware rect test from the Tier 1 loop.
                dx_local, dy_local = vx - ax, vy - ay
                if total_angle != 0:
                    dx_local, dy_local = (
                        dx_local * cos_a - dy_local * sin_a,
                        dx_local * sin_a + dy_local * cos_a,
                    )
                if (abs(dx_local) <= half_w * 1.5 and
                        abs(dy_local) <= half_h * 1.5):
                    continue
                # Skip wrong net
                if via.get("net", -1) != net_num or net_num < 0:
                    continue
                # Skip beyond Tier 2 search radius (Euclidean from pad center).
                # Rotation is distance-preserving, so dx_local/dy_local give
                # the same squared distance as (vx-ax)/(vy-ay).
                if (dx_local * dx_local + dy_local * dy_local >
                        nearby_search_radius * nearby_search_radius):
                    continue
                # Verify copper continuity
                continuity = copper_connected(
                    (vx, vy), (ax, ay),
                    pad_net_name, pad_layer,
                    zone_fills, zones,
                )
                if continuity is True:
                    nearby_verified_vias += 1
                    drill = via.get("drill", 0.3)
                    effective_nearby_verified += (drill / 0.3) ** 2
                elif continuity is None:
                    nearby_unverified_vias += 1
                # continuity is False: via on same net but not copper-connected,
                # skip (not contributing to thermal path)

            # Totals combining all three tiers
            strict_via_count = vias_in_pad + footprint_via_pads
            total_verified_via_count = strict_via_count + nearby_verified_vias
            total_effective_verified_vias = (
                effective_vias_in_pad + effective_fp_vias +
                effective_nearby_verified)

            # Density is still computed from strict in-pad contribution only —
            # it's a pad-area metric, not a whole-thermal-path metric
            density = 0.0
            if pad_area > 0:
                density = (effective_vias_in_pad + effective_fp_vias) / pad_area

            # Recommendations based on pad area
            # Rule of thumb: ~1 via per 1-2mm² of thermal pad area
            # Small QFN (pad < 10mm²): minimum 5-9 vias
            # Medium QFN (10-25mm²): minimum 9-16 vias
            # Large QFN/BGA (>25mm²): scale by area
            if pad_area < 10:
                recommended_min = 5
                recommended_ideal = 9
            elif pad_area < 25:
                recommended_min = 9
                recommended_ideal = 16
            else:
                recommended_min = max(9, int(pad_area * 0.5))
                recommended_ideal = max(16, int(pad_area * 0.8))

            # Assess adequacy using drill-weighted effective count including
            # nearby-verified contributions
            if total_effective_verified_vias >= recommended_ideal:
                adequacy = "good"
            elif total_effective_verified_vias >= recommended_min:
                adequacy = "adequate"
            elif total_verified_via_count > 0:
                adequacy = "insufficient"
            else:
                adequacy = "none"

            # Raw adequacy based on actual verified via count (ignoring drill)
            if total_verified_via_count >= recommended_ideal:
                raw_adequacy = "good"
            elif total_verified_via_count >= recommended_min:
                raw_adequacy = "adequate"
            elif total_verified_via_count > 0:
                raw_adequacy = "insufficient"
            else:
                raw_adequacy = "none"

            # When physical count meets threshold but drill weighting doesn't,
            # use raw adequacy as primary — drill size is a secondary concern
            # (many manufacturer reference designs use 0.2mm vias in thermal pads)
            drill_penalized = (raw_adequacy in ("adequate", "good") and
                               adequacy in ("insufficient", "none") and
                               total_verified_via_count > 0)
            if drill_penalized:
                adequacy = raw_adequacy

            # Explain which tiers contributed to the adequacy classification
            # (always present, never None — consumers can rely on this field)
            if nearby_verified_vias > 0 and strict_via_count > 0:
                adequacy_source = "mixed"
            elif nearby_verified_vias > 0:
                adequacy_source = "nearby_fillet"
            elif strict_via_count > 0:
                adequacy_source = "in_pad"
            else:
                adequacy_source = "none"

            entry: dict = {
                "component": ref,
                "value": fp.get("value", ""),
                "library": fp.get("library", ""),
                "layer": fp.get("layer", "F.Cu"),
                "pad_number": pad_num,
                "pad_size_mm": [round(w, 2), round(h, 2)],
                "pad_area_mm2": round(pad_area, 2),
                "net": pad.get("net_name", ""),
                "via_count": strict_via_count,
                "effective_via_count": round(
                    effective_vias_in_pad + effective_fp_vias, 1),
                "standalone_vias": vias_in_pad,
                "footprint_via_pads": footprint_via_pads,
                "nearby_verified_vias": nearby_verified_vias,
                "nearby_unverified_vias": nearby_unverified_vias,
                "nearby_search_radius_mm": round(nearby_search_radius, 2),
                "total_verified_via_count": total_verified_via_count,
                "total_effective_verified_vias": round(
                    total_effective_verified_vias, 1),
                "adequacy_source": adequacy_source,
                "via_density_per_mm2": round(density, 3),
                "vias_tented": vias_tented,
                "vias_untented": vias_untented,
                "recommended_min_vias": recommended_min,
                "recommended_ideal_vias": recommended_ideal,
                "adequacy": adequacy,
                "raw_adequacy": raw_adequacy,
            }

            if vias_untented > 0:
                entry["tenting_note"] = (
                    f"{vias_untented} via(s) are not tented — solder may wick "
                    f"through during reflow, creating voids under the thermal pad"
                )

            if drill_penalized and strict_via_count > 0:
                avg_drill = (drill_sum + fp_drill_sum) / strict_via_count
                strict_effective = effective_vias_in_pad + effective_fp_vias
                entry["small_via_note"] = (
                    f"{strict_via_count} vias present (avg drill "
                    f"{avg_drill:.2f}mm) but effective count "
                    f"({strict_effective:.1f}) is below threshold "
                    f"({recommended_min}) due to small drill size — "
                    f"design may follow manufacturer's recommended via pattern"
                )

            entry["detector"] = "analyze_thermal_pad_vias"
            entry["rule_id"] = "TV-001"
            entry["category"] = "thermal"
            entry["severity"] = "warning" if adequacy in ("none", "insufficient") else "info"
            entry["confidence"] = "deterministic"
            entry["evidence_source"] = "topology"
            entry["summary"] = f"Thermal vias: {ref} {adequacy} ({strict_via_count}/{recommended_min} min)"
            entry["description"] = (
                f"Thermal pad on {ref} pad {pad_num}: {adequacy} "
                f"({strict_via_count} vias, {recommended_min} recommended)."
            )
            entry["components"] = [ref]
            entry["nets"] = [pad.get("net_name", "")]
            entry["pins"] = []
            rec = []
            if adequacy in ("none", "insufficient"):
                rec.append(f"Add thermal vias under {ref} (need {recommended_min}, have {strict_via_count}).")
            if entry.get("tenting_note"):
                rec.append(entry["tenting_note"])
            entry["recommendation"] = " ".join(rec)
            entry["report_context"] = {
                "section": "Thermal",
                "impact": "Thermal dissipation",
                "standard_ref": "",
            }

            results.append(entry)

    # Sort: worst adequacy first
    adequacy_order = {"none": 0, "insufficient": 1, "adequate": 2, "good": 3}
    results.sort(key=lambda r: (adequacy_order.get(r["adequacy"], 4),
                                r["component"]))
    return results


# Generic-passive reference designators (C, R, L, FB + digits, optionally
# with a hierarchical sheet prefix like "U1/C5"). F10: CP-002 skips these
# because on a 2-layer board with a GND pour every decoupling cap's VCC
# pad is "uncovered" — that's expected, not a finding. Components on real
# touch / antenna pads use TP-prefixed refs or non-passive libraries and
# are surfaced via CP-003.
_PASSIVE_REF_RE = re.compile(r"^([A-Za-z0-9_]+/)?(C|R|L|FB)\d+$")


def _nearest_zone_copper_distance(fp: dict, fp_layer: str, gnd_zones: list,
                                  zones: list, zone_fills) -> tuple:
    """Distance from a footprint's pad outline to the nearest same-layer GND
    copper.

    KH-373: prefers the filled polygon edge (actual copper shape, holes
    included) over the zone bbox — the bbox was always 0.0 mm for any GND
    pour enclosing the footprint, mislabelled 'deterministic'. Falls back
    to KH-339's filled_bbox / outline_bbox approximation when polygon
    data is unavailable. Returns (distance, basis) where basis is
    'filled_polygon', 'filled_bbox', or 'outline_bbox' (None if no
    candidate zone).
    """
    if zone_fills is not None and getattr(zone_fills, "has_data", False):
        gnd_idxs = {i for i, z in enumerate(zones)
                   if z in gnd_zones and fp_layer in z.get("layers", [])}
        if gnd_idxs:
            best = min(zone_fills.min_edge_distance(px, py, fp_layer, gnd_idxs)
                       for px, py in _pad_sample_points(fp, fp_layer))
            if best < float("inf"):
                return best, "filled_polygon"

    fx, fy = fp.get("x", 0), fp.get("y", 0)
    min_dist = float('inf')
    basis = None
    for gz in gnd_zones:
        if fp_layer not in gz.get("layers", []):
            continue
        gz_basis = "filled_bbox" if gz.get("filled_bbox") else "outline_bbox"
        bbox = gz.get("filled_bbox") or gz.get("outline_bbox")
        if not bbox or len(bbox) != 4:
            continue
        bx_min, by_min, bx_max, by_max = bbox
        # EQ-102: d = √((px-zx)² + (py-zy)²) for point-to-zone-pour proximity.
        # Source: Self-evident — 2D Euclidean distance to the nearest
        #   axis-aligned bounding-box edge (dx/dy clamped to 0 when the
        #   point is inside the box on that axis).
        dx = max(bx_min - fx, 0, fx - bx_max)
        dy = max(by_min - fy, 0, fy - by_max)
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < min_dist:
            min_dist = dist
            basis = gz_basis
    return min_dist, basis


def analyze_copper_presence(footprints: list[dict], zones: list[dict],
                            zone_fills: ZoneFills,
                            ref_layer_map: dict[str, str] | None = None) -> dict:
    """Check zone copper presence at component pad locations.

    Uses point-in-polygon tests against zone filled polygon data to determine
    actual copper presence. Rather than listing every component with the common
    pattern (e.g., GND pour under everything on a 2-layer board), this reports
    a compact summary plus detailed exceptions:

    - Summary: how many components have opposite-layer copper, grouped by net
    - Exceptions: components WITHOUT opposite-layer copper when most others
      have it (e.g., touch pads with clearance in the ground pour)
    - Foreign zones: components with same-layer copper from a zone they're not
      connected to

    Requires filled zone data — run Fill All Zones in KiCad before analysis.
    """
    if not zone_fills.has_data:
        return {
            "warning": "No filled polygon data — zones may not have been "
                       "filled. Run Edit → Fill All Zones (B) in KiCad and "
                       "re-save before analysis.",
        }

    # Classify every component by opposite-layer copper status.
    # Use the component center (first pad centroid) for the check.
    opp_covered: dict[str, set[str]] = {}  # ref -> set of opp zone net names
    opp_uncovered: list[str] = []  # refs with NO opposite-layer copper
    foreign_zone_details: list[dict] = []  # same-layer foreign zone hits

    for fp in footprints:
        ref = fp.get("reference", "")
        fp_layer = fp.get("layer", "F.Cu")
        if ref_layer_map:
            opposite_layer = ref_layer_map.get(fp_layer, "B.Cu" if fp_layer == "F.Cu" else "F.Cu")
        else:
            opposite_layer = "B.Cu" if fp_layer == "F.Cu" else "F.Cu"
        pads = fp.get("pads", [])
        if not pads:
            continue

        # Check opposite-layer copper at each pad location
        has_opp = False
        opp_nets: set[str] = set()
        foreign_pads: list[dict] = []

        for pad in pads:
            px = pad.get("abs_x", fp["x"])
            py = pad.get("abs_y", fp["y"])
            pad_net = pad.get("net_number", 0)

            opp_zones = zone_fills.zones_at_point(
                px, py, opposite_layer, zones)
            if opp_zones:
                has_opp = True
                for z in opp_zones:
                    nn = z.get("net_name", "")
                    if nn:
                        opp_nets.add(nn)

            # Same-layer foreign zone check
            same_other = [
                z for z in zone_fills.zones_at_point(px, py, fp_layer, zones)
                if z.get("net", 0) != pad_net and pad_net > 0
            ]
            if same_other:
                foreign_pads.append({
                    "pad": str(pad.get("number", "")),
                    "position": [round(px, 3), round(py, 3)],
                    "foreign_zones": [z["net_name"] for z in same_other],
                })

        if has_opp:
            opp_covered[ref] = opp_nets
        else:
            opp_uncovered.append(ref)

        if foreign_pads:
            fz_nets = list(set(
                n for fp_pad in foreign_pads
                for n in fp_pad["foreign_zones"]
            ))
            # Classify: is every foreign zone a ground rail AND does this
            # component have a pin on that ground? That's the "desired"
            # case (decoupling cap sitting over GND pour) and should
            # surface as info, not warning. Anything else stays a
            # warning — mixed rails, non-ground foreign zones, or
            # components that don't actually reference the foreign net.
            fz_all_ground = bool(fz_nets) and all(
                is_ground_name(n) for n in fz_nets
            )
            comp_pad_nets = {
                (p.get("net_name") or "").upper()
                for p in fp.get("pads", []) or []
                if p.get("net_name")
            }
            comp_has_gnd_pad = any(
                is_ground_name(n) for n in comp_pad_nets
            )
            if fz_all_ground and comp_has_gnd_pad:
                severity = "info"
                impact = ("Decoupling / bypass cap sitting over the GND pour — "
                          "expected layout, not a clearance violation.")
                rec = ("No action. Bypass caps are intentionally placed over "
                       "the ground return to minimise loop area.")
            else:
                severity = "warning"
                impact = "Electrical isolation"
                rec = "Verify zone clearance rules or add keepout."

            foreign_zone_details.append({
                "component": ref,
                "value": fp.get("value", ""),
                "layer": fp_layer,
                "pads": foreign_pads,
                "detector": "analyze_copper_presence",
                "rule_id": "CP-001",
                "category": "copper_integrity",
                "severity": severity,
                "confidence": "deterministic",
                "evidence_source": "geometry",
                "summary": f"Foreign zone under {ref}",
                "description": (
                    f"Component {ref} has same-layer copper from foreign "
                    f"zone(s): {', '.join(fz_nets)}."
                ),
                "components": [ref],
                "nets": fz_nets,
                "pins": [fp_pad["pad"] for fp_pad in foreign_pads],
                "recommendation": rec,
                "report_context": {
                    "section": "Copper Integrity",
                    "impact": impact,
                    "standard_ref": "",
                },
            })

    # Build compact summary
    # Group covered components by which nets they sit over
    net_groups: dict[str, list[str]] = {}  # "GND" -> [ref1, ref2, ...]
    for ref, nets in opp_covered.items():
        key = ", ".join(sorted(nets))
        net_groups.setdefault(key, []).append(ref)

    opp_summary: list[dict] = []
    for nets_str, refs in sorted(net_groups.items(),
                                 key=lambda x: -len(x[1])):
        opp_summary.append({
            "opposite_layer_nets": nets_str,
            "component_count": len(refs),
            "components": sorted(refs),
        })

    result: dict = {
        "opposite_layer_summary": opp_summary,
    }

    # The interesting signal: components WITHOUT opposite-layer copper.
    # F10: emit CP-002 findings only for non-passive references — on a
    # 2-layer board with a GND pour on the opposite side, every decoupling
    # cap's VCC pad would otherwise fire CP-002, drowning the info tier.
    # Actual touch-sensitive / RF components are still surfaced via CP-003.
    # The summary list (`no_opposite_layer_copper`) keeps everything so
    # consumers that want the raw uncovered set still have it.
    if opp_uncovered:
        result["no_opposite_layer_copper"] = sorted(opp_uncovered)
        cp_002_refs = [r for r in opp_uncovered if not _PASSIVE_REF_RE.match(r)]
        if cp_002_refs:
            result["no_opposite_layer_copper_findings"] = [{
                "component": _ref,
                "detector": "analyze_copper_presence",
                "rule_id": "CP-002",
                "category": "copper_integrity",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "geometry",
                "summary": f"No opposite-layer copper under {_ref}",
                "description": (
                    f"Component {_ref} has no copper zone on the opposite layer."
                ),
                "components": [_ref],
                "nets": [],
                "pins": [],
                "recommendation": "",
                "report_context": {
                    "section": "Copper Integrity",
                    "impact": "Return path / shielding",
                    "standard_ref": "",
                },
            } for _ref in sorted(cp_002_refs)]

    if foreign_zone_details:
        result["same_layer_foreign_zones"] = foreign_zone_details

    # Touch pad GND clearance measurement
    # For components in opp_uncovered that look like touch pads, compute
    # distance to nearest same-layer GND zone edge
    _gnd_keywords = ("gnd", "vss", "ground", "agnd", "dgnd", "pgnd")
    gnd_zones = [z for z in zones
                 if z.get("net_name", "").lower() in _gnd_keywords
                 or "gnd" in z.get("net_name", "").lower()]
    touch_clearances = []
    for fp in footprints:
        ref = fp.get("reference", "")
        if ref not in opp_uncovered:
            continue
        lib = fp.get("library", "").lower()
        val = (fp.get("value") or "").lower()
        # KH-373: a bare "TP" ref prefix is not evidence of a touch pad --
        # 466/488 of the corpus's CP-003 "touch pad" refs were actually
        # TestPoint:* library parts. Require positive evidence instead
        # (a touch/capacitive-sensing library or value, or a TOUCH/TCH ref);
        # a testpoint library is never touch even if it also matches those.
        if "testpoint" in lib or "test_point" in lib:
            is_touch = False
        else:
            is_touch = (any(k in lib for k in ("touch", "capacitive", "captouch", "cap_touch"))
                        or any(k in val for k in ("touch", "capacitive", "captouch", "cap_touch"))
                        or ref.upper().startswith(("TOUCH", "TCH")))
        if not is_touch:
            continue
        fp_layer = fp.get("layer", "F.Cu")
        min_dist, _basis = _nearest_zone_copper_distance(fp, fp_layer,
                                                         gnd_zones, zones,
                                                         zone_fills)
        if min_dist < float('inf'):
            _conf = "deterministic" if _basis == "filled_polygon" else "heuristic"
            _note = ("" if _basis == "filled_polygon" else
                     " (zone bbox basis — fill polygon data unavailable; "
                     "actual clearance may be larger)")
            _nets = sorted({p.get("net_name") for p in fp.get("pads", [])
                          if p.get("net_name") and not is_ground_name(p["net_name"])})
            touch_clearances.append({
                "ref": ref,
                "layer": fp_layer,
                "gnd_clearance_mm": round(min_dist, 2),
                "measurement_basis": _basis,
                "detector": "analyze_copper_presence",
                "rule_id": "CP-003",
                "category": "copper_integrity",
                "severity": "info",
                "confidence": _conf,
                "evidence_source": "geometry",
                "summary": f"Touch pad {ref} GND clearance {round(min_dist, 2)}mm",
                "description": (
                    f"Touch pad {ref} on {fp_layer}: {round(min_dist, 2)}mm "
                    f"clearance to nearest GND zone copper{_note}."
                ),
                "components": [ref],
                "nets": _nets,
                "pins": [],
                "recommendation": "",
                "report_context": {
                    "section": "Copper Integrity",
                    "impact": "Touch sensitivity",
                    "standard_ref": "",
                },
            })
    if touch_clearances:
        result["touch_pad_gnd_clearance"] = touch_clearances

    return result


def analyze_via_in_pad(footprints: list[dict], vias: dict, thermal_pad_refs: set) -> list[dict]:
    """VP-001: Detect vias inside SMD pads that aren't tented."""
    findings: list[dict] = []
    via_list = vias.get("vias", [])
    if not via_list:
        return findings

    # Build SMD pad bboxes (excluding thermal pads already covered by TV-001)
    smd_pads: list[tuple[str, str, str, float, float, float, float]] = []
    for fp in footprints:
        ref = fp.get("reference", "")
        if ref in thermal_pad_refs:
            continue
        for pad in fp.get("pads", []):
            if pad.get("type") != "smd":
                continue
            # KH-349: pads "disabled" by clearing all copper layers
            # (e.g. (layers "Dwgs.User")) can't have via-in-pad issues.
            _pad_layers = pad.get("layers") or []
            if _pad_layers and not any(l.endswith(".Cu") for l in _pad_layers):
                continue
            px = pad.get("abs_x")
            py = pad.get("abs_y")
            if px is None or py is None:
                continue
            pw = pad.get("width", 0)
            ph = pad.get("height", 0)
            if pw <= 0 or ph <= 0:
                continue
            pad_num = pad.get("number", "?")
            smd_pads.append((ref, pad_num, pad.get("net_name", ""),
                             px, py, pw, ph,
                             pad.get("shape", "rect"), pad.get("angle", 0)))

    for via in via_list:
        vx = via.get("x")
        vy = via.get("y")
        if vx is None or vy is None:
            continue
        for ref, pad_num, net, ppx, ppy, pw, ph, pshape, pangle in smd_pads:
            if _point_in_pad(vx, vy, ppx, ppy, pw, ph, pshape, pangle):
                # Check tenting
                tenting = via.get("tenting", [])
                tented = len(tenting) > 0
                severity = "info" if tented else "warning"
                findings.append({
                    "component": ref,
                    "pad": pad_num,
                    "via_x": round(vx, 2),
                    "via_y": round(vy, 2),
                    "tented": tented,
                    "detector": "analyze_via_in_pad",
                    "rule_id": "VP-001",
                    "category": "dfm",
                    "severity": severity,
                    "confidence": "heuristic",
                    "evidence_source": "topology",
                    "summary": f"Via in pad: {ref}:{pad_num} ({'tented' if tented else 'untented'})",
                    "description": f"Via at ({round(vx, 2)}, {round(vy, 2)}) inside SMD pad {ref}:{pad_num}. {'Tented.' if tented else 'Not tented — solder may wick through.'}",
                    "components": [ref],
                    "nets": [net] if net else [],
                    "pins": [],
                    "recommendation": "" if tented else f"Fill and cap via in {ref}:{pad_num} or tent with solder mask.",
                    "report_context": {"section": "DFM", "impact": "Solder wicking risk" if not tented else "", "standard_ref": ""},
                })
                break  # One finding per via

    return findings


def analyze_board_edge_via_clearance(vias: dict, board_outline: dict) -> list[dict]:
    """BV-001: Check vias close to board edges."""
    # EQ-103: d = min distance from via center to any Edge.Cuts line segment.
    # Source: Self-evident — 2D point-to-segment distance (see EQ-098).
    findings: list[dict] = []
    via_list = vias.get("vias", [])
    edges = board_outline.get("edges", [])

    if not via_list or not edges:
        return findings

    def _pt_seg_dist(px, py, x1, y1, x2, y2):
        # EQ-104: Helper — same 2D point-to-segment distance as EQ-098.
        # Source: Self-evident — kept as a local helper to avoid import cycles.
        dx, dy = x2 - x1, y2 - y1
        length_sq = dx * dx + dy * dy
        if length_sq == 0:
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / length_sq))
        return math.sqrt((px - x1 - t * dx) ** 2 + (py - y1 - t * dy) ** 2)

    # Extract edge line segments
    edge_segs: list[tuple[float, float, float, float]] = []
    for edge in edges:
        etype = edge.get("type", "")
        if etype == "line":
            s = edge.get("start", [0, 0])
            e = edge.get("end", [0, 0])
            edge_segs.append((s[0], s[1], e[0], e[1]))
        elif etype == "rect":
            s = edge.get("start", [0, 0])
            e = edge.get("end", [0, 0])
            edge_segs.append((s[0], s[1], e[0], s[1]))
            edge_segs.append((e[0], s[1], e[0], e[1]))
            edge_segs.append((e[0], e[1], s[0], e[1]))
            edge_segs.append((s[0], e[1], s[0], s[1]))

    if not edge_segs:
        return findings

    threshold_mm = 0.5
    for via in via_list:
        vx = via.get("x")
        vy = via.get("y")
        if vx is None or vy is None:
            continue
        min_dist = float("inf")
        for x1, y1, x2, y2 in edge_segs:
            d = _pt_seg_dist(vx, vy, x1, y1, x2, y2)
            if d < min_dist:
                min_dist = d
        if min_dist < threshold_mm:
            findings.append({
                "via_x": round(vx, 2),
                "via_y": round(vy, 2),
                "edge_clearance_mm": round(min_dist, 3),
                "detector": "analyze_board_edge_via_clearance",
                "rule_id": "BV-001",
                "category": "dfm",
                "severity": "warning",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Via at ({round(vx, 1)}, {round(vy, 1)}) is {round(min_dist, 2)}mm from board edge",
                "description": f"Via at ({round(vx, 2)}, {round(vy, 2)}) is only {round(min_dist, 3)}mm from the board edge. Minimum recommended is {threshold_mm}mm.",
                "components": [],
                "nets": [],
                "pins": [],
                "recommendation": f"Move via at least {threshold_mm}mm from board edge to prevent damage during depanelization.",
                "report_context": {"section": "DFM", "impact": "Via damage during routing/depanelization", "standard_ref": ""},
            })

    return findings[:50]  # Cap at 50 findings
