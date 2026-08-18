"""
Typed data structures for KiCad analysis.

Provides AnalysisContext — the shared state object passed between all
analysis functions, replacing repeated comp_lookup/parsed_values/known_power_rails
construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from kicad_utils import is_ground_name, is_power_net_name, parse_value


@dataclass
class AnalysisContext:
    """Shared state passed to all 40+ signal and domain detector functions.

    Built once in ``analyze_schematic()`` after components, nets, and pin_net
    are fully resolved.  Provides indexed lookups and helper methods so
    detectors don't rebuild these structures individually.

    Attributes:
        components: All placed components (excluding power symbols/flags).
            Each dict has: reference, value, type, lib_id, footprint,
            properties, pins, and optionally mpn, datasheet.
        nets: Net connectivity graph.  ``{net_name: {"pins": [{"component": ref,
            "pin_number": num, "pin_name": name, "x": float, "y": float}], ...}}``.
        lib_symbols: Library symbol definitions extracted from the schematic's
            embedded ``lib_symbols`` section.  ``{lib_id: {value, pins, ...}}``.
        pin_net: Pin-to-net mapping.  ``{(ref, pin_number): (net_name, pin_info)}``.
            Covers every pin on every placed component.
        comp_lookup: Quick component lookup by reference.  ``{ref: component_dict}``.
            Auto-built from *components* in ``__post_init__``.
        parsed_values: Parsed SI values (ohms, farads, henries) per component.
            ``{ref: float}``.  Only components whose value string parses
            successfully are included.  Auto-built in ``__post_init__``.
        known_power_rails: Net names connected to power symbols (``#PWR``, ``#FLG``).
            Used by ``is_power_net()`` to distinguish power rails from signal nets.
        ref_pins: Per-component pin map.  ``{ref: {pin_number: (net_name, pin_info)}}``.
            Derived from *pin_net* for quick per-component pin enumeration.
        no_connects: List of no-connect markers from the schematic.
        generator_version: KiCad version string (e.g., ``"9.0.1"``).
        nq: Optional high-performance ``NetlistQueries`` object for multi-hop
            net tracing.  Initialized separately when available.
        hierarchy_context: Cross-sheet context for sub-sheet analysis.  None when
            analyzing a root schematic or when hierarchy discovery is disabled.
            When present, contains: root_schematic, target_sheet, sheets_in_project,
            cross_sheet_nets (per hierarchical label: external components, power rail
            status, connected sheets), project_power_rails, and
            reference_corrections_applied.

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
    pin_net: dict[tuple[str, str], tuple[str | None, str | None]]
    comp_lookup: dict[str, dict] = field(default_factory=dict)
    parsed_values: dict[str, float] = field(default_factory=dict)
    known_power_rails: set[str] = field(default_factory=set)
    ref_pins: dict[str, dict[str, tuple[str | None, str | None]]] = field(default_factory=dict)
    no_connects: list[dict] = field(default_factory=list)
    generator_version: str = "unknown"
    source: str = "unknown"
    nq: 'NetlistQueries | None' = field(default=None, repr=False)
    hierarchy_context: dict | None = field(default=None, repr=False)
    cache_dir: Path | None = field(default=None, repr=False)
    design_context: dict | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if not self.comp_lookup:
            self.comp_lookup = {c["reference"]: c for c in self.components}
        if not self.parsed_values:
            for c in self.components:
                val = parse_value(c.get("value", ""), component_type=c.get("type"))
                if val is not None:
                    self.parsed_values[c["reference"]] = val
        if not self.known_power_rails:
            for net_name, net_info in self.nets.items():
                for p in net_info.get("pins", []):
                    if p["component"].startswith("#PWR") or p["component"].startswith("#FLG"):
                        self.known_power_rails.add(net_name)
                        break
        if not self.ref_pins:
            rp: dict[str, dict[str, tuple[str | None, str | None]]] = {}
            for (comp_ref, pin_num), val in self.pin_net.items():
                rp.setdefault(comp_ref, {})[pin_num] = val
            self.ref_pins = rp

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
