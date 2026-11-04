"""PCB reader: .kicad_pcb extraction — layers, setup, nets, footprints, tracks,
vias, zones, outline, silkscreen, metadata, dimensions, groups, net classes.

Verbatim moves from analyze_pcb.py; no behaviour change. Reads only: the KiCad-10 synthetic
net map is built here (_build_net_mapping → PcbReaderState) and applied by pcb.pipeline.read_board.
"""
from __future__ import annotations

import math
import re

from kicad_core.sexp import find_all, find_first, get_at, get_property, get_value
from kicad_core.fields import get_mpn_property
from kicad_core.model import PcbReaderState
from pcb.geometry import (
    ZoneFills, _chain_segments, _extract_polygon_coords, _polygon_bbox, _shoelace_area,
    _shoelace_area_from_coords,
)


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
def _net_id(val: str | None) -> int:
    """Convert a net value to an integer ID during extraction.

    KiCad ≤9: val is a numeric string like "3" → returns 3.
    KiCad 10: val is a net name like "+3.3V" → 0 here; the synthetic ID is assigned by
    _build_net_mapping() and applied by the backfill through PcbReaderState.net_id().
    """
    if not val:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def _build_net_mapping(footprints: list[dict], tracks: dict, vias: dict,
                       zones: list[dict], state: PcbReaderState) -> dict[int, str]:
    """Build synthetic net ID mapping for KiCad 10 (no net declarations).

    Scans all pads, tracks, vias, and zones for unique net names and assigns
    sequential integer IDs. Returns the same dict[int, str] format as
    extract_nets() for backward compatibility.
    """
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
    state.net_name_to_id = {"": 0}
    for i, name in enumerate(sorted(names), start=1):
        net_names[i] = name
        state.net_name_to_id[name] = i
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

        # KH-414: any known MPN alias, case/whitespace-insensitive (was an
        # exact-case lookup of "MPN" / "Mfg Part" only).
        mpn = get_mpn_property(fp) or ""

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
