"""BaseBlock + sub-types — universal per-IC facts.

Mirrors base.schema.json. The ratings dicts (absolute_max,
recommended_operating, esd, thermal) are keyed by parameter name
(e.g. 'VIN_max') → list[SpecValue], matching the consumer-indexability
shape from spec §4.

Field-ordering note: Python dataclass syntax requires every required
field (no default) to precede every optional field (with default). The
JSON schema property order for BaseBlock puts `description` second
(optional) ahead of `absolute_max` (required) — Python forbids this.
BaseBlock resolves the tension by grouping all 5 required fields first
(family, package, absolute_max, recommended_operating, pinout), then
all 6 optional fields in schema order. `to_dict` output key order
therefore deviates from schema property order but remains stable
across runs. Consumers should not rely on either — dict key order
is not part of the contract.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .spec_value import Evidence, SpecValue
from .pinout import Pinout


@dataclass
class BodyMm:
    """Physical body dimensions in millimeters."""
    length: float = field(metadata={
        "description": "Body length in mm along the longest axis."})
    width: float = field(metadata={
        "description": "Body width in mm along the perpendicular-to-length axis."})
    height: float = field(metadata={
        "description": "Body height in mm (package thickness / standoff direction)."})


@dataclass
class Package:
    """Physical package shape."""
    code: str = field(metadata={
        "description": "Datasheet package code (e.g. 'SOIC-8', 'LQFP-64', 'WLCSP-25')."})
    pin_count: Optional[int] = field(default=None, metadata={
        "description": "Total pin/ball count."})
    pitch_mm: Optional[float] = field(default=None, metadata={
        "description": "Pin pitch in millimeters."})
    body_mm: Optional[BodyMm] = field(default=None, metadata={
        "description": "Body dimensions. None when datasheet doesn't publish."})
    thermal_pad: Optional[bool] = field(default=None, metadata={
        "description": "True iff package has an exposed thermal pad."})
    evidence: Optional[Evidence] = field(default=None, metadata={
        "description": "Provenance for the package entry."})


@dataclass
class MoistureSensitivity:
    """JEDEC J-STD-020 moisture-sensitivity ratings."""
    msl: Optional[int] = field(default=None, metadata={
        "description": "JEDEC Moisture Sensitivity Level (1–6)."})
    peak_reflow_c: Optional[float] = field(default=None, metadata={
        "description": "Maximum peak reflow temperature in °C."})
    evidence: Optional[Evidence] = field(default=None, metadata={
        "description": "Provenance."})


@dataclass
class ComplianceMark:
    """One compliance / qualification mark."""
    mark: str = field(metadata={
        "description": "Compliance mark or standard name (e.g. 'AEC-Q100', 'IEC 62368', 'ISO 13485')."})
    rating: Optional[str] = field(default=None, metadata={
        "description": "Rating within the mark (e.g. 'Grade 1' for AEC-Q100)."})
    evidence: Optional[Evidence] = field(default=None, metadata={
        "description": "Provenance."})


@dataclass
class PinRelationship:
    """Structured cross-pin relationship.

    Vocabulary (closed starter set in v1.4): compensation_network,
    matched_pair, requires_pullup, requires_pulldown, current_programming,
    stacked_internal, exclusive_with, timing_critical.
    """
    type: str = field(metadata={
        "description": "Relationship kind. Closed enum in base.schema.json — 8 values: "
                       "compensation_network, matched_pair, requires_pullup, "
                       "requires_pulldown, current_programming, stacked_internal, "
                       "exclusive_with, timing_critical. The dataclass stores any "
                       "string; enum enforcement happens at JSON-schema validation "
                       "(cache-write time), not at dataclass construction."})
    pins: list[str] = field(metadata={
        "description": "Pin numbers involved in this relationship."})
    notes: Optional[str] = field(default=None, metadata={
        "description": "Free-form prose describing the relationship."})
    evidence: Optional[Evidence] = field(default=None, metadata={
        "description": "Provenance."})


@dataclass
class BaseBlock:
    """Universal per-IC facts.

    absolute_max / recommended_operating / esd / thermal are keyed by
    parameter name (e.g. 'VIN_max') → list[SpecValue] — NOT flat lists.
    Consumer indexability per spec §4.
    """
    family: str = field(metadata={
        "description": "Human-readable functional family (e.g. 'step-down switching regulator')."})
    package: Package = field(metadata={
        "description": "Physical package shape."})
    absolute_max: dict[str, list[SpecValue]] = field(metadata={
        "description": "Absolute-maximum ratings keyed by parameter name → SpecValue[]. "
                       "Exceeding these kills the part."})
    recommended_operating: dict[str, list[SpecValue]] = field(metadata={
        "description": "Recommended operating conditions keyed by parameter name → SpecValue[]."})
    pinout: Pinout = field(metadata={
        "description": "Full pinout. Exposes .find(pin=...), .find(name=...), .in_domain(rail)."})
    description: Optional[str] = field(default=None, metadata={
        "description": "One-line part description."})
    thermal: Optional[dict[str, list[SpecValue]]] = field(default=None, metadata={
        "description": "Thermal characteristics keyed by parameter name → SpecValue[]. "
                       "Values in K/W, °C/W, K, or °C depending on parameter."})
    esd: Optional[dict[str, list[SpecValue]]] = field(default=None, metadata={
        "description": "ESD ratings keyed by test model (HBM, CDM, MM) → SpecValue[]."})
    moisture_sensitivity: Optional[MoistureSensitivity] = field(default=None, metadata={
        "description": "JEDEC MSL + peak reflow."})
    compliance: list[ComplianceMark] = field(default_factory=list, metadata={
        "description": "Compliance / qualification marks. Empty when no marks declared."})
    pin_relationships: list[PinRelationship] = field(default_factory=list, metadata={
        "description": "Structured cross-pin relationships (optional)."})
