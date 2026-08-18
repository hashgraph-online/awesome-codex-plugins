"""
Quality scoring for structured datasheet extractions.

Evaluates an extraction JSON against a completeness rubric across five
dimensions: pin coverage, voltage ratings, operating conditions, application
info, and SPICE-relevant specs. Returns a weighted score 0.0-10.0 with
per-dimension breakdown and a list of specific issues found.

The scoring is deterministic — same input always produces same score. It
runs after Claude performs the extraction and tells Claude (and the cache
manager) whether the extraction is good enough or needs a retry.
"""


# ---------------------------------------------------------------------------
# Category-specific electrical characteristic requirements
# ---------------------------------------------------------------------------

_ECHAR_REQUIREMENTS = {
    # category: (required_fields, nice_to_have_fields)
    "operational_amplifier": (
        ["gbw_hz", "slew_vus"],
        ["vos_mv", "aol_db", "rin_ohms"],
    ),
    "comparator": (
        ["prop_delay_ns"],
        ["vos_mv", "aol_db"],
    ),
    "linear_regulator": (
        ["vref_v", "quiescent_current_ua"],
        ["dropout_mv", "output_current_max_ma"],
    ),
    "switching_regulator": (
        ["vref_v", "switching_frequency_khz"],
        ["quiescent_current_ua", "output_current_max_ma"],
    ),
    "voltage_reference": (
        ["vref_v", "vref_accuracy_pct"],
        ["temp_coefficient_ppmk"],
    ),
    "microcontroller": (
        [],  # MCUs have diverse e-chars, no universal required set
        ["quiescent_current_ua", "io_voltage_max"],
    ),
    "esd_protection": (
        ["clamping_voltage_v"],
        ["leakage_current_na", "capacitance_pf"],
    ),
}

# Fallback for categories not listed above
_ECHAR_DEFAULT = ([], [])


# ---------------------------------------------------------------------------
# SPICE spec requirements per category
# ---------------------------------------------------------------------------

_SPICE_REQUIREMENTS = {
    "operational_amplifier": ["gbw_hz"],
    "comparator": [],  # comparators rarely need SPICE behavioral models
    "linear_regulator": ["vref", "dropout_mv"],
    "switching_regulator": ["vref"],
    "voltage_reference": ["vref"],
}


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def _score_pin_coverage(extraction, expected_pin_count=None):
    """Score pin coverage (0-10).

    10.0 = all pins present with name, type, and at least one electrical spec.
    Deductions: -2 per missing pin, -1 per pin with name only (no specs).
    0.0 if fewer than 50% of expected pins documented.
    """
    pins = extraction.get("pins", [])
    if not pins:
        return 0.0, ["No pins documented"]

    num_pins = len(pins)
    expected = expected_pin_count or num_pins  # if no expected count, use what we have

    # Check if we have enough pins
    if expected > 0 and num_pins < expected * 0.5:
        return 0.0, [f"Only {num_pins}/{expected} pins documented (<50%)"]

    issues = []
    pins_with_specs = 0
    pins_with_name_only = 0

    for pin in pins:
        has_name = bool(pin.get("name"))
        has_electrical = any([
            pin.get("voltage_abs_max") is not None,
            pin.get("voltage_operating_min") is not None,
            pin.get("voltage_operating_max") is not None,
            pin.get("current_max_ma") is not None,
            pin.get("threshold_high_v") is not None,
            pin.get("threshold_low_v") is not None,
        ])
        has_description = bool(pin.get("description"))
        has_required = bool(pin.get("required_external"))

        if has_name and (has_electrical or has_description or has_required):
            pins_with_specs += 1
        elif has_name:
            pins_with_name_only += 1
            issues.append(f"Pin {pin.get('number', '?')} ({pin.get('name', '?')}): name only, no specs")
        else:
            issues.append(f"Pin {pin.get('number', '?')}: missing name")

    # Calculate score
    if expected == 0:
        return 10.0, []

    missing = max(0, expected - num_pins)
    score = 10.0
    score -= missing * 2.0  # -2 per missing pin
    score -= pins_with_name_only * 1.0  # -1 per name-only pin

    if missing > 0:
        issues.insert(0, f"{missing} pin(s) missing from extraction")

    return max(0.0, min(10.0, score)), issues[:5]  # cap issues for readability


def _score_voltage_ratings(extraction):
    """Score voltage/thermal ratings completeness (0-10).

    10.0 = abs max has vin_max + junction_temp, operating has vin range + temp range.
    """
    abs_max = extraction.get("absolute_maximum_ratings", {})
    operating = extraction.get("recommended_operating_conditions", {})
    issues = []
    score = 10.0

    # Absolute maximum ratings
    if not abs_max:
        score -= 3.0
        issues.append("No absolute maximum ratings")
    else:
        if abs_max.get("junction_temp_max_c") is None:
            score -= 1.0
            issues.append("Missing junction temperature max")
        # Check for at least one voltage abs max
        voltage_keys = [k for k in abs_max if k.endswith("_max_v") and abs_max[k] is not None]
        if not voltage_keys:
            score -= 2.0
            issues.append("No voltage absolute maximum ratings")

    # Recommended operating conditions
    if not operating:
        score -= 3.0
        issues.append("No recommended operating conditions")
    else:
        if operating.get("vin_min_v") is None or operating.get("vin_max_v") is None:
            score -= 1.5
            issues.append("Missing input voltage operating range")
        if operating.get("temp_min_c") is None or operating.get("temp_max_c") is None:
            score -= 1.0
            issues.append("Missing operating temperature range")

    return max(0.0, min(10.0, score)), issues


def _score_application_info(extraction):
    """Score application circuit information (0-10).

    10.0 = has topology + 2+ component recommendations + formula/notes.
    """
    app = extraction.get("application_circuit", {})
    issues = []
    score = 10.0

    if not app:
        return 0.0, ["No application circuit information"]

    if not app.get("topology"):
        score -= 2.0
        issues.append("Missing circuit topology")

    # Count component recommendations
    rec_fields = [
        "inductor_recommended", "input_cap_recommended", "output_cap_recommended",
        "feedback_resistor_top_ohm", "feedback_resistor_bottom_ohm",
        "compensation_cap", "bootstrap_cap", "decoupling_cap",
    ]
    recs = sum(1 for f in rec_fields if app.get(f))
    # Also count any key ending in _recommended
    recs += sum(1 for k, v in app.items()
                if k.endswith("_recommended") and k not in rec_fields and v)

    if recs == 0:
        score -= 3.0
        issues.append("No component recommendations")
    elif recs == 1:
        score -= 1.5
        issues.append("Only 1 component recommendation (expect 2+)")

    if not app.get("vout_formula") and not app.get("notes"):
        score -= 2.0
        issues.append("No formula or application notes")
    elif not app.get("notes"):
        score -= 1.0
        issues.append("No layout/application notes")

    return max(0.0, min(10.0, score)), issues


def _score_electrical_chars(extraction):
    """Score electrical characteristics (0-10), category-dependent.

    Uses category-specific required/nice-to-have field lists.
    """
    category = extraction.get("category", "")
    echars = extraction.get("electrical_characteristics", {})
    issues = []

    required, nice = _ECHAR_REQUIREMENTS.get(category, _ECHAR_DEFAULT)

    if not echars:
        if required:
            return 0.0, [f"No electrical characteristics (need {', '.join(required)})"]
        return 5.0, ["No electrical characteristics (none strictly required for this category)"]

    score = 10.0

    # Check required fields
    for field in required:
        if echars.get(field) is None:
            score -= 3.0
            issues.append(f"Missing required: {field}")

    # Check nice-to-have fields
    for field in nice:
        if echars.get(field) is None:
            score -= 1.0
            issues.append(f"Missing optional: {field}")

    # Bonus: if category has no requirements but we got some data, that's good
    if not required and not nice:
        populated = sum(1 for v in echars.values() if v is not None)
        if populated >= 3:
            score = 10.0
        elif populated >= 1:
            score = 7.0
        else:
            score = 5.0

    return max(0.0, min(10.0, score)), issues[:5]


def _score_spice_specs(extraction):
    """Score SPICE-relevant specs (0-10).

    10.0 = enough fields for the component category's behavioral model.
    """
    category = extraction.get("category", "")
    spice = extraction.get("spice_specs", {})
    issues = []

    if not spice:
        # Check if we can derive from electrical_characteristics
        echars = extraction.get("electrical_characteristics", {})
        if echars:
            # Some specs can be pulled from e-chars
            return 5.0, ["No spice_specs section (could derive from electrical_characteristics)"]
        return 0.0, ["No SPICE-relevant specs"]

    required = _SPICE_REQUIREMENTS.get(category, [])
    score = 10.0

    for field in required:
        if spice.get(field) is None:
            score -= 4.0
            issues.append(f"Missing SPICE spec: {field}")

    # Count populated fields
    populated = sum(1 for v in spice.values() if v is not None)
    if populated == 0:
        return 0.0, ["spice_specs section is empty"]
    elif populated <= 2 and not required:
        score = min(score, 6.0)

    return max(0.0, min(10.0, score)), issues


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_extraction(extraction, expected_pin_count=None):
    """Score a datasheet extraction for completeness.

    Evaluates across five weighted dimensions and returns a total score
    (0.0-10.0) along with per-dimension scores and specific issues.

    Args:
        extraction: Parsed extraction JSON dict
        expected_pin_count: If known (from schematic), used for pin coverage

    Returns:
        {
            "total": 8.2,
            "pin_coverage": 9.0,
            "voltage_ratings": 8.5,
            "application_info": 7.0,
            "electrical_characteristics": 8.0,
            "spice_specs": 8.5,
            "issues": ["Missing abs max for SW pin", ...],
            "sufficient": True  # True if total >= 6.0
        }
    """
    pin_score, pin_issues = _score_pin_coverage(extraction, expected_pin_count)
    volt_score, volt_issues = _score_voltage_ratings(extraction)
    app_score, app_issues = _score_application_info(extraction)
    echar_score, echar_issues = _score_electrical_chars(extraction)
    spice_score, spice_issues = _score_spice_specs(extraction)

    # Weighted average (weights sum to 1.0)
    total = (
        pin_score * 0.35 +
        volt_score * 0.25 +
        app_score * 0.20 +
        echar_score * 0.10 +
        spice_score * 0.10
    )

    all_issues = pin_issues + volt_issues + app_issues + echar_issues + spice_issues

    return {
        "total": round(total, 1),
        "pin_coverage": round(pin_score, 1),
        "voltage_ratings": round(volt_score, 1),
        "application_info": round(app_score, 1),
        "electrical_characteristics": round(echar_score, 1),
        "spice_specs": round(spice_score, 1),
        "issues": all_issues,
        "sufficient": total >= 6.0,
    }


# ---------------------------------------------------------------------------
# v1.4 rubric extension (Phase 3a)
# ---------------------------------------------------------------------------

# Per-pin fields scored by population (1 point each, max 4 pts/pin)
_PIN_FIELDS = ("name", "type", "power_domain", "evidence")

# Base block "fully populated" reference field set
_BASE_FIELD_REFS = {
    "package":               ["code", "pin_count"],
    "thermal":               ["theta_ja"],
    "absolute_max":          ["VIN_max", "TJ_max"],
    "recommended_operating": ["VIN", "TA"],
    "esd":                   ["HBM"],
}

# Per-category required+nice-to-have fields
_CATEGORY_FIELD_REQS = {
    "regulator": {
        "required": ("topology", "vin_range", "vout_range", "iout_max"),
        "nice":     ("reference_voltage", "switching_freq", "cin_min", "cout_min", "enable_pin"),
    },
    # 3b: mcu, opamp, transistor, diode, crystal
}


def _populated(value) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, dict)) and not value:
        return False
    return True


def _pinout_completeness(extraction: dict) -> float:
    pinout = ((extraction.get("base") or {}).get("pinout")) or []
    if not isinstance(pinout, list):
        return 0.0  # sentinel ({_extraction_failed: true}) or malformed pinout block
    if not pinout:
        return 0.0
    pts_per_pin = len(_PIN_FIELDS)
    earned = 0
    total = pts_per_pin * len(pinout)
    for p in pinout:
        for f in _PIN_FIELDS:
            if _populated(p.get(f)):
                earned += 1
    return earned / total if total else 0.0


def _base_completeness(extraction: dict) -> float:
    base = extraction.get("base") or {}
    if not base:
        return 0.0
    if isinstance(base, dict) and base.get("_extraction_failed"):
        return 0.0  # base block extraction failed (post-retry sentinel)
    earned = 0
    total = sum(len(v) for v in _BASE_FIELD_REFS.values())
    for block, keys in _BASE_FIELD_REFS.items():
        b = base.get(block) or {}
        if not isinstance(b, dict):
            continue
        for k in keys:
            if _populated(b.get(k)):
                earned += 1
    return earned / total if total else 0.0


def _category_extension_completeness(extraction: dict) -> float:
    cats = extraction.get("categories") or []
    if not cats:
        return 0.0
    fractions = []
    for cat in cats:
        payload = extraction.get(cat)
        if not isinstance(payload, dict) or payload.get("_extraction_failed"):
            fractions.append(0.0)
            continue
        spec = _CATEGORY_FIELD_REQS.get(cat)
        if not spec:
            fractions.append(1.0)  # unknown category — full credit (3b will populate)
            continue
        req = spec["required"]
        nice = spec["nice"]
        req_score = sum(1 for f in req if _populated(payload.get(f))) / len(req) if req else 1.0
        nice_score = sum(1 for f in nice if _populated(payload.get(f))) / len(nice) if nice else 1.0
        fractions.append(0.7 * req_score + 0.3 * nice_score)
    return sum(fractions) / len(fractions) if fractions else 0.0


def score_v14_extraction(extraction: dict) -> dict:
    """Phase 3a quality score (0-100) for a v1.4 extraction JSON.

    Weighted dimensions:
      pinout_completeness            20%
      base_completeness              25%
      category_extension_completeness 25%
      reserved (v1.5)                30%   (full credit in v1.4)
    """
    dims = {
        "pinout_completeness": _pinout_completeness(extraction),
        "base_completeness": _base_completeness(extraction),
        "category_extension_completeness": _category_extension_completeness(extraction),
        "reserved_v15": 1.0,
    }
    weights = {
        "pinout_completeness": 0.20,
        "base_completeness": 0.25,
        "category_extension_completeness": 0.25,
        "reserved_v15": 0.30,
    }
    weighted = sum(dims[k] * weights[k] for k in dims)
    score = int(round(weighted * 100))
    return {"score": score, "dimensions": dims, "weights": weights}
