#!/usr/bin/env python3
"""
KiCad PCB Layout Analyzer — comprehensive single-pass extraction.

Parses a .kicad_pcb file and outputs structured JSON with:
- Board dimensions and layer stack
- Footprint inventory (components, positions, pads, nets)
- Routing analysis (tracks, vias, zones)
- Net connectivity and unrouted nets
- Design rule summary
- Statistics

Usage:
    python analyze_pcb.py <file.kicad_pcb|file.kicad_pro|dir/> [--output file.json]
"""

import heapq
import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import re

from sexp_parser import (
    find_all,
    find_first,
    get_at,
    get_property,
    get_value,
    parse_file,
)
from kicad_utils import (is_ground_name, is_power_net_name,
                         load_kicad_pro, extract_pro_net_classes,
                         extract_pro_design_rules, extract_pro_text_variables,
                         load_kicad_dru, load_lib_tables)
from pcb_connectivity import build_connectivity_graph
from finding_schema import compute_trust_summary, sort_findings, assign_finding_ids
from envelopes.pcb import PCBEnvelope
from schema_codec import emit_schema
from inputs_builder import build_inputs, build_compat
from capability_mode import get_capability_mode_ref

ANALYZER_SOURCE = "pcb"

# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _extract_polygon_coords(pts_node: list) -> list[tuple[float, float]]:
    """Extract (x, y) coordinate tuples from a (pts (xy x y) ...) node."""
    return [(float(xy[1]), float(xy[2])) for xy in find_all(pts_node, "xy")]


def _shoelace_area_from_coords(coords: list[tuple[float, float]]) -> float:
    """Compute polygon area from coordinate list using shoelace formula."""
    n = len(coords)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += coords[i][0] * coords[j][1] - coords[j][0] * coords[i][1]
    return abs(area) / 2.0


def _shoelace_area(pts_node: list) -> float:
    """Compute polygon area from a (pts (xy x y) ...) S-expression node.

    Returns positive area in mm².
    """
    return _shoelace_area_from_coords(_extract_polygon_coords(pts_node))


def _point_in_polygon(px: float, py: float,
                      polygon: list[tuple[float, float]]) -> bool:
    """Ray-casting point-in-polygon test.

    Returns True if point (px, py) is inside the polygon defined by
    a list of (x, y) vertices.
    """
    n = len(polygon)
    if n < 3:
        return False
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > py) != (yj > py)) and \
                (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _polygon_bbox(
    coords: list[tuple[float, float]],
) -> tuple[float, float, float, float]:
    """Compute bounding box of a polygon.

    Returns (min_x, min_y, max_x, max_y).
    """
    xs = [p[0] for p in coords]
    ys = [p[1] for p in coords]
    return (min(xs), min(ys), max(xs), max(ys))


class ZoneFills:
    """Spatial index for zone filled polygon data.

    Stores filled polygon coordinates extracted during zone parsing.
    Used for point-in-polygon queries to determine actual copper presence
    at specific locations. Not included in JSON output (coordinates are
    too large — often thousands of vertices per fill region).

    Requires that zones have been filled in KiCad (Edit → Fill All Zones)
    before the PCB file was saved. Stale fills will produce incorrect results.
    """

    def __init__(self) -> None:
        self._fills: list[
            tuple[int, int, str, list[tuple[float, float]],
                  tuple[float, float, float, float]]
        ] = []
        self._next_fill_id = 0

    def add(self, zone_idx: int, layer: str,
            coords: list[tuple[float, float]]) -> None:
        """Register a filled polygon region for spatial queries."""
        bbox = _polygon_bbox(coords)
        fill_id = self._next_fill_id
        self._next_fill_id += 1
        self._fills.append((fill_id, zone_idx, layer, coords, bbox))

    @property
    def has_data(self) -> bool:
        """True if any filled polygon data was loaded."""
        return len(self._fills) > 0

    def zones_at_point(self, x: float, y: float, layer: str,
                       zones: list[dict]) -> list[dict]:
        """Return zone dicts that have filled copper at (x, y) on layer."""
        results = []
        seen: set[int] = set()
        for _fill_id, zone_idx, fill_layer, coords, bbox in self._fills:
            if fill_layer != layer or zone_idx in seen:
                continue
            # Fast bounding box rejection
            if x < bbox[0] or x > bbox[2] or y < bbox[1] or y > bbox[3]:
                continue
            if _point_in_polygon(x, y, coords):
                results.append(zones[zone_idx])
                seen.add(zone_idx)
        return results

    def fill_regions_at_point(self, x: float, y: float, layer: str,
                              zones: list[dict],
                              *,
                              net_name: str | None = None) -> list[tuple[int, int]]:
        """Return ``(fill_id, zone_idx)`` regions containing the point."""
        results: list[tuple[int, int]] = []
        for fill_id, zone_idx, fill_layer, coords, bbox in self._fills:
            if fill_layer != layer:
                continue
            if x < bbox[0] or x > bbox[2] or y < bbox[1] or y > bbox[3]:
                continue
            if not _point_in_polygon(x, y, coords):
                continue
            if net_name is not None and zones[zone_idx].get("net_name", "") != net_name:
                continue
            results.append((fill_id, zone_idx))
        return results

    def has_copper_at(self, x: float, y: float, layer: str) -> bool:
        """Check if any zone has filled copper at (x, y) on layer."""
        for _fill_id, _zone_idx, fill_layer, coords, bbox in self._fills:
            if fill_layer != layer:
                continue
            if x < bbox[0] or x > bbox[2] or y < bbox[1] or y > bbox[3]:
                continue
            if _point_in_polygon(x, y, coords):
                return True
        return False

    def zone_nets_at_point(self, x: float, y: float, layer: str,
                           zones: list[dict]) -> list[str]:
        """Return net names of zones with filled copper at (x, y) on layer."""
        return [z["net_name"] for z in self.zones_at_point(x, y, layer, zones)
                if z.get("net_name")]


def _dist_point_to_segment(px, py, x1, y1, x2, y2):
    """Distance from point (px, py) to line segment (x1,y1)-(x2,y2)."""
    # EQ-098: d = min(||P - (A + t(B-A))||) with t clamped to [0,1]
    # Source: Self-evident — 2D point-to-segment distance (project, clamp, Euclidean).
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    proj_x, proj_y = x1 + t * dx, y1 + t * dy
    return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)


class CopperPresence:
    """Unified copper presence check across zones, tracks, and pads.

    Given a point (x, y) on a given layer, returns True if any copper
    object is within radius_mm.  Credits zone fills, track segments, and
    pads equally -- all provide valid return-current paths.

    Replaces bare ``ZoneFills.has_copper_at`` point-in-polygon checks
    that hit false negatives in KiCad zone fills (clearance channels
    carved around every track/pad make the filled polygon "swiss cheese";
    a sample point landing inside a clearance channel reports "no copper"
    even when GND fill is < 1 mm away).
    """

    def __init__(self, zone_fills, tracks_segments, footprints):
        self.zone_fills = zone_fills

        # Index track segments by layer for fast lookup
        self._tracks_by_layer = {}
        for seg in tracks_segments or []:
            layer = seg.get('layer')
            if layer:
                self._tracks_by_layer.setdefault(layer, []).append(seg)

        # Index pads by layer -- use absolute position (abs_x, abs_y)
        # and size (width, height) from extract_footprints() output
        self._pads_by_layer = {}
        for fp in footprints or []:
            for pad in fp.get('pads') or []:
                layers = pad.get('layers') or []
                px = pad.get('abs_x')
                py_val = pad.get('abs_y')
                if px is None or py_val is None:
                    continue
                pw = pad.get('width', 0)
                ph = pad.get('height', 0)
                for lyr in layers:
                    self._pads_by_layer.setdefault(lyr, []).append(
                        (px, py_val, pw, ph))

    # EQ-099: Perimeter sample at (x + r·cos(iπ/4), y + r·sin(iπ/4)) for i=0..7
    # Source: Self-evident — 8-point circle sampling at 45° intervals.
    def has_coverage_near(self, x, y, layer, *, radius_mm=0.5):
        """True if any copper on *layer* is within *radius_mm* of (x, y).

        Checks zone fills (center + 8-point perimeter), tracks, and pads.
        """
        zf = self.zone_fills
        if zf is not None and zf.has_data:
            # Center point -- fast path
            if zf.has_copper_at(x, y, layer):
                return True
            # 8-point perimeter at radius_mm
            for i in range(8):
                ang = i * math.pi / 4.0
                px = x + radius_mm * math.cos(ang)
                py = y + radius_mm * math.sin(ang)
                if zf.has_copper_at(px, py, layer):
                    return True

        # Track segments on this layer within radius
        for seg in self._tracks_by_layer.get(layer, []):
            half_w = seg.get('width', 0) / 2.0
            d = _dist_point_to_segment(
                x, y,
                seg.get('x1', 0), seg.get('y1', 0),
                seg.get('x2', 0), seg.get('y2', 0),
            )
            if d <= radius_mm + half_w:
                return True

        # Pads on this layer within radius
        for (pad_x, pad_y, pw, ph) in self._pads_by_layer.get(layer, []):
            half_diag = math.sqrt((pw / 2) ** 2 + (ph / 2) ** 2) if pw and ph else 0
            d = math.sqrt((x - pad_x) ** 2 + (y - pad_y) ** 2)
            if d <= radius_mm + half_diag:
                return True

        return False


def copper_connected(p1: tuple[float, float],
                     p2: tuple[float, float],
                     net: str,
                     layer: str,
                     zone_fills: "ZoneFills",
                     zones: list[dict],
                     *,
                     samples: int = 20) -> bool | None:
    """Check whether two points are joined by continuous same-net copper.

    Uses line-segment sampling through the ``ZoneFills`` spatial index to
    determine if a path between ``p1`` and ``p2`` stays entirely within a
    filled zone on ``net`` and ``layer``. This is a cheap approximation
    of a full copper connectivity graph — sufficient for verifying that
    a via near a thermal pad is actually copper-connected (fillet, flood,
    or cluster pattern) rather than sitting across a clearance slot.

    Args:
        p1: (x, y) of the first point in board coordinates (mm).
        p2: (x, y) of the second point in board coordinates (mm).
        net: Net name both points must share (e.g., "GND", "+3V3").
        layer: Copper layer name (e.g., "F.Cu", "B.Cu", "In1.Cu").
        zone_fills: ZoneFills spatial index from the PCB parser.
        zones: The full zone list the ZoneFills index was built from
            (needed for looking up net names attached to filled regions).
            Must be the same list returned alongside the ZoneFills
            instance during PCB parsing — mismatched pairs produce an
            IndexError deep inside ZoneFills.zones_at_point.
        samples: Number of sample points to test along the line segment,
            including both endpoints. Default 20 gives ~0.26 mm spacing
            on a 5 mm path (5 mm / 19 gaps). Increase for longer paths
            or tighter geometry; decrease for very short distances to
            save work.

    Returns:
        ``True`` if every sampled point along the segment lies in a filled
            zone whose net name matches ``net`` on ``layer``.
        ``False`` if any sample point is outside a same-net filled zone on
            ``layer`` (i.e., verified disconnected at least at that sample).
        ``None`` if the zone fill data is not available — the caller
            cannot distinguish connected from disconnected and should
            fall back to a proximity heuristic or skip the check.

    Limitations (document for consumers):
        - **Thermal relief clearances** can cause false negatives: a
          sample point might land inside the cross-shaped cutout of a
          thermal relief pattern rather than in the surrounding flood,
          even though the pad is electrically connected via the four
          spokes. Consumers that care about thermal-relief patterns
          should use more samples and/or accept a majority-pass rule
          rather than strict all-pass.
        - **Single-layer only.** Does not traverse vias to check
          cross-layer continuity. A pad connected to an inner plane
          through a via will look disconnected from a point on the
          outer layer even if the electrical path is valid. For
          cross-layer continuity verification, use this helper in
          combination with via-layer traversal logic.
        - **Linear sampling.** The function samples along a straight
          line between ``p1`` and ``p2``. Paths that curve around
          obstacles (e.g., a trace that routes around a keep-out) will
          be reported disconnected even though the copper is continuous
          along the routed path. For proximity-style checks (within a
          few mm), linear sampling is appropriate; for long-distance
          connectivity, use a different algorithm.
    """
    if not zone_fills.has_data:
        return None

    if samples < 2:
        samples = 2

    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1

    for i in range(samples):
        t = i / (samples - 1)
        sx = x1 + t * dx
        sy = y1 + t * dy
        nets_at_point = zone_fills.zone_nets_at_point(sx, sy, layer, zones)
        if net not in nets_at_point:
            return False

    return True


def _arc_length_3pt(sx: float, sy: float, mx: float, my: float,
                    ex: float, ey: float) -> float:
    """Compute arc length from three points (start, mid, end) on a circle."""
    # EQ-044: arc = R × θ from circumcircle (3-point arc length)
    D = 2.0 * (sx * (my - ey) + mx * (ey - sy) + ex * (sy - my))
    if abs(D) < 1e-10:
        # Collinear — treat as straight line
        return math.sqrt((ex - sx) ** 2 + (ey - sy) ** 2)

    ss = sx * sx + sy * sy
    ms = mx * mx + my * my
    es = ex * ex + ey * ey
    ux = (ss * (my - ey) + ms * (ey - sy) + es * (sy - my)) / D
    uy = (ss * (ex - mx) + ms * (sx - ex) + es * (mx - sx)) / D
    R = math.sqrt((sx - ux) ** 2 + (sy - uy) ** 2)

    a_s = math.atan2(sy - uy, sx - ux)
    a_m = math.atan2(my - uy, mx - ux)
    a_e = math.atan2(ey - uy, ex - ux)

    # Normalize angles relative to start
    def _norm(a: float) -> float:
        # EQ-047: Angle normalization to [0, 2π)
        a = (a - a_s) % (2.0 * math.pi)
        return a

    nm = _norm(a_m)
    ne = _norm(a_e)

    # Arc from start to end: two possible arcs (CCW ne, or CW 2π-ne).
    # Choose the one containing mid.
    if ne > 0 and 0 < nm < ne:
        arc_angle = ne
    elif ne > 0:
        arc_angle = 2.0 * math.pi - ne
    else:
        arc_angle = 2.0 * math.pi  # full circle edge case
    return R * arc_angle


def extract_layers(root: list) -> list[dict]:
    """Extract layer definitions."""
    layers_node = find_first(root, "layers")
    if not layers_node:
        return []

    layers = []
    for item in layers_node[1:]:
        if isinstance(item, list) and len(item) >= 3:
            layers.append({
                "number": int(item[0]) if str(item[0]).isdigit() else item[0],
                "name": item[1],
                "type": item[2],
                "alias": item[3] if len(item) > 3 and isinstance(item[3], str) else None,
            })
    return layers


def extract_setup(root: list) -> dict:
    """Extract board setup, stackup, and design rules."""
    setup_node = find_first(root, "setup")
    if not setup_node:
        return {}

    result = {}

    # Board thickness
    general = find_first(root, "general")
    if general:
        thickness = get_value(general, "thickness")
        if thickness:
            result["board_thickness_mm"] = float(thickness)

    # Stackup
    stackup = find_first(setup_node, "stackup")
    if stackup:
        stack_layers = []
        _NUMERIC_STACKUP_KEYS = {"thickness", "epsilon_r", "loss_tangent"}
        for layer in find_all(stackup, "layer"):
            layer_info = {"name": layer[1] if len(layer) > 1 else ""}
            for item in layer[2:]:
                if isinstance(item, list) and len(item) >= 2:
                    key, val = item[0], item[1]
                    if key in _NUMERIC_STACKUP_KEYS:
                        try:
                            val = float(val)
                        except (ValueError, TypeError):
                            pass
                    layer_info[key] = val
            stack_layers.append(layer_info)
        result["stackup"] = stack_layers

    # Design rules from setup
    _float_keys = [
        "pad_to_mask_clearance", "solder_mask_min_width",
        "pad_to_paste_clearance",
    ]
    for key in _float_keys:
        val = get_value(setup_node, key)
        if val:
            result[key] = float(val)

    # Paste clearance ratio
    pcr = get_value(setup_node, "pad_to_paste_clearance_ratio")
    if pcr:
        result["pad_to_paste_clearance_ratio"] = float(pcr)

    # Copper finish from stackup
    if stackup:
        cf = get_value(stackup, "copper_finish")
        if cf:
            result["copper_finish"] = cf
        dc = get_value(stackup, "dielectric_constraints")
        if dc:
            result["dielectric_constraints"] = dc

    # Legacy teardrops flag
    if general:
        lt = get_value(general, "legacy_teardrops")
        if lt:
            result["legacy_teardrops"] = lt

    # Soldermask bridges
    smb = get_value(setup_node, "allow_soldermask_bridges_in_footprints")
    if smb:
        result["allow_soldermask_bridges"] = smb

    # Design rules from pcbplotparams or design_settings (varies by version)
    # KiCad 9 stores rules in the .kicad_pro file, but some appear in the PCB
    # under (setup (design_settings ...)) or directly
    ds = find_first(setup_node, "design_settings") or setup_node
    for key in ["min_clearance", "min_track_width", "min_via_diameter",
                "min_via_drill", "min_uvia_diameter", "min_uvia_drill",
                "min_through_hole_pad", "min_hole_clearance"]:
        val = get_value(ds, key)
        if val:
            result.setdefault("design_rules", {})[key] = float(val)

    return result


def extract_nets(root: list) -> dict[int, str]:
    """Extract net declarations.

    KiCad ≤9: top-level (net number "name") declarations.
    KiCad 10: no declarations — call _build_net_mapping() after extraction.
    """
    nets = {}
    for item in root:
        if isinstance(item, list) and len(item) >= 3 and item[0] == "net":
            try:
                net_num = int(item[1])
            except (ValueError, TypeError):
                continue  # KiCad 10 has no numeric net declarations
            net_name = item[2]
            nets[net_num] = net_name
    return nets


# KiCad 10 net format helpers — nets are identified by name, not number.
_net_name_to_id: dict[str, int] = {}


def _net_id(val: str | None) -> int:
    """Convert a net value to an integer ID.

    KiCad ≤9: val is a numeric string like "3" → returns 3.
    KiCad 10: val is a net name like "+3.3V" → looks up synthetic ID.
    """
    if not val:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return _net_name_to_id.get(val, 0)


def _build_net_mapping(footprints: list[dict], tracks: dict, vias: dict,
                       zones: list[dict]) -> dict[int, str]:
    """Build synthetic net ID mapping for KiCad 10 (no net declarations).

    Scans all pads, tracks, vias, and zones for unique net names and assigns
    sequential integer IDs. Returns the same dict[int, str] format as
    extract_nets() for backward compatibility.
    """
    global _net_name_to_id
    names: set[str] = set()
    for fp in footprints:
        for pad in fp.get("pads", []):
            n = pad.get("net_name", "")
            if n:
                names.add(n)
    for seg in tracks.get("segments", []):
        n = seg.get("_net_name", "")
        if n:
            names.add(n)
    for arc in tracks.get("arcs", []):
        n = arc.get("_net_name", "")
        if n:
            names.add(n)
    for v in vias.get("vias", []):
        n = v.get("_net_name", "")
        if n:
            names.add(n)
    for z in zones:
        n = z.get("net_name", "")
        if n:
            names.add(n)
    # Assign sequential IDs (0 = unconnected, 1+ = real nets)
    net_names: dict[int, str] = {0: ""}
    _net_name_to_id = {"": 0}
    for i, name in enumerate(sorted(names), start=1):
        net_names[i] = name
        _net_name_to_id[name] = i
    return net_names


def extract_footprints(root: list) -> list[dict]:
    """Extract all placed footprints with pad details.

    Handles both KiCad 6+ (footprint ...) and KiCad 5 (module ...) formats.
    """
    # EQ-060: x'=x·cosθ-y·sinθ, y'=x·sinθ+y·cosθ (2D rotation)
    footprints = []

    # KiCad 6+: (footprint ...), KiCad 5: (module ...)
    fp_nodes = find_all(root, "footprint") or find_all(root, "module")

    for fp in fp_nodes:
        fp_lib = fp[1] if len(fp) > 1 else ""
        at = get_at(fp)
        x, y, angle = at if at else (0, 0, 0)

        layer = get_value(fp, "layer") or "F.Cu"

        # KiCad 6+: (property "Reference" "R1"), KiCad 5: (fp_text reference "R1")
        ref = get_property(fp, "Reference") or ""
        value = get_property(fp, "Value") or ""
        if not ref:
            for ft in find_all(fp, "fp_text"):
                if len(ft) >= 3:
                    if ft[1] == "reference":
                        # Some footprints have no text after the field name —
                        # ft[2] is then an attribute s-expression, not a string.
                        # Coerce to empty string in that case (KH-326).
                        ref = ft[2] if isinstance(ft[2], str) else ""
                    elif ft[1] == "value":
                        value = ft[2] if isinstance(ft[2], str) else ""

        mpn = get_property(fp, "MPN") or get_property(fp, "Mfg Part") or ""

        # Determine SMD vs through-hole + extended attributes
        attr_node = find_first(fp, "attr")
        attr_flags: list[str] = []
        if attr_node and len(attr_node) > 1:
            attr_flags = [a for a in attr_node[1:] if isinstance(a, str)]
            attr = attr_flags[0] if attr_flags else "smd"
        else:
            # Infer from pad types if attr not present (KiCad 5)
            has_tht = any(p[2] == "thru_hole" for p in find_all(fp, "pad") if len(p) > 2)
            attr = "through_hole" if has_tht else "smd"
            # KiCad 5 uses "virtual" for board-only items
            if attr_node and len(attr_node) > 1 and attr_node[1] == "virtual":
                attr = "smd"
                attr_flags = ["virtual"]

        is_dnp = "dnp" in attr_flags
        is_board_only = "board_only" in attr_flags or "virtual" in attr_flags
        exclude_from_bom = "exclude_from_bom" in attr_flags or is_board_only
        exclude_from_pos = "exclude_from_pos_files" in attr_flags or is_board_only

        # Schematic cross-reference (KiCad 6+)
        sch_path = get_value(fp, "path") or ""
        sch_sheetname = get_value(fp, "sheetname") or ""
        sch_sheetfile = get_value(fp, "sheetfile") or ""

        # Net tie pad groups
        net_tie_node = find_first(fp, "net_tie_pad_groups")
        net_tie_groups = None
        if net_tie_node and len(net_tie_node) > 1:
            net_tie_groups = net_tie_node[1]

        # Extended properties (MPN, manufacturer, etc.)
        manufacturer = get_property(fp, "Manufacturer") or ""
        digikey_pn = get_property(fp, "DigiKey Part") or ""
        description = get_property(fp, "Description") or ""

        # 3D model references
        models = []
        for model in find_all(fp, "model"):
            if len(model) > 1:
                models.append(model[1])

        # Extract pads
        pads = []
        for pad in find_all(fp, "pad"):
            if len(pad) < 4:
                continue
            pad_num = pad[1]
            pad_type = pad[2]  # smd, thru_hole, np_thru_hole
            pad_shape = pad[3]  # circle, rect, oval, roundrect, custom

            pad_at = get_at(pad)
            pad_size = find_first(pad, "size")
            pad_drill = find_first(pad, "drill")
            pad_net = find_first(pad, "net")
            pad_layers = find_first(pad, "layers")

            pad_info = {
                "number": pad_num,
                "type": pad_type,
                "shape": pad_shape,
            }

            if pad_at:
                # Pad position is relative to footprint; compute absolute
                px, py = pad_at[0], pad_at[1]
                pad_angle = pad_at[2]
                # KiCad PCB footprint rotations are clockwise in board coords.
                # Use the negative angle to map local pad offsets into absolute
                # board space; using +angle mirrors rotated footprints.
                if angle != 0:
                    rad = math.radians(-angle)
                    rpx = px * math.cos(rad) - py * math.sin(rad)
                    rpy = px * math.sin(rad) + py * math.cos(rad)
                    px, py = rpx, rpy
                pad_info["abs_x"] = round(x + px, 4)
                pad_info["abs_y"] = round(y + py, 4)
                if pad_angle != 0:
                    pad_info["angle"] = pad_angle

            if pad_size and len(pad_size) >= 3:
                pad_info["width"] = float(pad_size[1])
                pad_info["height"] = float(pad_size[2])

            if pad_drill and len(pad_drill) >= 2:
                # Drill can be (drill D) or (drill oval W H) or (drill D (offset X Y))
                drill_val = pad_drill[1]
                if drill_val == "oval" and len(pad_drill) >= 3:
                    pad_info["drill_shape"] = "oval"
                    pad_info["drill"] = float(pad_drill[2])
                    if len(pad_drill) >= 4 and isinstance(pad_drill[3], str):
                        pad_info["drill_h"] = float(pad_drill[3])
                else:
                    try:
                        pad_info["drill"] = float(drill_val)
                    except (ValueError, TypeError):
                        pass  # skip malformed drill entries

            if pad_net and len(pad_net) >= 3:
                # KiCad ≤9: (net number "name")
                pad_info["net_number"] = _net_id(pad_net[1])
                pad_info["net_name"] = pad_net[2]
            elif pad_net and len(pad_net) == 2:
                # KiCad 10: (net "name") — no numeric ID
                pad_info["net_name"] = pad_net[1]
                pad_info["net_number"] = _net_id(pad_net[1])

            if pad_layers and len(pad_layers) > 1:
                pad_info["layers"] = [l for l in pad_layers[1:] if isinstance(l, str)]

            # Pin function and type (from schematic, carried into PCB)
            pinfunc = get_value(pad, "pinfunction")
            pintype = get_value(pad, "pintype")
            if pinfunc:
                pad_info["pinfunction"] = pinfunc
            if pintype:
                pad_info["pintype"] = pintype

            # Per-pad zone connection override
            zc = get_value(pad, "zone_connect")
            if zc is not None:
                pad_info["zone_connect"] = int(zc)

            # Custom pad shape — flag it and estimate copper area from primitives
            if pad_shape == "custom":
                pad_info["is_custom"] = True
                primitives = find_first(pad, "primitives")
                if primitives:
                    custom_area = 0.0
                    for prim in find_all(primitives, "gr_poly"):
                        pts = find_first(prim, "pts")
                        if pts:
                            custom_area += _shoelace_area(pts)
                    if custom_area > 0:
                        pad_info["custom_copper_area_mm2"] = round(custom_area, 3)

            # Pad-level solder mask/paste overrides
            sm_margin = get_value(pad, "solder_mask_margin")
            sp_margin = get_value(pad, "solder_paste_margin")
            sp_ratio = get_value(pad, "solder_paste_margin_ratio")
            if sm_margin:
                pad_info["solder_mask_margin"] = float(sm_margin)
            if sp_margin:
                pad_info["solder_paste_margin"] = float(sp_margin)
            if sp_ratio:
                pad_info["solder_paste_ratio"] = float(sp_ratio)

            pads.append(pad_info)

        # Extract courtyard geometry: bounding box + chained outline polygons
        crtyd_pts: list[tuple[float, float]] = []
        crtyd_segs: list[tuple[tuple[float, float], tuple[float, float]]] = []
        crtyd_polys: list[list[tuple[float, float]]] = []
        crtyd_unchainable = False  # arcs/circles → polygon set would be incomplete

        def _fp_to_abs(lx: float, ly: float) -> tuple[float, float]:
            if angle != 0:
                rad = math.radians(-angle)
                rx = lx * math.cos(rad) - ly * math.sin(rad)
                ry = lx * math.sin(rad) + ly * math.cos(rad)
                lx, ly = rx, ry
            return (x + lx, y + ly)

        for gtype in ("fp_line", "fp_rect", "fp_circle", "fp_poly", "fp_arc"):
            for item in find_all(fp, gtype):
                item_layer = get_value(item, "layer")
                if not item_layer or "CrtYd" not in item_layer:
                    continue
                # fp_poly: extract all vertex coordinates
                if gtype == "fp_poly":
                    pts = find_first(item, "pts")
                    if pts:
                        poly = []
                        for xy in find_all(pts, "xy"):
                            if len(xy) >= 3:
                                poly.append(_fp_to_abs(float(xy[1]), float(xy[2])))
                        if len(poly) >= 3:
                            crtyd_polys.append(poly)
                        crtyd_pts.extend(poly)
                    continue
                if gtype == "fp_line":
                    p1 = find_first(item, "start")
                    p2 = find_first(item, "end")
                    if p1 and p2 and len(p1) >= 3 and len(p2) >= 3:
                        seg_a = _fp_to_abs(float(p1[1]), float(p1[2]))
                        seg_b = _fp_to_abs(float(p2[1]), float(p2[2]))
                        crtyd_segs.append((seg_a, seg_b))
                        crtyd_pts.extend((seg_a, seg_b))
                    continue
                if gtype == "fp_rect":
                    p1 = find_first(item, "start")
                    p2 = find_first(item, "end")
                    if p1 and p2 and len(p1) >= 3 and len(p2) >= 3:
                        sx, sy = float(p1[1]), float(p1[2])
                        ex, ey = float(p2[1]), float(p2[2])
                        corners = [_fp_to_abs(cx_, cy_) for cx_, cy_ in
                                   ((sx, sy), (ex, sy), (ex, ey), (sx, ey))]
                        crtyd_polys.append(corners)
                        crtyd_pts.extend(corners)
                    continue
                # fp_circle / fp_arc: bbox contribution only — polygon set
                # stays disabled so overlap falls back to the AABB (KH-350)
                crtyd_unchainable = True
                for key in ("start", "end", "center", "mid"):
                    node = find_first(item, key)
                    if node and len(node) >= 3:
                        crtyd_pts.append(_fp_to_abs(float(node[1]), float(node[2])))

        if crtyd_segs and not crtyd_unchainable:
            _chained = _chain_segments(crtyd_segs)
            if _chained:
                crtyd_polys.extend(_chained)
            else:
                crtyd_unchainable = True

        fp_entry: dict = {
            "library": fp_lib,
            "reference": ref,
            "value": value,
            "mpn": mpn,
            "x": x,
            "y": y,
            "angle": angle,
            "layer": layer,
            "type": attr,
            "pad_count": len(pads),
            "pads": pads,
        }

        # Extended attributes
        if is_dnp:
            fp_entry["dnp"] = True
        if is_board_only:
            fp_entry["board_only"] = True
        if exclude_from_bom:
            fp_entry["exclude_from_bom"] = True
        if exclude_from_pos:
            fp_entry["exclude_from_pos"] = True

        # Schematic cross-reference
        if sch_path:
            fp_entry["sch_path"] = sch_path
        if sch_sheetname:
            fp_entry["sheetname"] = sch_sheetname
        if sch_sheetfile:
            fp_entry["sheetfile"] = sch_sheetfile

        # Net tie
        if net_tie_groups:
            fp_entry["net_tie_pad_groups"] = net_tie_groups

        # Extended properties
        if manufacturer:
            fp_entry["manufacturer"] = manufacturer
        if digikey_pn:
            fp_entry["digikey_pn"] = digikey_pn
        if description:
            fp_entry["description"] = description

        # 3D models
        if models:
            fp_entry["models_3d"] = models

        if crtyd_pts:
            cxs = [p[0] for p in crtyd_pts]
            cys = [p[1] for p in crtyd_pts]
            fp_entry["courtyard"] = {
                "min_x": round(min(cxs), 3), "min_y": round(min(cys), 3),
                "max_x": round(max(cxs), 3), "max_y": round(max(cys), 3),
            }
            if crtyd_polys and not crtyd_unchainable:
                fp_entry["courtyard_poly"] = [
                    [[round(vx_, 3), round(vy_, 3)] for vx_, vy_ in poly]
                    for poly in crtyd_polys
                ]

        footprints.append(fp_entry)

    return footprints


def _chain_segments(segs: list, tol: float = 0.01) -> list | None:
    """Chain undirected 2D segments into closed loops (KH-350).

    Returns a list of polygons (each a list of (x, y) vertices, implicit
    closure) or None when any chain fails to close within tolerance —
    callers then keep the AABB-only behavior.
    """
    def _close(p, q):
        return abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol

    remaining = [s for s in segs if not _close(s[0], s[1])]
    polys = []
    while remaining:
        a, b = remaining.pop()
        path = [a, b]
        while not _close(path[0], path[-1]):
            tail = path[-1]
            for i, (p, q) in enumerate(remaining):
                if _close(p, tail):
                    path.append(q)
                    break
                if _close(q, tail):
                    path.append(p)
                    break
            else:
                return None  # open chain
            remaining.pop(i)
        poly = path[:-1]
        if len(poly) < 3:
            return None
        polys.append(poly)
    return polys


def _point_in_polys(px: float, py: float, polys: list) -> bool:
    """Even-odd ray-casting membership over a list of polygons."""
    inside = False
    for poly in polys:
        n = len(poly)
        j = n - 1
        for i in range(n):
            xi, yi = poly[i][0], poly[i][1]
            xj, yj = poly[j][0], poly[j][1]
            if (yi > py) != (yj > py):
                if px < (xj - xi) * (py - yi) / (yj - yi) + xi:
                    inside = not inside
            j = i
    return inside


def _refined_overlap_mm2(polys_a: list, polys_b: list,
                         ix1: float, iy1: float, ix2: float, iy2: float,
                         samples: int = 24) -> float:
    """True courtyard overlap area inside the AABB-intersection box,
    estimated by grid-sampling membership in both polygon sets (KH-350)."""
    w = ix2 - ix1
    h = iy2 - iy1
    if w <= 0 or h <= 0:
        return 0.0
    hits = 0
    for i in range(samples):
        px = ix1 + (i + 0.5) * w / samples
        for j in range(samples):
            py = iy1 + (j + 0.5) * h / samples
            if (_point_in_polys(px, py, polys_a)
                    and _point_in_polys(px, py, polys_b)):
                hits += 1
    return w * h * hits / (samples * samples)


def extract_tracks(root: list) -> dict:
    """Extract track segments with statistics."""
    segments = []
    for seg in find_all(root, "segment"):
        start = find_first(seg, "start")
        end = find_first(seg, "end")
        width = get_value(seg, "width")
        layer = get_value(seg, "layer")
        net = get_value(seg, "net")

        if start and end:
            seg_info = {
                "x1": float(start[1]), "y1": float(start[2]),
                "x2": float(end[1]), "y2": float(end[2]),
                "width": float(width) if width else 0,
                "layer": layer or "",
                "net": _net_id(net),
            }
            if net and not net.lstrip("-").isdigit():
                seg_info["_net_name"] = net  # KiCad 10: stash for mapping build
            segments.append(seg_info)

    # Also extract arcs
    arcs = []
    for arc in find_all(root, "arc"):
        start = find_first(arc, "start")
        mid = find_first(arc, "mid")
        end = find_first(arc, "end")
        width = get_value(arc, "width")
        layer = get_value(arc, "layer")
        net = get_value(arc, "net")

        if start and end:
            arc_info = {
                "start": [float(start[1]), float(start[2])],
                "mid": [float(mid[1]), float(mid[2])] if mid else None,
                "end": [float(end[1]), float(end[2])],
                "width": float(width) if width else 0,
                "layer": layer or "",
                "net": _net_id(net),
            }
            if net and not net.lstrip("-").isdigit():
                arc_info["_net_name"] = net
            arcs.append(arc_info)

    # Width statistics
    widths = {}
    for seg in segments:
        w = seg["width"]
        widths[w] = widths.get(w, 0) + 1
    for arc in arcs:
        w = arc["width"]
        widths[w] = widths.get(w, 0) + 1

    # Layer distribution
    layer_dist = {}
    for seg in segments:
        l = seg["layer"]
        layer_dist[l] = layer_dist.get(l, 0) + 1
    for arc in arcs:
        l = arc["layer"]
        layer_dist[l] = layer_dist.get(l, 0) + 1

    return {
        "segment_count": len(segments),
        "arc_count": len(arcs),
        "total_count": len(segments) + len(arcs),
        "width_distribution": widths,
        "layer_distribution": layer_dist,
        "segments": segments,
        "arcs": arcs,
    }


def extract_vias(root: list) -> dict:
    """Extract vias with statistics."""
    vias = []
    for via in find_all(root, "via"):
        at = get_at(via)
        size = get_value(via, "size")
        drill = get_value(via, "drill")
        net = get_value(via, "net")
        layers_node = find_first(via, "layers")

        # Via type is a bare token between 'via' and the first sub-list,
        # not a (type X) sublist. KiCad writers emit:
        #   Through: (via (at ...) ...)                — no token
        #   Blind:   (via blind (at ...) ...)
        #   Buried:  (via buried (at ...) ...)         — new in 10.0
        #   Micro:   (via micro (at ...) ...)
        via_type = "through"
        for child in via[1:]:
            if isinstance(child, str) and child in ("blind", "buried", "micro"):
                via_type = child
                break
            if isinstance(child, list):
                # First sub-list ends the bare-token region
                break

        via_info = {
            "x": at[0] if at else 0,
            "y": at[1] if at else 0,
            "size": float(size) if size else 0,
            "drill": float(drill) if drill else 0,
            "net": _net_id(net),
            "type": via_type,  # always emit; downstream defaults no longer needed
        }
        if net and not net.lstrip("-").isdigit():
            via_info["_net_name"] = net
        if layers_node and len(layers_node) > 1:
            via_info["layers"] = [l for l in layers_node[1:] if isinstance(l, str)]
        # Free (unanchored) vias — typically stitching or thermal
        if get_value(via, "free") == "yes":
            via_info["free"] = True
        # Via tenting
        tenting = find_first(via, "tenting")
        if tenting and len(tenting) > 1:
            via_info["tenting"] = [t for t in tenting[1:] if isinstance(t, str)]

        vias.append(via_info)

    # Size distribution
    sizes = {}
    for v in vias:
        key = f"{v['size']}/{v['drill']}"
        sizes[key] = sizes.get(key, 0) + 1

    return {
        "count": len(vias),
        "size_distribution": sizes,
        "vias": vias,
    }


def extract_zones(root: list) -> tuple[list[dict], ZoneFills]:
    """Extract copper zones with outline and filled polygon area/spatial data.

    Computes:
    - outline_area_mm2: area of the user-drawn zone boundary
    - outline_bbox: bounding box of the zone outline [min_x, min_y, max_x, max_y]
    - filled_area_mm2: total copper fill area (sum of all filled_polygon regions)
    - filled_bbox: bounding box of all filled polygons combined
    - fill_ratio: filled_area / outline_area (1.0 = fully filled, <1.0 = has gaps)
    - filled_layers: per-layer filled area breakdown
    - is_filled: whether the zone has been filled (has filled_polygon data)

    Returns:
        (zones, zone_fills) — zone_fills is a spatial index for point-in-polygon
        queries against the filled copper. The filled polygon coordinates are
        kept in memory (not in the JSON output) because they can be very large.
        Zone fills reflect the last time Fill All Zones was run in KiCad.
    """
    zones = []
    zone_fills = ZoneFills()
    for zone_idx, zone in enumerate(find_all(root, "zone")):
        net = get_value(zone, "net")
        net_name = get_value(zone, "net_name")
        layer = get_value(zone, "layer")
        layers_node = find_first(zone, "layers")

        # Zone properties
        connect_pads = find_first(zone, "connect_pads")
        clearance = None
        pad_connection = None
        if connect_pads:
            cl = get_value(connect_pads, "clearance")
            clearance = float(cl) if cl else None
            # Connection type: first bare string after "connect_pads" keyword
            for cp_item in connect_pads[1:]:
                if isinstance(cp_item, str) and cp_item in (
                        "yes", "no", "thru_hole_only", "full", "thermal_reliefs"):
                    pad_connection = cp_item
                    break

        # Keepout zone detection
        keepout = find_first(zone, "keepout")
        keepout_restrictions = None
        if keepout:
            keepout_restrictions = {}
            for restriction in ("tracks", "vias", "pads", "copperpour", "footprints"):
                val = get_value(keepout, restriction)
                if val:
                    keepout_restrictions[restriction] = val

        # Zone priority
        priority = get_value(zone, "priority")

        # Zone name (user-assigned)
        zone_name = get_value(zone, "name")

        min_thickness = get_value(zone, "min_thickness")
        fill = find_first(zone, "fill")
        thermal_gap = None
        thermal_bridge = None
        is_filled = False
        if fill:
            tg = get_value(fill, "thermal_gap")
            tb = get_value(fill, "thermal_bridge_width")
            thermal_gap = float(tg) if tg else None
            thermal_bridge = float(tb) if tb else None
            # "yes" in fill node means the zone has been filled
            is_filled = "yes" in fill
            if not is_filled:
                fill_mode = get_value(fill, "mode")
                if fill_mode in ("solid", "hatch"):
                    is_filled = True

        # Zone outline area and bounding box
        outline_area = 0.0
        outline_point_count = 0
        outline_bbox = None
        polygon = find_first(zone, "polygon")
        if polygon:
            pts = find_first(polygon, "pts")
            if pts:
                outline_coords = _extract_polygon_coords(pts)
                outline_point_count = len(outline_coords)
                outline_area = _shoelace_area_from_coords(outline_coords)
                if outline_coords:
                    outline_bbox = _polygon_bbox(outline_coords)

        # Filled polygon areas + spatial data for point-in-polygon queries
        filled_layers: dict[str, float] = {}
        total_filled_area = 0.0
        fill_count = 0
        filled_min_x = float('inf')
        filled_min_y = float('inf')
        filled_max_x = float('-inf')
        filled_max_y = float('-inf')
        for fp_node in find_all(zone, "filled_polygon"):
            fp_layer = get_value(fp_node, "layer") or layer or ""
            fp_pts = find_first(fp_node, "pts")
            if fp_pts:
                coords = _extract_polygon_coords(fp_pts)
                area = _shoelace_area_from_coords(coords)
                filled_layers[fp_layer] = filled_layers.get(fp_layer, 0.0) + area
                total_filled_area += area
                fill_count += 1
                # Store coordinates for spatial queries
                zone_fills.add(zone_idx, fp_layer, coords)
                # Track overall filled bounding box
                for cx, cy in coords:
                    if cx < filled_min_x:
                        filled_min_x = cx
                    if cy < filled_min_y:
                        filled_min_y = cy
                    if cx > filled_max_x:
                        filled_max_x = cx
                    if cy > filled_max_y:
                        filled_max_y = cy

        zone_layers = []
        if layers_node and len(layers_node) > 1:
            zone_layers = [l for l in layers_node[1:] if isinstance(l, str)]
        elif layer:
            zone_layers = [layer]

        # Compute filled bounding box (None if no fill data)
        filled_bbox = None
        if fill_count > 0 and filled_min_x != float('inf'):
            filled_bbox = (
                round(filled_min_x, 3), round(filled_min_y, 3),
                round(filled_max_x, 3), round(filled_max_y, 3),
            )

        # KiCad ≤9: (net number) + (net_name "name")
        # KiCad 10: (net "name"), no net_name node
        if net and not net.lstrip("-").isdigit():
            # KiCad 10: net value is the name itself
            net_name = net
        zone_info: dict = {
            "net": _net_id(net),
            "net_name": net_name or "",
            "layers": zone_layers,
            "clearance": clearance,
            "min_thickness": float(min_thickness) if min_thickness else None,
            "thermal_gap": thermal_gap,
            "thermal_bridge_width": thermal_bridge,
            "outline_points": outline_point_count,
            "outline_area_mm2": round(outline_area, 2),
            "is_filled": is_filled or fill_count > 0,
        }

        if outline_bbox:
            zone_info["outline_bbox"] = [round(v, 3) for v in outline_bbox]

        if keepout_restrictions:
            zone_info["is_keepout"] = True
            zone_info["keepout"] = keepout_restrictions
        if priority is not None:
            zone_info["priority"] = int(priority)
        if zone_name:
            zone_info["name"] = zone_name
        if pad_connection:
            zone_info["pad_connection"] = pad_connection

        if fill_count > 0:
            zone_info["filled_area_mm2"] = round(total_filled_area, 2)
            zone_info["fill_region_count"] = fill_count
            if filled_bbox:
                zone_info["filled_bbox"] = list(filled_bbox)
            if outline_area > 0:
                zone_info["fill_ratio"] = round(
                    total_filled_area / outline_area, 3)
            if len(filled_layers) > 1:
                zone_info["filled_layers"] = {
                    k: round(v, 2) for k, v in sorted(filled_layers.items())
                }

        zones.append(zone_info)

    return zones, zone_fills


def _extract_keepout_zones(zones: list[dict],
                           footprints: list[dict]) -> list[dict]:
    """Surface keepout/rule areas as a dedicated section.

    Filters keepout zones from the main zones array and enriches each
    with nearby component references (footprints within 5mm of the zone
    bounding box).
    """
    keepouts = []
    for z in zones:
        if not z.get('is_keepout'):
            continue
        bbox = z.get('outline_bbox')
        entry = {
            'name': z.get('name', ''),
            'layers': z.get('layers', []),
            'restrictions': z.get('keepout', {}),
            'bounding_box': bbox,
            'area_mm2': z.get('outline_area_mm2', 0),
            # Net the keepout is associated with — items on this net are
            # ALLOWED inside the keepout (KiCad rule-area semantic). 0 / ""
            # means "no specific net" → keepout applies to all items.
            'net': z.get('net', 0),
            'net_name': z.get('net_name', ''),
        }
        # Find footprints near this keepout zone
        if bbox and len(bbox) == 4:
            margin = 5.0  # mm
            bx_min, by_min, bx_max, by_max = bbox
            nearby = []
            for fp in footprints:
                fx = fp.get('x', 0)
                fy = fp.get('y', 0)
                if (bx_min - margin <= fx <= bx_max + margin
                        and by_min - margin <= fy <= by_max + margin):
                    nearby.append(fp.get('reference', ''))
            entry['nearby_components'] = sorted(
                r for r in nearby if r)
        keepouts.append(entry)
    return keepouts


def extract_board_outline(root: list) -> dict:
    """Extract board outline from Edge.Cuts layer."""
    edges = []

    for item_type in ["gr_line", "gr_arc", "gr_circle", "gr_rect", "gr_poly", "gr_curve"]:
        for item in find_all(root, item_type):
            layer = get_value(item, "layer")
            if layer != "Edge.Cuts":
                continue

            if item_type == "gr_line":
                start = find_first(item, "start")
                end = find_first(item, "end")
                if start and end:
                    edges.append({
                        "type": "line",
                        "start": [float(start[1]), float(start[2])],
                        "end": [float(end[1]), float(end[2])],
                    })
            elif item_type == "gr_arc":
                start = find_first(item, "start")
                mid = find_first(item, "mid")
                end = find_first(item, "end")
                if start and end:
                    edges.append({
                        "type": "arc",
                        "start": [float(start[1]), float(start[2])],
                        "mid": [float(mid[1]), float(mid[2])] if mid else None,
                        "end": [float(end[1]), float(end[2])],
                    })
            elif item_type == "gr_rect":
                start = find_first(item, "start")
                end = find_first(item, "end")
                if start and end:
                    edges.append({
                        "type": "rect",
                        "start": [float(start[1]), float(start[2])],
                        "end": [float(end[1]), float(end[2])],
                    })
            elif item_type == "gr_circle":
                center = find_first(item, "center")
                end = find_first(item, "end")
                if center and end:
                    edges.append({
                        "type": "circle",
                        "center": [float(center[1]), float(center[2])],
                        "end": [float(end[1]), float(end[2])],
                    })
            elif item_type == "gr_poly":
                pts = find_first(item, "pts")
                if pts:
                    points = []
                    for xy in pts:
                        if isinstance(xy, list) and len(xy) >= 3 and xy[0] == "xy":
                            points.append([float(xy[1]), float(xy[2])])
                    if points:
                        edges.append({"type": "polygon", "points": points})
            elif item_type == "gr_curve":
                pts = find_first(item, "pts")
                if pts:
                    points = []
                    for xy in pts:
                        if isinstance(xy, list) and len(xy) >= 3 and xy[0] == "xy":
                            points.append([float(xy[1]), float(xy[2])])
                    if points:
                        edges.append({"type": "curve", "points": points})

    # Compute bounding box from all edge points
    all_x = []
    all_y = []
    for e in edges:
        if e["type"] == "circle":
            # Circle: bounding box is center ± radius
            cx, cy = e["center"]
            ex, ey = e["end"]
            r = math.sqrt((ex - cx) ** 2 + (ey - cy) ** 2)
            all_x.extend([cx - r, cx + r])
            all_y.extend([cy - r, cy + r])
            continue
        if e["type"] == "arc" and e.get("mid"):
            # EQ-100: Arc bounding box — 3-point circumscribed circle via
            #   determinant, then check whether arc sweep (via atan2 of
            #   endpoints + midpoint) crosses any cardinal axis at 0, π/2, π,
            #   3π/2. Crossings extend the bbox to ±r.
            # Source: Standard computational geometry. Circumscribed circle
            #   from 3 points:
            #   https://en.wikipedia.org/wiki/Circumscribed_circle#Circumscribed_circles_of_triangles
            #   Arc bbox via cardinal-crossing test is a well-known CAD/CAM
            #   technique.
            # Arc: include start/end plus any cardinal extrema the arc passes through
            sx, sy = e["start"]
            mx, my = e["mid"]
            ex, ey = e["end"]
            all_x.extend([sx, ex])
            all_y.extend([sy, ey])
            # Compute center and radius from 3 points
            D = 2.0 * (sx * (my - ey) + mx * (ey - sy) + ex * (sy - my))
            if abs(D) > 1e-10:
                ss = sx * sx + sy * sy
                ms = mx * mx + my * my
                es = ex * ex + ey * ey
                ucx = (ss * (my - ey) + ms * (ey - sy) + es * (sy - my)) / D
                ucy = (ss * (ex - mx) + ms * (sx - ex) + es * (mx - sx)) / D
                r = math.sqrt((sx - ucx) ** 2 + (sy - ucy) ** 2)
                # Find which cardinal angles the arc sweeps through
                a_s = math.atan2(sy - ucy, sx - ucx)
                a_m = math.atan2(my - ucy, mx - ucx)
                a_e = math.atan2(ey - ucy, ex - ucx)
                # Determine sweep direction (CW or CCW) using mid-point
                nm = (a_m - a_s) % (2.0 * math.pi)
                ne = (a_e - a_s) % (2.0 * math.pi)
                if nm > ne:
                    # Arc goes CW (negative sweep) — swap direction
                    sweep = -((2.0 * math.pi) - ne)
                else:
                    sweep = ne
                # Check each cardinal angle (0, π/2, π, 3π/2)
                for cardinal, dx, dy in [(0, 1, 0), (math.pi / 2, 0, 1),
                                         (math.pi, -1, 0), (3 * math.pi / 2, 0, -1)]:
                    offset = (cardinal - a_s) % (2.0 * math.pi)
                    if sweep > 0 and offset <= sweep:
                        all_x.append(ucx + r * dx)
                        all_y.append(ucy + r * dy)
                    elif sweep < 0 and offset >= (2.0 * math.pi + sweep):
                        all_x.append(ucx + r * dx)
                        all_y.append(ucy + r * dy)
            continue
        # Polygons and curves: use all points
        if e["type"] in ("polygon", "curve") and "points" in e:
            for pt in e["points"]:
                all_x.append(pt[0])
                all_y.append(pt[1])
            continue
        # Lines, rects, arcs without mid: use raw endpoint coordinates
        for key in ["start", "end", "center", "mid"]:
            if key in e and e[key] is not None:
                all_x.append(e[key][0])
                all_y.append(e[key][1])

    bbox = None
    if all_x and all_y:
        bbox = {
            "min_x": min(all_x),
            "min_y": min(all_y),
            "max_x": max(all_x),
            "max_y": max(all_y),
            "width": round(max(all_x) - min(all_x), 3),
            "height": round(max(all_y) - min(all_y), 3),
        }

    return {
        "edge_count": len(edges),
        "edges": edges,
        "bounding_box": bbox,
        # Convenience aliases so consumers don't have to reach into bounding_box.
        # bbox already accounts for arc extrema (see EQ-100 above), so these are
        # correct on arc-edge outlines too; None only when no Edge.Cuts geometry.
        "width_mm": bbox["width"] if bbox else None,
        "height_mm": bbox["height"] if bbox else None,
    }


def analyze_connectivity(footprints: list[dict], tracks: dict, vias: dict,
                         net_names: dict[int, str],
                         zones: list[dict] | None = None) -> dict:
    """Analyze routing completeness — find unrouted nets.

    A net is considered routed if it has tracks, vias, or a copper zone
    covering it. Nets with only a single pad are skipped.
    """
    # Build set of nets that have pads
    pad_nets: dict[int, list[str]] = {}  # net_number -> list of "REF.pad"
    for fp in footprints:
        for pad in fp["pads"]:
            net_num = pad.get("net_number", 0)
            if net_num > 0:
                pad_nets.setdefault(net_num, []).append(f"{fp['reference']}.{pad['number']}")

    # Build set of nets that have routing (tracks, vias, or zones)
    routed_nets = set()
    for seg in tracks.get("segments", []):
        if seg["net"] > 0:
            routed_nets.add(seg["net"])
    for arc in tracks.get("arcs", []):
        if arc["net"] > 0:
            routed_nets.add(arc["net"])
    for via in vias.get("vias", []):
        if via["net"] > 0:
            routed_nets.add(via["net"])
    # Zones also route nets — a GND zone connects all GND pads
    if zones:
        for z in zones:
            zn = z.get("net", 0)
            if zn > 0:
                routed_nets.add(zn)

    # Find unrouted nets (have pads but no tracks/zones)
    unrouted = []
    for net_num, pads in pad_nets.items():
        if len(pads) >= 2 and net_num not in routed_nets:
            net_name = net_names.get(net_num, f"net_{net_num}")
            # Extract component refs from pad strings ("REF.pad" -> "REF")
            comp_refs = sorted(set(p.split(".")[0] for p in pads if "." in p))
            unrouted.append({
                "net_number": net_num,
                "net_name": net_name,
                "pad_count": len(pads),
                "pads": pads,
                "detector": "analyze_connectivity",
                "rule_id": "RT-001",
                "category": "connectivity",
                "severity": "error",
                "confidence": "deterministic",
                "evidence_source": "topology",
                "summary": f"Unrouted net {net_name} ({len(pads)} pads)",
                "description": f"Net {net_name} has {len(pads)} pads but no routing (tracks, vias, or zones).",
                "components": comp_refs,
                "nets": [net_name],
                "pins": [],
                "recommendation": f"Route net {net_name} to connect {len(pads)} pads",
                "report_context": {"section": "Connectivity", "impact": "functionality", "standard_ref": ""},
            })

    return {
        "total_nets_with_pads": len(pad_nets),
        "routed_nets": len(routed_nets & set(pad_nets.keys())),
        "unrouted_count": len(unrouted),
        "routing_complete": len(unrouted) == 0,
        "unrouted": sorted(unrouted, key=lambda u: u["net_name"]),
    }


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


def analyze_power_nets(footprints: list[dict], tracks: dict,
                       net_names: dict[int, str]) -> list[dict]:
    """Analyze routing of power/ground nets — track widths, via counts."""
    # EQ-052: d = √(Δx²+Δy²) (Euclidean distance)
    # Identify power/ground nets
    power_nets = {}
    for net_num, name in net_names.items():
        if is_power_net_name(name) or is_ground_name(name):
            power_nets[net_num] = {"name": name, "widths": set(), "track_count": 0,
                                   "total_length_mm": 0.0}

    if not power_nets:
        return []

    for seg in tracks.get("segments", []):
        net = seg["net"]
        if net in power_nets:
            power_nets[net]["widths"].add(seg["width"])
            power_nets[net]["track_count"] += 1
            dx = seg["x2"] - seg["x1"]
            dy = seg["y2"] - seg["y1"]
            power_nets[net]["total_length_mm"] += math.sqrt(dx * dx + dy * dy)

    result = []
    for net_num, info in sorted(power_nets.items(), key=lambda x: x[1]["name"]):
        if info["track_count"] == 0:
            continue  # Only zone-routed or single-pad
        widths = sorted(info["widths"])
        result.append({
            "net": info["name"],
            "track_count": info["track_count"],
            "total_length_mm": round(info["total_length_mm"], 2),
            "min_width_mm": widths[0] if widths else None,
            "max_width_mm": widths[-1] if widths else None,
            "widths_used": widths,
        })
    return result


_ESD_TVS_PREFIXES = ("esd", "prtr", "usblc", "tpd", "pesd", "sp05",
                     "rclamp", "nup", "lesd", "ip4", "dt104")


def _build_routing_graph(segments, arcs, vias_list):
    """Build a per-net adjacency graph from trace segments and vias.

    Nodes are coordinate tuples (x, y) rounded to 0.001mm.
    Edges are trace segments with length and width.

    Returns:
        Dict mapping net_id → {nodes: set, edges: dict[node → [(neighbor, length_mm, width_mm)]]}
    """
    # EQ-045: d = √(Δx²+Δy²) (routing graph edge weight)
    SNAP = 0.001  # Coordinate snapping precision (mm)

    def _snap(x, y):
        return (round(x / SNAP) * SNAP, round(y / SNAP) * SNAP)

    graphs = {}  # net_id → {"edges": defaultdict(list)}

    for seg in segments:
        net = seg.get("net", 0)
        if net <= 0:
            continue
        p1 = _snap(seg["x1"], seg["y1"])
        p2 = _snap(seg["x2"], seg["y2"])
        dx = seg["x2"] - seg["x1"]
        dy = seg["y2"] - seg["y1"]
        length = math.sqrt(dx * dx + dy * dy)
        width = seg.get("width", 0)

        g = graphs.setdefault(net, {})
        edges = g.setdefault("edges", {})
        edges.setdefault(p1, []).append((p2, length, width))
        edges.setdefault(p2, []).append((p1, length, width))

    for arc in arcs:
        net = arc.get("net", 0)
        if net <= 0:
            continue
        s, e = arc["start"], arc["end"]
        p1 = _snap(s[0], s[1])
        p2 = _snap(e[0], e[1])
        m = arc.get("mid")
        if m:
            length = _arc_length_3pt(s[0], s[1], m[0], m[1], e[0], e[1])
        else:
            dx, dy = e[0] - s[0], e[1] - s[1]
            length = math.sqrt(dx * dx + dy * dy)
        width = arc.get("width", 0)

        g = graphs.setdefault(net, {})
        edges = g.setdefault("edges", {})
        edges.setdefault(p1, []).append((p2, length, width))
        edges.setdefault(p2, []).append((p1, length, width))

    # Add vias as zero-length edges connecting the same point across layers
    for via in vias_list:
        net = via.get("net", 0)
        if net <= 0:
            continue
        vp = _snap(via["x"], via["y"])
        g = graphs.setdefault(net, {})
        edges = g.setdefault("edges", {})
        edges.setdefault(vp, [])  # Ensure via point exists as a node

    return graphs


def _route_distance(graph, start_xy, end_xy, snap=0.001):
    """Find the shortest routed distance between two points in a net graph.

    Uses Dijkstra's algorithm on the routing graph.

    Args:
        graph: {"edges": {node → [(neighbor, length, width)]}}
        start_xy: (x, y) tuple of start pad position
        end_xy: (x, y) tuple of end pad position
        snap: Coordinate snapping precision

    Returns:
        (total_length_mm, path_widths) or (None, None) if no path exists
    """
    def _snap(x, y):
        return (round(x / snap) * snap, round(y / snap) * snap)

    start = _snap(*start_xy)
    end = _snap(*end_xy)
    edges = graph.get("edges", {})

    if start not in edges or end not in edges:
        return None, None
    if start == end:
        return 0.0, []

    # Dijkstra
    dist = {start: 0.0}
    prev = {}
    widths = {}
    heap = [(0.0, start)]
    visited = set()

    while heap:
        d, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        if node == end:
            # Reconstruct path widths
            path_widths = []
            n = end
            while n in prev:
                path_widths.append(widths[n])
                n = prev[n]
            return round(d, 3), list(reversed(path_widths))
        for neighbor, length, width in edges.get(node, []):
            if neighbor in visited:
                continue
            new_dist = d + length
            if neighbor not in dist or new_dist < dist[neighbor]:
                dist[neighbor] = new_dist
                prev[neighbor] = node
                widths[neighbor] = width
                heapq.heappush(heap, (new_dist, neighbor))

    return None, None  # No path found


def analyze_pad_to_pad_distances(footprints, tracks, vias, net_names):
    """Compute actual routed trace distances between component pads on shared nets.

    Builds a routing graph per net and uses Dijkstra to find the shortest
    routed path between each pair of pads. Much more accurate than Euclidean
    distance for decoupling placement and parasitic extraction.

    Returns:
        Dict mapping "REF1.pad-REF2.pad" → {
            "net": net_name,
            "routed_distance_mm": float,
            "euclidean_distance_mm": float,
            "ratio": float (routed/euclidean — 1.0 = direct, >1.5 = detour),
            "min_width_mm": float
        }
    """
    # EQ-051: d = √(Δx²+Δy²) (pad-to-pad distance)
    # Build routing graphs
    graphs = _build_routing_graph(
        tracks.get("segments", []),
        tracks.get("arcs", []),
        vias.get("vias", [])
    )

    # Collect pad positions per net
    pad_positions = {}  # net_id → [(ref, pad_num, x, y)]
    for fp in footprints:
        ref = fp.get("reference", "")
        for pad in fp.get("pads", []):
            net = pad.get("net_number", 0)
            if net <= 0:
                continue
            x = pad.get("abs_x", fp.get("x", 0))
            y = pad.get("abs_y", fp.get("y", 0))
            pad_positions.setdefault(net, []).append((ref, pad["number"], x, y))

    results = {}
    for net_id, pads in pad_positions.items():
        if len(pads) < 2:
            continue
        graph = graphs.get(net_id)
        if not graph:
            continue
        net_name = net_names.get(net_id, f"net_{net_id}")

        # Compute distances between all pairs (limited to 20 pads per net
        # to avoid combinatorial explosion on power nets)
        if len(pads) > 20:
            continue  # Skip high-fanout nets

        for i in range(len(pads)):
            for j in range(i + 1, len(pads)):
                ref_a, pad_a, xa, ya = pads[i]
                ref_b, pad_b, xb, yb = pads[j]

                # Euclidean distance
                euclid = math.sqrt((xb - xa) ** 2 + (yb - ya) ** 2)
                if euclid < 0.1:
                    continue  # Same pad or overlapping

                # Routed distance
                routed, widths = _route_distance(graph, (xa, ya), (xb, yb))
                if routed is None:
                    continue

                key = f"{ref_a}.{pad_a}-{ref_b}.{pad_b}"
                entry = {
                    "net": net_name,
                    "routed_distance_mm": routed,
                    "euclidean_distance_mm": round(euclid, 3),
                    "ratio": round(routed / euclid, 2) if euclid > 0 else 0,
                }
                if widths:
                    entry["min_width_mm"] = min(widths)
                results[key] = entry

    return results


def analyze_return_path_continuity(tracks, net_names, zones, zone_fills,
                                    signal_nets=None, ref_layer_map=None,
                                    footprints=None, radius_mm=0.5,
                                    debug_samples=None):
    """Check ground/power plane continuity under signal traces.

    For each signal net's trace segments, samples points along the trace
    and checks if the opposite layer has a ground or power zone fill.
    Flags gaps in the reference plane that could cause return path
    discontinuities and EMI issues.

    Uses :class:`CopperPresence` for radius-based copper detection that
    credits zone fills, tracks, and pads — avoids false negatives from
    KiCad zone-fill clearance channels ("swiss cheese" polygons).

    Args:
        tracks: Track data dict with segments
        net_names: Net number → name mapping
        zones: Zone list (for zone metadata)
        zone_fills: ZoneFills spatial index
        signal_nets: Optional set of net names to check (default: all non-power)
        ref_layer_map: Layer → opposite reference layer mapping
        footprints: Footprint list (for pad copper credit)
        radius_mm: Radius (mm) for copper-presence search (default 0.5)
        debug_samples: If a list is passed, per-sample dicts are appended
            with keys {net, x, y, layer, hit} for GP-001 diagnostics.

    Returns:
        List of gap findings: [{net, layer, gap_start_mm, gap_length_mm, ...}]
    """
    # EQ-053: d = √(Δx²+Δy²) (trace-to-plane gap detection)
    if not zone_fills.has_data:
        return []

    cp = CopperPresence(zone_fills, tracks.get('segments', []), footprints)

    from kicad_utils import is_power_net_name, is_ground_name

    findings = []
    # Only check signal nets (not power/ground — they ARE the reference)
    segments = tracks.get("segments", [])

    # Group segments by net
    net_segments: dict[int, list] = {}
    for seg in segments:
        net = seg.get("net", 0)
        if net <= 0:
            continue
        net_name = net_names.get(net, "")
        if is_power_net_name(net_name) or is_ground_name(net_name):
            continue
        if signal_nets and net_name not in signal_nets:
            continue
        net_segments.setdefault(net, []).append(seg)

    SAMPLE_INTERVAL = 2.0  # mm between sample points

    for net_id, segs in net_segments.items():
        net_name = net_names.get(net_id, f"net_{net_id}")
        total_samples = 0
        gap_samples = 0

        for seg in segs:
            layer = seg.get("layer", "F.Cu")
            if ref_layer_map:
                opp_layer = ref_layer_map.get(layer, "B.Cu" if layer == "F.Cu" else "F.Cu")
            else:
                opp_layer = "B.Cu" if layer == "F.Cu" else "F.Cu"

            x1, y1 = seg["x1"], seg["y1"]
            x2, y2 = seg["x2"], seg["y2"]
            dx, dy = x2 - x1, y2 - y1
            length = math.sqrt(dx * dx + dy * dy)
            if length < 0.1:
                continue

            # Sample along the trace
            n_samples = max(2, int(length / SAMPLE_INTERVAL) + 1)
            for k in range(n_samples):
                t = k / max(n_samples - 1, 1)
                px = x1 + t * dx
                py = y1 + t * dy
                total_samples += 1

                # Check for ANY copper (zone, track, pad) on opposite layer
                hit = cp.has_coverage_near(px, py, opp_layer,
                                           radius_mm=radius_mm)
                if not hit:
                    gap_samples += 1
                if debug_samples is not None:
                    debug_samples.append({
                        'net': net_name, 'x': round(px, 2),
                        'y': round(py, 2), 'layer': opp_layer,
                        'hit': hit,
                    })

        if total_samples > 0 and gap_samples > 0:
            coverage_pct = round((1 - gap_samples / total_samples) * 100, 1)
            if coverage_pct < 95:  # Only report if significant gap
                total_length = sum(
                    math.sqrt((s["x2"]-s["x1"])**2 + (s["y2"]-s["y1"])**2)
                    for s in segs)
                findings.append({
                    "net": net_name,
                    "total_trace_mm": round(total_length, 1),
                    "samples_checked": total_samples,
                    "samples_with_reference_plane": total_samples - gap_samples,
                    "reference_plane_coverage_pct": coverage_pct,
                    "gap_note": f"{gap_samples} of {total_samples} sample points lack reference plane on opposite layer",
                })

    # Sort by coverage (worst first)
    findings.sort(key=lambda f: f["reference_plane_coverage_pct"])
    return findings


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

    if not ics or not caps:
        return []

    results = []
    for ic in ics:
        nearby = []
        for cap in caps:
            dist = _min_power_pad_distance(ic, cap)
            if dist <= 10.0:  # Within 10mm
                # Check if cap shares a net with IC (likely decoupling)
                ic_nets = {p.get("net_name") for p in ic.get("pads", []) if p.get("net_name")}
                cap_nets = {p.get("net_name") for p in cap.get("pads", []) if p.get("net_name")}
                shared = (ic_nets & cap_nets) - {""}
                nearby.append({
                    "cap": cap["reference"],
                    "value": cap.get("value", ""),
                    "distance_mm": round(dist, 2),
                    "shared_nets": sorted(shared) if shared else [],
                    "same_side": cap["layer"] == ic["layer"],
                })
        if nearby:
            nearby.sort(key=lambda n: n["distance_mm"])
            results.append({
                "ic": ic["reference"],
                "value": ic.get("value", ""),
                "layer": ic["layer"],
                "nearby_caps": nearby,
                "closest_cap_mm": nearby[0]["distance_mm"],
            })

    # ESD protection ICs need bypass caps within 3mm for clamping
    esd_ics = [fp for fp in footprints
               if re.match(r'^(U|IC)\d', fp.get("reference", ""))
               and any(fp.get("value", "").lower().startswith(p)
                       for p in _ESD_TVS_PREFIXES)]
    for ic in esd_ics:
        nearby = []
        for cap in caps:
            dist = _min_power_pad_distance(ic, cap)
            if dist <= 10.0:
                ic_nets = {p.get("net_name") for p in ic.get("pads", [])
                           if p.get("net_name")}
                cap_nets = {p.get("net_name") for p in cap.get("pads", [])
                            if p.get("net_name")}
                shared = (ic_nets & cap_nets) - {""}
                nearby.append({
                    "cap": cap["reference"],
                    "value": cap.get("value", ""),
                    "distance_mm": round(dist, 2),
                    "shared_nets": sorted(shared) if shared else [],
                    "same_side": cap["layer"] == ic["layer"],
                })
        if nearby:
            nearby.sort(key=lambda n: n["distance_mm"])
            results.append({
                "ic": ic["reference"],
                "value": ic.get("value", ""),
                "layer": ic["layer"],
                "category": "esd_bypass",
                "nearby_caps": nearby,
                "closest_cap_mm": nearby[0]["distance_mm"],
            })

    return results


def _safe_num(val, default=0):
    """Safely convert a value to float (handles None, str, etc.)."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _build_reference_layer_map(stackup: list[dict]) -> dict[str, str]:
    """Map each copper layer to its adjacent reference plane copper layer.

    Walks the stackup in order and for each copper layer, finds the nearest
    other copper layer (above or below, preferring the one separated by
    thinner dielectric). Returns a mapping like {"F.Cu": "In1.Cu", "In1.Cu": "F.Cu", ...}.

    Falls back to simple F.Cu<->B.Cu when no stackup is available.
    """
    if not stackup:
        return {"F.Cu": "B.Cu", "B.Cu": "F.Cu"}

    # Extract ordered copper layer names and their stackup indices
    copper_layers: list[tuple[int, str]] = []
    for i, layer in enumerate(stackup):
        if layer.get("type") == "copper":
            copper_layers.append((i, layer.get("name", "")))

    if len(copper_layers) < 2:
        return {"F.Cu": "B.Cu", "B.Cu": "F.Cu"}

    ref_map: dict[str, str] = {}
    for ci, (idx, name) in enumerate(copper_layers):
        # Find dielectric thickness to adjacent copper layers above and below
        best_neighbor = None
        best_thickness = float("inf")

        for direction, neighbor_ci in [(-1, ci - 1), (1, ci + 1)]:
            if neighbor_ci < 0 or neighbor_ci >= len(copper_layers):
                continue
            n_idx, n_name = copper_layers[neighbor_ci]
            # Sum dielectric thickness between this layer and the neighbor
            lo = min(idx, n_idx)
            hi = max(idx, n_idx)
            thickness = 0.0
            for k in range(lo + 1, hi):
                if stackup[k].get("type") in ("core", "prepreg"):
                    t = stackup[k].get("thickness")
                    if t is not None:
                        try:
                            thickness += float(t)
                        except (ValueError, TypeError):
                            thickness += 0.2
            if thickness < best_thickness:
                best_thickness = thickness
                best_neighbor = n_name

        if best_neighbor:
            ref_map[name] = best_neighbor

    return ref_map


def _microstrip_impedance(width_mm, height_mm, thickness_mm, epsilon_r):
    """Calculate single-ended microstrip characteristic impedance.

    Uses Wheeler's equations (IPC-2141) with effective width correction
    for finite copper thickness.

    Args:
        width_mm: Trace width in mm
        height_mm: Dielectric height to reference plane in mm
        thickness_mm: Copper thickness in mm
        epsilon_r: Relative permittivity of dielectric

    Returns:
        Characteristic impedance in ohms, or None if inputs invalid
    """
    width_mm = _safe_num(width_mm)
    height_mm = _safe_num(height_mm)
    thickness_mm = _safe_num(thickness_mm)
    epsilon_r = _safe_num(epsilon_r)
    if width_mm <= 0 or height_mm <= 0 or thickness_mm <= 0 or epsilon_r <= 0:
        return None
    w = width_mm
    h = height_mm
    t = thickness_mm
    er = epsilon_r
    # Effective width accounting for copper thickness (IPC-2141)
    if w > 2 * math.pi * t:
        w_eff = w + (t / math.pi) * (1 + math.log(2 * h / t))
    else:
        w_eff = w + (t / math.pi) * (1 + math.log(4 * math.pi * w / t))
    # Wheeler's equations
    # Source: IPC-2141 Design Guide
    # Verified: https://f4inx.github.io/posts/microstrip-formulas-comparison.html
    if w_eff / h < 1:
        # EQ-023: Z₀ = (60/√εr)ln(8h/w+w/4h) (Wheeler narrow microstrip)
        z0 = (60 / math.sqrt(er)) * math.log(8 * h / w_eff + w_eff / (4 * h))
    else:
        # EQ-024: Z₀ = 120π/(√εr(w/h+1.393+0.667ln(w/h+1.444))) (Wheeler wide)
        z0 = (120 * math.pi) / (math.sqrt(er) * (w_eff / h + 1.393 + 0.667 * math.log(w_eff / h + 1.444)))
    return z0


def _build_layer_heights(stackup):
    """Map copper layer names to their dielectric height above the nearest reference plane.

    Walks the stackup from top to bottom. Each copper layer's height is the
    thickness of the adjacent dielectric layer below it (for top layers) or
    above it (for bottom layers).

    Returns:
        Dict mapping layer name → (dielectric_height_mm, epsilon_r, copper_thickness_mm)
    """
    if not stackup:
        return {}

    heights = {}
    layers = list(stackup)

    for i, layer in enumerate(layers):
        if layer.get("type") != "copper":
            continue
        name = layer.get("name", "")
        cu_t = layer.get("thickness", 0.035)

        # Look for the nearest dielectric layer (below for top copper, above for bottom)
        # Try below first
        for j in range(i + 1, len(layers)):
            if layers[j].get("type") in ("core", "prepreg"):
                h = layers[j].get("thickness", 0.2)
                er = layers[j].get("epsilon_r", 4.5)
                heights[name] = (h, er, cu_t)
                break
        else:
            # No dielectric below — try above
            for j in range(i - 1, -1, -1):
                if layers[j].get("type") in ("core", "prepreg"):
                    h = layers[j].get("thickness", 0.2)
                    er = layers[j].get("epsilon_r", 4.5)
                    heights[name] = (h, er, cu_t)
                    break

    return heights


def analyze_net_lengths(tracks: dict, vias: dict,
                        net_names: dict[int, str],
                        include_segments: bool = False,
                        stackup: list = None) -> list[dict]:
    """Per-net trace length measurement for matched-length and routing analysis.

    Provides total length, per-layer breakdown, segment count, and via count
    for each routed net. Enables differential pair matching, bus length matching,
    and routing completeness assessment by higher-level logic.

    When include_segments=True, also emits per-segment width+length detail and
    per-via drill size, for parasitic extraction by the SPICE simulation skill.

    When stackup is provided, each trace segment also gets a characteristic
    impedance estimate (microstrip formula from IPC-2141).
    """
    # EQ-050: L = √(Δx²+Δy²) (track segment length)
    # Pre-compute layer-to-dielectric-height mapping for impedance calculation
    layer_heights = _build_layer_heights(stackup) if stackup else {}

    net_data: dict[int, dict] = {}

    for seg in tracks.get("segments", []):
        net = seg["net"]
        if net <= 0:
            continue
        dx = seg["x2"] - seg["x1"]
        dy = seg["y2"] - seg["y1"]
        length = math.sqrt(dx * dx + dy * dy)

        d = net_data.setdefault(net, {"layers": {}, "total_length": 0.0,
                                      "segment_count": 0, "via_count": 0})
        d["total_length"] += length
        d["segment_count"] += 1
        layer = seg["layer"]
        ld = d["layers"].setdefault(layer, {"length": 0.0, "segments": 0})
        ld["length"] += length
        ld["segments"] += 1

        if include_segments:
            seg_entry = {
                "layer": layer,
                "length_mm": round(length, 3),
                "width_mm": seg.get("width", 0),
            }
            # Add impedance if stackup is available
            if stackup and layer_heights and layer in layer_heights:
                h, er, cu_t = layer_heights[layer]
                z0 = _microstrip_impedance(seg.get("width", 0), h, cu_t, er)
                if z0:
                    seg_entry["impedance_ohm"] = round(z0, 1)
            d.setdefault("trace_segments", []).append(seg_entry)

    for arc in tracks.get("arcs", []):
        net = arc["net"]
        if net <= 0:
            continue
        s, e = arc["start"], arc["end"]
        m = arc.get("mid")
        if m:
            length = _arc_length_3pt(s[0], s[1], m[0], m[1], e[0], e[1])
        else:
            dx, dy = e[0] - s[0], e[1] - s[1]
            length = math.sqrt(dx * dx + dy * dy)

        d = net_data.setdefault(net, {"layers": {}, "total_length": 0.0,
                                      "segment_count": 0, "via_count": 0})
        d["total_length"] += length
        d["segment_count"] += 1
        layer = arc["layer"]
        ld = d["layers"].setdefault(layer, {"length": 0.0, "segments": 0})
        ld["length"] += length
        ld["segments"] += 1

        if include_segments:
            seg_entry = {
                "layer": layer,
                "length_mm": round(length, 3),
                "width_mm": arc.get("width", 0),
            }
            if stackup and layer_heights and layer in layer_heights:
                h, er, cu_t = layer_heights[layer]
                z0 = _microstrip_impedance(arc.get("width", 0), h, cu_t, er)
                if z0:
                    seg_entry["impedance_ohm"] = round(z0, 1)
            d.setdefault("trace_segments", []).append(seg_entry)

    for via in vias.get("vias", []):
        net = via["net"]
        if net <= 0:
            continue
        d = net_data.setdefault(net, {"layers": {}, "total_length": 0.0,
                                      "segment_count": 0, "via_count": 0})
        d["via_count"] += 1

        if include_segments:
            via_entry = {
                "drill_mm": via.get("drill", 0),
                "layers": via.get("layers", []),
            }
            # Compute stub length for through-hole vias on boards with >2 layers
            if stackup and layer_heights:
                via_layers = via.get("layers", [])
                if len(via_layers) >= 2 and len(layer_heights) > 2:
                    # Via connects between first and last of its layers;
                    # stub = total board thickness - span between connected layers
                    all_cu = [l["name"] for l in stackup if l.get("type") == "copper"]
                    if len(all_cu) > 2:
                        try:
                            top_idx = all_cu.index(via_layers[0])
                            bot_idx = all_cu.index(via_layers[-1])
                            # Stub = layers below the bottom connected layer
                            stub_layers = all_cu[bot_idx + 1:]
                            if stub_layers:
                                stub_mm = sum(layer_heights.get(l, (0.2, 4.5, 0.035))[0]
                                              for l in stub_layers)
                                via_entry["stub_length_mm"] = round(stub_mm, 3)
                        except ValueError:
                            pass
            d.setdefault("via_details", []).append(via_entry)

    result = []
    for net_num, data in sorted(net_data.items(),
                                key=lambda x: x[1]["total_length"], reverse=True):
        entry = {
            "net": net_names.get(net_num, f"net_{net_num}"),
            "net_number": net_num,
            "total_length_mm": round(data["total_length"], 3),
            "segment_count": data["segment_count"],
            "via_count": data["via_count"],
            "layers": {
                layer: {"length_mm": round(info["length"], 3),
                        "segments": info["segments"]}
                for layer, info in sorted(data["layers"].items())
            },
        }
        if include_segments:
            if "trace_segments" in data:
                entry["trace_segments"] = data["trace_segments"]
            if "via_details" in data:
                entry["via_details"] = data["via_details"]
        result.append(entry)
    return result


def analyze_ground_domains(footprints: list[dict], net_names: dict[int, str],
                           zones: list[dict]) -> dict:
    """Identify ground domain splits and component membership.

    Detects separate ground nets (GND, AGND, DGND, PGND, etc.) and reports
    which components connect to each. Components on multiple ground domains
    are flagged — these may be intentional (star ground) or errors.
    """
    ground_nets: dict[int, str] = {}
    for net_num, name in net_names.items():
        nu = name.upper()
        if any(g in nu for g in ("GND", "VSS", "GROUND")):
            ground_nets[net_num] = name

    if not ground_nets:
        return {"domain_count": 0, "domains": [], "multi_domain_components": []}

    domain_components: dict[int, set[str]] = {n: set() for n in ground_nets}
    component_domains: dict[str, set[int]] = {}

    for fp in footprints:
        ref = fp.get("reference", "")
        for pad in fp.get("pads", []):
            net_num = pad.get("net_number", 0)
            if net_num in ground_nets:
                domain_components[net_num].add(ref)
                component_domains.setdefault(ref, set()).add(net_num)

    ground_zones: dict[int, list[str]] = {}
    for z in zones:
        zn = z.get("net", 0)
        if zn in ground_nets:
            ground_zones.setdefault(zn, []).extend(z.get("layers", []))

    domains = []
    for net_num, name in sorted(ground_nets.items(), key=lambda x: x[1]):
        comps = sorted(domain_components.get(net_num, set()))
        domains.append({
            "net": name,
            "net_number": net_num,
            "component_count": len(comps),
            "components": comps,
            "has_zone": net_num in ground_zones,
            "zone_layers": sorted(set(ground_zones.get(net_num, []))),
        })

    multi = []
    for ref, nets in sorted(component_domains.items()):
        if len(nets) > 1:
            multi.append({
                "component": ref,
                "ground_nets": sorted(ground_nets[n] for n in nets),
            })

    return {
        "domain_count": len(domains),
        "domains": domains,
        "multi_domain_components": multi,
    }


def analyze_trace_proximity(tracks: dict, net_names: dict[int, str],
                            grid_size: float = 0.5) -> dict:
    """Identify signal nets with traces running close together on the same layer.

    Uses a spatial grid to find net pairs sharing grid cells, indicating
    physical proximity on the PCB. Power/ground nets are excluded since
    they are expected to be everywhere. Only pairs with significant coupling
    (≥2 shared cells) are reported.

    Returns proximity pairs sorted by approximate coupling length, plus the
    grid resolution used. Higher-level logic can use this to assess crosstalk
    risk, guard trace needs, or impedance concerns.
    """
    # EQ-057: d = √(Δx²+Δy²) (grid-based proximity scan)
    grid: dict[tuple[str, int, int], set[int]] = {}

    def _mark(x1: float, y1: float, x2: float, y2: float,
              layer: str, net: int) -> None:
        # EQ-046: d = √(Δx²+Δy²) (grid cell marking)
        if net <= 0:
            return
        dx, dy = x2 - x1, y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        if length < 0.001:
            return
        steps = max(1, int(length / (grid_size * 0.5)))
        inv = 1.0 / steps
        for i in range(steps + 1):
            t = i * inv
            gx = int((x1 + t * dx) / grid_size)
            gy = int((y1 + t * dy) / grid_size)
            grid.setdefault((layer, gx, gy), set()).add(net)

    for seg in tracks.get("segments", []):
        _mark(seg["x1"], seg["y1"], seg["x2"], seg["y2"],
              seg["layer"], seg["net"])
    for arc in tracks.get("arcs", []):
        s, e = arc["start"], arc["end"]
        _mark(s[0], s[1], e[0], e[1], arc["layer"], arc["net"])

    # Count shared cells per net pair (signal nets only)
    pair_counts: dict[tuple[str, int, int], int] = {}
    for (_layer, _gx, _gy), nets in grid.items():
        signal = sorted(n for n in nets
                        if not (is_power_net_name(net_names.get(n, "")) or is_ground_name(net_names.get(n, ""))))
        if len(signal) < 2:
            continue
        for i in range(len(signal)):
            for j in range(i + 1, len(signal)):
                pk = (_layer, signal[i], signal[j])
                pair_counts[pk] = pair_counts.get(pk, 0) + 1

    pairs = []
    for (layer, na, nb), count in pair_counts.items():
        if count < 2:
            continue
        pairs.append({
            "net_a": net_names.get(na, f"net_{na}"),
            "net_b": net_names.get(nb, f"net_{nb}"),
            "layer": layer,
            "shared_cells": count,
            "approx_coupling_mm": round(count * grid_size, 1),
        })

    pairs.sort(key=lambda p: p["approx_coupling_mm"], reverse=True)

    return {
        "grid_size_mm": grid_size,
        "proximity_pairs": pairs[:100],
        "total_pairs_found": len(pairs),
    }


def analyze_current_capacity(tracks: dict, vias: dict, zones: list[dict],
                             net_names: dict[int, str],
                             setup: dict) -> dict:
    """Provide facts for current capacity assessment (IPC-2221).

    For each net, reports the minimum track width and total copper cross-section
    data that higher-level logic needs to calculate current capacity using
    IPC-2221 formulas. Also reports via drill sizes per net (vias have lower
    current capacity than tracks of the same width).

    Focuses on power/ground nets where current capacity matters most, but
    also flags any signal net with unusually thin traces for its track count
    (potential bottleneck).
    """
    # Per-net track width data
    net_widths: dict[int, dict] = {}

    for seg in tracks.get("segments", []):
        net = seg["net"]
        if net <= 0:
            continue
        w = seg["width"]
        layer = seg["layer"]
        d = net_widths.setdefault(net, {
            "min_width": float("inf"), "max_width": 0.0,
            "widths": set(), "layers": set(), "segment_count": 0,
            "via_count": 0, "via_drills": set(),
        })
        d["min_width"] = min(d["min_width"], w)
        d["max_width"] = max(d["max_width"], w)
        d["widths"].add(w)
        d["layers"].add(layer)
        d["segment_count"] += 1

    for arc in tracks.get("arcs", []):
        net = arc["net"]
        if net <= 0:
            continue
        w = arc["width"]
        d = net_widths.setdefault(net, {
            "min_width": float("inf"), "max_width": 0.0,
            "widths": set(), "layers": set(), "segment_count": 0,
            "via_count": 0, "via_drills": set(),
        })
        d["min_width"] = min(d["min_width"], w)
        d["max_width"] = max(d["max_width"], w)
        d["widths"].add(w)
        d["layers"].add(arc["layer"])
        d["segment_count"] += 1

    for via in vias.get("vias", []):
        net = via["net"]
        if net <= 0:
            continue
        d = net_widths.setdefault(net, {
            "min_width": float("inf"), "max_width": 0.0,
            "widths": set(), "layers": set(), "segment_count": 0,
            "via_count": 0, "via_drills": set(),
        })
        d["via_count"] += 1
        if via.get("drill"):
            d["via_drills"].add(via["drill"])

    # Zone coverage per net
    net_zones: dict[int, list[dict]] = {}
    for z in zones:
        zn = z.get("net", 0)
        if zn > 0:
            net_zones.setdefault(zn, []).append({
                "layers": z.get("layers", []),
                "filled_area_mm2": z.get("filled_area_mm2"),
                "min_thickness": z.get("min_thickness"),
            })

    # Board thickness for internal layer calculation
    board_thickness = setup.get("board_thickness_mm", 1.6)

    # Build output — power/ground nets first, then any signal nets with
    # narrow traces (potential current bottlenecks)
    power_entries = []
    signal_narrow = []

    for net_num, data in net_widths.items():
        if data["min_width"] == float("inf"):
            continue
        name = net_names.get(net_num, f"net_{net_num}")
        is_power = is_power_net_name(name) or is_ground_name(name)

        entry = {
            "net": name,
            "net_number": net_num,
            "min_track_width_mm": data["min_width"],
            "max_track_width_mm": data["max_width"],
            "track_widths_used": sorted(data["widths"]),
            "copper_layers": sorted(data["layers"]),
            "segment_count": data["segment_count"],
            "via_count": data["via_count"],
        }
        if data["via_drills"]:
            entry["via_drill_sizes_mm"] = sorted(data["via_drills"])

        if net_num in net_zones:
            entry["zones"] = net_zones[net_num]

        if is_power:
            entry["detector"] = "analyze_current_capacity"
            entry["rule_id"] = "CC-DET"
            entry["category"] = "current_capacity"
            entry["severity"] = "info"
            entry["confidence"] = "deterministic"
            entry["evidence_source"] = "topology"
            entry["summary"] = f"Power net {name}: {data['min_width']}mm min trace"
            entry["description"] = (
                f"Power/ground net {name}: min trace {data['min_width']}mm, "
                f"max {data['max_width']}mm, {data['segment_count']} segments."
            )
            entry["components"] = []
            entry["nets"] = [name]
            entry["pins"] = []
            entry["recommendation"] = ""
            entry["report_context"] = {
                "section": "Current Capacity",
                "impact": "Power delivery",
                "standard_ref": "IPC-2221",
            }
            power_entries.append(entry)
        elif data["min_width"] <= 0.15 and data["segment_count"] >= 5:
            # Signal nets with ≤0.15mm traces and significant routing
            entry["detector"] = "analyze_current_capacity"
            entry["rule_id"] = "CC-002"
            entry["category"] = "current_capacity"
            entry["severity"] = "warning"
            entry["confidence"] = "deterministic"
            entry["evidence_source"] = "topology"
            entry["summary"] = f"Narrow signal: {name} min {data['min_width']}mm"
            entry["description"] = (
                f"Signal net {name} has narrow traces: min {data['min_width']}mm "
                f"across {data['segment_count']} segments."
            )
            entry["components"] = []
            entry["nets"] = [name]
            entry["pins"] = []
            entry["recommendation"] = "Widen trace or verify signal integrity requirements."
            entry["report_context"] = {
                "section": "Current Capacity",
                "impact": "Signal integrity",
                "standard_ref": "",
            }
            signal_narrow.append(entry)

    power_entries.sort(key=lambda e: e["net"])
    signal_narrow.sort(key=lambda e: e["min_track_width_mm"])

    return {
        "board_thickness_mm": board_thickness,
        "power_ground_nets": power_entries,
        "narrow_signal_nets": signal_narrow[:20],
    }


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
        return {}

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
            })

    for v in all_vias:
        vx, vy = v["x"], v["y"]
        v_net = v.get("net", 0)
        v_layers = v.get("layers", ["F.Cu", "B.Cu"])
        for pb in pad_boxes:
            # Via must be on the same copper layer as the pad
            if pb["layer"] not in v_layers:
                continue
            if (abs(vx - pb["cx"]) <= pb["hw"] and
                    abs(vy - pb["cy"]) <= pb["hh"]):
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
        if d > 0:
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

    result: dict = {
        "type_breakdown": type_breakdown,
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


def extract_silkscreen(root: list, footprints: list[dict]) -> dict:
    """Extract silkscreen text and check documentation completeness.

    Reports:
    - Board-level text (gr_text on SilkS layers): project name, version, logos
    - Per-footprint reference and user text visibility on silk
    - Text on Fab layers (assembly reference)
    - Documentation audit: missing board name/revision, connector labels,
      switch on/off indicators, polarity markers, pin-1 indicators
    """
    # ---- Board-level silkscreen text ----
    board_texts = []
    for gt in find_all(root, "gr_text"):
        layer = get_value(gt, "layer")
        if not layer:
            continue
        if "SilkS" not in layer and "Silkscreen" not in layer:
            continue
        text = gt[1] if len(gt) > 1 and isinstance(gt[1], str) else ""
        at = get_at(gt)
        board_texts.append({
            "text": text,
            "layer": layer,
            "x": round(at[0], 2) if at else None,
            "y": round(at[1], 2) if at else None,
        })

    # Fab layer text (assembly reference)
    fab_texts = []
    for gt in find_all(root, "gr_text"):
        layer = get_value(gt, "layer")
        if not layer or "Fab" not in layer:
            continue
        text = gt[1] if len(gt) > 1 and isinstance(gt[1], str) else ""
        fab_texts.append({
            "text": text,
            "layer": layer,
        })

    # ---- Per-footprint silkscreen text analysis ----
    # Parse raw footprint nodes for fp_text / property visibility on silk layers
    fp_nodes = find_all(root, "footprint") or find_all(root, "module")

    refs_visible = 0
    refs_hidden = 0
    hidden_refs: list[str] = []
    values_on_silk: list[str] = []
    user_silk_texts: list[dict] = []

    for fp_node in fp_nodes:
        fp_ref = get_property(fp_node, "Reference") or ""
        if not fp_ref:
            for ft in find_all(fp_node, "fp_text"):
                if len(ft) >= 3 and ft[1] == "reference":
                    fp_ref = ft[2]
                    break

        # Check reference visibility on silk (KiCad 9: property nodes, KiCad 5-8: fp_text)
        ref_visible = False
        for prop in find_all(fp_node, "property"):
            if len(prop) >= 3 and prop[1] == "Reference":
                layer = get_value(prop, "layer")
                if layer and ("SilkS" in layer or "Silkscreen" in layer):
                    # Check if hidden via (effects (font ...) hide)
                    effects = find_first(prop, "effects")
                    is_hidden = False
                    if effects:
                        for child in effects:
                            if child == "hide" or (isinstance(child, list) and child[0] == "hide"):
                                is_hidden = True
                                break
                    if not is_hidden:
                        ref_visible = True
                break

        # KiCad 5-8 fp_text check
        if not ref_visible:
            for ft in find_all(fp_node, "fp_text"):
                if len(ft) >= 3 and ft[1] == "reference":
                    layer = get_value(ft, "layer")
                    if layer and ("SilkS" in layer or "Silkscreen" in layer):
                        effects = find_first(ft, "effects")
                        is_hidden = False
                        if effects:
                            for child in effects:
                                if child == "hide" or (isinstance(child, list) and child[0] == "hide"):
                                    is_hidden = True
                                    break
                        if not is_hidden:
                            ref_visible = True
                    break

        if ref_visible:
            refs_visible += 1
        else:
            refs_hidden += 1
            if fp_ref:
                hidden_refs.append(fp_ref)

        # Check for value text visible on silk (common mistake — clutters board)
        for ft in find_all(fp_node, "fp_text"):
            if len(ft) >= 3 and ft[1] == "value":
                layer = get_value(ft, "layer")
                if layer and ("SilkS" in layer or "Silkscreen" in layer):
                    effects = find_first(ft, "effects")
                    is_hidden = False
                    if effects:
                        for child in effects:
                            if child == "hide" or (isinstance(child, list) and child[0] == "hide"):
                                is_hidden = True
                                break
                    if not is_hidden and fp_ref:
                        values_on_silk.append(fp_ref)

        # Also check property nodes for value on silk (KiCad 9)
        for prop in find_all(fp_node, "property"):
            if len(prop) >= 3 and prop[1] == "Value":
                layer = get_value(prop, "layer")
                if layer and ("SilkS" in layer or "Silkscreen" in layer):
                    effects = find_first(prop, "effects")
                    is_hidden = False
                    if effects:
                        for child in effects:
                            if child == "hide" or (isinstance(child, list) and child[0] == "hide"):
                                is_hidden = True
                                break
                    if not is_hidden and fp_ref and fp_ref not in values_on_silk:
                        values_on_silk.append(fp_ref)

        # Collect user-placed silk text within footprints (fp_text user "...")
        for ft in find_all(fp_node, "fp_text"):
            if len(ft) >= 3 and ft[1] == "user":
                layer = get_value(ft, "layer")
                if layer and ("SilkS" in layer or "Silkscreen" in layer):
                    effects = find_first(ft, "effects")
                    is_hidden = False
                    if effects:
                        for child in effects:
                            if child == "hide" or (isinstance(child, list) and child[0] == "hide"):
                                is_hidden = True
                                break
                    if not is_hidden:
                        user_silk_texts.append({
                            "footprint": fp_ref,
                            "text": ft[2],
                        })

    # ---- Documentation audit ----
    # Combine all visible silk text for checking
    all_silk_text = [t["text"] for t in board_texts]
    all_silk_text.extend(t["text"] for t in user_silk_texts)
    all_silk_upper = " ".join(t.upper() for t in all_silk_text)

    documentation_warnings = []

    # Check for board name / project name on silk
    has_board_name = False
    for t in board_texts:
        txt = t["text"].upper()
        # Common board name patterns: not just "REF**" or coordinates
        if txt and txt not in ("REF**", "${REFERENCE}") and len(txt) >= 3:
            has_board_name = True
            break
    if not has_board_name:
        documentation_warnings.append({
            "type": "missing_board_name",
            "severity": "suggestion",
            "message": "No board name or project identifier found in silkscreen text. "
                       "Consider adding the board name for easy identification.",
        })

    # Check for revision marking
    # KH-166: check title block rev field first (authoritative source)
    tb = find_first(root, "title_block")
    tb_rev = get_value(tb, "rev") if tb else None
    has_revision = bool(tb_rev)

    if not has_revision:
        rev_pattern = re.compile(r'\b(?:REV|VER|VERSION)\b|(?<!\w)[RV]\d', re.IGNORECASE)
        has_revision = any(rev_pattern.search(t) for t in all_silk_text)

    if not has_revision:
        documentation_warnings.append({
            "type": "missing_revision",
            "severity": "warning",
            "message": "No revision marking found in silkscreen. "
                       "Add a revision label (e.g., 'Rev A', 'V1.0') to track board versions.",
        })

    # ---- Component-specific documentation checks ----
    # Build lookup of which footprints have user silk text nearby
    fp_user_texts: dict[str, list[str]] = {}
    for ut in user_silk_texts:
        fp_user_texts.setdefault(ut["footprint"], []).append(ut["text"].upper())

    # Classify footprints by type for targeted checks
    switches = []
    connectors = []
    polarized = []  # LEDs, electrolytic caps, diodes
    test_points = []

    for fp in footprints:
        ref = fp.get("reference", "")
        lib = fp.get("library", "").lower()
        val = fp.get("value", "")
        # KH-102: Defensive coercion — some PCB files have list-typed value fields
        if isinstance(val, list):
            val = str(val[1]) if len(val) > 1 else ""
        val = val.lower()

        if not ref:
            continue
        prefix = ""
        for c in ref:
            if c.isalpha():
                prefix += c
            else:
                break

        if prefix in ("SW", "S", "BUT"):
            switches.append(ref)
        elif prefix in ("J", "P", "CN"):
            connectors.append(ref)
        elif prefix in ("D", "LED"):
            polarized.append(ref)
        elif prefix == "BT":
            polarized.append(ref)
        elif prefix == "TP":
            test_points.append(ref)
        elif prefix in ("C",):
            # Check if it's a polarized cap (electrolytic/tantalum)
            if any(kw in lib for kw in ("cp", "polarized", "elec", "tant")):
                polarized.append(ref)
            elif any(kw in val for kw in ("elec", "tant", "polarized")):
                polarized.append(ref)

    # Switches: check for on/off or function labels
    switches_without_labels = []
    for ref in switches:
        texts = fp_user_texts.get(ref, [])
        has_label = any(
            any(kw in t for kw in ("ON", "OFF", "RESET", "BOOT", "PWR", "POWER",
                                    "PUSH", "SW", "PROG", "FUNC", "MODE"))
            for t in texts
        )
        # Also check board-level texts near the switch
        if not has_label:
            switches_without_labels.append(ref)

    if switches_without_labels:
        documentation_warnings.append({
            "type": "missing_switch_labels",
            "severity": "warning",
            "components": switches_without_labels,
            "message": f"Switches without function labels on silkscreen: {switches_without_labels}. "
                       "Add ON/OFF, RESET, BOOT, or function description near each switch.",
        })

    # Connectors: check for pin-1 / signal name labels
    connectors_without_labels = []
    for ref in connectors:
        texts = fp_user_texts.get(ref, [])
        # Connectors with 3+ pins should have some labeling
        fp_data = next((f for f in footprints if f.get("reference") == ref), None)
        if fp_data and fp_data.get("pad_count", 0) >= 3:
            if not texts:
                connectors_without_labels.append(ref)

    if connectors_without_labels:
        documentation_warnings.append({
            "type": "missing_connector_labels",
            "severity": "suggestion",
            "components": connectors_without_labels,
            "message": f"Connectors (3+ pins) without silkscreen labels: {connectors_without_labels}. "
                       "Consider adding pin names, signal names, or connector function labels.",
        })

    # Polarized components: polarity markers are usually in the footprint itself
    # (dot, line, +/-) but we flag if there are many polarized parts for awareness
    if len(polarized) > 3:
        documentation_warnings.append({
            "type": "polarity_reminder",
            "severity": "info",
            "components": polarized,
            "message": f"{len(polarized)} polarized components (LEDs, diodes, batteries, "
                       "electrolytic caps). Verify polarity markers are visible on silkscreen.",
        })

    # ---- Assemble result ----
    result: dict = {
        "board_text_count": len(board_texts),
        "refs_visible_on_silk": refs_visible,
        "refs_hidden_on_silk": refs_hidden,
    }
    if board_texts:
        result["board_texts"] = board_texts
    if fab_texts:
        result["fab_texts"] = fab_texts[:20]
    if hidden_refs:
        result["hidden_refs"] = sorted(hidden_refs)[:30]
    if values_on_silk:
        result["values_visible_on_silk"] = sorted(values_on_silk)
    if user_silk_texts:
        result["user_silk_texts"] = user_silk_texts[:30]
    if documentation_warnings:
        result["documentation_warnings"] = documentation_warnings

    # ---- Fab notes completeness ----
    _fab_all_text = " ".join(t.get("text", "") for t in fab_texts).lower()
    _fab_notes_checklist = {
        "ipc_class": bool(re.search(r'ipc[-\s]*\d{4}|class\s*[123]', _fab_all_text)),
        "surface_finish": any(k in _fab_all_text for k in
                              ("enig", "hasl", "osp", "immersion", "surface finish")),
        "board_thickness": bool(re.search(r'\d+\.?\d*\s*mm.*thick|thickness', _fab_all_text)),
        "copper_weight": any(k in _fab_all_text for k in
                             ("1oz", "2oz", "1 oz", "2 oz", "copper weight", "35um", "70um")),
        "solder_mask": any(k in _fab_all_text for k in
                           ("solder mask", "soldermask", "mask color", "green", "black", "white", "blue")),
        "material": any(k in _fab_all_text for k in
                        ("fr4", "fr-4", "rogers", "isola", "material")),
    }
    _fab_missing = [k.replace("_", " ") for k, v in _fab_notes_checklist.items() if not v]
    result["fab_notes_completeness"] = {
        "checks": _fab_notes_checklist,
        "missing": _fab_missing,
        "completeness_pct": round(sum(_fab_notes_checklist.values()) / len(_fab_notes_checklist) * 100),
        "status": "pass" if not _fab_missing else "warning",
    }

    # ---- Silkscreen completeness ----
    _total_refs = refs_visible + refs_hidden
    _silk_checks = {
        "revision_marking": has_revision,
        "board_name": has_board_name,
        "ref_designators_visible": (refs_visible / _total_refs >= 0.9) if _total_refs > 0 else False,
        "connector_labels": len(connectors_without_labels) == 0,
        "polarity_markers": not any(
            w["type"] == "polarity_reminder" for w in documentation_warnings
        ),
    }
    _silk_missing = [k.replace("_", " ") for k, v in _silk_checks.items() if not v]
    result["silkscreen_completeness"] = {
        "checks": _silk_checks,
        "missing": _silk_missing,
        "completeness_pct": round(sum(_silk_checks.values()) / len(_silk_checks) * 100),
        "status": "pass" if not _silk_missing else "warning",
    }

    return result


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

            # Use courtyard if available for tighter estimate
            if fp.get("courtyard"):
                cy_box = fp["courtyard"]
                min_edge = min(
                    cy_box["min_x"] - bx_min,
                    bx_max - cy_box["max_x"],
                    cy_box["min_y"] - by_min,
                    by_max - cy_box["max_y"],
                )

            if min_edge < 1.0:  # Flag components within 1mm of edge
                clearance = round(min_edge, 2)
                # RF module footprints deliberately put the courtyard past the
                # board edge to expose the antenna to free space (WROOM-1 etc.).
                # Edge-mount footprints (SMA_Edge, USB_C vertical, MagJack,
                # microSD, BarrelJack, mounting holes, etc.) belong at the
                # board edge by design. Both demote the edge-clearance finding
                # to info with a hint.
                is_rf = _is_rf_module(fp)
                is_edge_mount = _is_edge_mount_footprint(fp)
                if is_rf:
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
                if clearance < 0 and not is_rf and not is_edge_mount:
                    # KH-344: negative clearance means the courtyard overhangs
                    # the outline — "move further from edge" is nonsense there.
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


def analyze_layer_transitions(tracks: dict, vias: dict,
                               net_names: dict[int, str]) -> list[dict]:
    """Identify signal net layer transitions (via usage patterns).

    For ground return path analysis, higher-level logic needs to know which
    signal nets change layers and where. A via forces the return current to
    find a path between layers — if there's no nearby stitching via on the
    reference plane, the return current loop area increases, raising EMI.

    Reports per-net: which layers are used, how many vias, and whether the
    net uses more than one copper layer (indicating layer transitions).
    """
    net_layers: dict[int, dict] = {}

    for seg in tracks.get("segments", []):
        net = seg["net"]
        if net <= 0:
            continue
        d = net_layers.setdefault(net, {"layers": set(), "vias": []})
        d["layers"].add(seg["layer"])

    for arc in tracks.get("arcs", []):
        net = arc["net"]
        if net <= 0:
            continue
        d = net_layers.setdefault(net, {"layers": set(), "vias": []})
        d["layers"].add(arc["layer"])

    for via in vias.get("vias", []):
        net = via["net"]
        if net <= 0 or net not in net_layers:
            continue
        net_layers[net]["vias"].append({
            "x": via["x"], "y": via["y"],
            "layers": via.get("layers", ["F.Cu", "B.Cu"]),
            "drill": via.get("drill", 0),
        })

    # Only report nets with layer transitions (multi-layer routing)
    result = []
    for net_num, data in sorted(net_layers.items()):
        if len(data["layers"]) < 2:
            continue
        name = net_names.get(net_num, f"net_{net_num}")
        if is_power_net_name(name) or is_ground_name(name):
            continue  # Power/ground layer transitions are expected

        entry = {
            "net": name,
            "net_number": net_num,
            "copper_layers": sorted(data["layers"]),
            "layer_count": len(data["layers"]),
            "via_count": len(data["vias"]),
        }
        if data["vias"]:
            entry["via_positions"] = [
                {"x": round(v["x"], 2), "y": round(v["y"], 2),
                 "layers": v["layers"]}
                for v in data["vias"]
            ]
        result.append(entry)

    result.sort(key=lambda e: e["via_count"], reverse=True)
    return result


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


def extract_board_metadata(root: list) -> dict:
    """Extract board-level metadata — title block, properties, paper size.

    Reports: title, revision, date, company, comments, board-level custom
    properties (e.g. COPYRIGHT, VERSION), and paper size.
    """
    result: dict = {}

    # Paper size
    paper = get_value(root, "paper")
    if paper:
        result["paper"] = paper

    # Title block
    tb = find_first(root, "title_block")
    if tb:
        for field in ("title", "date", "rev", "company"):
            val = get_value(tb, field)
            if val:
                result[field] = val
        # Comments (up to 9)
        for comment in find_all(tb, "comment"):
            if len(comment) >= 3:
                result.setdefault("comments", {})[comment[1]] = comment[2]

    # Board-level properties (KiCad 8+)
    for prop in find_all(root, "property"):
        if len(prop) >= 3 and isinstance(prop[1], str) and isinstance(prop[2], str):
            result.setdefault("properties", {})[prop[1]] = prop[2]

    return result


def extract_dimensions(root: list) -> list[dict]:
    """Extract dimension annotations (designer-placed measurements).

    These are verified measurements placed by the designer — connector spacing,
    board dimensions, mounting hole distances, etc.
    """
    dims = []
    for dim in find_all(root, "dimension"):
        dim_info: dict = {}

        # The measurement value (first numeric element after keyword)
        if len(dim) > 1:
            try:
                dim_info["value_mm"] = round(float(dim[1]), 3)
            except (ValueError, TypeError):
                pass

        layer = get_value(dim, "layer")
        if layer:
            dim_info["layer"] = layer

        # Dimension type (KiCad 8+)
        dtype = get_value(dim, "type")
        if dtype:
            dim_info["type"] = dtype

        # Text label
        gr_text = find_first(dim, "gr_text")
        if gr_text and len(gr_text) > 1:
            dim_info["text"] = gr_text[1]

        # Feature line endpoints (where the measurement spans)
        for feat in ("feature1", "feature2"):
            feat_node = find_first(dim, feat)
            if feat_node:
                pts = find_first(feat_node, "pts")
                if pts:
                    xys = find_all(pts, "xy")
                    if xys:
                        dim_info.setdefault("endpoints", []).append(
                            [round(float(xys[0][1]), 3),
                             round(float(xys[0][2]), 3)])

        if dim_info:
            dims.append(dim_info)
    return dims


def extract_groups(root: list) -> list[dict]:
    """Extract group definitions (designer-defined component/routing groups)."""
    groups = []
    for group in find_all(root, "group"):
        name = group[1] if len(group) > 1 and isinstance(group[1], str) else ""
        members_node = find_first(group, "members")
        member_count = 0
        if members_node:
            member_count = len([m for m in members_node[1:]
                                if isinstance(m, str)])
        if member_count > 0 or name:
            groups.append({
                "name": name,
                "member_count": member_count,
            })
    return groups


def extract_net_classes(root: list) -> list[dict]:
    """Extract net class definitions (KiCad 5 format — stored in PCB file).

    In KiCad 6+, net classes moved to .kicad_pro (JSON). This function handles
    the legacy format where they appear as (net_class ...) in the PCB.
    """
    classes = []
    for nc in find_all(root, "net_class"):
        if len(nc) < 3:
            continue
        name = nc[1]
        description = nc[2] if len(nc) > 2 and isinstance(nc[2], str) else ""

        info: dict = {"name": name}
        if description:
            info["description"] = description

        # Design rule values
        for key in ("clearance", "trace_width", "via_dia", "via_drill",
                     "uvia_dia", "uvia_drill"):
            val = get_value(nc, key)
            if val:
                info[key] = float(val)

        # Net assignments
        nets = []
        for item in find_all(nc, "add_net"):
            if len(item) > 1:
                nets.append(item[1])
        if nets:
            info["nets"] = nets
            info["net_count"] = len(nets)

        classes.append(info)
    return classes


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
    # JLCPCB standard process limits (mm)
    # Source: JLCPCB capabilities page, verified 2025-01.
    # Canonical table in references/standards-compliance.md "Fab House Capabilities"
    LIMITS_STD = {
        "min_track_width": 0.127,      # 5 mil — JLCPCB standard tier
        "min_track_spacing": 0.127,     # 5 mil — JLCPCB standard tier
        "min_drill": 0.2,              # PTH drill — JLCPCB standard tier
        "min_annular_ring": 0.125,     # via annular ring — JLCPCB standard tier
        "max_board_width": 100.0,      # pricing threshold (>100mm costs more)
        "max_board_height": 100.0,
        "min_board_dim": 10.0,         # handling minimum
    }
    # JLCPCB advanced process limits (mm)
    LIMITS_ADV = {
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

    # Determine active IPC class
    ipc_class = 2  # default
    if design_intent and design_intent.get('ipc_class') in (1, 2, 3):
        ipc_class = design_intent['ipc_class']
    ipc_limits = IPC_CLASS_LIMITS[ipc_class]

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

    violations = []
    metrics: dict = {}

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

    if all_widths:
        min_width = min(all_widths)
        metrics["min_track_width_mm"] = min_width

        check_width = (narrowest_non_class
                       if narrowest_non_class < float('inf')
                       else min_width)

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

    # --- Track spacing analysis (approximate from segment proximity) ---
    # Build spatial grid to find close tracks on the same layer
    segments = tracks.get("segments", [])
    if len(segments) > 1:
        min_spacing = float("inf")
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

        if min_spacing < float("inf"):
            metrics["approx_min_spacing_mm"] = round(min_spacing, 4)
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

    # --- Via drill analysis ---
    all_vias = vias.get("vias", [])
    if all_vias:
        drills = [v["drill"] for v in all_vias if v.get("drill", 0) > 0]
        if drills:
            min_drill = min(drills)
            metrics["min_drill_mm"] = min_drill
            if min_drill < LIMITS_ADV["min_drill"]:
                violations.append({
                    "parameter": "via_drill",
                    "actual_mm": min_drill,
                    "standard_limit_mm": LIMITS_STD["min_drill"],
                    "advanced_limit_mm": LIMITS_ADV["min_drill"],
                    "tier_required": "challenging",
                    "message": f"Via drill {min_drill}mm is below advanced process "
                               f"minimum ({LIMITS_ADV['min_drill']}mm)",
                    "detector": "analyze_dfm",
                    "rule_id": "DFM-001",
                    "category": "dfm",
                    "severity": "error",
                    "confidence": "deterministic",
                    "evidence_source": "topology",
                    "summary": f"Via drill {min_drill}mm below advanced minimum ({LIMITS_ADV['min_drill']}mm)",
                    "description": f"Via drill {min_drill}mm is below the advanced process minimum of {LIMITS_ADV['min_drill']}mm, requiring a challenging fab tier.",
                    "components": [],
                    "nets": [],
                    "pins": [],
                    "recommendation": f"Via drill {min_drill}mm is below advanced process minimum ({LIMITS_ADV['min_drill']}mm)",
                    "report_context": {"section": "DFM", "impact": "manufacturability", "standard_ref": ""},
                })
            elif min_drill < LIMITS_STD["min_drill"]:
                violations.append({
                    "parameter": "via_drill",
                    "actual_mm": min_drill,
                    "standard_limit_mm": LIMITS_STD["min_drill"],
                    "advanced_limit_mm": LIMITS_ADV["min_drill"],
                    "tier_required": "advanced",
                    "message": f"Via drill {min_drill}mm requires advanced process "
                               f"(standard: {LIMITS_STD['min_drill']}mm)",
                    "detector": "analyze_dfm",
                    "rule_id": "DFM-001",
                    "category": "dfm",
                    "severity": "warning",
                    "confidence": "deterministic",
                    "evidence_source": "topology",
                    "summary": f"Via drill {min_drill}mm requires advanced process (standard: {LIMITS_STD['min_drill']}mm)",
                    "description": f"Via drill {min_drill}mm is below the standard process minimum of {LIMITS_STD['min_drill']}mm, requiring an advanced fab tier.",
                    "components": [],
                    "nets": [],
                    "pins": [],
                    "recommendation": f"Via drill {min_drill}mm requires advanced process (standard: {LIMITS_STD['min_drill']}mm)",
                    "report_context": {"section": "DFM", "impact": "manufacturability", "standard_ref": ""},
                })

    # --- Annular ring analysis ---
    rings = []
    if all_vias:
        for v in all_vias:
            size = v.get("size", 0)
            drill = v.get("drill", 0)
            if size > 0 and drill > 0:
                rings.append(round((size - drill) / 2.0, 3))
        if rings:
            min_ring = min(rings)
            metrics["min_annular_ring_mm"] = min_ring
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

    # --- Board dimensions assessment ---
    bbox = board_outline.get("bounding_box")
    if bbox:
        width = bbox.get("width", 0)
        height = bbox.get("height", 0)
        metrics["board_width_mm"] = width
        metrics["board_height_mm"] = height

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

    # --- Determine overall DFM tier ---
    tier = "standard"
    for v in violations:
        req = v.get("tier_required", "standard")
        if req == "challenging":
            tier = "challenging"
            break
        elif req == "advanced" and tier != "challenging":
            tier = "advanced"

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
) -> dict | None:
    """Check layout against project-defined design rules.

    Compares actual track widths, via sizes, and drill diameters against
    the designer's own rules from ``.kicad_pro`` (global minimums) and
    ``.kicad_dru`` (per-context constraints).  Returns None if no
    project rules are available.

    This is separate from DFM analysis — DFM checks fab capabilities
    (can this be manufactured?), while this checks design intent
    (did I follow my own rules?).
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
    via_drills = [v["drill"] for v in all_vias if v.get("drill", 0) > 0]
    min_via_diameter = min(via_diameters) if via_diameters else None
    min_via_drill = min(via_drills) if via_drills else None

    # --- Check .kicad_pro global minimums ---
    checks = [
        ('min_track_width', min_track_width, design_rules.get('min_track_width')),
        ('min_via_diameter', min_via_diameter, design_rules.get('min_via_diameter')),
        ('min_via_drill', min_via_drill,
         design_rules.get('min_through_hole_diameter')
         or design_rules.get('min_via_drill')),
    ]
    for rule_name, actual, required in checks:
        if actual is None or required is None:
            continue
        rules_checked += 1
        if actual < required - 0.001:  # 1µm tolerance for float comparison
            violations.append({
                'rule': rule_name,
                'source': 'project',
                'required_mm': round(required, 4),
                'actual_mm': round(actual, 4),
                'message': (f"{rule_name.replace('_', ' ').title()} "
                            f"{actual:.3f}mm violates project minimum "
                            f"({required:.3f}mm)"),
            })

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
    # We don't evaluate condition expressions, but we can check
    # unconditional global constraints from .kicad_dru
    if custom_rules:
        for rule in custom_rules:
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
                elif ctype == 'hole_size' and min_via_drill is not None:
                    actual = min_via_drill
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
                        violations.append({
                            'rule': f"custom:{rule.get('name', ctype)}",
                            'source': 'kicad_dru',
                            'required_mm': round(cmin, 4),
                            'actual_mm': round(actual, 4),
                            'constraint_type': ctype,
                            'message': (f"Custom rule \"{rule.get('name', '')}\" "
                                        f"requires {ctype} >= {cmin:.3f}mm, "
                                        f"actual {actual:.3f}mm"),
                        })

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

    return result


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

            # Count vias within the thermal pad area
            # Account for footprint + pad rotation: the pad's width/height are
            # in the footprint's local coordinate frame, but the via positions
            # are in board space.  Rotate the via-to-pad offset back into the
            # pad's local frame for the rectangular containment check.
            fp_angle = fp.get("angle", 0)
            pad_angle = pad.get("angle", 0)
            total_angle = fp_angle + pad_angle
            total_rad = math.radians(-total_angle) if total_angle != 0 else 0.0
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


def _nearest_zone_copper_distance(fx: float, fy: float, fp_layer: str,
                                  gnd_zones: list) -> tuple:
    """Distance from a point to the nearest same-layer GND zone copper.

    KH-339: prefers filled_bbox (actual copper) over outline_bbox — the
    zone outline routinely overstates copper reach. Returns (distance,
    basis) where basis is 'filled_bbox' or 'outline_bbox' (None if no
    candidate zone).
    """
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
        is_touch = (ref.upper().startswith("TP")
                    or "touch" in lib or "capacitive" in lib)
        if not is_touch:
            continue
        fx, fy = fp.get("x", 0), fp.get("y", 0)
        fp_layer = fp.get("layer", "F.Cu")
        min_dist, _basis = _nearest_zone_copper_distance(fx, fy, fp_layer,
                                                         gnd_zones)
        if min_dist < float('inf'):
            _conf = "deterministic" if _basis == "filled_bbox" else "heuristic"
            _note = ("" if _basis == "filled_bbox" else
                     " (zone outline basis — fill data unavailable; actual "
                     "copper may be farther)")
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
                "nets": [],
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


def _point_in_pad(vx: float, vy: float, px: float, py: float,
                  width: float, height: float, shape: str,
                  pad_angle: float) -> bool:
    """Point-in-pad test for VP-001 (KH-340): circle/oval exact, other
    shapes as a rotated bounding rect. Pad `at` angles in .kicad_pcb are
    absolute (they already include the footprint rotation)."""
    dx = vx - px
    dy = vy - py
    if pad_angle:
        # Inverse of the local->absolute rotation used in extract_footprints
        rad = math.radians(-pad_angle)
        c, s = math.cos(rad), math.sin(rad)
        dx, dy = dx * c + dy * s, -dx * s + dy * c
    hw = width / 2
    hh = height / 2
    if shape == "circle":
        r = max(hw, hh)
        return dx * dx + dy * dy <= r * r
    if shape == "oval":
        # Stadium: center rect capped by semicircles of radius min(hw, hh)
        r = min(hw, hh)
        if hw >= hh:
            cx = max(abs(dx) - (hw - r), 0.0)
            return cx * cx + dy * dy <= r * r
        cy = max(abs(dy) - (hh - r), 0.0)
        return dx * dx + cy * cy <= r * r
    # rect / roundrect / trapezoid / custom: rotated bounding rect
    return abs(dx) <= hw and abs(dy) <= hh


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
                via_layers = via.get("layers", [])
                # A via is tented if it has solder mask coverage (heuristic: look for F.Mask/B.Mask)
                # KiCad doesn't export tenting directly in kicad_pcb; approximate from remove_unused_layers
                tented = via.get("remove_unused_layers", False)
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


def analyze_pcb(path: str, *, proximity: bool = False,
                include_trace_segments: bool = False,
                schematic_data: dict = None,
                return_path_radius_mm: float = 0.5,
                gp001_debug: bool = False) -> dict:
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
    """
    root = parse_file(path)

    layers = extract_layers(root)
    setup = extract_setup(root)
    net_names = extract_nets(root)
    footprints = extract_footprints(root)
    tracks = extract_tracks(root)
    vias = extract_vias(root)
    zones, zone_fills = extract_zones(root)
    outline = extract_board_outline(root)

    # KiCad 10: no net declarations — build synthetic mapping from content
    if not net_names:
        net_names = _build_net_mapping(footprints, tracks, vias, zones)
        # Backfill net IDs now that the mapping is built
        for seg in tracks.get("segments", []):
            if "_net_name" in seg:
                seg["net"] = _net_id(seg.pop("_net_name"))
        for arc in tracks.get("arcs", []):
            if "_net_name" in arc:
                arc["net"] = _net_id(arc.pop("_net_name"))
        for v in vias.get("vias", []):
            if "_net_name" in v:
                v["net"] = _net_id(v.pop("_net_name"))
        for z in zones:
            z["net"] = _net_id(z.get("net_name", ""))
        for fp in footprints:
            for pad in fp.get("pads", []):
                if pad.get("net_name") and pad.get("net_number", 0) == 0:
                    pad["net_number"] = _net_id(pad["net_name"])

    # Connectivity analysis (zone-aware)
    connectivity = analyze_connectivity(footprints, tracks, vias, net_names, zones)

    stats = compute_statistics(footprints, tracks, vias, zones, outline, connectivity, net_names, layers=layers)

    version = get_value(root, "version") or "unknown"
    generator_version = get_value(root, "generator_version") or "unknown"

    # Component grouping by reference prefix
    component_groups = group_components(footprints)

    # Per-net trace length measurement
    # Pass stackup for impedance calculation. If no stackup defined, use
    # a default 2-layer FR4 board (1.6mm total, 1oz copper, εr=4.5).
    _stackup = setup.get("stackup")
    if include_trace_segments and not _stackup:
        _stackup = [
            {"name": "F.Cu", "type": "copper", "thickness": 0.035},
            {"name": "dielectric", "type": "core", "thickness": 1.53,
             "epsilon_r": 4.5, "material": "FR4"},
            {"name": "B.Cu", "type": "copper", "thickness": 0.035},
        ]
    net_lengths = analyze_net_lengths(tracks, vias, net_names,
                                      include_segments=include_trace_segments,
                                      stackup=_stackup if include_trace_segments else None)

    # Power net routing analysis
    power_routing = analyze_power_nets(footprints, tracks, net_names)

    # Pad-to-pad routed distance analysis (only with --full, needs segment data)
    pad_distances = None
    if include_trace_segments:
        pad_distances = analyze_pad_to_pad_distances(
            footprints, tracks, vias, net_names)

    # Decoupling placement analysis
    decoupling = analyze_decoupling_placement(footprints)

    # Ground domain identification
    ground_domains = analyze_ground_domains(footprints, net_names, zones)

    # Current capacity facts
    current_capacity = analyze_current_capacity(tracks, vias, zones, net_names, setup)

    # Via analysis (types, annular ring, via-in-pad, fanout, current)
    via_analysis = analyze_vias(vias, footprints, net_names)

    # Thermal / via stitching analysis
    thermal = analyze_thermal_vias(footprints, vias, zones)

    # Layer transitions for ground return path analysis
    layer_transitions = analyze_layer_transitions(tracks, vias, net_names)

    # Placement analysis (courtyard overlaps, edge clearance, density)
    placement = analyze_placement(footprints, outline)

    # Silkscreen text extraction
    silkscreen = extract_silkscreen(root, footprints)

    # Board metadata (title block, properties, paper size)
    metadata = extract_board_metadata(root)

    # Dimension annotations
    dimensions = extract_dimensions(root)

    # Groups (designer-defined component/routing groupings)
    groups = extract_groups(root)

    # Net classes — try .kicad_pro first (KiCad 6+), fall back to PCB file (KiCad 5)
    pro = load_kicad_pro(str(path))
    project_settings = {}
    if pro:
        pro_net_classes = extract_pro_net_classes(pro)
        if pro_net_classes:
            net_classes = pro_net_classes
        else:
            net_classes = extract_net_classes(root)
        pro_rules = extract_pro_design_rules(pro)
        pro_text_vars = extract_pro_text_variables(pro)
        pcb_dir = os.path.dirname(str(path)) or '.'
        project_settings = {
            'source': os.path.basename(
                next((os.path.join(pcb_dir, f)
                      for f in os.listdir(pcb_dir)
                      if f.endswith('.kicad_pro')), '')),
        }
        if pro_net_classes:
            project_settings['net_classes'] = pro_net_classes
        if pro_rules:
            project_settings['design_rules'] = pro_rules
        if pro_text_vars:
            project_settings['text_variables'] = pro_text_vars
    else:
        net_classes = extract_net_classes(root)

    # Custom design rules (.kicad_dru)
    custom_rules = load_kicad_dru(str(path))
    if custom_rules:
        project_settings['custom_rules'] = custom_rules

    # Library tables
    lib_tables = load_lib_tables(str(path))
    if lib_tables.get('footprint_libs'):
        project_settings['footprint_libs'] = lib_tables['footprint_libs']

    # DFM (Design for Manufacturing) scoring
    design_rules = (project_settings.get('design_rules')
                    or setup.get("design_rules"))
    dfm = analyze_dfm(footprints, tracks, vias, outline, design_rules,
                       net_classes=net_classes, design_intent=None)

    # Tombstoning risk assessment for small passives
    tombstoning = analyze_tombstoning_risk(footprints, tracks, vias, zones)

    # Thermal pad via adequacy for QFN/BGA packages
    thermal_pad_vias = analyze_thermal_pad_vias(footprints, vias, zones, zone_fills)

    # Build reference layer map from stackup for multi-layer boards
    ref_layer_map = _build_reference_layer_map(setup.get("stackup", []))

    # Copper presence analysis (cross-layer zone fill at pad locations)
    copper_presence = analyze_copper_presence(footprints, zones, zone_fills,
                                              ref_layer_map=ref_layer_map)

    # Return path continuity (only with --full, expensive)
    return_path = None
    gp001_samples = [] if gp001_debug else None
    if include_trace_segments and zone_fills.has_data:
        return_path = analyze_return_path_continuity(
            tracks, net_names, zones, zone_fills,
            ref_layer_map=ref_layer_map,
            footprints=footprints,
            radius_mm=return_path_radius_mm,
            debug_samples=gp001_samples)

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
        "keepout_zones": _extract_keepout_zones(zones, footprints),
        "connectivity": connectivity,
        "net_lengths": net_lengths,
    }

    if pad_distances:
        result["pad_to_pad_distances"] = pad_distances
    # TH-043-residual: always emit (schema-required); empty list when no power routing.
    result["power_net_routing"] = power_routing if power_routing else []
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
        result["trace_proximity"] = analyze_trace_proximity(tracks, net_names)

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
            tracks, vias, project_settings)
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
    fiducial_check = analyze_fiducials(footprints)
    if fiducial_check.get("findings"):
        result["fiducial_check"] = fiducial_check

    test_point_cov = analyze_test_point_coverage(footprints, net_names)
    result["test_point_coverage"] = test_point_cov

    orientation = analyze_orientation_consistency(footprints)
    if orientation:
        result["orientation_consistency"] = orientation

    silkscreen_overlaps = analyze_silkscreen_pad_overlaps(
        footprints, silkscreen.get("board_texts", []))
    if silkscreen_overlaps:
        result["silkscreen_pad_overlaps"] = silkscreen_overlaps

    keepout_list = result.get("keepout_zones", [])
    keepout_violations = analyze_keepout_violations(footprints, vias, keepout_list)
    if keepout_violations:
        result["keepout_violations"] = keepout_violations

    if include_trace_segments:
        via_in_pad = analyze_via_in_pad(
            footprints, vias,
            {e.get("component", "") for e in (thermal_pad_vias or [])})
        if via_in_pad:
            result["via_in_pad_issues"] = via_in_pad

        edge_via = analyze_board_edge_via_clearance(vias, outline)
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
        except Exception:
            pass  # Non-critical — degrade gracefully

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

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="KiCad PCB Layout Analyzer")
    parser.add_argument("pcb", nargs="?",
                        help="Path to .kicad_pcb, .kicad_pro, or project directory")
    parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")
    parser.add_argument("--compact", action="store_true", help="Compact JSON output")
    parser.add_argument("--full", action="store_true",
                        help="Include individual track/via coordinate data")
    parser.add_argument("--proximity", action="store_true",
                        help="Run trace proximity analysis for crosstalk assessment")
    parser.add_argument("--schema", action="store_true",
                        help="Print JSON output schema and exit")
    parser.add_argument("--config", default=None,
                        help="Path to .kicad-happy.json project config file")
    parser.add_argument("--analysis-dir", default=None,
                        help="Write output to analysis cache directory (timestamped runs)")
    parser.add_argument("--schematic",
                        help="Schematic analysis JSON for cross-analyzer enrichment")
    parser.add_argument("--text", action="store_true",
                        help="Print human-readable text report to stdout")
    parser.add_argument('--stage', default=None,
                        choices=['schematic', 'layout', 'pre_fab', 'bring_up'],
                        help='Filter findings by review stage')
    parser.add_argument('--audience', default=None,
                        choices=['designer', 'reviewer', 'manager'],
                        help='Audience level for summaries and --text output')
    parser.add_argument('--return-path-radius-mm', type=float, default=0.5,
                        help='Radius (mm) for copper-presence in return-path analysis (default: 0.5)')
    parser.add_argument('--gp001-debug', action='store_true',
                        help='Emit per-sample diagnostic JSON to analysis dir')
    parser.add_argument('--only-deterministic', action='store_true',
                        help='Accepted for consistency; analyzers never write llm_* fields. '
                             'Honored by downstream consumers (Phase 4 spec §3.4).')
    args = parser.parse_args()

    if args.schema:
        emit_schema(PCBEnvelope)

    if not args.pcb:
        parser.error("the following arguments are required: pcb")

    # Resolve .kicad_pro or directory to the .kicad_pcb file
    from kicad_utils import resolve_project_input
    try:
        resolved, note = resolve_project_input(args.pcb, '.kicad_pcb')
        if note:
            print(f"Note: {note} → {os.path.basename(resolved)}",
                  file=sys.stderr)
        args.pcb = resolved
    except FileNotFoundError as e:
        parser.error(str(e))

    # Load project config (for project settings — suppressions applied to
    # EMC/thermal findings, not PCB warnings which lack rule_ids)
    try:
        from project_config import load_config_from_path, load_config
        if args.config:
            config = load_config_from_path(args.config)
        else:
            config = load_config(str(Path(args.pcb).parent))
    except ImportError:
        config = {"version": 1, "project": {}, "suppressions": []}

    # Build inputs provenance block (Track 1.3).
    # Resolve canonical analysis_dir ONCE (used for capability_mode_ref).
    # Includes --analysis-dir, fixing audit Highest-Risk #4 (split with output).
    if args.analysis_dir:
        _analysis_dir = Path(args.analysis_dir)
    elif args.output:
        _analysis_dir = Path(args.output).parent
    else:
        _analysis_dir = Path("analysis")

    # Resolve capability_mode_ref BEFORE build_inputs so inputs.run_id ==
    # capability_mode_ref.run_id (audit Highest-Risk #5).
    _capability_mode_ref = get_capability_mode_ref(_analysis_dir)

    _pcb_path = Path(args.pcb)
    if args.config:
        _cfg_path = Path(args.config) if Path(args.config).is_file() else None
    else:
        _default_cfg = _pcb_path.parent / ".kicad-happy.json"
        _cfg_path = _default_cfg if _default_cfg.is_file() else None
    inputs = build_inputs(
        source_files=[_pcb_path],
        config_path=_cfg_path,
        run_id=_capability_mode_ref["run_id"],
    )
    compat = build_compat()

    schematic_data = None
    if args.schematic:
        try:
            with open(args.schematic) as f:
                schematic_data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: cannot load schematic analysis: {e}", file=sys.stderr)
        if (schematic_data and 'signal_analysis' in schematic_data
                and 'findings' not in schematic_data):
            print(f'Warning: {args.schematic} uses the pre-v1.3 '
                  f'signal_analysis wrapper format — schematic cross-ref '
                  f'disabled. Re-run analyze_schematic.py for full '
                  f'analysis.', file=sys.stderr)
            schematic_data = None

    result = analyze_pcb(args.pcb, proximity=args.proximity,
                         include_trace_segments=args.full,
                         schematic_data=schematic_data,
                         return_path_radius_mm=args.return_path_radius_mm,
                         gp001_debug=args.gp001_debug)
    # Inject provenance and drop legacy 'file' key (already removed from
    # internal result assembly, but belt-and-suspenders).
    result["inputs"] = inputs
    result["compat"] = compat
    result.pop("file", None)

    # GP-001 debug: write per-sample diagnostics to disk and strip from output
    gp001_debug_data = result.pop("_gp001_debug_samples", None)
    if gp001_debug_data is not None:
        debug_dir = args.analysis_dir or str(Path(args.pcb).parent)
        debug_path = os.path.join(debug_dir, "gp001_debug.json")
        try:
            os.makedirs(debug_dir, exist_ok=True)
            with open(debug_path, "w") as f:
                json.dump({
                    "description": "GP-001 return-path per-sample diagnostics",
                    "radius_mm": args.return_path_radius_mm,
                    "total_samples": len(gp001_debug_data),
                    "hits": sum(1 for s in gp001_debug_data if s["hit"]),
                    "misses": sum(1 for s in gp001_debug_data if not s["hit"]),
                    "samples": gp001_debug_data,
                }, f, indent=2)
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
        from project_config import resolve_design_intent
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
    apply_output_filters(result, args.stage, args.audience)

    # Guarantee every finding carries a stable finding_id (Layer 2 merge keys
    # on it). Runs after all filtering; before any output branch.
    assign_finding_ids(result.get('findings', []), 'pcb')

    if args.text:
        from output_filters import format_text
        print(format_text(result.get('findings', []), args.audience or 'designer', args.stage))
        sys.exit(0)

    # Wire capability_mode_ref (Phase 4 spec §3.3).
    # capability_mode_ref already resolved early — reuse to keep run_id stable.
    result["capability_mode_ref"] = _capability_mode_ref

    indent = None if args.compact else 2
    output = json.dumps(result, indent=indent, default=str)

    if args.analysis_dir:
        import tempfile
        from analysis_cache import (ensure_analysis_dir, hash_source_file,
                                     should_create_new_run, create_run,
                                     overwrite_current, CANONICAL_OUTPUTS,
                                     resolve_analysis_dir)

        project_dir = str(Path(args.pcb).parent)
        analysis_dir = resolve_analysis_dir(args.analysis_dir)

        # Find .kicad_pro for manifest
        pro_file = ""
        try:
            for f in os.listdir(project_dir):
                if f.endswith(".kicad_pro"):
                    pro_file = f
                    break
        except OSError:
            pass

        # Ensure the target directory exists with manifest
        os.makedirs(analysis_dir, exist_ok=True)
        from analysis_cache import MANIFEST_FILENAME, save_manifest, _empty_manifest, GITIGNORE_CONTENT
        manifest_path = os.path.join(analysis_dir, MANIFEST_FILENAME)
        if not os.path.isfile(manifest_path):
            manifest = _empty_manifest()
            manifest['project'] = pro_file
            save_manifest(analysis_dir, manifest)
        gitignore_path = os.path.join(analysis_dir, '.gitignore')
        if not os.path.isfile(gitignore_path):
            with open(gitignore_path, 'w') as f:
                f.write(GITIGNORE_CONTENT)

        source_hashes = {os.path.basename(args.pcb): hash_source_file(args.pcb)}

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = os.path.join(tmp_dir, CANONICAL_OUTPUTS.get("pcb", "pcb.json"))
            Path(out_file).write_text(output)

            if should_create_new_run(analysis_dir, tmp_dir):
                run_id = create_run(
                    analysis_dir=analysis_dir,
                    outputs_dir=tmp_dir,
                    source_hashes=source_hashes,
                    scripts={"pcb": f"analyze_pcb.py {os.path.basename(args.pcb)}"},
                )
                print(f"Analysis cached: {os.path.join(analysis_dir, run_id, 'pcb.json')}", file=sys.stderr)
            else:
                overwrite_current(analysis_dir, tmp_dir, source_hashes=source_hashes)
                print(f"Analysis cache updated (current run)", file=sys.stderr)

    elif args.output:
        Path(args.output).write_text(output)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
