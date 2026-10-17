"""
Netlist query layer for KiCad schematic analysis.

Provides efficient indexed queries over the netlist produced by
build_net_map().  Constructed from an AnalysisContext after the net map
is ready.  NOT a new solver — a query layer on top of existing data.

Usage:
    from netlist_queries import NetlistQueries
    ctx.nq = NetlistQueries(ctx)
    caps = ctx.nq.capacitors_on_net("VCC", exclude_ref="U1")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kicad_types import AnalysisContext


class NetlistQueries:
    """Efficient query layer over build_net_map() output.

    Pre-builds three indexes from ctx.nets in a single pass:
      _nets_by_comp  — ref -> set of net names
      _comps_by_net  — net_name -> set of refs
      _type_index    — net_name -> {comp_type -> [refs]}
    """

    def __init__(self, ctx: AnalysisContext) -> None:
        self.ctx = ctx
        self._nets_by_comp: dict[str, set[str]] = {}
        self._comps_by_net: dict[str, set[str]] = {}
        self._type_index: dict[str, dict[str, list[str]]] = {}
        self._build_indexes()

    def _build_indexes(self) -> None:
        """Single pass over ctx.nets to populate all indexes."""
        ctx = self.ctx
        for net_name, net_info in ctx.nets.items():
            comp_set: set[str] = set()
            type_map: dict[str, list[str]] = {}
            for p in net_info.get("pins", []):
                ref = p["component"]
                # Skip power/flag symbols — they're connectivity markers
                if ref.startswith("#PWR") or ref.startswith("#FLG"):
                    continue
                comp = ctx.comp_lookup.get(ref)
                if not comp:
                    continue
                comp_set.add(ref)
                self._nets_by_comp.setdefault(ref, set()).add(net_name)
                ctype = comp["type"]
                type_map.setdefault(ctype, [])
                # Avoid duplicate refs in type list for same net
                if ref not in type_map[ctype]:
                    type_map[ctype].append(ref)
            self._comps_by_net[net_name] = comp_set
            self._type_index[net_name] = type_map

    # ------------------------------------------------------------------
    # Direct queries
    # ------------------------------------------------------------------

    def components_on_net(self, net_name: str,
                          exclude_refs: set[str] | None = None,
                          comp_type: str | None = None) -> list[dict]:
        """All components on a net, optionally filtered by type.

        Returns enriched dicts matching _get_net_components format:
        {reference, type, value, pin_name, pin_number}.
        One entry per pin (not per component) for components with
        multiple pins on the same net.
        """
        net_info = self.ctx.nets.get(net_name)
        if not net_info:
            return []
        exclude = exclude_refs or set()
        result = []
        for p in net_info["pins"]:
            ref = p["component"]
            if ref in exclude:
                continue
            if ref.startswith("#PWR") or ref.startswith("#FLG"):
                continue
            comp = self.ctx.comp_lookup.get(ref)
            if not comp:
                continue
            if comp_type and comp["type"] != comp_type:
                continue
            result.append({
                "reference": ref,
                "type": comp["type"],
                "value": comp["value"],
                "pin_name": p.get("pin_name", ""),
                "pin_number": p["pin_number"],
            })
        return result

    def pins_on_net(self, net_name: str) -> list[dict]:
        """All pin dicts on a net (raw from ctx.nets)."""
        net_info = self.ctx.nets.get(net_name)
        return net_info["pins"] if net_info else []

    def nets_for_component(self, ref: str) -> dict[str, str]:
        """Map of pin_number -> net_name for all pins of a component."""
        pins = self.ctx.ref_pins.get(ref, {})
        return {pnum: net for pnum, (net, _) in pins.items() if net}

    def net_for_pin(self, ref: str, pin_number: str) -> str | None:
        """Net name for a specific pin."""
        result = self.ctx.pin_net.get((ref, pin_number))
        return result[0] if result else None

    def are_connected(self, ref1: str, pin1: str,
                      ref2: str, pin2: str) -> bool:
        """True if two pins are on the same net."""
        n1 = self.net_for_pin(ref1, pin1)
        n2 = self.net_for_pin(ref2, pin2)
        return n1 is not None and n1 == n2

    # ------------------------------------------------------------------
    # Typed neighbor helpers
    # ------------------------------------------------------------------

    def resistors_on_net(self, net_name: str,
                         exclude_ref: str = '') -> list[dict]:
        """Resistors on a net."""
        excl = {exclude_ref} if exclude_ref else None
        return self.components_on_net(net_name, exclude_refs=excl,
                                     comp_type='resistor')

    def capacitors_on_net(self, net_name: str,
                          exclude_ref: str = '') -> list[dict]:
        """Capacitors on a net."""
        excl = {exclude_ref} if exclude_ref else None
        return self.components_on_net(net_name, exclude_refs=excl,
                                     comp_type='capacitor')

    def inductors_on_net(self, net_name: str,
                         exclude_ref: str = '') -> list[dict]:
        """Inductors on a net."""
        excl = {exclude_ref} if exclude_ref else None
        return self.components_on_net(net_name, exclude_refs=excl,
                                     comp_type='inductor')

    def ics_on_net(self, net_name: str,
                   exclude_ref: str = '') -> list[dict]:
        """ICs on a net."""
        excl = {exclude_ref} if exclude_ref else None
        return self.components_on_net(net_name, exclude_refs=excl,
                                     comp_type='ic')

    def diodes_on_net(self, net_name: str,
                      exclude_ref: str = '') -> list[dict]:
        """Diodes on a net."""
        excl = {exclude_ref} if exclude_ref else None
        return self.components_on_net(net_name, exclude_refs=excl,
                                     comp_type='diode')

    # ------------------------------------------------------------------
    # Fanout and topology
    # ------------------------------------------------------------------

    def net_fanout(self, net_name: str) -> int:
        """Number of unique component refs on a net (excludes power symbols)."""
        return len(self._comps_by_net.get(net_name, set()))

    def is_point_to_point(self, net_name: str) -> bool:
        """True if net connects exactly 2 component pins."""
        net_info = self.ctx.nets.get(net_name)
        if not net_info:
            return False
        real_pins = [p for p in net_info["pins"]
                     if not p["component"].startswith("#PWR")
                     and not p["component"].startswith("#FLG")]
        return len(real_pins) == 2

    def is_bus_net(self, net_name: str, threshold: int = 6) -> bool:
        """True if net connects >= threshold components."""
        return self.net_fanout(net_name) >= threshold

    def shared_nets(self, ref1: str, ref2: str) -> list[str]:
        """All nets that both components touch."""
        nets1 = self._nets_by_comp.get(ref1, set())
        nets2 = self._nets_by_comp.get(ref2, set())
        return sorted(nets1 & nets2)

    # ------------------------------------------------------------------
    # Multi-hop tracing
    # ------------------------------------------------------------------

    def trace_through(self, start_net: str, through_ref: str) -> list[str]:
        """Follow a signal through a component to its other net(s).

        For 2-pin components, returns exactly one net.
        For multi-pin, returns all nets except start_net.
        """
        other_nets = self._nets_by_comp.get(through_ref, set())
        return [n for n in other_nets if n != start_net]

    def trace_path(self, start_ref: str, start_pin: str,
                   max_hops: int = 5,
                   follow_types: set[str] | None = None,
                   skip_power_gnd: bool = True) -> list[dict]:
        """BFS trace from a pin through intermediate components.

        Each hop follows through a component's other pins to new nets.
        follow_types limits which component types to traverse.
        Returns list of {net_name, component, pin_in, pin_out, hop}.
        """
        start_net = self.net_for_pin(start_ref, start_pin)
        if not start_net:
            return []

        path: list[dict] = []
        visited_nets: set[str] = {start_net}
        visited_refs: set[str] = {start_ref}
        frontier = [(start_net, 0)]

        while frontier:
            next_frontier: list[tuple[str, int]] = []
            for current_net, hop in frontier:
                if hop >= max_hops:
                    continue
                for p in self.ctx.nets.get(current_net, {}).get("pins", []):
                    ref = p["component"]
                    if ref in visited_refs:
                        continue
                    if ref.startswith("#PWR") or ref.startswith("#FLG"):
                        continue
                    comp = self.ctx.comp_lookup.get(ref)
                    if not comp:
                        continue
                    ctype = comp["type"]
                    # Record reaching this component
                    if follow_types and ctype not in follow_types:
                        # Terminal — record but don't traverse through
                        path.append({
                            "net_name": current_net,
                            "component": ref,
                            "type": ctype,
                            "pin_in": p["pin_number"],
                            "hop": hop + 1,
                            "terminal": True,
                        })
                        continue
                    visited_refs.add(ref)
                    # Follow through to other nets
                    for other_net in self.trace_through(current_net, ref):
                        if other_net in visited_nets:
                            continue
                        if skip_power_gnd and (
                            self.ctx.is_power_net(other_net)
                            or self.ctx.is_ground(other_net)
                        ):
                            continue
                        visited_nets.add(other_net)
                        path.append({
                            "net_name": other_net,
                            "component": ref,
                            "type": ctype,
                            "pin_in": p["pin_number"],
                            "hop": hop + 1,
                            "terminal": False,
                        })
                        next_frontier.append((other_net, hop + 1))
            frontier = next_frontier
        return path

    def components_within_hops(self, ref: str, max_hops: int = 2,
                               comp_type: str | None = None) -> list[dict]:
        """All components reachable within N net-hops from ref.

        hop 0 = components sharing a direct net with ref.
        """
        result: list[dict] = []
        seen_refs: set[str] = {ref}
        frontier_nets = self._nets_by_comp.get(ref, set()).copy()
        visited_nets: set[str] = set(frontier_nets)

        for _hop in range(max_hops + 1):
            next_nets: set[str] = set()
            for net_name in frontier_nets:
                for comp_ref in self._comps_by_net.get(net_name, set()):
                    if comp_ref in seen_refs:
                        continue
                    seen_refs.add(comp_ref)
                    comp = self.ctx.comp_lookup.get(comp_ref)
                    if not comp:
                        continue
                    if comp_type and comp["type"] != comp_type:
                        continue
                    result.append({
                        "reference": comp_ref,
                        "type": comp["type"],
                        "value": comp["value"],
                        "hop": _hop,
                    })
                    # Expand to this component's other nets for next hop
                    for n in self._nets_by_comp.get(comp_ref, set()):
                        if n not in visited_nets:
                            visited_nets.add(n)
                            next_nets.add(n)
            frontier_nets = next_nets

        return result

    # ------------------------------------------------------------------
    # Net name annotations for downstream consumers
    # ------------------------------------------------------------------

    def pin_net_annotations(self) -> dict[str, dict[str, str]]:
        """Generate net name mapping for rendering at pin endpoints.

        Returns {ref: {pin_number: net_name}} for every pin with a
        named net (not __unnamed_*).
        """
        result: dict[str, dict[str, str]] = {}
        for ref, pins in self.ctx.ref_pins.items():
            if ref.startswith("#PWR") or ref.startswith("#FLG"):
                continue
            pin_map: dict[str, str] = {}
            for pnum, (net_name, _) in pins.items():
                if net_name and not net_name.startswith("__unnamed_"):
                    pin_map[pnum] = net_name
            if pin_map:
                result[ref] = pin_map
        return result

    # ------------------------------------------------------------------
    # Integrity checks
    # ------------------------------------------------------------------

    def floating_pins(self) -> list[dict]:
        """Pins on unnamed nets with fanout=1 (likely unconnected).

        Excludes pins with no-connect markers.
        """
        result: list[dict] = []
        for net_name, net_info in self.ctx.nets.items():
            if not net_name.startswith("__unnamed_"):
                continue
            if net_info.get("no_connect"):
                continue
            pins = net_info.get("pins", [])
            real_pins = [p for p in pins
                         if not p["component"].startswith("#PWR")
                         and not p["component"].startswith("#FLG")]
            if len(real_pins) == 1:
                p = real_pins[0]
                result.append({
                    "component": p["component"],
                    "pin_number": p["pin_number"],
                    "pin_name": p.get("pin_name", ""),
                    "pin_type": p.get("pin_type", ""),
                    "net_name": net_name,
                })
        return result
