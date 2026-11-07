"""Datasheet verification bridge for kicad-happy.

Compares extracted datasheet specifications against actual schematic
connections. Produces findings for voltage violations, missing required
external components, and decoupling inadequacy.

Requires datasheets/extracted/ cache populated by the LLM extraction
pipeline (via sync_datasheets_digikey + Claude extraction).
"""

import os
import re
import sys
from pathlib import Path

# Allow imports from same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datasheet_types.cache_reader import MAX_CACHE_BYTES, read_json_object, safe_extract_dir  # noqa: E402
from distributor_core.manifest import manifest_file_path  # noqa: E402


MAX_EXTRACTION_BYTES = MAX_CACHE_BYTES


def _load_extraction(extract_dir: str, mpn: str) -> dict:
    """Load extraction JSON for an MPN. Always returns dict; never None.

    Returns {} only for: missing dir, missing MPN, file not found, JSON
    parse error, undecodable, non-object, symlinked or oversized file, or
    OSError. Quality is NOT a gate here — callers emit an `extraction_quality_low` info finding via
    `_quality_finding` instead.

    Two cache shapes supported:
    - v1.4: extraction.quality_score on 0-100 scale.
    - v1.3 legacy: extraction_metadata.extraction_score (cache manager) or
      meta.extraction_score on 0-10 scale.
    """
    if not extract_dir or not mpn:
        return {}

    # Preserve dots and hyphens — planner/merger write literal MPN-named
    # files (`ABM8G-106-12.000MHZ-T.json`), so the legacy positional path
    # MUST match what they wrote. Aligned with
    # datasheet_types.cache_reader.sanitize_mpn and the flag-mode regex in
    # _cli_v14 below.
    sanitized = re.sub(r'[^A-Za-z0-9_.-]', '_', mpn.strip())

    # Direct file lookup
    path = os.path.join(extract_dir, f"{sanitized}.json")
    if os.path.isfile(path):
        return _read_extraction_file(path)

    # Manifest-based lookup; try manifest.json, fall back to legacy
    # index.json. The cache manager keys entries by a hashed file stem and
    # records the requested MPN in `mpn`, so match either.
    idx_path = os.path.join(extract_dir, "manifest.json")
    if not os.path.isfile(idx_path):
        idx_path = os.path.join(extract_dir, "index.json")
    if os.path.isfile(idx_path):
        try:
            idx = read_json_object(idx_path) or {}
            entries = idx.get("extractions", {})
            for k, v in entries.items():
                if not isinstance(v, dict):
                    continue
                if (k.upper() != sanitized.upper()
                        and str(v.get("mpn") or "").strip().upper() != mpn.strip().upper()):
                    continue
                fpath = manifest_file_path(Path(extract_dir), v.get("file"))
                if fpath is not None and fpath.is_file():
                    return _read_extraction_file(str(fpath))
        except (ValueError, OSError, AttributeError):
            pass

    return {}


def _read_extraction_file(path: str) -> dict:
    """Read one extraction file; {} when unreadable, undecodable, symlinked,
    oversized or not an object."""
    return read_json_object(path) or {}


def _is_sectioned_format(extraction: dict) -> bool:
    """Return True if extraction is sectioned (has a top-level 'base' key)."""
    return isinstance(extraction.get("base"), dict)


def _domain_absolute_voltage_max(base: dict, domain: str) -> float | None:
    """Resolve a per-domain abs-max voltage from base.absolute_max.

    Tries key patterns: "<domain>_max", "<domain>".  Returns the SpecValue
    `max` field (first entry) or None if unavailable.
    """
    abs_max = base.get("absolute_max") or {}
    for key in (f"{domain}_max", domain):
        sv_list = abs_max.get(key)
        if isinstance(sv_list, list) and sv_list:
            sv = sv_list[0]
            if isinstance(sv, dict):
                v = sv.get("max")
                if isinstance(v, (int, float)):
                    return v
    return None


def _domain_operating_voltage_max(base: dict, domain: str) -> float | None:
    """Resolve a per-domain operating-max voltage from base.recommended_operating."""
    rec_op = base.get("recommended_operating") or {}
    sv_list = rec_op.get(domain)
    if isinstance(sv_list, list) and sv_list:
        sv = sv_list[0]
        if isinstance(sv, dict):
            v = sv.get("max")
            if isinstance(v, (int, float)):
                return v
    return None


def _legacy_verifier_view(extraction: dict) -> dict:
    """Return a flat legacy view of an extraction dict for use by the verifiers.

    Flat legacy (has 'pins'): returned unchanged.
    Sectioned (base/pinout, has 'base'): synthesize the flat legacy keys the
    verifiers READ:
      - 'pins': list of dicts with 'number', 'name', 'type', 'voltage_abs_max',
        'voltage_operating_max'.  One entry per number of each base.pinout[]
        record, with voltage limits resolved per-domain from
        base.absolute_max / base.recommended_operating via power_domain.
        A pin's own absolute_max / recommended SpecValue lists
        (pinout.schema.json) override the domain values. A 5 V-tolerant pin
        takes only its own limits: the domain's are not its limits, so
        without its own it gets no check.
        'required_external' is NOT synthesised (no v2 equivalent) — verifiers
        skip pins without it, so externals/decoupling remain unverifiable.
      - 'application_circuit': NOT synthesised — no v2 equivalent key.
        verify_decoupling short-circuits on its absence.

    Returns {} (empty) if extraction is neither shape.
    """
    if not extraction:
        return extraction
    # v1: already has pins list at top level
    if "pins" in extraction:
        return extraction
    # sectioned: synthesise flat legacy pins from base.pinout
    if not _is_sectioned_format(extraction):
        return extraction
    base = extraction["base"]
    pinout = base.get("pinout") or []
    v1_pins = []
    for pin in pinout:
        if not isinstance(pin, dict):
            continue
        numbers = pin.get("numbers") or []
        if isinstance(numbers, str):
            numbers = [numbers]
        numbers = [str(n) for n in numbers if str(n)]
        if not numbers:
            continue
        pin_type = pin.get("type") or ""
        domain = pin.get("power_domain")
        v_abs_max = _spec_max_voltage(pin.get("absolute_max"))
        if not isinstance(v_abs_max, (int, float)):
            v_abs_max = None
        v_op_max = _spec_max_voltage(pin.get("recommended"))
        if not isinstance(v_op_max, (int, float)):
            v_op_max = None
        if domain and pin.get("is_5v_tolerant") is not True:
            if v_abs_max is None:
                v_abs_max = _domain_absolute_voltage_max(base, domain)
            if v_op_max is None:
                v_op_max = _domain_operating_voltage_max(base, domain)
        for pin_number in numbers:
            v1_pins.append({
                "number": pin_number,
                "name": pin.get("name") or f"pin {pin_number}",
                "type": pin_type,
                "voltage_abs_max": v_abs_max,
                "voltage_operating_max": v_op_max,
                # required_external intentionally absent — no v2 equivalent
            })
    # Build the minimal v1 view; no application_circuit (no v2 equivalent)
    return {"pins": v1_pins, "_v2_adapted": True}


def _not_verifiable_finding(mpn: str, detail: str) -> dict:
    """Info finding when a trust-gate-passing extraction has no usable data
    for a verifier.  Degradation must be VISIBLE, never silent.
    """
    return {
        "type": "extraction_not_verifiable",
        "severity": "info",
        "mpn": mpn,
        "detail": detail,
    }


def _v13_score(extraction: dict):
    """Legacy 0-10 score: the cache manager's `extraction_metadata`, else `meta`."""
    for block in ("extraction_metadata", "meta"):
        meta = extraction.get(block)
        score = meta.get("extraction_score") if isinstance(meta, dict) else None
        if isinstance(score, (int, float)):
            return score
    return None


def _v14_score(extraction: dict):
    """v1.4 0-100 score from the `extraction` block, or None."""
    block = extraction.get("extraction")
    score = block.get("quality_score") if isinstance(block, dict) else None
    return score if isinstance(score, (int, float)) else None


def _passes_trust_gate(extraction: dict) -> bool:
    """Return True if extraction quality is acceptable (or unknown).

    v1.4: extraction.quality_score 0-100, threshold 60.
    v1.3: extraction_metadata (else meta).extraction_score 0-10, threshold 6.0.
    No quality metadata at all: pass (don't gate; let downstream decide).
    """
    quality_v14 = _v14_score(extraction)
    if quality_v14 is not None:
        return quality_v14 >= 60
    quality_v13 = _v13_score(extraction)
    if isinstance(quality_v13, (int, float)):
        return quality_v13 >= 6.0
    return True


def _quality_finding(mpn, extraction):
    """Info finding when extraction quality is below the trust threshold.

    Quality is visible data, not a gate. Returns None
    when the extraction passes the threshold or carries no score.
    """
    if not extraction or _passes_trust_gate(extraction):
        return None
    q14 = _v14_score(extraction)
    q13 = _v13_score(extraction)
    score = q14 if q14 is not None else q13
    return {
        "type": "extraction_quality_low",
        "severity": "info",
        "mpn": mpn,
        "quality_score": score,
        "detail": (f"{mpn}: extraction quality score {score} is below the "
                   f"trust threshold; verification findings for this part "
                   f"are based on a low-quality extraction"),
    }


def _resolve_extract_dir(project_dir: str) -> str:
    """The project's own datasheets/extracted/ directory, or "" when absent.
    The parent folder is not searched: for a project in a shared temp dir it
    could hold extractions planted by another user."""
    c = os.path.join(project_dir, "datasheets", "extracted")
    return c if os.path.isdir(c) and safe_extract_dir(c) is not None else ""


def _estimate_net_voltage(net_name: str, rail_voltages: dict) -> float:
    """Estimate the voltage on a net from rail_voltages or name parsing."""
    if not net_name:
        return None

    # Direct lookup in rail_voltages
    v = rail_voltages.get(net_name)
    if v is not None:
        return v

    # Parse from name: +3V3 → 3.3, +5V → 5.0, 12V0 → 12.0
    nu = net_name.upper().lstrip("+").rstrip("V")
    # VnnVn format: 3V3 → 3.3
    m = re.match(r'^(\d+)V(\d+)$', nu)
    if m:
        return float(f"{m.group(1)}.{m.group(2)}")
    # Plain voltage: 5V → 5.0, 12V → 12.0
    m = re.match(r'^(\d+\.?\d*)V?$', nu)
    if m:
        return float(m.group(1))

    return None


def verify_pin_voltages(components: list, nets: dict, extraction_dir: str,
                        rail_voltages: dict) -> list:
    """P1: Verify pin voltage boundaries against datasheet abs max / operating ranges.

    For each IC with an extraction, checks every pin's connected net voltage
    against the pin's voltage_abs_max and voltage_operating_max from the
    extraction.

    Returns list of finding dicts.
    """
    findings = []
    seen_quality_mpns: set = set()

    for comp in components:
        if comp.get("type") != "ic":
            continue
        ref = comp["reference"]
        mpn = comp.get("mpn") or comp.get("value", "")
        if not mpn or mpn == ref:
            continue

        extraction = _load_extraction(extraction_dir, mpn)
        if mpn not in seen_quality_mpns:
            seen_quality_mpns.add(mpn)
            qf = _quality_finding(mpn, extraction)
            if qf:
                findings.append(qf)
        if not extraction:
            continue
        view = _legacy_verifier_view(extraction)
        if not view or not view.get("pins"):
            # Loud only for v2-adapted views; v1 caches without
            # pins keep the pre-adapter silent-skip behavior byte-identical.
            if view.get("_v2_adapted") and _passes_trust_gate(extraction):
                findings.append(_not_verifiable_finding(
                    mpn,
                    "pin-voltage checks could not run: extraction has no usable pin voltage data",
                ))
            continue

        pin_nets = comp.get("pin_nets", {})
        if not pin_nets:
            continue

        # Build pin lookup from extraction: pin_number → pin_data
        ext_pins = {}
        for p in view["pins"]:
            pnum = str(p.get("number", ""))
            if pnum:
                ext_pins[pnum] = p

        for pin_num, net_name in pin_nets.items():
            ext_pin = ext_pins.get(pin_num)
            if not ext_pin:
                continue

            # Skip GND pins
            pin_type = (ext_pin.get("type") or "").lower()
            if pin_type in ("ground", "gnd"):
                continue

            v_abs_max = ext_pin.get("voltage_abs_max")
            v_op_max = ext_pin.get("voltage_operating_max")
            net_voltage = _estimate_net_voltage(net_name, rail_voltages)

            if net_voltage is None:
                continue

            pin_name = ext_pin.get("name", f"pin {pin_num}")

            # Check abs max violation
            if v_abs_max is not None and net_voltage > v_abs_max:
                findings.append({
                    "type": "pin_voltage_abs_max_exceeded",
                    "severity": "error",
                    "ref": ref,
                    "mpn": mpn,
                    "pin_number": pin_num,
                    "pin_name": pin_name,
                    "net": net_name,
                    "net_voltage_V": net_voltage,
                    "abs_max_V": v_abs_max,
                    "margin_V": round(v_abs_max - net_voltage, 3),
                    "detail": (f"{ref} pin {pin_num} ({pin_name}) on {net_name} "
                               f"({net_voltage}V) exceeds absolute maximum "
                               f"({v_abs_max}V) by {net_voltage - v_abs_max:.2f}V"),
                })
            # Check operating range exceeded (warning, not critical)
            elif v_op_max is not None and net_voltage > v_op_max:
                margin_pct = (v_abs_max - net_voltage) / v_abs_max * 100 if v_abs_max else 0
                findings.append({
                    "type": "pin_voltage_operating_exceeded",
                    "severity": "error" if margin_pct < 10 else "warning",
                    "ref": ref,
                    "mpn": mpn,
                    "pin_number": pin_num,
                    "pin_name": pin_name,
                    "net": net_name,
                    "net_voltage_V": net_voltage,
                    "operating_max_V": v_op_max,
                    "abs_max_V": v_abs_max,
                    "detail": (f"{ref} pin {pin_num} ({pin_name}) on {net_name} "
                               f"({net_voltage}V) exceeds recommended operating "
                               f"maximum ({v_op_max}V)"),
                })

    return findings


def verify_required_externals(components: list, nets: dict, extraction_dir: str,
                              comp_lookup: dict) -> list:
    """P1: Verify required external components per datasheet pin specs.

    Checks pins with 'required_external' field in extraction — these are
    pins where the datasheet says "connect X here" (bypass cap, pull-up,
    inductor, etc.). Verifies something appropriate is actually connected.

    Returns list of finding dicts.
    """
    findings = []
    seen_quality_mpns: set = set()

    for comp in components:
        if comp.get("type") != "ic":
            continue
        ref = comp["reference"]
        mpn = comp.get("mpn") or comp.get("value", "")
        if not mpn or mpn == ref:
            continue

        extraction = _load_extraction(extraction_dir, mpn)
        if mpn not in seen_quality_mpns:
            seen_quality_mpns.add(mpn)
            qf = _quality_finding(mpn, extraction)
            if qf:
                findings.append(qf)
        if not extraction:
            continue
        view = _legacy_verifier_view(extraction)
        if not view or not view.get("pins"):
            # Loud only for v2-adapted views; v1 caches without
            # pins keep the pre-adapter silent-skip behavior byte-identical.
            if view.get("_v2_adapted") and _passes_trust_gate(extraction):
                findings.append(_not_verifiable_finding(
                    mpn,
                    "required-external checks could not run: extraction has no usable pin data",
                ))
            continue
        # v2-adapted views have pins but no required_external per pin
        if view.get("_v2_adapted") and _passes_trust_gate(extraction):
            findings.append(_not_verifiable_finding(
                mpn,
                "required-external checks could not run: "
                "v2 extraction format has no per-pin required_external data",
            ))

        pin_nets = comp.get("pin_nets", {})

        ext_pins = {}
        for p in view["pins"]:
            pnum = str(p.get("number", ""))
            if pnum:
                ext_pins[pnum] = p

        for pin_num, net_name in pin_nets.items():
            ext_pin = ext_pins.get(pin_num)
            if not ext_pin:
                continue

            required = ext_pin.get("required_external")
            if not required:
                continue

            pin_name = ext_pin.get("name", f"pin {pin_num}")
            pin_type = (ext_pin.get("type") or "").lower()

            # Skip ground pins (always connected)
            if pin_type in ("ground", "gnd"):
                continue

            # Check what's connected to this pin's net
            net_info = nets.get(net_name, {})
            net_pins = net_info.get("pins", []) if isinstance(net_info, dict) else []

            # Find other components on this net (excluding the IC itself)
            connected_refs = set()
            connected_types = set()
            for p in net_pins:
                c_ref = p.get("component", "")
                if c_ref and c_ref != ref:
                    connected_refs.add(c_ref)
                    c = comp_lookup.get(c_ref, {})
                    connected_types.add(c.get("type", ""))

            # Parse required_external for expected component types
            req_lower = required.lower()
            expected_types = set()
            if any(k in req_lower for k in ("cap", "capacitor", "decoupling", "bypass")):
                expected_types.add("capacitor")
            if any(k in req_lower for k in ("resistor", "pull-up", "pullup", "pull-down", "divider")):
                expected_types.add("resistor")
            if any(k in req_lower for k in ("inductor", "ferrite", "bead")):
                expected_types.update(("inductor", "ferrite_bead"))
            if any(k in req_lower for k in ("diode", "schottky")):
                expected_types.add("diode")

            if not expected_types:
                continue  # Can't parse requirement — skip

            # Check if any expected type is connected
            if not expected_types & connected_types:
                # Nothing matching the requirement is connected
                findings.append({
                    "type": "missing_required_external",
                    "severity": "error",
                    "ref": ref,
                    "mpn": mpn,
                    "pin_number": pin_num,
                    "pin_name": pin_name,
                    "net": net_name,
                    "required": required,
                    "expected_types": sorted(expected_types),
                    "connected_types": sorted(connected_types),
                    "detail": (f"{ref} pin {pin_num} ({pin_name}): datasheet requires "
                               f"\"{required}\" but none found on net {net_name}"),
                })

    return findings


# Capacitance units, micro as "u", the micro sign or Greek mu.
_CAP_UNIT = r'(?:uf|\u00b5f|\u03bcf|nf|pf)'
# A count is not followed by more digits/letters or by a capacitance unit.
_NOT_A_VALUE = r'(?![\w.]|\s*' + _CAP_UNIT + ')'


def _parse_cap_recommendation(text: str) -> dict:
    """Parse a capacitor recommendation string into structured requirements.

    Examples:
        "10uF ceramic, X5R or X7R" -> {min_farads: 10e-6, count: 1, dielectric: ["X5R","X7R"]}
        "22uF ceramic x2" -> {min_farads: 22e-6, count: 2}
        "2 x 10uF" -> {min_farads: 10e-6, count: 2}
        "100nF" -> {min_farads: 100e-9, count: 1}
    """
    from kicad_core.values import parse_value

    result = {"min_farads": None, "count": 1, "dielectric": [], "max_distance_mm": None}

    if not text:
        return result

    text_lower = text.lower()

    # Count: a number multiplying a capacitance ("2 x 10uF"), an "x2" glued
    # to the unit ("22uFx2"), else a standalone "x2"/"x 2" that is not itself
    # followed by a value. The digit of X5R/X7R is a temperature code and
    # "max 10mm" / "10x10mm" are not quantities.
    count_match = (re.search(r'(?<![\w.])(\d+)\s*[x\u00d7]\s*\d+\.?\d*\s*' + _CAP_UNIT, text_lower)
                   or re.search(_CAP_UNIT + r'\s*[x\u00d7]\s*(\d+)' + _NOT_A_VALUE, text_lower)
                   or re.search(r'(?<![a-z0-9])[x\u00d7]\s*(\d+)' + _NOT_A_VALUE, text_lower))
    if count_match:
        result["count"] = int(count_match.group(1))

    # Extract distance: "within 10mm", "< 5mm"
    dist_match = re.search(r'within\s+(\d+\.?\d*)\s*mm', text_lower)
    if not dist_match:
        dist_match = re.search(r'<\s*(\d+\.?\d*)\s*mm', text_lower)
    if dist_match:
        result["max_distance_mm"] = float(dist_match.group(1))

    # Extract dielectric: X5R, X7R, C0G, NP0
    for d in ("X5R", "X7R", "X7S", "C0G", "NP0", "X6S"):
        if d.lower() in text_lower:
            result["dielectric"].append(d)

    # Extract capacitance value
    cap_match = re.search(r'(\d+\.?\d*)\s*(uF|\u00b5F|\u03bcF|nF|pF|u|\u00b5|\u03bc|n|p)', text, re.IGNORECASE)
    if cap_match:
        val_str = cap_match.group(1) + cap_match.group(2)
        parsed = parse_value(val_str, component_type="capacitor")
        if parsed:
            result["min_farads"] = parsed

    return result


_RECOMMENDATION_ROLES = {
    "input_cap_recommended": ("input",),
    "output_cap_recommended": ("output",),
    "decoupling_cap": ("input", "output"),
}


def _power_pin_roles(pin: dict) -> tuple:
    """Supply roles of an extracted power pin. The extraction schema lets
    power pins carry direction "passive" or none; their role then comes from
    the pin's function (VIN/VOUT; SW, FB and GND pins supply nothing), else
    its name (an OUT or VO<n> pin is an output, any other a supply input)."""
    direction = (pin.get("direction") or "").lower()
    if direction == "bidirectional":
        return ("input", "output")
    if direction in ("input", "output"):
        return (direction,)
    if direction not in ("passive", ""):
        return ()
    function = (pin.get("function") or "").upper()
    if function in ("SW", "FB", "GND"):
        return ()
    if function in ("VIN", "VOUT"):
        return ("input",) if function == "VIN" else ("output",)
    name = (pin.get("name") or "").upper()
    if "OUT" in name or re.fullmatch(r"VO\d*", name):
        return ("output",)
    return ("input",)


def _ic_ground_nets(pin_nets: dict, ext_pins: dict) -> set:
    """Nets on the IC's own ground pins (type ground, or function GND on a
    pin typed power): a PGND2 or AVSS that the ground-name rules miss."""
    out = set()
    for pin_num, net_name in pin_nets.items():
        ep = ext_pins.get(pin_num) or {}
        if ((ep.get("type") or "").lower() == "ground"
                or (ep.get("function") or "").upper() == "GND"):
            out.add(net_name)
    return out


def _on_ground(net_name, ic_ground: set) -> bool:
    from kicad_core.netnames import is_ground_name
    return net_name in ic_ground or is_ground_name(net_name)


def verify_decoupling(components: list, nets: dict, extraction_dir: str,
                      comp_lookup: dict, parsed_values: dict) -> list:
    """P2: Verify per-IC decoupling against datasheet application circuit.

    For each IC with an extraction containing application_circuit.decoupling_cap
    or input_cap_recommended / output_cap_recommended, checks that the actual
    caps on power pins meet the requirements (count, value, type).

    Returns list of finding dicts.
    """
    findings = []
    seen_quality_mpns: set = set()

    for comp in components:
        if comp.get("type") != "ic":
            continue
        ref = comp["reference"]
        mpn = comp.get("mpn") or comp.get("value", "")
        if not mpn or mpn == ref:
            continue

        extraction = _load_extraction(extraction_dir, mpn)
        if mpn not in seen_quality_mpns:
            seen_quality_mpns.add(mpn)
            qf = _quality_finding(mpn, extraction)
            if qf:
                findings.append(qf)
        if not extraction:
            continue
        view = _legacy_verifier_view(extraction)
        if not view or not view.get("application_circuit"):
            # Loud only for v2-adapted views; v1 caches that never
            # populated the optional application_circuit field keep the
            # pre-adapter silent-skip behavior byte-identical.
            if view.get("_v2_adapted") and _passes_trust_gate(extraction):
                findings.append(_not_verifiable_finding(
                    mpn,
                    "decoupling checks could not run: extraction has no application_circuit data",
                ))
            continue
        app_circuit = view["application_circuit"]

        pin_nets = comp.get("pin_nets", {})
        ext_pins = {str(p.get("number", "")): p for p in view.get("pins", [])}

        # Collect recommendations
        recommendations = []
        for key in ("input_cap_recommended", "output_cap_recommended", "decoupling_cap"):
            text = app_circuit.get(key)
            if text:
                recommendations.append((key, text, _parse_cap_recommendation(text)))

        if not recommendations:
            continue

        ic_ground = _ic_ground_nets(pin_nets, ext_pins)

        # Supply nets per role; a recommendation is checked only on the
        # pins of its role, and a symbol without such a pin is skipped.
        role_nets = {"input": set(), "output": set()}
        for pin_num, net_name in pin_nets.items():
            ep = ext_pins.get(pin_num)
            if not ep or (ep.get("type") or "").lower() != "power" or _on_ground(net_name, ic_ground):
                continue
            for role in _power_pin_roles(ep):
                role_nets[role].add(net_name)

        for key, text, req in recommendations:
            if req["min_farads"] is None:
                continue
            nets_for_key = sorted(set().union(*(role_nets[r] for r in _RECOMMENDATION_ROLES[key])))
            if not nets_for_key:
                continue

            # A bypass cap returns to ground; a cap listed without its
            # terminal nets is taken as given.
            caps, seen = [], set()
            for net_name in nets_for_key:
                net_info = nets.get(net_name, {})
                for p in net_info.get("pins", []) if isinstance(net_info, dict) else []:
                    c_ref = p.get("component", "")
                    c = comp_lookup.get(c_ref, {})
                    if c.get("type") != "capacitor" or c_ref == ref or c_ref in seen:
                        continue
                    cap_nets = c.get("pin_nets")
                    if isinstance(cap_nets, dict) and cap_nets and not any(
                            n != net_name and _on_ground(n, ic_ground) for n in cap_nets.values()):
                        continue
                    seen.add(c_ref)
                    caps.append({
                        "ref": c_ref,
                        "value": c.get("value", ""),
                        "farads": parsed_values.get(c_ref, 0),
                        "net": net_name,
                    })

            # Find matching caps (value >= recommended)
            matching = [c for c in caps if c["farads"] >= req["min_farads"] * 0.8]
            total_matching = len(matching)

            if total_matching < req["count"]:
                severity = "error" if total_matching == 0 else "warning"
                findings.append({
                    "type": "decoupling_insufficient",
                    "severity": severity,
                    "ref": ref,
                    "mpn": mpn,
                    "requirement_key": key,
                    "requirement_text": text,
                    "required_count": req["count"],
                    "required_min_farads": req["min_farads"],
                    "actual_count": total_matching,
                    "actual_caps": [{"ref": c["ref"], "value": c["value"]} for c in caps],
                    "detail": (f"{ref} ({mpn}): datasheet recommends \"{text}\" "
                               f"but found {total_matching}/{req['count']} matching caps "
                               f"on power pins"),
                })

    return findings


def _merge_ic_units(components):
    """One entry per physical IC: the analysis lists each unit of a
    multi-unit part separately, with only that unit's pins. Units merge when
    reference, lib_id and value agree; a repeated unit number starts a second
    part, and an unannotated `U?` reference never merges."""
    out, groups = [], {}
    for c in components:
        ref = c.get("reference", "")
        if c.get("type") != "ic" or not ref or ref.endswith("?"):
            out.append(c)
            continue
        key = (ref, c.get("lib_id", ""), c.get("value", ""))
        unit = c.get("unit") or 1
        group = groups.get(key)
        if group is None or unit in group["units"]:
            merged = dict(c)
            merged["pin_nets"] = dict(c.get("pin_nets") or {})
            group = {"entry": merged, "units": {unit}}
            groups[key] = group
            out.append(merged)
            continue
        group["units"].add(unit)
        entry = group["entry"]
        for pin, net in (c.get("pin_nets") or {}).items():
            entry["pin_nets"].setdefault(pin, net)
        if not entry.get("mpn") and c.get("mpn"):
            entry["mpn"] = c["mpn"]
    return out


def run_datasheet_verification(analysis: dict, project_dir: str = "") -> dict:
    """Run all datasheet verification checks.

    Args:
        analysis: Full schematic analysis JSON (from analyze_schematic.py)
        project_dir: Project directory for finding datasheets/extracted/

    Returns dict with:
        findings: list of verification findings
        summary: {ics_checked, ics_with_extractions, total_findings, by_severity}
    """
    components = _merge_ic_units(analysis.get("components", []))
    nets = analysis.get("nets", {})
    rail_voltages = analysis.get("rail_voltages", {})
    parsed_values = {}
    comp_lookup = {}
    for c in components:
        ref = c.get("reference", "")
        comp_lookup[ref] = c
        pv = c.get("parsed_value")
        if isinstance(pv, (int, float)):
            parsed_values[ref] = pv
        elif isinstance(pv, dict):
            parsed_values[ref] = pv.get("value", 0)

    # Resolve extraction directory
    if not project_dir:
        src_file = analysis.get("file", "")
        if src_file:
            project_dir = os.path.dirname(os.path.abspath(src_file))
    extract_dir = _resolve_extract_dir(project_dir) if project_dir else ""

    if not extract_dir:
        return {"findings": [], "summary": {
            "ics_checked": 0, "ics_with_extractions": 0,
            "total_findings": 0, "by_severity": {},
            "note": "No datasheets/extracted/ directory found",
        }}

    # Count ICs with extractions
    ic_count = 0
    ic_with_ext = 0
    for c in components:
        if c.get("type") == "ic":
            ic_count += 1
            mpn = c.get("mpn") or c.get("value", "")
            if mpn and _load_extraction(extract_dir, mpn):
                ic_with_ext += 1

    # Run checks
    all_findings = []
    all_findings.extend(verify_pin_voltages(components, nets, extract_dir, rail_voltages))
    all_findings.extend(verify_required_externals(components, nets, extract_dir, comp_lookup))
    all_findings.extend(verify_decoupling(components, nets, extract_dir, comp_lookup, parsed_values))

    # Merge per-MPN info findings emitted independently by each verifier:
    # - extraction_not_verifiable: combine details into one finding per MPN.
    # - extraction_quality_low: identical duplicates; keep the first per MPN
    #   (once per distinct MPN).
    nv_by_mpn: dict = {}
    seen_quality_low: set = set()
    other_findings: list = []
    for f in all_findings:
        ftype = f.get("type")
        if ftype == "extraction_not_verifiable":
            mpn_key = f.get("mpn", "")
            if mpn_key not in nv_by_mpn:
                nv_by_mpn[mpn_key] = f.copy()
            else:
                # Append additional detail from subsequent verifiers
                existing = nv_by_mpn[mpn_key]["detail"]
                extra = f.get("detail", "")
                if extra and extra not in existing:
                    nv_by_mpn[mpn_key]["detail"] = f"{existing}; {extra}"
        elif ftype == "extraction_quality_low":
            mpn_key = f.get("mpn", "")
            if mpn_key in seen_quality_low:
                continue
            seen_quality_low.add(mpn_key)
            other_findings.append(f)
        else:
            other_findings.append(f)
    # Reconstruct: non-nv findings first, then one nv per MPN
    all_findings = other_findings + list(nv_by_mpn.values())

    # Build severity summary
    by_severity = {}
    for f in all_findings:
        sev = f.get("severity", "info")
        by_severity[sev] = by_severity.get(sev, 0) + 1

    return {
        "findings": all_findings,
        "summary": {
            "ics_checked": ic_count,
            "ics_with_extractions": ic_with_ext,
            "total_findings": len(all_findings),
            "by_severity": by_severity,
        },
    }


# ---------------------------------------------------------------------------
# v1.4 extension: verify_v14_extraction
# ---------------------------------------------------------------------------

def _spec_max(sv_list):
    if isinstance(sv_list, list) and sv_list and isinstance(sv_list[0], dict):
        return sv_list[0].get("max")
    return None


def _spec_max_voltage(sv_list):
    """First SpecValue max with a voltage (or unspecified) unit.

    Per-pin absolute_max lists may mix voltage and current entries
    (pinout.schema.json) — comparing a current rating against net volts
    would fabricate false CRITICALs.
    """
    if not isinstance(sv_list, list):
        return None
    for sv in sv_list:
        if isinstance(sv, dict) and sv.get("unit") in (None, "", "V"):
            return sv.get("max")
    return None


def _all_pin_numbers(pinout):
    nums = set()
    for pin in pinout or []:
        for n in pin.get("numbers", []) or []:
            nums.add(str(n))
    return nums


_PIN_FIELDS_BY_CATEGORY = {
    "regulator": ("feedback_pin", "compensation_pin", "enable_pin", "power_good_pin", "vin_pin", "vout_pin"),
    "diode": (),
    "transistor": (),  # pin_assignment is a nested object — checked separately if needed
    "opamp": ("shutdown_pin",),
    "mcu": ("reset_pin",),  # boot_pins is a list-of-objects, not validated
    "crystal": (),
}


def verify_v14_extraction(extraction: dict) -> list[dict]:
    """Return inconsistencies in a v1.4 extraction JSON.

    Each finding: {path, severity ('warning'|'error'), description}.
    Empty list = clean.
    """
    issues: list[dict] = []
    base = extraction.get("base") or {}
    pinout = base.get("pinout") or []
    rec_op = base.get("recommended_operating") or {}
    abs_max = base.get("absolute_max") or {}

    # 1. power_domain references resolve to recommended_operating keys
    rec_keys = set(rec_op.keys())
    for i, pin in enumerate(pinout):
        pd = pin.get("power_domain")
        if pd is not None and pd not in rec_keys:
            issues.append({
                "path": f"base.pinout[{i}].power_domain",
                "severity": "warning",
                "description": f"power_domain {pd!r} does not resolve to a key in base.recommended_operating ({sorted(rec_keys)})",
            })

    # 2. min/max sanity within each SpecValue
    for block_name, block in (("recommended_operating", rec_op), ("absolute_max", abs_max)):
        for key, sv_list in (block or {}).items():
            if not isinstance(sv_list, list):
                continue
            for j, sv in enumerate(sv_list):
                if not isinstance(sv, dict):
                    continue
                lo, hi = sv.get("min"), sv.get("max")
                if lo is not None and hi is not None:
                    try:
                        if float(lo) > float(hi):
                            issues.append({
                                "path": f"base.{block_name}.{key}[{j}]",
                                "severity": "error",
                                "description": f"min > max ({lo} > {hi})",
                            })
                    except (TypeError, ValueError):
                        pass

    # 3. recommended.max <= absolute.max for matching parameter pairs (heuristic on key suffix)
    for rec_key, rec_list in rec_op.items():
        rec_hi = _spec_max(rec_list)
        if rec_hi is None:
            continue
        # Try exact match (rec key VIN ↔ abs_max key VIN_max), or same key in absolute_max
        candidates = [f"{rec_key}_max", rec_key]
        for cand in candidates:
            if cand not in abs_max:
                continue
            abs_hi = _spec_max(abs_max[cand])
            if abs_hi is None:
                continue
            try:
                if float(rec_hi) > float(abs_hi):
                    issues.append({
                        "path": f"base.recommended_operating.{rec_key}",
                        "severity": "error",
                        "description": f"recommended.max ({rec_hi}) exceeds absolute_max.{cand}.max ({abs_hi})",
                    })
            except (TypeError, ValueError):
                pass
            break

    # 4. category pin references resolve to pinout (registry-driven)
    pin_nums = _all_pin_numbers(pinout)
    for category, fields in _PIN_FIELDS_BY_CATEGORY.items():
        block = extraction.get(category)
        if not isinstance(block, dict) or block.get("_extraction_failed"):
            continue
        for f in fields:
            v = block.get(f)
            if v is None:
                continue
            if str(v) not in pin_nums:
                issues.append({
                    "path": f"{category}.{f}",
                    "severity": "error",
                    "description": f"references pin {v!r} which is not present in base.pinout ({sorted(pin_nums)})",
                })

    # 4b. absolute_max placement sniff — flag entries whose evidence.section
    # looks like an operating-point / characterization table. Catches the
    # "Table 2 electrical characteristics stuffed into absolute_max" failure
    # mode observed on USBLC6-2SC6. Uses a denylist for known operating-point markers; a
    # section that contains stress markers ("absolute"/"stress"/"maximum
    # ratings") is allowed through even if it also contains operating
    # words (combined tables). Default is silent-pass on ambiguous names.
    _op_marker_re = re.compile(
        r'\b(electrical\s+characteristic|operating\s+condition|recommended\s+operating|dc\s+characteristic|ac\s+characteristic)',
        re.IGNORECASE,
    )
    _stress_marker_re = re.compile(
        r'\b(absolute|stress|maximum\s+rating)',
        re.IGNORECASE,
    )
    for key, sv_list in (abs_max or {}).items():
        if not isinstance(sv_list, list):
            continue
        for j, sv in enumerate(sv_list):
            if not isinstance(sv, dict):
                continue
            evidence = sv.get("evidence") or {}
            section = (evidence.get("section") or "").strip()
            if not section:
                continue  # no evidence to sniff — silent skip
            looks_operating = bool(_op_marker_re.search(section))
            looks_stress = bool(_stress_marker_re.search(section))
            if looks_operating and not looks_stress:
                issues.append({
                    "path": f"base.absolute_max.{key}[{j}].evidence.section",
                    "severity": "warning",
                    "description": (
                        f"absolute_max entry cites section {section!r}, which "
                        "looks like operating-point / characterization data "
                        "(no 'absolute'/'stress'/'maximum rating' keywords). "
                        "May be placed in the wrong slot."
                    ),
                })

    # 5. categories array consistency
    cats = extraction.get("categories") or []
    for cat in cats:
        payload = extraction.get(cat)
        if payload is None:
            issues.append({
                "path": f"categories[{cat!r}]",
                "severity": "error",
                "description": f"categories lists {cat!r} but top-level {cat} field is missing",
            })
        elif isinstance(payload, dict) and payload.get("_extraction_failed") is True:
            issues.append({
                "path": f"{cat}",
                "severity": "error",
                "description": f"category {cat!r} payload is the partial-merge sentinel: {payload.get('reason') or 'no reason given'}",
            })
        elif isinstance(payload, dict) and not payload:
            issues.append({
                "path": f"categories[{cat!r}]",
                "severity": "error",
                "description": f"categories lists {cat!r} but top-level {cat} field is an empty object",
            })
        elif isinstance(payload, list) and not payload:
            issues.append({
                "path": f"categories[{cat!r}]",
                "severity": "error",
                "description": f"categories lists {cat!r} but top-level {cat} field is an empty list",
            })

    return issues


def _cli_v14(argv: list[str] | None = None) -> int:
    """v1.4 verifier CLI.

    Two invocation shapes supported:

    1. Positional (original): ``datasheet_verify.py <extraction_path>``
    2. Flag-based (harness 4-check gate, Check 2):
       ``datasheet_verify.py --mpn <mpn> --extract-dir <dir> --self-consistency --json``

    Output shape:
        positional → {"issues": [...], "count": N}
        flag-based with --json → {"violations": [...], "count": N, "mpn": ..., "extract_dir": ...}

    Exit codes:
        0  no issues
        1  ≥1 issue
        2  CLI / I/O error (missing file, bad JSON, missing required flags)
    """
    import argparse, json as _json, re as _re, sys as _sys
    from pathlib import Path as _Path

    ap = argparse.ArgumentParser(
        description="Verify v1.4 extraction JSON for cross-field consistency."
    )
    ap.add_argument(
        "extraction_path",
        nargs="?",
        help="path to <mpn>.json extraction (positional mode)",
    )
    ap.add_argument(
        "--mpn",
        help="MPN to look up under --extract-dir (flag mode)",
    )
    ap.add_argument(
        "--extract-dir",
        type=_Path,
        help="directory containing <mpn>.json (flag mode)",
    )
    ap.add_argument(
        "--self-consistency",
        action="store_true",
        help=(
            "explicit opt-in to v1.4 self-consistency mode "
            "(flag mode; required when using --mpn/--extract-dir)"
        ),
    )
    ap.add_argument(
        "--json",
        dest="emit_json",
        action="store_true",
        help="emit harness-shape JSON ({violations: [...]}) instead of legacy {issues: [...]}",
    )
    args = ap.parse_args(argv)

    flag_mode = bool(args.mpn or args.extract_dir or args.self_consistency)
    positional_mode = args.extraction_path is not None

    if flag_mode and positional_mode:
        print(
            "error: cannot mix positional extraction_path with --mpn/--extract-dir flags",
            file=_sys.stderr,
        )
        return 2
    if flag_mode:
        if not (args.mpn and args.extract_dir and args.self_consistency):
            print(
                "error: flag mode requires --mpn, --extract-dir, and --self-consistency",
                file=_sys.stderr,
            )
            return 2
        sanitized = _re.sub(r"[^A-Za-z0-9_.-]", "_", args.mpn.strip())
        path = args.extract_dir / f"{sanitized}.json"
    elif positional_mode:
        path = _Path(args.extraction_path)
    else:
        ap.print_usage(_sys.stderr)
        print(
            "error: must supply either positional extraction_path "
            "or --mpn/--extract-dir/--self-consistency",
            file=_sys.stderr,
        )
        return 2

    if not path.exists():
        print(f"error: extraction file not found: {path}", file=_sys.stderr)
        return 2
    try:
        extraction = _json.loads(path.read_text(encoding="utf-8"))
    except _json.JSONDecodeError as exc:
        print(f"error: extraction file is not valid JSON: {exc}", file=_sys.stderr)
        return 2

    issues = verify_v14_extraction(extraction)

    if flag_mode and args.emit_json:
        _json.dump(
            {
                "violations": issues,
                "count": len(issues),
                "mpn": args.mpn,
                "extract_dir": str(args.extract_dir),
            },
            _sys.stdout,
            indent=2,
        )
    elif args.emit_json or positional_mode:
        _json.dump({"issues": issues, "count": len(issues)}, _sys.stdout, indent=2)
    else:
        # Flag mode without --json: minimal human summary.
        print(f"{args.mpn}: {len(issues)} issue(s)")
        for i in issues:
            print(f"  [{i['severity']}] {i['path']}: {i['description']}")
    if args.emit_json or positional_mode:
        _sys.stdout.write("\n")
    return 0 if not issues else 1


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # UTF-8 on a cp1252 pipe (Windows)
        if (getattr(_stream, "encoding", "") or "").lower().replace("-", "") != "utf8" \
                and hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.exit(_cli_v14())
