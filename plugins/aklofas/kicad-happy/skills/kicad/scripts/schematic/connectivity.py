"""Schematic connectivity: bus resolution and the net map.

Verbatim moves from bus_resolver.py and analyze_schematic.py; no behaviour change.
Bus logic replicates KiCad's bus semantics: ordered vector expansion,
group/labeled-group buses (dot-joined members), nested groups, bus_alias
resolution inside groups, and the _{...}/^{...}/~{...} text-markup exclusion.
"""
from __future__ import annotations

import re

from kicad_core.values import COORD_EPSILON
from kicad_core.model import Net


_VECTOR_RE = re.compile(r"^(?P<prefix>[^\[\]{}\s]+)\[(?P<a>\d+)\.\.(?P<b>\d+)\]$")
_GROUP_RE = re.compile(r"^(?P<prefix>[^\[\]{}\s]*)\{(?P<members>[^{}]+)\}$")
_MAX_DEPTH = 4


def expand_bus_name(name, aliases=None, _depth=0):
    """Ordered member expansion for a KiCad bus name; None if not a bus."""
    if _depth > _MAX_DEPTH or not isinstance(name, str) or not name:
        return None
    m = _VECTOR_RE.match(name)
    if m:
        a, b = int(m.group("a")), int(m.group("b"))
        step = 1 if b >= a else -1
        return [f"{m.group('prefix')}{i}" for i in range(a, b + step, step)]
    m = _GROUP_RE.match(name)
    if m:
        prefix = m.group("prefix")
        # _{...}/^{...}/~{...} is KiCad subscript/superscript/overline markup.
        # On a plain net name it is not a bus (~{OE}, C_{Out}). But when the
        # wrapped content is itself a bus, KiCad distributes the markup over
        # each expanded member — the overline/subscript stays on every member:
        #   ~{IPL[0..2]}      -> ~{IPL0} ~{IPL1} ~{IPL2}
        #   SIMM_~{CAS[0..3]} -> SIMM_~{CAS0} SIMM_~{CAS1} ...
        if prefix.endswith(("_", "^", "~")):
            markup = prefix[-1]
            base = prefix[:-1]
            inner = expand_bus_name(m.group("members"), aliases, _depth + 1)
            if inner is None:
                return None
            return [f"{base}{markup}{{{mem}}}" for mem in inner]
        members = []
        for tok in m.group("members").split():
            if aliases and tok in aliases:
                sub = []
                for am in aliases[tok]:
                    nested = expand_bus_name(am, aliases, _depth + 1)
                    sub.extend(nested if nested else [am])
            else:
                sub = expand_bus_name(tok, aliases, _depth + 1) or [tok]
            for member in sub:
                members.append(f"{prefix}.{member}" if prefix else member)
        return members or None
    return None


_EPSILON = 0.01


def _point_on_segment(px, py, x1, y1, x2, y2, tol=0.05):
    """Point-on-segment test (bbox + cross-product collinearity).

    Same math as analyze_schematic.py:1408-1424, copied rather than
    imported to keep this module stdlib-only and analyzer-independent.
    """
    if px < min(x1, x2) - tol or px > max(x1, x2) + tol:
        return False
    if py < min(y1, y2) - tol or py > max(y1, y2) + tol:
        return False
    cross = (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)
    seg_len_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
    if seg_len_sq < tol * tol:
        return False
    if abs(cross) / (seg_len_sq ** 0.5) > tol:
        return False
    return True


class BusGraph:
    """Per-sheet bus connectivity graph (GH #25 phase 2).

    Clusters bus wire segments (sharing an endpoint, or T-tapped mid-span)
    via union-find, attaches bus labels (local/hier/pin) to the cluster
    they touch, and resolves bus-entry taps to their wire-side endpoint.
    """

    def __init__(self, sheet, bus_wires, bus_entries, aliases):
        self.sheet = sheet
        self._bus_entries = bus_entries
        self._aliases = aliases or {}
        self._parent = {}
        self._segments = []  # (k1, k2, x1, y1, x2, y2)
        self._attachments = []  # insertion-ordered: {cid, name, ns, role, expansion}
        self._cluster_labels = {}  # cid -> list of attachments, insertion order
        self._cluster_members = {}  # cid -> set of member names

        self.taps = []
        self.ports = []
        self.unresolved = []

        self._build_clusters(bus_wires)

    # -- union-find over rounded endpoint coordinates --

    def _key(self, x, y):
        return (round(x / _EPSILON) * _EPSILON, round(y / _EPSILON) * _EPSILON)

    def _find(self, k):
        while self._parent.get(k, k) != k:
            self._parent[k] = self._parent.get(self._parent[k], self._parent[k])
            k = self._parent[k]
        return k

    def _union(self, a, b):
        ra, rb = self._find(a), self._find(b)
        if ra != rb:
            self._parent[ra] = rb

    def _build_clusters(self, bus_wires):
        for w in bus_wires:
            k1, k2 = self._key(w["x1"], w["y1"]), self._key(w["x2"], w["y2"])
            self._union(k1, k2)
            self._segments.append((k1, k2, w["x1"], w["y1"], w["x2"], w["y2"]))

        # T-taps: an endpoint landing mid-span on another segment joins
        # that segment's cluster (electrically continuous, KiCad-style).
        for i, (k1, k2, x1, y1, x2, y2) in enumerate(self._segments):
            for ex, ey, ek in ((x1, y1, k1), (x2, y2, k2)):
                for j, (ok1, _ok2, ox1, oy1, ox2, oy2) in enumerate(self._segments):
                    if j == i:
                        continue
                    if _point_on_segment(ex, ey, ox1, oy1, ox2, oy2):
                        self._union(ek, ok1)

    def _segment_touched(self, x, y):
        """Anchor key of the first bus segment (x,y) lies on, or None."""
        for k1, _k2, x1, y1, x2, y2 in self._segments:
            if _point_on_segment(x, y, x1, y1, x2, y2):
                return k1
        return None

    def cluster_at(self, x, y):
        anchor = self._segment_touched(x, y)
        if anchor is None:
            anchor = self._key(x, y)
        return self._find(anchor)

    def add_bus_label(self, name, x, y, *, ns="", role="local"):
        anchor = self._segment_touched(x, y)
        if anchor is None:
            return False
        expansion = expand_bus_name(name, self._aliases)
        if expansion is None:
            return False
        self._attachments.append({
            "cid": self._find(anchor), "name": name, "ns": ns,
            "role": role, "expansion": expansion,
        })
        return True

    def finalize(self):
        for att in self._attachments:
            cid = att["cid"]
            self._cluster_labels.setdefault(cid, []).append(att)
            self._cluster_members.setdefault(cid, set()).update(att["expansion"])
            if att["role"] in ("pin", "hier"):
                self.ports.append({
                    "role": att["role"], "cluster": cid, "ns": att["ns"],
                    "name": att["name"], "members": list(att["expansion"]),
                })

        for entry in self._bus_entries:
            x, y = entry["x"], entry["y"]
            tx, ty = x + entry["dx"], y + entry["dy"]
            bus_anchor = self._segment_touched(x, y)
            tap_anchor = self._segment_touched(tx, ty)
            if bus_anchor is not None and tap_anchor is None:
                self.taps.append({"cluster": self._find(bus_anchor), "x": tx, "y": ty})
            elif tap_anchor is not None and bus_anchor is None:
                self.taps.append({"cluster": self._find(tap_anchor), "x": x, "y": y})
            elif bus_anchor is not None and tap_anchor is not None:
                self.note_unresolved("entry_both_ends_on_bus")
            else:
                self.note_unresolved("entry_off_bus")

    def cluster_member_set(self, cid):
        return self._cluster_members.get(cid)

    def cluster_ordered(self, cid, width):
        # The cluster's own member naming comes from a local bus label if it
        # has one, else from a hierarchical bus label — both name the local
        # wire, so a co-clustered sheet pin maps positionally to them. A sheet
        # PIN never participates: it carries the FAR-side (child's) member
        # names, which map positionally, not the local ordering. Local wins
        # over hier so a local relabel (e.g. m68k's SIMM_~{CAS[0..3]} over a
        # ~{CAS[0..3]} pin) still governs; hier is the fallback that lets a
        # root/pass-through bus label (openmd's {PHASES} feeding OUT{PHASES}
        # and V{PHASES} pins) canonicalize the cluster.
        atts = self._cluster_labels.get(cid, [])
        for role in ("local", "hier"):
            matches = [att["expansion"] for att in atts
                       if att["role"] == role and len(att["expansion"]) == width]
            # Ambiguity is two DIFFERENT expansions of the same width — the same
            # bus labeled twice along one wire (readability) is not ambiguous.
            distinct = {tuple(m) for m in matches}
            if len(distinct) == 1:
                return list(matches[0])
            if len(distinct) > 1:
                self.note_unresolved("ambiguous_bus_width", str(width))
                return None
        return None

    def note_unresolved(self, reason, name=None):
        # cluster_ordered() is called once per co-clustered sheet pin, so an
        # ambiguous width is re-reported for every pin sharing the cluster —
        # collapse to one note per distinct (reason, name) pair.
        entry = {"reason": reason, "name": name}
        if entry not in self.unresolved:
            self.unresolved.append(entry)


def match_ports(pin_ports, hier_ports, unresolved):
    """Pair parent-side sheet-pin ports with child-side hier-label ports.

    Indexes hier_ports by (ns, name) (iterating hier_ports in list order —
    if two hier ports share a key the sheet is malformed: first one wins
    the index slot and a note is appended to unresolved). For each pin port
    in pin_ports (in list order) finds its counterpart by the same key and
    pairs member slots positionally: parent = port["parent_ordered"] or
    port["members"] (an anonymous parent cluster falls back to the pin's
    own expansion — spec rule 3/5); child = hier port's "members". A width
    mismatch appends a note to unresolved and contributes no pairs for that
    port (no partial mapping). A missing counterpart in either direction
    (a pin port with no hier port at that key, or vice versa) also appends
    a note; the hier-side pass runs after the pin-side pass, iterating
    hier_ports in list order. Returns
    [((pin_sheet, pin_cluster, parent_member),
      (hier_sheet, hier_cluster, child_member)), ...].

    "parent_ordered" is not computed here — the caller (Task 10) computes
    it via cluster_ordered(cluster, len(members)) on the parent graph and
    stashes it on the port dict before calling this function.
    """
    hier_by_key = {}
    for hier in hier_ports:
        key = (hier["ns"], hier["name"])
        if key in hier_by_key:
            unresolved.append({
                "reason": "duplicate_hier_port",
                "name": hier["name"],
            })
            continue
        hier_by_key[key] = hier

    pin_keys = {(pin["ns"], pin["name"]) for pin in pin_ports}

    pairs = []
    for pin in pin_ports:
        key = (pin["ns"], pin["name"])
        hier = hier_by_key.get(key)
        if hier is None:
            unresolved.append({
                "reason": "no_hier_counterpart_for_pin",
                "name": pin["name"],
            })
            continue
        parent = pin["parent_ordered"] or pin["members"]
        child = hier["members"]
        if len(parent) != len(child):
            unresolved.append({
                "reason": "bus_width_mismatch",
                "name": pin["name"],
            })
            continue
        for i in range(len(parent)):
            pairs.append((
                (pin["sheet"], pin["cluster"], parent[i]),
                (hier["sheet"], hier["cluster"], child[i]),
            ))

    for hier in hier_ports:
        key = (hier["ns"], hier["name"])
        if key not in pin_keys:
            unresolved.append({
                "reason": "no_pin_counterpart_for_hier",
                "name": hier["name"],
            })

    return pairs


def build_net_map(components: list[dict], wires: list[dict], labels: list[dict],
                  power_symbols: list[dict], junctions: list[dict],
                  no_connects: list[dict] | None = None,
                  sheet_names: list[str] | None = None,
                  bus_elements: dict | None = None) -> dict[str, Net]:
    """Build a connectivity map using union-find on coordinates.

    Groups all electrically connected points into nets, then names them
    from labels and power symbols.

    When ``bus_elements`` carries bus wires (GH #25), a per-sheet bus pass
    resolves hierarchical bus connectivity: bus-name labels are consumed out
    of the ordinary label handling, and their members are joined by name,
    by bus entry, and — across sheet pins — positionally to the child sheet's
    hier-label bus. On ``bus_elements=None`` or a board with no bus wires the
    pass is inert and the output is byte-identical to the pre-#25 map.
    """
    EPSILON = COORD_EPSILON

    # Collect all electrical points
    # Each point: (sheet, x, y, source_info)
    # The sheet index keeps each sheet's coordinate space separate so that
    # wires on different sheets at the same (x,y) don't falsely merge.
    parent = {}
    point_info = {}  # key -> list of info dicts

    def key(x, y, sheet=0):
        return (sheet, round(x / EPSILON) * EPSILON, round(y / EPSILON) * EPSILON)

    def find(p):
        while parent.get(p, p) != p:
            parent[p] = parent.get(parent[p], parent[p])
            p = parent[p]
        return p

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    def add_point(x, y, info, sheet=0):
        k = key(x, y, sheet)
        if k not in parent:
            parent[k] = k
        point_info.setdefault(k, []).append(info)
        return k

    # Add component pins. PWR_FLAG is an ERC marker, not a real connection —
    # still register its position so the net gets a has_pwr_flag annotation.
    for comp in components:
        is_pwr_flag = comp.get("value") == "PWR_FLAG" or comp.get("type") == "power_flag"
        sheet = comp.get("_sheet", 0)
        for pin in comp.get("pins", []):
            if is_pwr_flag:
                add_point(pin["x"], pin["y"], {
                    "source": "pwr_flag",
                    "component": comp["reference"],
                }, sheet)
            else:
                add_point(pin["x"], pin["y"], {
                    "source": "pin",
                    "component": comp["reference"],
                    "pin_number": pin["number"],
                    "pin_name": pin["name"],
                    "pin_type": pin["type"],
                }, sheet)

    # Add wire endpoints and union them.
    # Also build a list of wire segments so we can detect points that land
    # mid-wire (labels, pins, junctions, power symbols placed on a wire
    # between its endpoints).
    wire_segments = []  # list of (k1, k2, x1, y1, x2, y2, sheet)
    # Spatial grid index for fast wire segment lookup — avoids O(W*P) scans.
    # Grid cell size of 5mm captures typical KiCad schematic wire lengths.
    _WIRE_GRID_SIZE = 5.0
    wire_grid: dict[tuple, list[int]] = {}  # (sheet, gx, gy) -> [index into wire_segments]

    for wire in wires:
        sheet = wire.get("_sheet", 0)
        k1 = add_point(wire["x1"], wire["y1"], {"source": "wire"}, sheet)
        k2 = add_point(wire["x2"], wire["y2"], {"source": "wire"}, sheet)
        union(k1, k2)
        idx = len(wire_segments)
        wire_segments.append((k1, k2, wire["x1"], wire["y1"], wire["x2"], wire["y2"], sheet))
        # Index this segment in all grid cells its bounding box overlaps
        min_x, max_x = min(wire["x1"], wire["x2"]), max(wire["x1"], wire["x2"])
        min_y, max_y = min(wire["y1"], wire["y2"]), max(wire["y1"], wire["y2"])
        gx0 = int(min_x // _WIRE_GRID_SIZE)
        gx1 = int(max_x // _WIRE_GRID_SIZE)
        gy0 = int(min_y // _WIRE_GRID_SIZE)
        gy1 = int(max_y // _WIRE_GRID_SIZE)
        for gx in range(gx0, gx1 + 1):
            for gy in range(gy0, gy1 + 1):
                wire_grid.setdefault((sheet, gx, gy), []).append(idx)

    def point_on_segment(px, py, x1, y1, x2, y2):
        """Check if point (px,py) lies on the wire segment (x1,y1)-(x2,y2)."""
        # Quick bounding box check with tolerance
        tol = 0.05
        if px < min(x1, x2) - tol or px > max(x1, x2) + tol:
            return False
        if py < min(y1, y2) - tol or py > max(y1, y2) + tol:
            return False
        # Cross product to check collinearity
        cross = (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)
        seg_len_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
        if seg_len_sq < tol * tol:
            return False
        # Distance from point to line, squared
        if abs(cross) / (seg_len_sq ** 0.5) > tol:
            return False
        return True

    def union_with_overlapping_wires(k, px, py, sheet=0):
        """Union point k with every wire segment it lies on (same sheet only)."""
        gx = int(px // _WIRE_GRID_SIZE)
        gy = int(py // _WIRE_GRID_SIZE)
        candidates = wire_grid.get((sheet, gx, gy), ())
        for idx in candidates:
            wk1, wk2, wx1, wy1, wx2, wy2, ws = wire_segments[idx]
            if point_on_segment(px, py, wx1, wy1, wx2, wy2):
                union(k, wk1)
                # KH-360: no early return — a junction/label at a crossing
                # must join every wire under it, matching KiCad's
                # connection_graph (all coincident lines are inserted).

    # Bus pass classification (GH #25). Group bus wires/entries per sheet,
    # build a BusGraph for every sheet that carries bus wire, and attach each
    # bus-name label to its cluster. Consumed bus-name labels are removed from
    # ordinary label handling (they create no coordinate point, no label_keys
    # entry, no net_labels) — this drops the 0-pin bus-name phantoms and the
    # bare-name parent↔child union, both of which the bus pass replaces.
    bus_active = bool(bus_elements and bus_elements.get("bus_wires"))
    bus_graphs: dict[int, BusGraph] = {}
    bus_aliases: dict = {}
    bus_label_idx: set[int] = set()
    bus_named_labels: list[tuple] = []  # (sheet, bare, x, y) for local/hier labels
    if bus_active:
        bus_aliases = {a["name"]: a["members"]
                       for a in bus_elements.get("bus_aliases", [])}
        wires_by_sheet: dict[int, list] = {}
        entries_by_sheet: dict[int, list] = {}
        for bw in bus_elements.get("bus_wires", []):
            wires_by_sheet.setdefault(bw.get("_sheet", 0), []).append(bw)
        for be_ in bus_elements.get("bus_entries", []):
            entries_by_sheet.setdefault(be_.get("_sheet", 0), []).append(be_)
        for s in wires_by_sheet:
            bus_graphs[s] = BusGraph(s, wires_by_sheet[s],
                                     entries_by_sheet.get(s, []), bus_aliases)
        for idx, lbl in enumerate(labels):
            s = lbl.get("_sheet", 0)
            g = bus_graphs.get(s)
            if g is None:
                continue
            raw_name = lbl["name"]
            if isinstance(raw_name, list):
                raw_name = str(raw_name[0]) if raw_name else ""
            bare = lbl.get("_bare_name", raw_name)
            if expand_bus_name(bare, bus_aliases) is None:
                continue
            role = ("pin" if lbl.get("_is_sheet_pin")
                    else ("hier" if lbl["type"] == "hierarchical_label"
                          else "local"))
            if g.add_bus_label(bare, lbl["x"], lbl["y"],
                               ns=lbl.get("_hier_ns", ""), role=role):
                bus_label_idx.add(idx)
                if role in ("local", "hier"):
                    bus_named_labels.append((s, bare, lbl["x"], lbl["y"]))
            else:
                g.note_unresolved("label_not_on_bus_wire", bare)
        for g in bus_graphs.values():
            g.finalize()

    # Add labels — in KiCad, labels can be placed anywhere on a wire,
    # not just at endpoints, so we must check for mid-wire placement.
    label_keys: dict[str, list] = {}  # label_name -> list of coordinate keys
    for idx, lbl in enumerate(labels):
        if idx in bus_label_idx:
            continue
        sheet = lbl.get("_sheet", 0)
        # KH-078: Defensive coercion — malformed labels can have list names
        lbl_name = lbl["name"]
        if isinstance(lbl_name, list):
            lbl_name = str(lbl_name[0]) if lbl_name else ""
        k = add_point(lbl["x"], lbl["y"], {
            "source": "label",
            "name": lbl_name,
            "label_type": lbl["type"],
        }, sheet)
        # Only global labels and power symbols connect across sheets.
        # Local labels only connect within the same sheet (handled by wire union).
        if lbl["type"] == "global_label":
            label_keys.setdefault(lbl_name, []).append(k)
        elif lbl["type"] == "hierarchical_label":
            # Cross-sheet by (namespaced) name — the pre-existing hier union.
            label_keys.setdefault(lbl_name, []).append(k)
            # AND same-name LOCAL labels on this sheet: KiCad joins a real
            # hierarchical label to same-name local labels within its own sheet
            # (openmd's root V_{ANA}, where a hier V_{ANA} and a local V_{ANA}
            # name one net). Sheet PINS are excluded: a sheet pin's bare name is
            # the child's, and several pins for different child instances share
            # one bare name on one parent sheet — they must stay per-instance
            # (mapped through the hierarchy), never merged by same-sheet name.
            if not lbl.get("_is_sheet_pin"):
                bare = lbl.get("_bare_name", lbl_name)
                label_keys.setdefault((bare, sheet), []).append(k)
        else:
            # Local labels: union same-name labels within this sheet only
            local_key = (lbl_name, sheet)
            label_keys.setdefault(local_key, []).append(k)
        union_with_overlapping_wires(k, lbl["x"], lbl["y"], sheet)

    # Add power symbols — compute actual pin position from lib symbol.
    # PWR_FLAG is a DRC-only marker (tells ERC a net has a power source).
    # It doesn't create real connectivity, so exclude it entirely.
    for ps in power_symbols:
        if ps["net_name"] == "PWR_FLAG":
            continue
        sheet = ps.get("_sheet", 0)
        k = add_point(ps["x"], ps["y"], {
            "source": "power_symbol",
            "net_name": ps["net_name"],
            "power_scope": ps.get("_power_scope", "global"),
        }, sheet)
        # Global power symbols connect across all sheets; local power symbols
        # only connect within the same sheet (isolated power domains).
        if ps.get("_power_scope") == "local":
            local_key = (ps["net_name"], sheet)
            label_keys.setdefault(local_key, []).append(k)
        else:
            label_keys.setdefault(ps["net_name"], []).append(k)
        union_with_overlapping_wires(k, ps["x"], ps["y"], sheet)

    # Legacy hidden power-in pins: in KiCad 4/5, ICs could have invisible
    # power-in pins (VCC, GND) that create implicit global net connections
    # by pin name.  These pins have no wires attached — they connect solely
    # by their name matching other hidden power pins or power symbols.
    for comp in components:
        if comp.get("type") == "power_symbol":
            continue
        sheet = comp.get("_sheet", 0)
        for pin in comp.get("pins", []):
            if pin.get("hidden") and pin["type"] == "power_in" and pin["name"]:
                k = key(pin["x"], pin["y"], sheet)
                label_keys.setdefault(pin["name"], []).append(k)

    # Union global/hierarchical labels and power symbols with the same name.
    # This is what connects nets across different parts of the schematic.
    for lbl_name, keys in label_keys.items():
        for j in range(1, len(keys)):
            union(keys[0], keys[j])

    # Add junctions — also check mid-wire placement
    for junc in junctions:
        sheet = junc.get("_sheet", 0)
        k = add_point(junc["x"], junc["y"], {"source": "junction"}, sheet)
        union_with_overlapping_wires(k, junc["x"], junc["y"], sheet)

    # Add no-connect markers to the union-find so NC'd pins are absorbed into
    # the same group and the resulting net gets tagged as intentional NC.
    # Without this, NC'd pins that have no wire create isolated __unnamed_N nets
    # that look like unfinished connections to downstream analysis.
    if no_connects:
        for nc in no_connects:
            sheet = nc.get("_sheet", 0)
            # A no-connect marker is an ERC annotation, never a connection.
            # add_point() already shares the coordinate key with a pin or wire
            # endpoint on the same point, which is all the absorption and NC
            # tagging described above needs. Unioning the marker with every
            # *overlapping* wire also caught wires passing mid-span beneath it,
            # which KiCad does not connect, dragging the NC'd pin into that
            # wire's net — a false-positive connection.
            add_point(nc["x"], nc["y"], {"source": "no_connect"}, sheet)

    # Bus pass unions (GH #25). A bus member is joined into the coordinate
    # union-find through a synthetic slot key ("bus", sheet, cluster, member).
    # Three mechanisms feed the same slot:
    #   (A) by name — a wire labelled with a member name (Increment0) IS that
    #       member, bus entry or not (KiCad names bus members after labels);
    #   (B) by bus entry — an entry-tapped wire, resolved by intersecting the
    #       tapped net's local labels with the cluster member set (covers
    #       unlabelled tapped wires that (A) can't reach);
    #   (C) across a sheet pin — the parent's pin-port members map positionally
    #       onto the matching child hier-port members.
    if bus_active and bus_graphs:
        def bus_slot(sheet, cid, member):
            sk = ("bus", sheet, cid, member)
            if sk not in parent:
                parent[sk] = sk
            return sk

        # (A) Name-based member joining for local/hier bus labels. Sheet-pin
        # ("pin") labels are excluded: their members name the child's nets,
        # not the parent's local nets, so they map only positionally in (C).
        # Only the same-sheet LOCAL key `(member, s)` is accepted — a
        # local/hier bus member is local-scoped, so it must not fuse with a
        # coincidentally same-named GLOBAL label (keyed bare) elsewhere; KiCad
        # keeps local/hier bus scope separate from the global net space.
        #
        # Same-sheet bus-name joining (member_rep): a local or hierarchical
        # bus label has sheet scope — KiCad connects same-name local/hier
        # labels within a sheet. Two physically-separate bus clusters on one
        # sheet that carry labels sharing a member name are therefore one net
        # for that member (the member-level analogue of the ordinary same-name
        # local-label union that the bus pass suppressed for bus labels). This
        # is what chains a pass-through sheet's parent-side cluster to its
        # child-side sheet-pin clusters (e.g. m68k's Memory routing D[0..31]
        # down to Cache/SIMM/CDC). Sheet pins are excluded (not in
        # bus_named_labels), so a pin without a co-located local label does not
        # name-join — it connects only by wire and the positional match (C).
        member_rep: dict[tuple, tuple] = {}  # (sheet, member) -> a member slot
        for s, bare, lx, ly in bus_named_labels:
            g = bus_graphs[s]
            cid = g.cluster_at(lx, ly)
            expansion = expand_bus_name(bare, bus_aliases)
            if not expansion:
                continue
            for member in expansion:
                slot = bus_slot(s, cid, member)
                lk = label_keys.get((member, s))
                if lk:
                    union(slot, lk[0])
                rep = member_rep.get((s, member))
                if rep is None:
                    member_rep[(s, member)] = slot
                else:
                    union(rep, slot)

        # (B1) Register every bus-entry tap point and union it with the wires
        # it lands on. This must precede the root_names sweep so a tapped
        # wire's labels are visible on the tap's net.
        tap_points = []  # (sheet, tap_key, tap)
        for s in sorted(bus_graphs):
            g = bus_graphs[s]
            for tap in g.taps:
                tk = add_point(tap["x"], tap["y"], {"source": "bus_tap"}, s)
                union_with_overlapping_wires(tk, tap["x"], tap["y"], s)
                tap_points.append((s, tk, tap))

        # Local label names present on each union group, for tap member ID.
        root_names: dict = {}
        for pk, infos in point_info.items():
            for i in infos:
                if (i["source"] == "label"
                        and (i.get("label_type") or "label")
                        in ("label", "directive_label") and i.get("name")):
                    root_names.setdefault(find(pk), set()).add(i["name"])

        # (B2) Resolve each tap to its member slot(s) (after the root_names
        # sweep). Normally the tapped wire carries exactly one member label.
        # When several member wires of one bus are shorted together (e.g. all
        # tied to GND), the tapped net carries every one of those labels — KiCad
        # collapses those members to a single net, so we union the tap with each
        # matched member slot (sorted for determinism). A tap whose net carries
        # no label at all is genuinely unlabeled; a tap whose net DOES carry a
        # label that just isn't one of this bus's member names is a distinct
        # failure (the label misnamed/mistargeted, not absent) — kept separate
        # so the reason says what was actually unresolved.
        for s, tk, tap in tap_points:
            g = bus_graphs[s]
            names = root_names.get(find(tk), set())
            mset = g.cluster_member_set(tap["cluster"])
            cand = (names & mset) if mset is not None else set(names)
            if cand:
                for member in sorted(cand):
                    union(tk, bus_slot(s, tap["cluster"], member))
            elif names:
                g.note_unresolved("entry_tap_name_not_in_bus", sorted(names)[0])
            else:
                g.note_unresolved("unlabeled_entry_tap", None)

        # (C) Positional sheet-pin port matching.
        pin_ports, hier_ports = [], []
        for s in sorted(bus_graphs):
            g = bus_graphs[s]
            for p in g.ports:
                p = dict(p, sheet=s)
                if p["role"] == "pin":
                    p["parent_ordered"] = g.cluster_ordered(
                        p["cluster"], len(p["members"]))
                    pin_ports.append(p)
                else:
                    hier_ports.append(p)

        # (C0) Co-clustered sheet pins are one physical bus. When a bus is
        # routed straight from one sub-sheet symbol's pin to another's on a
        # single cluster (no relabeling local label to canonicalize it), the
        # two differently-named pins are the same wire, so bit i of each is one
        # net. Join their member slots positionally, using the SAME effective
        # ordering (C) uses — the cluster's local-label ordering if present,
        # else the pin's own members — so this stays consistent with the
        # pin↔hier mapping below. With a local label all pins already share
        # that ordering, so this is a no-op there; it only bridges the
        # no-local-label case (e.g. m68k's Bus sheet routing PEP_AD↔AD,
        # ISA_D↔D, ATA_D↔D straight through to the peripheral sub-sheets).
        pins_by_cluster: dict[tuple, list] = {}
        for p in pin_ports:
            pins_by_cluster.setdefault((p["sheet"], p["cluster"]), []).append(p)
        for grp in pins_by_cluster.values():
            if len(grp) < 2:
                continue
            ref = grp[0]["parent_ordered"] or grp[0]["members"]
            for other in grp[1:]:
                eff = other["parent_ordered"] or other["members"]
                if len(eff) != len(ref):
                    continue
                for i in range(len(ref)):
                    union(bus_slot(grp[0]["sheet"], grp[0]["cluster"], ref[i]),
                          bus_slot(other["sheet"], other["cluster"], eff[i]))

        all_unresolved: list = []
        for (ps, pc, pm), (cs, cc, cm) in match_ports(
                pin_ports, hier_ports, all_unresolved):
            union(bus_slot(ps, pc, pm), bus_slot(cs, cc, cm))

        bus_elements["_unresolved"] = all_unresolved + [
            u for s in sorted(bus_graphs) for u in bus_graphs[s].unresolved]

    # Build net groups
    net_groups: dict[tuple, list[tuple]] = {}
    for k in parent:
        root_k = find(k)
        net_groups.setdefault(root_k, []).append(k)

    # Name the nets
    staged = []
    net_id = 0
    for root_k, members in net_groups.items():
        # Collect all info for this net
        all_info = []
        for m in members:
            all_info.extend(point_info.get(m, []))

        # Find net name using KiCad's priority:
        # global_label > power_symbol > hierarchical_label > local label > pin
        _NET_NAME_PRIORITY = {
            "global_label": 0,
            "power_symbol": 1,
            "hierarchical_label": 2,
            "label": 3,
            "directive_label": 4,
        }

        # Accumulate every global / hierarchical / local label attached to
        # this net (LB-001 reads this; also useful for report annotations).
        # Dedup by (name, label_type).
        # best = (priority, tiebreak_sheet, seq, name, is_local, sheet)
        # tiebreak_sheet is -1 for global-scope sources so, at equal priority,
        # a global name beats a local one and a lower (parent) sheet beats a
        # higher one — KiCad names a resolved net after the parent member
        # label. seq preserves first-seen order at full ties.
        best = None
        seq = 0
        net_labels_seen: set[tuple[str, str]] = set()
        net_labels: list[dict] = []
        for m in members:
            m_sheet = m[0]
            for info in point_info.get(m, []):
                src = info["source"]
                if src == "power_symbol":
                    p = _NET_NAME_PRIORITY["power_symbol"]
                    cand_name = info["net_name"]
                    is_local = info.get("power_scope") == "local"
                elif src == "label":
                    lbl_name = info.get("name") or ""
                    lbl_type = info.get("label_type") or "label"
                    p = _NET_NAME_PRIORITY.get(lbl_type, 3)
                    cand_name = lbl_name
                    is_local = lbl_type in ("label", "directive_label")
                    key_tuple = (lbl_name, lbl_type)
                    if lbl_name and key_tuple not in net_labels_seen:
                        net_labels_seen.add(key_tuple)
                        net_labels.append({"name": lbl_name, "type": lbl_type})
                else:
                    continue
                if cand_name:
                    cand = (p, m_sheet if is_local else -1, seq,
                            cand_name, is_local, m_sheet)
                    if best is None or cand[:3] < best[:3]:
                        best = cand
                seq += 1
        net_name = best[3] if best else None

        # Check if any member of this group is a no-connect marker OR a
        # library-defined NC pin (pin type "no_connect" in the symbol def).
        has_nc_marker = (
            any(i["source"] == "no_connect" for i in all_info)
            or any(i.get("pin_type") in ("no_connect", "unconnected")
                   for i in all_info if i["source"] == "pin")
        )

        has_pwr_flag = any(i["source"] == "pwr_flag" for i in all_info)

        if net_name is None:
            # Only create unnamed nets if they have component pins
            has_pins = any(i["source"] == "pin" for i in all_info)
            if not has_pins:
                continue
            net_name = f"__unnamed_{net_id}"
            net_id += 1

        # Collect pin connections
        pin_connections = []
        for info in all_info:
            if info["source"] == "pin":
                pin_connections.append({
                    "component": info["component"],
                    "pin_number": info["pin_number"],
                    "pin_name": info["pin_name"],
                    "pin_type": info["pin_type"],
                })

        # Keep nets that have pin connections, OR named nets (from labels/power symbols)
        # even without pins — this supports legacy files where pin positions aren't available
        if pin_connections or not net_name.startswith("__unnamed_"):
            staged.append({
                "bare": net_name,
                "is_local": bool(best) and best[4],
                "sheet": best[5] if best else 0,
                "pins": pin_connections,
                "point_count": len([m for m in members if m[0] != "bus"]),
                "no_connect": has_nc_marker,
                "has_pwr_flag": has_pwr_flag,
                "labels": net_labels,
            })

    # KH-359: one entry per union-find group. On bare-name collisions the
    # global-scope group keeps the bare key; local groups get KiCad-style
    # /<sheet>/<name> keys (sheet file stem, #N for repeated instance stems).
    n_sheets = 1 + max((e["sheet"] for e in staged), default=0)
    sheet_labels, _stem_counts = [], {}
    for i in range(n_sheets):
        stem = (sheet_names[i] if sheet_names and i < len(sheet_names)
                else f"sheet{i}")
        _stem_counts[stem] = _stem_counts.get(stem, 0) + 1
        n = _stem_counts[stem]
        sheet_labels.append(stem if n == 1 else f"{stem}#{n}")

    by_bare: dict[str, list[dict]] = {}
    for e in staged:
        by_bare.setdefault(e["bare"], []).append(e)

    nets = {}
    for bare, entries in by_bare.items():
        for e in entries:
            if len(entries) == 1 or not e["is_local"]:
                k = bare
            else:
                k = f"/{sheet_labels[e['sheet']]}/{bare}"
            n = 2
            while k in nets:
                k = f"/{sheet_labels[e['sheet']]}/{bare}#{n}"
                n += 1
            entry = {
                "name": k,
                "pins": e["pins"],
                "point_count": e["point_count"],
                "no_connect": e["no_connect"],
                "has_pwr_flag": e["has_pwr_flag"],
                "labels": e["labels"],
            }
            if k != bare:
                entry["display_name"] = bare
            nets[k] = entry
    return nets


# Internal-only fields the bus pass (GH #25) reads off namespaced hierarchical
# labels. They must never reach the user-facing `labels` output. `_sheet` is
# NOT one of these — it has leaked on every label since before this branch, so
# stripping it would itself change baseline output.
_INTERNAL_LABEL_KEYS = ("_bare_name", "_hier_ns", "_is_sheet_pin")


def _labels_for_output(labels: list[dict]) -> list[dict]:
    """Return a copy of `labels` with the bus-pass internal keys removed."""
    return [{k: v for k, v in lbl.items() if k not in _INTERNAL_LABEL_KEYS}
            for lbl in labels]


def get_net_neighbors(net_info: dict, exclude_ref: str) -> list[dict]:
    """Get all components on a net except the given reference, with their details."""
    neighbors = []
    for p in net_info["pins"]:
        if p["component"] != exclude_ref and not p["component"].startswith("#"):
            neighbors.append({
                "component": p["component"],
                "pin_number": p["pin_number"],
                "pin_name": p["pin_name"],
                "pin_type": p["pin_type"],
            })
    return neighbors
