"""Rich finding schema shared by all detectors and validators.

Every detection and validation finding uses make_finding() to produce
a self-describing dict consumable by suggest-fixes and lighter LLMs.
"""

from __future__ import annotations

import hashlib
import re

VALID_SEVERITIES = ('error', 'warning', 'info')
VALID_CONFIDENCES = ('deterministic', 'heuristic', 'datasheet-backed')
VALID_EVIDENCE_SOURCES = (
    'datasheet', 'topology', 'heuristic_rule', 'symbol_footprint',
    'bom', 'geometry', 'api_lookup',
)
VALID_FIX_TYPES = (
    'resistor_value_change', 'capacitor_value_change',
    'add_component', 'remove_component', 'swap_connection', 'add_protection',
)


def _normalize_locator(s):
    """Lowercase + strip + collapse whitespace for finding_id locator portion."""
    if s is None:
        return ""
    return " ".join(str(s).split()).lower()


def _short_hash(s):
    """SHA-256 prefix used as fallback locator when no component/net/pin available."""
    return hashlib.sha256(str(s).encode("utf-8")).hexdigest()[:12]


def _first_nonempty(*candidates):
    """Return first non-empty list element of first non-None candidate list."""
    for cand in candidates:
        if cand:
            for item in cand:
                if item:
                    return item
    return None


# A "numbered" rule code (AM-001, LR-001, …). Only these may occupy the
# rule_id segment of the 3-part finding_id form; detection/audit codes
# (*-DET, *-AUD) and lowercase section names are not numbered rules and fold
# into the 2-part form below.
_RULE_CODE_RE = re.compile(r"^[A-Z]+-\d+$")


def _id_segment(s):
    """Reduce `s` to a single well-formed finding_id segment.

    Any character outside the locator/detection-id charset (`[A-Za-z0-9_./+-]`)
    — including the `:` separator and whitespace — collapses to `-`, so the
    result can never introduce a spurious segment boundary. Guarantees the
    output is non-empty.
    """
    seg = re.sub(r"[^A-Za-z0-9_./+-]+", "-", str(s)).strip("-")
    return seg or "x"


def _derive_finding_id(*, source, rule_id, detection_id, components, nets, pins, summary):
    """Derive a stable, well-formed finding_id per Phase 4 spec §3.2.

    Priority:
        1. {source}:{detection_id}        (detector provided one)
        2. {source}:{rule_id}:{primary}   (component/net/pin locator)
        3. {source}:{rule_id}:{hash}      (short SHA fallback on summary)

    Forms 2/3 (the colon-separated rule_id form) are used only when `rule_id`
    is a numbered rule code (`[A-Z]+-\\d+`). Any other rule_id — *-DET / *-AUD
    detection/audit codes, lowercase section names — and every detection_id
    fold into the colon-free `{source}:{token}` form so the id always parses as
    one of the two spec shapes regardless of the constructing detector.
    """
    if detection_id:
        return f"{source}:{_id_segment(detection_id)}"
    primary = _first_nonempty(components, nets, pins)
    if primary is not None:
        # Pin items may be dicts; coerce to string repr first
        if isinstance(primary, dict):
            primary = primary.get("ref") or primary.get("number") or str(primary)
        locator = _id_segment(_normalize_locator(primary))
    else:
        locator = _id_segment(_short_hash(summary))
    if _RULE_CODE_RE.match(rule_id or ""):
        return f"{source}:{rule_id}:{locator}"
    return f"{source}:{_id_segment(rule_id)}-{locator}"


def assign_finding_ids(findings, source):
    """Guarantee every finding in `findings` carries a stable, unique finding_id.

    Most detectors don't route through make_finding (EMC has its own helper,
    several emit raw dicts), so finding_id was absent on the bulk of findings —
    which made the Layer 2 merge a silent no-op (merge_annotations.py matches
    annotations to findings by finding_id). This pass runs once per analyzer at
    serialization time, after all filtering/appends, so the entire findings[]
    is covered regardless of construction path.

    Overwrites any existing finding_id so the `{source}:` prefix is consistent
    envelope-wide (`source` is the canonical analyzer name == file stem, e.g.
    "schematic", not the per-caller "sch"). Distinct findings that derive the
    same id get a `#N` suffix; if the *same object* appears in the list more
    than once (a pre-existing aliasing quirk in a couple detectors), it keeps a
    single id rather than being bumped to a spurious `#1`. Call AFTER
    sort_findings so the suffix order is deterministic across runs.
    """
    seen = {}
    assigned = {}
    for f in findings:
        if not isinstance(f, dict):
            continue
        if id(f) in assigned:
            continue
        fid = _derive_finding_id(
            source=source,
            rule_id=f.get("rule_id", "UNK"),
            detection_id=f.get("detection_id"),
            components=f.get("components", []),
            nets=f.get("nets", []),
            pins=f.get("pins", []),
            summary=f.get("summary", ""),
        )
        if fid in seen:
            seen[fid] += 1
            fid = f"{fid}#{seen[fid]}"
        else:
            seen[fid] = 0
        f["finding_id"] = fid
        assigned[id(f)] = fid
    return findings


def derive_deep_review_id(finding):
    """finding_id for a Deep Review finding (v2.0 spec §3.C).

    deep_review:<12-hex> — stable hash over (category, normalized anchors,
    normalized summary). Anchors come from the evidence block so the id is
    tied to what the finding cites. LLM rewording of the summary changes
    the id by design; diff_analysis compensates with anchor-level fuzzy
    matching (advisory only).
    """
    category = (finding.get('category') or '').strip().lower()
    ev = finding.get('evidence') or {}
    anchors = sorted(
        str(a).strip().upper()
        for key in ('components', 'nets', 'pins')
        for a in (ev.get(key) or [])
    )
    summary = ' '.join((finding.get('summary') or '').lower().split())
    payload = '\x1f'.join([category, '|'.join(anchors), summary])
    return 'deep_review:' + _short_hash(payload)


def assign_deep_review_ids(findings):
    """Stamp finding_id on every Deep Review finding, in place.

    Same collision discipline as assign_finding_ids: distinct findings
    that derive the same id get a #N suffix, in list order.
    """
    seen = {}
    for f in findings:
        if not isinstance(f, dict):
            continue
        fid = derive_deep_review_id(f)
        if fid in seen:
            seen[fid] += 1
            fid = f"{fid}#{seen[fid]}"
        else:
            seen[fid] = 0
        f['finding_id'] = fid
    return findings


_SEVERITY_NORMALIZE = {
    # Legacy uppercase pre-v1.3 taxonomy
    "CRITICAL": "error",
    "HIGH": "error",
    "MEDIUM": "warning",
    "LOW": "info",
    "INFO": "info",
    # Lowercase legacy variants
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "info",
    # v1.4 normalized vocab (pass-through)
    "error": "error",
    "warning": "warning",
    "info": "info",
}


def normalize_severity(sev):
    """Map any severity string to the v1.4 normalized vocabulary.

    Accepts legacy uppercase (CRITICAL/HIGH/MEDIUM/LOW/INFO) and v1.4
    lowercase (error/warning/info). Returns one of {"error", "warning",
    "info"}. Returns "info" for None, non-string, or unknown input.

    Use this anywhere a consumer reads `finding["severity"]` — analyzer
    outputs may carry either taxonomy depending on the producer code
    path (EMC + voltage_derating still emit legacy uppercase via
    _normalize_severity, schematic+pcb+thermal emit v1.4 lowercase).
    """
    if not isinstance(sev, str):
        return "info"
    return _SEVERITY_NORMALIZE.get(
        sev, _SEVERITY_NORMALIZE.get(sev.upper(), "info"))


def make_finding(
    detector: str,
    rule_id: str,
    category: str,
    summary: str,
    description: str,
    severity: str = 'warning',
    confidence: str = 'heuristic',
    evidence_source: str = 'heuristic_rule',
    components: list | None = None,
    nets: list | None = None,
    pins: list | None = None,
    recommendation: str = '',
    fix_params: dict | None = None,
    report_section: str | None = None,
    impact: str | None = None,
    standard_ref: str | None = None,
    source: str | None = None,
    design_context: dict | None = None,
    **extra,
) -> dict:
    """Build a rich finding dict with consistent structure.

    Required fields: detector, rule_id, category, summary, description.
    All other fields have sensible defaults.

    design_context: accepted for call-site compatibility; severity tuning
        retired in v2.0 (spec §5) — the value is ignored.

    Extra kwargs are merged into the finding (e.g., domain-specific data).
    """
    if severity not in VALID_SEVERITIES:
        raise ValueError(
            f"make_finding: invalid severity {severity!r} "
            f"(valid: {VALID_SEVERITIES})")
    if confidence not in VALID_CONFIDENCES:
        raise ValueError(
            f"make_finding: invalid confidence {confidence!r} "
            f"(valid: {VALID_CONFIDENCES})")
    if evidence_source not in VALID_EVIDENCE_SOURCES:
        raise ValueError(
            f"make_finding: invalid evidence_source {evidence_source!r} "
            f"(valid: {VALID_EVIDENCE_SOURCES})")
    finding = {
        'detector': detector,
        'rule_id': rule_id,
        'category': category,
        'summary': summary,
        'description': description,
        'components': list(components) if components is not None else [],
        'nets': list(nets) if nets is not None else [],
        # Note: list(pins) creates a shallow copy. In v1.4, pins items are sometimes
        # dicts (e.g., {"ref": "U1", "pin": "5"}); mutating those dict elements
        # post-call still affects the finding's pins. Current production callers
        # don't mutate pin dicts post-construction, so this is safe today. v1.5
        # PinRef migration will tighten pins to a typed structure and revisit this.
        'pins': list(pins) if pins is not None else [],
        'severity': severity,
        'confidence': confidence,
        'evidence_source': evidence_source,
        'recommendation': recommendation,
    }
    if fix_params is not None:
        finding['fix_params'] = fix_params
    finding['report_context'] = {
        'section': report_section or category.replace('_', ' ').title(),
        'impact': impact or '',
        'standard_ref': standard_ref or '',
    }
    if extra:
        finding.update(extra)
    finding['finding_id'] = _derive_finding_id(
        source=source or "unknown",
        rule_id=rule_id,
        detection_id=finding.get('detection_id'),
        components=components,
        nets=nets,
        pins=pins,
        summary=summary,
    )
    return finding


def make_provenance(evidence: str, confidence: str = 'heuristic',
                    claimed_components: list | None = None) -> dict:
    """Create a provenance dict for a detector output.

    Attaches to detection dicts to record how a detection was made.
    Part of the KH-263 detector provenance contract.

    Args:
        evidence: Detection method string. Convention: {detector_short}_{method}.
        confidence: One of VALID_CONFIDENCES (deterministic, heuristic,
            datasheet-backed).
        claimed_components: Component references this detection owns.

    Returns:
        Provenance dict with fields: evidence, confidence,
        claimed_components, excluded_by, suppressed_candidates.
    """
    if confidence not in VALID_CONFIDENCES:
        raise ValueError(
            f"make_provenance: invalid confidence {confidence!r} "
            f"(valid: {VALID_CONFIDENCES})")
    return {
        'evidence': evidence,
        'confidence': confidence,
        'claimed_components': claimed_components or [],
        'excluded_by': [],
        'suppressed_candidates': [],
    }


def compute_trust_summary(findings, bom=None):
    """Compute a trust summary from a list of findings.

    Aggregates finding metadata into a single trust posture block that
    tells users how much of the report is solid, heuristic, or missing
    evidence.

    Args:
        findings: List of finding dicts (each should have confidence,
            evidence_source fields).
        bom: Optional BOM list from schematic analyzer. If provided,
            computes manufacturer evidence coverage.

    Returns:
        Dict with trust posture fields.
    """
    total = len(findings)

    by_confidence = {}
    for c in VALID_CONFIDENCES:
        by_confidence[c] = 0
    by_evidence = {}
    for e in VALID_EVIDENCE_SOURCES:
        by_evidence[e] = 0

    has_provenance = 0
    unknown_confidence = 0
    unknown_evidence = 0

    for f in findings:
        if not isinstance(f, dict):
            continue
        conf = f.get('confidence', '')
        ev = f.get('evidence_source', '')
        if conf in by_confidence:
            by_confidence[conf] += 1
        else:
            unknown_confidence += 1
        if ev in by_evidence:
            by_evidence[ev] += 1
        else:
            unknown_evidence += 1
        if f.get('provenance') is not None:
            has_provenance += 1

    # BOM evidence coverage
    bom_coverage = None
    if bom is not None:
        bom_total = 0
        bom_with_mpn = 0
        bom_with_datasheet = 0
        for comp in bom:
            if not isinstance(comp, dict):
                continue
            if comp.get('type') in ('power_symbol', 'power_flag', 'flag'):
                continue
            bom_total += 1
            if comp.get('mpn') or comp.get('MPN'):
                bom_with_mpn += 1
            if comp.get('datasheet') and comp['datasheet'] not in ('', '~'):
                bom_with_datasheet += 1
        if bom_total > 0:
            bom_coverage = {
                'total_components': bom_total,
                'with_mpn': bom_with_mpn,
                'with_datasheet': bom_with_datasheet,
                'mpn_pct': round(100 * bom_with_mpn / bom_total, 1),
                'datasheet_pct': round(100 * bom_with_datasheet / bom_total, 1),
            }

    # Determine trust level
    if total == 0:
        trust_level = 'high'
    else:
        heuristic_pct = 100 * by_confidence.get('heuristic', 0) / total
        if heuristic_pct > 50 or unknown_confidence > 0:
            trust_level = 'low'
        elif heuristic_pct > 20:
            trust_level = 'mixed'
        else:
            trust_level = 'high'

    # v1.4 break: the aggregate key renames 'datasheet-backed' (hyphen)
    # to 'datasheet_backed' (underscore) to match the typed envelope
    # primitive at analyzer_envelope.ByConfidence. The per-finding
    # `confidence` value is unchanged — only this rollup key moves.
    by_confidence_out = {
        'deterministic': by_confidence.get('deterministic', 0),
        'heuristic': by_confidence.get('heuristic', 0),
        'datasheet_backed': by_confidence.get('datasheet-backed', 0),
    }
    result = {
        'total_findings': total,
        'trust_level': trust_level,
        'by_confidence': by_confidence_out,
        'by_evidence_source': by_evidence,
        # None when no findings — avoids "100% coverage of nothing"
        # misleading aggregates in downstream consumers.
        'provenance_coverage_pct': round(100 * has_provenance / total, 1) if total else None,
    }
    if unknown_confidence:
        result['unknown_confidence'] = unknown_confidence
    if unknown_evidence:
        result['unknown_evidence_source'] = unknown_evidence
    if bom_coverage is not None:
        result['bom_coverage'] = bom_coverage
    return result


# ---------------------------------------------------------------------------
# Deterministic ordering for findings lists
# ---------------------------------------------------------------------------

def sort_findings(findings):
    """Sort a findings list in-place by a stable composite key.

    Produces deterministic output across runs so baseline snapshots stay
    byte-identical and git diffs stay minimal.  Sort key:

        (rule_id, detector, sorted_components, sorted_nets, summary)

    Also sorts each finding's ``components``, ``nets``, and ``pins`` lists
    in place so upstream set/dict iteration order doesn't surface as drift
    in the output.  Ties fall through to ``summary`` as the final
    disambiguator.  Non-dict entries are tolerated (sorted to the end).

    Args:
        findings: List of finding dicts.  Mutated in place.

    Returns:
        The same list (for chaining convenience).
    """
    # First pass: canonicalize nested list fields within each finding so
    # set-iteration order doesn't leak into output.
    for f in findings:
        if not isinstance(f, dict):
            continue
        for key in ('components', 'nets', 'pins'):
            v = f.get(key)
            if isinstance(v, list) and all(not isinstance(x, (dict, list)) for x in v):
                f[key] = sorted(v, key=str)

    def _key(f):
        if not isinstance(f, dict):
            return (1, '', '', '', '', '')
        comps = f.get('components') or []
        nets = f.get('nets') or []
        first_comp = str(comps[0]) if comps else ''
        first_net = str(nets[0]) if nets else ''
        return (
            0,
            str(f.get('rule_id') or ''),
            str(f.get('detector') or ''),
            first_comp,
            first_net,
            str(f.get('summary') or ''),
        )
    findings.sort(key=_key)
    return findings


# ---------------------------------------------------------------------------
# Detector name constants — avoids string typos across consumers
# ---------------------------------------------------------------------------

class Det:
    """Detector name constants for filtering findings."""
    # Signal detectors
    VOLTAGE_DIVIDERS = 'detect_voltage_dividers'
    RC_FILTERS = 'detect_rc_filters'
    LC_FILTERS = 'detect_lc_filters'
    CRYSTAL_CIRCUITS = 'detect_crystal_circuits'
    OPAMP_CIRCUITS = 'detect_opamp_circuits'
    TRANSISTOR_CIRCUITS = 'detect_transistor_circuits'
    BRIDGE_CIRCUITS = 'detect_bridge_circuits'
    LED_DRIVERS = 'detect_led_drivers'
    POWER_REGULATORS = 'detect_power_regulators'
    INTEGRATED_LDOS = 'detect_integrated_ldos'
    DECOUPLING = 'detect_decoupling'
    CURRENT_SENSE = 'detect_current_sense'
    PROTECTION_DEVICES = 'detect_protection_devices'
    DESIGN_OBSERVATIONS = 'detect_design_observations'
    VOLTAGE_DERATING = 'analyze_voltage_derating'
    # Domain detectors
    BUZZER_SPEAKERS = 'detect_buzzer_speakers'
    KEY_MATRICES = 'detect_key_matrices'
    ISOLATION_BARRIERS = 'detect_isolation_barriers'
    ETHERNET_INTERFACES = 'detect_ethernet_interfaces'
    HDMI_DVI_INTERFACES = 'detect_hdmi_dvi_interfaces'
    LVDS_INTERFACES = 'detect_lvds_interfaces'
    MEMORY_INTERFACES = 'detect_memory_interfaces'
    RF_CHAINS = 'detect_rf_chains'
    RF_MATCHING = 'detect_rf_matching'
    BMS_SYSTEMS = 'detect_bms_systems'
    BATTERY_CHARGERS = 'detect_battery_chargers'
    MOTOR_DRIVERS = 'detect_motor_drivers'
    ADDRESSABLE_LEDS = 'detect_addressable_leds'
    DEBUG_INTERFACES = 'detect_debug_interfaces'
    POWER_PATH = 'detect_power_path'
    ADC_CIRCUITS = 'detect_adc_circuits'
    RESET_SUPERVISORS = 'detect_reset_supervisors'
    CLOCK_DISTRIBUTION = 'detect_clock_distribution'
    DISPLAY_INTERFACES = 'detect_display_interfaces'
    SENSOR_INTERFACES = 'detect_sensor_interfaces'
    LEVEL_SHIFTERS = 'detect_level_shifters'
    AUDIO_CIRCUITS = 'detect_audio_circuits'
    LED_DRIVER_ICS = 'detect_led_driver_ics'
    RTC_CIRCUITS = 'detect_rtc_circuits'
    THERMOCOUPLE_RTD = 'detect_thermocouple_rtd'
    WIRELESS_MODULES = 'detect_wireless_modules'
    TRANSFORMER_FEEDBACK = 'detect_transformer_feedback'
    I2C_ADDRESS_CONFLICTS = 'detect_i2c_address_conflicts'
    ENERGY_HARVESTING = 'detect_energy_harvesting'
    PWM_LED_DIMMING = 'detect_pwm_led_dimming'
    HEADPHONE_JACK = 'detect_headphone_jack'
    SOLDER_JUMPERS = 'detect_solder_jumpers'
    LABEL_ALIASES = 'detect_label_aliases'
    POWER_PIN_DC_PATH = 'audit_power_pin_dc_paths'
    # Audit detectors
    ESD_AUDIT = 'audit_esd_protection'
    LED_AUDIT = 'audit_led_circuits'
    CONNECTOR_GROUND_AUDIT = 'audit_connector_ground_distribution'
    RAIL_SOURCE_AUDIT = 'audit_rail_sources'
    SOURCING_GATE = 'audit_sourcing_gate'
    DATASHEET_COVERAGE = 'audit_datasheet_coverage'
    # Connectivity detectors
    CONNECTIVITY_SINGLE_PIN = 'analyze_connectivity'
    # Validation detectors
    PULLUPS = 'validate_pullups'
    VOLTAGE_LEVELS = 'validate_voltage_levels'
    I2C_BUS = 'validate_i2c_bus'
    SPI_BUS = 'validate_spi_bus'
    CAN_BUS = 'validate_can_bus'
    USB_BUS = 'validate_usb_bus'
    POWER_SEQUENCING = 'validate_power_sequencing'
    LED_RESISTORS = 'validate_led_resistors'
    FEEDBACK_STABILITY = 'validate_feedback_stability'


# ---------------------------------------------------------------------------
# Finding filter helpers — used by all consumers of analyzer JSON output
# ---------------------------------------------------------------------------

def get_findings(data, detector=None,
                 rule_prefix=None,
                 category=None):
    """Filter findings from an analyzer result dict.

    Args:
        data: Analyzer result dict with top-level 'findings' key.
        detector: Filter by detector name (e.g., Det.POWER_REGULATORS).
        rule_prefix: Filter by rule_id prefix (e.g., 'PU-').
        category: Filter by category (e.g., 'signal_integrity').

    Returns:
        List of matching finding dicts.
    """
    findings = data.get('findings', [])
    if detector:
        return [f for f in findings if f.get('detector') == detector]
    if rule_prefix:
        return [f for f in findings if f.get('rule_id', '').startswith(rule_prefix)]
    if category:
        return [f for f in findings if f.get('category') == category]
    return list(findings)


def group_findings(data):
    """Group findings by detector name.

    Returns:
        Dict mapping detector name to list of findings.
        Usage: group_findings(schematic).get(Det.POWER_REGULATORS, [])
    """
    groups = {}
    for f in data.get('findings', []):
        groups.setdefault(f.get('detector', ''), []).append(f)
    return groups


# ---------------------------------------------------------------------------
# Detection-type key mapping — adapter between the flat findings[] `detector`
# namespace and the detection-type keys used by detection_schema.SCHEMAS.
# Consumed by what_if.py and diff_analysis.py.
# ---------------------------------------------------------------------------

DETECTOR_TO_SCHEMA_KEY = {
    "detect_power_regulators": "power_regulators",
    "detect_integrated_ldos": "power_regulators",
    "detect_voltage_dividers": "voltage_dividers",
    "detect_rc_filters": "rc_filters",
    "detect_lc_filters": "lc_filters",
    "detect_crystal_circuits": "crystal_circuits",
    "detect_decoupling": "decoupling_analysis",
    "detect_current_sense": "current_sense",
    "detect_protection_devices": "protection_devices",
    "detect_opamp_circuits": "opamp_circuits",
    "detect_transistor_circuits": "transistor_circuits",
    "detect_bridge_circuits": "bridge_circuits",
    "detect_rf_matching": "rf_matching",
    "detect_rf_chains": "rf_chains",
    "detect_bms_systems": "bms_systems",
    "detect_battery_chargers": "battery_chargers",
    "detect_motor_drivers": "motor_drivers",
    "detect_ethernet_interfaces": "ethernet_interfaces",
    "detect_buzzer_speakers": "buzzer_speaker_circuits",
    "detect_key_matrices": "key_matrices",
    "detect_isolation_barriers": "isolation_barriers",
    "detect_hdmi_dvi_interfaces": "hdmi_dvi_interfaces",
    "detect_lvds_interfaces": "lvds_interfaces",
    "detect_memory_interfaces": "memory_interfaces",
    "detect_addressable_leds": "addressable_led_chains",
    "detect_debug_interfaces": "debug_interfaces",
    "detect_adc_circuits": "adc_circuits",
    "detect_reset_supervisors": "reset_supervisors",
    "detect_clock_distribution": "clock_distribution",
    "detect_display_interfaces": "display_interfaces",
    "detect_sensor_interfaces": "sensor_interfaces",
    "detect_level_shifters": "level_shifters",
    "detect_audio_circuits": "audio_circuits",
    "detect_led_driver_ics": "led_driver_ics",
    "detect_rtc_circuits": "rtc_circuits",
    "detect_thermocouple_rtd": "thermocouple_rtd",
    "detect_wireless_modules": "wireless_modules",
    "detect_transformer_feedback": "transformer_feedback",
    "detect_i2c_address_conflicts": "i2c_address_conflicts",
    "detect_energy_harvesting": "energy_harvesting",
    "detect_pwm_led_dimming": "pwm_led_dimming",
    "detect_headphone_jack": "headphone_jacks",
    "detect_power_path": "power_path",
    "detect_design_observations": "design_observations",
    "detect_led_drivers": "led_drivers",
    "audit_esd_protection": "esd_coverage_audit",
    "audit_led_circuits": "led_audit",
    "audit_connector_ground_distribution": "connector_ground_audit",
}


def group_findings_by_detection_type(data):
    """Group flat findings[] by detection-type key.

    Returns {detection_type_key: [finding, ...]} — an adapter between the
    flat findings[] `detector` namespace and the detection-type keys used
    by detection_schema.SCHEMAS / SIGNAL_REGISTRY.  Detector names are
    mapped via DETECTOR_TO_SCHEMA_KEY so downstream code (SCHEMAS, SPICE
    templates, what_if --fix) works unchanged.

    Detects pre-v1.3 JSON (signal_analysis wrapper, no findings[]) and
    emits a warning to stderr.  Returns empty dict in that case — callers
    should check is_old_schema() first if they need to abort early.
    """
    if "signal_analysis" in data and "findings" not in data:
        import sys
        print("Warning: this JSON uses the pre-v1.3 signal_analysis wrapper "
              "format. Re-run the analyzer to produce the current findings[] "
              "format.", file=sys.stderr)
        return {}
    sa = {}
    for f in data.get("findings", []):
        det = f.get("detector", "")
        if det:
            key = DETECTOR_TO_SCHEMA_KEY.get(det, det)
            sa.setdefault(key, []).append(f)
    return sa


def is_old_schema(data):
    """Return True if data uses the pre-v1.3 signal_analysis wrapper format."""
    return "signal_analysis" in data and "findings" not in data


def strip_llm_overlays(data):
    """Recursively remove all keys starting with 'llm_'. Phase 4 spec §3.4 / HI-3.

    Canonical implementation lives in
    skills/kicad/review/scripts/merge_annotations.py; this is a duplicate
    so analyzers/consumers don't need to take a dep on the review
    sub-component to compute the deterministic baseline. Both
    implementations are byte-equivalent; harness B-test asserts.
    """
    if isinstance(data, dict):
        return {k: strip_llm_overlays(v) for k, v in data.items()
                if not k.startswith("llm_")}
    if isinstance(data, list):
        return [strip_llm_overlays(item) for item in data]
    return data
