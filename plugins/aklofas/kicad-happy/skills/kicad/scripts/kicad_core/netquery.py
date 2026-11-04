"""Pin/net index primitives (kicad_core). The two net helpers that lived in kicad_utils, the index builders and BridgeFact."""

from dataclasses import dataclass

from kicad_core.model import Net, PinNetEntry
from kicad_core.values import parse_value


def build_pin_to_net_map(nets: dict[str, Net]) -> dict[tuple[str, str], PinNetEntry]:
    """Build a reverse map: (component, pin_number) -> (net_name, net_info)."""
    pin_net = {}
    for net_name, net_info in nets.items():
        for p in net_info["pins"]:
            pin_net[(p["component"], p["pin_number"])] = (net_name, net_info)
    return pin_net


def get_two_pin_nets(pin_net: dict, ref: str) -> tuple[str | None, str | None]:
    """Get the two nets a 2-pin component connects to.

    Takes pin_net map explicitly instead of closing over it.
    Falls back to enumerating all pins when "1"/"2" aren't found.
    """
    n1, _ = pin_net.get((ref, "1"), (None, None))
    n2, _ = pin_net.get((ref, "2"), (None, None))
    if n1 is not None and n2 is not None:
        return n1, n2
    # Fallback for non-"1"/"2" pin numbering (Eagle imports, diodes A/K, etc.)
    ref_entries = {k[1]: v for k, v in pin_net.items() if k[0] == ref}
    if len(ref_entries) == 2:
        nets = [net for net, _ in ref_entries.values()]
        return nets[0], nets[1]
    return n1, n2


def build_net_id_map(pcb):
    """Return {net_id (int): net_name (str)} from PCB JSON.

    Handles both the current flat form pcb['nets'] = {"6": "GND", ...}
    and the legacy nested form pcb['nets']['net_info'] = [{"id": 6, ...}, ...].
    """
    nets = pcb.get('nets', {})
    out = {}
    if isinstance(nets, dict):
        for k, v in nets.items():
            if isinstance(v, str):
                try:
                    out[int(k)] = v
                except (ValueError, TypeError):
                    continue
        if out:
            return out
        for ni in nets.get('net_info', []) or []:
            try:
                out[int(ni.get('id', -1))] = ni.get('name', '')
            except (ValueError, TypeError):
                continue
    return out


def build_ref_pins(nets: dict) -> dict[str, list[tuple[str, str, str]]]:
    """ref -> [(pin_number, net_name, pin_type)] in net-map order.

    This is the per-ref hop table the PP-001 walk uses; the order is the order
    ``build_net_map`` emitted the nets and their pins, which the walk depends on.
    """
    ref_pins: dict[str, list[tuple[str, str, str]]] = {}
    for net_name, net_info in nets.items():
        for p in net_info.get("pins", []):
            ref = p.get("component") or ""
            if not ref:
                continue
            ref_pins.setdefault(ref, []).append(
                (str(p.get("pin_number", "")), net_name,
                 str(p.get("pin_type", ""))))
    return ref_pins


@dataclass(frozen=True)
class BridgeFact:
    """What is known about one DC-bridge-capable component (U3).

    ref:           component reference
    nets:          endpoint nets in net-map order (jumper detections: the detection's ``nets``)
    kind:          "jumper" | "resistor" | "inductor" | "ferrite_bead" | "fuse"
    default_state: jumpers: the detection's ``default_state`` ("bridged" / "open" / other), else None
    resistance:    resistors: parsed ohms, 0.0 for a bare zero-ohm spelling, None when unparsable; else None
    """
    ref: str
    nets: tuple[str, ...]
    kind: str
    default_state: str | None
    resistance: float | None


@dataclass(frozen=True)
class BridgeFacts:
    """Two views over the same facts. ``by_ref`` is keyed by component (the PP-001 predicate's
    input; the component's own type decides its kind). ``jumpers`` lists one fact per
    solder-jumper detection in detection order (the RS audit's input), whatever the
    component's type is."""
    by_ref: dict[str, BridgeFact]
    jumpers: list[BridgeFact]


_BRIDGE_KINDS = ("inductor", "ferrite_bead", "fuse", "resistor", "jumper")
_ZERO_OHM_SPELLINGS = ("0", "0r", "0ohm", "0ohms")


def build_bridge_facts(components: list[dict],
                       ref_pins: dict[str, list[tuple[str, str, str]]],
                       solder_jumpers: list[dict] | None) -> BridgeFacts:
    """Build the shared DC-bridge facts for the RS and PP audits.

    Acceptance stays with each audit: RS accepts two-net jumpers in state
    bridged/open; PP accepts inductors, ferrite beads, fuses, resistors <= 1 Ω
    and bridged jumpers. This function only records facts.
    """
    detections = {}
    for sj in (solder_jumpers or []):
        detections.setdefault(sj.get("reference"), sj)
    by_ref: dict[str, BridgeFact] = {}
    for c in components:
        ref = c.get("reference") or ""
        t = (c.get("type") or c.get("category") or "").lower()
        if not ref or t not in _BRIDGE_KINDS:
            if ref:
                by_ref.pop(ref, None)   # duplicate refs: the last component wins, as the old dict did
            continue
        nets = tuple(dict.fromkeys(net for _pn, net, _pt in ref_pins.get(ref, [])))
        if t == "jumper":
            sj = detections.get(ref)
            state = sj.get("default_state") if sj else None
            if sj and sj.get("nets"):
                nets = tuple(sj.get("nets"))
            by_ref[ref] = BridgeFact(ref, nets, "jumper", state, None)
            continue
        resistance = None
        if t == "resistor":
            v = parse_value(c.get("value", ""), component_type="resistor")
            if v is None:
                val = (c.get("value") or "").strip().lower().replace(" ", "")
                resistance = 0.0 if val in _ZERO_OHM_SPELLINGS else None
            else:
                resistance = v
        by_ref[ref] = BridgeFact(ref, nets, t, None, resistance)
    jumpers = [BridgeFact(sj.get("reference", ""), tuple(sj.get("nets") or []), "jumper",
                          sj.get("default_state"), None)
               for sj in (solder_jumpers or [])]
    return BridgeFacts(by_ref, jumpers)
