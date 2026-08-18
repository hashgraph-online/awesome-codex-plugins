#!/usr/bin/env python3
"""
Diff-aware design review for KiCad analysis outputs.

Compares two analysis JSON files (base vs head) and reports changes:
new/removed/modified components, signal parameter shifts, EMC finding
deltas, and SPICE status transitions.

Usage:
    python3 diff_analysis.py base.json head.json
    python3 diff_analysis.py base.json head.json --text
    python3 diff_analysis.py base.json head.json --output diff.json
    python3 diff_analysis.py base.json head.json --threshold 2.0

Supports: schematic, PCB, EMC, and SPICE analyzer outputs (auto-detected).
Zero dependencies — Python 3.8+ stdlib only.
"""

import argparse
import json
import os
import sys


# ---------------------------------------------------------------------------
# Signal analysis identity & value registry
# ---------------------------------------------------------------------------
# Maps detection type -> (identity_fields, value_fields)
# identity_fields: dotpath fields that uniquely identify a detection
# value_fields: numeric/string fields to compare for changes

from detection_schema import SCHEMAS as _SCHEMAS
from finding_schema import group_findings_by_detection_type, normalize_severity

# SIGNAL_REGISTRY is derived from the unified detection schema.
# Kept as a module-level name for backward compat (validate_signal_registry, _diff_items).
SIGNAL_REGISTRY = {dt: (s.identity_fields, s.value_fields) for dt, s in _SCHEMAS.items()}


def validate_signal_registry(sample_output: dict) -> list[str]:
    """Check SIGNAL_REGISTRY keys exist in a sample analyzer output.

    Returns list of warning strings for any registered detection type
    whose key is not found in the findings of the sample output.
    Useful for catching stale registry entries after schema changes.
    """
    sa = group_findings_by_detection_type(sample_output)
    warnings = []
    for key in SIGNAL_REGISTRY:
        if key not in sa:
            warnings.append(f"SIGNAL_REGISTRY key '{key}' not in findings")
    return warnings


# ---------------------------------------------------------------------------
# Shared primitives
# ---------------------------------------------------------------------------

def _resolve(data, dotpath):
    """Navigate a dotted path like 'statistics.total_components' to a value."""
    obj = data
    for key in dotpath.split("."):
        if isinstance(obj, dict) and key in obj:
            obj = obj[key]
        else:
            return None
    return obj


def _diff_counts(base, head, paths):
    """Compare numeric values at dotted paths. Returns only changed paths."""
    deltas = {}
    for path in paths:
        bv = _resolve(base, path)
        hv = _resolve(head, path)
        if bv is None and hv is None:
            continue
        bv = bv if bv is not None else 0
        hv = hv if hv is not None else 0
        if bv != hv:
            deltas[path] = {"base": bv, "head": hv, "delta": hv - bv}
    return deltas


def _identity_key(item, fields):
    """Build a stable identity string from dotpath fields on a dict item."""
    parts = []
    for field in fields:
        val = item
        for key in field.split("."):
            if isinstance(val, dict) and key in val:
                val = val[key]
            else:
                val = None
                break
        if val is None:
            return None
        if isinstance(val, list):
            parts.append("|".join(str(v) for v in sorted(val)))
        else:
            parts.append(str(val))
    return "::".join(parts) if parts else None


def _generic_identity(item):
    """Fallback identity extraction for unknown detection types."""
    for field in ("reference", "ref"):
        if field in item and isinstance(item[field], str):
            return item[field]
    # Try nested ref fields
    for key, val in item.items():
        if isinstance(val, dict) and "ref" in val:
            return val["ref"]
    return None


def _diff_lists(base_items, head_items, id_fields, value_fields, threshold):
    """Match items by identity, return added/removed/modified/unchanged.

    Returns:
        {added: [...], removed: [...], modified: [...], unchanged_count: int}
    """
    result = {"added": [], "removed": [], "modified": [], "unchanged_count": 0}

    if not isinstance(base_items, list):
        base_items = []
    if not isinstance(head_items, list):
        head_items = []

    def _get_key(item):
        did = item.get("detection_id") if isinstance(item, dict) else None
        if did:
            return did
        if id_fields:
            key = _identity_key(item, id_fields)
            if key:
                return key
        return _generic_identity(item)

    # Build identity maps
    base_map = {}
    for item in base_items:
        key = _get_key(item)
        if key:
            base_map[key] = item

    head_map = {}
    for item in head_items:
        key = _get_key(item)
        if key:
            head_map[key] = item

    # Find added, removed, modified
    for key, item in head_map.items():
        if key not in base_map:
            result["added"].append(_summarize_detection(item, id_fields))
        else:
            changes = _compare_fields(base_map[key], item, value_fields, threshold)
            if changes:
                result["modified"].append({
                    "identity": key.replace("::", "/"),
                    "changes": changes,
                    "base_item": base_map[key],
                    "head_item": item,
                })
            else:
                result["unchanged_count"] += 1

    for key in base_map:
        if key not in head_map:
            result["removed"].append(_summarize_detection(base_map[key], id_fields))

    return result


def _compare_fields(base_item, head_item, fields, threshold):
    """Compare specific fields between two matched items. Returns list of changes."""
    changes = []
    for field in fields:
        bv = _resolve(base_item, field)
        hv = _resolve(head_item, field)
        if bv == hv:
            continue
        if bv is None or hv is None:
            changes.append({"field": field, "base": bv, "head": hv})
            continue
        if isinstance(bv, (int, float)) and isinstance(hv, (int, float)):
            if bv != 0:
                pct = (hv - bv) / abs(bv) * 100
                if abs(pct) < threshold:
                    continue
                changes.append({
                    "field": field, "base": bv, "head": hv,
                    "delta_pct": round(pct, 1),
                })
            elif hv != 0:
                changes.append({"field": field, "base": bv, "head": hv})
        else:
            changes.append({"field": field, "base": bv, "head": hv})
    return changes


def _summarize_detection(item, id_fields):
    """Create a concise summary of a detection for added/removed lists."""
    summary = {}
    # Include identity fields
    for field in (id_fields or []):
        val = _resolve(item, field)
        if val is not None:
            summary[field.split(".")[-1]] = val
    # Include common fields
    for key in ("reference", "ref", "value", "type", "topology"):
        if key in item and isinstance(item[key], str):
            summary[key] = item[key]
    # Include sub-dict refs
    for key, val in item.items():
        if isinstance(val, dict) and "ref" in val and key not in summary:
            summary[key + "_ref"] = val["ref"]
    return summary


def _pct_delta(old, new):
    """Calculate percentage change. Returns None if old is zero."""
    if old == 0:
        return None
    return round((new - old) / abs(old) * 100, 1)


# ---------------------------------------------------------------------------
# Assessment diff
# ---------------------------------------------------------------------------

def diff_assessments(base_items, head_items):
    """Diff two assessments[] lists. Returns {added, removed, unchanged_count}.

    Assessments are informational measurements (no severity). They are
    keyed by (rule_id, sorted components tuple) so that a per-component
    measurement keeps a stable identity across runs. Use `detection_id`
    when present — it is the authoritative stable identifier.
    """
    def _key(a):
        if not isinstance(a, dict):
            return ("", "", ())
        det_id = a.get("detection_id") or ""
        rid = a.get("rule_id", "")
        refs = tuple(sorted(a.get("components") or []))
        return (det_id, rid, refs)

    if not isinstance(base_items, list):
        base_items = []
    if not isinstance(head_items, list):
        head_items = []

    base_map = {}
    for a in base_items:
        if isinstance(a, dict):
            base_map[_key(a)] = a
    head_map = {}
    for a in head_items:
        if isinstance(a, dict):
            head_map[_key(a)] = a

    added_keys = sorted(set(head_map) - set(base_map))
    removed_keys = sorted(set(base_map) - set(head_map))
    unchanged = len(set(base_map) & set(head_map))

    def _summarize(key, item):
        _, rid, refs = key
        entry = {"rule_id": rid, "components": list(refs)}
        if isinstance(item, dict) and item.get("summary"):
            entry["summary"] = item["summary"]
        return entry

    return {
        "added": [_summarize(k, head_map[k]) for k in added_keys],
        "removed": [_summarize(k, base_map[k]) for k in removed_keys],
        "unchanged_count": unchanged,
    }


def _attach_assessments_diff(result, base, head):
    """Run diff_assessments on the envelopes and attach if non-empty."""
    a_diff = diff_assessments(base.get("assessments", []),
                              head.get("assessments", []))
    if a_diff["added"] or a_diff["removed"] or a_diff["unchanged_count"]:
        result["assessments"] = a_diff


# ---------------------------------------------------------------------------
# Auto-detection
# ---------------------------------------------------------------------------

def detect_type(data):
    """Infer analyzer type from top-level JSON keys."""
    # Prefer explicit analyzer_type field when present
    at = data.get("analyzer_type")
    if at:
        return at
    # Deep review gate output — unambiguous: no analyzer envelope has "quarantined"
    if "findings" in data and "quarantined" in data:
        return "deep_review"
    # Fallback heuristic for older JSON files
    if "findings" in data and "components" in data:
        return "schematic"
    if "footprints" in data and "tracks" in data:
        return "pcb"
    summary = data.get("summary", {})
    if "findings" in data and "emc_risk_score" in summary:
        return "emc"
    if "simulation_results" in data:
        return "spice"
    if "findings" in data and "thermal_score" in summary:
        return "thermal"
    # Detect pre-v1.3 schematic format (signal_analysis wrapper, no findings[])
    if "signal_analysis" in data and "components" in data:
        return "schematic_old"
    return None


# ---------------------------------------------------------------------------
# Schematic diff
# ---------------------------------------------------------------------------

def diff_schematic(base, head, threshold):
    """Diff two schematic analysis JSONs."""
    result = {}

    # Statistics
    stat_paths = [
        "statistics.total_components", "statistics.total_nets",
        "statistics.unique_parts", "statistics.total_wires",
        "statistics.total_no_connects",
    ]
    stats = _diff_counts(base, head, stat_paths)
    if stats:
        result["statistics"] = stats

    # Components: match by reference
    base_comps = {c["reference"]: c for c in base.get("components", [])
                  if isinstance(c, dict) and "reference" in c}
    head_comps = {c["reference"]: c for c in head.get("components", [])
                  if isinstance(c, dict) and "reference" in c}

    comp_diff = {"added": [], "removed": [], "modified": []}
    for ref, comp in head_comps.items():
        if ref not in base_comps:
            comp_diff["added"].append({
                "reference": ref, "value": comp.get("value", ""),
                "footprint": comp.get("footprint", ""),
            })
        else:
            bc = base_comps[ref]
            changes = []
            for field in ("value", "footprint", "mpn"):
                bv = bc.get(field, "")
                hv = comp.get(field, "")
                if bv != hv:
                    changes.append({"field": field, "base": bv, "head": hv})
            if changes:
                comp_diff["modified"].append({"reference": ref, "changes": changes})

    for ref in base_comps:
        if ref not in head_comps:
            bc = base_comps[ref]
            comp_diff["removed"].append({
                "reference": ref, "value": bc.get("value", ""),
                "footprint": bc.get("footprint", ""),
            })

    if comp_diff["added"] or comp_diff["removed"] or comp_diff["modified"]:
        result["components"] = comp_diff

    # Signal analysis (grouped from flat findings[])
    base_sa = group_findings_by_detection_type(base)
    head_sa = group_findings_by_detection_type(head)
    all_keys = set(list(base_sa.keys()) + list(head_sa.keys()))
    sa_diff = {}

    for det_type in sorted(all_keys):
        base_items = base_sa.get(det_type, [])
        head_items = head_sa.get(det_type, [])

        if det_type in SIGNAL_REGISTRY:
            id_fields, val_fields = SIGNAL_REGISTRY[det_type]
        else:
            id_fields, val_fields = ["reference"], []

        diff = _diff_lists(base_items, head_items, id_fields, val_fields, threshold)
        if diff["added"] or diff["removed"] or diff["modified"]:
            sa_diff[det_type] = diff

    if sa_diff:
        result["signal_analysis"] = sa_diff

    # Attribution: correlate signal changes with component changes
    if "signal_analysis" in result and "components" in result:
        comp_changes = {}
        for m in result["components"].get("modified", []):
            for ch in m.get("changes", []):
                if ch["field"] == "value":
                    comp_changes[m["reference"]] = {
                        "base_value": ch["base"], "head_value": ch["head"]}

        if comp_changes:
            for det_type, det_diff in result.get("signal_analysis", {}).items():
                for mod in det_diff.get("modified", []):
                    # Find changed components referenced in this detection
                    attributed = []
                    # Check identity string for component refs
                    identity = mod.get("identity", "")
                    for ref in comp_changes:
                        if ref in identity:
                            attributed.append(ref)
                    # Also check the items themselves if available
                    for item_key in ("base_item", "head_item"):
                        item = mod.get(item_key, {})
                        if isinstance(item, dict):
                            for key, val in item.items():
                                if isinstance(val, dict) and "ref" in val:
                                    r = val["ref"]
                                    if r in comp_changes and r not in attributed:
                                        attributed.append(r)
                    if attributed:
                        mod["attributed_to"] = [
                            {"ref": ref, **comp_changes[ref]} for ref in sorted(attributed)
                        ]

    # BOM changes
    base_bom = {(b.get("value", ""), b.get("footprint", "")): b
                for b in base.get("bom", []) if isinstance(b, dict)}
    head_bom = {(b.get("value", ""), b.get("footprint", "")): b
                for b in head.get("bom", []) if isinstance(b, dict)}

    bom_diff = {"added": [], "removed": [], "quantity_changes": []}
    for key, entry in head_bom.items():
        if key not in base_bom:
            bom_diff["added"].append({
                "value": entry.get("value", ""),
                "footprint": entry.get("footprint", ""),
                "quantity": entry.get("quantity", 0),
            })
        else:
            bq = base_bom[key].get("quantity", 0)
            hq = entry.get("quantity", 0)
            if bq != hq:
                bom_diff["quantity_changes"].append({
                    "value": entry.get("value", ""),
                    "footprint": entry.get("footprint", ""),
                    "base_qty": bq, "head_qty": hq, "delta": hq - bq,
                })
    for key in base_bom:
        if key not in head_bom:
            entry = base_bom[key]
            bom_diff["removed"].append({
                "value": entry.get("value", ""),
                "footprint": entry.get("footprint", ""),
                "quantity": entry.get("quantity", 0),
            })

    if bom_diff["added"] or bom_diff["removed"] or bom_diff["quantity_changes"]:
        result["bom"] = bom_diff

    # Connectivity issues (items may be strings or dicts)
    def _conn_key(item):
        if isinstance(item, dict):
            return json.dumps(item, sort_keys=True)
        return str(item)

    conn_diff = {}
    for section in ("single_pin_nets", "floating_nets", "multi_driver_nets"):
        base_items = base.get("connectivity_issues", {}).get(section, [])
        head_items = head.get("connectivity_issues", {}).get(section, [])
        base_map = {_conn_key(i): i for i in base_items}
        head_map = {_conn_key(i): i for i in head_items}
        new_keys = set(head_map) - set(base_map)
        resolved_keys = set(base_map) - set(head_map)
        if new_keys or resolved_keys:
            entry = {}
            if new_keys:
                entry["new"] = [head_map[k] for k in sorted(new_keys)]
            if resolved_keys:
                entry["resolved"] = [base_map[k] for k in sorted(resolved_keys)]
            conn_diff[section] = entry
    if conn_diff:
        result["connectivity"] = conn_diff

    # ERC warnings (list of dicts — key on type/net/message for stable identity)
    def _erc_key(w):
        if isinstance(w, dict):
            return (w.get("type", ""), w.get("net", ""), w.get("message", ""))
        return (str(w),)

    base_erc_list = base.get("design_analysis", {}).get("erc_warnings", [])
    head_erc_list = head.get("design_analysis", {}).get("erc_warnings", [])
    base_erc_map = {_erc_key(w): w for w in base_erc_list if isinstance(w, (dict, str))}
    head_erc_map = {_erc_key(w): w for w in head_erc_list if isinstance(w, (dict, str))}
    new_keys = set(head_erc_map) - set(base_erc_map)
    resolved_keys = set(base_erc_map) - set(head_erc_map)
    if new_keys or resolved_keys:
        erc = {}
        if new_keys:
            erc["new_warnings"] = [head_erc_map[k] for k in sorted(new_keys)]
        if resolved_keys:
            erc["resolved_warnings"] = [base_erc_map[k] for k in sorted(resolved_keys)]
        result["erc"] = erc

    _attach_assessments_diff(result, base, head)

    return result


# ---------------------------------------------------------------------------
# PCB diff
# ---------------------------------------------------------------------------

def diff_pcb(base, head, threshold):
    """Diff two PCB analysis JSONs."""
    result = {}

    # Statistics
    stat_paths = [
        "statistics.footprint_count", "statistics.track_segments",
        "statistics.via_count", "statistics.zone_count",
        "statistics.net_count", "statistics.copper_layers_used",
        "statistics.board_width_mm", "statistics.board_height_mm",
        "statistics.total_track_length_mm",
    ]
    stats = _diff_counts(base, head, stat_paths)
    if stats:
        result["statistics"] = stats

    # Routing completeness
    base_rc = _resolve(base, "connectivity.routing_complete")
    head_rc = _resolve(head, "connectivity.routing_complete")
    if base_rc != head_rc:
        result["routing_complete"] = {"base": base_rc, "head": head_rc}

    unrouted = _diff_counts(base, head, ["connectivity.unrouted_count"])
    if unrouted:
        result["unrouted"] = unrouted

    # Footprints: match by reference
    base_fps = {f["reference"]: f for f in base.get("footprints", [])
                if isinstance(f, dict) and "reference" in f}
    head_fps = {f["reference"]: f for f in head.get("footprints", [])
                if isinstance(f, dict) and "reference" in f}

    fp_diff = {"added": [], "removed": [], "modified": []}
    for ref, fp in head_fps.items():
        if ref not in base_fps:
            fp_diff["added"].append({
                "reference": ref, "value": fp.get("value", ""),
                "lib_id": fp.get("lib_id", ""), "layer": fp.get("layer", ""),
            })
        else:
            bfp = base_fps[ref]
            changes = []
            for field in ("value", "lib_id", "layer"):
                bv = bfp.get(field, "")
                hv = fp.get(field, "")
                if bv != hv:
                    changes.append({"field": field, "base": bv, "head": hv})
            if changes:
                fp_diff["modified"].append({"reference": ref, "changes": changes})

    for ref in base_fps:
        if ref not in head_fps:
            bfp = base_fps[ref]
            fp_diff["removed"].append({
                "reference": ref, "value": bfp.get("value", ""),
                "layer": bfp.get("layer", ""),
            })

    if fp_diff["added"] or fp_diff["removed"] or fp_diff["modified"]:
        result["footprints"] = fp_diff

    _attach_assessments_diff(result, base, head)

    return result


# ---------------------------------------------------------------------------
# EMC diff
# ---------------------------------------------------------------------------

def diff_emc(base, head, threshold):
    """Diff two EMC analysis JSONs."""
    result = {}

    # Risk score
    base_score = _resolve(base, "summary.emc_risk_score")
    head_score = _resolve(head, "summary.emc_risk_score")
    if base_score is not None and head_score is not None and base_score != head_score:
        result["risk_score"] = {
            "base": base_score, "head": head_score,
            "delta": head_score - base_score,
        }

    # Severity distribution
    sev_paths = ["summary.critical", "summary.high", "summary.medium",
                 "summary.low", "summary.info"]
    sev_delta = _diff_counts(base, head, sev_paths)
    if sev_delta:
        result["by_severity"] = sev_delta

    # Findings: match by (rule_id, sorted nets, sorted components)
    def _finding_key(f):
        rule = f.get("rule_id", "")
        nets = "|".join(sorted(f.get("nets", [])))
        comps = "|".join(sorted(f.get("components", [])))
        return f"{rule}::{nets}::{comps}"

    base_findings = {_finding_key(f): f for f in base.get("findings", [])
                     if isinstance(f, dict)}
    head_findings = {_finding_key(f): f for f in head.get("findings", [])
                     if isinstance(f, dict)}

    findings_diff = {"new": [], "resolved": [], "changed_severity": []}

    for key, f in head_findings.items():
        if key not in base_findings:
            findings_diff["new"].append({
                "rule_id": f.get("rule_id", ""),
                "severity": f.get("severity", ""),
                "title": f.get("title", ""),
                "category": f.get("category", ""),
                "nets": f.get("nets", []),
                "components": f.get("components", []),
            })
        else:
            bf = base_findings[key]
            if bf.get("severity") != f.get("severity"):
                findings_diff["changed_severity"].append({
                    "rule_id": f.get("rule_id", ""),
                    "base_severity": bf.get("severity", ""),
                    "head_severity": f.get("severity", ""),
                    "title": f.get("title", ""),
                })

    for key, f in base_findings.items():
        if key not in head_findings:
            findings_diff["resolved"].append({
                "rule_id": f.get("rule_id", ""),
                "severity": f.get("severity", ""),
                "title": f.get("title", ""),
                "category": f.get("category", ""),
            })

    if findings_diff["new"] or findings_diff["resolved"] or findings_diff["changed_severity"]:
        result["findings"] = findings_diff

    # Per-net score changes
    base_nets = {n["net"]: n for n in base.get("per_net_scores", [])
                 if isinstance(n, dict) and "net" in n}
    head_nets = {n["net"]: n for n in head.get("per_net_scores", [])
                 if isinstance(n, dict) and "net" in n}

    net_changes = []
    for net, entry in head_nets.items():
        if net in base_nets:
            bs = base_nets[net].get("score", 0)
            hs = entry.get("score", 0)
            if abs(hs - bs) >= threshold:
                net_changes.append({
                    "net": net, "base_score": bs, "head_score": hs,
                    "delta": hs - bs,
                })
    if net_changes:
        net_changes.sort(key=lambda n: -abs(n["delta"]))
        result["per_net_scores"] = net_changes

    _attach_assessments_diff(result, base, head)

    return result


# ---------------------------------------------------------------------------
# SPICE diff
# ---------------------------------------------------------------------------

def diff_spice(base, head, threshold):
    """Diff two SPICE simulation JSONs."""
    result = {}

    # Summary deltas
    sum_paths = ["summary.pass", "summary.warn", "summary.fail", "summary.skip",
                 "summary.total"]
    sum_delta = _diff_counts(base, head, sum_paths)
    if sum_delta:
        result["summary"] = sum_delta

    # Results: match by (subcircuit_type, sorted components)
    def _sim_key(r):
        stype = r.get("subcircuit_type", "")
        comps = "|".join(sorted(r.get("components", [])))
        return f"{stype}::{comps}"

    base_results = {_sim_key(r): r for r in base.get("simulation_results", [])
                    if isinstance(r, dict)}
    head_results = {_sim_key(r): r for r in head.get("simulation_results", [])
                    if isinstance(r, dict)}

    status_changes = []
    new_results = []
    removed_results = []

    for key, r in head_results.items():
        if key not in base_results:
            new_results.append({
                "subcircuit_type": r.get("subcircuit_type", ""),
                "components": r.get("components", []),
                "status": r.get("status", ""),
            })
        else:
            br = base_results[key]
            bs = br.get("status", "")
            hs = r.get("status", "")
            if bs != hs:
                entry = {
                    "subcircuit_type": r.get("subcircuit_type", ""),
                    "components": r.get("components", []),
                    "base_status": bs,
                    "head_status": hs,
                }
                # Add note for regressions
                if bs == "pass" and hs in ("fail", "warn"):
                    delta = r.get("delta", {})
                    notes = [f"{k}={v}" for k, v in delta.items()
                             if isinstance(v, (int, float))]
                    if notes:
                        entry["note"] = ", ".join(notes[:3])
                status_changes.append(entry)

    for key, r in base_results.items():
        if key not in head_results:
            removed_results.append({
                "subcircuit_type": r.get("subcircuit_type", ""),
                "components": r.get("components", []),
                "status": r.get("status", ""),
            })

    if status_changes:
        result["status_changes"] = status_changes
    if new_results:
        result["new_results"] = new_results
    if removed_results:
        result["removed_results"] = removed_results

    # Monte Carlo concerns diff
    base_mc = base.get("monte_carlo_summary", {}).get("concerns", [])
    head_mc = head.get("monte_carlo_summary", {}).get("concerns", [])
    if base_mc or head_mc:
        def _mc_key(c):
            return f"{c.get('subcircuit_type', '')}::{c.get('metric', '')}"
        base_mc_map = {_mc_key(c): c for c in base_mc}
        head_mc_map = {_mc_key(c): c for c in head_mc}
        new_concerns = [c for k, c in head_mc_map.items() if k not in base_mc_map]
        resolved_concerns = [c for k, c in base_mc_map.items() if k not in head_mc_map]
        if new_concerns or resolved_concerns:
            mc = {}
            if new_concerns:
                mc["new"] = new_concerns
            if resolved_concerns:
                mc["resolved"] = resolved_concerns
            result["monte_carlo"] = mc

    _attach_assessments_diff(result, base, head)

    return result


# ---------------------------------------------------------------------------
# Thermal diff
# ---------------------------------------------------------------------------

def diff_thermal(base, head, threshold):
    """Diff two thermal analyzer JSONs.

    Thermal's primary output is assessments[] (per-component Tj estimates
    are TH-DET assessments as of v1.4). Findings are thermal *warnings*.
    """
    result = {}

    # Summary deltas
    stat_paths = [
        "summary.total_findings", "summary.active", "summary.suppressed",
        "summary.components_assessed", "summary.thermal_score",
    ]
    stats = _diff_counts(base, head, stat_paths)
    if stats:
        result["statistics"] = stats

    # Findings: match by (rule_id, sorted components)
    def _finding_key(f):
        rule = f.get("rule_id", "")
        comps = "|".join(sorted(f.get("components", [])))
        return f"{rule}::{comps}"

    base_findings = {_finding_key(f): f for f in base.get("findings", [])
                     if isinstance(f, dict)}
    head_findings = {_finding_key(f): f for f in head.get("findings", [])
                     if isinstance(f, dict)}

    findings_diff = {"new": [], "resolved": [], "changed_severity": []}
    for key, f in head_findings.items():
        if key not in base_findings:
            findings_diff["new"].append({
                "rule_id": f.get("rule_id", ""),
                "severity": f.get("severity", ""),
                "summary": f.get("summary", ""),
                "components": f.get("components", []),
            })
        else:
            bf = base_findings[key]
            if bf.get("severity") != f.get("severity"):
                findings_diff["changed_severity"].append({
                    "rule_id": f.get("rule_id", ""),
                    "base_severity": bf.get("severity", ""),
                    "head_severity": f.get("severity", ""),
                    "summary": f.get("summary", ""),
                })
    for key, f in base_findings.items():
        if key not in head_findings:
            findings_diff["resolved"].append({
                "rule_id": f.get("rule_id", ""),
                "severity": f.get("severity", ""),
                "summary": f.get("summary", ""),
            })

    if findings_diff["new"] or findings_diff["resolved"] or findings_diff["changed_severity"]:
        result["findings"] = findings_diff

    _attach_assessments_diff(result, base, head)

    return result


# ---------------------------------------------------------------------------
# Deep review diff
# ---------------------------------------------------------------------------

def diff_deep_review(base, head, threshold=None):
    """Diff two deep_review.json files (v2.0 spec §3.C).

    Exact finding_id match is primary. Fuzzy pass is advisory only:
    LLM rewording changes the summary hash, so a persisting issue can
    surface as fixed+new — a disappeared and an appeared finding with
    the same category and the same evidence-component set are flagged
    'likely same, reworded'.
    """
    def _by_id(doc):
        return {f["finding_id"]: f for f in doc.get("findings", [])
                if isinstance(f, dict) and f.get("finding_id")}

    b, h = _by_id(base), _by_id(head)
    fixed = [b[k] for k in sorted(b.keys() - h.keys())]
    new = [h[k] for k in sorted(h.keys() - b.keys())]
    still_open = [h[k] for k in sorted(b.keys() & h.keys())]

    def _fuzzy_key(f):
        ev = f.get("evidence") or {}
        comps = tuple(sorted(str(c).upper() for c in ev.get("components") or []))
        return ((f.get("category") or "").lower(), comps)

    new_by_key = {}
    for f in new:
        new_by_key.setdefault(_fuzzy_key(f), []).append(f)
    reworded = []
    for f in fixed:
        for cand in new_by_key.get(_fuzzy_key(f), []):
            reworded.append({
                "base_finding_id": f.get("finding_id"),
                "head_finding_id": cand.get("finding_id"),
                "category": f.get("category"),
                "note": "likely same finding, reworded (advisory)",
            })
    return {
        "fixed": fixed,
        "new": new,
        "still_open": still_open,
        "reworded_candidates": reworded,
        "quarantined_head": len(head.get("quarantined") or []),
    }


# ---------------------------------------------------------------------------
# Severity classification
# ---------------------------------------------------------------------------

def classify_severity(analyzer_type, diff_result):
    """Classify overall change severity."""
    if not diff_result:
        return "none"

    # Breaking: SPICE pass->fail, new EMC error-severity findings, new ERC warnings
    if analyzer_type == "spice":
        for sc in diff_result.get("status_changes", []):
            if sc.get("base_status") == "pass" and sc.get("head_status") == "fail":
                return "breaking"

    if analyzer_type == "emc":
        for f in diff_result.get("findings", {}).get("new", []):
            # Accept v1.4 error and legacy CRITICAL (both map to "error" via normalize).
            if normalize_severity(f.get("severity")) == "error":
                return "breaking"

    if analyzer_type == "schematic":
        if diff_result.get("erc", {}).get("new_warnings"):
            return "breaking"

    # Major: component changes, signal parameter shifts, new/removed detections
    if "signal_analysis" in diff_result or "components" in diff_result:
        return "major"
    if "findings" in diff_result:
        return "major"
    if "status_changes" in diff_result:
        return "major"
    if "footprints" in diff_result:
        fp = diff_result["footprints"]
        if fp.get("added") or fp.get("removed") or fp.get("modified"):
            return "major"

    # Minor: only statistics changes
    if "statistics" in diff_result:
        return "minor"

    return "none"


def classify_regressions(analyzer_type, diff_result):
    """Identify specific regressions in the diff.

    Returns list of {category, severity, detail} for changes that
    made the design worse.
    """
    regressions = []

    if analyzer_type == "schematic":
        # New ERC warnings
        for w in diff_result.get("erc", {}).get("new_warnings", []):
            regressions.append({
                "category": "erc",
                "severity": "breaking",
                "detail": f"New ERC warning: {w.get('type', '?')} on {w.get('net', '?')}",
            })
        # New connectivity issues
        for issue_type in ("single_pin_nets", "floating_nets", "multi_driver_nets"):
            conn = diff_result.get("connectivity", {}).get(issue_type, {})
            new_items = conn.get("new", [])
            for item in new_items:
                detail = item if isinstance(item, str) else str(item)
                regressions.append({
                    "category": "connectivity",
                    "severity": "major",
                    "detail": f"New {issue_type.replace('_', ' ')}: {detail}",
                })
        # Removed protection devices
        for p in diff_result.get("signal_analysis", {}).get("protection_devices", {}).get("removed", []):
            ident = p.get("identity", p.get("reference", "?"))
            regressions.append({
                "category": "protection",
                "severity": "major",
                "detail": f"Protection device removed: {ident}",
            })

    elif analyzer_type == "emc":
        # New error-severity findings (v1.4 collapsed CRITICAL/HIGH into "error").
        # Legacy CRITICAL/HIGH still normalize to "error" via normalize_severity.
        for f in diff_result.get("findings", {}).get("new", []):
            raw_sev = f.get("severity", "")
            if normalize_severity(raw_sev) == "error":
                regressions.append({
                    "category": "emc",
                    "severity": "breaking",
                    "detail": f"New EMC finding: {f.get('rule_id', '?')} ({raw_sev})",
                })
        # Risk score increase
        risk = diff_result.get("risk_score", {})
        if isinstance(risk, dict) and risk.get("delta", 0) > 0:
            regressions.append({
                "category": "emc_risk",
                "severity": "major",
                "detail": f"EMC risk score increased: {risk.get('base', '?')} \u2192 {risk.get('head', '?')}",
            })

    elif analyzer_type == "spice":
        # Pass -> fail transitions
        for sc in diff_result.get("status_changes", []):
            if sc.get("base_status") == "pass" and sc.get("head_status") == "fail":
                regressions.append({
                    "category": "spice",
                    "severity": "breaking",
                    "detail": f"SPICE regression: {sc.get('subcircuit_type', '?')} pass\u2192fail",
                })

    elif analyzer_type == "pcb":
        # Unrouted count increase
        stats = diff_result.get("statistics", {})
        for path, info in stats.items():
            if "unrouted" in path and isinstance(info, dict) and info.get("delta", 0) > 0:
                regressions.append({
                    "category": "routing",
                    "severity": "major",
                    "detail": f"Unrouted nets increased: {info.get('base', 0)} \u2192 {info.get('head', 0)}",
                })
        # Also check dedicated unrouted field
        unrouted = diff_result.get("unrouted", {})
        for path, info in unrouted.items():
            if isinstance(info, dict) and info.get("delta", 0) > 0:
                regressions.append({
                    "category": "routing",
                    "severity": "major",
                    "detail": f"Unrouted nets increased: {info.get('base', 0)} \u2192 {info.get('head', 0)}",
                })

    return regressions


# ---------------------------------------------------------------------------
# Summary builder
# ---------------------------------------------------------------------------

def build_summary(analyzer_type, diff_result):
    """Build a top-level summary of all changes."""
    added = 0
    removed = 0
    modified = 0

    if analyzer_type == "schematic":
        comp = diff_result.get("components", {})
        added += len(comp.get("added", []))
        removed += len(comp.get("removed", []))
        modified += len(comp.get("modified", []))
        for det_type, det_diff in diff_result.get("signal_analysis", {}).items():
            added += len(det_diff.get("added", []))
            removed += len(det_diff.get("removed", []))
            modified += len(det_diff.get("modified", []))

    elif analyzer_type == "pcb":
        fp = diff_result.get("footprints", {})
        added += len(fp.get("added", []))
        removed += len(fp.get("removed", []))
        modified += len(fp.get("modified", []))

    elif analyzer_type == "emc":
        findings = diff_result.get("findings", {})
        added += len(findings.get("new", []))
        removed += len(findings.get("resolved", []))
        modified += len(findings.get("changed_severity", []))

    elif analyzer_type == "spice":
        added += len(diff_result.get("new_results", []))
        removed += len(diff_result.get("removed_results", []))
        modified += len(diff_result.get("status_changes", []))

    elif analyzer_type == "thermal":
        findings = diff_result.get("findings", {})
        added += len(findings.get("new", []))
        removed += len(findings.get("resolved", []))
        modified += len(findings.get("changed_severity", []))

    # Assessments (all analyzer types carry assessments[])
    assessments = diff_result.get("assessments", {})
    added += len(assessments.get("added", []))
    removed += len(assessments.get("removed", []))

    total = added + removed + modified
    severity = classify_severity(analyzer_type, diff_result)

    return {
        "total_changes": total,
        "added": added,
        "removed": removed,
        "modified": modified,
        "severity": severity,
    }


# ---------------------------------------------------------------------------
# Text formatter
# ---------------------------------------------------------------------------

MAX_TEXT_ITEMS = 20


def format_text(output):
    """Format diff output as human-readable text."""
    lines = []
    atype = output.get("analyzer_type", "?")
    summary = output.get("summary", {})
    severity = summary.get("severity", "none")
    total = summary.get("total_changes", 0)

    lines.append(f"Design Changes: {atype} ({severity}) — {total} changes")

    regressions = output.get("regressions", [])

    if total == 0 and not regressions:
        lines.append("  No changes detected.")
        return "\n".join(lines)

    s = summary
    lines.append(f"  +{s['added']} added, -{s['removed']} removed, ~{s['modified']} modified")

    if regressions:
        lines.append("")
        lines.append(f"\u26a0 {len(regressions)} regression(s) detected:")
        for r in regressions:
            lines.append(f"  [{r['severity'].upper()}] {r['detail']}")

    lines.append("")

    diff = output.get("diff", {})
    shown = 0

    # Components (schematic)
    comp = diff.get("components", {})
    if comp:
        lines.append("Components:")
        for c in comp.get("added", [])[:5]:
            lines.append(f"  + {c.get('reference', '?')} {c.get('value', '')} {c.get('footprint', '')}")
            shown += 1
        for c in comp.get("removed", [])[:5]:
            lines.append(f"  - {c.get('reference', '?')} {c.get('value', '')} {c.get('footprint', '')}")
            shown += 1
        for c in comp.get("modified", [])[:5]:
            ref = c.get("reference", "?")
            for ch in c.get("changes", []):
                lines.append(f"  ~ {ref}: {ch['field']} {ch.get('base', '?')} → {ch.get('head', '?')}")
            shown += 1
        lines.append("")

    # Signal analysis (schematic)
    sa = diff.get("signal_analysis", {})
    if sa:
        lines.append("Signal Analysis:")
        for det_type, det_diff in sa.items():
            label = det_type.replace("_", " ").title()
            for item in det_diff.get("added", [])[:3]:
                desc = " ".join(f"{k}={v}" for k, v in item.items())
                lines.append(f"  + New {label}: {desc}")
                shown += 1
            for item in det_diff.get("removed", [])[:3]:
                desc = " ".join(f"{k}={v}" for k, v in item.items())
                lines.append(f"  - Removed {label}: {desc}")
                shown += 1
            for item in det_diff.get("modified", [])[:3]:
                identity = item.get("identity", "?")
                changes = ", ".join(
                    f"{ch['field']} {ch.get('base', '?')} → {ch.get('head', '?')}"
                    for ch in item.get("changes", [])
                )
                lines.append(f"  ~ {label} {identity}: {changes}")
                attr = item.get("attributed_to", [])
                if attr:
                    causes = ", ".join(
                        f"{a['ref']} {a['base_value']}\u2192{a['head_value']}" for a in attr)
                    lines.append(f"      caused by: {causes}")
                shown += 1
            if shown >= MAX_TEXT_ITEMS:
                break
        lines.append("")

    # Footprints (PCB)
    fp = diff.get("footprints", {})
    if fp:
        lines.append("Footprints:")
        for f in fp.get("added", [])[:5]:
            lines.append(f"  + {f.get('reference', '?')} {f.get('value', '')} ({f.get('layer', '')})")
        for f in fp.get("removed", [])[:5]:
            lines.append(f"  - {f.get('reference', '?')} {f.get('value', '')} ({f.get('layer', '')})")
        for f in fp.get("modified", [])[:5]:
            ref = f.get("reference", "?")
            for ch in f.get("changes", []):
                lines.append(f"  ~ {ref}: {ch['field']} {ch.get('base', '?')} → {ch.get('head', '?')}")
        lines.append("")

    # EMC findings
    findings = diff.get("findings", {})
    if findings:
        lines.append("EMC Findings:")
        for f in findings.get("new", [])[:5]:
            lines.append(f"  NEW: {f.get('rule_id', '?')} ({f.get('severity', '?')}) {f.get('title', '')}")
        for f in findings.get("resolved", [])[:5]:
            lines.append(f"  RESOLVED: {f.get('rule_id', '?')} ({f.get('severity', '?')}) {f.get('title', '')}")
        for f in findings.get("changed_severity", [])[:3]:
            lines.append(f"  CHANGED: {f.get('rule_id', '?')} {f.get('base_severity', '?')} → {f.get('head_severity', '?')}")
        lines.append("")

    # SPICE status changes
    status_changes = diff.get("status_changes", [])
    if status_changes:
        lines.append("SPICE:")
        for sc in status_changes[:5]:
            direction = "REGRESSION" if sc.get("head_status") == "fail" else "FIXED" if sc.get("head_status") == "pass" else "CHANGED"
            comps = ", ".join(sc.get("components", []))
            lines.append(f"  {direction}: {sc.get('subcircuit_type', '?')} {comps}: "
                         f"{sc.get('base_status', '?')} → {sc.get('head_status', '?')}")
        lines.append("")

    # Assessments (informational measurements — present on all analyzer types)
    assessments = diff.get("assessments", {})
    if assessments and (assessments.get("added")
                        or assessments.get("removed")
                        or assessments.get("unchanged_count")):
        lines.append("Assessments:")
        added = assessments.get("added", [])
        removed = assessments.get("removed", [])
        if added:
            lines.append(f"  + Added ({len(added)}):")
            for a in added[:5]:
                refs = a.get("components") or []
                refs_str = "[" + ", ".join(refs) + "]" if refs else "[]"
                lines.append(f"    - {a.get('rule_id', '?')} on {refs_str}")
            if len(added) > 5:
                lines.append(f"    ... and {len(added) - 5} more")
        if removed:
            lines.append(f"  - Removed ({len(removed)}):")
            for a in removed[:5]:
                refs = a.get("components") or []
                refs_str = "[" + ", ".join(refs) + "]" if refs else "[]"
                lines.append(f"    - {a.get('rule_id', '?')} on {refs_str}")
            if len(removed) > 5:
                lines.append(f"    ... and {len(removed) - 5} more")
        unchanged = assessments.get("unchanged_count", 0)
        lines.append(f"  Unchanged: {unchanged}")
        lines.append("")

    # Risk score
    risk = diff.get("risk_score", {})
    if risk:
        lines.append(f"EMC Risk Score: {risk.get('base', '?')} → {risk.get('head', '?')} "
                      f"(delta {risk.get('delta', 0):+d})")
        lines.append("")

    remaining = total - shown
    if remaining > 0:
        lines.append(f"  ... and {remaining} more changes")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Deep review text formatter
# ---------------------------------------------------------------------------

def _format_deep_review_text(output):
    """Compact text block for a deep_review diff output."""
    dr = output.get("deep_review", {})
    fixed = dr.get("fixed", [])
    new = dr.get("new", [])
    still_open = dr.get("still_open", [])
    reworded = dr.get("reworded_candidates", [])
    quarantined_head = dr.get("quarantined_head", 0)

    lines = [
        f"Deep Review Changes: {len(fixed)} fixed, {len(new)} new, "
        f"{len(still_open)} still open, {quarantined_head} quarantined in head",
    ]
    if fixed:
        lines.append("")
        lines.append("Fixed:")
        for f in fixed[:MAX_TEXT_ITEMS]:
            lines.append(f"  - {f.get('finding_id', '?')} — {f.get('summary', '')}")
    if new:
        lines.append("")
        lines.append("New:")
        for f in new[:MAX_TEXT_ITEMS]:
            lines.append(f"  + {f.get('finding_id', '?')} — {f.get('summary', '')}")
    if still_open:
        lines.append("")
        lines.append(f"Still open: {len(still_open)} finding(s) unchanged")
    if reworded:
        lines.append("")
        lines.append("Reworded candidates (advisory):")
        for r in reworded:
            lines.append(
                f"  ~ {r.get('base_finding_id', '?')} → {r.get('head_finding_id', '?')}"
                f" [{r.get('category', '?')}]"
            )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Multi-run trend extraction
# ---------------------------------------------------------------------------

def _extract_trends(analysis_dir, output_type, n_runs):
    """Extract metric values across the last N runs.

    Returns {det_type: {identity: {field: [(run_id, value), ...]}}}
    """
    from analysis_cache import list_runs, CANONICAL_OUTPUTS

    runs = list_runs(analysis_dir, limit=n_runs)
    if len(runs) < 2:
        return {}

    filename = CANONICAL_OUTPUTS.get(output_type, f"{output_type}.json")
    trends = {}

    for run_id, _meta in runs:
        path = os.path.join(analysis_dir, run_id, filename)
        if not os.path.isfile(path):
            continue
        try:
            with open(path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        sa = group_findings_by_detection_type(data)
        for det_type, detections in sa.items():
            if not isinstance(detections, list):
                continue
            if det_type not in SIGNAL_REGISTRY:
                continue
            id_fields, val_fields = SIGNAL_REGISTRY[det_type]
            for det in detections:
                key = _identity_key(det, id_fields)
                if not key:
                    key = _generic_identity(det)
                if not key:
                    continue
                bucket = trends.setdefault(det_type, {}).setdefault(key, {})
                for field in val_fields:
                    val = _resolve(det, field)
                    if isinstance(val, (int, float)):
                        bucket.setdefault(field, []).append((run_id, val))

    return trends


def _format_trends(trends, n_runs):
    """Format trend data as human-readable text."""
    lines = []
    lines.append(f"Metric Trends (last {n_runs} runs)")
    lines.append("")

    if not trends:
        lines.append("  No tracked metrics found across runs.")
        return "\n".join(lines)

    for det_type in sorted(trends):
        lines.append(f"  {det_type}:")
        for identity in sorted(trends[det_type]):
            fields = trends[det_type][identity]
            for field, datapoints in sorted(fields.items()):
                if len(datapoints) < 2:
                    continue
                # Reverse to chronological (list_runs returns newest-first)
                datapoints = list(reversed(datapoints))
                vals = [f"{v:.4g}" for _, v in datapoints]
                first_val = datapoints[0][1]
                last_val = datapoints[-1][1]
                val_chain = " \u2192 ".join(vals)
                if first_val != 0:
                    pct = (last_val - first_val) / abs(first_val) * 100
                    arrow = "\u2191" if pct > 1 else "\u2193" if pct < -1 else "\u2192"
                    lines.append(f"    {identity} {field}: {val_chain} ({arrow}{abs(pct):.1f}%)")
                else:
                    lines.append(f"    {identity} {field}: {val_chain}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Compare two KiCad analysis JSON files and report changes"
    )
    parser.add_argument("base", nargs="?", help="Path to base (old) analysis JSON")
    parser.add_argument("head", nargs="?", help="Path to head (new) analysis JSON")
    parser.add_argument("--analysis-dir", "-d",
                        help="Analysis directory — auto-resolve runs from manifest")
    parser.add_argument("--run", action="append", default=[],
                        help="Run ID to compare (use twice: --run OLD --run NEW). "
                             "Special: 'current', 'previous', or YYYY-MM-DD_HHMM")
    parser.add_argument("--type", dest="output_type",
                        help="Output type to diff (schematic, pcb, emc, spice, "
                             "deep_review). Default: auto-detect first common output")
    parser.add_argument("--output", "-o", help="Write output JSON to file (default: stdout)")
    parser.add_argument("--text", action="store_true", help="Output human-readable text instead of JSON")
    parser.add_argument("--threshold", type=float, default=1.0,
                        help="Ignore numeric deltas below this percentage (default: 1.0%%)")
    parser.add_argument("--trend", type=int, metavar="N",
                        help="Show metric trends across last N runs (requires --analysis-dir)")
    parser.add_argument("--only-deterministic", action="store_true",
                        help="Read raw analysis/<run>/<analyzer>.json instead of "
                             "analysis/merged/<run>/<analyzer>.json. "
                             "Strips Layer 2 overlays for CI/offline use (Phase 4 spec §3.4).")
    args = parser.parse_args()

    # Resolve runs from analysis cache if --analysis-dir is provided
    if args.analysis_dir:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from analysis_cache import list_runs, CANONICAL_OUTPUTS

        analysis_dir = args.analysis_dir
        if not os.path.isdir(analysis_dir):
            print(f"Error: analysis directory not found: {analysis_dir}", file=sys.stderr)
            sys.exit(1)

        # Determine which runs to compare
        if len(args.run) == 2:
            run_ids = args.run
        elif len(args.run) == 1:
            run_ids = [args.run[0], "current"]
        else:
            run_ids = ["previous", "current"]

        # Resolve special names
        all_runs = list_runs(analysis_dir)
        if not all_runs:
            print("Error: no runs found in analysis directory", file=sys.stderr)
            sys.exit(1)

        resolved = []
        for rid in run_ids:
            if rid == "current":
                resolved.append(all_runs[0][0])
            elif rid == "previous":
                if len(all_runs) < 2:
                    print("Error: only one run exists — nothing to diff", file=sys.stderr)
                    sys.exit(1)
                resolved.append(all_runs[1][0])
            else:
                # Exact run ID
                found = False
                for r_id, _ in all_runs:
                    if r_id == rid:
                        found = True
                        break
                if not found:
                    print(f"Error: run '{rid}' not found in manifest", file=sys.stderr)
                    sys.exit(1)
                resolved.append(rid)

        # Determine output type
        out_type = args.output_type
        if not out_type:
            # Auto-detect: find first common output between the two runs
            for otype in ("schematic", "pcb", "emc", "spice"):
                fname = CANONICAL_OUTPUTS.get(otype, f"{otype}.json")
                if (os.path.isfile(os.path.join(analysis_dir, resolved[0], fname)) and
                    os.path.isfile(os.path.join(analysis_dir, resolved[1], fname))):
                    out_type = otype
                    break
            if not out_type:
                print("Error: no common output files between runs", file=sys.stderr)
                sys.exit(1)

        filename = CANONICAL_OUTPUTS.get(out_type, f"{out_type}.json")
        args.base = os.path.join(analysis_dir, resolved[0], filename)
        args.head = os.path.join(analysis_dir, resolved[1], filename)

    elif not args.base or not args.head:
        if not args.trend:
            parser.error("provide base and head paths, or use --analysis-dir")

    if args.trend:
        if not args.analysis_dir:
            parser.error("--trend requires --analysis-dir")
        out_type = args.output_type or "schematic"
        trends = _extract_trends(args.analysis_dir, out_type, args.trend)
        if args.text:
            print(_format_trends(trends, args.trend))
        else:
            json.dump({"trends": trends, "n_runs": args.trend}, sys.stdout, indent=2)
            print()
        sys.exit(0)

    # Load inputs (honor --only-deterministic: skip merged/ overlay)
    def _load_input(path, label):
        from pathlib import Path
        p = Path(path)
        if not args.only_deterministic:
            candidate = p.parent.parent / "merged" / p.parent.name / p.name
            if candidate.exists():
                p = candidate
        try:
            with open(p) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error reading {label} file {path}: {e}", file=sys.stderr)
            sys.exit(1)

    base = _load_input(args.base, "base")
    head = _load_input(args.head, "head")

    # Detect types
    base_type = detect_type(base)
    head_type = detect_type(head)
    if not base_type or not head_type:
        print("Error: could not detect analyzer type from JSON", file=sys.stderr)
        sys.exit(1)
    # Check for pre-v1.3 format
    old_files = []
    if base_type == "schematic_old":
        old_files.append(f"base ({args.base})")
    if head_type == "schematic_old":
        old_files.append(f"head ({args.head})")
    if old_files:
        print(f"Error: {' and '.join(old_files)} use the pre-v1.3 "
              f"signal_analysis wrapper format.\n"
              f"Re-run analyze_schematic.py to produce the current "
              f"findings[] format, then re-run this diff.",
              file=sys.stderr)
        sys.exit(1)
    if base_type != head_type:
        print(f"Error: type mismatch — base is {base_type}, head is {head_type}", file=sys.stderr)
        sys.exit(1)

    # Run diff
    # Note: deep_review is NOT in the dispatch table below because it has a
    # bespoke output envelope ({"deep_review": ...}) — it's handled by the
    # early-exit block immediately following. If the early-exit were removed,
    # the dict path would wrap the result under "diff" instead, breaking the
    # contract.
    diff_funcs = {
        "schematic": diff_schematic,
        "pcb": diff_pcb,
        "emc": diff_emc,
        "spice": diff_spice,
        "thermal": diff_thermal,
    }
    if base_type not in diff_funcs and base_type != "deep_review":
        print(f"Error: no diff function for analyzer type '{base_type}'",
              file=sys.stderr)
        sys.exit(1)

    if base_type == "deep_review":
        dr_result = diff_deep_review(base, head)
        output = {
            "diff_version": "1.0",
            "analyzer_type": base_type,
            "base_file": args.base,
            "head_file": args.head,
            "deep_review": dr_result,
        }
        if args.text:
            text = _format_deep_review_text(output)
            if args.output:
                with open(args.output, "w") as f:
                    f.write(text)
            else:
                print(text)
        else:
            output_json = json.dumps(output, indent=2)
            if args.output:
                with open(args.output, "w") as f:
                    f.write(output_json)
            else:
                print(output_json)
        sys.exit(0)

    diff_result = diff_funcs[base_type](base, head, args.threshold)
    summary = build_summary(base_type, diff_result)

    output = {
        "diff_version": "1.0",
        "analyzer_type": base_type,
        "base_file": args.base,
        "head_file": args.head,
        "has_changes": summary["total_changes"] > 0,
        "summary": summary,
        "diff": diff_result,
    }

    regressions = classify_regressions(base_type, diff_result)
    if regressions:
        output["regressions"] = regressions
        output["summary"]["regressions"] = len(regressions)

    if args.text:
        text = format_text(output)
        if args.output:
            with open(args.output, "w") as f:
                f.write(text)
        else:
            print(text)
    else:
        output_json = json.dumps(output, indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output_json)
        else:
            print(output_json)


if __name__ == "__main__":
    main()
