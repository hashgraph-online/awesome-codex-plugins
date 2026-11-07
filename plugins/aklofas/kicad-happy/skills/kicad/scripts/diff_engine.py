#!/usr/bin/env python3
"""Pure diff engine for kicad-happy analysis outputs.

Compares two parsed analyzer JSON documents and classifies the change.
No I/O, no CLI, no rendering: diff_analysis.py (the CLI + text renderer)
and analysis_cache.should_create_new_run both build on this module.
Split out of diff_analysis.py in the v3 refactor to remove the
analysis_cache <-> diff_analysis import cycle.
"""
import json
import re

from detection_schema import SCHEMAS as _SCHEMAS
from finding_schema import group_findings_by_detection_type
from kicad_core.render import normalize_severity, severity_bucket, summary_or_title


# ---------------------------------------------------------------------------
# Signal analysis identity & value registry
# ---------------------------------------------------------------------------
# Maps detection type -> (identity_fields, value_fields)
# identity_fields: dotpath fields that uniquely identify a detection
# value_fields: numeric/string fields to compare for changes


# SIGNAL_REGISTRY is derived from the unified detection schema.
# Kept as a module-level name; validate_signal_registry reads it.
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


# A `#N` suffix is the producer's collision counter: it follows list order, not the finding.
_POSITIONAL_SUFFIX = re.compile(r"#\d+$")
# Unnamed nets are numbered per run; the number moves when unrelated wiring changes.
_UNNAMED_NET = re.compile(r"__unnamed_\d+", re.IGNORECASE)


def _fid_stem(fid):
    return _POSITIONAL_SUFFIX.sub("", fid)


def _content_key(f):
    def _join(values):
        return ",".join(sorted(_UNNAMED_NET.sub("__unnamed", str(v))
                               for v in (values or []) if not isinstance(v, (dict, list))))
    summary = _UNNAMED_NET.sub("__unnamed", str(f.get("summary") or ""))
    return f"{f.get('rule_id', '')}::{_join(f.get('nets'))}::{_join(f.get('components'))}::{summary}"


def finding_key(f, positional=None):
    """The identity of one finding across two runs.

    Its `finding_id`, unless that id is positional (a `#N` collision suffix, or
    an unnamed-net locator); then a content key from rule_id, sorted nets
    (unnamed-net numbers dropped), sorted components and summary. Pass
    `positional=True` for an id whose stem collides in either run, which makes
    even the unsuffixed first member of the group positional.
    """
    fid = f.get("finding_id")
    if isinstance(fid, str) and fid:
        if positional is None:
            positional = bool(_POSITIONAL_SUFFIX.search(fid))
        if not positional and not _UNNAMED_NET.search(fid):
            return fid
    return _content_key(f)


def _canonical(f):
    rest = {k: v for k, v in f.items() if k != "finding_id"}
    return _UNNAMED_NET.sub("__unnamed", json.dumps(rest, sort_keys=True, default=str))


def match_findings(base_items, head_items, legacy_key=None, prefer_legacy=False):
    """Key two finding lists for matching; returns (base_map, head_map), key -> finding.

    `legacy_key(f)` is the section's older identity: it keys findings without a
    `finding_id` (older JSON), and with `prefer_legacy` it is kept for any
    finding whose legacy key is unique in both runs. Everything else is keyed
    by `finding_key`, an id stem being positional when it collides in either
    run. Findings that still share a key are numbered after sorting them by
    content, so input order never pairs two different findings.
    """
    sides = [[f for f in (items if isinstance(items, list) else []) if isinstance(f, dict)]
             for items in (base_items, head_items)]
    legacy = [[(legacy_key(f) if legacy_key else None) for f in side] for side in sides]
    legacy_counts = [{} for _ in sides]
    for counts, keys in zip(legacy_counts, legacy):
        for k in keys:
            if k:
                counts[k] = counts.get(k, 0) + 1
    positional = set()
    for side in sides:
        stems = {}
        for f in side:
            fid = f.get("finding_id")
            if isinstance(fid, str) and fid:
                stem = _fid_stem(fid)
                stems[stem] = stems.get(stem, 0) + 1
                if stem != fid:
                    positional.add(stem)
        positional.update(s for s, n in stems.items() if n > 1)

    def _unique_legacy(k):
        return (k and not _UNNAMED_NET.search(k)
                and all(counts.get(k, 0) <= 1 for counts in legacy_counts))

    keyed = []
    for side, lkeys in zip(sides, legacy):
        keys = []
        for f, lk in zip(side, lkeys):
            fid = f.get("finding_id")
            has_fid = isinstance(fid, str) and bool(fid)
            if _unique_legacy(lk) and (prefer_legacy or not has_fid):
                keys.append(lk)
            elif has_fid:
                keys.append(finding_key(f, positional=_fid_stem(fid) in positional))
            else:
                keys.append(_content_key(f))
        keyed.append(keys)

    shared = set()
    for keys in keyed:
        seen = set()
        for k in keys:
            if k in seen:
                shared.add(k)
            seen.add(k)
    groups = []
    for side, keys in zip(sides, keyed):
        g = {}
        for f, k in zip(side, keys):
            g.setdefault(k, []).append(f)
        groups.append(g)
    numbered = [{}, {}]
    for k in sorted(shared):
        # Identical findings pair first, so a removed member of the group is
        # reported as removed rather than shifting its neighbours' numbers.
        pools = [sorted(g.get(k, []), key=_canonical) for g in groups]
        canon = [[_canonical(f) for f in pool] for pool in pools]
        n = 0
        head_used = [False] * len(pools[1])
        base_left = []
        for bf, bc in zip(pools[0], canon[0]):
            for j, hc in enumerate(canon[1]):
                if not head_used[j] and hc == bc:
                    head_used[j] = True
                    n += 1
                    numbered[0].setdefault(k, []).append((f"{k}#{n}", bf))
                    numbered[1].setdefault(k, []).append((f"{k}#{n}", pools[1][j]))
                    break
            else:
                base_left.append(bf)
        head_left = [f for f, used in zip(pools[1], head_used) if not used]
        for side, left in ((0, base_left), (1, head_left)):
            for m, f in enumerate(left, n + 1):
                numbered[side].setdefault(k, []).append((f"{k}#{m}", f))
    maps = []
    for side in (0, 1):
        out = {}
        for k, group in groups[side].items():
            if k in shared:
                out.update(numbered[side][k])
            else:
                out[k] = group[0]
        maps.append(out)
    return maps[0], maps[1]


def _diff_lists(base_items, head_items, id_fields, value_fields, threshold):
    """Match items by identity, return added/removed/modified/unchanged.

    Returns:
        {added: [...], removed: [...], modified: [...], unchanged_count: int}
    """
    result = {"added": [], "removed": [], "modified": [], "unchanged_count": 0}

    def _get_key(item):
        did = item.get("detection_id")
        if did:
            return did
        if id_fields:
            key = _identity_key(item, id_fields)
            if key:
                return key
        return _generic_identity(item)

    base_map, head_map = match_findings(base_items, head_items, _get_key, prefer_legacy=True)

    fields = [f for f in value_fields if f != "severity"] + ([] if value_fields else ["summary"])

    # Find added, removed, modified
    for key, item in head_map.items():
        if key not in base_map:
            result["added"].append(_summarize_detection(item, id_fields))
        else:
            changes = _compare_fields(base_map[key], item, fields, threshold)
            changes += _severity_change(base_map[key], item)
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


def _severity_change(base_item, head_item):
    """[change] when the two severities differ in meaning (legacy `WARN` and
    `warning` are the same), else []."""
    bv, hv = base_item.get("severity"), head_item.get("severity")
    if severity_bucket(bv) == severity_bucket(hv):
        return []
    return [{"field": "severity", "base": bv, "head": hv}]


def _compare_fields(base_item, head_item, fields, threshold):
    """Compare specific fields between two matched items. Returns list of changes."""
    changes = []
    for field in fields:
        bv = _resolve(base_item, field)
        hv = _resolve(head_item, field)
        if bv == hv:
            continue
        if isinstance(bv, str) and isinstance(hv, str) and \
                _UNNAMED_NET.sub("__unnamed", bv) == _UNNAMED_NET.sub("__unnamed", hv):
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
    if not summary:
        for key in ("rule_id", "severity", "components", "summary"):
            if item.get(key):
                summary[key] = item[key]
    return summary


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
                    # finding_ids carry refs lowercased; match whole tokens
                    # without case so C1 never claims C11.
                    named = {t.lower() for t in re.split(r"[^A-Za-z0-9_]+", mod.get("identity", ""))}
                    for item_key in ("base_item", "head_item"):
                        item = mod.get(item_key, {})
                        if isinstance(item, dict):
                            for key, val in item.items():
                                if isinstance(val, dict) and isinstance(val.get("ref"), str):
                                    named.add(val["ref"].lower())
                            comps = item.get("components")
                            if isinstance(comps, list):
                                named.update(c.lower() for c in comps if isinstance(c, str))
                    for ref in comp_changes:
                        if ref.lower() in named:
                            attributed.append(ref)
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
            return _UNNAMED_NET.sub("__unnamed", json.dumps(item, sort_keys=True))
        return _UNNAMED_NET.sub("__unnamed", str(item))

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
    def _pair_in_pin_order(x):
        # A pair lists its pins in net order, which moves with the net; keep
        # each pin_type with its pin.
        if not isinstance(x, dict) or not isinstance(x.get("pins"), list):
            return x
        pins, types = x["pins"], x.get("pin_types")
        out = dict(x)
        if isinstance(types, list) and len(types) == len(pins):
            pairs = sorted(zip(pins, types), key=lambda pt: json.dumps(pt, sort_keys=True))
            out["pins"] = [p for p, _ in pairs]
            out["pin_types"] = [t for _, t in pairs]
        else:
            out["pins"] = sorted(pins, key=lambda p: json.dumps(p, sort_keys=True))
        return out

    def _erc_key(w):
        if isinstance(w, dict):
            net = w.get("net", "")
            if isinstance(net, str) and _UNNAMED_NET.search(net):
                # the pins name an unnamed net; its number does not
                pins = sorted(json.dumps(_pair_in_pin_order(x), sort_keys=True)
                              for x in (w.get("pins") or []) + (w.get("pairs") or []))
                return (w.get("type", ""), "__unnamed",
                        _UNNAMED_NET.sub("__unnamed", str(w.get("message", ""))),
                        _UNNAMED_NET.sub("__unnamed", "|".join(pins)))
            return (w.get("type", ""), net, w.get("message", ""))
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

    def _fpid(fp):
        return fp.get("footprint") or fp.get("library") or fp.get("lib_id") or ""

    fp_diff = {"added": [], "removed": [], "modified": []}
    for ref, fp in head_fps.items():
        if ref not in base_fps:
            fp_diff["added"].append({
                "reference": ref, "value": fp.get("value", ""),
                "footprint": _fpid(fp), "layer": fp.get("layer", ""),
            })
        else:
            bfp = base_fps[ref]
            changes = []
            for field, bv, hv in (("value", bfp.get("value", ""), fp.get("value", "")),
                                  ("footprint", _fpid(bfp), _fpid(fp)),
                                  ("layer", bfp.get("layer", ""), fp.get("layer", ""))):
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

    findings_diff = _diff_findings(base, head, _rule_components_key, "summary")
    if findings_diff:
        result["findings"] = findings_diff

    _attach_assessments_diff(result, base, head)

    return result


def _rule_components_key(f):
    return f"{f.get('rule_id', '')}::{'|'.join(sorted(map(str, f.get('components') or [])))}"


def _diff_findings(base, head, legacy_key, text_key):
    """new / resolved / changed_severity between two envelopes' findings[], or {}.

    Findings match by `match_findings`. `text_key` is the row field carrying the
    finding's text: "title" (EMC, read through summary_or_title) or "summary".
    """
    base_map, head_map = match_findings(base.get("findings", []), head.get("findings", []), legacy_key)

    def _text(f):
        return summary_or_title(f) if text_key == "title" else f.get("summary", "")

    def _row(f, located):
        row = {"rule_id": f.get("rule_id", ""), "severity": f.get("severity", ""), text_key: _text(f)}
        if text_key == "title":
            row["category"] = f.get("category", "")
            if located:
                row["nets"] = f.get("nets", [])
        if located:
            row["components"] = f.get("components", [])
        return row

    out = {"new": [], "resolved": [], "changed_severity": []}
    for key, f in head_map.items():
        if key not in base_map:
            out["new"].append(_row(f, True))
        elif _severity_change(base_map[key], f):
            out["changed_severity"].append({
                "rule_id": f.get("rule_id", ""),
                "base_severity": base_map[key].get("severity", ""),
                "head_severity": f.get("severity", ""),
                text_key: _text(f),
            })
    for key, f in base_map.items():
        if key not in head_map:
            out["resolved"].append(_row(f, False))
    return out if (out["new"] or out["resolved"] or out["changed_severity"]) else {}


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
    sev_paths = ["summary.by_severity.error", "summary.by_severity.warning",
                 "summary.by_severity.info",
                 # flat counts of pre-v1.4 output
                 "summary.critical", "summary.high", "summary.medium",
                 "summary.low", "summary.info"]
    sev_delta = _diff_counts(base, head, sev_paths)
    if sev_delta:
        result["by_severity"] = sev_delta

    def _legacy_key(f):
        rule = f.get("rule_id", "")
        nets = "|".join(sorted(f.get("nets", [])))
        comps = "|".join(sorted(f.get("components", [])))
        return f"{rule}::{nets}::{comps}"

    findings_diff = _diff_findings(base, head, _legacy_key, "title")
    if findings_diff:
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
                 "summary.info", "summary.total"]
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

    findings_diff = _diff_findings(base, head, _rule_components_key, "summary")
    if findings_diff:
        result["findings"] = findings_diff

    _attach_assessments_diff(result, base, head)

    return result


# ---------------------------------------------------------------------------
# Deep review diff
# ---------------------------------------------------------------------------

def diff_deep_review(base, head, threshold=None):
    """Diff two deep_review.json files.

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
    if "routing_complete" in diff_result or "unrouted" in diff_result:
        return "major"

    # Minor: anything else that moved (counts, scores, BOM, ERC fixes, ...)
    if has_changes(diff_result):
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
        # The risk score runs 0 (worst) to 100 (lowest risk): a fall is the regression.
        risk = diff_result.get("risk_score", {})
        if isinstance(risk, dict) and risk.get("delta", 0) < 0:
            regressions.append({
                "category": "emc_risk",
                "severity": "major",
                "detail": f"EMC risk score fell (100 = lowest risk): {risk.get('base', '?')} \u2192 {risk.get('head', '?')}",
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

# Sections keyed by the analyzer-output path of a scalar ({path: {base, head,
# delta}}), and single-scalar sections with the path they read.
_METRIC_SECTIONS = ("statistics", "unrouted", "by_severity", "summary")
_METRIC_SCALARS = {"routing_complete": "connectivity.routing_complete",
                   "risk_score": "summary.emc_risk_score"}


def has_changes(diff_result):
    """True when any diff section records a change.

    An assessments block holding only `unchanged_count` is not a change.
    """
    for key, value in diff_result.items():
        if key == "assessments":
            if value.get("added") or value.get("removed"):
                return True
        elif value:
            return True
    return False


def build_summary(analyzer_type, diff_result):
    """Build a top-level summary of all changes.

    `total_changes` counts listed items (components, detections, footprints,
    findings, simulation results, assessments, BOM lines, connectivity issues,
    ERC warnings, per-net scores, Monte Carlo concerns). Scalar paths
    (statistics, routing, unrouted, risk score, severity counts, SPICE summary
    counts) are listed by path in `metric_changes`, so one added part is not
    counted again through every rollup it moves.
    """
    added = removed = modified = 0

    def _count(section, add_key, remove_key, modify_key=None):
        nonlocal added, removed, modified
        added += len(section.get(add_key) or [])
        removed += len(section.get(remove_key) or [])
        if modify_key:
            modified += len(section.get(modify_key) or [])

    for key in ("components", "footprints"):
        _count(diff_result.get(key, {}), "added", "removed", "modified")
    for det_diff in diff_result.get("signal_analysis", {}).values():
        _count(det_diff, "added", "removed", "modified")
    _count(diff_result.get("findings", {}), "new", "resolved", "changed_severity")
    _count(diff_result.get("bom", {}), "added", "removed", "quantity_changes")
    for conn in diff_result.get("connectivity", {}).values():
        _count(conn, "new", "resolved")
    _count(diff_result.get("erc", {}), "new_warnings", "resolved_warnings")
    _count(diff_result.get("monte_carlo", {}), "new", "resolved")
    _count(diff_result.get("assessments", {}), "added", "removed")
    added += len(diff_result.get("new_results", []))
    removed += len(diff_result.get("removed_results", []))
    modified += len(diff_result.get("status_changes", []))
    modified += len(diff_result.get("per_net_scores", []))

    metric_changes = [path for k in _METRIC_SECTIONS for path in (diff_result.get(k) or {})]
    metric_changes += [path for k, path in _METRIC_SCALARS.items() if k in diff_result]

    return {
        "total_changes": added + removed + modified,
        "added": added,
        "removed": removed,
        "modified": modified,
        "metric_changes": sorted(metric_changes),
        "severity": classify_severity(analyzer_type, diff_result),
    }
