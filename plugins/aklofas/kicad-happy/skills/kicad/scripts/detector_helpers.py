"""Shared helper functions for signal and domain detectors.

Extracted from repeated patterns across signal_detectors.py and
domain_detectors.py to eliminate boilerplate and reduce copy-paste risk.
"""

from __future__ import annotations

from collections.abc import Iterable

from kicad_core.classify import classify_ic_function
from kicad_core.netnames import net_leaf
from kicad_types import AnalysisContext


def index_two_pin_components(
    ctx: AnalysisContext,
    components: list[dict],
) -> tuple[dict[str, tuple[str, str]], dict[str, list[str]]]:
    """Index 2-pin components by their connected nets.

    Returns:
        comp_nets: ``{ref: (net1, net2)}`` for each valid component
        net_to_comps: ``{net_name: [ref, ...]}`` reverse index

    Skips components with missing nets, single-net connections, or
    same net on both pins (shorted).
    """
    comp_nets: dict[str, tuple[str, str]] = {}
    net_to_comps: dict[str, list[str]] = {}
    for comp in components:
        ref = comp["reference"]
        n1, n2 = ctx.get_two_pin_nets(ref)
        if not n1 or not n2 or n1 == n2:
            continue
        comp_nets[ref] = (n1, n2)
        net_to_comps.setdefault(n1, []).append(ref)
        net_to_comps.setdefault(n2, []).append(ref)
    return comp_nets, net_to_comps


def get_pin_net(ctx: AnalysisContext, ref: str, pin_names: tuple[str, ...]) -> str | None:
    """Find the net connected to a pin matching any of the given names."""
    pins = ctx.ref_pins.get(ref, {})
    for pnum, (net, _) in pins.items():
        comp = ctx.comp_lookup.get(ref)
        if not comp:
            continue
        for p in comp.get('pins', []):
            if p.get('number') == pnum and p.get('name', '').upper() in pin_names:
                return net
    # Fallback: check net pin_name via ctx.nets
    for pnum, (net, _) in pins.items():
        if not net or net not in ctx.nets:
            continue
        for np in ctx.nets[net]['pins']:
            if np['component'] == ref and np.get('pin_name', '').upper() in pin_names:
                return net
    return None


def get_components_by_type(
    ctx: AnalysisContext,
    comp_type: str | tuple[str, ...],
    with_parsed_values: bool = False,
) -> list[dict]:
    """Filter ctx.components by type, optionally requiring a parsed value.

    Args:
        comp_type: Single type string or tuple of types.
        with_parsed_values: If True, only include components whose reference
            appears in ``ctx.parsed_values``.
    """
    if isinstance(comp_type, str):
        comp_type = (comp_type,)
    result = [c for c in ctx.components if c["type"] in comp_type]
    if with_parsed_values:
        result = [c for c in result if c["reference"] in ctx.parsed_values]
    return result


def get_unique_ics(ctx) -> list:
    """Return deduplicated list of IC components.

    Components with duplicate references are collapsed: the list keeps the
    position of a reference's first occurrence and the record of its last.
    """
    return list({c["reference"]: c for c in ctx.components if c["type"] == "ic"}.values())


def match_ic_keywords(component: dict, keywords: list[str] | tuple[str, ...]) -> bool:
    """Check if an IC's value+lib_id contains any of the given keywords.

    Performs case-insensitive matching against the concatenation of the
    component's ``value`` and ``lib_id`` fields.  Only matches components
    with ``type == 'ic'``.
    """
    if component.get("type") != "ic":
        return False
    val_lib = (component.get("value", "") + " " + component.get("lib_id", "")).lower()
    return any(k in val_lib for k in keywords)


def match_family(comp: dict, families: dict[str, Iterable[str]]) -> str | None:
    """Return the family of a part's longest keyword, or None.

    Reads the first of ``mpn``, ``value``, ``lib_id`` that contains any keyword
    (case-insensitive substring). A tie in length between two families is None.
    ``families`` holds one detector's own tables; never pool families across
    detectors, since a part can belong to one family in each.
    """
    for field in ("mpn", "value", "lib_id"):
        text = (comp.get(field) or "").lower()
        if not text:
            continue
        best: dict[str, int] = {}
        for fam, keywords in families.items():
            n = max((len(k) for k in keywords if k in text), default=0)
            if n:
                best[fam] = n
        if best:
            top = max(best.values())
            winners = [f for f, n in best.items() if n == top]
            return winners[0] if len(winners) == 1 else None
    return None


# TVS/ESD part-name fragments: the protection-device and USB VBUS keyword sets, plus
# families without either word in their names (SRV05, SM712, CDSOT, USBUF/USBULC,
# NUF2/STF202 USB filters, AOZ89xx, H5VU, CM121x/CM123x, BSD5C, SP300x/SP301x,
# Wurth 82400xxx, CDDFN, ECMF).  Not "sp30": SP30xx also names RS-485 transceivers.
_PROTECTION_KEYWORDS = ("tvs", "esd", "pesd", "prtr", "usblc", "sp0", "tpd", "ip4", "rclamp",
                        "smaj", "smbj", "p6ke", "1.5ke", "lesd", "nup", "srv05", "sm712", "cdsot",
                        "usbuf", "usbulc", "nuf2", "stf202", "aoz89", "h5vu", "cm121", "cm123",
                        "bsd5c", "sp300", "sp301", "82400", "cddfn", "ecmf")
_DRIVER_PIN_TYPES = ("output", "tri_state", "power_out")


def _only_this_part_drives(ctx: AnalysisContext, ref: str, net: str) -> bool:
    """True when every other part on *net* has passive pins and *ref* has no input there.

    Such a net is a clamp's own supply/reference node (an ESD array's VP pin left open or
    decoupled), not a line the part protects.
    """
    pins = [p for p in ctx.nets.get(net, {}).get("pins", []) if not p["component"].startswith("#")]
    return (all(p.get("pin_type") == "passive" for p in pins if p["component"] != ref)
            and not any(p.get("pin_type") == "input" for p in pins if p["component"] == ref))


def is_protection_part(comp: dict, ctx: AnalysisContext, pair_suffixes) -> bool:
    """True when *comp* is a clamp (TVS/ESD diode or array, varistor), not a protected device.

    SPICE source symbols and unfitted parts (DNP or off the board) never count.  An IC without a
    protection name still counts when it only reaches ground, supplies, at most one node of
    its own (open or decoupled) and differential-pair lines (upper-case net suffixes in
    *pair_suffixes*) and drives none of them: an unnamed ESD array.
    """
    if (comp.get("dnp") or comp.get("on_board") is False
            or (comp.get("lib_id") or "").startswith("Simulation_SPICE:")):
        return False
    ctype = comp.get("type")
    if ctype in ("varistor", "surge_arrester"):
        return True
    if ctype not in ("diode", "ic", "other"):
        return False
    text = " ".join((comp.get("value") or "", comp.get("lib_id") or "", comp.get("mpn") or "")).lower()
    if any(k in text for k in _PROTECTION_KEYWORDS):
        return True
    if ctype != "ic":
        return False
    # A part that drives a pin is a transceiver or buffer even when its description
    # mentions its own ESD rating ("CAN transceiver with ESD protection").
    ref = comp.get("reference")
    if any(p.get("type") in _DRIVER_PIN_TYPES
           for c in ctx.components if c.get("reference") == ref for p in c.get("pins") or []):
        return False
    if classify_ic_function(comp.get("lib_id", ""), comp.get("value", ""),
                            comp.get("description", "")) == "protection":
        return True
    nets = {net for net, _ in ctx.ref_pins.get(ref, {}).values() if net}
    if not any(ctx.is_ground(n) for n in nets):
        return False
    suffixes = tuple(pair_suffixes)
    pair_lines = own_nodes = 0
    for n in sorted(nets):
        if ctx.is_ground(n) or ctx.is_power_net(n):
            continue
        if net_leaf(n).upper().endswith(suffixes):
            pair_lines += 1
        elif _only_this_part_drives(ctx, ref, n):
            own_nodes += 1
        else:
            return False
    # One own node is an array's VP/VBUS pin; an MCU or switch leaves several such nets.
    return pair_lines >= 2 and own_nodes <= 1


_PARALLEL_VALUE_NOUN = {"resistor": "resistors", "inductor": "inductors", "capacitor": "caps"}


def parallel_groups(ctx: AnalysisContext, comp_type: str) -> dict[str, dict]:
    """``{member_ref: group}`` for two-terminal parts of ``comp_type`` (resistor, inductor
    or capacitor) that share both nets; every such part has a group, alone or not.

    A group is ``{"refs": [sorted refs], "nets": (n1, n2), "value": float | None}``;
    ``refs[0]`` represents it.  Resistors and inductors combine as 1/sum(1/x), capacitors
    as sum(x); a lone member keeps its parsed value.  A member whose value did not parse
    makes the value None.  A DNP part beside a fitted one maps to a one-ref group marked
    ``"excluded"``.  Potentiometers and networks (not two pins) and parts sharing a
    reference with another part have no group.
    """
    cache = ctx.parallel_group_cache
    if comp_type in cache:
        return cache[comp_type]
    of_type = [c for c in ctx.components if c.get("type") == comp_type]
    ref_count: dict[str, int] = {}
    for comp in of_type:
        ref_count[comp["reference"]] = ref_count.get(comp["reference"], 0) + 1
    by_nets: dict[frozenset, dict[str, bool]] = {}
    nets_of: dict[frozenset, tuple[str, str]] = {}
    for comp in of_type:
        ref = comp["reference"]
        if ref_count[ref] != 1 or len(ctx.ref_pins.get(ref, {})) != 2:
            continue
        n1, n2 = ctx.get_two_pin_nets(ref)
        if not n1 or not n2 or n1 == n2:
            continue
        key = frozenset((n1, n2))
        by_nets.setdefault(key, {})[ref] = not comp.get("dnp")
        nets_of.setdefault(key, (n1, n2))
    groups: dict[str, dict] = {}
    for key, members in by_nets.items():
        fitted = sorted(r for r, fit in members.items() if fit)
        refs = fitted or sorted(members)
        if fitted:
            for r in sorted(set(members) - set(fitted)):
                groups[r] = {"refs": [r], "nets": nets_of[key], "value": None, "excluded": True}
        vals = [ctx.parsed_values.get(r) for r in refs]
        if any(v is None for v in vals):
            value = None
        elif len(vals) == 1:
            value = vals[0]
        elif comp_type == "capacitor":
            value = sum(vals)
        elif any(v <= 0 for v in vals):
            value = 0.0
        else:
            value = 1.0 / sum(1.0 / v for v in vals)
        group = {"refs": refs, "nets": nets_of[key], "value": value}
        for r in refs:
            groups[r] = group
    cache[comp_type] = groups
    return groups


def _group_of(ctx: AnalysisContext, ref: str) -> dict | None:
    comp = ctx.comp_lookup.get(ref)
    if not comp or comp.get("type") not in _PARALLEL_VALUE_NOUN:
        return None
    return parallel_groups(ctx, comp["type"]).get(ref)


def group_reps(ctx: AnalysisContext, components: list[dict]) -> list[dict]:
    """``components`` with each parallel group reduced to its representative (first ref);
    groups whose value is unknown and DNP parts beside fitted ones are dropped."""
    out = []
    seen: set[str] = set()
    for c in components:
        g = _group_of(ctx, c["reference"])
        if g is None:
            out.append(c)
            continue
        rep = g["refs"][0]
        if g.get("excluded") or g["value"] is None or rep in seen:
            continue
        seen.add(rep)
        out.append(ctx.comp_lookup[rep])
    return out


def group_value(ctx: AnalysisContext, ref: str) -> float | None:
    """The equivalent value of ``ref``'s parallel group, else its own parsed value."""
    g = _group_of(ctx, ref)
    return ctx.parsed_values.get(ref) if g is None else g["value"]


def group_members(ctx: AnalysisContext, ref: str) -> list[str]:
    """Every fitted member of ``ref``'s parallel group, sorted; ``[ref]`` when alone."""
    g = _group_of(ctx, ref)
    return list(g["refs"]) if g else [ref]


def group_part(ctx: AnalysisContext, ref: str, unit_key: str) -> dict:
    """The part dict a detector records for ``ref``'s parallel group:
    ``{"ref", "value", unit_key, "parallel_refs"?}`` (``parallel_refs`` only for more
    than one member; capacitor groups also keep ``parallel_caps``)."""
    g = _group_of(ctx, ref)
    if not g or len(g["refs"]) == 1:
        return {"ref": ref, "value": ctx.comp_lookup[ref]["value"], unit_key: group_value(ctx, ref)}
    comp_type = ctx.comp_lookup[ref]["type"]
    part = {"ref": g["refs"][0], "value": f"{len(g['refs'])} {_PARALLEL_VALUE_NOUN[comp_type]} parallel",
            unit_key: g["value"], "parallel_refs": list(g["refs"])}
    if comp_type == "capacitor":
        part["parallel_caps"] = list(g["refs"])
    return part


_SUPPLY_PIN_TYPES = ("power_in", "power_out")


def _is_led_node(ctx: AnalysisContext, pins: list[dict]) -> bool:
    """True when every part on a net other than resistors is an LED and no pin takes or
    gives power: the node LEDs share with their resistor, whatever its name."""
    types = [ctx.comp_lookup.get(p["component"], {}).get("type") for p in pins]
    return ("led" in types and all(t in ("led", "resistor") for t in types)
            and not any(p.get("pin_type") in _SUPPLY_PIN_TYPES for p in pins))


def is_led_rail(ctx: AnalysisContext, net: str) -> bool:
    """True when *net* is a supply rail as an LED sees it: a net with a power symbol, or a
    power-like name with more than three pins that is not an LED node (``+5V_LED`` shared
    by parallel LEDs and their resistor, ``VBUS_LED_A``)."""
    if net in ctx.known_power_rails:
        return True
    pins = ctx.nets.get(net, {}).get("pins", [])
    return ctx.is_power_net(net) and len(pins) > 3 and not _is_led_node(ctx, pins)


def led_string(ctx: AnalysisContext, ref: str) -> tuple[list[str], str | None, str | None]:
    """The series string *ref* belongs to: its LEDs in order, and the string's end nets on
    the side of pin 1 and of pin 2.  Two LEDs are in series when a net holds exactly their
    two pins.  A lone LED is a string of one ending on its own nets."""
    n1, n2 = ctx.get_two_pin_nets(ref)
    seen = {ref}

    def walk(net):
        chain = []
        while net and not ctx.is_ground(net) and not is_led_rail(ctx, net):
            pins = ctx.nets.get(net, {}).get("pins", [])
            others = [p["component"] for p in pins if p["component"] not in seen]
            if len(pins) != 2 or len(others) != 1:
                break
            nxt = others[0]
            if (ctx.comp_lookup.get(nxt, {}).get("type") != "led"
                    or len(ctx.ref_pins.get(nxt, {})) != 2):
                break
            seen.add(nxt)
            chain.append(nxt)
            a, b = ctx.get_two_pin_nets(nxt)
            net = b if a == net else a
        return chain, net

    up, end1 = walk(n1)
    down, end2 = walk(n2)
    return list(reversed(up)) + [ref] + down, end1, end2


def led_forward_voltage(comp: dict, table: dict[str, float], default: float = 2.0) -> float:
    """Forward voltage of the first colour in *table* named by the LED's value or lib_id."""
    combined = (comp.get("value", "") + " " + comp.get("lib_id", "")).lower()
    for color, vf in table.items():
        if color in combined:
            return vf
    return default
