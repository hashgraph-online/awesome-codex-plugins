"""
Typed data structures for KiCad analysis.

Provides AnalysisContext — the shared state object passed between all
analysis functions, replacing repeated comp_lookup/parsed_values/known_power_rails
construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from kicad_core.model import PinNetEntry
from kicad_core.netquery import build_pin_to_net_map
from kicad_core.netnames import is_ground_name, is_power_net_name
from kicad_core.values import parse_value


def index_components(components: list[dict]) -> tuple[dict[str, dict], dict[str, float]]:
    comp_lookup = {c["reference"]: c for c in components}
    parsed_values: dict[str, float] = {}
    for c in components:
        val = parse_value(c.get("value", ""), component_type=c.get("type"))
        if val is not None:
            parsed_values[c["reference"]] = val
    return comp_lookup, parsed_values


def scan_power_rails(nets: dict[str, dict]) -> set[str]:
    rails: set[str] = set()
    for net_name, net_info in nets.items():
        for p in net_info.get("pins", []):
            if p["component"].startswith("#PWR") or p["component"].startswith("#FLG"):
                rails.add(net_name)
                break
    return rails


def index_ref_pins(pin_net: dict) -> dict[str, dict[str, PinNetEntry]]:
    rp: dict[str, dict[str, PinNetEntry]] = {}
    for (comp_ref, pin_num), val in pin_net.items():
        rp.setdefault(comp_ref, {})[pin_num] = val
    return rp


@dataclass
class AnalysisContext:
    """Shared state passed to all 40+ signal and domain detector functions.

    Construct through ``build_analysis_context()``; a directly constructed context gets
    no derived indexes.  Built after components, nets, and pin_net are fully resolved.  Provides indexed lookups and helper methods so
    detectors don't rebuild these structures individually.

    Attributes:
        components: All placed components (excluding power symbols/flags).
            Each dict has: reference, value, type, lib_id, footprint,
            properties, pins, and optionally mpn, datasheet.
        nets: Net connectivity graph.  ``{net_name: {"pins": [{"component": ref,
            "pin_number": num, "pin_name": name, "x": float, "y": float}], ...}}``.
        lib_symbols: Library symbol definitions extracted from the schematic's
            embedded ``lib_symbols`` section.  ``{lib_id: {value, pins, ...}}``.
        pin_net: Pin-to-net mapping.  ``{(ref, pin_number): (net_name, net_record)}`` — the full net record, not a pin name.
            Covers every pin on every placed component.
        comp_lookup: Quick component lookup by reference.  ``{ref: component_dict}``.
            Built from *components* by ``build_analysis_context``.
        parsed_values: Parsed SI values (ohms, farads, henries) per component.
            ``{ref: float}``.  Only components whose value string parses
            successfully are included.  Built by ``build_analysis_context``.
        known_power_rails: Net names connected to power symbols (``#PWR``, ``#FLG``).
            Used by ``is_power_net()`` to distinguish power rails from signal nets.
        ref_pins: Per-component pin map.  ``{ref: {pin_number: (net_name, net_record)}}``.
            Derived from *pin_net* for quick per-component pin enumeration.
        no_connects: List of no-connect markers from the schematic.
        generator_version: KiCad version string (e.g., ``"9.0.1"``).
        nq: ``NetlistQueries`` object for multi-hop net tracing.  Detectors
            require a context built by ``build_analysis_context``, which always
            installs ``nq``.
        diagnostics: Sink for guarded failures (``kicad_core.diagnostics.record``); the
            schematic pipeline merges it into the envelope's ``diagnostics``.

    Methods:
        is_power_net(name): True if *name* is a known power rail or matches
            common power net name patterns (VCC, +3V3, VBUS, etc.).
        is_ground(name): True if *name* matches ground patterns (GND, VSS, etc.).
        get_two_pin_nets(ref): Returns ``(net1, net2)`` for a 2-pin component.
            Handles standard "1"/"2" numbering and falls back to enumerating
            all pins for non-standard numbering (Eagle imports, diodes A/K).
    """

    components: list[dict]
    nets: dict[str, dict]
    lib_symbols: dict
    pin_net: dict[tuple[str, str], PinNetEntry]
    comp_lookup: dict[str, dict] = field(default_factory=dict)
    parsed_values: dict[str, float] = field(default_factory=dict)
    known_power_rails: set[str] = field(default_factory=set)
    ref_pins: dict[str, dict[str, PinNetEntry]] = field(default_factory=dict)
    no_connects: list[dict] = field(default_factory=list)
    generator_version: str = "unknown"
    source: str = "unknown"
    nq: 'NetlistQueries | None' = field(default=None, repr=False)
    cache_dir: Path | None = field(default=None, repr=False)
    project_dir: str | None = field(default=None, repr=False)
    diagnostics: list = field(default_factory=list, repr=False)

    def is_power_net(self, name: str | None) -> bool:
        return is_power_net_name(name, self.known_power_rails)

    def is_ground(self, name: str | None) -> bool:
        return is_ground_name(name)

    def get_two_pin_nets(self, ref: str) -> tuple[str | None, str | None]:
        n1, _ = self.pin_net.get((ref, "1"), (None, None))
        n2, _ = self.pin_net.get((ref, "2"), (None, None))
        if n1 is not None and n2 is not None:
            return n1, n2
        # Fallback for non-"1"/"2" pin numbering (Eagle imports, diodes A/K, etc.)
        pins = self.ref_pins.get(ref, {})
        if len(pins) == 2:
            nets = [net for net, _ in pins.values()]
            return nets[0], nets[1]
        return n1, n2


def build_analysis_context(components: list[dict], nets: dict[str, dict], lib_symbols: dict, *,
                           no_connects: list[dict] | None = None,
                           generator_version: str = "unknown", source: str = "unknown",
                           cache_dir: Path | None = None, project_dir: str | None = None,
                           known_power_rails: set[str] | None = None) -> AnalysisContext:
    """The single construction point for production contexts (spec §4.2).

    Builds ``pin_net`` and every index, installs the ``NetlistQueries`` layer and
    returns a context no detector has to complete. ``known_power_rails`` overrides
    the power-symbol scan (synthetic fixtures); an explicit set (including an empty
    one) is used as given; ``no_connects`` is kept by reference.
    """
    pin_net = build_pin_to_net_map(nets)
    comp_lookup, parsed_values = index_components(components)
    rails = scan_power_rails(nets) if known_power_rails is None else known_power_rails
    ctx = AnalysisContext(
        components=components, nets=nets, lib_symbols=lib_symbols, pin_net=pin_net,
        comp_lookup=comp_lookup, parsed_values=parsed_values, known_power_rails=rails,
        ref_pins=index_ref_pins(pin_net),
        no_connects=no_connects if no_connects is not None else [],
        generator_version=generator_version, source=source,
        cache_dir=cache_dir, project_dir=project_dir, diagnostics=[],
    )
    from netlist_queries import NetlistQueries  # local: netlist_queries annotates with this class
    ctx.nq = NetlistQueries(ctx)
    return ctx
