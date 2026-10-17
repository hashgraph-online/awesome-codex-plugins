"""Monte Carlo tolerance analysis for SPICE subcircuit simulations.

Provides tolerance parsing, value sampling, and statistical aggregation
for running N simulations with randomized component values within
tolerance bands.

Zero external dependencies — uses only Python 3.8+ stdlib.
"""

import copy
import math
import random
import sys
import os

# Allow importing from kicad scripts directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                 "..", "..", "kicad", "scripts"))
from kicad_utils import parse_tolerance


# Default tolerances when not specified in the component value string.
# Based on standard E-series and common component types.
DEFAULT_TOLERANCE = {
    "resistor": 0.05,       # 5% (E24 series default)
    "capacitor": 0.10,      # 10% (ceramic MLCC default)
    "inductor": 0.20,       # 20% (standard inductor)
}

# Map from value key in detection dicts to component type
_VALUE_KEYS = {
    "ohms": "resistor",
    "farads": "capacitor",
    "henries": "inductor",
}

# Primary metric per detection type — from unified schema
from detection_schema import get_primary_metric as _schema_get_primary_metric


def resolve_tolerance(det_component: dict, component_type: str) -> float:
    """Determine tolerance for a component from its detection dict entry.

    Tries parse_tolerance() on the 'value' string first, then falls back
    to DEFAULT_TOLERANCE by component_type.

    Args:
        det_component: Dict with 'ref', 'value', and 'ohms'/'farads'/'henries'
        component_type: "resistor", "capacitor", or "inductor"

    Returns:
        Tolerance as a fraction (e.g., 0.05 for 5%)
    """
    value_str = det_component.get("value", "")
    if value_str:
        tol = parse_tolerance(value_str)
        if tol is not None:
            return tol
    return DEFAULT_TOLERANCE.get(component_type, 0.05)


def find_toleranceable_components(det: dict) -> list:
    """Find all component value fields in a detection dict.

    Walks 1-2 levels deep looking for sub-dicts with 'ref' + one of
    'ohms'/'farads'/'henries'.

    Returns:
        List of (key_path, component_type, nominal_value, tolerance) tuples.
        key_path is a list of keys like ["resistor", "ohms"] or
        ["r_top", "ohms"].
    """
    results = []

    def _check_sub(sub, path_prefix):
        """Check if a dict is a component sub-dict with a value key."""
        if not isinstance(sub, dict) or "ref" not in sub:
            return
        for vkey, ctype in _VALUE_KEYS.items():
            if vkey in sub and isinstance(sub[vkey], (int, float)):
                nominal = sub[vkey]
                if nominal <= 0:
                    continue
                tol = resolve_tolerance(sub, ctype)
                results.append((path_prefix + [vkey], ctype, nominal, tol))

    for key, val in det.items():
        if isinstance(val, dict):
            _check_sub(val, [key])
            # Check one level deeper (e.g., feedback_divider.r_top)
            for subkey, subval in val.items():
                if isinstance(subval, dict):
                    _check_sub(subval, [key, subkey])
        elif isinstance(val, list):
            # Handle lists of component dicts (e.g., load_caps, capacitors)
            for idx, item in enumerate(val):
                if isinstance(item, dict):
                    _check_sub(item, [key, idx])

    return results


def _set_nested(d: dict, path: list, value: float):
    """Set a value in a nested dict/list by path."""
    obj = d
    for key in path[:-1]:
        obj = obj[key]
    obj[path[-1]] = value


def _get_nested(d: dict, path: list):
    """Get a value from a nested dict/list by path."""
    obj = d
    for key in path:
        obj = obj[key]
    return obj


def _recalc_derived(det: dict, det_type: str = None) -> None:
    """Recalculate derived fields after perturbing component values.

    When det_type is provided, uses schema-driven dispatch.
    When None, falls back to trying all applicable schemas (backward compat).
    """
    from detection_schema import recalc_derived as _schema_recalc, SCHEMAS

    if det_type:
        _schema_recalc(det, det_type)
        return

    # Fallback: run all recalc functions (safe — each checks structural keys)
    seen = set()
    for _dt, schema in SCHEMAS.items():
        for df in schema.derived:
            fn_id = id(df.recalc)
            if fn_id not in seen:
                df.recalc(det)
                seen.add(fn_id)


def sample_detection(det: dict, components: list, rng: random.Random,
                     distribution: str = "gaussian", det_type: str = None) -> dict:
    """Create a deep copy of det with randomized component values.

    Args:
        det: Original detection dict
        components: Output from find_toleranceable_components()
        rng: Seeded random.Random instance for reproducibility
        distribution: "gaussian" (3sigma = tolerance) or "uniform"

    Returns:
        New dict with perturbed component values and recalculated derived fields
    """
    sampled = copy.deepcopy(det)

    for key_path, _ctype, nominal, tol in components:
        if distribution == "gaussian":
            # 3-sigma = tolerance band (99.7% within spec)
            factor = 1.0 + rng.gauss(0, tol / 3.0)
        else:
            factor = 1.0 + rng.uniform(-tol, tol)
        # Clamp to positive values (component values can't go negative)
        new_val = max(nominal * factor, nominal * 1e-6)
        _set_nested(sampled, key_path, new_val)

    _recalc_derived(sampled, det_type=det_type)
    return sampled


def _pearson_r(xs: list, ys: list) -> float:
    """Compute Pearson correlation coefficient (stdlib only)."""
    n = len(xs)
    if n < 3:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    sx = sum((x - mx) ** 2 for x in xs)
    sy = sum((y - my) ** 2 for y in ys)
    if sx == 0 or sy == 0:
        return 0.0
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / (sx * sy) ** 0.5


def aggregate_mc_results(nominal_result: dict, mc_results: list,
                         components: list, sampled_values: list,
                         subcircuit_type: str, n_requested: int,
                         distribution: str, seed: int,
                         det_type: str = None) -> dict:
    """Compute statistical summary from N Monte Carlo simulation results.

    Args:
        nominal_result: Result from the nominal (unperturbed) simulation
        mc_results: List of N result dicts from perturbed simulations
        components: Toleranceable components list from find_toleranceable_components()
        sampled_values: List of dicts mapping component ref -> sampled value (one per trial)
        subcircuit_type: Type string (e.g., "rc_filter") for metric lookup
        n_requested: Number of MC trials requested
        distribution: "gaussian" or "uniform"
        seed: Random seed used
        det_type: Plural detection type key (e.g., "rc_filters") for schema lookup

    Returns:
        Dict with n_samples, components, statistics, sensitivity
    """
    result = {
        "n_samples": n_requested,
        "n_converged": len(mc_results),
        "distribution": distribution,
        "seed": seed,
        "components": [],
        "statistics": {},
        "sensitivity": [],
    }

    # Component info
    for key_path, ctype, nominal, tol in components:
        # Get ref from the component sub-dict
        ref_path = key_path[:-1]  # path to the component dict (without the value key)
        ref = "?"
        try:
            comp_dict = nominal_result.get("_det", {})
            obj = comp_dict
            for k in ref_path:
                obj = obj[k]
            ref = obj.get("ref", "?")
        except (KeyError, TypeError, IndexError):
            pass
        result["components"].append({
            "ref": ref,
            "type": ctype,
            "nominal": nominal,
            "tolerance_pct": round(tol * 100, 1),
        })

    if not mc_results:
        return result

    # Collect all simulated metric values across MC runs
    # Try the primary metric first, then fall back to all metrics
    primary = _schema_get_primary_metric(det_type) if det_type else _schema_get_primary_metric(subcircuit_type)
    nominal_sim = nominal_result.get("simulated", {})
    metrics_to_analyze = []

    if primary and primary in nominal_sim:
        metrics_to_analyze = [primary]
    else:
        # Use all numeric simulated metrics
        metrics_to_analyze = [k for k, v in nominal_sim.items()
                              if isinstance(v, (int, float))]

    for metric in metrics_to_analyze:
        values = []
        for r in mc_results:
            sim = r.get("simulated", {})
            v = sim.get(metric)
            if v is not None and isinstance(v, (int, float)) and math.isfinite(v):
                values.append(v)

        if len(values) < 2:
            continue

        n = len(values)
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / (n - 1)
        std = math.sqrt(variance)
        v_min = min(values)
        v_max = max(values)
        nominal_val = nominal_sim.get(metric, mean)

        spread_pct = 0.0
        if nominal_val != 0:
            spread_pct = round((v_max - v_min) / abs(nominal_val) * 100, 1)

        result["statistics"][metric] = {
            "nominal": nominal_val,
            "mean": round(mean, 6),
            "std": round(std, 6),
            "min": round(v_min, 6),
            "max": round(v_max, 6),
            "p3sigma_lo": round(mean - 3 * std, 6),
            "p3sigma_hi": round(mean + 3 * std, 6),
            "spread_pct": spread_pct,
        }

        # Sensitivity analysis: which component contributes most
        if sampled_values and len(sampled_values) == len(values):
            sensitivities = []
            for i, (key_path, ctype, nominal, tol) in enumerate(components):
                comp_values = [sv.get(i, nominal) for sv in sampled_values]
                if len(comp_values) == len(values):
                    r = _pearson_r(comp_values, values)
                    r_sq = r * r
                    ref = result["components"][i]["ref"] if i < len(result["components"]) else "?"
                    sensitivities.append({
                        "ref": ref,
                        "tolerance_pct": round(tol * 100, 1),
                        "contribution_pct": round(r_sq * 100, 1),
                        "metric": metric,
                    })

            # Normalize contributions to sum to 100%
            total = sum(s["contribution_pct"] for s in sensitivities)
            if total > 0:
                for s in sensitivities:
                    s["contribution_pct"] = round(s["contribution_pct"] / total * 100, 1)

            sensitivities.sort(key=lambda s: -s["contribution_pct"])
            result["sensitivity"].extend(sensitivities)

    return result
