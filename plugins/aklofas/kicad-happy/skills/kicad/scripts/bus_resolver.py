"""Bus name expansion and per-sheet bus connectivity graph (GH #25).

Pure bus logic, isolated from the rest of the analyzer: stdlib-only and no
imports from analyze_schematic. Replicates KiCad's bus semantics: ordered
vector expansion, group/labeled-group buses (dot-joined members), nested
groups, bus_alias resolution inside groups, and the _{...}/^{...}/~{...}
text-markup exclusion.
"""

import re

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
