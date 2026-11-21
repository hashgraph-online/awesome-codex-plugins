"""ERC pin semantics as KiCad 10 applies them by default: the pin-conflict map, the driver
sets, stacked pins and the default severities.

Sources: eeschema/erc/erc_settings.cpp (m_defaultPinMap, default severities), eeschema/erc/erc.cpp
(DrivingPinTypes, DrivingPowerPinTypes, DrivenPinTypes, TestPinToPin) and
eeschema/sch_pin.cpp (SCH_PIN::IsStacked).
"""
from __future__ import annotations

from functools import cmp_to_key
from math import hypot, inf

from kicad_core.coords import to_iu

_ORDER = ("input", "output", "bidirectional", "tri_state", "passive", "free",
          "unspecified", "power_in", "power_out", "open_collector", "open_emitter", "no_connect")
_IDX = {t: i for i, t in enumerate(_ORDER)}
OK, WARNING, ERROR = 0, 1, 2
_O, _W, _E = OK, WARNING, ERROR
_PIN_MAP = (
    #  I   O   Bi  3S  Pas NIC UnS PwI PwO OC  OE  NC
    (_O, _O, _O, _O, _O, _O, _W, _O, _O, _O, _O, _E),  # I
    (_O, _E, _O, _W, _O, _O, _W, _O, _E, _E, _E, _E),  # O
    (_O, _O, _O, _O, _O, _O, _W, _O, _W, _O, _W, _E),  # Bi
    (_O, _W, _O, _O, _O, _O, _W, _W, _E, _W, _W, _E),  # 3S
    (_O, _O, _O, _O, _O, _O, _W, _O, _O, _O, _O, _E),  # Pas
    (_O, _O, _O, _O, _O, _O, _O, _O, _O, _O, _O, _E),  # NIC
    (_W, _W, _W, _W, _W, _O, _W, _W, _W, _W, _W, _E),  # UnS
    (_O, _O, _O, _W, _O, _O, _W, _O, _O, _O, _O, _E),  # PwI
    (_O, _E, _W, _E, _O, _O, _W, _O, _E, _E, _E, _E),  # PwO
    (_O, _E, _O, _W, _O, _O, _W, _O, _E, _O, _O, _E),  # OC
    (_O, _E, _W, _W, _O, _O, _W, _O, _E, _O, _O, _E),  # OE
    (_E, _E, _E, _E, _E, _E, _E, _E, _E, _E, _E, _E),  # NC
)
DRIVING = frozenset({"output", "power_out", "passive", "tri_state", "bidirectional"})
DRIVING_POWER = frozenset({"power_out"})
DRIVEN = frozenset({"input", "power_in"})
# Pin kinds that actively drive a net (multi_driver_nets keeps conflicts among these).
DRIVERS = frozenset({"output", "power_out", "tri_state", "bidirectional",
                     "open_collector", "open_emitter"})
SEVERITY = {ERROR: "error", WARNING: "warning"}
# ERC_SETTINGS::m_PinTypeWeights: which pin of a conflicting pair carries the marker.
_PIN_WEIGHT = {"free": 11, "unspecified": 10, "passive": 9, "open_collector": 8,
               "open_emitter": 7, "input": 6, "tri_state": 5, "bidirectional": 4,
               "output": 3, "power_in": 2, "power_out": 1, "no_connect": 0}


def pin_kind(t: str | None) -> str:
    """A pin type string as a KiCad electrical type (the legacy 'unconnected' is no_connect)."""
    t = (t or "unspecified").lower()
    if t == "unconnected":
        return "no_connect"
    return t if t in _IDX else "unspecified"


def pair_level(a: str | None, b: str | None) -> int:
    return _PIN_MAP[_IDX[pin_kind(a)]][_IDX[pin_kind(b)]]


def pin_positions(components: list[dict]) -> dict:
    """(ref, pin number) -> (sheet, x, y, name), positions in schematic IU."""
    pos = {}
    for c in components:
        for p in c.get("pins") or []:
            if p.get("x") is None or p.get("y") is None:
                continue
            pos[(c["reference"], p.get("number", ""))] = (
                c.get("_sheet", 0), to_iu(p["x"]), to_iu(p["y"]), p.get("name"))
    return pos


def is_stacked(a: dict, b: dict, positions: dict) -> bool:
    """SCH_PIN::IsStacked: same symbol, position and name; same type or one passive/free."""
    if a["component"] != b["component"]:
        return False
    pa = positions.get((a["component"], a["pin_number"]))
    if pa is None or pa != positions.get((b["component"], b["pin_number"])):
        return False
    ta, tb = pin_kind(a.get("pin_type")), pin_kind(b.get("pin_type"))
    return ta == tb or ta in ("passive", "free") or tb in ("passive", "free")


def net_pin_conflicts(pins: list[dict], positions: dict) -> list[tuple[int, int, int]]:
    """Every non-OK pin pair on one net as (i, j, level) with i < j, stacked pins skipped."""
    by_kind: dict[int, list[int]] = {}
    for i, p in enumerate(pins):
        by_kind.setdefault(_IDX[pin_kind(p.get("pin_type"))], []).append(i)
    kinds = sorted(by_kind)
    out = []
    for n, ka in enumerate(kinds):
        for kb in kinds[n:]:
            level = _PIN_MAP[ka][kb]
            if not level:
                continue
            for i in by_kind[ka]:
                for j in by_kind[kb]:
                    if ka == kb and j <= i:
                        continue
                    if not is_stacked(pins[i], pins[j], positions):
                        out.append((min(i, j), max(i, j), level))
    out.sort()
    return out


def undriven_kind(pins: list[dict]) -> str | None:
    """TestPinToPin's drive test: 'pin_not_driven', 'power_pin_not_driven' or None.

    A net with a power input pin is a power net, driven only by a power output pin.
    """
    kinds = {pin_kind(p.get("pin_type")) for p in pins}
    if not kinds & DRIVEN:
        return None
    power = "power_in" in kinds
    if kinds & (DRIVING_POWER if power else DRIVING):
        return None
    return "power_pin_not_driven" if power else "pin_not_driven"


_DIGITS = frozenset("0123456789")


def str_num_cmp(a: str, b: str) -> int:
    """KiCad StrNumCmp (case-sensitive): digit runs compare as numbers."""
    i = j = 0
    while i < len(a) and j < len(b):
        c1, c2 = a[i], b[j]
        if c1 in _DIGITS and c2 in _DIGITS:
            i0, j0 = i, j
            while i < len(a) and a[i] in _DIGITS:
                i += 1
            while j < len(b) and b[j] in _DIGITS:
                j += 1
            n1, n2 = int(a[i0:i]), int(b[j0:j])
            if n1 != n2:
                return -1 if n1 < n2 else 1
            c1 = a[i] if i < len(a) else "\0"
            c2 = b[j] if j < len(b) else "\0"
        if c1 != c2:
            return -1 if c1 < c2 else 1
        i, j = min(i + 1, len(a)), min(j + 1, len(b))
    if i == len(a) and j != len(b):
        return -1
    if i != len(a) and j == len(b):
        return 1
    return 0


def _descending_hinted(keys: list[tuple[int, int]]) -> list[int]:
    """Order of std::inserter(multimap<..., greater>, begin()) fed (key, item) in turn.

    A hinted multimap insert puts the element "as close as possible to the position just
    prior to" the hint ([associative.reqmts]), so equal keys do not keep insertion order.
    """
    out: list[tuple[int, int]] = []
    hint = 0
    for k, item in keys:
        lower = sum(1 for e in out if e[0] > k)
        upper = sum(1 for e in out if e[0] >= k)
        at = min(max(hint, lower), upper)
        out.insert(at, (k, item))
        hint = at + 1
    return [item for _k, item in out]


def pin_to_pin_markers(pins: list[dict], positions: dict) -> list[tuple[int, int, int]]:
    """The pin-to-pin markers KiCad 10 places on one net, as (marked pin, other pin, level).

    erc.cpp TestPinToPin: pins sorted by reference then number; each pin, by descending type
    weight, takes every remaining conflict it is part of and gets one marker naming the nearest
    other pin on its own sheet (else the last one on another sheet).
    """
    def ref_num(i, j):
        a, b = pins[i], pins[j]
        return (str_num_cmp(a["component"], b["component"])
                or str_num_cmp(str(a["pin_number"]), str(b["pin_number"])))

    order = sorted(range(len(pins)), key=cmp_to_key(ref_num))
    ordered = [pins[k] for k in order]
    left = net_pin_conflicts(ordered, positions)
    if not left:
        return []
    weight = {}
    for i, j, _level in left:
        weight[i] = _PIN_WEIGHT[pin_kind(ordered[i].get("pin_type"))]
        weight[j] = _PIN_WEIGHT[pin_kind(ordered[j].get("pin_type"))]
    out = []
    for p in _descending_hinted([(weight[i], i) for i in sorted(weight)]):
        if not left:
            break
        here = positions.get((ordered[p]["component"], ordered[p]["pin_number"]))
        nearest, best, level = None, inf, OK
        rest = []
        for t in left:
            if p not in (t[0], t[1]):
                rest.append(t)
                continue
            other = t[1] if t[0] == p else t[0]
            there = positions.get((ordered[other]["component"], ordered[other]["pin_number"]))
            if here is None or there is None or here[0] != there[0]:
                if best == inf:
                    nearest, level = other, t[2]
            else:
                d = hypot(here[1] - there[1], here[2] - there[2])
                if best == inf or d < best:
                    best, nearest, level = d, other, t[2]
        left = rest
        if nearest is not None:
            out.append((order[p], order[nearest], level))
    return out
