"""PCB routing analyses: connectivity, power-net routing, routed distances, return
path, net lengths/impedance, ground domains, trace proximity, current capacity, layer transitions."""

import heapq
import math

from kicad_core.netnames import is_ground_name, is_pin_guarded_signal, is_power_net_name, net_leaf
from pcb.geometry import CopperPresence, _arc_length_3pt


def board_pin_signals(footprints: list[dict], power_rails: set[str] | None = None) -> frozenset[str]:
    """Board nets named VPP/VM whose pads say signal (is_pin_guarded_signal), unless the
    rail set names them. A board without pad pin types (before KiCad 7) keeps the name rule."""
    pin_types: dict[str, list[str]] = {}
    for fp in footprints:
        for pad in fp.get("pads", []):
            if pad.get("net_name"):
                pin_types.setdefault(pad["net_name"], []).append(pad.get("pintype", ""))
    return frozenset(
        n for n, types in pin_types.items()
        if n not in (power_rails or ()) and is_pin_guarded_signal(n, [(t, None) for t in types]))


def analyze_connectivity(footprints: list[dict], tracks: dict, vias: dict,
                         net_names: dict[int, str],
                         zones: list[dict] | None = None,
                         graphics: list[dict] | None = None) -> dict:
    """Analyze routing completeness — find unrouted nets.

    A net is considered routed if it has tracks, vias, a copper zone or a copper
    graphic (KiCad 8+ shapes with a net) covering it. Nets with only a single pad
    are skipped.
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
    for g in graphics or []:
        if g.get("net", 0) > 0:
            routed_nets.add(g["net"])
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


def analyze_power_nets(footprints: list[dict], tracks: dict,
                       net_names: dict[int, str],
                       power_rails: set[str] | None = None,
                       pin_signals: frozenset = frozenset()) -> list[dict]:
    """Analyze routing of power/ground nets — track widths, via counts."""
    # EQ-052: d = √(Δx²+Δy²) (Euclidean distance)
    # Identify power/ground nets
    power_nets = {}
    for net_num, name in net_names.items():
        if (name not in pin_signals and is_power_net_name(name, power_rails)) or is_ground_name(name):
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

    for arc in tracks.get("arcs", []):
        net = arc["net"]
        if net in power_nets:
            s, e, m = arc["start"], arc["end"], arc.get("mid")
            if m:
                length = _arc_length_3pt(s[0], s[1], m[0], m[1], e[0], e[1])
            else:
                length = math.hypot(e[0] - s[0], e[1] - s[1])
            power_nets[net]["widths"].add(arc["width"])
            power_nets[net]["track_count"] += 1
            power_nets[net]["total_length_mm"] += length

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
                                    debug_samples=None, vias=None,
                                    power_rails=None, copper_order=None, pin_signals=frozenset(),
                                    stackup=None, reference_changes=None):
    """Check ground/power plane continuity under signal traces.

    For each signal net's trace segments, samples points along the trace
    and checks if the reference layer has a ground or power zone fill.
    Flags gaps in the reference plane that could cause return path
    discontinuities and EMI issues.

    Only ground or power-rail zone fills count as the reference: the return
    current of a microstrip flows in the nearest plane, and a power plane
    serves when it is decoupled to ground (Ott, EMC Engineering ch. 16).
    Other nets' fills, tracks and pads are not a reference plane. A fill
    within radius_mm of the sample counts, so KiCad's clearance channels
    ("swiss cheese" fill polygons) are not gaps.

    Args:
        tracks: Track data dict with segments
        net_names: Net number → name mapping
        zones: Zone list (for zone metadata)
        zone_fills: ZoneFills spatial index
        signal_nets: Optional set of net names to check (default: all non-power)
        ref_layer_map: Layer → opposite reference layer mapping (used when
            no stackup is given)
        footprints: Accepted for callers; pads are not a reference plane.
        radius_mm: Radius (mm) for copper-presence search (default 0.5)
        debug_samples: If a list is passed, per-sample dicts are appended
            with keys {net, x, y, layer, hit} for GP-001 diagnostics.
        vias: Optional via dict from extract_vias(). When given, a sample
            that misses copper on the opposite layer is still credited as
            a hit if it falls inside a via's own antipad — that void is
            expected (KiCad clears copper around a via for isolation), not
            a reference-plane gap. The credit only applies when
            the via's physical layer span actually reaches the probed
            layer — a blind/buried via doesn't get credit for an antipad
            on a layer it never touches.
        power_rails: Optional set of net names to treat as power/ground
            regardless of naming heuristics.
        copper_order: Ordered list of copper layer names (from
            `_copper_order_from_stackup`) used to test via layer span.
            Missing data falls back to the through-via assumption (never reduces credit).
        stackup: Board stackup (the file's or the inferred one). When given,
            each layer's reference is the nearest layer carrying ground or
            power zone copper (`_build_reference_layer_map`).
        reference_changes: If a list is passed, one dict is appended per place
            where a signal trace's reference plane changes from one plane net
            to another (`_plane_net_changes`).

    Returns:
        List of gap findings: [{net, layer, gap_start_mm, gap_length_mm, ...}]
    """
    # EQ-053: d = √(Δx²+Δy²) (trace-to-plane gap detection)
    if not zone_fills.has_data:
        return []

    from kicad_core.netnames import is_power_net_name, is_ground_name

    cp = CopperPresence(zone_fills, None, None)
    ref_idxs = {i for i, z in enumerate(zones)
                if (name := z.get("net_name") or "")
                and (is_ground_name(name)
                     or (name not in pin_signals and is_power_net_name(name, power_rails)))}
    if stackup is not None:
        ref_layer_map = _build_reference_layer_map(stackup, zone_fills.fill_layers(ref_idxs))

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
        if (net_name not in pin_signals and is_power_net_name(net_name, power_rails)) or is_ground_name(net_name):
            continue
        if signal_nets and net_name not in signal_nets:
            continue
        net_segments.setdefault(net, []).append(seg)

    SAMPLE_INTERVAL = 2.0  # mm between sample points

    # Pre-index vias into a coarse grid, once, before the net loop: a via's
    # own antipad on the opposite copper layer is an expected void, not a
    # reference-plane gap. Grid pattern mirrors the proximity grid
    # in analyze_trace_proximity() to keep the per-sample check O(1) instead
    # of O(via_count).
    ANTIPAD_CLEARANCE = 0.2  # mm — conservative upper bound for default zone clearance
    ANTIPAD_GRID = 2.0  # mm
    zone_clearances = [z.get("clearance") for z in zones if z.get("clearance")]
    antipad_clearance = max([ANTIPAD_CLEARANCE] + zone_clearances)
    via_grid: dict[tuple[int, int], list[tuple[float, float, float, list]]] = {}
    for v in (vias or {}).get("vias", []):
        vr = v.get("size", 0) / 2.0
        if vr <= 0:
            continue
        gx, gy = int(v["x"] / ANTIPAD_GRID), int(v["y"] / ANTIPAD_GRID)
        via_grid.setdefault((gx, gy), []).append((v["x"], v["y"], vr, v.get("layers") or []))

    def _in_via_antipad(px: float, py: float, layer: str) -> bool:
        gx, gy = int(px / ANTIPAD_GRID), int(py / ANTIPAD_GRID)
        for dgx in (-1, 0, 1):
            for dgy in (-1, 0, 1):
                for vx, vy, vr, vlayers in via_grid.get((gx + dgx, gy + dgy), ()):
                    if (px - vx) ** 2 + (py - vy) ** 2 <= (vr + antipad_clearance) ** 2 \
                            and _via_spans_layer(vlayers, layer, copper_order):
                        return True
        return False

    def _ref_net_at(px: float, py: float, layer: str):
        nets = {zones[zi].get("net_name") for _fid, zi in
                zone_fills.fill_regions_at_point(px, py, layer, zones) if zi in ref_idxs}
        return next(iter(nets)) if len(nets) == 1 else None

    track_refs = reference_changes is not None
    for net_id, segs in net_segments.items():
        net_name = net_names.get(net_id, f"net_{net_id}")
        total_samples = 0
        gap_samples = 0
        seg_samples = []

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
            seg_refs = []
            for k in range(n_samples):
                t = k / max(n_samples - 1, 1)
                px = x1 + t * dx
                py = y1 + t * dy
                total_samples += 1

                hit = cp.has_coverage_near(px, py, opp_layer, radius_mm=radius_mm,
                                           zone_idxs=ref_idxs, fills_only=True)
                antipad_credit = False
                if not hit and _in_via_antipad(px, py, opp_layer):
                    hit = True  # expected void — via's own antipad
                    antipad_credit = True
                if not hit:
                    gap_samples += 1
                if track_refs:
                    ref_net = _ref_net_at(px, py, opp_layer) if hit and not antipad_credit else None
                    seg_refs.append((ref_net, px, py, t * length))
                if debug_samples is not None:
                    sample = {
                        'net': net_name, 'x': round(px, 2),
                        'y': round(py, 2), 'layer': opp_layer,
                        'hit': hit,
                    }
                    if antipad_credit:
                        sample['antipad_credit'] = True
                    debug_samples.append(sample)
            if track_refs:
                seg_samples.append((layer, opp_layer, (layer, round(x1, 3), round(y1, 3)),
                                    (layer, round(x2, 3), round(y2, 3)), seg_refs))

        if track_refs:
            for lyr, rl, sa, sb, cx, cy in _plane_net_changes(seg_samples, SAMPLE_INTERVAL):
                if sa[0] > sb[0]:
                    sa, sb = sb, sa
                reference_changes.append({
                    "net": net_name, "layer": lyr, "reference_layer": rl,
                    "net_a": sa[0], "net_b": sb[0], "x": round(cx, 2), "y": round(cy, 2),
                    "sample_points": [[round(sa[1], 2), round(sa[2], 2)],
                                      [round(sb[1], 2), round(sb[2], 2)]]})

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


def _plane_net_changes(segs, min_run_mm):
    """Where the plane net under one signal net's trace changes.

    segs: one (layer, reference_layer, start_key, end_key, samples) per segment, the keys
    naming the segment ends (segments of the net meet where keys are equal) and samples
    [(plane net or None, x, y, mm along the segment)] in order. A plane net counts only
    where it holds over at least min_run_mm of trace, counted across segment ends that
    meet, so a pad-sized island is not a change. Returns (layer, reference_layer,
    sample_a, sample_b, x, y): consecutive counted samples of different nets on a
    segment (the change at their midpoint), or the nearest counted samples of two nets
    on segments that meet (the change at the junction).
    """
    runs = []  # (segment index, first sample, last sample, net)
    parent: list[int] = []
    at_end: dict = {}  # (segment end, net) -> runs touching it

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for si, (_l, _r, k_start, k_end, smp) in enumerate(segs):
        k = 0
        while k < len(smp):
            j = k
            while j + 1 < len(smp) and smp[j + 1][0] == smp[k][0]:
                j += 1
            if smp[k][0] is not None:
                parent.append(len(runs))
                if k == 0:
                    at_end.setdefault((k_start, smp[k][0]), []).append(len(runs))
                if j == len(smp) - 1:
                    at_end.setdefault((k_end, smp[k][0]), []).append(len(runs))
                runs.append((si, k, j, smp[k][0]))
            k = j + 1
    for members in at_end.values():
        for ri in members[1:]:
            parent[find(ri)] = find(members[0])
    held: dict = {}
    for ri, (si, k0, k1, _net) in enumerate(runs):
        smp = segs[si][4]
        held[find(ri)] = held.get(find(ri), 0.0) + smp[k1][3] - smp[k0][3]
    known: dict = {}
    for ri, (si, k0, k1, _net) in enumerate(runs):
        if held[find(ri)] >= min_run_mm - 1e-6:
            known.setdefault(si, []).extend(segs[si][4][k0:k1 + 1])

    changes = []
    ends: dict = {}
    for si, ks in known.items():
        layer, ref_layer, k_start, k_end, _smp = segs[si]
        for a, b in zip(ks, ks[1:]):
            if a[0] != b[0]:
                changes.append((layer, ref_layer, a, b, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2))
        ends.setdefault(k_start, []).append((layer, ref_layer, ks[0]))
        ends.setdefault(k_end, []).append((layer, ref_layer, ks[-1]))
    for key, items in ends.items():
        by_net: dict = {}
        for layer, ref_layer, smp in items:
            by_net.setdefault(smp[0], (layer, ref_layer, smp))
        if len(by_net) > 1:
            a, b = sorted(by_net)[:2]
            layer, ref_layer, sa = by_net[a]
            changes.append((layer, ref_layer, sa, by_net[b][2], key[1], key[2]))
    return changes


def _safe_num(val, default=0):
    """Safely convert a value to float (handles None, str, etc.)."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _build_reference_layer_map(stackup: list[dict],
                               ref_layers: set[str] | None = None) -> dict[str, str]:
    """Map each copper layer to its adjacent reference plane copper layer.

    Walks the stackup in order and for each copper layer, finds the nearest
    other copper layer (above or below, preferring the one separated by
    thinner dielectric). Returns a mapping like {"F.Cu": "In1.Cu", "In1.Cu": "F.Cu", ...}.

    With ref_layers (the layers carrying ground or power zone copper), the
    reference is the nearest other layer in that set, at any distance; a
    layer with none of it is never a reference plane. A layer with no such
    layer elsewhere keeps its adjacent layer.

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

    def dielectric_between(a: int, b: int) -> float:
        thickness = 0.0
        for k in range(min(a, b) + 1, max(a, b)):
            if stackup[k].get("type") in ("core", "prepreg"):
                t = stackup[k].get("thickness")
                if t is not None:
                    try:
                        thickness += float(t)
                    except (ValueError, TypeError):
                        thickness += 0.2
        return thickness

    ref_map: dict[str, str] = {}
    for ci, (idx, name) in enumerate(copper_layers):
        adjacent = [n for n in (ci - 1, ci + 1) if 0 <= n < len(copper_layers)]
        candidates = adjacent
        if ref_layers is not None:
            candidates = [n for n in range(len(copper_layers))
                          if copper_layers[n][1] != name and copper_layers[n][1] in ref_layers] \
                or adjacent
        # Thinnest dielectric, then fewest layers away, then the layer above.
        best = min(candidates, key=lambda n: (dielectric_between(idx, copper_layers[n][0]),
                                              abs(n - ci), n > ci))
        if copper_layers[best][1]:
            ref_map[name] = copper_layers[best][1]

    return ref_map


def _copper_order_from_stackup(stackup: list[dict]) -> list[str]:
    """Ordered copper layer names from the stackup.

    Falls back to simple F.Cu/B.Cu when no usable stackup is available.
    """
    names = [l.get("name", "") for l in (stackup or []) if l.get("type") == "copper" and l.get("name")]
    return names if len(names) >= 2 else ["F.Cu", "B.Cu"]


def _via_spans_layer(via_layers: list[str], layer: str, copper_order: list[str]) -> bool:
    """True when `layer` is within the via's physical span. Missing
    data -> True (through-via assumption)."""
    if not via_layers or len(via_layers) < 2 or not copper_order:
        return True
    try:
        a, b, l = (copper_order.index(via_layers[0]), copper_order.index(via_layers[1]),
                   copper_order.index(layer))
    except ValueError:
        return True
    return min(a, b) <= l <= max(a, b)


def _microstrip_impedance(width_mm, height_mm, thickness_mm, epsilon_r, outer=True):
    """Calculate single-ended microstrip characteristic impedance.

    Hammerstad's closed form with effective width correction for finite copper
    thickness. On an outer layer the field is partly in air, so Z0 uses the
    effective permittivity; an inner layer (outer=False) keeps the bulk
    epsilon_r, a rough estimate since a buried trace is stripline.

    Args:
        width_mm: Trace width in mm
        height_mm: Dielectric height to reference plane in mm
        thickness_mm: Copper thickness in mm
        epsilon_r: Relative permittivity of dielectric
        outer: True for a top or bottom copper layer

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
    # Source: E. Hammerstad, "Equations for Microstrip Circuit Design", Proc. 5th European
    # Microwave Conf., 1975; Pozar, Microwave Engineering, 4th ed., §3.8 (eqs. 3.195-3.196)
    u = w_eff / h
    e_eff = er
    if outer:
        # EQ-109: εeff = (εr+1)/2 + (εr−1)/2·[(1+12h/w)^−½ + 0.04(1−w/h)² for w/h<1] (Hammerstad)
        e_eff = (er + 1) / 2 + (er - 1) / 2 * (1 + 12 / u) ** -0.5
        if u < 1:
            e_eff += (er - 1) / 2 * 0.04 * (1 - u) ** 2
    if w_eff / h < 1:
        # EQ-023: Z₀ = (60/√εeff)ln(8h/w+w/4h) (Hammerstad narrow microstrip)
        z0 = (60 / math.sqrt(e_eff)) * math.log(8 * h / w_eff + w_eff / (4 * h))
    else:
        # EQ-024: Z₀ = 120π/(√εeff(w/h+1.393+0.667ln(w/h+1.444))) (Hammerstad wide)
        z0 = (120 * math.pi) / (math.sqrt(e_eff) * (w_eff / h + 1.393 + 0.667 * math.log(w_eff / h + 1.444)))
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
    impedance estimate (microstrip formula; see _microstrip_impedance).
    """
    # EQ-050: L = √(Δx²+Δy²) (track segment length)
    # Pre-compute layer-to-dielectric-height mapping for impedance calculation
    layer_heights = _build_layer_heights(stackup) if stackup else {}
    copper = [l.get("name") for l in (stackup or []) if l.get("type") == "copper"]
    outer_layers = {copper[0], copper[-1]} if copper else set()

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
                z0 = _microstrip_impedance(seg.get("width", 0), h, cu_t, er,
                                            outer=layer in outer_layers)
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
                z0 = _microstrip_impedance(arc.get("width", 0), h, cu_t, er,
                                            outer=layer in outer_layers)
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
                           zones: list[dict], power_rails: set[str] | None = None) -> dict:
    """Identify ground domain splits and component membership.

    Detects separate ground nets (GND, AGND, DGND, PGND, etc.) and reports
    which components connect to each. Components on multiple ground domains
    are flagged — these may be intentional (star ground) or errors.
    """
    # COM also names an analog-switch or motor common: a ground domain only when the rail
    # set names it. AGND_CODEC, PGND2 or ESP_GND2 are grounds too, but a net KiCad names
    # after a pin (Net-(U1-GND), unconnected-(U1-GND-Pad3), a panel's Board_0-Net-(U1-GND))
    # is not.
    def _is_ground(name: str) -> bool:
        leaf = net_leaf(name).upper()
        if leaf == "COM":
            return name in (power_rails or ())
        return is_ground_name(name, power_rails) or (
            any(g in leaf for g in ("GND", "VSS", "GROUND"))
            and "NET-(" not in leaf and "UNCONNECTED-(" not in leaf)

    ground_nets: dict[int, str] = {
        net_num: name for net_num, name in net_names.items() if _is_ground(name)}

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
                            grid_size: float = 0.5,
                            power_rails: set[str] | None = None,
                            pin_signals: frozenset = frozenset()) -> dict:
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
                        if not ((net_names.get(n, "") not in pin_signals and is_power_net_name(net_names.get(n, ""), power_rails))
                                or is_ground_name(net_names.get(n, ""))))
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
                             setup: dict,
                             power_rails: set[str] | None = None,
                             pin_signals: frozenset = frozenset()) -> dict:
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
        is_power = (name not in pin_signals and is_power_net_name(name, power_rails)) or is_ground_name(name)

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


def analyze_layer_transitions(tracks: dict, vias: dict,
                               net_names: dict[int, str],
                               power_rails: set[str] | None = None,
                               pin_signals: frozenset = frozenset()) -> list[dict]:
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
        if (name not in pin_signals and is_power_net_name(name, power_rails)) or is_ground_name(name):
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
