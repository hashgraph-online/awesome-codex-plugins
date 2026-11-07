"""Copper connectivity graph via union-find over pads, vias, and zone fills.

Builds a per-net island map from PCB data: pads connected by tracks or zone
copper are grouped into islands. Nets with multiple islands have plane splits
or routing gaps. Gap locations are estimated from island bounding boxes.

Called from analyze_pcb.py in --full mode. Requires track segment coordinates,
via positions, footprint pad positions, and ZoneFills polygon data.
"""

from __future__ import annotations

import math
import re

from pcb.geometry import (
    _point_in_polygon, _segment_segment_distance, pad_copper_layers, pads_touch,
    segment_to_pad_distance,
)

# Copper closer than this counts as touching (rounding in the board file).
_CONTACT_EPS = 0.005


def _node_probe_points(x: float,
                       y: float,
                       copper_radius: float) -> list[tuple[float, float]]:
    """Probe center plus perimeter points around a copper feature.

    Uses 8 perimeter points (not 16) at one radius to keep zone lookups
    bounded.  Total: 9 probes per node (center + 8 perimeter).
    """
    points = [(x, y)]
    radius = max(0.05, copper_radius * 0.85) if copper_radius > 0 else 0.10
    for i in range(8):
        ang = i * math.pi / 4.0
        points.append((x + radius * math.cos(ang), y + radius * math.sin(ang)))
    return points


def _node_fill_regions(node: dict,
                       zone_fills,
                       zones: list[dict],
                       net_name: str) -> set[int]:
    """Return same-net fill-region ids touching a pad, via or track end."""
    if zone_fills is None or not zone_fills.has_data:
        return set()
    x = node.get('x')
    y = node.get('y')
    layer = node.get('layer', '')
    if x is None or y is None or not layer:
        return set()
    regions: set[int] = set()
    # A track probes its end point only (KiCad also joins a track whose body overlaps
    # the fill; not modelled). A pad or via probes its outline.
    points = ([(x, y)] if node.get('kind') == 'track'
              else _node_probe_points(x, y, node.get('copper_radius', 0.0)))
    for px, py in points:
        for fill_id, _zone_idx in zone_fills.fill_regions_at_point(
                px, py, layer, zones, net_name=net_name):
            regions.add(fill_id)
    return regions


def _bucket_coord(value: float, tolerance: float) -> int:
    """Bucket a coordinate for endpoint clustering."""
    if tolerance <= 0:
        tolerance = 0.05
    return int(round(value / tolerance))


def _stackup_sort_key(layer: str) -> tuple[int, int]:
    """Order copper layers by physical stackup position, not alphabetically.

    KiCad names inner copper layers ``In1.Cu``..``InN.Cu``, numbered
    top-to-bottom, so the physical order is ``F.Cu < In1.Cu < ... < InN.Cu
    < B.Cu``. Alphabetical sorting would put ``B.Cu`` first, breaking the
    "expand a via to the layers between its endpoints" logic below.
    """
    if layer == 'F.Cu':
        return (0, 0)
    if layer == 'B.Cu':
        return (2, 0)
    m = re.match(r'In(\d+)\.Cu', layer)
    return (1, int(m.group(1))) if m else (1, 0)


def _expand_copper_layers(layers: list[str],
                          copper_layers: list[str]) -> list[str]:
    """Expand a via's copper layer specs to the physical layers it touches.

    - ``*.Cu`` expands to every copper layer.
    - A via records only its two endpoint layers (e.g. a through via is
      ``["F.Cu", "B.Cu"]``); expand it to every layer between the endpoints,
      inclusive, so it unions through any inner plane it passes through
      (GH issue #24). ``copper_layers`` must be in physical stackup order.
    - Any other list of concrete layers is returned de-duplicated.
    """
    cu = [layer for layer in (layers or [])
          if layer == '*.Cu' or '.Cu' in layer]
    if '*.Cu' in cu:
        return list(copper_layers)
    concrete = [layer for layer in cu if layer in copper_layers]
    if len(concrete) == 2:
        i = copper_layers.index(concrete[0])
        j = copper_layers.index(concrete[1])
        lo, hi = (i, j) if i <= j else (j, i)
        return copper_layers[lo:hi + 1]
    # Preserve order while de-duplicating
    return list(dict.fromkeys(cu))


class UnionFind:
    """Weighted union-find with path compression."""

    def __init__(self) -> None:
        self._parent: dict[str, str] = {}
        self._rank: dict[str, int] = {}

    def make_set(self, x: str) -> None:
        if x not in self._parent:
            self._parent[x] = x
            self._rank[x] = 0

    def find(self, x: str) -> str:
        if self._parent[x] != x:
            self._parent[x] = self.find(self._parent[x])
        return self._parent[x]

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self._rank[ra] < self._rank[rb]:
            ra, rb = rb, ra
        self._parent[rb] = ra
        if self._rank[ra] == self._rank[rb]:
            self._rank[ra] += 1

    def components(self) -> dict[str, list[str]]:
        """Return {root: [members]} for all sets."""
        groups: dict[str, list[str]] = {}
        for x in self._parent:
            root = self.find(x)
            groups.setdefault(root, []).append(x)
        return groups


class _CellIndex:
    """Uniform grid of items (track pieces, pads) by the cells their copper covers."""

    def __init__(self, cell_size: float = 1.0) -> None:
        self._cell = cell_size
        self._grid: dict[tuple[int, int], list[int]] = {}

    def _cells(self, x0: float, y0: float, x1: float, y1: float):
        c = self._cell
        for cx in range(math.floor(x0 / c), math.floor(x1 / c) + 1):
            for cy in range(math.floor(y0 / c), math.floor(y1 / c) + 1):
                yield cx, cy

    def add_box(self, idx: int, x0: float, y0: float, x1: float, y1: float) -> None:
        for cell in self._cells(x0, y0, x1, y1):
            self._grid.setdefault(cell, []).append(idx)

    def add_segment(self, idx: int, x1: float, y1: float, x2: float, y2: float,
                    reach: float) -> None:
        """Index a thick segment by the cells along it, not its whole bounding box."""
        step = self._cell / 2.0
        n = max(1, math.ceil(math.hypot(x2 - x1, y2 - y1) / step))
        r = reach + step / 2.0
        cells: set[tuple[int, int]] = set()
        for k in range(n + 1):
            x = x1 + (x2 - x1) * k / n
            y = y1 + (y2 - y1) * k / n
            cells.update(self._cells(x - r, y - r, x + r, y + r))
        for cell in cells:
            self._grid.setdefault(cell, []).append(idx)

    def query(self, x0: float, y0: float, x1: float, y1: float) -> list[int]:
        found: set[int] = set()
        for cell in self._cells(x0, y0, x1, y1):
            found.update(self._grid.get(cell, ()))
        return sorted(found)


def _arc_chords(start, mid, end, tol: float = 0.005) -> list[tuple[float, float]]:
    """Points along a start/mid/end arc whose chords stay within `tol` of the arc,
    using at most 64 chords (a large arc's chords may then sag further)."""
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
    sweep = ne if nm <= ne else ne - tau
    max_step = 2.0 * math.acos(max(-1.0, 1.0 - tol / r)) if r > tol else math.pi
    n = min(64, max(2, math.ceil(abs(sweep) / max_step)))
    pts = [(sx, sy)]
    for k in range(1, n):
        a = a_s + sweep * k / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pts.append((ex, ey))
    return pts


def build_connectivity_graph(
    footprints: list[dict],
    tracks: dict,
    vias: dict,
    zone_fills,
    zones: list[dict],
    net_id_map: dict[int, str],
    board_layers: list[dict] | None = None,
    graphics: list[dict] | None = None,
) -> dict[str, dict]:
    """Build per-net connectivity graph using union-find.

    Copper joins where it overlaps: a pad or via unions with every same-layer
    track piece its copper touches (real pad shape), track pieces union with
    each other, arcs as chords, and a via inside a pad unions with it. A copper
    graphic with a net is its outline as track pieces of its stroke width; a
    filled one also joins every same-net pad, via or track end inside it.

    Args:
        footprints: PCB footprint list with pads (abs_x, abs_y, net_name).
        tracks: Track dict with 'segments' and 'arcs' keys.
        vias: Via dict with 'vias' key.
        zone_fills: ZoneFills instance with filled polygon data.
        zones: Zone list matching zone_fills index.
        net_id_map: {net_id: net_name} mapping.
        board_layers: the board layer table (``extract_layers``); its copper
            layers are what ``*.Cu`` pads expand to.
        graphics: copper graphics with a net (``reader.extract_copper_graphics``).

    Returns:
        Dict keyed by net_name with islands, components, gaps, disconnected_pads.
    """
    segments = tracks.get('segments', [])
    arcs = tracks.get('arcs', []) or []
    via_list = vias.get('vias', [])
    wildcards = ('*.Cu', 'F&B.Cu')
    copper_layer_set: set[str] = set()
    for layer in board_layers or []:
        name = layer.get('name') if isinstance(layer, dict) else None
        if isinstance(name, str) and name.endswith('.Cu') and name not in wildcards:
            copper_layer_set.add(name)
    for seg in list(segments) + list(arcs):
        layer = seg.get('layer', '')
        if '.Cu' in layer and layer not in wildcards:
            copper_layer_set.add(layer)
    for via in via_list:
        for layer in via.get('layers', []) or []:
            if '.Cu' in layer and layer not in wildcards:
                copper_layer_set.add(layer)
    for zone in zones:
        for layer in zone.get('layers', []) or []:
            if '.Cu' in layer and layer not in wildcards:
                copper_layer_set.add(layer)
    copper_layers = sorted(copper_layer_set, key=_stackup_sort_key) or ['F.Cu', 'B.Cu']

    # Collect all nodes per net
    net_nodes: dict[str, list[dict]] = {}
    net_track_segments: dict[str, list[dict]] = {}

    # Each pad is its own node: pads sharing a reference and number join only through
    # copper or the footprint's jumper settings, as in KiCad.
    pad_instance_counts: dict[str, int] = {}
    jumper_pads: list[list[str]] = []
    for fp in footprints:
        ref = fp.get('reference', '')
        fp_pad_keys: dict[str, list[str]] = {}
        for pad in fp.get('pads', []):
            net_name = pad.get('net_name', '')
            if not net_name:
                continue
            x = pad.get('abs_x')
            y = pad.get('abs_y')
            if x is None or y is None:
                continue
            report_key = f"{ref}:{pad.get('number', '?')}"
            instance_idx = pad_instance_counts.get(report_key, 0)
            pad_instance_counts[report_key] = instance_idx + 1
            pad_key = report_key if instance_idx == 0 else f"{report_key}#{instance_idx}"
            fp_pad_keys.setdefault(str(pad.get('number', '?')), []).append(pad_key)
            layers = pad_copper_layers(pad, copper_layers)
            width = pad.get('width', 0) or 0
            height = pad.get('height', 0) or 0
            copper_radius = max(width, height) / 2.0 if (width or height) else 0.0
            reach = math.hypot(width, height) / 2.0
            for prim in pad.get('_prims', ()):
                hw = prim['width'] / 2.0
                for px, py in prim['pts']:
                    reach = max(reach, math.hypot(px - x, py - y) + hw)
            for layer in layers:
                net_nodes.setdefault(net_name, []).append({
                    'key': pad_key,
                    'report_key': pad_key,
                    'x': x,
                    'y': y,
                    'layer': layer,
                    'copper_radius': copper_radius,
                    'reach': reach,
                    'shape': pad,
                    'kind': 'pad',
                })

        if fp.get('_duplicate_pad_jumpers'):
            jumper_pads.extend(keys for keys in fp_pad_keys.values() if len(keys) > 1)
        for group in fp.get('_jumper_pad_groups', ()):
            keys = [k for number in group for k in fp_pad_keys.get(number, ())]
            if len(keys) > 1:
                jumper_pads.append(keys)

    for i, via in enumerate(via_list):
        net_id = via.get('net', 0)
        net_name = net_id_map.get(net_id, '') if isinstance(net_id, int) else str(net_id)
        if not net_name:
            continue
        x = via.get('x')
        y = via.get('y')
        if x is None or y is None:
            continue
        via_key = f"via_{i}"
        layers = _expand_copper_layers(via.get('layers', []), copper_layers)
        size = via.get('size', 0) or 0
        copper_radius = size / 2.0 if size else 0.0
        for layer in layers:
            net_nodes.setdefault(net_name, []).append({
                'key': via_key,
                'report_key': via_key,
                'x': x,
                'y': y,
                'layer': layer,
                'copper_radius': copper_radius,
                'reach': copper_radius,
                'shape': {'abs_x': x, 'abs_y': y, 'width': size, 'height': size,
                          'shape': 'circle'},
                'kind': 'via',
            })

    pieces: list[tuple[str, dict]] = []
    for seg_idx, seg in enumerate(segments):
        pieces.append((f"seg_{seg_idx}", seg))
    for arc_idx, arc in enumerate(arcs):
        if not arc.get('start') or not arc.get('end'):
            continue
        pts = _arc_chords(arc['start'], arc.get('mid'), arc['end'])
        for k in range(len(pts) - 1):
            pieces.append((f"arc_{arc_idx}.{k}", {
                'x1': pts[k][0], 'y1': pts[k][1],
                'x2': pts[k + 1][0], 'y2': pts[k + 1][1],
                'width': arc.get('width', 0),
                'layer': arc.get('layer', ''),
                'net': arc.get('net', 0),
            }))

    net_regions: dict[str, list[dict]] = {}
    net_graphics: dict[str, list[dict]] = {}
    for gi, g in enumerate(graphics or []):
        pts = g.get('pts') or []
        n = len(pts)
        closed = g.get('closed') and n >= 3
        for k in range(n if closed else n - 1):
            pieces.append((f"gr_{gi}.{k}", {
                'x1': pts[k][0], 'y1': pts[k][1],
                'x2': pts[(k + 1) % n][0], 'y2': pts[(k + 1) % n][1],
                'width': g.get('width', 0),
                'layer': g.get('layer', ''),
                'net': g.get('net', 0),
            }))
        g_net = g.get('net', 0)
        g_name = net_id_map.get(g_net, '') if isinstance(g_net, int) else str(g_net)
        if g_name and n >= 2:
            net_graphics.setdefault(g_name, []).append(
                {'key': f"gr_{gi}.0:a", 'layer': g.get('layer', ''), 'pts': pts})
        if closed and g.get('filled') and g_name:
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            net_regions.setdefault(g_name, []).append({
                'key': f"gr_{gi}.0:a", 'layer': g.get('layer', ''), 'pts': pts,
                'bbox': (min(xs), min(ys), max(xs), max(ys))})

    for piece_key, seg in pieces:
        seg_net_id = seg.get('net', 0)
        net_name = net_id_map.get(seg_net_id, '') if isinstance(seg_net_id, int) else str(seg_net_id)
        if not net_name:
            continue
        layer = seg.get('layer', '')
        if not layer or '.Cu' not in layer:
            continue
        x1 = seg.get('x1')
        y1 = seg.get('y1')
        x2 = seg.get('x2')
        y2 = seg.get('y2')
        if None in (x1, y1, x2, y2):
            continue
        a_key = f"{piece_key}:a"
        b_key = f"{piece_key}:b"
        width = seg.get('width', 0) or 0
        copper_radius = width / 2.0 if width else 0.0
        node_a = {
            'key': a_key,
            'x': x1,
            'y': y1,
            'layer': layer,
            'copper_radius': copper_radius,
            'kind': 'track',
        }
        node_b = {
            'key': b_key,
            'x': x2,
            'y': y2,
            'layer': layer,
            'copper_radius': copper_radius,
            'kind': 'track',
        }
        net_nodes.setdefault(net_name, []).extend([node_a, node_b])
        net_track_segments.setdefault(net_name, []).append({
            'a': a_key,
            'b': b_key,
            'layer': layer,
            'x1': x1,
            'y1': y1,
            'x2': x2,
            'y2': y2,
            'width': width,
        })

    result: dict[str, dict] = {}
    zone_nets = {z.get('net_name') for z in zones}

    for net_name, nodes in net_nodes.items():
        if len(nodes) < 2:
            if nodes:
                first_key = nodes[0]['key']
                result[net_name] = {
                    'islands': 1,
                    'components': {first_key: 0},
                    'gaps': [],
                    'disconnected_pads': [],
                }
            continue

        uf = UnionFind()
        all_keys: set[str] = set()
        report_keys: set[str] = set()
        logical_groups: dict[str, list[str]] = {}
        for node in nodes:
            key = node['key']
            uf.make_set(key)
            all_keys.add(key)
            if node.get('kind') in ('pad', 'via'):
                report_key = node.get('report_key', key)
                report_keys.add(report_key)
                logical_groups.setdefault(report_key, []).append(key)

        for keys in jumper_pads:
            present = [k for k in keys if k in all_keys]
            for i in range(1, len(present)):
                uf.union(present[0], present[i])

        node_layers = list(dict.fromkeys(node['layer'] for node in nodes))
        key_positions = {node['key']: (node['x'], node['y']) for node in nodes}

        # Phase 1: Route graph from explicit segment endpoints
        endpoint_buckets: dict[tuple[str, int, int], list[str]] = {}
        for node in nodes:
            if node.get('kind') != 'track':
                continue
            bucket = (
                node['layer'],
                _bucket_coord(node['x'], 0.05),
                _bucket_coord(node['y'], 0.05),
            )
            endpoint_buckets.setdefault(bucket, []).append(node['key'])
        for members in endpoint_buckets.values():
            for i in range(1, len(members)):
                uf.union(members[0], members[i])
        net_segs = net_track_segments.get(net_name, [])
        for seg in net_segs:
            uf.union(seg['a'], seg['b'])

        # Track pieces whose copper overlaps are one conductor.
        seg_grids: dict[str, _CellIndex] = {}
        for i, seg in enumerate(net_segs):
            seg_grids.setdefault(seg['layer'], _CellIndex()).add_segment(
                i, seg['x1'], seg['y1'], seg['x2'], seg['y2'], seg['width'] / 2.0)
        for i, seg in enumerate(net_segs):
            hw = seg['width'] / 2.0 + _CONTACT_EPS
            for j in seg_grids[seg['layer']].query(
                    min(seg['x1'], seg['x2']) - hw, min(seg['y1'], seg['y2']) - hw,
                    max(seg['x1'], seg['x2']) + hw, max(seg['y1'], seg['y2']) + hw):
                if j <= i:
                    continue
                other = net_segs[j]
                if (_segment_segment_distance(
                        seg['x1'], seg['y1'], seg['x2'], seg['y2'],
                        other['x1'], other['y1'], other['x2'], other['y2'])
                        <= seg['width'] / 2.0 + other['width'] / 2.0 + _CONTACT_EPS):
                    uf.union(seg['a'], other['a'])

        # Phase 2: a pad or via joins every track piece its copper touches.
        pv_nodes = [node for node in nodes if node.get('kind') in ('pad', 'via')]
        for node in pv_nodes:
            grid = seg_grids.get(node['layer'])
            if not grid:
                continue
            r = node['reach'] + _CONTACT_EPS
            for j in grid.query(node['x'] - r, node['y'] - r, node['x'] + r, node['y'] + r):
                seg = net_segs[j]
                if segment_to_pad_distance(seg, node['shape']) <= seg['width'] / 2.0 + _CONTACT_EPS:
                    uf.union(node['key'], seg['a'])

        # A via whose copper overlaps a pad (via in pad) joins it directly.
        pad_grids: dict[str, _CellIndex] = {}
        for i, node in enumerate(pv_nodes):
            if node['kind'] == 'pad':
                r = node['reach']
                pad_grids.setdefault(node['layer'], _CellIndex()).add_box(
                    i, node['x'] - r, node['y'] - r, node['x'] + r, node['y'] + r)
        for via in pv_nodes:
            grid = pad_grids.get(via['layer'])
            if via['kind'] != 'via' or not grid:
                continue
            x, y, r = via['x'], via['y'], via['reach']
            for i in grid.query(x - r, y - r, x + r, y + r):
                pad = pv_nodes[i]
                point = {'x1': x, 'y1': y, 'x2': x, 'y2': y}
                if segment_to_pad_distance(point, pad['shape']) <= r + _CONTACT_EPS:
                    uf.union(via['key'], pad['key'])

        # Pads whose copper overlaps on a shared layer are one conductor (stacked and
        # castellated pads, compound pads written as several pads of one number).
        for i, node in enumerate(pv_nodes):
            grid = pad_grids.get(node['layer'])
            if node['kind'] != 'pad' or not grid:
                continue
            r = node['reach']
            for j in grid.query(node['x'] - r, node['y'] - r, node['x'] + r, node['y'] + r):
                other = pv_nodes[j]
                if j <= i or uf.find(other['key']) == uf.find(node['key']):
                    continue
                if pads_touch(node['shape'], other['shape']):
                    uf.union(node['key'], other['key'])

        # A filled copper graphic joins the pads, vias and track ends inside it.
        for reg in net_regions.get(net_name, ()):
            if reg['key'] not in all_keys:
                continue
            bx0, by0, bx1, by1 = reg['bbox']
            for node in nodes:
                x, y = node['x'], node['y']
                if (node['layer'] == reg['layer'] and bx0 <= x <= bx1 and by0 <= y <= by1
                        and _point_in_polygon(x, y, reg['pts'])):
                    uf.union(reg['key'], node['key'])

        # Phase 3: Zone fills join the pads, vias, track ends and copper graphics
        # inside the same fill region.
        if zone_fills is not None and zone_fills.has_data:
            probe_kinds = ('pad', 'via', 'track') if net_name in zone_nets else ('pad', 'via')
            for layer in node_layers:
                layer_pv = [node for node in nodes
                            if node['layer'] == layer
                            and node.get('kind') in probe_kinds]
                layer_gr = [g for g in net_graphics.get(net_name, ())
                            if g['layer'] == layer and g['key'] in all_keys]
                if len(layer_pv) + len(layer_gr) < 2:
                    continue
                fill_groups: dict[int, list[str]] = {}
                for node in layer_pv:
                    for fill_id in _node_fill_regions(node, zone_fills, zones, net_name):
                        fill_groups.setdefault(fill_id, []).append(node['key'])
                # A copper graphic overlapping a same-net fill is joined to it.
                for g in layer_gr:
                    hit: set[int] = set()
                    for x, y in g['pts']:
                        for fill_id, _zone_idx in zone_fills.fill_regions_at_point(
                                x, y, layer, zones, net_name=net_name):
                            hit.add(fill_id)
                    for fill_id in sorted(hit):
                        fill_groups.setdefault(fill_id, []).append(g['key'])
                for _fill_id, members in fill_groups.items():
                    for i in range(1, len(members)):
                        uf.union(members[0], members[i])

        # Build island map
        components_map = uf.components()
        island_id_map: dict[str, int] = {}
        island_keys: dict[int, list[str]] = {}
        for idx, (root, members) in enumerate(sorted(components_map.items())):
            for m in members:
                island_id_map[m] = idx
            island_keys[idx] = members

        num_islands = len(components_map)

        # Find gaps
        gaps = []
        if num_islands > 1:
            island_bboxes: dict[int, tuple[float, float, float, float]] = {}
            for island_idx, members in island_keys.items():
                xs = [key_positions[k][0] for k in members if k in key_positions]
                ys = [key_positions[k][1] for k in members if k in key_positions]
                if xs and ys:
                    island_bboxes[island_idx] = (min(xs), min(ys), max(xs), max(ys))

            # Layer of each island's first node (in node order), for the gap's layer.
            first_node: dict[int, int] = {}
            for n_idx, node in enumerate(nodes):
                first_node.setdefault(island_id_map[node['key']], n_idx)

            island_ids_sorted = sorted(island_bboxes.keys())
            for i in range(len(island_ids_sorted)):
                for j in range(i + 1, len(island_ids_sorted)):
                    id_a, id_b = island_ids_sorted[i], island_ids_sorted[j]
                    ba = island_bboxes[id_a]
                    bb = island_bboxes[id_b]
                    gx1 = min(ba[2], bb[2])
                    gy1 = min(ba[3], bb[3])
                    gx2 = max(ba[0], bb[0])
                    gy2 = max(ba[1], bb[1])
                    if gx1 > gx2:
                        gx1, gx2 = gx2, gx1
                    if gy1 > gy2:
                        gy1, gy2 = gy2, gy1
                    layer_guess = nodes[min(first_node[id_a], first_node[id_b])]['layer']
                    gaps.append({
                        'layer': layer_guess,
                        'bbox': [round(gx1, 2), round(gy1, 2), round(gx2, 2), round(gy2, 2)],
                        'between_islands': [id_a, id_b],
                    })

        # Find disconnected pad pairs
        disconnected = []
        pad_keys = sorted(k for k in report_keys if not k.startswith('via_'))
        if num_islands > 1 and len(pad_keys) > 1:
            island_rep_pads: dict[int, str] = {}
            for pk in pad_keys:
                members = logical_groups.get(pk, [pk])
                island_candidates = [
                    island_id_map[m] for m in members if m in island_id_map
                ]
                if not island_candidates:
                    continue
                isl = max(set(island_candidates), key=island_candidates.count)
                if isl is not None and isl not in island_rep_pads:
                    island_rep_pads[isl] = pk
            rep_list = list(island_rep_pads.values())
            for i in range(len(rep_list)):
                for j in range(i + 1, len(rep_list)):
                    disconnected.append([rep_list[i], rep_list[j]])

        report_components = {}
        for report_key in sorted(report_keys):
            members = logical_groups.get(report_key, [report_key])
            island_candidates = [island_id_map[m] for m in members if m in island_id_map]
            if island_candidates:
                report_components[report_key] = max(
                    set(island_candidates), key=island_candidates.count)

        result[net_name] = {
            'islands': num_islands,
            'components': report_components,
            'gaps': gaps,
            'disconnected_pads': disconnected,
        }

    return result
