"""PCB geometry primitives: polygon area/containment, zone fills, copper presence,
pad outlines and sampling.

ZoneFills / CopperPresence / copper_connected are the spatial index every copper-aware check
reads; the pad helpers are shared by copper presence, thermal-pad vias and via-in-pad.
"""
from __future__ import annotations

import math

from kicad_core.sexp import find_all


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def arc_points(start, mid, end, tol: float = 0.002,
               max_chords: int = 64) -> list[tuple[float, float]]:
    """Points along a start/mid/end arc, chords within `tol` of the curve."""
    (sx, sy), (ex, ey) = start, end
    if not mid:
        return [(sx, sy), (ex, ey)]
    mx, my = mid
    d = 2.0 * (sx * (my - ey) + mx * (ey - sy) + ex * (sy - my))
    if abs(d) < 1e-12:
        return [(sx, sy), (mx, my), (ex, ey)]
    ss, ms, es = sx * sx + sy * sy, mx * mx + my * my, ex * ex + ey * ey
    cx = (ss * (my - ey) + ms * (ey - sy) + es * (sy - my)) / d
    cy = (ss * (ex - mx) + ms * (sx - ex) + es * (mx - sx)) / d
    r = math.hypot(sx - cx, sy - cy)
    tau = 2.0 * math.pi
    a_s = math.atan2(sy - cy, sx - cx)
    nm = (math.atan2(my - cy, mx - cx) - a_s) % tau
    ne = (math.atan2(ey - cy, ex - cx) - a_s) % tau
    if (sx, sy) == (ex, ey):
        ne = tau
    sweep = ne if nm <= ne else ne - tau
    max_step = 2.0 * math.acos(max(-1.0, 1.0 - tol / r)) if r > tol else math.pi
    n = min(max_chords, max(2, math.ceil(abs(sweep) / max_step)))
    pts = [(sx, sy)]
    for k in range(1, n):
        a = a_s + sweep * k / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pts.append((ex, ey))
    return pts


def pts_coords(pts_node: list) -> list[tuple[float, float]]:
    """Ordered (x, y) points of a (pts (xy x y) (arc (start) (mid) (end)) ...) node.

    KiCad's outline parser appends each arc to the chain; arcs are expanded to chords
    and a joint shared by two entries is kept once."""
    out: list[tuple[float, float]] = []

    def add(p):
        if not out or abs(out[-1][0] - p[0]) > 1e-9 or abs(out[-1][1] - p[1]) > 1e-9:
            out.append(p)

    for it in pts_node[1:]:
        if not isinstance(it, list) or not it:
            continue
        if it[0] == "xy" and len(it) >= 3:
            add((float(it[1]), float(it[2])))
        elif it[0] == "arc":
            ends = {}
            for sub in it[1:]:
                if isinstance(sub, list) and len(sub) >= 3 and sub[0] in ("start", "mid", "end"):
                    ends[sub[0]] = (float(sub[1]), float(sub[2]))
            if "start" in ends and "end" in ends:
                for p in arc_points(ends["start"], ends.get("mid"), ends["end"]):
                    add(p)
    return out


def _extract_polygon_coords(pts_node: list) -> list[tuple[float, float]]:
    """Extract (x, y) coordinate tuples from a (pts (xy x y) (arc ...) ...) node."""
    return pts_coords(pts_node)


def _point_segment_distance(px: float, py: float, x1: float, y1: float,
                            x2: float, y2: float) -> float:
    dx, dy = x2 - x1, y2 - y1
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / length_sq))
    return math.hypot(px - x1 - t * dx, py - y1 - t * dy)


def _polyline_distance(px: float, py: float, pts: list, closed: bool) -> float | None:
    pts = [(float(p[0]), float(p[1])) for p in pts]
    if not pts:
        return None
    if len(pts) == 1:
        return math.hypot(px - pts[0][0], py - pts[0][1])
    n = len(pts)
    pairs = range(n) if closed else range(n - 1)
    return min(_point_segment_distance(px, py, *pts[i], *pts[(i + 1) % n]) for i in pairs)


def _arc_distance(px: float, py: float, start, mid, end) -> float:
    sx, sy = start
    mx, my = mid
    ex, ey = end
    if (sx, sy) == (ex, ey):
        # Full circle: start and mid are opposite ends of a diameter.
        cx, cy = (sx + mx) / 2.0, (sy + my) / 2.0
        return abs(math.hypot(px - cx, py - cy) - math.hypot(sx - cx, sy - cy))
    d = 2.0 * (sx * (my - ey) + mx * (ey - sy) + ex * (sy - my))
    if abs(d) < 1e-12:
        return min(_point_segment_distance(px, py, sx, sy, mx, my),
                   _point_segment_distance(px, py, mx, my, ex, ey))
    ss, ms, es = sx * sx + sy * sy, mx * mx + my * my, ex * ex + ey * ey
    cx = (ss * (my - ey) + ms * (ey - sy) + es * (sy - my)) / d
    cy = (ss * (ex - mx) + ms * (sx - ex) + es * (mx - sx)) / d
    r = math.hypot(sx - cx, sy - cy)
    tau = 2.0 * math.pi
    a_s = math.atan2(sy - cy, sx - cx)
    nm = (math.atan2(my - cy, mx - cx) - a_s) % tau
    ne = (math.atan2(ey - cy, ex - cx) - a_s) % tau
    # The mid point is on the sweep: counter-clockwise when it comes before the end.
    ccw = nm <= ne
    off = (math.atan2(py - cy, px - cx) - a_s) % tau
    inside = off <= ne if ccw else (tau - off) % tau <= tau - ne
    if inside:
        return abs(math.hypot(px - cx, py - cy) - r)
    return min(math.hypot(px - sx, py - sy), math.hypot(px - ex, py - ey))


def _bezier_points(ctrl: list, steps: int = 32) -> list:
    if len(ctrl) != 4:
        return ctrl
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = ctrl
    out = []
    for i in range(steps + 1):
        t = i / steps
        u = 1.0 - t
        a, b, c, e = u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t
        out.append((a * x0 + b * x1 + c * x2 + e * x3, a * y0 + b * y1 + c * y2 + e * y3))
    return out


def outline_edge_distance(px: float, py: float, edges: list[dict]) -> float | None:
    """Shortest distance from (px, py) to a board outline made of ``board_outline.edges``
    entries; None when no edge is usable."""
    best: float | None = None
    for e in edges:
        t = e.get("type")
        d = None
        if t == "line" and e.get("start") and e.get("end"):
            d = _point_segment_distance(px, py, *e["start"], *e["end"])
        elif t == "rect" and e.get("start") and e.get("end"):
            (x1, y1), (x2, y2) = e["start"], e["end"]
            d = _polyline_distance(px, py, [(x1, y1), (x2, y1), (x2, y2), (x1, y2)], True)
        elif t == "circle" and e.get("center") and e.get("end"):
            cx, cy = e["center"]
            d = abs(math.hypot(px - cx, py - cy) - math.hypot(e["end"][0] - cx, e["end"][1] - cy))
        elif t == "arc" and e.get("start") and e.get("end") and e.get("mid"):
            d = _arc_distance(px, py, e["start"], e["mid"], e["end"])
        elif t == "polygon" and e.get("points"):
            d = _polyline_distance(px, py, e["points"], True)
        elif t == "curve" and e.get("points"):
            d = _polyline_distance(px, py, _bezier_points(e["points"]), False)
        if d is not None and (best is None or d < best):
            best = d
    return best


# KiCad board.h DEFAULT_CHAINING_EPSILON_MM: Edge.Cuts ends this close (Euclidean) are joined
OUTLINE_CHAINING_EPSILON_MM = 0.01
_OUTLINE_MAX_CHORDS = 512


def _outline_shape_points(e: dict) -> tuple[list, bool] | None:
    """(points, closed) for one board_outline edge; None when the edge is unusable."""
    t = e.get("type")
    if t == "line" and e.get("start") and e.get("end"):
        return [tuple(e["start"]), tuple(e["end"])], False
    if t == "arc" and e.get("start") and e.get("end"):
        return arc_points(e["start"], e.get("mid"), e["end"], max_chords=_OUTLINE_MAX_CHORDS), False
    if t == "curve" and e.get("points") and len(e["points"]) == 4:
        return [tuple(p) for p in _bezier_points(e["points"])], False
    if t == "rect" and e.get("start") and e.get("end"):
        (x1, y1), (x2, y2) = e["start"], e["end"]
        return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)], True
    if t == "polygon" and e.get("points") and len(e["points"]) >= 3:
        return [tuple(p) for p in e["points"]], True
    if t == "circle" and e.get("center") and e.get("end"):
        cx, cy = e["center"]
        ex, ey = e["end"]
        r = math.hypot(ex - cx, ey - cy)
        if r <= 0.0:
            return None
        # chord count as arc_points: sagitta within 0.002 mm
        n = min(_OUTLINE_MAX_CHORDS,
                max(8, math.ceil(2.0 * math.pi / (2.0 * math.acos(max(-1.0, 1.0 - 0.002 / r))))))
        a0 = math.atan2(ey - cy, ex - cx)
        return [(cx + r * math.cos(a0 + 2.0 * math.pi * k / n),
                 cy + r * math.sin(a0 + 2.0 * math.pi * k / n)) for k in range(n)], True
    return None


def outline_loops(edges: list[dict]) -> list[list[tuple[float, float]]] | None:
    """Closed loops of a board outline (``board_outline.edges``), as KiCad chains Edge.Cuts.

    Rects, polygons and circles are loops of their own; lines, arcs and curves are joined end to
    end within OUTLINE_CHAINING_EPSILON_MM. None when any chain does not close, an edge is
    unusable or a loop is drawn twice: KiCad then uses the outline's bounding box
    (BuildBoardPolygonOutlines).
    """
    eps = OUTLINE_CHAINING_EPSILON_MM
    loops: list[list[tuple[float, float]]] = []
    open_paths: list[list[tuple[float, float]]] = []
    for e in edges:
        shape = _outline_shape_points(e)
        if shape is None:
            return None
        pts, closed = shape
        if closed:
            loops.append(pts)
        elif math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) > 0.0:
            open_paths.append(pts)

    # endpoint grid with cell size eps: a neighbour sits in the same or an adjacent cell
    grid: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for i, p in enumerate(open_paths):
        for end in (0, -1):
            x, y = p[end]
            grid.setdefault((math.floor(x / eps), math.floor(y / eps)), []).append((i, end))
    used = [False] * len(open_paths)

    def _nearest(pt):
        gx, gy = math.floor(pt[0] / eps), math.floor(pt[1] / eps)
        best = None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for i, end in grid.get((gx + dx, gy + dy), ()):
                    if used[i]:
                        continue
                    q = open_paths[i][end]
                    d = math.hypot(q[0] - pt[0], q[1] - pt[1])
                    if d <= eps and (best is None or (d, i, end) < best):
                        best = (d, i, end)
        return best

    for seed in range(len(open_paths)):
        if used[seed]:
            continue
        used[seed] = True
        path = list(open_paths[seed])
        while True:
            head, tail = path[0], path[-1]
            if len(path) > 2 and math.hypot(head[0] - tail[0], head[1] - tail[1]) <= eps:
                break
            nxt = _nearest(tail)
            if nxt is None:
                return None
            _, i, end = nxt
            used[i] = True
            seg = open_paths[i] if end == 0 else open_paths[i][::-1]
            path.extend(seg[1:])
        loops.append(path[:-1])
    loops = [lp for lp in loops if len(lp) >= 3]
    # a shape drawn twice cancels itself under even-odd; KiCad rejects overlapping outlines
    seen: set = set()
    for lp in loops:
        key = frozenset((round(x, 4), round(y, 4)) for x, y in lp)
        if key in seen:
            return None
        seen.add(key)
    return loops or None


def point_in_outline(px: float, py: float, loops: list) -> bool:
    """Even-odd membership: a point inside a slot or cutout loop is off the board."""
    return _point_in_polys(px, py, loops)


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
                      polygon: list[tuple[float, float]],
                      edges=None) -> bool:
    """Ray-casting point-in-polygon test.

    Returns True if point (px, py) is inside the polygon defined by
    a list of (x, y) vertices.

    edges: optional iterable of vertex indices i, each naming the edge (i - 1, i).
    Only those edges are tested; the result is unchanged as long as it holds every
    edge whose y-span contains py (the ZoneFills strip index).
    """
    n = len(polygon)
    if n < 3:
        return False
    inside = False
    for i in (range(n) if edges is None else edges):
        xi, yi = polygon[i]
        xj, yj = polygon[i - 1]
        if ((yi > py) != (yj > py)) and \
                (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
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


def _strip_of(y: float, y0: float, h: float, k: int) -> int:
    """The strip a y falls in, clamped to 0..k-1 (NaN falls in strip 0)."""
    t = (y - y0) / h
    return 0 if not t > 0 else k - 1 if t >= k else int(t)


class ZoneFills:
    """Spatial index for zone filled polygon data.

    Stores filled polygon coordinates extracted during zone parsing.
    Used for point-in-polygon queries to determine actual copper presence
    at specific locations. Not included in JSON output (coordinates are
    too large — often thousands of vertices per fill region).

    Requires that zones have been filled in KiCad (Edit → Fill All Zones)
    before the PCB file was saved. Stale fills will produce incorrect results.

    `min_edge_distance` additionally maintains a lazily built per-fill
    segment grid so nearest-edge queries don't need to walk every
    vertex of every fill. Point queries use a lazily built per-fill strip
    index (`_strip_index`) so the ray cast only tests edges near the point's y.
    """

    def __init__(self) -> None:
        self._fills: list[
            tuple[int, int, str, list[tuple[float, float]],
                  tuple[float, float, float, float]]
        ] = []
        self._next_fill_id = 0
        self._grids: dict[int, tuple] = {}
        self._strips: dict[int, tuple] = {}
        self._inflate: dict[int, float] = {}

    def add(self, zone_idx: int, layer: str,
            coords: list[tuple[float, float]], inflate: float = 0.0) -> None:
        """Register a filled polygon region for spatial queries.

        inflate > 0: the copper is the polygon grown by this radius with round
        corners (a KiCad 5 fill stored as the centre line of its stroke)."""
        bbox = _polygon_bbox(coords)
        fill_id = self._next_fill_id
        self._next_fill_id += 1
        if inflate > 0:
            self._inflate[fill_id] = inflate
            bbox = (bbox[0] - inflate, bbox[1] - inflate,
                    bbox[2] + inflate, bbox[3] + inflate)
        self._fills.append((fill_id, zone_idx, layer, coords, bbox))

    def _strip_index(self, fill_id: int):
        """Lazily built horizontal strips: strip -> indices i of the edges (i - 1, i)
        whose y-span overlaps that strip. (y0, strip height, strip count, strips).

        The ray cast only toggles on an edge with min(yi, yj) <= py < max(yi, yj). The strip
        number never decreases as y grows, so every such edge is listed in py's strip and
        testing that strip alone gives the same answer as walking every edge."""
        s = self._strips.get(fill_id)
        if s is not None:
            return s
        coords = self._fills[fill_id][3]
        n = len(coords)
        ys = [p[1] for p in coords]
        y0 = min(ys, default=0.0)
        span = max(ys, default=0.0) - y0
        spans = [(min(ys[i], ys[i - 1]), max(ys[i], ys[i - 1])) for i in range(n)]
        k = max(1, min(4096, n // 8))
        # tall edges are listed in every strip they cross: coarsen a comb-shaped fill until the
        # index holds at most 32n entries, counted before any strip is filled
        while k > 1 and sum(_strip_of(hi, y0, span / k or 1.0, k)
                            - _strip_of(lo, y0, span / k or 1.0, k) + 1
                            for lo, hi in spans) > 32 * n:
            k //= 2
        h = span / k or 1.0
        strips: list[list[int]] = [[] for _ in range(k)]
        for i, (lo, hi) in enumerate(spans):
            for b in range(_strip_of(lo, y0, h, k), _strip_of(hi, y0, h, k) + 1):
                strips[b].append(i)
        s = (y0, h, k, strips)
        self._strips[fill_id] = s
        return s

    def _contains(self, fill_id: int, x: float, y: float,
                  coords: list[tuple[float, float]]) -> bool:
        if len(coords) >= 3:
            y0, h, k, strips = self._strip_index(fill_id)
            inside = _point_in_polygon(x, y, coords, strips[_strip_of(y, y0, h, k)])
        else:
            inside = False
        if inside:
            return True
        r = self._inflate.get(fill_id)
        return r is not None and self._near_edge(fill_id, x, y, r)

    def _near_edge(self, fill_id: int, x: float, y: float, r: float) -> bool:
        """True when (x, y) is within r of the fill's polygon boundary."""
        cell, _ncx, _ncy, cells = self._segment_grid(fill_id)
        _fid, _zidx, _layer, coords, bbox = self._fills[fill_id]
        n = len(coords)
        seen: set = set()
        for cx in range(int((x - r - bbox[0]) // cell), int((x + r - bbox[0]) // cell) + 1):
            for cy in range(int((y - r - bbox[1]) // cell), int((y + r - bbox[1]) // cell) + 1):
                for i in cells.get((cx, cy), ()):
                    if i in seen:
                        continue
                    seen.add(i)
                    x1, y1 = coords[i]
                    x2, y2 = coords[(i + 1) % n]
                    if _dist_point_to_segment(x, y, x1, y1, x2, y2) <= r:
                        return True
        return False

    def _segment_grid(self, fill_id: int):
        """Lazily built uniform grid: cell -> indices of polygon segments whose
        bbox overlaps that cell. (cell_size, ncx, ncy, cells)."""
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

    def fill_layers(self, zone_idxs) -> set[str]:
        """Layers on which any of zone_idxs has filled copper."""
        return {layer for _fid, zone_idx, layer, _coords, _bbox in self._fills
                if zone_idx in zone_idxs}

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
            if self._contains(_fill_id, x, y, coords):
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
            if not self._contains(fill_id, x, y, coords):
                continue
            if net_name is not None and zones[zone_idx].get("net_name", "") != net_name:
                continue
            results.append((fill_id, zone_idx))
        return results

    def has_copper_at(self, x: float, y: float, layer: str, zone_idxs=None) -> bool:
        """Check if any zone (of zone_idxs, when given) has filled copper at (x, y) on layer."""
        for _fill_id, _zone_idx, fill_layer, coords, bbox in self._fills:
            if fill_layer != layer:
                continue
            if zone_idxs is not None and _zone_idx not in zone_idxs:
                continue
            if x < bbox[0] or x > bbox[2] or y < bbox[1] or y > bbox[3]:
                continue
            if self._contains(_fill_id, x, y, coords):
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

        Uses a lazily built per-fill segment grid; results are
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
        An inflated fill's edge is its polygon grown by the radius: the
        polygon distance d becomes d + r inside the polygon, |d - r| outside.
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
        max_inflate = max(self._inflate.values(), default=0.0)
        for offset, fid, coords, bbox in candidates:
            if offset - max_inflate >= best:
                break  # sorted ascending: every remaining candidate is >= offset >= best
            rad = self._inflate.get(fid, 0.0)
            fbest = float("inf")  # polygon distance for this fill
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
                if r > 0:
                    lower = math.hypot(offset, (r - 1) * cell)
                    if lower >= fbest or lower - rad >= best:
                        break  # exact: every unvisited segment is >= lower away
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
                        if d < fbest:
                            fbest = d
                r += 1
            if rad and fbest < float("inf"):
                fbest = fbest + rad if _point_in_polygon(x, y, coords) else abs(fbest - rad)
            if fbest < best:
                best = fbest
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
    """Copper presence check across zones, tracks, and pads.

    Given a point (x, y) on a given layer, returns True if any copper
    object is within radius_mm.  Zone fills, track segments and pads all
    count as copper; a return-path caller asks for zone fills only, since
    a track or pad of another net is not a reference plane.

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
    def has_coverage_near(self, x, y, layer, *, radius_mm=0.5, zone_idxs=None,
                          fills_only=False):
        """True if any copper on *layer* is within *radius_mm* of (x, y).

        Checks zone fills (center + 8-point perimeter), tracks, and pads.
        zone_idxs limits the fills to those zones; fills_only skips tracks and pads.
        """
        zf = self.zone_fills
        if zf is not None and zf.has_data:
            # Center point -- fast path
            if zf.has_copper_at(x, y, layer, zone_idxs):
                return True
            # 8-point perimeter at radius_mm
            for i in range(8):
                ang = i * math.pi / 4.0
                px = x + radius_mm * math.cos(ang)
                py = y + radius_mm * math.sin(ang)
                if zf.has_copper_at(px, py, layer, zone_idxs):
                    return True
        if fills_only:
            return False

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


def _chain_segments(segs: list, tol: float = 0.02) -> list | None:
    """Chain undirected 2D segments into closed loops.

    Returns a list of polygons (each a list of (x, y) vertices, implicit
    closure) or None when any chain fails to close within tolerance —
    callers then keep the AABB-only behavior.
    """
    def _close(p, q):  # Euclidean, as KiCad's close_enough (convert_shape_list_to_polygon.cpp)
        return math.hypot(p[0] - q[0], p[1] - q[1]) <= tol

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


def _signed_depth(px: float, py: float, polys: list) -> float:
    """Distance from (px, py) to the polygon set's boundary, negative outside."""
    d = min(_point_segment_distance(px, py, poly[i - 1][0], poly[i - 1][1], poly[i][0], poly[i][1])
            for poly in polys for i in range(len(poly)))
    return d if _point_in_polys(px, py, polys) else -d


def _signed_area(ring: list) -> float:
    return sum(ring[i - 1][0] * ring[i][1] - ring[i][0] * ring[i - 1][1]
               for i in range(len(ring))) / 2


def _inset_polys(polys: list, inset: float) -> list:
    """Shrink an even-odd polygon set by ``inset``: every edge moves ``inset`` towards the
    set's inside and neighbouring edges meet at their mitred intersection, as KiCad's
    courtyard deflate does. A ring that shrinks away is dropped."""
    out = []
    for k, poly in enumerate(polys):
        ring = [(float(p[0]), float(p[1])) for i, p in enumerate(poly)
                if (float(p[0]), float(p[1])) != (float(poly[i - 1][0]), float(poly[i - 1][1]))]
        area = _signed_area(ring) if len(ring) >= 3 else 0.0
        if area == 0:
            continue
        nested = sum(1 for j, other in enumerate(polys)
                     if j != k and _point_in_polygon(ring[0][0], ring[0][1],
                                                     [(q[0], q[1]) for q in other]))
        # left normal points inside a counter-clockwise ring; a hole's inside is its outside
        sign = (1 if area > 0 else -1) * (-1 if nested % 2 else 1)
        lines = []
        for i in range(len(ring)):
            (ax, ay), (bx, by) = ring[i - 1], ring[i]
            ln = math.hypot(bx - ax, by - ay)
            nx, ny = -(by - ay) / ln * sign * inset, (bx - ax) / ln * sign * inset
            lines.append((ax + nx, ay + ny, bx - ax, by - ay))
        shrunk = []
        for i in range(len(lines)):
            px, py, dx, dy = lines[i - 1]
            qx, qy, ex, ey = lines[i]
            den = dx * ey - dy * ex
            if abs(den) < 1e-12 * (dx * dx + dy * dy + ex * ex + ey * ey):
                shrunk.append((qx, qy))
                continue
            t = ((qx - px) * ey - (qy - py) * ex) / den
            mx, my = px + t * dx, py + t * dy
            vx, vy = ring[i - 1]
            if den * sign < 0 and math.hypot(mx - vx, my - vy) > 2 * inset:
                # a sharp inward notch: bevel instead of a long mitre spike
                shrunk.extend(((px + dx, py + dy), (qx, qy)))
            else:
                shrunk.append((mx, my))
        # a ring narrower than twice the inset turns inside out
        if _signed_area(shrunk) * area > 0:
            out.append(shrunk)
    return out


def courtyards_collide(polys_a: list, polys_b: list, inset: float = 0.005) -> bool:
    """True when the two polygon sets (even-odd) still meet after each is shrunk by ``inset``.

    KiCad shrinks every courtyard by 0.005 mm before its collision test, so courtyards that
    touch or overlap by less than 0.01 mm are legal; shrunk shapes that touch (to 0.1 nm,
    below KiCad's 1 nm unit) collide.
    """
    sa, sb = _inset_polys(polys_a, inset), _inset_polys(polys_b, inset)
    if not sa or not sb:
        return False
    bxa = _polygon_bbox([p for poly in sa for p in poly])
    bxb = _polygon_bbox([p for poly in sb for p in poly])
    if (bxa[0] > bxb[2] + 1e-7 or bxb[0] > bxa[2] + 1e-7
            or bxa[1] > bxb[3] + 1e-7 or bxb[1] > bxa[3] + 1e-7):
        return False
    edges_b = [(*poly[i - 1], *poly[i]) for poly in sb for i in range(len(poly))]
    for poly in sa:
        for i in range(len(poly)):
            ax, ay = poly[i - 1]
            bx, by = poly[i]
            for edge in edges_b:
                if _segment_segment_distance(ax, ay, bx, by, *edge) <= 1e-7:
                    return True
    # boundaries apart: the sets meet only if one holds the other
    return (any(_point_in_polys(poly[0][0], poly[0][1], sb) for poly in sa)
            or any(_point_in_polys(poly[0][0], poly[0][1], sa) for poly in sb))


def overlap_area_mm2(polys_a: list, polys_b: list,
                     ix1: float, iy1: float, ix2: float, iy2: float) -> float:
    """Overlap area of two polygon sets inside the box, by adaptive subdivision: a cell whose
    centre lies deeper inside both (or further outside either) than its half-diagonal is
    wholly in (out); others split along their long side down to 1/1024 of the box."""
    min_side = max(ix2 - ix1, iy2 - iy1) / 1024
    area = 0.0
    cells = [(ix1, iy1, ix2, iy2)]
    while cells:
        x1, y1, x2, y2 = cells.pop()
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        depth = min(_signed_depth(mx, my, polys_a), _signed_depth(mx, my, polys_b))
        half_diag = math.hypot(x2 - x1, y2 - y1) / 2
        if depth >= half_diag:
            area += (x2 - x1) * (y2 - y1)
        elif depth <= -half_diag:
            continue
        elif max(x2 - x1, y2 - y1) <= min_side:
            if depth > 0:
                area += (x2 - x1) * (y2 - y1)
        elif x2 - x1 >= y2 - y1:
            cells.extend(((x1, y1, mx, y2), (mx, y1, x2, y2)))
        else:
            cells.extend(((x1, y1, x2, my), (x1, my, x2, y2)))
    return area


def _refined_overlap_mm2(polys_a: list, polys_b: list,
                         ix1: float, iy1: float, ix2: float, iy2: float,
                         samples: int = 24) -> float:
    """Courtyard overlap area inside the box (ix1, iy1)-(ix2, iy2), estimated by grid-sampling
    membership in both polygon sets. A thin overlap can fall between the samples."""
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
    a literal membership test.
    """
    layers = pad.get("layers")
    if (pad.get("type") == "np_thru_hole" and layer.endswith(".Cu")
            and not npth_flashes_copper(pad)):
        return False
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
    Bbox corners would sit well outside the copper of a large round pad and
    read an unrelated fill cutout as the clearance.
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
    rotated by the pad angle; THT pads via their "*.Cu" wildcard;
    circle/oval pads sampled on their true outline);
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
    """Point-in-pad test for VP-001: circle/oval exact, other
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


def _nm(v) -> int:
    return round(float(v or 0) * 1e6)


def npth_flashes_copper(pad: dict) -> bool:
    """True when an NPTH pad carries copper, as KiCad's PAD::IsOnCopperLayer decides: it
    has none when, on any of its padstack layers, a centred circle pad is no wider than
    the hole or a centred oval pad fits inside it; other shapes always keep copper."""
    dx = _nm(pad.get("drill"))
    dy = _nm(pad.get("drill_h", pad.get("drill"))) if pad.get("drill_shape") == "oval" else dx
    main = {"shape": pad.get("shape", ""), "width": pad.get("width", 0),
            "height": pad.get("height", 0), "offset": pad.get("_drill_offset", False)}
    stack = [{**main, **e} for e in pad.get("_padstack") or ()]
    # A padstack entry for F.Cu replaces the pad's own (front) properties.
    if not any(e["layer"] == "F.Cu" for e in stack):
        stack.append(main)
    for props in stack:
        if props["offset"]:
            continue
        w, h = _nm(props["width"]), _nm(props["height"])
        if props["shape"] == "circle" and w <= dx:
            return False
        if props["shape"] == "oval" and w <= dx and h <= dy:
            return False
    return True


def pad_copper_layers(pad: dict, copper_layers: list[str]) -> list[str]:
    """Copper layers a pad connects on: ``*.Cu`` is every board copper layer,
    ``F&B.Cu`` the two outer ones. An NPTH pad connects only when it carries copper,
    and then on its first copper layer in stack order only (KiCad's CN_LIST::Add)."""
    layers = pad.get("layers") or []
    if pad.get("type") == "np_thru_hole":
        if not npth_flashes_copper(pad):
            return []
        if "*.Cu" in layers or "F&B.Cu" in layers:
            return ["F.Cu"]
        order = {name: i for i, name in enumerate(copper_layers)}
        own = [layer for layer in layers if layer.endswith(".Cu")]
        return [min(own, key=lambda name: order.get(name, len(order)))] if own else []
    out: list[str] = []
    for layer in layers:
        if layer == "*.Cu":
            out.extend(copper_layers)
        elif layer == "F&B.Cu":
            out.extend(("F.Cu", "B.Cu"))
        elif layer.endswith(".Cu"):
            out.append(layer)
    return list(dict.fromkeys(out))


def _segment_segment_distance(ax: float, ay: float, bx: float, by: float,
                              cx: float, cy: float, dx: float, dy: float) -> float:
    """Shortest distance between segments AB and CD (0 when they cross)."""
    def cross(ox, oy, px, py, qx, qy):
        return (px - ox) * (qy - oy) - (py - oy) * (qx - ox)
    d1 = cross(cx, cy, dx, dy, ax, ay)
    d2 = cross(cx, cy, dx, dy, bx, by)
    d3 = cross(ax, ay, bx, by, cx, cy)
    d4 = cross(ax, ay, bx, by, dx, dy)
    if d1 * d2 < 0 and d3 * d4 < 0:
        return 0.0
    return min(_point_segment_distance(ax, ay, cx, cy, dx, dy),
               _point_segment_distance(bx, by, cx, cy, dx, dy),
               _point_segment_distance(cx, cy, ax, ay, bx, by),
               _point_segment_distance(dx, dy, ax, ay, bx, by))


def _segment_box_distance(ax: float, ay: float, bx: float, by: float,
                          hw: float, hh: float) -> float:
    """Distance from segment AB to the axis-aligned box |x| <= hw, |y| <= hh."""
    if (abs(ax) <= hw and abs(ay) <= hh) or (abs(bx) <= hw and abs(by) <= hh):
        return 0.0
    corners = ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))
    return min(_segment_segment_distance(ax, ay, bx, by, *corners[i], *corners[(i + 1) % 4])
               for i in range(4))


def segment_to_pad_distance(seg: dict, pad: dict) -> float:
    """Distance from a track centreline (x1, y1)-(x2, y2) to a pad's copper; 0 when they
    overlap. circle, oval (stadium), rect/trapezoid (box), roundrect (inner box grown by
    the corner radius, ``roundrect_rratio`` x the short side, KiCad default 0.25); a custom
    pad is its anchor plus its primitives (``_anchor``/``_prims`` from the reader), or the
    max(w, h)/2 circle without them. The pad angle is absolute, as in `_point_in_pad`."""
    w = pad.get("width", 0) or 0
    h = pad.get("height", 0) or 0
    px, py = pad["abs_x"], pad["abs_y"]
    ax, ay = seg["x1"] - px, seg["y1"] - py
    bx, by = seg["x2"] - px, seg["y2"] - py
    shape = pad.get("shape", "rect")
    if shape == "custom" and "_anchor" in pad:
        return _custom_pad_distance(seg, pad)
    if shape in ("circle", "custom"):
        d = _point_segment_distance(0.0, 0.0, ax, ay, bx, by)
        return max(0.0, d - max(w, h) / 2.0)
    angle = pad.get("angle") or 0
    if angle:
        # Inverse of the pad's local -> board rotation, as in `_point_in_pad`.
        rad = math.radians(-angle)
        c, s = math.cos(rad), math.sin(rad)
        ax, ay = ax * c + ay * s, -ax * s + ay * c
        bx, by = bx * c + by * s, -bx * s + by * c
    hw, hh = w / 2.0, h / 2.0
    if shape == "oval":
        r = min(hw, hh)
        if hw >= hh:
            core = (-(hw - r), 0.0, hw - r, 0.0)
        else:
            core = (0.0, -(hh - r), 0.0, hh - r)
        return max(0.0, _segment_segment_distance(ax, ay, bx, by, *core) - r)
    rr = 0.0
    if shape == "roundrect":
        ratio = pad.get("roundrect_rratio", 0.25)
        rr = min(max(ratio, 0.0), 0.5) * min(w, h)
    return max(0.0, _segment_box_distance(ax, ay, bx, by, hw - rr, hh - rr) - rr)


def _pad_cores(pad: dict) -> list[tuple[dict, float]]:
    """A pad's copper as segments with a radius whose union covers its outline (a circle is
    its centre, an oval its core segment, a box or roundrect its edges, a custom pad its
    anchor plus its primitives); together with `segment_to_pad_distance` in the other
    direction this finds overlap and containment."""
    px, py = pad["abs_x"], pad["abs_y"]
    w = pad.get("width", 0) or 0
    h = pad.get("height", 0) or 0
    shape = pad.get("shape", "rect")
    if shape == "custom" and "_anchor" in pad:
        anchor = {k: pad[k] for k in ("abs_x", "abs_y", "width", "height", "angle") if k in pad}
        anchor["shape"] = pad["_anchor"]
        if anchor["shape"] == "circle":
            anchor["height"] = anchor.get("width", 0)
        cores = _pad_cores(anchor)
        for prim in pad["_prims"]:
            pts, hw = prim["pts"], prim["width"] / 2.0
            n = len(pts)
            if n == 1:
                cores.append(({"x1": pts[0][0], "y1": pts[0][1], "x2": pts[0][0], "y2": pts[0][1]}, hw))
            for i in range(n if prim["closed"] and n >= 3 else n - 1):
                (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
                cores.append(({"x1": x1, "y1": y1, "x2": x2, "y2": y2}, hw))
        return cores
    if shape in ("circle", "custom"):
        return [({"x1": px, "y1": py, "x2": px, "y2": py}, max(w, h) / 2.0)]
    hw, hh = w / 2.0, h / 2.0
    if shape == "oval":
        r = min(hw, hh)
        local = [((-(hw - r), 0.0), (hw - r, 0.0))] if hw >= hh else [((0.0, -(hh - r)), (0.0, hh - r))]
    else:
        r = 0.0
        if shape == "roundrect":
            r = min(max(pad.get("roundrect_rratio", 0.25), 0.0), 0.5) * min(w, h)
        bx, by = hw - r, hh - r
        corners = ((-bx, -by), (bx, -by), (bx, by), (-bx, by))
        local = [(corners[i], corners[(i + 1) % 4]) for i in range(4)]
    rad = math.radians(-(pad.get("angle") or 0))
    c, s = math.cos(rad), math.sin(rad)
    cores = []
    for (ax, ay), (bx_, by_) in local:
        cores.append(({"x1": px + ax * c - ay * s, "y1": py + ax * s + ay * c,
                       "x2": px + bx_ * c - by_ * s, "y2": py + bx_ * s + by_ * c}, r))
    return cores


def pads_touch(a: dict, b: dict, eps: float = 0.005) -> bool:
    """True when the copper of pads *a* and *b* overlaps (or one contains the other)."""
    return any(segment_to_pad_distance(seg, b) <= r + eps for seg, r in _pad_cores(a)) or \
        any(segment_to_pad_distance(seg, a) <= r + eps for seg, r in _pad_cores(b))


def _custom_pad_distance(seg: dict, pad: dict) -> float:
    """`segment_to_pad_distance` for a custom pad: KiCad's copper is the anchor (a circle of
    the size's x, or the size box) plus every primitive, each stroked by its width."""
    anchor = {k: pad[k] for k in ("abs_x", "abs_y", "width", "height", "angle") if k in pad}
    anchor["shape"] = pad["_anchor"]
    if anchor["shape"] == "circle":
        anchor["height"] = anchor.get("width", 0)
    best = segment_to_pad_distance(seg, anchor)
    x1, y1, x2, y2 = seg["x1"], seg["y1"], seg["x2"], seg["y2"]
    for prim in pad["_prims"]:
        if best <= 0:
            break
        pts = prim["pts"]
        n = len(pts)
        if prim["filled"] and (_point_in_polygon(x1, y1, pts) or _point_in_polygon(x2, y2, pts)):
            return 0.0
        hw = prim["width"] / 2.0
        if n == 1:
            d = _point_segment_distance(pts[0][0], pts[0][1], x1, y1, x2, y2)
            best = min(best, max(0.0, d - hw))
            continue
        for i in range(n if prim["closed"] and n >= 3 else n - 1):
            (qx1, qy1), (qx2, qy2) = pts[i], pts[(i + 1) % n]
            d = _segment_segment_distance(x1, y1, x2, y2, qx1, qy1, qx2, qy2)
            best = min(best, max(0.0, d - hw))
    return best
