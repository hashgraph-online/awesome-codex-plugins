"""PCB geometry primitives: polygon area/containment, zone fills, copper presence,
pad outlines and sampling. Verbatim moves from analyze_pcb.py; no behaviour change.

ZoneFills / CopperPresence / copper_connected are the spatial index every copper-aware check
reads; the pad helpers are shared by copper presence, thermal-pad vias and via-in-pad.
"""
from __future__ import annotations

import math

from kicad_core.sexp import find_all


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

    `min_edge_distance` additionally maintains a lazily built per-fill
    segment grid (KH-420) so nearest-edge queries don't need to walk every
    vertex of every fill.
    """

    def __init__(self) -> None:
        self._fills: list[
            tuple[int, int, str, list[tuple[float, float]],
                  tuple[float, float, float, float]]
        ] = []
        self._next_fill_id = 0
        self._grids: dict[int, tuple] = {}

    def add(self, zone_idx: int, layer: str,
            coords: list[tuple[float, float]]) -> None:
        """Register a filled polygon region for spatial queries."""
        bbox = _polygon_bbox(coords)
        fill_id = self._next_fill_id
        self._next_fill_id += 1
        self._fills.append((fill_id, zone_idx, layer, coords, bbox))

    def _segment_grid(self, fill_id: int):
        """Lazily built uniform grid: cell -> indices of polygon segments whose
        bbox overlaps that cell. (cell_size, ncx, ncy, cells). KH-420."""
        g = self._grids.get(fill_id)
        if g is not None:
            return g
        _fid, _zidx, _layer, coords, bbox = self._fills[fill_id]
        assert _fid == fill_id
        w = max(bbox[2] - bbox[0], 0.0)
        h = max(bbox[3] - bbox[1], 0.0)
        cell = max(0.5, max(w, h) / 64.0)
        ncx = int(w // cell) + 1
        ncy = int(h // cell) + 1
        cells: dict = {}
        n = len(coords)
        for i in range(n):
            x1, y1 = coords[i]
            x2, y2 = coords[(i + 1) % n]
            cx0 = int((min(x1, x2) - bbox[0]) // cell)
            cx1 = int((max(x1, x2) - bbox[0]) // cell)
            cy0 = int((min(y1, y2) - bbox[1]) // cell)
            cy1 = int((max(y1, y2) - bbox[1]) // cell)
            for cx in range(cx0, cx1 + 1):
                for cy in range(cy0, cy1 + 1):
                    cells.setdefault((cx, cy), []).append(i)
        g = (cell, ncx, ncy, cells)
        self._grids[fill_id] = g
        return g

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

    def min_edge_distance(self, x: float, y: float, layer: str,
                          zone_idxs: set | None = None) -> float:
        """Distance from (x, y) to the nearest edge of any filled polygon on
        `layer` (optionally only zones in zone_idxs). inf when none.

        Uses a lazily built per-fill segment grid (KH-420); results are
        identical to the full walk. The ring search is centered on the
        query point's projection onto the fill's bbox (not the point
        itself) so a point far outside a small/distant fill's bbox still
        bounds the search to the fill's own grid extent; the cutoff folds
        in that projection offset via math.hypot so it stays exact.
        Cutoff is exact: for C = clamp(Q, bbox) and any S inside the
        bbox, |Q-S| >= hypot(|Q-C|, |C-S|) (projection onto a convex
        set), and every unvisited segment has |C-S| >= (r-1)*cell.
        Fills are visited nearest-bbox-first so `best` tightens early and
        farther fills short-circuit before any grid is even built.
        """
        best = float("inf")
        candidates = []
        for fid, zidx, fl, coords, bbox in self._fills:
            if fl != layer or (zone_idxs is not None and zidx not in zone_idxs):
                continue
            dx = max(bbox[0] - x, 0.0, x - bbox[2])
            dy = max(bbox[1] - y, 0.0, y - bbox[3])
            candidates.append((math.hypot(dx, dy), fid, coords, bbox))
        candidates.sort(key=lambda c: c[0])
        for offset, fid, coords, bbox in candidates:
            if offset >= best:
                break  # sorted ascending: every remaining candidate is >= offset >= best
            cell, ncx, ncy, cells = self._segment_grid(fid)
            # Project (x, y) onto the bbox; this point's cell is always
            # inside [0, ncx-1] x [0, ncy-1], so max_ring below is bounded
            # by the fill's own grid size regardless of how far outside
            # the bbox (x, y) actually is.
            cx = min(max(x, bbox[0]), bbox[2])
            cy = min(max(y, bbox[1]), bbox[3])
            px = min(max(int((cx - bbox[0]) // cell), 0), ncx - 1)
            py = min(max(int((cy - bbox[1]) // cell), 0), ncy - 1)
            # Farthest ring that can still hold a grid cell from this point.
            max_ring = max(px, (ncx - 1) - px, py, (ncy - 1) - py)
            seen: set = set()
            n = len(coords)
            r = 0
            while r <= max_ring:
                if r > 0 and math.hypot(offset, (r - 1) * cell) >= best:
                    break  # exact: every unvisited segment is >= hypot(offset, (r-1)*cell) away
                # Walk only the O(r) boundary cells of this ring (not the
                # full (2r+1)^2 square): ring 0 is just the own cell; ring
                # r>0 is the top/bottom rows and left/right columns of the
                # (2r+1)x(2r+1) square centered on (px, py).
                if r == 0:
                    ring_cells = ((px, py),)
                else:
                    ring_cells = [(px + ddx, py - r) for ddx in range(-r, r + 1)]
                    ring_cells += [(px + ddx, py + r) for ddx in range(-r, r + 1)]
                    ring_cells += [(px - r, py + ddy) for ddy in range(-r + 1, r)]
                    ring_cells += [(px + r, py + ddy) for ddy in range(-r + 1, r)]
                for cell_key in ring_cells:
                    segs = cells.get(cell_key)
                    if not segs:
                        continue
                    for i in segs:
                        if i in seen:
                            continue
                        seen.add(i)
                        x1, y1 = coords[i]
                        x2, y2 = coords[(i + 1) % n]
                        d = _dist_point_to_segment(x, y, x1, y1, x2, y2)
                        if d < best:
                            best = d
                r += 1
        return best


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


def _pad_on_layer(pad: dict, layer: str, default_layer: str) -> bool:
    """True when `pad` has copper on `layer`.

    Pad `layers` may name layers explicitly ("F.Cu" "B.Cu"), use KiCad's
    wildcards ("*.Cu" = every copper layer; "F&B.Cu" = outer copper), or be
    absent (legacy/minimal footprints -> assume the footprint's own layer).
    Through-hole pads always carry "*.Cu", which is why they were skipped by
    a literal membership test (KH-413).
    """
    layers = pad.get("layers")
    if not layers:
        return layer == default_layer
    if layer in layers:
        return True
    if not layer.endswith(".Cu"):
        return False
    if "*.Cu" in layers:
        return True
    if "F&B.Cu" in layers and layer in ("F.Cu", "B.Cu"):
        return True
    return False


def _pad_outline_points(shape: str, hw: float, hh: float) -> list[tuple[float, float]]:
    """8 points on a pad's outline in the pad's local frame (unrotated).

    circle: on the circumference at 45° steps (r = max(hw, hh)).
    oval:   on the stadium boundary at 45° steps — a stadium is the Minkowski
            sum of a segment and a circle of radius r = min(hw, hh), so the
            boundary point in direction θ is the segment end on that side
            plus r·(cos θ, sin θ).
    other:  the box corners + edge midpoints (unchanged behaviour).
    KH-419 (SacMap TP1: bbox corners of a Ø15 mm pad sat 3.1 mm outside the
    copper and read an unrelated fill cutout as the clearance).
    """
    if shape == "circle":
        r = max(hw, hh)
        return [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in range(0, 360, 45)]
    if shape == "oval":
        r = min(hw, hh)
        pts = []
        for a in range(0, 360, 45):
            c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
            if hw >= hh:
                pts.append((math.copysign(hw - r, c) * (1 if abs(c) > 1e-12 else 0) + r * c, r * s))
            else:
                pts.append((r * c, math.copysign(hh - r, s) * (1 if abs(s) > 1e-12 else 0) + r * s))
        return pts
    return [(-hw, -hh), (0, -hh), (hw, -hh), (hw, 0), (hw, hh), (0, hh), (-hw, hh), (-hw, 0)]


def _pad_sample_points(fp: dict, fp_layer: str) -> list[tuple[float, float]]:
    """Points on the outline of every pad of `fp` on `fp_layer` (8 per pad,
    rotated by the pad angle; THT pads via their "*.Cu" wildcard, KH-413;
    circle/oval pads sampled on their true outline, KH-419);
    footprint origin when no pad has geometry."""
    pts: list[tuple[float, float]] = []
    for pad in fp.get("pads", []):
        if not _pad_on_layer(pad, fp_layer, fp_layer) or "abs_x" not in pad:
            continue
        cx, cy = pad["abs_x"], pad["abs_y"]
        hw, hh = pad.get("width", 0) / 2.0, pad.get("height", 0) / 2.0
        # KiCad writes a pad's (at x y angle) orientation as the ABSOLUTE
        # board orientation -- it already includes the footprint's own
        # rotation, so it must not be added again here.
        pad_abs_angle = pad.get("angle") or 0
        ang = math.radians(-pad_abs_angle)
        for ox, oy in _pad_outline_points(pad.get("shape", ""), hw, hh):
            pts.append((cx + ox * math.cos(ang) - oy * math.sin(ang),
                        cy + ox * math.sin(ang) + oy * math.cos(ang)))
    return pts or [(fp.get("x", 0), fp.get("y", 0))]


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
