"""Schematic connectivity: bus resolution and the net map.

Bus logic replicates KiCad's bus semantics: ordered vector expansion,
group/labeled-group buses (dot-joined members), nested groups, bus_alias
resolution inside groups, and the _{...}/^{...}/~{...} text-markup exclusion.
"""
from __future__ import annotations

from kicad_core.coords import segment_hit_iu, to_iu
from kicad_core.diagnostics import record
from kicad_core.model import Net
from kicad_core.sexp import net_name_escape, unescape_string


_MAX_DEPTH = 4
# KiCad text markup: a brace after one of these is formatting, not a bus group.
_MARKUP = ("_", "^", "~")


def _parse_bus_vector(name):
    """(prefix, suffix, ascending indices) for a KiCad vector bus name, else None.

    Port of NET_SETTINGS::ParseBusVector: a descending range is read ascending,
    ``[n..n]`` is not a bus, the suffix may only be ``+ - P N``, and markup may sit
    in the prefix (``R_{C}[0..1]``), wrap the name (``~{BE[0..3]}``) or decorate
    the range (``D_{[1..2]}``).
    """
    prefix, nest, wraps, i, n = "", 0, False, 0, len(name)
    while True:
        if i >= n:
            return None
        ch = name[i]
        if ch == "{":
            if i > 0 and name[i - 1] in _MARKUP:
                nest += 1
                prefix += ch
                i += 1
                continue
            return None
        if ch == "}":
            nest -= 1
            prefix += ch
            i += 1
            continue
        if ch == "\\" and i + 1 < n and name[i + 1] == " ":
            prefix += " "
            i += 2
            continue
        if ch in " ]":
            return None
        if ch == "[":
            if nest > 0:
                f = prefix.rfind("{")
                if f > 0 and prefix[f - 1] in _MARKUP:
                    if f == len(prefix) - 1:
                        prefix = prefix[:f - 1]
                    else:
                        wraps = True
            break
        prefix += ch
        i += 1
    j = name.find("..", i + 1)
    if j < 0 or not (name[i + 1:j].isdigit() or name[i + 1:j] == ""):
        return None
    k = name.find("]", j + 2)
    if k < 0 or not (name[j + 2:k].isdigit() or name[j + 2:k] == ""):
        return None
    begin, end = int(name[i + 1:j] or 0), int(name[j + 2:k] or 0)
    suffix = ""
    for ch in name[k + 1:]:
        if ch == "}":
            nest -= 1
            if wraps:
                suffix += ch
        elif ch in "+-PN":
            suffix += ch
        else:
            return None
    if nest != 0 or begin == end:
        return None
    return prefix, suffix, list(range(min(begin, end), max(begin, end) + 1))


def _parse_bus_group(name):
    """(prefix, [member tokens]) for a KiCad group bus name, else None.

    Port of NET_SETTINGS::ParseBusGroup: members are separated by spaces or
    commas, keep their markup (``~{OE}``), and text after the closing brace is
    ignored.
    """
    prefix, nest, i, n = "", 0, 0, len(name)
    while i < n:
        ch = name[i]
        if ch == "{":
            if i > 0 and name[i - 1] in _MARKUP:
                nest += 1
                prefix += ch
                i += 1
                continue
            break
        if ch == "}":
            nest -= 1
            prefix += ch
            i += 1
            continue
        if ch == "\\" and i + 1 < n and name[i + 1] == " ":
            prefix += " "
            i += 2
            continue
        if ch in " []":
            return None
        prefix += ch
        i += 1
    if nest != 0 or i + 1 >= n:
        return None
    i += 1
    members, tok = [], ""
    while i < n:
        ch = name[i]
        if ch == "{":
            if name[i - 1] in _MARKUP:
                nest += 1
                tok += ch
                i += 1
                continue
            return None
        if ch == "}":
            if nest:
                nest -= 1
                tok += ch
                i += 1
                continue
            if tok:
                members.append(tok)
            return prefix, members
        if ch == "\\" and i + 1 < n and name[i + 1] == " ":
            tok += " "
            i += 2
            continue
        if ch in " ,":
            if tok:
                members.append(tok)
            tok = ""
            i += 1
            continue
        tok += ch
        i += 1
    return None


def bus_kind(name):
    """'vector', 'group' or None, as KiCad classifies a label name."""
    if not isinstance(name, str) or not name:
        return None
    # KiCad parses a label as a bus after UnescapeString (sch_connection.cpp).
    name = unescape_string(name)
    if _parse_bus_vector(name):
        return "vector"
    group = _parse_bus_group(name)
    return "group" if group and group[1] else None


def expand_bus_name(name, aliases=None, _depth=0):
    """Ordered member expansion for a KiCad bus name; None if not a bus.

    Vector members come in ascending index order; group members in written
    order, ``<prefix>.<member>`` when the group has a prefix. A group member
    that names a bus alias expands to the alias's members.
    """
    if _depth > _MAX_DEPTH or not isinstance(name, str) or not name:
        return None
    name = unescape_string(name)
    vector = _parse_bus_vector(name)
    if vector:
        prefix, suffix, indices = vector
        return [f"{prefix}{i}{suffix}" for i in indices]
    group = _parse_bus_group(name)
    if not group:
        return None
    prefix, tokens = group
    members = []
    for tok in tokens:
        if aliases and tok in aliases:
            sub = []
            for am in aliases[tok]:
                nested = expand_bus_name(am, aliases, _depth + 1)
                sub.extend(nested if nested else [am])
        else:
            # A plain group member is escaped as a net name; the group prefix and a nested
            # vector's members stay decoded, so kicad-cli joins neither to an escaped tap label.
            sub = expand_bus_name(tok, aliases, _depth + 1) or [net_name_escape(tok)]
        for member in sub:
            members.append(f"{prefix}.{member}" if prefix else member)
    return members or None


def _local_member_names(name, members):
    """A group bus's members without the group prefix (KiCad LocalName)."""
    group = _parse_bus_group(unescape_string(name)) if isinstance(name, str) else None
    if not group or not group[0]:
        return list(members)
    pre = group[0] + "."
    return [m[len(pre):] if m.startswith(pre) else m for m in members]


def pair_bus_members(a_name, a_members, b_name, b_members):
    """Member pairs KiCad joins when bus ``a`` reaches bus ``b`` across a sheet pin.

    Two vectors pair by position up to the narrower one; two groups pair by
    member name without the group prefix; mixed kinds pair by position only at
    equal width. Returns ``(pairs, reason)``; ``reason`` is set only when
    nothing pairs.
    """
    ka, kb = bus_kind(a_name), bus_kind(b_name)
    if ka == kb == "group":
        local_a = _local_member_names(a_name, a_members)
        index_b = {m: i for i, m in enumerate(_local_member_names(b_name, b_members))}
        pairs = [(a_members[i], b_members[index_b[m]])
                 for i, m in enumerate(local_a) if m in index_b]
        return pairs, (None if pairs else "bus_member_mismatch")
    if ka == kb == "vector":
        width = min(len(a_members), len(b_members))
        return list(zip(a_members[:width], b_members[:width])), None
    if len(a_members) != len(b_members):
        return [], "bus_width_mismatch"
    return list(zip(a_members, b_members)), None


_EPSILON = 0.01


def _point_on_segment(px, py, x1, y1, x2, y2, tol=0.05):
    """Point-on-segment test in mm with a 0.05 mm tolerance (bbox + distance to the line).

    Bus clusters and bus-entry taps keep this tolerance; build_net_map also uses it to
    report points that are near a wire without lying on it.
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

    def __init__(self, sheet, bus_wires, bus_entries, aliases, junctions=()):
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
        self.last_label = None  # name of the label cluster_ordered() last used

        self._build_clusters(bus_wires)
        # A junction joins every bus passing through it, interiors included.
        for j in junctions:
            hit = [k1 for k1, _k2, x1, y1, x2, y2 in self._segments
                   if _point_on_segment(j["x"], j["y"], x1, y1, x2, y2)]
            for k in hit[1:]:
                self._union(hit[0], k)

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

    # Bus label kinds that drive a bus subgraph, strongest first (a sheet pin never does).
    _DRIVER_RANK = {"global": 0, "local": 1, "hier": 2}

    def cluster_driver(self, cid):
        """The bus label KiCad picks to drive the cluster, or None.

        ResolveDrivers: the strongest kind, then a strict superset of members,
        then the alphabetically first name.
        """
        atts = [a for a in self._cluster_labels.get(cid, []) if a["role"] in self._DRIVER_RANK]
        if not atts:
            return None
        top = min(self._DRIVER_RANK[a["role"]] for a in atts)
        cands = sorted((a for a in atts if self._DRIVER_RANK[a["role"]] == top),
                       key=lambda a: _driver_sort_name(a["name"]))
        best = cands[0]
        for a in cands[1:]:
            if set(best["expansion"]) < set(a["expansion"]):
                best = a
        return best

    def member_aliases(self, cid):
        """``(member, driver member)`` pairs joining the cluster's other labels onto its driver.

        KiCad matchBusMember: a vector driver matches by position; a group driver
        matches by member name, and a vector member it cannot name by position;
        a group label on a vector driver matches nothing.
        """
        drv = self.cluster_driver(cid)
        if drv is None:
            return []
        dk = bus_kind(drv["name"])
        out, seen = [], {drv["name"]}
        for a in self._cluster_labels.get(cid, []):
            if a["role"] not in self._DRIVER_RANK or a["name"] in seen:
                continue
            seen.add(a["name"])
            sk = bus_kind(a["name"])
            if dk == sk == "group":
                pairs, _reason = pair_bus_members(a["name"], a["expansion"],
                                                  drv["name"], drv["expansion"])
            elif dk == sk == "vector":
                pairs = list(zip(a["expansion"], drv["expansion"]))
            elif dk == "group" and sk == "vector":
                flat = drv["expansion"]
                by_name = dict(zip(_local_member_names(drv["name"], flat), flat))
                pairs = [(m, by_name[m] if m in by_name else flat[i])
                         for i, m in enumerate(a["expansion"]) if m in by_name or i < len(flat)]
            else:
                pairs = []
            out.extend((m, d) for m, d in pairs if m != d)
        return out

    def labelled_clusters(self):
        return sorted(self._cluster_labels)

    def cluster_ordered(self, cid, width):
        """The member list a co-clustered sheet pin maps from: the cluster driver's.

        KiCad clones the driver's connection onto the pin whatever its width;
        ``width`` is kept for callers. Sets ``last_label`` to the driver's name.
        """
        drv = self.cluster_driver(cid)
        self.last_label = drv["name"] if drv else None
        return list(drv["expansion"]) if drv else None

    def note_unresolved(self, reason, name=None):
        # One note per distinct (reason, name) pair.
        entry = {"reason": reason, "name": name}
        if entry not in self.unresolved:
            self.unresolved.append(entry)


def _parent_side(pin):
    """(members, bus name) a sheet pin maps from: its cluster's driver label, else the pin."""
    if pin.get("parent_ordered"):
        return pin["parent_ordered"], pin.get("parent_name") or pin["name"]
    return pin["members"], pin["name"]


def match_ports(pin_ports, hier_ports, unresolved):
    """Pair parent-side sheet-pin ports with child-side hier-label ports.

    Indexes hier_ports by (ns, name) (iterating hier_ports in list order —
    if two hier ports share a key the sheet is malformed: first one wins
    the index slot and a note is appended to unresolved). For each pin port
    in pin_ports (in list order) finds its counterpart by the same key and
    pairs member slots with pair_bus_members: parent = port["parent_ordered"]
    (named port["parent_name"]) or port["members"] (an anonymous parent
    cluster falls back to the pin's own expansion); child = hier port's
    "members". Vectors pair by position up to the narrower bus, groups by
    member name; a port where nothing pairs appends a note to unresolved.
    A missing counterpart in either direction
    (a pin port with no hier port at that key, or vice versa) also appends
    a note; the hier-side pass runs after the pin-side pass, iterating
    hier_ports in list order. Returns
    [((pin_sheet, pin_cluster, parent_member),
      (hier_sheet, hier_cluster, child_member)), ...].

    "parent_ordered" is not computed here — the caller (build_net_map) computes
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
        parent, parent_name = _parent_side(pin)
        member_pairs, reason = pair_bus_members(parent_name, parent,
                                                hier["name"], hier["members"])
        if reason:
            unresolved.append({"reason": reason, "name": pin["name"]})
        for pm, cm in member_pairs:
            pairs.append((
                (pin["sheet"], pin["cluster"], pm),
                (hier["sheet"], hier["cluster"], cm),
            ))

    for hier in hier_ports:
        key = (hier["ns"], hier["name"])
        if key not in pin_keys:
            unresolved.append({
                "reason": "no_pin_counterpart_for_hier",
                "name": hier["name"],
            })

    return pairs


class CoordinateNearMiss(Exception):
    """A point within 0.01 mm of another point, or 0.05 mm of a wire, that KiCad does not join."""


_NEAR_MISS_CAP = 20
_NEAR_MISS_IU = 100  # 0.01 mm
_NEAR_MISS_EFFECT = "not connected (KiCad joins exact coordinates)"


def _mm(v: float) -> str:
    text = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def _describe_point(info: dict) -> str:
    src = info["source"]
    if src == "pin":
        return f"pin '{info['component']}.{info['pin_number']}'"
    if src == "pwr_flag":
        return f"PWR_FLAG pin '{info['component']}'"
    if src == "label":
        kind = (info.get("label_type") or "label").replace("_", " ")
        return f"{kind} '{info.get('name') or ''}'"
    if src == "power_symbol":
        return f"power symbol '{info['net_name']}'"
    return {"wire": "wire end", "junction": "junction", "no_connect": "no-connect marker",
            "bus_tap": "bus entry"}.get(src, src)


def _distance_to_segment_iu(p, a, b) -> float:
    abx, aby = b[0] - a[0], b[1] - a[1]
    apx, apy = p[0] - a[0], p[1] - a[1]
    f = abx * abx + aby * aby
    t = 0.0 if f == 0 else max(0.0, min(1.0, (apx * abx + apy * aby) / f))
    return ((apx - t * abx) ** 2 + (apy - t * aby) ** 2) ** 0.5


def build_net_map(components: list[dict], wires: list[dict], labels: list[dict],
                  power_symbols: list[dict], junctions: list[dict],
                  no_connects: list[dict] | None = None,
                  sheet_names: list[str] | None = None,
                  bus_elements: dict | None = None,
                  diagnostics: list | None = None,
                  sheet_paths: list[str] | None = None) -> dict[str, Net]:
    """Build a connectivity map using union-find on coordinates.

    Groups all electrically connected points into nets, then names them
    from labels and power symbols.

    Points join only at identical KiCad internal units (100 nm); a label joins
    a wire within 1 IU, a junction only exactly on it, a pin (power symbols
    included) only at a wire end. A point left unjoined within 0.01 mm of
    another point or 0.05 mm of a wire is recorded in ``diagnostics`` as a
    ``CoordinateNearMiss`` (at most 20, then one summary record).

    When ``bus_elements`` carries bus wires (GH #25), a per-sheet bus pass
    resolves hierarchical bus connectivity: bus-name labels are consumed out
    of the ordinary label handling, and their members are joined by name,
    by bus entry, and — across sheet pins — positionally to the child sheet's
    hier-label bus. On ``bus_elements=None`` or a board with no bus wires the
    pass is inert and the output is byte-identical to the pre-#25 map.

    ``sheet_paths`` gives each sheet index its human sheet path ("/", "/Power/",
    sheet names net-name escaped); with it, equal-rank labels on different sheets
    tie-break as KiCad does (see the driver loop).  Without it the sheet index
    stands in for the path.
    """
    # Collect all electrical points
    # Each point: (sheet, x, y, source_info)
    # The sheet index keeps each sheet's coordinate space separate so that
    # wires on different sheets at the same (x,y) don't falsely merge.
    parent = {}
    point_info = {}  # key -> list of info dicts
    # 0.01 mm buckets, used only to report points that are close but not equal:
    # (sheet, bx, by) -> {key: (x, y, info) of its first point}
    near_buckets: dict[tuple, dict] = {}
    near_wires: dict[tuple, tuple] = {}  # (key, wire index) -> (x, y, info)

    def key(x, y, sheet=0):
        return (sheet, to_iu(x), to_iu(y))

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
        near_buckets.setdefault((sheet, round(x / 0.01), round(y / 0.01)), {}).setdefault(
            k, (x, y, info))
        return k

    nc_pins: list[tuple] = []  # (own key, position key) of each NC-type pin
    # Add component pins. PWR_FLAG is an ERC marker, not a real connection —
    # still register its position so the net gets a has_pwr_flag annotation.
    for comp in components:
        pins = comp.get("pins") or []
        # a power symbol with only power-output pins is a PWR_FLAG whatever its Value
        is_pwr_flag = (comp.get("value") == "PWR_FLAG" or comp.get("type") == "power_flag"
                       or (comp.get("type") == "power_symbol" and pins
                           and all(p.get("type") == "power_out" for p in pins)))
        sheet = comp.get("_sheet", 0)
        number_keys: dict[str, list] = {}
        for pin in pins:
            if not is_pwr_flag and pin["type"] in ("no_connect", "unconnected"):
                # KiCad never joins an NC-type pin to anything at its position
                # (SCH_PIN::ConnectionPropagatesTo): the pin is a net of its own.
                k = ("nc_pin", len(nc_pins))
                pos = key(pin["x"], pin["y"], sheet)
                parent.setdefault(pos, pos)  # what else lands here keeps its place in net order
                parent[k] = k
                point_info[k] = [{
                    "source": "pin",
                    "component": comp["reference"],
                    "pin_number": pin["number"],
                    "pin_name": pin["name"],
                    "pin_type": pin["type"],
                }]
                nc_pins.append((k, pos))
                continue
            if is_pwr_flag:
                add_point(pin["x"], pin["y"], {
                    "source": "pwr_flag",
                    "component": comp["reference"],
                }, sheet)
            else:
                k = add_point(pin["x"], pin["y"], {
                    "source": "pin",
                    "component": comp["reference"],
                    "pin_number": pin["number"],
                    "pin_name": pin["name"],
                    "pin_type": pin["type"],
                }, sheet)
                number_keys.setdefault(pin["number"], []).append(k)
        # KiCad 10 jumper symbols join, inside the placed symbol, the pins of each jumper
        # pin group and (with duplicate_pin_numbers_are_jumpers) the pins sharing a number.
        if comp.get("_jumper_groups"):
            groups, dup_numbers = comp["_jumper_groups"]
            linked = [ks for ks in number_keys.values() if len(ks) > 1] if dup_numbers else []
            linked += [[k for n in sorted(g) for k in number_keys.get(n, [])] for g in groups]
            for ks in linked:
                for k in ks[1:]:
                    union(ks[0], k)

    # Add wire endpoints and union them.
    # Also build a list of wire segments so we can detect points that land
    # mid-wire (labels, junctions and bus-entry taps placed on a wire between
    # its endpoints).
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

    def wires_near(px, py, sheet):
        return wire_grid.get((sheet, int(px // _WIRE_GRID_SIZE), int(py // _WIRE_GRID_SIZE)), ())

    def union_with_overlapping_wires(k, px, py, sheet, dist_iu, info):
        """Union point k with every same-sheet wire within dist_iu IU of it.

        dist_iu None joins no wire here (a pin meets a wire only at its end,
        which shares k). A wire within 0.05 mm that does not join is kept as a
        near-miss candidate.
        """
        for idx in wires_near(px, py, sheet):
            wk1, wk2, wx1, wy1, wx2, wy2, _ws = wire_segments[idx]
            if dist_iu is not None and segment_hit_iu(k[1:], wk1[1:], wk2[1:], dist_iu):
                union(k, wk1)
                # no early return — a junction/label at a crossing
                # must join every wire under it, matching KiCad's
                # connection_graph (all coincident lines are inserted).
            elif _point_on_segment(px, py, wx1, wy1, wx2, wy2):
                near_wires.setdefault((k, idx), (px, py, info))

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
    bus_named_labels: list[tuple] = []  # (sheet, bare, x, y, role), local/global/hier
    if bus_active:
        bus_aliases = {a["name"]: a["members"]
                       for a in bus_elements.get("bus_aliases", [])}
        wires_by_sheet: dict[int, list] = {}
        entries_by_sheet: dict[int, list] = {}
        for bw in bus_elements.get("bus_wires", []):
            wires_by_sheet.setdefault(bw.get("_sheet", 0), []).append(bw)
        for be_ in bus_elements.get("bus_entries", []):
            entries_by_sheet.setdefault(be_.get("_sheet", 0), []).append(be_)
        junctions_by_sheet: dict[int, list] = {}
        for j in junctions:
            junctions_by_sheet.setdefault(j.get("_sheet", 0), []).append(j)
        for s in wires_by_sheet:
            bus_graphs[s] = BusGraph(s, wires_by_sheet[s],
                                     entries_by_sheet.get(s, []), bus_aliases,
                                     junctions_by_sheet.get(s, ()))
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
            if lbl.get("_is_sheet_pin"):
                role = "pin"
            elif lbl["type"] == "hierarchical_label":
                role = "hier"
            elif lbl["type"] == "global_label":
                role = "global"
            else:
                role = "local"
            if g.add_bus_label(bare, lbl["x"], lbl["y"],
                               ns=lbl.get("_hier_ns", ""), role=role):
                bus_label_idx.add(idx)
                if role != "pin":
                    bus_named_labels.append((s, bare, lbl["x"], lbl["y"], role))
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
        # Defensive coercion — malformed labels can have list names
        lbl_name = lbl["name"]
        if isinstance(lbl_name, list):
            lbl_name = str(lbl_name[0]) if lbl_name else ""
        lbl_info = {
            "source": "label",
            "name": lbl_name,
            "label_type": lbl["type"],
            "bare_name": lbl.get("_bare_name"),
            "is_sheet_pin": bool(lbl.get("_is_sheet_pin")),
        }
        k = add_point(lbl["x"], lbl["y"], lbl_info, sheet)
        # Only global labels and power symbols connect across sheets.
        # Local labels only connect within the same sheet (handled by wire union).
        if lbl["type"] == "global_label":
            label_keys.setdefault(lbl_name, []).append(k)
            # KiCad also joins a global label to same-name local labels on its own sheet.
            label_keys.setdefault((lbl_name, sheet), []).append(k)
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
        # KiCad joins a label to a wire it hits within 1 IU.
        union_with_overlapping_wires(k, lbl["x"], lbl["y"], sheet, 1, lbl_info)

    # Add power symbols — compute actual pin position from lib symbol.
    # PWR_FLAG is a DRC-only marker (tells ERC a net has a power source).
    # It doesn't create real connectivity, so exclude it entirely.
    for ps in power_symbols:
        if ps["net_name"] == "PWR_FLAG" or ps.get("_drives") is False:
            continue
        sheet = ps.get("_sheet", 0)
        ps_info = {
            "source": "power_symbol",
            "net_name": ps["net_name"],
            "power_scope": ps.get("_power_scope", "global"),
        }
        k = add_point(ps["x"], ps["y"], ps_info, sheet)
        # Global power symbols connect across all sheets; local power symbols
        # only connect within the same sheet (isolated power domains).
        if ps.get("_power_scope") == "local":
            local_key = (ps["net_name"], sheet)
            label_keys.setdefault(local_key, []).append(k)
        else:
            label_keys.setdefault(ps["net_name"], []).append(k)
            # ... and a same-name local label on its sheet joins it, as for a global label.
            label_keys.setdefault((ps["net_name"], sheet), []).append(k)
        # A power symbol is a pin: KiCad joins it to a wire only at a wire end.
        union_with_overlapping_wires(k, ps["x"], ps["y"], sheet, None, ps_info)

    # Legacy hidden power-in pins: in KiCad 4/5, ICs could have invisible
    # power-in pins (VCC, GND) that create implicit global net connections
    # by pin name.  These pins have no wires attached — they connect solely
    # by their name matching other hidden power pins or power symbols.
    # A power-input pin of a power-flagged library symbol is global even when
    # visible (SCH_PIN::IsGlobalPower).
    for comp in components:
        if comp.get("type") == "power_symbol":
            continue
        sheet = comp.get("_sheet", 0)
        for pin in comp.get("pins", []):
            if ((pin.get("hidden") or comp.get("_global_power_part"))
                    and pin["type"] == "power_in" and pin["name"]):
                k = key(pin["x"], pin["y"], sheet)
                label_keys.setdefault(pin["name"], []).append(k)
                label_keys.setdefault((pin["name"], sheet), []).append(k)

    # Union global/hierarchical labels and power symbols with the same name.
    # This is what connects nets across different parts of the schematic.
    for lbl_name, keys in label_keys.items():
        for j in range(1, len(keys)):
            union(keys[0], keys[j])

    # Add junctions — also check mid-wire placement
    for junc in junctions:
        sheet = junc.get("_sheet", 0)
        junc_info = {"source": "junction"}
        k = add_point(junc["x"], junc["y"], junc_info, sheet)
        # KiCad joins a junction to the wires it lies exactly on.
        union_with_overlapping_wires(k, junc["x"], junc["y"], sheet, 0, junc_info)

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
    #   (C) across a sheet pin — the parent's pin-port members map onto the
    #       matching child hier-port members (vectors by position, groups by
    #       member name).
    if bus_active and bus_graphs:
        def bus_slot(sheet, cid, member):
            sk = ("bus", sheet, cid, member)
            if sk not in parent:
                parent[sk] = sk
            return sk

        # (A) Name-based member joining for local/global/hier bus labels. Sheet-pin
        # ("pin") labels are excluded: their members name the child's nets,
        # not the parent's local nets, so they map only positionally in (C).
        # A local/hier bus label accepts only the same-sheet LOCAL key
        # `(member, s)` — its members are local-scoped, so they must not fuse
        # with a coincidentally same-named GLOBAL label (keyed bare) elsewhere;
        # KiCad keeps local/hier bus scope separate from the global net space.
        # A global bus label also takes the bare key (below).
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
        #
        # A GLOBAL bus label's members are global nets, as KiCad names them: the
        # same member under any global bus on any sheet is one net, and a global
        # net label or power symbol of the member's name (the bare label_keys
        # entry) joins it.
        member_rep: dict[tuple, tuple] = {}  # (sheet, member) -> a member slot
        global_rep: dict[str, tuple] = {}  # member -> a slot, across sheets
        for s, bare, lx, ly, role in bus_named_labels:
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
                if role == "global":
                    grep_ = global_rep.get(member)
                    if grep_ is None:
                        global_rep[member] = slot
                    else:
                        union(grep_, slot)
                    gk = label_keys.get(member)
                    if gk:
                        union(slot, gk[0])

        # (A2) Several bus labels on one bus wire: KiCad renames the other
        # labels' members onto the label that drives the bus (matchBusMember),
        # so D[4..7] on a D[0..7] wire joins D4 with D0.
        for s in sorted(bus_graphs):
            g = bus_graphs[s]
            for cid in g.labelled_clusters():
                for m, d in g.member_aliases(cid):
                    union(bus_slot(s, cid, m), bus_slot(s, cid, d))

        # (B1) Register every bus-entry tap point and union it with the wires
        # it lands on. This must precede the root_names sweep so a tapped
        # wire's labels are visible on the tap's net.
        tap_points = []  # (sheet, tap_key, tap)
        for s in sorted(bus_graphs):
            g = bus_graphs[s]
            for tap in g.taps:
                tk = add_point(tap["x"], tap["y"], {"source": "bus_tap"}, s)
                for idx in wires_near(tap["x"], tap["y"], s):
                    wk1, _wk2, wx1, wy1, wx2, wy2, _ws = wire_segments[idx]
                    if _point_on_segment(tap["x"], tap["y"], wx1, wy1, wx2, wy2):
                        union(tk, wk1)
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
        # Read every tap's names first: joining a tap to its slot below can
        # re-root its net, and root_names is keyed by the roots before that.
        tap_names = [root_names.get(find(tk), set()) for _s, tk, _tap in tap_points]
        for (s, tk, tap), names in zip(tap_points, tap_names):
            g = bus_graphs[s]
            mset = g.cluster_member_set(tap["cluster"])
            cand = (names & mset) if mset is not None else set(names)
            if cand:
                for member in sorted(cand):
                    union(tk, bus_slot(s, tap["cluster"], member))
            elif names:
                g.note_unresolved("entry_tap_name_not_in_bus", sorted(names)[0])
            else:
                g.note_unresolved("unlabeled_entry_tap", None)

        # (C) Sheet-pin port matching.
        pin_ports, hier_ports = [], []
        for s in sorted(bus_graphs):
            g = bus_graphs[s]
            for p in g.ports:
                p = dict(p, sheet=s)
                if p["role"] == "pin":
                    p["parent_ordered"] = g.cluster_ordered(
                        p["cluster"], len(p["members"]))
                    p["parent_name"] = g.last_label
                    pin_ports.append(p)
                else:
                    hier_ports.append(p)

        # (C0) Co-clustered sheet pins with no bus label on their wire: KiCad picks one
        # pin to drive the bus (ResolveDrivers: a superset of members, then the name)
        # and clones its bus onto the other pins, so every child maps by position onto
        # the driving pin's members in (C). The pins' own member names stay apart:
        # X[2..5] beside X[0..5] maps its X2 onto X0, it does not join X2. Pins of
        # mixed kinds (a vector beside a group) keep their own members and join pin to
        # pin with pair_bus_members.
        pins_by_cluster: dict[tuple, list] = {}
        for p in pin_ports:
            pins_by_cluster.setdefault((p["sheet"], p["cluster"]), []).append(p)
        for grp in pins_by_cluster.values():
            if len(grp) < 2 or any(q["parent_ordered"] for q in grp):
                continue
            if len({bus_kind(q["name"]) for q in grp}) == 1:
                ranked = sorted(grp, key=lambda q: _driver_sort_name(q["name"]))
                drv = ranked[0]
                for q in ranked[1:]:
                    if set(drv["members"]) < set(q["members"]):
                        drv = q
                for q in grp:
                    q["parent_ordered"] = list(drv["members"])
                    q["parent_name"] = drv["name"]
                continue
            for other in grp[1:]:
                member_pairs, _reason = pair_bus_members(
                    grp[0]["name"], grp[0]["members"], other["name"], other["members"])
                for rm, em in member_pairs:
                    union(bus_slot(grp[0]["sheet"], grp[0]["cluster"], rm),
                          bus_slot(other["sheet"], other["cluster"], em))

        all_unresolved: list = []
        for (ps, pc, pm), (cs, cc, cm) in match_ports(
                pin_ports, hier_ports, all_unresolved):
            union(bus_slot(ps, pc, pm), bus_slot(cs, cc, cm))

        bus_elements["_unresolved"] = all_unresolved + [
            u for s in sorted(bus_graphs) for u in bus_graphs[s].unresolved]

    _record_near_misses(near_buckets, near_wires, wire_segments, find, sheet_names, diagnostics)

    # An NC-type pin is touched when another pin or a connection point other than a
    # no-connect marker sits on it (ERC TestNoConnectPins); stacked NC pins report once.
    nc_keys = {k for k, _pos in nc_pins}
    net_groups: dict[tuple, list[tuple]] = {}
    for k in parent:
        if k not in nc_keys:
            net_groups.setdefault(find(k), []).append(k)
    named_roots = {r for r, ms in net_groups.items()
                   if any(i["source"] in ("pin", "label", "power_symbol")
                          for m in ms for i in point_info.get(m, ()))}
    nc_touched: set = set()
    nc_marked: set = set()
    nc_later: set = set()  # split off a net that still exists: numbered after the other nets
    seen_positions: set = set()
    for k, pos in nc_pins:
        here = point_info.get(pos, ())
        if any(i["source"] == "no_connect" for i in here):
            nc_marked.add(k)
        if any(i["source"] != "no_connect" for i in here) and pos not in seen_positions:
            nc_touched.add(k)
        if find(pos) in named_roots or pos in seen_positions:
            nc_later.add(k)
        seen_positions.add(pos)

    # Build net groups
    ordered: dict[tuple, list[tuple]] = {}
    for k in parent:
        if k in nc_keys:
            if k not in nc_later:
                ordered[k] = [k]
            continue
        r = find(k)
        if r not in ordered:
            ordered[r] = net_groups[r]
    for k, _pos in nc_pins:
        if k in nc_later:
            ordered[k] = [k]
    net_groups = ordered

    # Name the nets
    staged = []
    net_id = 0
    for root_k, members in net_groups.items():
        # Collect all info for this net
        all_info = []
        for m in members:
            all_info.extend(point_info.get(m, []))

        # Find net name using KiCad's driver priority (connection_graph.h PRIORITY):
        # global label > power symbol (global, then local) > local label >
        # hierarchical label > sheet pin
        _NET_NAME_PRIORITY = {
            "global_label": 0,
            "power_symbol": 1,
            "label": 2,
            "hierarchical_label": 3,
            "sheet_pin": 4,
            "directive_label": 5,
        }

        # Accumulate every global / hierarchical / local label attached to
        # this net (LB-001 reads this; also useful for report annotations).
        # Dedup by (name, label_type).
        # best = (priority, tiebreak_sheet, tiebreak_name, name, is_local, sheet)
        # At equal priority KiCad prefers the shallower sheet, then the lower
        # full net name, sheet path included ("/Amplifier/EN" before
        # "/Video/AMP_STB"; ResolveDrivers, propagateToNeighbors).
        # tiebreak_sheet is -1 for global-scope sources, else the sheet depth
        # and tiebreak_name the escaped name behind the sheet path (sheet names
        # escaped, separators plain, as KiCad's PathHumanReadable).  Without
        # sheet_paths it is the sheet index (breadth-first, never deeper for a
        # lower index) and the bare escaped name.
        best = None
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
                    sheet_scoped = is_local
                    tie_name = cand_name
                elif src == "label":
                    lbl_name = info.get("name") or ""
                    lbl_type = info.get("label_type") or "label"
                    p = _NET_NAME_PRIORITY.get(
                        "sheet_pin" if info.get("is_sheet_pin") else lbl_type, 2)
                    cand_name = lbl_name
                    is_local = lbl_type in ("label", "directive_label")
                    sheet_scoped = lbl_type != "global_label"
                    tie_name = info.get("bare_name") or lbl_name
                    key_tuple = (lbl_name, lbl_type)
                    if lbl_name and key_tuple not in net_labels_seen:
                        net_labels_seen.add(key_tuple)
                        entry = {"name": lbl_name, "type": lbl_type}
                        if info.get("bare_name"):
                            entry["_bare_name"] = info["bare_name"]
                        net_labels.append(entry)
                else:
                    continue
                if cand_name:
                    if not sheet_scoped:
                        tie = (-1, _driver_sort_name(tie_name))
                    elif sheet_paths and 0 <= m_sheet < len(sheet_paths):
                        sp = sheet_paths[m_sheet]
                        tie = (sp.count("/"), sp + _driver_sort_name(tie_name))
                    else:
                        tie = (m_sheet, _driver_sort_name(tie_name))
                    cand = (p, *tie, cand_name, is_local, m_sheet)
                    if best is None or cand[:3] < best[:3]:
                        best = cand
        net_name = best[3] if best else None

        # Check if any member of this group is a no-connect marker OR a
        # library-defined NC pin (pin type "no_connect" in the symbol def).
        nc_marker = (any(i["source"] == "no_connect" for i in all_info)
                     or root_k in nc_marked)
        has_nc_marker = (
            nc_marker
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
                "nc_marker": nc_marker,
                "nc_touched": root_k in nc_touched,
                "labels": net_labels,
            })

    # one entry per union-find group. On bare-name collisions the
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
            if e["nc_marker"]:
                entry["_nc_marker"] = True  # a no-connect marker, not only an NC-type pin
            if e["nc_touched"]:
                entry["_nc_touched"] = True  # something else sits on this NC-type pin
            # The key keeps KiCad's escaped name; display_name is the name KiCad shows.
            shown = unescape_string(bare)
            if k != shown:
                entry["display_name"] = shown
            nets[k] = entry
    return nets


def _driver_sort_name(name: str) -> str:
    """The text KiCad sorts equal-rank drivers by: the name escaped as a net name."""
    return name.replace("/", "{slash}").replace("\n", "").replace("\r", "")


def _record_near_misses(near_buckets, near_wires, wire_segments, find, sheet_names, diagnostics):
    """Record each near-miss candidate that ends up not connected."""
    def sheet_label(sheet):
        return sheet_names[sheet] if sheet_names and 0 <= sheet < len(sheet_names) else sheet

    events = []
    reported = set()
    for (sheet, bx, by), pts in sorted(near_buckets.items()):
        for k in sorted(pts):
            if k in reported:
                continue
            # Compare with the neighbouring buckets too, so a pair across a bucket edge is seen;
            # each point is reported against the first point near it that it does not join.
            k0 = None
            for nx in (bx - 1, bx, bx + 1):
                for ny in (by - 1, by, by + 1):
                    for kn in near_buckets.get((sheet, nx, ny), ()):
                        if (kn < k and (k0 is None or kn < k0)
                                and (kn[1] - k[1]) ** 2 + (kn[2] - k[2]) ** 2 <= _NEAR_MISS_IU ** 2
                                and find(kn) != find(k)):
                            k0, src0 = kn, near_buckets[(sheet, nx, ny)][kn]
            if k0 is None:
                continue
            reported.add(k)
            x, y, info = pts[k]
            x0, y0, info0 = src0
            d = ((k[1] - k0[1]) ** 2 + (k[2] - k0[2]) ** 2) ** 0.5 / 1e4
            events.append((k, f"sheet {sheet_label(k[0])}: {_describe_point(info)} at ({_mm(x)}, {_mm(y)}) mm"
                              f" is {_mm(d)} mm from {_describe_point(info0)} at ({_mm(x0)}, {_mm(y0)})"))
    for (k, idx), (x, y, info) in near_wires.items():
        wk1, wk2, wx1, wy1, wx2, wy2, _ws = wire_segments[idx]
        if find(k) == find(wk1):
            continue
        d = _distance_to_segment_iu(k[1:], wk1[1:], wk2[1:]) / 1e4
        where = (f"lies inside wire ({_mm(wx1)}, {_mm(wy1)})-({_mm(wx2)}, {_mm(wy2)})"
                 " (a pin joins a wire only at its ends)" if d == 0 else
                 f"is {_mm(d)} mm from wire ({_mm(wx1)}, {_mm(wy1)})-({_mm(wx2)}, {_mm(wy2)})")
        events.append((k, f"sheet {sheet_label(k[0])}: {_describe_point(info)} at ({_mm(x)}, {_mm(y)}) mm"
                          f" {where}"))
    events.sort()
    for _k, message in events[:_NEAR_MISS_CAP]:
        record(diagnostics, "schematic.connectivity.build_net_map",
               CoordinateNearMiss(message), _NEAR_MISS_EFFECT)
    if len(events) > _NEAR_MISS_CAP:
        record(diagnostics, "schematic.connectivity.build_net_map",
               CoordinateNearMiss(f"{len(events) - _NEAR_MISS_CAP} more near misses not listed"),
               _NEAR_MISS_EFFECT)


# Internal-only fields the bus pass (GH #25) reads off namespaced hierarchical
# labels. They must never reach the user-facing `labels` output. `_sheet` is
# NOT one of these — it has leaked on every label since before this branch, so
# stripping it would itself change baseline output.
_INTERNAL_LABEL_KEYS = ("_bare_name", "_hier_ns", "_is_sheet_pin")


def _labels_for_output(labels: list[dict]) -> list[dict]:
    """Return a copy of `labels` with the bus-pass internal keys removed."""
    return [{k: v for k, v in lbl.items() if k not in _INTERNAL_LABEL_KEYS}
            for lbl in labels]


def strip_net_label_internals(nets: dict) -> None:
    """Drop the bus-pass/LB-001 internal keys from every net's ``labels``, in place."""
    for info in nets.values():
        if info.get("labels"):
            info["labels"] = _labels_for_output(info["labels"])


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
