"""Phase 4 4c: 6 new detectors consuming v1.4 datasheet facts via lookup().

Each detector probes facts.base.<field> or facts.regulator.<field> via the
typed Consumer API (datasheet_types) and emits findings with
confidence='datasheet-backed' + evidence_source='datasheet' when data is
present. Soft-skip when the cache is missing or below trust gate — no
analyzer ever blocks on lookup() per Phase 4 spec §5.1.

API surface (Phase 4b alignment, 2026-05-03):
    facts = get_facts(mpn, cache_dir=cache_dir)        # may be None
    if facts is None: return []                        # silent skip
    specs = facts.base.absolute_max.get(key)           # list[SpecValue]
    if has_data(specs):
        sv = best(specs, min_confidence='medium')      # SpecValue or None
        if sv is not None and sv.max is not None:
            ...

Synonym resolution (Phase 4c addendum §A2): base.absolute_max,
base.recommended_operating, and base.thermal use additionalProperties:
SpecValue[] — extractors emit mixed key spellings (VDD/VCC/VDDA, TJ/TJ_max).
_resolve_key() walks a synonym tuple and returns the first match.

All findings tagged schema_era='v1.4' for harness regression assertions.
"""
from __future__ import annotations

import logging
from typing import Optional

from finding_schema import make_finding
from lookup_helpers import get_facts, has_data, best


log = logging.getLogger(__name__)


# Synonym tables for rail-key resolution. Order matters: first match wins.
VDD_SYNONYMS = ("VDD", "VCC", "VDDA", "VDDIO", "VCC_dual_supply",
                "VCC_single_supply", "VDDD", "AVDD", "DVDD")
TJ_SYNONYMS = ("TJ", "TJ_max", "TJmax", "Tj", "Tj_max")
THETA_JA_SYNONYMS = ("theta_ja", "Rtheta_JA", "R_theta_JA", "RthJA")


def _resolve_key(block: Optional[dict], synonyms) -> Optional[list]:
    """Return the first synonym's SpecValue list from `block`, or None.

    Synonym order in the tuple defines resolution priority. None block
    or no key match → None (caller treats as no data).
    """
    if not block:
        return None
    for key in synonyms:
        specs = block.get(key)
        if specs:
            return specs
    return None


def _candidate_synonyms(domain: Optional[str], base_synonyms: tuple) -> tuple:
    """Build a synonym tuple that prefers the pin's declared domain first,
    then falls back to the base synonym set."""
    if not domain:
        return base_synonyms
    if domain in base_synonyms:
        # Move declared domain to the front
        return (domain,) + tuple(s for s in base_synonyms if s != domain)
    return (domain,) + base_synonyms


def _connected_net(ctx, ref: str, pin_numbers) -> Optional[str]:
    """Return the net connected to the first matching pin number, or None."""
    if not pin_numbers:
        return None
    for pnum in pin_numbers:
        key = (ref, str(pnum))
        if key in ctx.pin_net:
            net, _ = ctx.pin_net[key]
            if net:
                return net
    return None


def _component_mpn(component: dict) -> Optional[str]:
    """Resolve an IC's MPN with the same fallback chain as Phase 4b."""
    return component.get("mpn") or component.get("value") or None


# ---------------------------------------------------------------------------
# AM-001 — absolute-max violation
# ---------------------------------------------------------------------------

def detect_absolute_max_violations(ctx, rail_voltages: dict) -> list[dict]:
    """AM-001: For each IC pin with a power_domain, compare the connected
    rail voltage to base.absolute_max[domain] (with synonym resolution).

    Per-pin Pin.absolute_max overrides the rail-level limit when stricter.

    Severity: error (safety check — exceeding absolute_max kills the part).
    """
    findings: list[dict] = []
    cache_dir = getattr(ctx, "cache_dir", None)
    design_context = getattr(ctx, "design_context", None)

    for component in ctx.components:
        ref = component.get("reference") or component.get("ref")
        mpn = _component_mpn(component)
        if not ref or not mpn:
            continue
        facts = get_facts(mpn, cache_dir=cache_dir)
        if facts is None:
            continue
        base = getattr(facts, "base", None)
        if base is None:
            continue
        am_block = getattr(base, "absolute_max", None)
        pinout = getattr(base, "pinout", None)
        if not am_block or pinout is None:
            continue

        for pin in pinout:
            domain = getattr(pin, "power_domain", None)
            if not domain:
                continue
            net = _connected_net(ctx, ref, getattr(pin, "numbers", []))
            if net is None:
                continue
            rail_v = rail_voltages.get(net)
            if rail_v is None:
                continue

            synonyms = _candidate_synonyms(domain, VDD_SYNONYMS)
            specs = _resolve_key(am_block, synonyms)
            if not has_data(specs):
                continue
            sv = best(specs, min_confidence="medium")
            if sv is None or sv.max is None:
                continue
            absolute_max_v = sv.max

            # Per-pin override: tighten the rail-level limit if pin publishes
            # a stricter per-pin absolute_max.
            pin_specs = getattr(pin, "absolute_max", None)
            if has_data(pin_specs):
                pin_sv = best(pin_specs, min_confidence="medium")
                if pin_sv is not None and pin_sv.max is not None and pin_sv.max < absolute_max_v:
                    absolute_max_v = pin_sv.max

            if rail_v <= absolute_max_v:
                continue

            pin_number = pin.numbers[0] if pin.numbers else "?"
            findings.append(make_finding(
                detector="detect_absolute_max_violations",
                rule_id="AM-001",
                category="electrical_safety",
                summary=(f"{ref} pin {pin_number} ({pin.name}) on {net} at "
                          f"{rail_v}V exceeds absolute_max {absolute_max_v}V"),
                description=(f"Pin {pin_number} of {ref} ({mpn}) connects to "
                              f"net {net} at an estimated {rail_v}V, exceeding "
                              f"the datasheet absolute_max of {absolute_max_v}V "
                              f"for power domain {domain}. Exceeding absolute_max "
                              f"can permanently damage the part."),
                severity="error",
                confidence="datasheet-backed",
                evidence_source="datasheet",
                components=[ref],
                nets=[net],
                pins=[{"ref": ref, "pin": pin_number, "name": pin.name}],
                recommendation=(f"Reduce {net} voltage below {absolute_max_v}V "
                                 f"or replace {ref} with a part rated to handle "
                                 f"{rail_v}V on the {domain} domain."),
                report_section="Electrical Safety",
                impact="Risk of permanent device damage or destruction.",
                source=ctx.source,
                design_context=design_context,
                schema_era="v1.4",
                rail_voltage=rail_v,
                absolute_max_v=absolute_max_v,
                domain=domain,
            ))
    return findings


# ---------------------------------------------------------------------------
# OV-001 — VCC outside recommended operating range
# ---------------------------------------------------------------------------

def detect_vcc_outside_recommended(ctx, rail_voltages: dict) -> list[dict]:
    """OV-001: For each IC pin with a power_domain, verify the connected
    rail voltage is within base.recommended_operating[domain] range
    (with synonym resolution).

    Severity: warning (base severity; tuning matrix retired in v2.0, spec §5).
    """
    findings: list[dict] = []
    cache_dir = getattr(ctx, "cache_dir", None)
    design_context = getattr(ctx, "design_context", None)

    for component in ctx.components:
        ref = component.get("reference") or component.get("ref")
        mpn = _component_mpn(component)
        if not ref or not mpn:
            continue
        facts = get_facts(mpn, cache_dir=cache_dir)
        if facts is None:
            continue
        base = getattr(facts, "base", None)
        if base is None:
            continue
        rec_block = getattr(base, "recommended_operating", None)
        pinout = getattr(base, "pinout", None)
        if not rec_block or pinout is None:
            continue

        for pin in pinout:
            domain = getattr(pin, "power_domain", None)
            if not domain:
                continue
            net = _connected_net(ctx, ref, getattr(pin, "numbers", []))
            if net is None:
                continue
            rail_v = rail_voltages.get(net)
            if rail_v is None:
                continue

            synonyms = _candidate_synonyms(domain, VDD_SYNONYMS)
            specs = _resolve_key(rec_block, synonyms)
            if not has_data(specs):
                continue
            sv = best(specs, min_confidence="medium")
            if sv is None:
                continue
            v_min = sv.min
            v_max = sv.max

            pin_number = pin.numbers[0] if pin.numbers else "?"

            if v_min is not None and rail_v < v_min:
                findings.append(make_finding(
                    detector="detect_vcc_outside_recommended",
                    rule_id="OV-001",
                    category="electrical_safety",
                    summary=(f"{ref} pin {pin_number} ({pin.name}) on {net} at "
                              f"{rail_v}V below recommended min {v_min}V"),
                    description=(f"Pin {pin_number} of {ref} ({mpn}) connects to "
                                  f"net {net} at {rail_v}V, below the recommended "
                                  f"operating minimum of {v_min}V for domain {domain}. "
                                  f"Operation outside the recommended range may "
                                  f"compromise specified electrical characteristics."),
                    severity="warning",
                    confidence="datasheet-backed",
                    evidence_source="datasheet",
                    components=[ref],
                    nets=[net],
                    pins=[{"ref": ref, "pin": pin_number, "name": pin.name}],
                    recommendation=(f"Raise {net} to at least {v_min}V or use a "
                                     f"part rated for lower-voltage operation."),
                    report_section="Electrical Safety",
                    impact="Specified electrical characteristics may not be met.",
                    source=ctx.source,
                    design_context=design_context,
                    schema_era="v1.4",
                    rail_voltage=rail_v,
                    recommended_min=v_min,
                    domain=domain,
                ))
            elif v_max is not None and rail_v > v_max:
                findings.append(make_finding(
                    detector="detect_vcc_outside_recommended",
                    rule_id="OV-001",
                    category="electrical_safety",
                    summary=(f"{ref} pin {pin_number} ({pin.name}) on {net} at "
                              f"{rail_v}V above recommended max {v_max}V"),
                    description=(f"Pin {pin_number} of {ref} ({mpn}) connects to "
                                  f"net {net} at {rail_v}V, above the recommended "
                                  f"operating maximum of {v_max}V for domain {domain}. "
                                  f"Still within absolute_max but specified "
                                  f"performance is not guaranteed."),
                    severity="warning",
                    confidence="datasheet-backed",
                    evidence_source="datasheet",
                    components=[ref],
                    nets=[net],
                    pins=[{"ref": ref, "pin": pin_number, "name": pin.name}],
                    recommendation=(f"Reduce {net} below {v_max}V or use a part "
                                     f"rated for higher-voltage operation."),
                    report_section="Electrical Safety",
                    impact="Specified electrical characteristics may not be met.",
                    source=ctx.source,
                    design_context=design_context,
                    schema_era="v1.4",
                    rail_voltage=rail_v,
                    recommended_max=v_max,
                    domain=domain,
                ))
    return findings


# ---------------------------------------------------------------------------
# TJ-001 — junction temperature exceeds TJmax (thermal)
# ---------------------------------------------------------------------------

def detect_tj_exceeds_max(assessments, *, source, cache_dir,
                            design_context=None) -> list[dict]:
    """TJ-001: Recompute junction temperature using v1.4 facts.base.thermal
    [theta_ja] and compare to facts.base.absolute_max[TJ_SYNONYMS].

    Severity: error.

    Each assessment must carry: ref, value (or mpn), ambient_c, pdiss_w.
    Existing v1.3 thermal pipeline (analyze_thermal._compute_junction_temps)
    populates these fields; TJ-001 is an additive rule on top.
    """
    findings: list[dict] = []
    for a in assessments:
        ref = a.get("ref")
        mpn = a.get("mpn") or a.get("value")
        if not ref or not mpn:
            continue
        facts = get_facts(mpn, cache_dir=cache_dir)
        if facts is None:
            continue
        base = getattr(facts, "base", None)
        if base is None:
            continue

        thermal_block = getattr(base, "thermal", None)
        theta_specs = _resolve_key(thermal_block, THETA_JA_SYNONYMS)
        if not has_data(theta_specs):
            continue
        theta_sv = best(theta_specs, min_confidence="medium")
        if theta_sv is None:
            continue
        # Prefer typ; fall back to max (worst-case) when typ is absent.
        theta = theta_sv.typ if theta_sv.typ is not None else theta_sv.max
        if theta is None:
            continue

        am_block = getattr(base, "absolute_max", None)
        tj_specs = _resolve_key(am_block, TJ_SYNONYMS)
        if not has_data(tj_specs):
            continue
        tj_sv = best(tj_specs, min_confidence="medium")
        if tj_sv is None or tj_sv.max is None:
            continue
        tj_max = tj_sv.max

        ambient = a.get("ambient_c", 25.0)
        pdiss = a.get("pdiss_w", 0.0)
        tj_v14 = ambient + theta * pdiss

        if tj_v14 <= tj_max:
            continue

        findings.append(make_finding(
            detector="detect_tj_exceeds_max",
            rule_id="TJ-001",
            category="thermal",
            summary=(f"{ref} ({mpn}) estimated TJ {tj_v14:.1f}°C exceeds "
                      f"datasheet TJmax {tj_max}°C"),
            description=(f"Component {ref} ({mpn}): TJ = ambient ({ambient}°C) + "
                          f"θJA ({theta}°C/W) × P_diss ({pdiss}W) = {tj_v14:.1f}°C, "
                          f"exceeding datasheet TJmax of {tj_max}°C. "
                          f"Operation may cause thermal shutdown, accelerated "
                          f"aging, or permanent damage."),
            severity="error",
            confidence="datasheet-backed",
            evidence_source="datasheet",
            components=[ref],
            recommendation=(f"Reduce P_diss below "
                             f"{(tj_max - ambient) / theta:.2f}W, improve PCB "
                             f"thermal path (more copper, vias, or heat-sinking), "
                             f"or select a part with a higher TJmax / lower θJA."),
            report_section="Thermal",
            impact="Risk of thermal shutdown or accelerated device aging.",
            source=source,
            design_context=design_context,
            schema_era="v1.4",
            tj_estimated_c=round(tj_v14, 1),
            tj_max_c=tj_max,
            theta_ja=theta,
            pdiss_w=pdiss,
            ambient_c=ambient,
        ))
    return findings


# ---------------------------------------------------------------------------
# FT-001 — 5V signal on non-5V-tolerant pin
# ---------------------------------------------------------------------------

# Threshold below which a net voltage is considered safe even on a non-tolerant
# pin. Anything ≥ this triggers FT-001 when pin.is_5v_tolerant is False.
_FT_001_THRESHOLD_V = 4.5


def detect_5v_on_non_tolerant_pin(ctx, rail_voltages: dict) -> list[dict]:
    """FT-001: For each IC pin where Pin.is_5v_tolerant is False, check the
    connected net voltage. Emit error when net ≥ 5V threshold.

    Pin.is_5v_tolerant=None (unknown) is treated as no-finding (skip silent)
    per Pin schema convention. Severity: error.
    """
    findings: list[dict] = []
    cache_dir = getattr(ctx, "cache_dir", None)
    design_context = getattr(ctx, "design_context", None)

    for component in ctx.components:
        ref = component.get("reference") or component.get("ref")
        mpn = _component_mpn(component)
        if not ref or not mpn:
            continue
        facts = get_facts(mpn, cache_dir=cache_dir)
        if facts is None:
            continue
        base = getattr(facts, "base", None)
        if base is None:
            continue
        pinout = getattr(base, "pinout", None)
        if pinout is None:
            continue

        for pin in pinout:
            tolerant = getattr(pin, "is_5v_tolerant", None)
            if tolerant is None or tolerant is True:
                continue  # Skip unknown (None) and explicitly tolerant pins.
            net = _connected_net(ctx, ref, getattr(pin, "numbers", []))
            if net is None:
                continue
            sig_v = rail_voltages.get(net)
            if sig_v is None or sig_v < _FT_001_THRESHOLD_V:
                continue

            pin_number = pin.numbers[0] if pin.numbers else "?"
            findings.append(make_finding(
                detector="detect_5v_on_non_tolerant_pin",
                rule_id="FT-001",
                category="electrical_safety",
                summary=(f"{ref} pin {pin_number} ({pin.name}) on {net} sees "
                          f"{sig_v}V but is not 5V-tolerant"),
                description=(f"Pin {pin_number} of {ref} ({mpn}) is connected "
                              f"to net {net} at an estimated {sig_v}V. The "
                              f"datasheet marks this pin as NOT 5V-tolerant — "
                              f"applying 5V can damage the input or violate "
                              f"absolute-max ratings."),
                severity="error",
                confidence="datasheet-backed",
                evidence_source="datasheet",
                components=[ref],
                nets=[net],
                pins=[{"ref": ref, "pin": pin_number, "name": pin.name}],
                recommendation=(f"Insert a level shifter, voltage divider, or "
                                 f"current-limiting resistor between {net} and "
                                 f"pin {pin_number} ({pin.name})."),
                report_section="Electrical Safety",
                impact="Risk of permanent input damage from over-voltage signal.",
                source=ctx.source,
                design_context=design_context,
                schema_era="v1.4",
                signal_voltage=sig_v,
                is_5v_tolerant=False,
            ))
    return findings


# ---------------------------------------------------------------------------
# PM-001 — pin signal type mismatch
# ---------------------------------------------------------------------------

# Map peripheral hint regex → set of acceptable peripheral name fragments on
# AltFunction.peripheral / .name. A net name matching the regex requires
# the connected pin's alt_functions to include at least one matching peripheral.
import re as _re

_PERIPHERAL_HINTS = (
    (_re.compile(r"\b(USART|UART)\d*", _re.IGNORECASE), ("USART", "UART")),
    (_re.compile(r"\bI2C\d*", _re.IGNORECASE), ("I2C",)),
    (_re.compile(r"\bSPI\d*", _re.IGNORECASE), ("SPI",)),
    (_re.compile(r"\bCAN\d*", _re.IGNORECASE), ("CAN",)),
    (_re.compile(r"\bUSB", _re.IGNORECASE), ("USB",)),
    (_re.compile(r"\bI2S\d*", _re.IGNORECASE), ("I2S",)),
)


def _infer_peripheral(net_name: str) -> Optional[tuple]:
    """Return the peripheral-name tuple if net_name matches a known hint."""
    if not net_name:
        return None
    for pat, peripherals in _PERIPHERAL_HINTS:
        if pat.search(net_name):
            return peripherals
    return None


def detect_wrong_signal_type(ctx) -> list[dict]:
    """PM-001: For each IC pin connected to a net whose name suggests a
    specific peripheral (UART/I2C/SPI/USB/CAN/I2S), verify the pin's
    Pin.alt_functions includes at least one matching peripheral.

    Skipped silently when alt_functions is empty (datasheet didn't publish
    the pinout's peripheral mapping). Severity: warning.
    """
    findings: list[dict] = []
    cache_dir = getattr(ctx, "cache_dir", None)
    design_context = getattr(ctx, "design_context", None)

    for component in ctx.components:
        ref = component.get("reference") or component.get("ref")
        mpn = _component_mpn(component)
        if not ref or not mpn:
            continue
        facts = get_facts(mpn, cache_dir=cache_dir)
        if facts is None:
            continue
        base = getattr(facts, "base", None)
        if base is None:
            continue
        pinout = getattr(base, "pinout", None)
        if pinout is None:
            continue

        for pin in pinout:
            alt_functions = getattr(pin, "alt_functions", None) or []
            if not alt_functions:
                continue  # No published mapping — can't validate.
            net = _connected_net(ctx, ref, getattr(pin, "numbers", []))
            if net is None:
                continue
            inferred = _infer_peripheral(net)
            if inferred is None:
                continue
            # Pin supports the peripheral if any AltFunction's peripheral or
            # name contains a matching family fragment.
            supported = False
            for af in alt_functions:
                af_peripheral = (getattr(af, "peripheral", "") or "").upper()
                af_name = (getattr(af, "name", "") or "").upper()
                for hint in inferred:
                    hint_upper = hint.upper()
                    if hint_upper in af_peripheral or hint_upper in af_name:
                        supported = True
                        break
                if supported:
                    break
            if supported:
                continue

            pin_number = pin.numbers[0] if pin.numbers else "?"
            af_names = [getattr(af, "name", "?") for af in alt_functions]
            findings.append(make_finding(
                detector="detect_wrong_signal_type",
                rule_id="PM-001",
                category="design_intent",
                summary=(f"{ref} pin {pin_number} ({pin.name}) on {net} expects "
                          f"{inferred[0]} but pin only supports {af_names}"),
                description=(f"Net name '{net}' suggests {inferred[0]} signal "
                              f"function, but pin {pin_number} of {ref} ({mpn}) "
                              f"alternate-function table only lists: {af_names}. "
                              f"Either rename the net or move to a pin that "
                              f"supports the intended peripheral."),
                severity="warning",
                confidence="datasheet-backed",
                evidence_source="datasheet",
                components=[ref],
                nets=[net],
                pins=[{"ref": ref, "pin": pin_number, "name": pin.name}],
                recommendation=(f"Verify the schematic intent for net {net}. If "
                                 f"the {inferred[0]} routing is intentional, "
                                 f"reassign to a pin that supports it."),
                report_section="Design Intent",
                impact="Likely net-naming error or incorrect pin assignment.",
                source=ctx.source,
                design_context=design_context,
                schema_era="v1.4",
                inferred_peripheral=inferred[0],
                supported_alt_functions=af_names,
            ))
    return findings


# ---------------------------------------------------------------------------
# EX-001 — missing required component (regulator passives)
# ---------------------------------------------------------------------------

def _net_has_component_type(ctx, net: str, comp_type: str) -> bool:
    """True iff any component of comp_type ('capacitor', 'inductor', etc.)
    is connected to `net`."""
    if not net:
        return False
    net_info = ctx.nets.get(net) or {}
    for pin_info in net_info.get("pins", []):
        comp_ref = pin_info.get("component")
        if not comp_ref:
            continue
        comp = ctx.comp_lookup.get(comp_ref) or {}
        if comp.get("type") == comp_type:
            return True
    return False


def detect_missing_required_components(ctx, power_regulators: list) -> list[dict]:
    """EX-001: For each regulator with mpn-backed v1.4 facts, verify that
    datasheet-required components are present:
      - regulator.cin_min populated → expect a capacitor on input_rail
      - regulator.cout_min populated → expect a capacitor on output_rail
      - regulator.inductor_range populated → expect an inductor in the topology

    Severity: error. Soft-skip when no MPN, no facts, or the relevant rail
    is unknown (input_rail/output_rail is None on the regulator dict).
    """
    findings: list[dict] = []
    cache_dir = getattr(ctx, "cache_dir", None)
    design_context = getattr(ctx, "design_context", None)

    for reg in power_regulators:
        ref = reg.get("ref") or reg.get("reference")
        mpn = reg.get("mpn") or reg.get("value")
        if not ref or not mpn:
            continue
        facts = get_facts(mpn, cache_dir=cache_dir)
        if facts is None:
            continue
        regulator = getattr(facts, "regulator", None)
        if regulator is None:
            continue

        input_rail = reg.get("input_rail")
        output_rail = reg.get("output_rail")

        # Cin check
        cin_specs = getattr(regulator, "cin_min", None)
        if has_data(cin_specs) and input_rail:
            sv = best(cin_specs, min_confidence="medium")
            if sv is not None and not _net_has_component_type(ctx, input_rail, "capacitor"):
                findings.append(_make_ex_001(
                    ref, mpn, "input cap", input_rail, sv,
                    "regulator.cin_min", ctx.source, design_context,
                    f"Add a {sv.min}F (min) input capacitor between {input_rail} and ground."
                ))

        # Cout check
        cout_specs = getattr(regulator, "cout_min", None)
        if has_data(cout_specs) and output_rail:
            sv = best(cout_specs, min_confidence="medium")
            if sv is not None and not _net_has_component_type(ctx, output_rail, "capacitor"):
                findings.append(_make_ex_001(
                    ref, mpn, "output cap", output_rail, sv,
                    "regulator.cout_min", ctx.source, design_context,
                    f"Add a {sv.min}F (min) output capacitor between {output_rail} and ground."
                ))

        # Inductor check (switching regulators only)
        l_specs = getattr(regulator, "inductor_range", None)
        if has_data(l_specs):
            sv = best(l_specs, min_confidence="medium")
            if sv is not None and not reg.get("inductor"):
                # Switching regulator with no detected inductor in topology.
                rec_l = sv.typ if sv.typ is not None else (sv.min or sv.max)
                rail_for_finding = output_rail or input_rail or "(unknown rail)"
                findings.append(_make_ex_001(
                    ref, mpn, "inductor", rail_for_finding, sv,
                    "regulator.inductor_range", ctx.source, design_context,
                    f"Add a {rec_l}H inductor between the switch node and {output_rail}."
                ))
    return findings


def _make_ex_001(ref, mpn, kind, rail, sv, datasheet_field, source,
                   design_context, recommendation):
    """Build an EX-001 finding from common args."""
    spec_min = getattr(sv, "min", None)
    spec_typ = getattr(sv, "typ", None)
    spec_max = getattr(sv, "max", None)
    return make_finding(
        detector="detect_missing_required_components",
        rule_id="EX-001",
        category="completeness",
        summary=(f"{ref} ({mpn}) requires {kind} per datasheet but none "
                  f"found on {rail}"),
        description=(f"Datasheet field {datasheet_field} for {ref} ({mpn}) "
                      f"specifies a required {kind} on {rail}; no component "
                      f"of that kind is connected to that net in the schematic. "
                      f"Required spec: min={spec_min}, typ={spec_typ}, "
                      f"max={spec_max} {getattr(sv, 'unit', '')}."),
        severity="error",
        confidence="datasheet-backed",
        evidence_source="datasheet",
        components=[ref],
        nets=[rail] if rail else [],
        recommendation=recommendation,
        report_section="Completeness",
        impact="Regulator may oscillate, fail to start, or violate datasheet stability requirements.",
        source=source,
        design_context=design_context,
        schema_era="v1.4",
        missing_kind=kind,
        datasheet_field=datasheet_field,
        spec_min=spec_min,
        spec_typ=spec_typ,
        spec_max=spec_max,
    )
