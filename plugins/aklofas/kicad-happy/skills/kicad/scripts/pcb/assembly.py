"""PCB placement and assembly checks: decoupling placement, placement/courtyards,
tombstoning, switching loops, fiducials, test points, orientation, silkscreen overlaps, keepouts.
Verbatim moves from analyze_pcb.py."""

import math
import re

from kicad_core.netnames import is_ground_name
from pcb.geometry import _refined_overlap_mm2


_ESD_TVS_PREFIXES = ("esd", "prtr", "usblc", "tpd", "pesd", "sp05",
                     "rclamp", "nup", "lesd", "ip4", "dt104")


def _min_power_pad_distance(ic_fp: dict, cap_fp: dict) -> float:
    """Minimum distance between IC power/ground pads and capacitor pads.

    Uses absolute pad coordinates for accurate distance on large packages
    where footprint center can be 3+ mm from the actual power pin.
    Falls back to footprint center distance if pad data is missing.
    """
    # EQ-101: d = √((x1-x2)² + (y1-y2)²) over all pad pairs; return minimum.
    # Source: Self-evident — 2D Euclidean distance.
    ic_pads = ic_fp.get("pads", [])
    cap_pads = cap_fp.get("pads", [])

    # Find IC pads on power or ground nets
    power_pads = []
    for pad in ic_pads:
        net = pad.get("net_name", "")
        if not net:
            continue
        nu = net.upper()
        is_pwr_gnd = (
            nu in ("GND", "VSS", "AGND", "DGND", "PGND", "VCC", "VDD",
                   "AVCC", "AVDD", "DVCC", "DVDD") or
            nu.startswith(("GND", "VSS", "VCC", "VDD", "+")) or
            nu.endswith(("GND", "VSS")) or
            "V" in nu and any(c.isdigit() for c in nu)
        )
        if is_pwr_gnd:
            power_pads.append(pad)

    if not power_pads or not cap_pads:
        # Fallback: footprint center distance
        dx = ic_fp["x"] - cap_fp["x"]
        dy = ic_fp["y"] - cap_fp["y"]
        return math.sqrt(dx * dx + dy * dy)

    # Minimum distance between any IC power pad and any cap pad
    min_dist = float("inf")
    for ip in power_pads:
        ix, iy = ip.get("abs_x"), ip.get("abs_y")
        if ix is None or iy is None:
            continue
        for cp in cap_pads:
            cx, cy = cp.get("abs_x"), cp.get("abs_y")
            if cx is None or cy is None:
                continue
            d = math.sqrt((ix - cx) ** 2 + (iy - cy) ** 2)
            if d < min_dist:
                min_dist = d
    return min_dist


def _nearby_decoupling_caps(ic: dict, caps: list[dict]) -> tuple[list[dict], list[str]]:
    """Caps within 10 mm that share a non-ground net with the IC (KH-379).
    Returns (nearby sorted by distance, refs of <=10 mm caps rejected as
    ground-only)."""
    ic_nets = {p.get("net_name") for p in ic.get("pads", []) if p.get("net_name")}
    nearby, rejected = [], []
    for cap in caps:
        dist = _min_power_pad_distance(ic, cap)
        if dist > 10.0:
            continue
        cap_nets = {p.get("net_name") for p in cap.get("pads", []) if p.get("net_name")}
        shared = {n for n in (ic_nets & cap_nets) if n and not is_ground_name(n)}
        if not shared:
            rejected.append(cap["reference"])
            continue
        nearby.append({"cap": cap["reference"], "value": cap.get("value", ""),
                       "distance_mm": round(dist, 2), "shared_nets": sorted(shared),
                       "same_side": cap["layer"] == ic["layer"]})
    nearby.sort(key=lambda n: (n["distance_mm"], n["cap"]))
    return nearby, sorted(rejected)


def analyze_decoupling_placement(footprints: list[dict]) -> list[dict]:
    """For each IC, find nearby capacitors and report distances.

    Helps verify decoupling caps are placed close to IC power pins.
    """
    # EQ-048: d = √(Δx²+Δy²) (cap-to-IC distance)
    ics = [fp for fp in footprints
           if re.match(r'^(U|IC)\d', fp.get("reference", ""))
           and not any(fp.get("value", "").lower().startswith(p)
                       for p in _ESD_TVS_PREFIXES)]
    caps = [fp for fp in footprints if re.match(r'^C\d', fp.get("reference", ""))]

    if not caps:
        return []

    results = []
    for ic in ics:
        nearby, rejected = _nearby_decoupling_caps(ic, caps)
        if nearby:
            entry = {
                "ic": ic["reference"],
                "value": ic.get("value", ""),
                "layer": ic["layer"],
                "nearby_caps": nearby,
                "closest_cap_mm": nearby[0]["distance_mm"],
            }
            if rejected:
                entry["gnd_only_caps"] = rejected
            results.append(entry)

    # ESD protection ICs need bypass caps within 3mm for clamping
    esd_ics = [fp for fp in footprints
               if re.match(r'^(U|IC)\d', fp.get("reference", ""))
               and any(fp.get("value", "").lower().startswith(p)
                       for p in _ESD_TVS_PREFIXES)]
    for ic in esd_ics:
        nearby, rejected = _nearby_decoupling_caps(ic, caps)
        if nearby:
            entry = {
                "ic": ic["reference"],
                "value": ic.get("value", ""),
                "layer": ic["layer"],
                "category": "esd_bypass",
                "nearby_caps": nearby,
                "closest_cap_mm": nearby[0]["distance_mm"],
            }
            if rejected:
                entry["gnd_only_caps"] = rejected
            results.append(entry)

    return results


_RF_MODULE_KEYWORDS = (
    'ESP32', 'ESP8266', 'WROOM', 'WROVER', 'XIAO', 'nRF52', 'nRF53',
    'RN4871', 'RN4870', 'RAK', 'LoRa', 'SIM800', 'SIM7', 'EC25', 'SIM868',
    'BGM', 'BGT', 'BM71', 'HM-10', 'HC-05',
)


_RF_LIB_KEYWORDS = ('RF_Module', 'RF_WiFi', 'RF_Bluetooth', 'RF_GPS')


def _is_rf_module(fp: dict) -> bool:
    """Return True if the footprint looks like an RF/wireless module."""
    library = fp.get('library', '') or ''
    value = fp.get('value', '') or ''
    for kw in _RF_LIB_KEYWORDS:
        if kw in library:
            return True
    for kw in _RF_MODULE_KEYWORDS:
        if kw.lower() in value.lower() or kw.lower() in library.lower():
            return True
    return False


# Edge-mount footprint categories: by-design at the board edge — PM-002 edge
# clearance should demote to info (not warning/error) for these. rc.2 4.1
# expansion (SparkFun review).
_EDGE_MOUNT_LIBRARY_KEYWORDS = (
    'SMA_Edge',                           # edge-launch SMA antenna connectors
    'USB_C_Receptacle',                   # vertical/board-edge USB-C
    'USB_Mini', 'USB_Micro',              # board-edge USB Mini/Micro
    'USB_A_Vertical', 'USB_B_Vertical',
    'MagJack',                            # RJ45 with integrated mag — by-edge
    'microSD', 'SD_Card',                 # microSD/SD card edge sockets
    'BarrelJack',                         # DC barrel jack at edge
    'Standoff', 'Mounting',               # mounting features near edge are intentional
    'TerminalBlock',                      # screw terminals at board edge
    'Phoenix_MSTB',                       # Phoenix MSTB/MSTBA/MSTBVA terminal-block family (F8)
    'JST_', 'Molex_PicoBlade',            # edge-launched JST/Molex wire-to-board
)


_EDGE_MOUNT_VALUE_KEYWORDS = (
    'EDGE', 'VERTICAL',                   # value-string hints
)


def _is_edge_mount_footprint(fp: dict) -> bool:
    """Return True if the footprint is designed to sit at the board edge
    (board-edge connector, edge-launch antenna, mounting hole, etc.).
    PM-002 demotes edge-clearance findings to info for these.
    """
    library = fp.get('library', '') or fp.get('footprint', '') or ''
    value = fp.get('value', '') or ''
    for kw in _EDGE_MOUNT_LIBRARY_KEYWORDS:
        if kw.lower() in library.lower():
            return True
    for kw in _EDGE_MOUNT_VALUE_KEYWORDS:
        if kw in value.upper():
            return True
    return False


def analyze_placement(footprints: list[dict], outline: dict) -> dict:
    """Component placement analysis — courtyard overlaps and edge clearance.

    Reports:
    - Courtyard overlaps: pairs of components on the same side whose courtyard
      bounding boxes overlap (potential physical collision or assembly issue)
    - Edge clearance: components closest to board edges (flagged if <0.5mm)
    - Placement density per board side
    """
    # Courtyard overlap detection (AABB intersection, same side only)
    overlaps = []
    fp_with_cy = [(fp, fp["courtyard"]) for fp in footprints if fp.get("courtyard")]

    for i in range(len(fp_with_cy)):
        fp_a, cy_a = fp_with_cy[i]
        for j in range(i + 1, len(fp_with_cy)):
            fp_b, cy_b = fp_with_cy[j]
            # Only check components on the same side
            if fp_a["layer"] != fp_b["layer"]:
                continue
            # AABB overlap check
            if (cy_a["min_x"] < cy_b["max_x"] and cy_a["max_x"] > cy_b["min_x"] and
                    cy_a["min_y"] < cy_b["max_y"] and cy_a["max_y"] > cy_b["min_y"]):
                # Compute overlap area
                ox = min(cy_a["max_x"], cy_b["max_x"]) - max(cy_a["min_x"], cy_b["min_x"])
                oy = min(cy_a["max_y"], cy_b["max_y"]) - max(cy_a["min_y"], cy_b["min_y"])
                overlap_mm2 = round(ox * oy, 3)
                # KH-350: AABB is only a pre-filter — notched courtyards
                # (QFP cross shapes) fill their corners in bbox space. With
                # chained polygons on both parts, measure the true overlap.
                _polys_a = fp_a.get("courtyard_poly")
                _polys_b = fp_b.get("courtyard_poly")
                if _polys_a and _polys_b:
                    _refined = _refined_overlap_mm2(
                        _polys_a, _polys_b,
                        max(cy_a["min_x"], cy_b["min_x"]),
                        max(cy_a["min_y"], cy_b["min_y"]),
                        min(cy_a["max_x"], cy_b["max_x"]),
                        min(cy_a["max_y"], cy_b["max_y"]))
                    if _refined <= 0.0:
                        continue
                    overlap_mm2 = round(_refined, 3)
                is_rf_overlap = _is_rf_module(fp_a) or _is_rf_module(fp_b)
                # RF module courtyards deliberately encode the antenna RF
                # keepout (e.g., ESP32-S3-WROOM-1 extends ~7mm past the body
                # to enforce the no-copper keepout).  Overlap with a neighbor
                # usually means the neighbor is inside the keepout, not a
                # physical body collision.  Demote to info with a hint.
                if is_rf_overlap:
                    severity = 'info'
                elif overlap_mm2 > 1.0:
                    severity = 'error'
                else:
                    severity = 'warning'
                rf_note = (' (courtyard includes RF keepout — verify neighbor '
                           'is outside the antenna keepout, not a body collision)'
                           if is_rf_overlap else '')
                overlaps.append({
                    "component_a": fp_a["reference"],
                    "component_b": fp_b["reference"],
                    "layer": fp_a["layer"],
                    "overlap_mm2": overlap_mm2,
                    "detector": "analyze_placement",
                    "rule_id": "PM-001",
                    "category": "placement",
                    "severity": severity,
                    "confidence": "deterministic",
                    "evidence_source": "topology",
                    "summary": f"Courtyard overlap between {fp_a['reference']} and {fp_b['reference']} ({overlap_mm2}mm\u00b2){rf_note}",
                    "description": f"Components {fp_a['reference']} and {fp_b['reference']} have overlapping courtyards on {fp_a['layer']} ({overlap_mm2}mm\u00b2 overlap area). Threshold: \u22651.0mm\u00b2 = error, else warning; RF-module overlaps demote to info (courtyard encodes RF keepout).",
                    "components": [fp_a["reference"], fp_b["reference"]],
                    "nets": [],
                    "pins": [],
                    "recommendation": f"Resolve courtyard overlap between {fp_a['reference']} and {fp_b['reference']} — move components apart or adjust courtyard geometry",
                    "report_context": {"section": "Placement", "impact": "assembly", "standard_ref": ""},
                })

    overlaps.sort(key=lambda o: o["overlap_mm2"], reverse=True)

    # Edge clearance — distance from component center to nearest board edge
    edge_close: list[dict] = []
    bbox = outline.get("bounding_box")
    if bbox:
        bx_min, by_min = bbox["min_x"], bbox["min_y"]
        bx_max, by_max = bbox["max_x"], bbox["max_y"]
        for fp in footprints:
            if not fp.get("reference"):
                continue
            cx, cy = fp["x"], fp["y"]
            # Distance to nearest edge (simplified — board outline as rectangle)
            d_left = cx - bx_min
            d_right = bx_max - cx
            d_top = cy - by_min
            d_bottom = by_max - cy
            min_edge = min(d_left, d_right, d_top, d_bottom)
            fp_min_x = fp_max_x = cx
            fp_min_y = fp_max_y = cy

            # Use courtyard if available for tighter estimate
            if fp.get("courtyard"):
                cy_box = fp["courtyard"]
                fp_min_x, fp_max_x = cy_box["min_x"], cy_box["max_x"]
                fp_min_y, fp_max_y = cy_box["min_y"], cy_box["max_y"]
                min_edge = min(
                    cy_box["min_x"] - bx_min,
                    bx_max - cy_box["max_x"],
                    cy_box["min_y"] - by_min,
                    by_max - cy_box["max_y"],
                )

            if min_edge < 1.0:  # Flag components within 1mm of edge
                clearance = round(min_edge, 2)
                # KH-389: a bbox entirely outside the outline bbox isn't "near
                # the edge" — it's off the board. Distinct classification,
                # checked ahead of the RF/edge-mount exemptions below (those
                # are for by-design partial overhang, not fully-off-board).
                is_off_board = (fp_max_x < bx_min or fp_min_x > bx_max or
                                 fp_max_y < by_min or fp_min_y > by_max)
                # RF module footprints deliberately put the courtyard past the
                # board edge to expose the antenna to free space (WROOM-1 etc.).
                # Edge-mount footprints (SMA_Edge, USB_C vertical, MagJack,
                # microSD, BarrelJack, mounting holes, etc.) belong at the
                # board edge by design. Both demote the edge-clearance finding
                # to info with a hint.
                is_rf = _is_rf_module(fp)
                is_edge_mount = _is_edge_mount_footprint(fp)
                if is_off_board:
                    severity = 'warning'
                    rf_suffix = ''
                elif is_rf:
                    severity = 'info'
                    rf_suffix = (' (RF module antenna at board edge — '
                                 'verify antenna clearance, not a body collision)')
                elif is_edge_mount:
                    severity = 'info'
                    rf_suffix = (' (edge-mount footprint — by-design at board edge)')
                elif clearance < 0.5:
                    severity = 'error'
                    rf_suffix = ''
                else:
                    severity = 'warning'
                    rf_suffix = ''
                _summary = f"{fp['reference']} is {clearance}mm from board edge{rf_suffix}"
                _description = (f"Component {fp['reference']} on {fp['layer']} is only "
                                f"{clearance}mm from the board edge, risking damage "
                                f"during depaneling or handling.")
                _recommendation = (f"Move {fp['reference']} further from board edge "
                                   f"(currently {clearance}mm, recommend >= 1.0mm)")
                if is_off_board:
                    # KH-389: fully outside the outline — distinct from an
                    # overhang, never rendered as a negative distance.
                    _summary = (f"{fp['reference']} placed off-board "
                                f"({abs(clearance):.1f} mm outside outline)")
                    _description = (f"Component {fp['reference']} on {fp['layer']} has "
                                    f"its footprint entirely outside the board outline "
                                    f"({abs(clearance):.1f}mm outside), not merely "
                                    f"overhanging the edge.")
                    _recommendation = (f"Move {fp['reference']} onto the board — its "
                                       f"footprint currently lies completely outside "
                                       f"the outline.")
                elif clearance < 0:
                    # KH-344/KH-389: negative clearance means the courtyard
                    # overhangs the outline — "move further from edge" is
                    # nonsense there. Applies regardless of the RF/edge-mount
                    # exemption (those only demote severity, not the message).
                    _summary = (f"{fp['reference']} courtyard overhangs board "
                                f"edge by {abs(clearance)}mm")
                    _description = (f"Component {fp['reference']} on {fp['layer']} has "
                                    f"a courtyard extending {abs(clearance)}mm past the "
                                    f"board outline. If not intentional (castellated or "
                                    f"edge-mount part), it will collide with the edge.")
                    _recommendation = (f"Verify the overhang on {fp['reference']} is "
                                       f"intentional; if not, place it inside the outline.")
                edge_close.append({
                    "component": fp["reference"],
                    "layer": fp["layer"],
                    "edge_clearance_mm": clearance,
                    "detector": "analyze_placement",
                    "rule_id": "PM-002",
                    "category": "placement",
                    "severity": severity,
                    "confidence": "deterministic",
                    "evidence_source": "topology",
                    "summary": _summary,
                    "description": _description,
                    "components": [fp["reference"]],
                    "nets": [],
                    "pins": [],
                    "recommendation": _recommendation,
                    "report_context": {"section": "Placement", "impact": "manufacturability", "standard_ref": ""},
                })

    edge_close.sort(key=lambda e: e["edge_clearance_mm"])

    # Placement density
    board_area = None
    if bbox:
        board_area = bbox["width"] * bbox["height"]

    front_count = sum(1 for fp in footprints if fp["layer"] == "F.Cu")
    back_count = sum(1 for fp in footprints if fp["layer"] == "B.Cu")

    density: dict = {}
    if board_area and board_area > 0:
        density["board_area_cm2"] = round(board_area / 100.0, 2)
        if front_count:
            density["front_density_per_cm2"] = round(front_count / (board_area / 100.0), 1)
        if back_count:
            density["back_density_per_cm2"] = round(back_count / (board_area / 100.0), 1)

    result: dict = {"density": density}
    if overlaps:
        result["courtyard_overlaps"] = overlaps[:50]
        result["overlap_count"] = len(overlaps)
    if edge_close:
        result["edge_clearance_warnings"] = edge_close[:20]

    return result


def _extract_package_code(footprint_name: str) -> str:
    """Extract package size code from footprint library name.

    Recognizes patterns like:
    - "Capacitor_SMD:C_0402_1005Metric" -> "0402"
    - "Resistor_SMD:R_0201_0603Metric" -> "0201"
    - "Package_TO_SOT_SMD:SOT-23" -> ""
    """
    m = re.search(r'[_:](?:C|R|L)_(\d{4})_', footprint_name)
    if m:
        return m.group(1)
    # Also try bare pattern like "0402" or "0201" in the name
    m = re.search(r'(?:^|[_:])(\d{4})(?:_|$|Metric)', footprint_name)
    if m:
        code = m.group(1)
        if code in ("0201", "0402", "0603", "0805", "1206", "1210", "2512"):
            return code
    return ""


def analyze_tombstoning_risk(footprints: list[dict], tracks: dict,
                             vias: dict,
                             zones: list[dict] | None = None) -> list[dict]:
    """Tombstoning risk assessment for small passive components.

    Tombstoning occurs when thermal asymmetry during reflow causes one pad
    of a small passive to lift off. Common causes:
    - One pad connected to a ground pour (high thermal mass), other to a
      thin signal trace
    - Asymmetric track widths connected to each pad
    - Proximity to thermal vias or large copper areas on one side

    Focuses on 0201 and 0402 passives (highest risk due to small size).

    Returns a list of at-risk components with risk level and reason.
    """
    # EQ-056: d = √(Δx²+Δy²) (pad center asymmetry)
    # Identify small passive components
    small_passives = []
    for fp in footprints:
        if fp.get("dnp") or fp.get("board_only"):
            continue
        lib = fp.get("library", "")
        ref = fp.get("reference", "")
        # Must be a passive (C, R, L prefix)
        prefix = ""
        for c in ref:
            if c.isalpha():
                prefix += c
            else:
                break
        if prefix not in ("C", "R", "L"):
            continue

        pkg = _extract_package_code(lib)
        if pkg not in ("0201", "0402"):
            continue

        # Must have exactly 2 pads for tombstoning to apply
        pads = fp.get("pads", [])
        if len(pads) != 2:
            continue

        small_passives.append({
            "fp": fp,
            "package": pkg,
            "prefix": prefix,
        })

    if not small_passives:
        return []

    # Build net->zone mapping to identify ground pour connections
    zone_nets: set[int] = set()
    zone_net_layers: dict[int, set[str]] = {}
    if zones:
        for z in zones:
            zn = z.get("net", 0)
            if zn > 0:
                zone_nets.add(zn)
                for zl in z.get("layers", []):
                    zone_net_layers.setdefault(zn, set()).add(zl)

    # Build net->track width lookup from segments near each pad
    # For efficiency, build a lookup of track widths per net
    net_track_widths: dict[int, list[float]] = {}
    for seg in tracks.get("segments", []):
        net = seg["net"]
        if net > 0:
            net_track_widths.setdefault(net, []).append(seg["width"])
    for arc in tracks.get("arcs", []):
        net = arc["net"]
        if net > 0:
            net_track_widths.setdefault(net, []).append(arc["width"])

    # Analyze each small passive
    at_risk: list[dict] = []
    for sp in small_passives:
        fp = sp["fp"]
        pads = fp["pads"]
        pad_a = pads[0]
        pad_b = pads[1]

        net_a = pad_a.get("net_number", 0)
        net_b = pad_b.get("net_number", 0)
        net_name_a = pad_a.get("net_name", "")
        net_name_b = pad_b.get("net_name", "")

        risks: list[str] = []
        risk_level = "low"

        # Check 1: Ground pour asymmetry
        # If one pad is on a zone net and the other is not
        a_on_zone = net_a in zone_nets
        b_on_zone = net_b in zone_nets

        if a_on_zone != b_on_zone:
            # One pad has zone, the other doesn't — thermal asymmetry
            zone_pad = "pad 1" if a_on_zone else "pad 2"
            zone_net = net_name_a if a_on_zone else net_name_b
            risks.append(f"{zone_pad} connected to zone net ({zone_net}), "
                         f"other pad is signal-only — thermal asymmetry")
            risk_level = "high" if sp["package"] == "0201" else "medium"

        # Check 2: GND net on one pad, signal on other (common tombstone cause)
        a_is_gnd = is_ground_name(net_name_a)
        b_is_gnd = is_ground_name(net_name_b)
        if a_is_gnd != b_is_gnd:
            gnd_pad = "pad 1" if a_is_gnd else "pad 2"
            risks.append(f"{gnd_pad} is GND (likely ground pour), "
                         f"other pad is signal — thermal asymmetry risk")
            if risk_level == "low":
                risk_level = "medium"

        # Check 3: Track width asymmetry
        widths_a = net_track_widths.get(net_a, [])
        widths_b = net_track_widths.get(net_b, [])
        if widths_a and widths_b:
            avg_a = sum(widths_a) / len(widths_a)
            avg_b = sum(widths_b) / len(widths_b)
            if avg_a > 0 and avg_b > 0:
                ratio = max(avg_a, avg_b) / min(avg_a, avg_b)
                if ratio > 3.0:
                    risks.append(f"Track width asymmetry: pad 1 avg "
                                 f"{round(avg_a, 3)}mm vs pad 2 avg "
                                 f"{round(avg_b, 3)}mm (ratio {round(ratio, 1)}x)")
                    if risk_level == "low":
                        risk_level = "medium"

        # Check 4: Thermal via proximity (one pad near thermal vias)
        via_counts = [0, 0]
        for pad_idx, pad in enumerate([pad_a, pad_b]):
            px = pad.get("abs_x", fp["x"])
            py = pad.get("abs_y", fp["y"])
            for via in vias.get("vias", []):
                dx = via["x"] - px
                dy = via["y"] - py
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < 1.0:  # Within 1mm
                    via_counts[pad_idx] += 1

        if via_counts[0] != via_counts[1] and max(via_counts) >= 2:
            more_pad = "pad 1" if via_counts[0] > via_counts[1] else "pad 2"
            risks.append(f"{more_pad} has {max(via_counts)} nearby vias vs "
                         f"{min(via_counts)} on other pad — thermal asymmetry")
            if risk_level == "low":
                risk_level = "medium"

        if risks:
            at_risk.append({
                "component": fp["reference"],
                "value": fp.get("value", ""),
                "package": sp["package"],
                "layer": fp.get("layer", "F.Cu"),
                "risk_level": risk_level,
                "pad_1_net": net_name_a,
                "pad_2_net": net_name_b,
                "reasons": risks,
                "detector": "analyze_tombstoning_risk",
                "rule_id": "TB-001",
                "category": "dfm",
                "severity": "warning" if risk_level == "high" else "info",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"{fp['reference']} ({sp['package']}) tombstoning risk: {risk_level}",
                "description": f"{fp['reference']} ({sp['package']}, {fp.get('value', '')}) has {risk_level} tombstoning risk due to thermal asymmetry between pads.",
                "components": [fp["reference"]],
                "nets": [],
                "pins": [],
                "recommendation": "; ".join(risks),
                "report_context": {"section": "DFM", "impact": "assembly", "standard_ref": ""},
            })

    # Sort by risk level (high first)
    risk_order = {"high": 0, "medium": 1, "low": 2}
    at_risk.sort(key=lambda r: (risk_order.get(r["risk_level"], 3),
                                r["component"]))
    return at_risk


def _compute_switching_loop_areas(footprints: list, schematic_data: dict) -> list:
    """Compute hot loop triangle areas for switching regulators.

    Uses regulator refs from schematic + footprint positions from PCB.
    Returns list of {regulator_ref, regulator_value, inductor_ref, cap_ref,
    area_mm2, vertices_mm}.
    """
    regulators = [f for f in schematic_data.get('findings', [])
                  if f.get('detector') == 'detect_power_regulators']
    if not regulators:
        return []

    fp_pos = {}
    for fp in footprints:
        ref = fp.get('reference', '')
        if ref:
            fp_pos[ref] = (fp.get('x') or 0, fp.get('y') or 0)

    results = []
    for reg in regulators:
        topology = reg.get('topology', '').lower()
        if topology in ('ldo', 'linear', 'unknown', 'ic_with_internal_regulator',
                        'load_switch', 'charge_pump'):
            continue

        ref = reg.get('ref', reg.get('reference', ''))
        inductor_ref = reg.get('inductor')
        input_caps = reg.get('input_capacitors', [])

        if not inductor_ref or not input_caps:
            continue

        ic_pos = fp_pos.get(ref)
        ind_pos = fp_pos.get(inductor_ref)
        cap_ref = input_caps[0].get('ref', '') if isinstance(input_caps[0], dict) else str(input_caps[0])
        cap_pos = fp_pos.get(cap_ref)

        if not ic_pos or not ind_pos or not cap_pos:
            continue
        if ic_pos == (0, 0) or ind_pos == (0, 0) or cap_pos == (0, 0):
            continue

        # Shoelace formula for triangle area
        vertices = [cap_pos, ic_pos, ind_pos]
        area = 0.0
        n = len(vertices)
        for i in range(n):
            j = (i + 1) % n
            area += vertices[i][0] * vertices[j][1]
            area -= vertices[j][0] * vertices[i][1]
        area_mm2 = abs(area) / 2.0

        results.append({
            "regulator_ref": ref,
            "regulator_value": reg.get('value', ''),
            "inductor_ref": inductor_ref,
            "cap_ref": cap_ref,
            "area_mm2": round(area_mm2, 1),
            "vertices_mm": [list(v) for v in vertices],
        })

    return results


def _finest_smd_pad_dim(footprints: list[dict], side: str) -> float | None:
    """Return the smallest SMD pad dimension (width or height) on the given side.

    Uses pad 'width' and 'height' fields as a proxy for pad pitch — fine-pitch
    parts (BGA, fine-pitch QFN) have smaller pads. Returns None when no SMD
    pads with size data are found.
    """
    min_dim: float | None = None
    for fp in footprints:
        layer = fp.get("layer", "F.Cu")
        fp_side = layer if layer in ("F.Cu", "B.Cu") else "F.Cu"
        if fp_side != side:
            continue
        for pad in fp.get("pads", []):
            if pad.get("type") != "smd":
                continue
            w = pad.get("width")
            h = pad.get("height")
            if w is None or h is None:
                continue
            dim = min(float(w), float(h))
            if dim > 0 and (min_dim is None or dim < min_dim):
                min_dim = dim
    return min_dim


def _fiducial_severity_from_pitch(min_pad_dim: float | None) -> tuple[str, str]:
    """Return (severity, pitch_note) based on smallest SMD pad dimension.

    Thresholds use pad size as a proxy for pitch:
      <= 0.3 mm pad dim  -> likely BGA / fine-pitch QFN  -> 'error'
      <= 0.5 mm pad dim  -> medium pitch (SOT-563 etc.)  -> 'warning'
      >  0.5 mm or None  -> coarse pitch                 -> 'info'
    """
    if min_pad_dim is None:
        return "info", " (pad pitch unknown — coarse assumed)"
    if min_pad_dim <= 0.3:
        return "error", f" (finest pad dim {min_pad_dim:.2f}mm — BGA/fine-pitch QFN present)"
    if min_pad_dim <= 0.5:
        return "warning", f" (finest pad dim {min_pad_dim:.2f}mm — medium-pitch part present)"
    return "info", f" (finest pad dim {min_pad_dim:.2f}mm — coarse pitch only)"


def analyze_fiducials(footprints: list[dict]) -> dict:
    """FD-001: Check for assembly fiducial markers."""
    fiducials_by_side: dict[str, list[str]] = {"F.Cu": [], "B.Cu": []}
    smd_by_side: dict[str, int] = {"F.Cu": 0, "B.Cu": 0}

    for fp in footprints:
        ref = fp.get("reference", "")
        val = fp.get("value", "")
        if not isinstance(val, str):
            val = str(val)
        lib = (fp.get("library", "") + " " + val + " " + ref).lower()
        layer = fp.get("layer", "F.Cu")
        side = layer if layer in fiducials_by_side else "F.Cu"

        if any(k in lib for k in ("fiducial", "fid_", "fiducial_")):
            fiducials_by_side[side].append(ref)

        # Count SMD components per side
        pads = fp.get("pads", [])
        if any(p.get("type") == "smd" for p in pads):
            smd_by_side[side] = smd_by_side.get(side, 0) + 1

    findings: list[dict] = []
    for side, fids in fiducials_by_side.items():
        smd_count = smd_by_side.get(side, 0)
        if smd_count == 0:
            continue  # No SMD on this side, fiducials not required
        count = len(fids)
        if count >= 3:
            continue  # Adequate

        # Pitch-aware severity: use finest SMD pad dimension as pitch proxy
        min_pad_dim = _finest_smd_pad_dim(footprints, side)
        severity, pitch_note = _fiducial_severity_from_pitch(min_pad_dim)

        if count == 0:
            summary = f"No fiducials on {side} ({smd_count} SMD components){pitch_note}"
        else:
            summary = f"Only {count} fiducial(s) on {side} (need >= 3){pitch_note}"

        findings.append({
            "side": side,
            "fiducial_count": count,
            "fiducial_refs": fids,
            "smd_component_count": smd_count,
            "finest_smd_pad_dim_mm": min_pad_dim,
            "detector": "analyze_fiducials",
            "rule_id": "FD-001",
            "category": "assembly",
            "severity": severity,
            "confidence": "deterministic",
            "evidence_source": "topology",
            "summary": summary,
            "description": f"{side} has {count} fiducial(s) but {smd_count} SMD components. Assembly machines need >= 3 fiducials for accurate placement.",
            "components": fids,
            "nets": [],
            "pins": [],
            "recommendation": "Add fiducial markers for pick-and-place alignment (3 per side with SMD).",
            "report_context": {"section": "Assembly", "impact": "Pick-and-place alignment", "standard_ref": "IPC-7351"},
        })

    return {"findings": findings}


def analyze_test_point_coverage(footprints: list[dict], net_names: dict) -> dict:
    """TE-001: Check test point coverage across nets."""
    tp_nets: set[str] = set()
    for fp in footprints:
        ref = fp.get("reference", "")
        if not ref.upper().startswith("TP"):
            continue
        for pad in fp.get("pads", []):
            net = pad.get("net_name", "")
            if net:
                tp_nets.add(net)

    # Count signal nets (exclude power/ground)
    all_signal_nets = set()
    for net_id, name in net_names.items():
        if not name:
            continue
        n = name.upper()
        is_pg = n in ("GND", "VSS", "VDD", "VCC") or n.startswith(("+", "GND"))
        if not is_pg:
            all_signal_nets.add(name)

    total = len(all_signal_nets)
    covered = len(tp_nets & all_signal_nets)
    pct = (covered / total * 100) if total > 0 else 100

    if pct >= 95:
        severity = "info"
    elif pct >= 50:
        severity = "info"
    else:
        severity = "warning"

    finding = {
        "total_signal_nets": total,
        "nets_with_test_points": covered,
        "coverage_pct": round(pct, 1),
        "test_point_count": len([fp for fp in footprints if fp.get("reference", "").upper().startswith("TP")]),
        "detector": "analyze_test_point_coverage",
        "rule_id": "TE-001",
        "category": "testability",
        "severity": severity,
        "confidence": "deterministic",
        "evidence_source": "topology",
        "summary": f"Test point coverage: {covered}/{total} nets ({pct:.0f}%)",
        "description": f"{covered} of {total} signal nets have test points ({pct:.0f}% coverage).",
        "components": [],
        "nets": [],
        "pins": [],
        "recommendation": "Add test points to improve ICT/flying probe coverage." if pct < 95 else "",
        "report_context": {"section": "Testability", "impact": "ICT accessibility", "standard_ref": ""},
    }

    return finding


def analyze_orientation_consistency(footprints: list[dict]) -> list[dict]:
    """OR-001: Check passive component orientation consistency per board side."""
    from collections import Counter

    findings: list[dict] = []
    passives_by_side: dict[str, list[tuple[str, float]]] = {}

    for fp in footprints:
        ref = fp.get("reference", "")
        # Only check passives (R, C, L with 2 pads)
        if not ref or ref[0] not in ("R", "C", "L"):
            continue
        pads = fp.get("pads", [])
        if len(pads) != 2:
            continue
        layer = fp.get("layer", "F.Cu")
        angle = fp.get("angle", 0) or 0
        # Normalize angle to 0-179 range (0 and 180 are same orientation)
        norm_angle = round(angle % 180)
        passives_by_side.setdefault(layer, []).append((ref, norm_angle))

    for side, components in passives_by_side.items():
        if len(components) < 5:
            continue  # Too few to judge consistency

        angles = Counter(a for _, a in components)
        majority_angle, majority_count = angles.most_common(1)[0]
        deviators = [(ref, a) for ref, a in components if a != majority_angle]

        if not deviators:
            continue

        deviation_pct = len(deviators) / len(components) * 100
        if deviation_pct < 10:
            continue  # Minor inconsistency, not worth flagging

        findings.append({
            "side": side,
            "total_passives": len(components),
            "majority_angle": majority_angle,
            "majority_count": majority_count,
            "deviator_count": len(deviators),
            "deviator_refs": [ref for ref, _ in deviators[:20]],
            "detector": "analyze_orientation_consistency",
            "rule_id": "OR-001",
            "category": "assembly",
            "severity": "info",
            "confidence": "heuristic",
            "evidence_source": "topology",
            "summary": f"Orientation: {len(deviators)} passives on {side} deviate from {majority_angle} deg majority",
            "description": f"{len(deviators)} of {len(components)} passives on {side} are not at the majority {majority_angle} deg orientation.",
            "components": [ref for ref, _ in deviators[:20]],
            "nets": [],
            "pins": [],
            "recommendation": "Align passive component orientations for consistent pick-and-place.",
            "report_context": {"section": "Assembly", "impact": "Pick-and-place efficiency", "standard_ref": ""},
        })

    return findings


def analyze_silkscreen_pad_overlaps(footprints: list[dict], board_texts: list[dict]) -> list[dict]:
    """SK-001: Check for silkscreen text overlapping exposed pads."""
    findings: list[dict] = []

    # Collect all exposed pad bboxes (SMD pads on front/back)
    pad_bboxes: list[tuple[str, str, float, float, float, float]] = []
    for fp in footprints:
        ref = fp.get("reference", "")
        for pad in fp.get("pads", []):
            if pad.get("type") != "smd":
                continue
            px = pad.get("abs_x")
            py = pad.get("abs_y")
            if px is None or py is None:
                continue
            hw = pad.get("width", 0) / 2
            hh = pad.get("height", 0) / 2
            if hw <= 0 or hh <= 0:
                continue
            layers = pad.get("layers", [])
            for layer in layers:
                if ".Cu" in layer:
                    silk_layer = "F.SilkS" if "F." in layer else "B.SilkS"
                    pad_bboxes.append((ref, silk_layer, px - hw, py - hh, px + hw, py + hh))

    if not pad_bboxes:
        return findings

    # Check board-level silkscreen texts against pad bboxes
    flagged_refs: set[str] = set()
    for text_entry in board_texts:
        tx = text_entry.get("x")
        ty = text_entry.get("y")
        tlayer = text_entry.get("layer", "")
        if tx is None or ty is None:
            continue
        if "SilkS" not in tlayer and "Silkscreen" not in tlayer:
            continue
        for ref, silk_layer, x1, y1, x2, y2 in pad_bboxes:
            if ref in flagged_refs:
                continue
            if silk_layer.startswith(tlayer[0]):  # Same side (F/B)
                if x1 <= tx <= x2 and y1 <= ty <= y2:
                    flagged_refs.add(ref)
                    findings.append({
                        "component": ref,
                        "silk_layer": tlayer,
                        "detector": "analyze_silkscreen_pad_overlaps",
                        "rule_id": "SK-001",
                        "category": "dfm",
                        "severity": "warning",
                        "confidence": "heuristic",
                        "evidence_source": "topology",
                        "summary": f"Silkscreen overlaps pad on {ref} ({tlayer})",
                        "description": f"Silkscreen text on {tlayer} overlaps an exposed SMD pad on {ref}.",
                        "components": [ref],
                        "nets": [],
                        "pins": [],
                        "recommendation": f"Move silkscreen text away from exposed pads on {ref}.",
                        "report_context": {"section": "DFM", "impact": "Solder paste/solder joint interference", "standard_ref": ""},
                    })

    return findings


def analyze_keepout_violations(footprints: list[dict], vias: dict,
                                keepout_zones: list[dict]) -> list[dict]:
    """KO-001: Check for components or vias inside keepout zones (bbox check)."""
    findings: list[dict] = []
    if not keepout_zones:
        return findings

    via_list = vias.get("vias", [])

    for kz in keepout_zones:
        bbox = kz.get("bounding_box")
        if not bbox or len(bbox) < 4:
            continue
        kx1, ky1, kx2, ky2 = bbox[0], bbox[1], bbox[2], bbox[3]
        restrictions = kz.get("restrictions", {})
        kz_name = kz.get("name", "unnamed")
        kz_layers = kz.get("layers", [])
        # KiCad rule-area "allowed net" — items on this net are ALLOWED
        # inside the keepout (e.g., an antenna keepout that excludes copper
        # except the antenna's own net). 0 / "" / None means "no exemption,
        # restrict all items". rc.2 4.1 expansion (SparkFun review).
        kz_allowed_net_id = kz.get("net") or 0
        kz_allowed_net_name = kz.get("net_name") or ""

        # Check footprints
        if restrictions.get("footprints", False):
            for fp in footprints:
                ref = fp.get("reference", "")
                fx = fp.get("x", 0)
                fy = fp.get("y", 0)
                fp_layer = fp.get("layer", "")
                if not any(l in kz_layers or l == "*" or "*.Cu" in kz_layers for l in [fp_layer]):
                    continue
                if kx1 <= fx <= kx2 and ky1 <= fy <= ky2:
                    # Net exclusion: if any pad of this footprint is on the
                    # keepout's allowed net, the footprint is permitted here.
                    if kz_allowed_net_name:
                        fp_nets = fp.get("connected_nets", []) or list(
                            (fp.get("pad_nets") or {}).values())
                        # pad_nets values are dicts with 'net' key; connected_nets is strings
                        fp_net_names = set()
                        for n in fp_nets:
                            if isinstance(n, str):
                                fp_net_names.add(n)
                            elif isinstance(n, dict) and n.get("net"):
                                fp_net_names.add(n["net"])
                        if kz_allowed_net_name in fp_net_names:
                            continue
                    findings.append({
                        "component": ref,
                        "keepout_name": kz_name,
                        "keepout_layers": kz_layers,
                        "keepout_allowed_net": kz_allowed_net_name,
                        "detector": "analyze_keepout_violations",
                        "rule_id": "KO-001",
                        "category": "placement",
                        "severity": "error",
                        "confidence": "heuristic",
                        "evidence_source": "topology",
                        "summary": f"Keepout violation: {ref} inside keepout zone{' ' + kz_name if kz_name != 'unnamed' else ''}",
                        "description": f"Component {ref} center is inside keepout zone {kz_name} (bbox check).",
                        "components": [ref],
                        "nets": [],
                        "pins": [],
                        "recommendation": f"Move {ref} outside the keepout zone.",
                        "report_context": {"section": "Placement", "impact": "Design rule violation", "standard_ref": ""},
                    })

        # Check vias
        if restrictions.get("vias", False):
            for via in via_list:
                vx = via.get("x")
                vy = via.get("y")
                if vx is None or vy is None:
                    continue
                if kx1 <= vx <= kx2 and ky1 <= vy <= ky2:
                    # Net exclusion: a via on the keepout's allowed net is
                    # permitted (e.g., an antenna trace's tuning via inside
                    # the antenna keepout).
                    if kz_allowed_net_id:
                        via_net_id = via.get("net")
                        if via_net_id == kz_allowed_net_id:
                            continue
                    findings.append({
                        "via_x": round(vx, 2),
                        "via_y": round(vy, 2),
                        "keepout_name": kz_name,
                        "keepout_allowed_net": kz_allowed_net_name,
                        "detector": "analyze_keepout_violations",
                        "rule_id": "KO-001",
                        "category": "placement",
                        "severity": "error",
                        "confidence": "heuristic",
                        "evidence_source": "topology",
                        "summary": f"Keepout violation: via at ({round(vx, 1)}, {round(vy, 1)}) inside keepout{' ' + kz_name if kz_name != 'unnamed' else ''}",
                        "description": f"Via at ({round(vx, 2)}, {round(vy, 2)}) is inside keepout zone {kz_name} (bbox check).",
                        "components": [],
                        "nets": [],
                        "pins": [],
                        "recommendation": "Move via outside the keepout zone.",
                        "report_context": {"section": "Placement", "impact": "Design rule violation", "standard_ref": ""},
                    })

    return findings[:50]
