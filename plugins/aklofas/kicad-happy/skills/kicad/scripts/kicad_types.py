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
from kicad_core.netnames import (
    configured_rail_voltage, is_ground_name, is_pin_guarded_signal, is_power_net_name, rail_matches,
)
from kicad_core.diagnostics import record
from kicad_core.values import AmbiguousValueSeparator, ambiguous_separator, parse_value

_AMBIGUOUS_RECORD_CAP = 20
_AMBIGUOUS_EFFECT = "value not parsed; value-based checks skip the part"


def index_components(components: list[dict], diagnostics: list | None = None
                     ) -> tuple[dict[str, dict], dict[str, float]]:
    comp_lookup = {c["reference"]: c for c in components}
    parsed_values: dict[str, float] = {}
    ambiguous: list[str] = []
    for c in components:
        val = parse_value(c.get("value", ""), component_type=c.get("type"))
        if val is not None:
            parsed_values[c["reference"]] = val
        elif (c.get("type") in ("resistor", "capacitor", "inductor")
              and ambiguous_separator(c.get("value", ""))):
            ambiguous.append(f"{c['reference']} value {c.get('value')!r}: separator may be a "
                             f"decimal mark or a thousands separator")
    if diagnostics is not None:
        for message in ambiguous[:_AMBIGUOUS_RECORD_CAP]:
            record(diagnostics, "kicad_types.index_components",
                   AmbiguousValueSeparator(message), _AMBIGUOUS_EFFECT)
        if len(ambiguous) > _AMBIGUOUS_RECORD_CAP:
            record(diagnostics, "kicad_types.index_components",
                   AmbiguousValueSeparator(f"{len(ambiguous) - _AMBIGUOUS_RECORD_CAP} more "
                                           f"ambiguous values not listed"),
                   _AMBIGUOUS_EFFECT)
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
        nq: ``NetlistQueries`` object for multi-hop net tracing.  Detectors
            require a context built by ``build_analysis_context``, which always
            installs ``nq``.
        diagnostics: Sink for guarded failures (``kicad_core.diagnostics.record``); the
            schematic pipeline merges it into the envelope's ``diagnostics``.
        rail_by_net: Rail voltages keyed by full net name, filled by the schematic
            pipeline; two instances of one sheet keep separate entries.
        rail_overrides: ``analysis.power_rails.voltage_overrides`` from the project
            config, ``{net_name: volts}``.
        rail_ignore: ``analysis.power_rails.ignore`` glob patterns.
        parallel_group_cache: ``detector_helpers.parallel_groups`` results per part type.

    Methods:
        is_power_net(name): True if *name* is a known power rail or matches
            common power net name patterns (VCC, +3V3, VBUS, etc.).
        is_ground(name): True if *name* matches ground patterns (GND, VSS, etc.).
        rail_voltage(net): The configured voltage, else the exact net's entry in
            ``rail_by_net``; None for an ignored rail.
        config_rail_voltage(net): The user's override for *net*, or None.
        rail_ignored(net): True if *net* matches an ``ignore`` pattern.
        rail_voltage_or(net, estimate): None for an ignored rail, else the override,
            else ``estimate(net)``.
        rail_source_fields(*nets): The finding key marking a config-sourced voltage.
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
    source: str = "unknown"
    nq: 'NetlistQueries | None' = field(default=None, repr=False)
    cache_dir: Path | None = field(default=None, repr=False)
    project_dir: str | None = field(default=None, repr=False)
    diagnostics: list = field(default_factory=list, repr=False)
    pin_guarded_signals: frozenset = field(default_factory=frozenset, repr=False)
    topology_rails: frozenset = field(default_factory=frozenset, repr=False)
    rail_by_net: dict[str, float] = field(default_factory=dict, repr=False)
    rail_overrides: dict[str, float] = field(default_factory=dict, repr=False)
    rail_ignore: tuple[str, ...] = field(default=(), repr=False)
    parallel_group_cache: dict = field(default_factory=dict, init=False, repr=False, compare=False)

    def is_power_net(self, name: str | None, *, by_pins: bool = True) -> bool:
        """*by_pins* False leaves out the rails known only by their pins (``topology_rails``)."""
        return name not in self.pin_guarded_signals and (
            is_power_net_name(name, self.known_power_rails)
            or (by_pins and name in self.topology_rails))

    def is_ground(self, name: str | None) -> bool:
        return is_ground_name(name, self.known_power_rails)

    def rail_voltage(self, net: str | None) -> float | None:
        """Voltage of the exact net *net* (full hierarchical name) from the rail map.

        The user's override comes first and an ignored rail has none. The map is built
        by the schematic pipeline (``build_rail_map``); a context it has not run on
        knows only the overrides.
        """
        return self.rail_voltage_or(net, self.rail_by_net.get)

    def config_rail_voltage(self, net: str | None) -> float | None:
        """The configured voltage for *net* (``configured_rail_voltage``), or None."""
        return configured_rail_voltage(self.rail_overrides, net)

    def rail_ignored(self, net: str | None) -> bool:
        return rail_matches(self.rail_ignore, net)

    def rail_source_fields(self, *nets: str | None) -> dict:
        """``{"rail_voltage_source": "config"}`` for a finding whose rail voltage came
        from a config override on one of *nets*, else ``{}``."""
        if any(not self.rail_ignored(n) and self.config_rail_voltage(n) is not None
               for n in nets):
            return {"rail_voltage_source": "config"}
        return {}

    def rail_voltage_or(self, net: str | None, estimate) -> float | None:
        """None for an ignored rail, else the configured voltage, else ``estimate(net)``."""
        if not net:
            return None
        if self.rail_ignored(net):
            return None
        v = self.config_rail_voltage(net)
        return v if v is not None else estimate(net)

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


def pin_guarded_signal_nets(nets: dict[str, dict], comp_lookup: dict[str, dict],
                            power_rails: set[str] | None = None) -> frozenset[str]:
    """Nets named VPP/VM that carry an IC signal pin and no power pin (is_pin_guarded_signal)."""
    rails = power_rails or set()
    return frozenset(
        name for name, info in nets.items()
        if name not in rails and is_pin_guarded_signal(name, [
            (p.get("pin_type"), (comp_lookup.get(p.get("component")) or {}).get("type") == "ic")
            for p in info.get("pins", [])]))


def build_analysis_context(components: list[dict], nets: dict[str, dict], lib_symbols: dict, *,
                           no_connects: list[dict] | None = None,
                           source: str = "unknown",
                           cache_dir: Path | None = None, project_dir: str | None = None,
                           known_power_rails: set[str] | None = None,
                           power_rails_config: dict | None = None) -> AnalysisContext:
    """The single construction point for production contexts.

    Builds ``pin_net`` and every index, installs the ``NetlistQueries`` layer and
    returns a context no detector has to complete. ``known_power_rails`` overrides
    the power-symbol scan (synthetic fixtures); an explicit set (including an empty
    one) is used as given; ``no_connects`` is kept by reference. ``power_rails_config``
    is the project config's ``analysis.power_rails`` (its ``voltage_overrides`` and
    ``ignore`` reach every detector).
    """
    pin_net = build_pin_to_net_map(nets)
    diagnostics: list = []
    comp_lookup, parsed_values = index_components(components, diagnostics)
    rails = scan_power_rails(nets) if known_power_rails is None else known_power_rails
    ctx = AnalysisContext(
        components=components, nets=nets, lib_symbols=lib_symbols, pin_net=pin_net,
        comp_lookup=comp_lookup, parsed_values=parsed_values, known_power_rails=rails,
        ref_pins=index_ref_pins(pin_net),
        no_connects=no_connects if no_connects is not None else [],
        source=source,
        cache_dir=cache_dir, project_dir=project_dir, diagnostics=diagnostics,
        pin_guarded_signals=pin_guarded_signal_nets(nets, comp_lookup, rails),
    )
    if power_rails_config:
        ctx.rail_overrides = {
            k: v for k, v in (power_rails_config.get("voltage_overrides") or {}).items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)}
        ctx.rail_ignore = tuple(
            p for p in (power_rails_config.get("ignore") or ()) if isinstance(p, str))
    from schematic.net_analysis import topology_rail_nets  # local: net_analysis imports this module
    ctx.topology_rails = topology_rail_nets(
        nets, comp_lookup, ctx.ref_pins, ctx.is_power_net, ctx.is_ground)
    from netlist_queries import NetlistQueries  # local: netlist_queries annotates with this class
    ctx.nq = NetlistQueries(ctx)
    return ctx
