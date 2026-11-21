"""
Netlist query layer for KiCad schematic analysis.

Provides efficient indexed queries over the netlist produced by
build_net_map().  Constructed from an AnalysisContext after the net map
is ready.  NOT a new solver — a query layer on top of existing data.

Usage:
    from netlist_queries import NetlistQueries
    ctx.nq = NetlistQueries(ctx)
    ics = ctx.nq.ics_on_net("VCC", exclude_ref="U1")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kicad_types import AnalysisContext


class NetlistQueries:
    """Efficient query layer over build_net_map() output.

    Pre-builds one index from ctx.nets in a single pass:
      _nets_by_comp  — ref -> set of net names
    """

    def __init__(self, ctx: AnalysisContext) -> None:
        self.ctx = ctx
        self._nets_by_comp: dict[str, set[str]] = {}
        self._build_indexes()

    def _build_indexes(self) -> None:
        """Single pass over ctx.nets to populate the index."""
        ctx = self.ctx
        for net_name, net_info in ctx.nets.items():
            for p in net_info.get("pins", []):
                ref = p["component"]
                # Skip power/flag symbols — they're connectivity markers
                if ref.startswith("#PWR") or ref.startswith("#FLG"):
                    continue
                comp = ctx.comp_lookup.get(ref)
                if not comp:
                    continue
                self._nets_by_comp.setdefault(ref, set()).add(net_name)

    # ------------------------------------------------------------------
    # Direct queries
    # ------------------------------------------------------------------

    def components_on_net(self, net_name: str,
                          exclude_refs: set[str] | None = None,
                          comp_type: str | None = None) -> list[dict]:
        """All components on a net, optionally filtered by type.

        Returns enriched dicts:
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

    # ------------------------------------------------------------------
    # Typed neighbor helpers
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Multi-hop tracing
    # ------------------------------------------------------------------

    def trace_through(self, start_net: str, through_ref: str) -> list[str]:
        """Follow a signal through a component to its other net(s).

        For 2-pin components, returns exactly one net.
        For multi-pin, returns all nets except start_net.
        """
        other_nets = self._nets_by_comp.get(through_ref, set())
        return sorted(n for n in other_nets if n != start_net)
