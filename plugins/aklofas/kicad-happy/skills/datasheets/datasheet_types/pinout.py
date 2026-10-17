"""Pin + AltFunction dataclasses + Pinout wrapper class.

Mirrors pinout.schema.json. Pin shape is flagged x-still-calibrating
through v1.4 — shape may shift with real-corpus feedback before v1.5.

Pinout is NOT a dataclass because its JSON root is a bare array. It
wraps list[Pin] and exposes .find / .in_domain / __iter__ / __len__
for consumer ergonomics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .spec_value import Evidence, SpecValue


@dataclass
class AltFunction:
    """One alternate function on a muxed pin."""
    name: str = field(metadata={
        "description": "Alternate function name (e.g. 'USART1_TX', 'SPI2_MISO')."})
    peripheral: str = field(metadata={
        "description": "Peripheral family (e.g. 'USART1'). Detectors filter on this."})
    role: Optional[str] = field(default=None, metadata={
        "description": "Role within the peripheral ('TX', 'MISO', ...). None when N/A."})
    af_code: Optional[str] = field(default=None, metadata={
        "description": "Datasheet-specific AF selector (e.g. 'AF7'). Opaque to detectors."})


@dataclass
class Pin:
    """One pin on a package.

    Field ordering matches pinout.schema.json for stable to_dict output.
    """
    numbers: list[str] = field(metadata={
        "description": "Pin number(s). Always a list even for single-pin records. "
                       "Strings for BGA grids ('A1'), LGA, stacked internal pins."})
    name: str = field(metadata={
        "description": "Primary pin name as printed in the datasheet pinout table."})
    type: str = field(metadata={
        "description": "Electrical role — KiCad ERC vocabulary (input, output, bidirectional, "
                       "tri_state, passive, open_collector, open_emitter, power_in, "
                       "power_out, not_connected, unspecified)."})
    subtype: Optional[str] = field(default=None, metadata={
        "description": "Refinement of 'type' (e.g. 'open_drain'). None when unspecified."})
    description: Optional[str] = field(default=None, metadata={
        "description": "Human-readable pin description."})
    power_domain: Optional[str] = field(default=None, metadata={
        "description": "Power-supply rail key. Must resolve to a base.recommended_operating entry. "
                       "None for pins outside any power domain."})
    alt_functions: list[AltFunction] = field(default_factory=list, metadata={
        "description": "Alternate-function table for muxed pins. Empty for fixed-function pins."})
    is_5v_tolerant: Optional[bool] = field(default=None, metadata={
        "description": "True iff datasheet explicitly rates the pin for 5V signals. "
                       "None when unspecified — detectors treat None as unknown."})
    absolute_max: Optional[list[SpecValue]] = field(default=None, metadata={
        "description": "Per-pin absolute-maximum ratings. None when datasheet only publishes "
                       "module-level absolute max."})
    recommended: Optional[list[SpecValue]] = field(default=None, metadata={
        "description": "Per-pin recommended operating ratings."})
    drive_strength: Optional[list[SpecValue]] = field(default=None, metadata={
        "description": "Per-pin output drive strength (IOH, IOL)."})
    notes: Optional[str] = field(default=None, metadata={
        "description": "Free-form cross-pin constraints or usage notes. "
                       "Structured relationships live in base.pin_relationships instead."})
    evidence: Optional[Evidence] = field(default=None, metadata={
        "description": "Provenance for this pin entry. None only for derived/internal entries."})


class Pinout:
    """Wrapper around list[Pin] with lookup helpers.

    Not a dataclass — the JSON shape is a bare array, and we want method
    chaining (ds.pinout.find(pin="5")). The codec special-cases this
    class: from_dict(Pinout, data) expects a list of Pin dicts, to_dict
    emits a bare list.
    """

    def __init__(self, pins: list[Pin]):
        self.pins = pins

    def find(self, *, pin: Optional[str] = None, name: Optional[str] = None) -> Optional[Pin]:
        """Find a pin by number OR name. Returns None if not found.

        When both `pin` and `name` are supplied, matches on either — first
        match in list order wins, with no priority between number and name.
        The ambiguous case (both args matching different pins) is a misuse
        of the API; prefer passing exactly one.
        """
        if pin is None and name is None:
            return None
        for p in self.pins:
            if pin is not None and pin in p.numbers:
                return p
            if name is not None and p.name == name:
                return p
        return None

    def in_domain(self, rail: str) -> list[Pin]:
        """Return every pin whose power_domain equals `rail`."""
        return [p for p in self.pins if p.power_domain == rail]

    def __iter__(self):
        return iter(self.pins)

    def __len__(self) -> int:
        return len(self.pins)

    def __repr__(self) -> str:
        return f"Pinout(pins={len(self.pins)} pins)"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Pinout):
            return NotImplemented
        return self.pins == other.pins
