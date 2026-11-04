"""Schematic audits (annotation, labels, PWR_FLAG, footprint filters, sourcing, datasheet coverage, generic transistor symbols, grounds, bus topology, wire geometry, pin coverage, instance and hierarchical-label consistency): verbatim move from analyze_schematic.py; no behaviour change."""
from __future__ import annotations

import json
import math
import re
from pathlib import (
    Path,
)
from kicad_core.classify import NON_COMPONENT_TYPES
from kicad_core.netnames import (
    is_ground_name as _is_ground_name,
)
from schematic.connectivity import (
    expand_bus_name,
)


def check_annotation_completeness(components: list[dict]) -> dict:
    """Check for annotation issues: duplicate references, unannotated ('?') refs, missing values.

    These are common pre-fabrication mistakes that KiCad's ERC should also catch,
    but detecting them in the script output helps catch them earlier in the workflow.
    """
    # Skip power symbols and flags
    real_components = [c for c in components
                       if c["type"] not in ("power_symbol", "power_flag", "flag")]

    # Duplicate references (same ref, different UUID — not multi-unit which share refs)
    ref_uuids: dict[str, list[str]] = {}
    for c in real_components:
        ref_uuids.setdefault(c["reference"], []).append(c["uuid"])
    # Multi-unit symbols legitimately share a reference, so only flag if the
    # UUIDs come from symbols with unit=None (single-unit) or if there are
    # more instances than expected units
    duplicates = []
    for ref, uuids in ref_uuids.items():
        if len(uuids) > 1:
            # Check if these are multi-unit instances (different unit numbers)
            units = [c.get("unit") for c in real_components if c["reference"] == ref]
            unique_units = set(u for u in units if u is not None)
            if len(unique_units) < len(uuids):
                duplicates.append(ref)

    # Unannotated references (contain '?')
    unannotated = sorted(set(
        c["reference"] for c in real_components if "?" in c["reference"]
    ))

    # Missing values (empty or "~" which KiCad uses as placeholder)
    missing_value = sorted(set(
        c["reference"] for c in real_components
        if c["type"] not in ("test_point", "mounting_hole", "fiducial", "graphic")
        and (not c["value"] or c["value"] == "~")
    ))

    # References that don't follow standard numbering (e.g., R0, C0 — unusual starting point)
    zero_indexed = sorted(set(
        c["reference"] for c in real_components
        if re.match(r'^[A-Z]+0$', c["reference"])
    ))

    result = {}
    if duplicates:
        result["duplicate_references"] = sorted(duplicates)
    if unannotated:
        result["unannotated"] = unannotated
    if missing_value:
        result["missing_value"] = missing_value
    if zero_indexed:
        result["zero_indexed_refs"] = zero_indexed
    return result


def validate_label_shapes(labels: list[dict], nets: dict) -> list[dict]:
    """Validate global/hierarchical label shapes against net signal direction.

    Label shapes (input, output, bidirectional, tri_state, passive) should be
    consistent for the same net name and should match the electrical direction
    of the signals on that net.
    """
    warnings = []

    # Group labels by net name
    net_labels: dict[str, list[dict]] = {}
    for lbl in labels:
        if lbl["type"] in ("global_label", "hierarchical_label") and lbl.get("shape"):
            net_labels.setdefault(lbl["name"], []).append(lbl)

    # Check for shape inconsistency within the same net
    for net_name, lbls in net_labels.items():
        shapes = set(l["shape"] for l in lbls)
        if len(shapes) > 1:
            warnings.append({
                "type": "inconsistent_shape",
                "net": net_name,
                "shapes": sorted(shapes),
                "message": f"Net '{net_name}' has labels with different shapes: {sorted(shapes)}",
            })

    # Check for input-shaped labels on nets driven only by other inputs (no source)
    for net_name, lbls in net_labels.items():
        shapes = set(l["shape"] for l in lbls)
        if shapes == {"input"} and net_name in nets:
            net_info = nets[net_name]
            pin_types = set(p["pin_type"] for p in net_info["pins"]
                           if not p["component"].startswith("#"))
            drivers = {"output", "tri_state", "power_out", "open_collector", "open_emitter", "bidirectional"}
            if not (pin_types & drivers):
                warnings.append({
                    "type": "undriven_input_label",
                    "net": net_name,
                    "message": f"Net '{net_name}' has input-shaped label(s) but no driver pins on the net",
                })

    return warnings


def audit_pwr_flags(components: list[dict], nets: dict, known_power_rails: set) -> list[dict]:
    """Audit power rails for missing PWR_FLAG symbols.

    KiCad requires PWR_FLAG on power nets that are only driven by power_in pins
    (e.g., a connector supplying power). Without PWR_FLAG, ERC reports "power pin
    not driven" errors.
    """
    warnings = []

    # Check each power rail (sorted: set order is hash-randomized per
    # process and pwr_flag_warnings must be byte-stable across runs)
    for net_name in sorted(known_power_rails):
        if net_name not in nets:
            continue
        net_info = nets[net_name]
        # KH-354: PWR_FLAG pins never appear in pins[] (build_net_map
        # registers them as source points) — credit the net-level flag.
        if net_info.get("has_pwr_flag"):
            continue
        pin_types = set(p["pin_type"] for p in net_info["pins"])

        # If the net has only power_in pins (no power_out), it needs PWR_FLAG
        has_power_out = "power_out" in pin_types
        has_power_in = "power_in" in pin_types

        if has_power_in and not has_power_out:
            warnings.append({
                "net": net_name,
                "message": f"Power rail '{net_name}' has power_in pins but no power_out or PWR_FLAG — ERC will flag this",
                "pin_types": sorted(pin_types),
            })

    return warnings


def validate_footprint_filters(components: list[dict], lib_symbols: dict) -> list[dict]:
    """Validate assigned footprints against library symbol ki_fp_filters.

    If a symbol defines footprint filter patterns (ki_fp_filters), the assigned
    footprint should match at least one pattern. Mismatches suggest wrong footprint
    assignment (e.g., through-hole resistor assigned to SMD symbol).
    """
    import fnmatch
    warnings = []

    for c in components:
        if c["type"] in NON_COMPONENT_TYPES:
            continue
        if not c["footprint"]:
            continue

        sym_def = lib_symbols.get(c["lib_id"], {})
        fp_filters_str = sym_def.get("ki_fp_filters", "")
        if not fp_filters_str:
            continue

        # ki_fp_filters is a space-separated list of glob patterns
        patterns = fp_filters_str.split()
        if not patterns:
            continue

        # Extract just the footprint name (after the library prefix)
        fp_name = c["footprint"].split(":")[-1] if ":" in c["footprint"] else c["footprint"]
        fp_full = c["footprint"]

        # Check if any pattern matches
        matched = False
        for pat in patterns:
            if fnmatch.fnmatch(fp_name, pat) or fnmatch.fnmatch(fp_full, pat):
                matched = True
                break

        if not matched:
            # Check if the footprint is from a custom/project-local library.
            # Standard KiCad libraries use well-known prefixes; anything else
            # is project-local and mismatches are intentional.
            _STANDARD_FP_LIBS = {
                "Capacitor_SMD", "Capacitor_THT", "Resistor_SMD", "Resistor_THT",
                "Inductor_SMD", "Inductor_THT", "Package_SO", "Package_QFP",
                "Package_DFN_QFN", "Package_BGA", "Package_TO_SOT_SMD",
                "Package_TO_SOT_THT", "Connector_PinHeader", "Connector_PinSocket",
                "Connector_USB", "Crystal", "LED_SMD", "LED_THT", "Diode_SMD",
                "Diode_THT", "RF_Module", "Button_Switch_SMD", "Button_Switch_THT",
                "Fuse", "TestPoint", "Buzzer_Beeper", "Relay_SMD", "Relay_THT",
                "Transformer_SMD", "Transformer_THT", "Varistor", "Jumper",
                "MountingHole", "Fiducial", "Heatsink",
            }
            sym_lib = c["lib_id"].split(":")[0] if ":" in c["lib_id"] else ""
            fp_lib = c["footprint"].split(":")[0] if ":" in c["footprint"] else ""
            custom_library = bool(fp_lib and (
                (sym_lib and sym_lib.lower() == fp_lib.lower())
                or fp_lib not in _STANDARD_FP_LIBS
            ))

            warnings.append({
                "component": c["reference"],
                "footprint": c["footprint"],
                "filters": patterns,
                "custom_library": custom_library,
                "message": f"{c['reference']}: footprint '{fp_name}' doesn't match any filter pattern {patterns}",
            })

    return warnings


def _bom_real_components(components: list[dict]) -> list[dict]:
    """Filter to components that count as real BOM parts.

    Excludes power symbols/flags, test points, mounting holes, fiducials,
    graphics, DNP parts, and anything not marked in_bom. Shared by
    audit_datasheet_coverage (DS-001/002/003) and audit_sourcing_gate
    (SS-001/002/003) — both need the same "real BOM part" definition
    (KH-390).
    """
    return [c for c in components
            if c.get("type") not in NON_COMPONENT_TYPES
            and c.get("in_bom") and not c.get("dnp")]


def audit_datasheet_coverage(components: list[dict],
                             project_dir: str) -> list[dict]:
    """Emit a banner-level finding when datasheet evidence is absent.

    Datasheets are what separate a consistency check from a correctness
    check: without them, the reviewer can only confirm the design agrees
    with itself. When the project has no ``datasheets/`` directory AND
    none of its BOM components carry an MPN, any pin-level or electrical
    claim in a downstream review is guesswork. Surface that fact loudly
    instead of letting it slip into a footnote.

    Rule IDs: DS-001 (no datasheets dir + no MPNs — reviews cannot be
    grounded in manufacturer data), DS-002 (datasheets dir missing but
    MPNs are set — offer to sync).
    """
    findings: list[dict] = []
    real = _bom_real_components(components)
    # Deduplicate by reference (multi-unit symbols)
    seen = set()
    unique = []
    for c in real:
        ref = c.get("reference", "")
        if ref and ref not in seen:
            seen.add(ref)
            unique.append(c)
    total = len(unique)
    if total == 0:
        return findings

    with_mpn = [c for c in unique if c.get("mpn")]
    mpn_count = len(with_mpn)
    mpn_pct = (mpn_count / total * 100) if total else 0.0

    # Look for datasheets in conventional locations relative to the
    # project directory. extracted/ holds structured extractions from the
    # datasheet_extract_cache; its presence implies datasheets exist.
    import os as _os
    pd = project_dir or "."
    # rc.2 4.2: widened search — walk up 1–2 parent dirs and match the case-
    # insensitive [Dd]atasheets?/ pattern (singular or plural). Eliminates
    # DS-001 FPs on repos where the datasheets directory lives one level up
    # (multi-project monorepos, board variant subfolders, etc.).
    _DS_DIR_NAMES = (
        "datasheets", "Datasheets",
        "datasheet", "Datasheet",
    )
    candidates: list[str] = []
    _bases = [pd, _os.path.dirname(pd) or pd]
    _grand = _os.path.dirname(_bases[1]) if _bases[1] else pd
    if _grand and _grand != _bases[1]:
        _bases.append(_grand)
    for _base in _bases:
        for _name in _DS_DIR_NAMES:
            candidates.append(_os.path.join(_base, _name))
            candidates.append(_os.path.join(_base, _name, "extracted"))
        candidates.append(_os.path.join(_base, "docs", "datasheets"))
        candidates.append(_os.path.join(_base, "documentation", "datasheets"))
    ds_dir_found = next(
        (c for c in candidates if _os.path.isdir(c)), None)
    ds_file_count = 0
    if ds_dir_found:
        try:
            for _root, _dirs, _files in _os.walk(ds_dir_found):
                ds_file_count += sum(1 for f in _files
                                     if f.lower().endswith((".pdf", ".json")))
        except OSError:
            pass

    # Build finding.
    if ds_dir_found and ds_file_count > 0:
        # Datasheets present — no banner needed. Emit info-only if coverage
        # is partial so the reviewer knows which lines are ungrounded.
        # DS-003 counts by unique BOM line (value + footprint), the same
        # basis SS-002 uses — a line has coverage if ANY instance carries
        # an MPN (KH-390: the two denominators used to disagree).
        line_groups: dict[tuple, dict] = {}
        for c in real:
            key = (c.get("value", ""), c.get("footprint", ""))
            line = line_groups.setdefault(key, {"refs": [], "has_mpn": False})
            r = c.get("reference", "")
            if r:
                line["refs"].append(r)
            if c.get("mpn"):
                line["has_mpn"] = True
        line_total = len(line_groups)
        missing_lines = [line for line in line_groups.values()
                         if not line["has_mpn"]]
        line_pct = ((line_total - len(missing_lines)) / line_total * 100
                    if line_total else 0.0)
        refs_without_mpn = sorted(
            {r for line in missing_lines for r in line["refs"]})[:20]
        if line_pct < 90 and refs_without_mpn:
            findings.append({
                "detector": "audit_datasheet_coverage",
                "rule_id": "DS-003",
                "severity": "info",
                "confidence": "deterministic",
                "evidence_source": "bom",
                "category": "verification",
                "summary": (f"Datasheets present ({ds_file_count} files) but "
                            f"{len(missing_lines)} of {line_total} unique "
                            "BOM lines lack an MPN — those lines can't be "
                            "cross-referenced."),
                "components": refs_without_mpn,
                "nets": [],
                "pins": [],
                "datasheets_dir": ds_dir_found,
                "datasheet_file_count": ds_file_count,
                "bom_size": line_total,
                "mpn_coverage_percent": round(line_pct, 1),
                "recommendation": ("Set the MPN field on the listed parts "
                                   "and re-sync datasheets so every BOM "
                                   "entry has manufacturer evidence."),
                "report_context": {
                    "section": "Datasheet Coverage",
                    "impact": ("Partial coverage: pin mapping and electrical "
                               "claims for unmapped parts remain unverified."),
                    "standard_ref": "",
                },
            })
        return findings

    if mpn_count == 0:
        # DS-001: no datasheets dir AND no MPNs. Downstream review cannot
        # make any verified claim — this is a correctness-vs-consistency
        # gap the reviewer has to state up front.
        findings.append({
            "detector": "audit_datasheet_coverage",
            "rule_id": "DS-001",
            "severity": "error",
            "confidence": "deterministic",
            "evidence_source": "bom",
            "category": "verification",
            "summary": ("No datasheets directory found and no BOM parts "
                        "have MPNs. Review is a consistency check only — "
                        "manufacturer specs cannot be verified."),
            "components": [],
            "nets": [],
            "pins": [],
            "datasheets_dir": None,
            "datasheet_file_count": 0,
            "bom_size": total,
            "mpn_coverage_percent": 0.0,
            "recommendation": (
                "Before reporting 'verified' findings, (1) populate the MPN "
                "field on BOM parts, (2) run the datasheet sync skill "
                "(digikey, mouser, lcsc, or element14) to download PDFs "
                "into ./datasheets/, then re-run analysis. If datasheets "
                "are unreachable, state every pin-level and electrical "
                "claim as 'per symbol/library' (consistency), not "
                "'verified against datasheet' (correctness)."),
            "report_context": {
                "section": "Datasheet Coverage",
                "impact": ("Report wording must avoid 'verified' / "
                           "'datasheet-confirmed' language for every BOM "
                           "part — none have manufacturer evidence "
                           "attached."),
                "standard_ref": "",
            },
        })
    else:
        # DS-002: MPNs exist but no datasheets dir. Low-friction fix — tell
        # the reviewer to run sync.
        findings.append({
            "detector": "audit_datasheet_coverage",
            "rule_id": "DS-002",
            "severity": "warning",
            "confidence": "deterministic",
            "evidence_source": "bom",
            "category": "verification",
            "summary": (f"No datasheets directory found ({mpn_count}/{total}"
                        " parts have MPNs). Sync datasheets before making "
                        "pin-level claims."),
            "components": sorted(c.get("reference", "")
                                 for c in with_mpn)[:20],
            "nets": [],
            "pins": [],
            "datasheets_dir": None,
            "datasheet_file_count": 0,
            "bom_size": total,
            "mpn_coverage_percent": round(mpn_pct, 1),
            "recommendation": (
                "Run datasheet sync via the digikey / mouser / lcsc / "
                "element14 skill (which one depends on the user's "
                "distributor access and API credentials). A ./datasheets/ "
                "directory with PDFs and a manifest.json enables pin-level "
                "verification in the next analyzer run."),
            "report_context": {
                "section": "Datasheet Coverage",
                "impact": ("Review claims must stay at consistency level "
                           "until datasheets land."),
                "standard_ref": "",
            },
        })
    return findings


def audit_sourcing_fields(components: list[dict]) -> dict:
    """Audit component sourcing completeness: MPN, distributor part numbers.

    For manufacturing readiness, every BOM component needs at minimum an MPN.
    Distributor PNs (DigiKey, Mouser, LCSC) accelerate ordering.
    """
    real = [c for c in components
            if c["type"] not in NON_COMPONENT_TYPES
            and c["in_bom"] and not c["dnp"]]

    # Deduplicate by reference (multi-unit symbols)
    seen = set()
    unique = []
    for c in real:
        if c["reference"] not in seen:
            seen.add(c["reference"])
            unique.append(c)

    missing_mpn = [c["reference"] for c in unique if not c.get("mpn")]
    missing_digikey = [c["reference"] for c in unique if not c.get("digikey")]
    missing_mouser = [c["reference"] for c in unique if not c.get("mouser")]
    missing_lcsc = [c["reference"] for c in unique if not c.get("lcsc")]

    total = len(unique)
    result = {
        "total_bom_components": total,
        "mpn_coverage": f"{total - len(missing_mpn)}/{total}",
    }
    if missing_mpn:
        result["missing_mpn"] = sorted(missing_mpn)
    if missing_digikey:
        result["missing_digikey"] = sorted(missing_digikey)
    if missing_lcsc:
        result["missing_lcsc"] = sorted(missing_lcsc)

    # Compute readiness score
    if total > 0:
        mpn_pct = (total - len(missing_mpn)) / total * 100
        result["mpn_percent"] = round(mpn_pct, 1)
    return result


def audit_sourcing_gate(components: list[dict]) -> list[dict]:
    """Emit rich findings that gate fabrication on BOM completeness.

    `audit_sourcing_fields()` returns a numeric summary; this surfaces
    the gap as findings so the stage filter and severity rollups see
    it. Rule tiers:
      SS-001  mpn_percent < 50        severity=error  (pre-fab blocker)
      SS-002  50 <= mpn_percent < 80  severity=warning
      SS-003  80 <= mpn_percent < 100 severity=info
    mpn_percent == 100 emits nothing.
    """
    findings: list[dict] = []
    real = _bom_real_components(components)
    if not real:
        return findings

    # Group by BOM line (value + footprint).  A BOM line has coverage if any
    # instance carries an MPN — the user can propagate it to siblings.
    # Counting references instead inflates the denominator: a single generic
    # 10 K resistor shared across 5 refs would register as 5 misses.
    bom_lines: dict[tuple, dict] = {}
    for c in real:
        key = (c.get("value", ""), c.get("footprint", ""))
        line = bom_lines.setdefault(key, {"refs": [], "has_mpn": False})
        r = c.get("reference", "")
        if r:
            line["refs"].append(r)
        if c.get("mpn"):
            line["has_mpn"] = True

    total = len(bom_lines)
    if total == 0:
        return findings
    missing_lines = [line for line in bom_lines.values()
                     if not line["has_mpn"]]
    # Collect refs from missing lines for the description, sorted naturally.
    missing = sorted({r for line in missing_lines for r in line["refs"]})
    covered = total - len(missing_lines)
    pct = covered / total * 100.0

    if pct >= 100.0:
        return findings
    if pct < 50.0:
        rid, sev = "SS-001", "error"
        headline = ("Sourcing blocker: BOM has <50% MPN coverage "
                    f"({covered}/{total} unique parts). Board is not pre-fab ready.")
    elif pct < 80.0:
        rid, sev = "SS-002", "warning"
        headline = (f"Sourcing gap: {covered}/{total} unique BOM lines have an MPN "
                    f"({pct:.0f}%). Populate before fab.")
    else:
        rid, sev = "SS-003", "info"
        headline = (f"Sourcing nearly complete: {covered}/{total} unique parts "
                    f"have MPNs ({pct:.0f}%). Fill in remaining lines.")

    findings.append({
        "detector": "audit_sourcing_gate",
        "rule_id": rid,
        "severity": sev,
        "confidence": "deterministic",
        "evidence_source": "bom",
        "category": "sourcing",
        "summary": headline,
        "description": (f"Sourcing audit: {covered} of {total} unique BOM "
                        f"lines (grouped by value + footprint) carry a "
                        f"manufacturer part number ({pct:.1f}%). Pre-fab "
                        f"readiness requires 100% coverage; production "
                        f"assembly requires all parts sourceable via one of "
                        f"the supported distributors."),
        "components": missing[:50],
        "nets": [],
        "pins": [],
        "mpn_coverage_percent": round(pct, 1),
        "missing_mpn_lines": len(missing_lines),
        "missing_mpn_refs": len(missing),
        "total_bom_lines": total,
        "recommendation": (
            "Populate the MPN field on the listed refs (use the digikey / "
            "mouser / lcsc / element14 skill to search by value/footprint "
            "when the MPN isn't already known)."),
        "report_context": {
            "section": "Sourcing",
            "impact": ("Pre-fab gate: board cannot be ordered until MPN "
                       "coverage reaches 100%."),
            "standard_ref": "",
        },
    })
    return findings


def audit_dnp_rate(components: list[dict]) -> list[dict]:
    """Emit BL-001 when DNP coverage is high enough to make the BOM
    effectively empty.

    The SS-001..003 sourcing rules filter to non-DNP components first, so
    a 100%-DNP BOM passes them silently — but a reviewer skimming "no
    SS-* findings" might miss that no parts will actually be placed by
    assembly. BL-001 surfaces that explicitly.

    Tiers:
      ≥90% DNP  →  severity=error    ("assembly cannot place this BOM")
      ≥50% DNP  →  severity=warning  ("most parts marked DNP — confirm")
      <50% DNP  →  no finding (DNP-by-variant is a normal pattern)

    A single-component schematic doesn't fire — BL-001's value is on full
    assemblies, not on one-component drafts.
    """
    real = [c for c in components
            if c.get("type") not in NON_COMPONENT_TYPES
            and c.get("in_bom")]
    if len(real) < 2:
        return []
    dnp_count = sum(1 for c in real if c.get("dnp"))
    total = len(real)
    pct = dnp_count / total * 100.0
    if pct < 50.0:
        return []
    if pct >= 90.0:
        sev = "error"
        headline = (
            f"BOM is effectively empty: {dnp_count}/{total} ({pct:.0f}%) "
            "components are marked DNP — no parts will be placed by assembly."
        )
        impact = ("Pre-fab gate: the BOM as-is cannot be sent to an assembly "
                  "house. Confirm whether this is the intended stuffing variant.")
    else:
        sev = "warning"
        headline = (
            f"High DNP rate: {dnp_count}/{total} ({pct:.0f}%) components marked "
            "DNP. Confirm intended stuffing variant before fab."
        )
        impact = ("Most components are flagged DNP — likely a no-stuff variant "
                  "or an in-progress BOM. Confirm before assembly.")
    dnp_refs = sorted(c.get("reference", "") for c in real if c.get("dnp"))
    return [{
        "detector": "audit_dnp_rate",
        "rule_id": "BL-001",
        "severity": sev,
        "confidence": "deterministic",
        "evidence_source": "bom",
        "category": "sourcing",
        "summary": headline,
        "description": (
            f"Audited {total} non-fixture BOM components; {dnp_count} are "
            f"marked DNP ({pct:.1f}%). The DNP flag tells the assembly "
            "house to skip a component — at this rate the resulting board "
            "would be largely unpopulated."),
        "components": dnp_refs[:50],
        "nets": [],
        "pins": [],
        "dnp_rate_percent": round(pct, 1),
        "dnp_count": dnp_count,
        "total_components": total,
        "recommendation": (
            "If this BOM is for a no-stuff stuffing variant, suppress BL-001 "
            "via project config. Otherwise clear the DNP flag on components "
            "that should be assembled."),
        "report_context": {
            "section": "Sourcing",
            "impact": impact,
            "standard_ref": "",
        },
    }]


# Generic transistor symbol prefixes that encode assumed pin order
_GENERIC_TRANSISTOR_PREFIXES = ("Q_NPN_", "Q_PNP_", "Q_NMOS_", "Q_PMOS_")


# Map prefix to human-readable type
_GENERIC_TYPE_LABELS = {
    "Q_NPN_": "NPN",
    "Q_PNP_": "PNP",
    "Q_NMOS_": "NMOS",
    "Q_PMOS_": "PMOS",
}


# Map single-letter pin abbreviations to full names
_PIN_LETTER_NAMES = {
    "B": "Base", "C": "Collector", "E": "Emitter",
    "G": "Gate", "S": "Source", "D": "Drain",
}


def check_generic_transistor_symbols(components: list[dict],
                                     schematic_path: str = "") -> list[dict]:
    """Flag transistors using generic KiCad symbols instead of device-specific ones.

    Generic symbols (Q_NPN_BCE, Q_NMOS_GSD, etc.) encode an assumed pin order
    that may not match the actual part. SOT-23 pin mapping varies by manufacturer:
    BCE vs BEC vs CBE for BJTs, GSD vs GDS vs SGD for MOSFETs. Using a generic
    symbol with the wrong pin order produces a board that silently doesn't work.

    Device-specific symbols (MMBT3904, AO3400A) encode the correct pinout for
    that particular part and are always safer.

    If a datasheets/manifest.json (or legacy index.json) exists next to the schematic, the check also notes
    whether a datasheet is available for manual pinout verification.
    """
    warnings = []

    # Load datasheet manifest if available (prefer new manifest.json, fall
    # back to legacy index.json for projects that haven't been migrated).
    ds_index: dict[str, dict] = {}
    if schematic_path:
        sch_dir = Path(schematic_path).parent
        ds_dir = sch_dir / "datasheets"
        idx_path = ds_dir / "manifest.json"
        if not idx_path.is_file():
            idx_path = ds_dir / "index.json"
        if idx_path.is_file():
            try:
                ds_index = json.loads(idx_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass

    # Deduplicate by reference (multi-unit symbols)
    seen: set[str] = set()

    for c in components:
        if c["type"] != "transistor":
            continue
        ref = c["reference"]
        if ref in seen:
            continue
        seen.add(ref)

        lib_id = c.get("lib_id", "")
        # Extract symbol name (part after the colon)
        sym_name = lib_id.split(":")[-1] if ":" in lib_id else lib_id

        # Check if this is a generic transistor symbol
        matched_prefix = None
        for prefix in _GENERIC_TRANSISTOR_PREFIXES:
            if sym_name.startswith(prefix):
                matched_prefix = prefix
                break

        if matched_prefix is None:
            continue

        # Extract pin order suffix (e.g., "GSD" from "Q_NMOS_GSD")
        pin_suffix = sym_name[len(matched_prefix):]
        sym_type = _GENERIC_TYPE_LABELS.get(matched_prefix, "transistor")

        # Expand pin abbreviations for the message
        pin_names = "-".join(
            _PIN_LETTER_NAMES.get(ch, ch) for ch in pin_suffix
        ) if pin_suffix else pin_suffix

        mpn = c.get("mpn", "")
        value = c.get("value", "")
        footprint = c.get("footprint", "")
        fp_name = footprint.split(":")[-1] if ":" in footprint else footprint

        # Check datasheet availability by MPN
        has_datasheet = False
        if mpn and ds_index:
            # index.json keys may be MPN strings or nested under "components"
            if isinstance(ds_index, dict):
                if mpn in ds_index:
                    has_datasheet = True
                elif "components" in ds_index:
                    comps = ds_index["components"]
                    if isinstance(comps, dict) and mpn in comps:
                        has_datasheet = True
                    elif isinstance(comps, list):
                        has_datasheet = any(
                            e.get("mpn") == mpn for e in comps
                            if isinstance(e, dict)
                        )

        # Build human-readable part identifier
        part_id = mpn or value or "unknown part"

        # Build message
        if has_datasheet:
            action = f"Verify pinout against the {part_id} datasheet (available in datasheets/) or switch to a device-specific symbol."
        elif mpn:
            action = f"Verify pinout against the {part_id} datasheet or switch to a device-specific symbol."
        else:
            action = "Add an MPN and verify pinout against the datasheet, or switch to a device-specific symbol."

        msg = (
            f"{ref}: Generic {sym_type} symbol ({sym_name}) used"
            f"{' for ' + part_id if part_id != 'unknown part' else ''}"
            f"{' in ' + fp_name if fp_name else ''}."
            f" Pin order ({pin_names}) may not match the actual part."
            f" {action}"
        )

        warnings.append({
            "component": ref,
            "lib_id": lib_id,
            "value": value,
            "mpn": mpn,
            "footprint": footprint,
            "symbol_pin_order": pin_suffix,
            "symbol_type": sym_type,
            "has_datasheet": has_datasheet,
            "severity": "warning",
            "message": msg,
        })

    return warnings


def summarize_alternate_pins(lib_symbols: dict) -> list[dict]:
    """Summarize symbols that have alternate pin definitions (dual-function pins).

    Alternate pins are common on MCUs where GPIO pins can serve as SPI/I2C/UART/PWM
    peripherals. This summary helps understand the pin multiplexing capabilities.
    """
    results = []
    for name, sym in lib_symbols.items():
        alts = sym.get("alternates")
        if not alts:
            continue

        pin_summary = []
        for pin_num, alt_list in sorted(alts.items()):
            # Find the primary pin name
            primary_name = ""
            for p in sym["pins"]:
                if p["number"] == pin_num:
                    primary_name = p["name"]
                    break
            pin_summary.append({
                "pin": pin_num,
                "primary": primary_name,
                "alternates": [a["name"] for a in alt_list],
            })

        results.append({
            "symbol": name,
            "pins_with_alternates": len(alts),
            "total_pins": len(sym["pins"]),
            "details": pin_summary,
        })

    return results


def classify_ground_domains(nets: dict, components: list[dict]) -> dict:
    """Classify ground nets into domains: signal, analog, digital, earth, chassis, power.

    Multiple ground domains in a design need careful management — star grounding,
    proper domain separation, and single-point connections between domains.
    """
    ground_nets = {}
    for net_name, net_info in nets.items():
        if not _is_ground_name(net_name):
            continue

        nu = net_name.upper()
        if any(x in nu for x in ("AGND", "GNDA", "VSS_A", "VSSA")):
            domain = "analog"
        elif any(x in nu for x in ("DGND", "GNDD", "VSS_D", "VSSD")):
            domain = "digital"
        elif any(x in nu for x in ("PGND", "GNDPWR", "VSS_P")):
            domain = "power"
        elif any(x in nu for x in ("EARTH", "PE", "FG", "CHASSIS", "SHIELD")):
            domain = "earth/chassis"
        else:
            domain = "signal"

        pin_count = len([p for p in net_info["pins"] if not p["component"].startswith("#")])
        connected_components = sorted(set(
            p["component"] for p in net_info["pins"] if not p["component"].startswith("#")
        ))
        ground_nets[net_name] = {
            "domain": domain,
            "connections": pin_count,
            "components": connected_components,
        }

    domains = {}
    for net_name, info in ground_nets.items():
        d = info["domain"]
        domains.setdefault(d, []).append(net_name)

    result = {"ground_nets": ground_nets}
    if len(domains) > 1:
        result["multiple_domains"] = True
        result["domains"] = domains
        result["note"] = "Multiple ground domains detected — verify proper star/single-point connection between domains"
    else:
        result["multiple_domains"] = False
    return result


def analyze_bus_topology(bus_elements: dict, labels: list[dict], nets: dict) -> dict:
    """Analyze bus structure: which signals are grouped, naming consistency, member coverage.

    Checks that bus aliases have corresponding labels for all members, and that
    bus naming follows consistent patterns (e.g., D[0..7] has labels D0..D7).
    """
    result = {
        "bus_wire_count": len(bus_elements.get("bus_wires", [])),
        "bus_entry_count": len(bus_elements.get("bus_entries", [])),
        # GH #25 honesty invariant (spec §4): bus constructs the resolver
        # could not confidently resolve are surfaced, never silently dropped.
        "unresolved": sorted(
            ({"reason": u.get("reason", ""), "name": u.get("name")}
             for u in bus_elements.get("_unresolved", [])),
            key=lambda u: (u["reason"], u["name"] is None, u["name"] or ""),
        ),
    }

    aliases = bus_elements.get("bus_aliases", [])
    if aliases:
        alias_info = []
        all_label_names = set(l["name"] for l in labels)
        # KH-359: net keys may be sheet-qualified (/<sheet>/<name>) with the
        # bare name on display_name. Bus alias members are always bare
        # label names, so match against keys ∪ display_names.
        display_index = set(nets)
        for _v in nets.values():
            dn = _v.get("display_name")
            if dn:
                display_index.add(dn)
        for alias in aliases:
            members = alias["members"]
            present = [m for m in members if m in all_label_names]
            missing = [m for m in members if m not in all_label_names]
            # Check which member names resolve to actual nets
            resolved = [m for m in members if m in display_index]
            entry = {
                "name": alias["name"],
                "member_count": len(members),
                "present_labels": len(present),
                "resolved_nets": len(resolved),
            }
            if missing:
                entry["missing_labels"] = missing
            unresolved = [m for m in members if m not in display_index]
            if unresolved:
                entry["unresolved_members"] = unresolved
            alias_info.append(entry)
        result["aliases"] = alias_info

    # Detect bus-like label patterns (D0..D7, ADDR0..ADDR15, etc.)
    bus_patterns: dict[str, list[str]] = {}
    for lbl in labels:
        m = re.match(r'^([A-Za-z_]+)(\d+)$', lbl["name"])
        if m:
            prefix = m.group(1)
            bus_patterns.setdefault(prefix, []).append(lbl["name"])

    detected_buses = []
    for prefix, members in sorted(bus_patterns.items()):
        if len(members) >= 3:  # At least 3 signals to be bus-like
            nums = sorted(int(re.search(r'\d+$', m).group()) for m in members)
            expected = list(range(nums[0], nums[-1] + 1))
            missing_nums = [n for n in expected if n not in nums]
            entry = {
                "prefix": prefix,
                "width": len(members),
                "range": f"{prefix}{nums[0]}..{prefix}{nums[-1]}",
            }
            if missing_nums:
                entry["missing"] = [f"{prefix}{n}" for n in missing_nums]
            detected_buses.append(entry)

    if detected_buses:
        result["detected_bus_signals"] = detected_buses

    return result


def analyze_wire_geometry(wires: list[dict]) -> dict:
    """Analyze wire routing geometry for schematic cleanliness.

    Flags non-orthogonal wires (diagonal), very short wires (possible stubs),
    and computes overall wire statistics.
    """
    # EQ-064: L = √(Δx²+Δy²) (wire segment length)
    if not wires:
        return {"total_wires": 0}

    diagonal = []
    short_wires = []
    total_length = 0.0

    for w in wires:
        dx = abs(w["x2"] - w["x1"])
        dy = abs(w["y2"] - w["y1"])
        length = math.sqrt(dx * dx + dy * dy)
        total_length += length

        # Non-orthogonal: neither horizontal nor vertical (with tolerance)
        is_h = dy < 0.01
        is_v = dx < 0.01
        if not is_h and not is_v and length > 0.1:
            diagonal.append({
                "from": [round(w["x1"], 2), round(w["y1"], 2)],
                "to": [round(w["x2"], 2), round(w["y2"], 2)],
                "length": round(length, 2),
            })

        # Very short wires (< 1mm) — possible stubs or misclicks
        if 0 < length < 1.0:
            short_wires.append({
                "from": [round(w["x1"], 2), round(w["y1"], 2)],
                "to": [round(w["x2"], 2), round(w["y2"], 2)],
                "length": round(length, 3),
            })

    result = {
        "total_wires": len(wires),
        "total_length_mm": round(total_length, 1),
        "avg_length_mm": round(total_length / len(wires), 1) if wires else 0,
    }
    if diagonal:
        result["diagonal_wires"] = diagonal[:20]  # Cap output
        result["diagonal_count"] = len(diagonal)
    if short_wires:
        result["short_wires"] = short_wires[:20]
        result["short_wire_count"] = len(short_wires)
    return result


def check_simulation_readiness(components: list[dict], lib_symbols: dict) -> dict:
    """Check if components have SPICE simulation models assigned.

    KiCad's built-in NGSPICE simulator requires each component to have a
    simulation model (Sim.Type, Sim.Params, etc.) for the circuit to simulate.
    """
    real = [c for c in components
            if c["type"] not in NON_COMPONENT_TYPES]

    # Check for Sim_* properties which indicate SPICE model assignment
    # These are stored as component properties but we extracted only standard ones.
    # We can at least check lib_symbol descriptions for SPICE-related keywords.
    has_model_hint = []
    no_model = []

    for c in real:
        sym = lib_symbols.get(c["lib_id"], {})
        desc = (sym.get("description", "") + " " + sym.get("keywords", "")).lower()
        ctype = c["type"]

        # Passives (R, C, L) have built-in SPICE models
        if ctype in ("resistor", "capacitor", "inductor"):
            has_model_hint.append(c["reference"])
        elif "spice" in desc or "simulation" in desc or "sim_" in desc:
            has_model_hint.append(c["reference"])
        elif ctype in ("diode", "led", "transistor"):
            # Common discrete parts — may have models
            has_model_hint.append(c["reference"])
        else:
            no_model.append(c["reference"])

    total = len(real)
    modeled = len(has_model_hint)

    result = {
        "total_components": total,
        "likely_simulatable": modeled,
        "needs_model": len(no_model),
    }
    if no_model:
        result["components_without_model"] = sorted(set(no_model))[:30]
    if total > 0:
        result["simulatable_percent"] = round(modeled / total * 100, 1)
    return result


def audit_property_patterns(components: list[dict]) -> dict:
    """Audit property naming consistency across components.

    Checks that MPN, manufacturer, and distributor fields use consistent
    property names (e.g., not a mix of "MPN" vs "Mfg Part" vs "Part Number").
    Also checks for common data entry issues.
    """
    real = [c for c in components
            if c["type"] not in ("power_symbol", "power_flag", "flag")]

    issues = []

    # Check for value field anomalies
    for c in real:
        val = c.get("value", "")
        ref = c["reference"]

        # Reference designator accidentally used as value
        if val == ref:
            issues.append({
                "component": ref,
                "issue": "value_equals_reference",
                "message": f"{ref}: value is same as reference designator (likely placeholder)",
            })

        # Lib_id used as value (forgot to set value)
        if val and ":" in val and val == c.get("lib_id", ""):
            issues.append({
                "component": ref,
                "issue": "value_is_lib_id",
                "message": f"{ref}: value appears to be the library ID '{val}' (not a real value)",
            })

        # Footprint in the value field
        if val and ("_SMD:" in val or "_THT:" in val or "Resistor_SMD" in val):
            issues.append({
                "component": ref,
                "issue": "value_looks_like_footprint",
                "message": f"{ref}: value '{val}' looks like a footprint, not a component value",
            })

    # Check for MPN/value inconsistency within same BOM group
    # (same value + footprint should have same MPN)
    bom_groups: dict[tuple, list] = {}
    for c in real:
        if c["in_bom"] and not c["dnp"] and c.get("value"):
            key = (c["value"], c["footprint"])
            bom_groups.setdefault(key, []).append(c)

    for key, group in bom_groups.items():
        mpns = set(c["mpn"] for c in group if c["mpn"])
        if len(mpns) > 1:
            refs = sorted(c["reference"] for c in group)
            issues.append({
                "components": refs,
                "issue": "inconsistent_mpn",
                "message": f"Components with value '{key[0]}' / footprint '{key[1]}' have different MPNs: {sorted(mpns)}",
            })

    result = {}
    if issues:
        result["issues"] = issues
        result["issue_count"] = len(issues)
    return result


def spatial_clustering(components: list[dict]) -> dict:
    """Analyze component placement clustering to identify functional groups.

    Groups components by proximity to help identify subcircuit boundaries
    and check for spatial organization of the schematic.
    """
    real = [c for c in components
            if c["type"] not in ("power_symbol", "power_flag", "flag")]

    if not real:
        return {"clusters": []}

    # Simple grid-based clustering: divide the schematic into regions
    xs = [c["x"] for c in real]
    ys = [c["y"] for c in real]

    if not xs or not ys:
        return {"clusters": []}

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_range = x_max - x_min or 1
    y_range = y_max - y_min or 1

    # Use quadrant-based grouping (4x4 grid)
    grid_cols = min(4, max(1, int(x_range / 40)))
    grid_rows = min(4, max(1, int(y_range / 30)))

    cell_w = x_range / grid_cols if grid_cols > 1 else x_range + 1
    cell_h = y_range / grid_rows if grid_rows > 1 else y_range + 1

    grid: dict[tuple, list] = {}
    for c in real:
        col = min(int((c["x"] - x_min) / cell_w), grid_cols - 1)
        row = min(int((c["y"] - y_min) / cell_h), grid_rows - 1)
        grid.setdefault((row, col), []).append(c)

    clusters = []
    for (row, col), members in sorted(grid.items()):
        type_counts: dict[str, int] = {}
        for c in members:
            type_counts[c["type"]] = type_counts.get(c["type"], 0) + 1

        refs = sorted(c["reference"] for c in members)
        clusters.append({
            "region": f"row{row}_col{col}",
            "component_count": len(members),
            "types": type_counts,
            "references": refs if len(refs) <= 20 else refs[:20] + [f"... +{len(refs)-20} more"],
        })

    # Component density and spread statistics
    result = {
        "bounding_box": {
            "x_min": round(x_min, 1), "y_min": round(y_min, 1),
            "x_max": round(x_max, 1), "y_max": round(y_max, 1),
            "width_mm": round(x_range, 1), "height_mm": round(y_range, 1),
        },
        "clusters": clusters,
        "grid_size": f"{grid_rows}x{grid_cols}",
    }
    return result


def verify_pin_coverage(components: list[dict], lib_symbols: dict) -> list[dict]:
    """Verify that all non-NC library pins are accounted for on placed symbols.

    Checks if a placed symbol has fewer pins connected than the library definition
    expects, which could indicate missing connections or wrong unit placement.
    """
    warnings = []

    # Group components by reference (multi-unit symbols)
    ref_components: dict[str, list[dict]] = {}
    for c in components:
        if c["type"] in ("power_symbol", "power_flag", "flag"):
            continue
        ref_components.setdefault(c["reference"], []).append(c)

    for ref, comp_list in ref_components.items():
        c = comp_list[0]  # Use first instance for lib_id lookup
        sym_def = lib_symbols.get(c["lib_id"])
        if not sym_def:
            continue

        lib_pins = sym_def["pins"]
        if not lib_pins:
            continue

        # Count placed pins across all units
        placed_pin_nums = set()
        for comp in comp_list:
            for pin in comp.get("pins", []):
                placed_pin_nums.add(pin.get("number", ""))

        # Count expected pins from library (excluding no-connect type pins)
        expected_pins = set()
        for p in lib_pins:
            if p["type"] != "no_connect":
                expected_pins.add(p["number"])

        missing = expected_pins - placed_pin_nums
        if missing and len(missing) > len(expected_pins) * 0.3:
            # More than 30% of pins missing — likely a real issue
            warnings.append({
                "component": ref,
                "lib_id": c["lib_id"],
                "expected_pins": len(expected_pins),
                "placed_pins": len(placed_pin_nums),
                "missing_count": len(missing),
                "message": f"{ref}: {len(missing)}/{len(expected_pins)} library pins not placed (may need more units or check symbol)",
            })

    return warnings


def check_instance_consistency(components: list[dict]) -> list[dict]:
    """Check multi-unit and multi-instance symbol consistency.

    For multi-unit symbols (e.g., quad op-amp), verify all expected units are placed.
    For multi-instance sheets, verify reference numbering doesn't collide.
    """
    warnings = []

    # Group by lib_id to find multi-unit symbols
    lib_groups: dict[str, list[dict]] = {}
    for c in components:
        if c["type"] in ("power_symbol", "power_flag", "flag"):
            continue
        lib_groups.setdefault(c["lib_id"], []).append(c)

    # Check for partial unit placement
    for lib_id, comp_list in lib_groups.items():
        # Group by reference
        ref_units: dict[str, set[int]] = {}
        for c in comp_list:
            if c["unit"] is not None:
                ref_units.setdefault(c["reference"], set()).add(c["unit"])

        for ref, units in ref_units.items():
            if not units:
                continue
            max_unit = max(units)
            expected = set(range(1, max_unit + 1))
            missing = expected - units
            if missing:
                warnings.append({
                    "component": ref,
                    "lib_id": lib_id,
                    "placed_units": sorted(units),
                    "missing_units": sorted(missing),
                    "message": f"{ref}: units {sorted(missing)} not placed (of {max_unit} total)",
                })

    # Check for reference collisions across sheets
    ref_sheets: dict[str, set] = {}
    for c in components:
        if c["type"] in ("power_symbol", "power_flag", "flag"):
            continue
        sheet = c.get("_sheet", 0)
        ref_sheets.setdefault(c["reference"], set()).add(sheet)

    for ref, sheets in ref_sheets.items():
        if len(sheets) > 1:
            # Same reference on different sheets with different UUIDs
            instances = [c for c in components if c["reference"] == ref]
            uuids = set(c["uuid"] for c in instances)
            units = set(c["unit"] for c in instances if c["unit"] is not None)
            # Multi-unit on different sheets is OK (unit != None and different units)
            if len(uuids) > len(units) and len(units) > 0:
                pass  # Multi-unit, different units — fine
            elif len(uuids) > 1 and not units:
                warnings.append({
                    "component": ref,
                    "sheets": sorted(sheets),
                    "message": f"{ref}: appears on {len(sheets)} sheets with different UUIDs (reference collision?)",
                })

    return warnings


def validate_hierarchical_labels(labels: list[dict], nets: dict,
                                 bus_elements: dict | None = None) -> dict:
    """Validate hierarchical label usage for cross-sheet connectivity.

    Checks for orphaned hierarchical labels (no matching sheet pin), hierarchical
    labels that don't connect to any net, and naming consistency.
    """
    hier_labels = [l for l in labels if l["type"] == "hierarchical_label"]
    global_labels = [l for l in labels if l["type"] == "global_label"]

    result = {
        "hierarchical_label_count": len(hier_labels),
        "global_label_count": len(global_labels),
    }

    # Bus-name hierarchical labels are consumed by the bus pass (expanded to
    # members), so they legitimately never appear as a net under their own bus
    # name — In[0..7], {PHASES}, etc. Excluding them keeps this validation from
    # false-flagging every hierarchical bus as unconnected (GH #25).
    aliases = {a["name"]: a["members"]
               for a in (bus_elements or {}).get("bus_aliases", [])}

    def _is_bus_label(l: dict) -> bool:
        bare = l.get("_bare_name", l["name"])
        return expand_bus_name(bare, aliases) is not None

    # Check for hierarchical labels that don't appear in any net (bus labels
    # excluded — they resolve to member nets, not a net under their bus name).
    scalar_hier_names = set(l["name"] for l in hier_labels if not _is_bus_label(l))
    hier_names = set(l["name"] for l in hier_labels)
    global_names = set(l["name"] for l in global_labels)
    net_names = set(nets.keys())

    unconnected_hier = sorted(scalar_hier_names - net_names)
    if unconnected_hier:
        result["unconnected_hierarchical"] = unconnected_hier

    # Check for naming conflicts between global and hierarchical labels
    conflicts = sorted(hier_names & global_names)
    if conflicts:
        result["global_hier_name_conflicts"] = conflicts
        result["conflict_warning"] = "Same name used as both global and hierarchical label — may cause unexpected connections"

    # Group global labels by name and check for single-instance labels
    # (a global label used only once is suspicious — it should connect to something)
    global_name_counts: dict[str, int] = {}
    for l in global_labels:
        global_name_counts[l["name"]] = global_name_counts.get(l["name"], 0) + 1

    single_use = sorted(n for n, c in global_name_counts.items() if c == 1)
    if single_use:
        result["single_use_global_labels"] = single_use

    return result
