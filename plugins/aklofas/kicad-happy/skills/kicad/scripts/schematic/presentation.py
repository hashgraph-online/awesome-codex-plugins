"""Schematic result assembly: turns the parsed sheets, net map, BOM and
analyses into the analyzer output dict. Bodies are verbatim from analyze_schematic.py;
only the signatures and the input unpacking are new.
"""

from kicad_core.classify import NON_COMPONENT_TYPES
from kicad_core.values import parse_value
from kicad_core.project import (
    extract_pro_text_variables,
    load_lib_tables,
    load_kicad_pro,
)
from schematic.connectivity import _labels_for_output
from schematic.bom_stats import compute_statistics
from finding_schema import (
    compute_trust_summary,
    sort_findings,
    make_finding,
)


def assemble_result(ctx, parsed, nets, bom, analyses, *, path, sheets_parsed,
                    hierarchy_warning, format_newer_note, generator_version,
                    file_version) -> dict:
    """Build the schematic analyzer result dict (historical key order).

    MUTATES its inputs as the pre-v3 code did: components gain category /
    parsed_value / pin_nets (and lose _unit_pins), __unnamed_ nets may gain a
    display_name, the root title block may be filled from .kicad_pro text
    variables, usb_compliance loses its "findings" key, and every signal
    detection gains detector / detection_id.
    """
    all_components = parsed["components"]
    all_wires = parsed["wires"]
    all_labels = parsed["labels"]
    all_no_connects = parsed["no_connects"]
    all_text_annotations = parsed["text_annotations"]
    root_title_block = parsed["title_block"]
    power_symbols = parsed["power_symbols"]
    subcircuits = analyses.subcircuits
    ic_analysis = analyses.ic_analysis
    transistor_analysis = analyses.transistor_analysis
    connectivity_issues = analyses.connectivity_issues
    signal_analysis = analyses.signal_analysis
    design_analysis = analyses.design_analysis
    annotation_issues = analyses.annotation_issues
    label_shape_warnings = analyses.label_shape_warnings
    pwr_flag_warnings = analyses.pwr_flag_warnings
    fp_filter_warnings = analyses.fp_filter_warnings
    sourcing_audit = analyses.sourcing_audit
    datasheet_coverage_findings = analyses.datasheet_coverage_findings
    sourcing_gate_findings = analyses.sourcing_gate_findings
    dnp_rate_findings = analyses.dnp_rate_findings
    alternate_pins = analyses.alternate_pins
    ground_domains = analyses.ground_domains
    bus_topology = analyses.bus_topology
    wire_geometry = analyses.wire_geometry
    sim_readiness = analyses.sim_readiness
    property_issues = analyses.property_issues
    placement = analyses.placement
    pin_coverage = analyses.pin_coverage
    instance_issues = analyses.instance_issues
    hier_label_analysis = analyses.hier_label_analysis
    generic_sym_warnings = analyses.generic_sym_warnings
    pdn_analysis = analyses.pdn_analysis
    power_sequencing = analyses.power_sequencing
    sleep_current = analyses.sleep_current
    voltage_derating = analyses.voltage_derating
    power_budget = analyses.power_budget
    bom_optimization = analyses.bom_optimization
    test_coverage = analyses.test_coverage
    assembly_complexity = analyses.assembly_complexity
    usb_compliance = analyses.usb_compliance
    inrush_analysis = analyses.inrush_analysis
    protocol_compliance = analyses.protocol_compliance

    # Add parsed numeric values to all passive components and category field
    for comp in all_components:
        comp["category"] = comp.get("type")
        if comp["type"] in ("resistor", "capacitor", "inductor", "ferrite_bead", "crystal"):
            pv = parse_value(comp.get("value", ""), component_type=comp["type"])
            if pv is not None:
                comp["parsed_value"] = pv

    # Statistics
    stats = compute_statistics(all_components, nets, bom, all_wires, all_no_connects)

    # Annotate __unnamed_N nets with a human-readable display_name when
    # exactly one named IC pin is on them. Does NOT rename the net —
    # only adds a display hint consumers can use in reports.
    _IC_TYPES = {"ic", "regulator", "opamp", "microcontroller", "memory",
                 "connector_ic", "analog_ic", "mixed_signal",
                 "power_management", "interface"}
    _comp_by_ref = {c.get("reference"): c for c in all_components}
    for _net_name, _info in nets.items():
        if not _net_name.startswith("__unnamed_"):
            continue
        if _info.get("display_name"):
            continue
        _named_ic_pin = None
        for _p in _info.get("pins", []) or []:
            _pname = (_p.get("pin_name") or "").strip()
            if not _pname or _pname in ("~", "NC"):
                continue
            _ref = _p.get("component") or ""
            _comp = _comp_by_ref.get(_ref)
            if not _comp:
                continue
            _ctype = (_comp.get("type") or _comp.get("category") or "").lower()
            if _ctype not in _IC_TYPES:
                continue
            if _named_ic_pin is None:
                _named_ic_pin = (_ref, _pname)
            else:
                # Multiple named IC pins — ambiguous, skip annotation.
                _named_ic_pin = None
                break
        if _named_ic_pin:
            _info["display_name"] = f"{_named_ic_pin[0]}.{_named_ic_pin[1]}"

    # Load .kicad_pro for project metadata (KiCad 6+)
    pro = load_kicad_pro(str(path))
    project_settings = {}
    if pro:
        text_vars = extract_pro_text_variables(pro)
        if text_vars:
            project_settings['text_variables'] = text_vars
            # Enrich title block with text variables where empty
            if root_title_block:
                for tb_key, var_name in (('title', 'TITLE'),
                                          ('company', 'COMPANY'),
                                          ('revision', 'REVISION')):
                    if not root_title_block.get(tb_key) and var_name in text_vars:
                        root_title_block[tb_key] = text_vars[var_name]

    # Library tables
    lib_tables = load_lib_tables(str(path))
    if lib_tables.get('symbol_libs'):
        project_settings['symbol_libs'] = lib_tables['symbol_libs']

    # Enrich components with pin-to-net mapping for downstream consumers
    # KH-211: Include __unnamed_* nets so that connections through unlabelled
    # wires (common in hierarchical sub-sheets) appear in pin_nets.
    _pin_nets: dict[str, dict[str, str]] = {}
    for _net_name, _net_info in nets.items():
        if isinstance(_net_info, dict):
            for _p in _net_info.get('pins', []):
                _comp_ref = _p.get('component', '')
                _pin_num = _p.get('pin_number', '')
                if _comp_ref and _pin_num:
                    _pin_nets.setdefault(_comp_ref, {})[_pin_num] = _net_name
    for _comp in all_components:
        _all_pn = _pin_nets.get(_comp.get('reference', ''), {})
        _valid = _comp.get("_unit_pins")
        if _valid and len(_all_pn) > len(_valid):
            _comp['pin_nets'] = {k: v for k, v in _all_pn.items() if k in _valid}
        else:
            _comp['pin_nets'] = _all_pn
        _comp.pop("_unit_pins", None)

    # Flatten signal_analysis: all list values become findings, dict values promote to top level
    # KH-388: detect_voltage_dividers' feedback-network path deliberately
    # appends the SAME finding dict to both the `voltage_dividers` and
    # `feedback_networks` signal_analysis lists — see the 8c36212 cascade
    # warning in signal_detectors.py:324-346; that double-emission must
    # stay, it feeds detect_rc_filters' exclusion set. Dedup here instead
    # so the shared object doesn't also duplicate in the flattened
    # findings[] output. id()-based dedup is safe for ANY detector (a
    # dict appearing twice in the SAME analysis output is always the same
    # aliasing quirk noted in finding_schema.py's assign_finding_ids). The
    # (detector, components) key belt is scoped to detect_voltage_dividers
    # only — other detectors (e.g. VM-001) legitimately emit multiple
    # distinct findings for the same component pair on different nets, so
    # a components-only key would wrongly collapse those. Order-preserving
    # (first occurrence wins).
    findings = []
    _flatten_seen_ids = set()
    _flatten_seen_vd_keys = set()
    for _sa_key, _sa_value in signal_analysis.items():
        if isinstance(_sa_value, list):
            _det_name = f"detect_{_sa_key}"
            for _item in _sa_value:
                if isinstance(_item, dict) and "detector" not in _item:
                    _item["detector"] = _det_name
            for _item in _sa_value:
                if isinstance(_item, dict):
                    _iid = id(_item)
                    if _iid in _flatten_seen_ids:
                        continue
                    _flatten_seen_ids.add(_iid)
                    if _item.get("detector") == "detect_voltage_dividers":
                        _vkey = (_item.get("detector"), tuple(_item.get("components") or []))
                        if _vkey in _flatten_seen_vd_keys:
                            continue
                        _flatten_seen_vd_keys.add(_vkey)
                findings.append(_item)

    # Datasheet-coverage audit findings (DS-001 / DS-002 / DS-003) surface
    # up front so reviewers can't miss the "this is a consistency-only
    # check" banner when no manufacturer evidence is available.
    if datasheet_coverage_findings:
        findings.extend(datasheet_coverage_findings)

    if sourcing_gate_findings:
        findings.extend(sourcing_gate_findings)

    if dnp_rate_findings:
        findings.extend(dnp_rate_findings)

    # NT-001 — single-pin nets weighted by pin type (Task 3)
    nt_findings = connectivity_issues.get("single_pin_net_findings", [])
    if nt_findings:
        findings.extend(nt_findings)

    # VD-001..004 — component voltage/power derating (rich findings since v1.4)
    if voltage_derating:
        findings.extend(voltage_derating)

    # UC-001..004 — USB compliance check failures (KH-338)
    if usb_compliance:
        findings.extend(usb_compliance.pop("findings", []))

    if format_newer_note:
        findings.append(make_finding(
            detector="format_version_gate", rule_id="FV-001",
            category="file_format",
            summary=format_newer_note,
            description=format_newer_note,
            severity="info", confidence="deterministic",
            evidence_source="topology",
            schema_era="v3.0",
        ))

    # Build severity summary
    sev_counts = {"error": 0, "warning": 0, "info": 0}
    for _f in findings:
        _sev = _f.get("severity", "info").lower() if isinstance(_f, dict) else "info"
        if _sev in ("critical", "high"):
            sev_counts["error"] += 1
        elif _sev in ("medium", "warning"):
            sev_counts["warning"] += 1
        else:
            sev_counts["info"] += 1

    # Deterministic order so repeated runs produce byte-identical output
    # (KH-316).  Sort key: (rule_id, detector, first_component, first_net, summary).
    sort_findings(findings)

    result = {
        "analyzer_type": "schematic",
        "schema_version": "1.4.0",
        "summary": {"total_findings": len(findings), "by_severity": sev_counts},
        "trust_summary": compute_trust_summary(findings, bom=bom),
        "kicad_version": generator_version,
        "file_version": file_version,
        "title_block": root_title_block,
        "statistics": stats,
        "findings": findings,
        "assessments": [],
        "bom": bom,
        "components": [
            {k: v for k, v in c.items() if k != "pins"}
            for c in all_components
            if c["type"] not in ("power_symbol", "power_flag", "flag")
        ],
        "nets": nets,
        "subcircuits": subcircuits,
        "ic_pin_analysis": ic_analysis,
        "transistor_pin_analysis": transistor_analysis,
        "design_analysis": design_analysis,
        "connectivity_issues": connectivity_issues,
        "labels": _labels_for_output(all_labels),
        "no_connects": all_no_connects,
        "power_symbols": power_symbols,
        "annotation_issues": annotation_issues,
        "label_shape_warnings": label_shape_warnings,
        "pwr_flag_warnings": pwr_flag_warnings,
        "footprint_filter_warnings": fp_filter_warnings,
        "sourcing_audit": sourcing_audit,
        "ground_domains": ground_domains,
        "bus_topology": bus_topology,
        "wire_geometry": wire_geometry,
        "simulation_readiness": sim_readiness,
        "property_issues": property_issues,
        "placement_analysis": placement,
        "hierarchical_labels": hier_label_analysis,
    }

    # Promote dict values from signal_analysis to top level (rail_voltages, net_classifications, etc.)
    for _sa_key, _sa_value in signal_analysis.items():
        if isinstance(_sa_value, dict):
            result[_sa_key] = _sa_value

    # Only include non-empty optional sections
    if all_text_annotations:
        result["text_annotations"] = all_text_annotations
    if alternate_pins:
        result["alternate_pin_summary"] = alternate_pins
    if pin_coverage:
        result["pin_coverage_warnings"] = pin_coverage
    if instance_issues:
        result["instance_consistency_warnings"] = instance_issues
    if generic_sym_warnings:
        result["generic_symbol_warnings"] = generic_sym_warnings
    if pdn_analysis:
        result["pdn_impedance"] = pdn_analysis
    if sleep_current:
        result["sleep_current_audit"] = sleep_current
    if power_budget:
        result["power_budget"] = power_budget
    if power_sequencing:
        result["power_sequencing"] = power_sequencing
    if bom_optimization:
        result["bom_optimization"] = bom_optimization
    if test_coverage:
        result["test_coverage"] = test_coverage
    if assembly_complexity:
        result["assembly_complexity"] = assembly_complexity
    if usb_compliance:
        result["usb_compliance"] = usb_compliance
    if inrush_analysis:
        result["inrush_analysis"] = inrush_analysis
    if protocol_compliance:
        result["protocol_compliance"] = protocol_compliance

    if len(sheets_parsed) > 1:
        result["sheets"] = sheets_parsed
    if project_settings:
        result["project_settings"] = project_settings
    if hierarchy_warning:
        result["hierarchy_warning"] = hierarchy_warning

    # --- Missing information section ---
    # Aggregates data gaps so downstream consumers can separate
    # "missing data" from "actual design issues"
    missing_info = {}
    # Missing MPNs and footprints (from statistics)
    missing_mpn = stats.get("missing_mpn", [])
    if missing_mpn:
        missing_info["missing_mpn"] = missing_mpn
    missing_fp = stats.get("missing_footprint", [])
    if missing_fp:
        missing_info["missing_footprint"] = missing_fp
    # Components with MPN but no datasheet URL
    missing_ds = [c["reference"] for c in all_components
                  if c.get("mpn") and not c.get("datasheet")
                  and c["type"] not in ("power_symbol", "power_flag", "flag")]
    if missing_ds:
        missing_info["missing_datasheet"] = sorted(missing_ds)
    # Regulators with heuristic Vref (no datasheet lookup available)
    sig = signal_analysis or {}
    heuristic_vref = [r["ref"] for r in sig.get("power_regulators", [])
                      if r.get("vref_source") == "heuristic"]
    if heuristic_vref:
        missing_info["heuristic_vref"] = heuristic_vref
    if missing_info:
        result["missing_info"] = missing_info

    # BOM lock verification (production readiness)
    _bom_real = [c for c in all_components
                 if c.get("type") not in NON_COMPONENT_TYPES
                 and not c.get("reference", "").startswith("#")
                 and c.get("in_bom", True) and not c.get("dnp", False)]
    # Deduplicate multi-unit symbols
    _bom_seen = set()
    _bom_dedup = []
    for _bc in _bom_real:
        if _bc["reference"] not in _bom_seen:
            _bom_seen.add(_bc["reference"])
            _bom_dedup.append(_bc)
    _bom_real = _bom_dedup
    _bom_no_mpn = [c["reference"] for c in _bom_real if not c.get("mpn")]
    _bom_generic = [c["reference"] for c in _bom_real
                    if c.get("value", "") in ("", "~", "DNP", "DNF", "NC")
                    or c.get("value", "").startswith("?")]
    _bom_lock_pct = round((1 - len(_bom_no_mpn) / max(len(_bom_real), 1)) * 100)
    result["bom_lock"] = {
        "total_bom_components": len(_bom_real),
        "components_with_mpn": len(_bom_real) - len(_bom_no_mpn),
        "missing_mpn": _bom_no_mpn[:20],
        "missing_mpn_count": len(_bom_no_mpn),
        "generic_values": _bom_generic[:10],
        "lock_pct": _bom_lock_pct,
        "status": "pass" if _bom_lock_pct >= 95 else
                  "warning" if _bom_lock_pct >= 70 else "fail",
    }

    # Add stable detection IDs for diff matching
    from detection_schema import compute_detection_id as _compute_det_id
    for _det_type, _dets in signal_analysis.items():
        if isinstance(_dets, list):
            for _det in _dets:
                if isinstance(_det, dict):
                    _det["detection_id"] = _compute_det_id(_det, _det_type)

    return result


def assemble_legacy_result(*, nets, all_components, signal_analysis, real_components,
                           sheets_parsed, stats, bom, subcircuits, design_analysis,
                           all_labels, all_no_connects, power_symbols, annotation_issues,
                           legacy_resolution) -> dict:
    """Build the legacy (.sch) result dict; its key set stays distinct from the modern one.

    MUTATES components (pin_nets, _unit_pins) and signal detections
    (detection_id, detector) as the pre-v3 code did.
    """
    # Enrich components with pin-to-net mapping (legacy path)
    # KH-211: Include __unnamed_* nets so that connections through unlabelled
    # wires (common in hierarchical sub-sheets) appear in pin_nets.
    _pin_nets_l: dict[str, dict[str, str]] = {}
    for _net_name, _net_info in nets.items():
        if isinstance(_net_info, dict):
            for _p in _net_info.get('pins', []):
                _comp_ref = _p.get('component', '')
                _pin_num = _p.get('pin_number', '')
                if _comp_ref and _pin_num:
                    _pin_nets_l.setdefault(_comp_ref, {})[_pin_num] = _net_name
    for _comp in all_components:
        _all_pn = _pin_nets_l.get(_comp.get('reference', ''), {})
        _valid = _comp.get("_unit_pins")
        if _valid and len(_all_pn) > len(_valid):
            _comp['pin_nets'] = {k: v for k, v in _all_pn.items() if k in _valid}
        else:
            _comp['pin_nets'] = _all_pn
        _comp.pop("_unit_pins", None)

    # Add stable detection IDs for diff matching (legacy path)
    from detection_schema import compute_detection_id as _compute_det_id
    for _det_type, _dets in signal_analysis.items():
        if isinstance(_dets, list):
            for _det in _dets:
                if isinstance(_det, dict):
                    _det["detection_id"] = _compute_det_id(_det, _det_type)

    # Flatten signal_analysis: all list values become findings, dict values move to top level
    findings = []
    top_level_dicts = {}
    for key, value in signal_analysis.items():
        if isinstance(value, list):
            _det_name = f"detect_{key}"
            for _item in value:
                if isinstance(_item, dict) and "detector" not in _item:
                    _item["detector"] = _det_name
            findings.extend(value)
        elif isinstance(value, dict):
            # rail_voltages, net_classifications, etc. — promote to top level
            top_level_dicts[key] = value

    sev_counts = {"error": 0, "warning": 0, "info": 0}
    for f in findings:
        sev = f.get("severity", "info").lower() if isinstance(f, dict) else "info"
        if sev in ("critical", "high"):
            sev_counts["error"] += 1
        elif sev in ("medium", "warning"):
            sev_counts["warning"] += 1
        else:
            sev_counts["info"] += 1

    # Legacy analysis quality summary (KH-271)
    _pin_source_counts = {"parsed_lib": 0, "suffix_match": 0, "snapped_to_wire": 0, "unresolved": 0}
    for c in real_components:
        src = c.get("_pin_source", "unresolved")
        if src in _pin_source_counts:
            _pin_source_counts[src] += 1
        else:
            _pin_source_counts[src] = 1

    # Deterministic order for byte-identical repeated runs (KH-316).
    sort_findings(findings)

    result = {
        "analyzer_type": "schematic",
        "schema_version": "1.4.0",
        "summary": {"total_findings": len(findings), "by_severity": sev_counts},
        "trust_summary": compute_trust_summary(findings),
        "kicad_version": "5 (legacy)",
        "file_version": "4",
        "title_block": {},  # legacy .sch has no (title_block ...) node (TH-043)
        "sheets_parsed": len(sheets_parsed),
        "sheet_files": sheets_parsed,
        "statistics": stats,
        "bom": bom,
        "components": real_components,
        "nets": nets,
        "subcircuits": subcircuits,
        "findings": findings,
        "assessments": [],
        "design_analysis": design_analysis,
        "labels": _labels_for_output(all_labels),
        "no_connects": all_no_connects,
        "power_symbols": power_symbols,
        "annotation_issues": annotation_issues,
        "legacy_analysis_quality": {
            "is_legacy_schematic": True,
            "library_resolution": legacy_resolution,
            "pin_source_coverage": _pin_source_counts,
        },
    }
    # Promote dict values from signal_analysis to top level (rail_voltages, etc.)
    result.update(top_level_dicts)
    return result
