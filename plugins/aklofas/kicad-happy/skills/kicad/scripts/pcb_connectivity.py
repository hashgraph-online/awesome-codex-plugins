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
    """Return same-net fill-region ids touching a pad or via."""
    if zone_fills is None or not zone_fills.has_data:
        return set()
    x = node.get('x')
    y = node.get('y')
    layer = node.get('layer', '')
    if x is None or y is None or not layer:
        return set()
    regions: set[int] = set()
    for px, py in _node_probe_points(x, y, node.get('copper_radius', 0.0)):
        for fill_id, _zone_idx in zone_fills.fill_regions_at_point(
                px, py, layer, zones, net_name=net_name):
            regions.add(fill_id)
    return regions


def _bucket_coord(value: float, tolerance: float) -> int:
    """Bucket a coordinate for endpoint clustering."""
    if tolerance <= 0:
        tolerance = 0.05
    return int(round(value / tolerance))


def _dist_point_to_segment(px: float, py: float,
                           x1: float, y1: float,
                           x2: float, y2: float) -> float:
    """Euclidean distance from a point to a segment."""
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)


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
    """Expand copper layer specs to the physical layers they actually touch.

    - ``*.Cu`` expands to every copper layer.
    - A via records only its two endpoint layers (e.g. a through via is
      ``["F.Cu", "B.Cu"]``); expand it to every layer between the endpoints,
      inclusive, so it unions through any inner plane it passes through
      (GH issue #24). ``copper_layers`` must be in physical stackup order.
    - A single concrete layer (e.g. an SMD pad) is returned unchanged.
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


class _SpatialGrid:
    """Simple 2D grid index for fast nearest-neighbor lookup."""

    def __init__(self, cell_size: float = 0.5) -> None:
        self._cell = cell_size
        self._grid: dict[tuple[int, int], list[tuple[str, float, float]]] = {}

    def add(self, key: str, x: float, y: float) -> None:
        cx, cy = int(x / self._cell), int(y / self._cell)
        self._grid.setdefault((cx, cy), []).append((key, x, y))

    def nearest(self, x: float, y: float, tolerance: float) -> str | None:
        """Find nearest key within tolerance. Returns None if nothing close."""
        cx, cy = int(x / self._cell), int(y / self._cell)
        best_key = None
        best_dist = tolerance * tolerance
        r = max(1, int(math.ceil(tolerance / self._cell)))
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                for key, kx, ky in self._grid.get((cx + dx, cy + dy), []):
                    d2 = (kx - x) ** 2 + (ky - y) ** 2
                    if d2 < best_dist:
                        best_dist = d2
                        best_key = key
        return best_key


def build_connectivity_graph(
    footprints: list[dict],
    tracks: dict,
    vias: dict,
    zone_fills,
    zones: list[dict],
    net_id_map: dict[int, str],
) -> dict[str, dict]:
    """Build per-net connectivity graph using union-find.

    Args:
        footprints: PCB footprint list with pads (abs_x, abs_y, net_name).
        tracks: Track dict with 'segments' key.
        vias: Via dict with 'vias' key.
        zone_fills: ZoneFills instance with filled polygon data.
        zones: Zone list matching zone_fills index.
        net_id_map: {net_id: net_name} mapping.

    Returns:
        Dict keyed by net_name with islands, components, gaps, disconnected_pads.
    """
    segments = tracks.get('segments', [])
    via_list = vias.get('vias', [])
    copper_layer_set: set[str] = set()
    for seg in segments:
        layer = seg.get('layer', '')
        if '.Cu' in layer:
            copper_layer_set.add(layer)
    for via in via_list:
        for layer in via.get('layers', []) or []:
            if '.Cu' in layer:
                copper_layer_set.add(layer)
    for zone in zones:
        for layer in zone.get('layers', []) or []:
            if '.Cu' in layer:
                copper_layer_set.add(layer)
    copper_layers = sorted(copper_layer_set, key=_stackup_sort_key) or ['F.Cu', 'B.Cu']

    # Collect all nodes per net
    net_nodes: dict[str, list[dict]] = {}
    net_track_segments: dict[str, list[dict]] = {}

    for fp in footprints:
        ref = fp.get('reference', '')
        pad_instance_counts: dict[str, int] = {}
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
            layers = _expand_copper_layers(pad.get('layers', []), copper_layers)
            width = pad.get('width', 0) or 0
            height = pad.get('height', 0) or 0
            copper_radius = max(width, height) / 2.0 if (width or height) else 0.0
            for layer in layers:
                net_nodes.setdefault(net_name, []).append({
                    'key': pad_key,
                    'report_key': report_key,
                    'x': x,
                    'y': y,
                    'layer': layer,
                    'copper_radius': copper_radius,
                    'kind': 'pad',
                })

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
                'kind': 'via',
            })

    for seg_idx, seg in enumerate(segments):
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
        a_key = f"seg_{seg_idx}:a"
        b_key = f"seg_{seg_idx}:b"
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

        # Compound pads can be represented by multiple copper primitives with
        # the same reference/pad number. They are a single electrical node.
        for members in logical_groups.values():
            for i in range(1, len(members)):
                uf.union(members[0], members[i])

        # Spatial index per layer
        layer_grids: dict[str, _SpatialGrid] = {}
        track_layer_grids: dict[str, _SpatialGrid] = {}
        key_positions: dict[str, tuple[float, float]] = {}
        for node in nodes:
            key = node['key']
            x = node['x']
            y = node['y']
            layer = node['layer']
            grid = layer_grids.setdefault(layer, _SpatialGrid(0.5))
            grid.add(key, x, y)
            if node.get('kind') == 'track':
                track_grid = track_layer_grids.setdefault(layer, _SpatialGrid(0.5))
                track_grid.add(key, x, y)
            key_positions[key] = (x, y)

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
        for seg in net_track_segments.get(net_name, []):
            uf.union(seg['a'], seg['b'])

        # Phase 2: Attach pads and vias to routed copper nearby.
        # Use the spatial grid to find candidate track endpoints instead of
        # iterating all segments — keeps this O(pads × nearby) not O(pads × all).
        # Build a reverse index from track endpoint key → segment dict so we
        # can do distance-to-segment verification on grid hits.
        seg_by_endpoint: dict[str, dict] = {}
        for seg in net_track_segments.get(net_name, []):
            seg_by_endpoint.setdefault(seg['a'], seg)
            seg_by_endpoint.setdefault(seg['b'], seg)

        for node in nodes:
            if node.get('kind') not in ('pad', 'via'):
                continue
            grid = track_layer_grids.get(node['layer'])
            if not grid:
                continue
            tolerance = max(0.5, node.get('copper_radius', 0.0) + 0.25)
            nearby = grid.nearest(node['x'], node['y'], tolerance)
            if nearby and nearby != node['key']:
                # Verify via distance-to-segment if we have the segment data
                seg = seg_by_endpoint.get(nearby)
                if seg and seg['layer'] == node['layer']:
                    clearance = (node.get('copper_radius', 0.0)
                                 + (seg.get('width', 0.0) / 2.0) + 0.12)
                    if _dist_point_to_segment(
                            node['x'], node['y'],
                            seg['x1'], seg['y1'],
                            seg['x2'], seg['y2']) <= clearance:
                        uf.union(node['key'], nearby)
                else:
                    uf.union(node['key'], nearby)

        # Phase 3: Zone fills — only probe pads and vias (track endpoints
        # are already connected via Phase 1).
        if zone_fills is not None and zone_fills.has_data:
            for layer, grid in layer_grids.items():
                layer_pv = [node for node in nodes
                            if node['layer'] == layer
                            and node.get('kind') in ('pad', 'via')]
                if len(layer_pv) < 2:
                    continue
                fill_groups: dict[int, list[str]] = {}
                for node in layer_pv:
                    for fill_id in _node_fill_regions(node, zone_fills, zones, net_name):
                        fill_groups.setdefault(fill_id, []).append(node['key'])
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
                    layer_guess = ''
                    for node in nodes:
                        key = node['key']
                        if key in island_keys.get(id_a, []) or key in island_keys.get(id_b, []):
                            layer_guess = node['layer']
                            break
                    gaps.append({
                        'layer': layer_guess,
                        'bbox': [round(gx1, 2), round(gy1, 2), round(gx2, 2), round(gy2, 2)],
                        'between_islands': [id_a, id_b],
                    })

        # Find disconnected pad pairs
        disconnected = []
        pad_keys = [k for k in report_keys if not k.startswith('via_')]
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
