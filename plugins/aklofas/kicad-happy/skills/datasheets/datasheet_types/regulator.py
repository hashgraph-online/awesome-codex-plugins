"""Regulator category extension typed access.

Mirrors regulator.schema.json v0.3. Flat topology enum per spec §7.
Nested StabilityConditions (feeds SV-001) and Sequencing (feeds ST-001)
blocks.

Trust-gating helpers (.best(), .trusted()) are Track 2.4 — NOT here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .spec_value import Evidence, SpecValue


@dataclass
class StabilityConditions:
    """Output-capacitor stability window. Consumed by SV-001."""
    cap_types_allowed: list[str] = field(default_factory=list, metadata={
        "description": "Allowed output-cap technology families (closed vocabulary — "
                       "ceramic_c0g, ceramic_x5r, ceramic_x7r, ceramic_x7s, tantalum, "
                       "polymer, electrolytic, film)."})
    esr_range: Optional[list[SpecValue]] = field(default=None, metadata={
        "description": "Permitted output-cap ESR range. None when datasheet doesn't publish one."})
    notes: Optional[str] = field(default=None, metadata={
        "description": "Free-form stability notes."})
    evidence: Optional[Evidence] = field(default=None, metadata={
        "description": "Provenance."})


@dataclass
class Sequencing:
    """Power-on sequencing requirements. Consumed by ST-001."""
    must_rise_after: list[str] = field(default_factory=list, metadata={
        "description": "Rail names this rail must come up after."})
    must_rise_before: list[str] = field(default_factory=list, metadata={
        "description": "Rail names this rail must come up before."})
    max_inter_rail_delay: Optional[list[SpecValue]] = field(default=None, metadata={
        "description": "Maximum allowed time gap between the dependency rail and this rail "
                       "coming into regulation."})
    notes: Optional[str] = field(default=None, metadata={
        "description": "Free-form sequencing notes."})
    evidence: Optional[Evidence] = field(default=None, metadata={
        "description": "Provenance."})


@dataclass
class Regulator:
    """Voltage-regulator category extension.

    topology is the only hard-required field — every regulator knows
    its own topology. Every other field is optional because datasheet
    coverage varies.
    """
    topology: str = field(metadata={
        "description": "ldo | buck | boost | buck_boost | sepic | flyback | charge_pump | isolated. "
                       "Closed enum in regulator.schema.json; dataclass stores any string and defers "
                       "enum enforcement to JSON-schema cache-write time."})
    vin_range: Optional[list[SpecValue]] = field(default=None, metadata={
        "description": "Input-voltage operating range."})
    vout_range: Optional[list[SpecValue]] = field(default=None, metadata={
        "description": "Output-voltage range (fixed parts: single value; adjustable: min→max)."})
    iout_max: Optional[list[SpecValue]] = field(default=None, metadata={
        "description": "Maximum output current."})
    reference_voltage: Optional[list[SpecValue]] = field(default=None, metadata={
        "description": "Feedback reference voltage (adjustable parts only). Consumed by FS-001."})
    feedback_pin: Optional[str] = field(default=None, metadata={
        "description": "Pin number of the feedback input. Resolves to base.pinout[*].numbers."})
    compensation_pin: Optional[str] = field(default=None, metadata={
        "description": "Pin number for external compensation network (externally-compensated topologies)."})
    enable_pin: Optional[str] = field(default=None, metadata={
        "description": "Pin number of the EN/SHDN input. None for parts without an enable pin."})
    power_good_pin: Optional[str] = field(default=None, metadata={
        "description": "Pin number of the PGOOD output. None for parts without power-good."})
    cin_min: Optional[list[SpecValue]] = field(default=None, metadata={
        "description": "Minimum input-capacitor value. Consumed by EX-001."})
    cout_min: Optional[list[SpecValue]] = field(default=None, metadata={
        "description": "Minimum output-capacitor value."})
    inductor_range: Optional[list[SpecValue]] = field(default=None, metadata={
        "description": "Recommended inductor value range (switching topologies only)."})
    switching_freq: Optional[list[SpecValue]] = field(default=None, metadata={
        "description": "Nominal switching frequency (switching topologies only)."})
    dropout: Optional[list[SpecValue]] = field(default=None, metadata={
        "description": "Dropout voltage (LDO only)."})
    psrr: Optional[list[SpecValue]] = field(default=None, metadata={
        "description": "Power-supply rejection ratio across frequency."})
    line_regulation: Optional[list[SpecValue]] = field(default=None, metadata={
        "description": "Line regulation across input-voltage range."})
    load_regulation: Optional[list[SpecValue]] = field(default=None, metadata={
        "description": "Load regulation across output-current range."})
    stability_conditions: Optional[StabilityConditions] = field(default=None, metadata={
        "description": "Output-cap stability window. Consumed by SV-001."})
    sequencing: Optional[Sequencing] = field(default=None, metadata={
        "description": "Power-on sequencing constraints. Consumed by ST-001."})
