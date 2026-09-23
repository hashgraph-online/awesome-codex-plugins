"""output_filters.py — Stage and audience filtering for all analyzers.

Provides:
    STAGES              — canonical stage tuple
    assign_stages()     — add 'stages' list field to each finding
    apply_stage_filter()— mark in_active_stage boolean on each finding
    build_audience_summary() — compute designer/reviewer/manager summaries
    format_text()       — render human-readable text output
    apply_output_filters()   — one-call integration helper

Python 3.8+ stdlib only.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Stage definitions
# ---------------------------------------------------------------------------

STAGES = ('schematic', 'layout', 'pre_fab', 'bring_up')

# Each entry is a list of rule_id *prefixes* (checked with str.startswith).
# A finding matches a stage if its rule_id starts with any prefix in that
# stage's list.  Prefixes that end with a digit (e.g. "PS-001") are exact
# prefix-matches so they don't accidentally match "PS-002".
_STAGE_RULES: Dict[str, List[str]] = {
    'schematic': [
        'PU-', 'VM-', 'PR-', 'PS-001',
        'LR-', 'FS-', 'IA-',
        # *-DET rules (schematic-level detectors)
        'VD-DET', 'RC-DET', 'LC-DET', 'XL-DET', 'OA-DET', 'TR-DET',
        'BR-DET', 'LD-DET', 'PR-DET', 'IL-DET', 'DC-DET', 'CS-DET',
        'PD-DET', 'DO-DET', 'BZ-DET', 'KM-DET', 'IB-DET', 'ET-DET',
        'HD-DET', 'LV-DET', 'MI-DET', 'RF-DET', 'RM-DET', 'BM-DET',
        'BC-DET', 'MD-DET', 'AL-DET', 'DI-DET', 'PP-DET', 'AD-DET',
        'RS-DET', 'CD-DET', 'DP-DET', 'SI-DET', 'LS-DET', 'AU-DET',
        'LI-DET', 'RT-DET', 'TC-DET',
        # *-AUD rules
        'EP-AUD', 'LA-AUD', 'CG-AUD',
        # WL, TF, SC, AH, PL
        'WL-', 'TF-', 'SC-', 'AH-', 'PL-',
        # LC / LT lifecycle
        'LC-', 'LT-',
        'NT-001',
        'RS-001', 'RS-002',
        'LB-001',
        'PP-001',
        'SP-001',
    ],
    'layout': [
        'NR-', 'RP-', 'TW-', 'PS-002',
        'VS-', 'DP-', 'GP-', 'DC-', 'SW-', 'CK-', 'BE-', 'XT-',
        'ML-', 'SH-', 'TH-',
        'DFM-001', 'DFM-002',
        'PM-001', 'PM-002',
        'TB-001',
        'TS-DET', 'TP-DET', 'CC-DET', 'CC-002',
        'TV-001', 'CP-001', 'CP-002', 'CP-003',
        'SK-001', 'VP-001', 'BV-001', 'KO-001', 'OR-001',
        'TS-001', 'TS-002', 'TS-003', 'TS-004', 'TS-005',
        'TP-001', 'TP-002',
        'TH-DET',
    ],
    'pre_fab': [
        'XV-', 'CC-', 'EG-', 'DA-', 'IO-', 'EF-', 'ES-',
        'RT-001', 'FD-001', 'TE-001',
        'GR-001', 'GR-002', 'GR-003', 'GR-004', 'GR-005',
        'SS-001', 'SS-002', 'SS-003',
    ],
    'bring_up': [
        'WL-', 'TF-', 'SC-', 'AH-', 'PL-',
        'DI-DET', 'RS-DET',
    ],
}

# ---------------------------------------------------------------------------
# Severity normalization
# ---------------------------------------------------------------------------

def _severity_bucket(severity: str) -> str:
    """Normalize a finding severity string to error/warning/info bucket."""
    s = (severity or '').upper()
    if s in ('CRITICAL', 'HIGH', 'ERROR'):
        return 'error'
    if s in ('MEDIUM', 'WARNING', 'WARN'):
        return 'warning'
    return 'info'


# ---------------------------------------------------------------------------
# Stage assignment
# ---------------------------------------------------------------------------

def assign_stages(findings: List[Dict[str, Any]]) -> None:
    """Add a ``stages`` list field to each finding based on rule_id prefix.

    Mutates findings in place.  A finding may belong to multiple stages.
    Defaults to ``['schematic']`` if no rule prefix matches.
    """
    for f in findings:
        rule_id: str = f.get('rule_id', '') or ''
        matched: List[str] = []
        for stage, prefixes in _STAGE_RULES.items():
            for prefix in prefixes:
                if rule_id.startswith(prefix):
                    if stage not in matched:
                        matched.append(stage)
                    break  # next stage
        f['stages'] = matched if matched else ['schematic']


# ---------------------------------------------------------------------------
# Stage filter application
# ---------------------------------------------------------------------------

def apply_stage_filter(findings: List[Dict[str, Any]], stage: str) -> Dict[str, Any]:
    """Mark ``in_active_stage`` boolean on each finding.

    Returns the stage_filter summary dict:
        {"active_stage": str, "included_count": int, "excluded_count": int}
    """
    if stage not in STAGES:
        raise ValueError(f"Unknown stage {stage!r}; must be one of {STAGES}")

    included = 0
    excluded = 0
    for f in findings:
        stages = f.get('stages', ['schematic'])
        active = stage in stages
        f['in_active_stage'] = active
        if active:
            included += 1
        else:
            excluded += 1

    return {
        'active_stage': stage,
        'included_count': included,
        'excluded_count': excluded,
    }


# ---------------------------------------------------------------------------
# Audience summary construction
# ---------------------------------------------------------------------------

def build_audience_summary(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute designer / reviewer / manager summaries from findings list.

    All three views are always computed and returned together under their
    respective keys.
    """
    # ------------------------------------------------------------------
    # Pre-compute buckets
    # ------------------------------------------------------------------
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    infos: List[Dict[str, Any]] = []
    by_category: Dict[str, int] = defaultdict(int)
    by_category_err_warn: Dict[str, int] = defaultdict(int)

    for f in findings:
        bucket = _severity_bucket(f.get('severity', ''))
        cat = f.get('category', 'uncategorized') or 'uncategorized'
        by_category[cat] += 1
        if bucket == 'error':
            errors.append(f)
            by_category_err_warn[cat] += 1
        elif bucket == 'warning':
            warnings.append(f)
            by_category_err_warn[cat] += 1
        else:
            infos.append(f)

    top_issues_full = (errors + warnings)[:10]
    top_issues_reviewer = [
        {
            'rule_id': f.get('rule_id', ''),
            'severity': f.get('severity', ''),
            'summary': f.get('summary', f.get('message', '')),
            'recommendation': f.get('recommendation', f.get('fix', '')),
            'category': f.get('category', 'uncategorized'),
        }
        for f in errors + warnings
    ]

    # ------------------------------------------------------------------
    # Stage readiness
    # ------------------------------------------------------------------
    stage_readiness: Dict[str, str] = {}
    for stage in STAGES:
        stage_errors = sum(
            1 for f in findings
            if stage in f.get('stages', ['schematic'])
            and _severity_bucket(f.get('severity', '')) == 'error'
        )
        stage_warnings = sum(
            1 for f in findings
            if stage in f.get('stages', ['schematic'])
            and _severity_bucket(f.get('severity', '')) == 'warning'
        )
        if stage_errors > 0:
            stage_readiness[stage] = 'needs_work'
        elif stage_warnings > 0:
            stage_readiness[stage] = 'needs_review'
        else:
            stage_readiness[stage] = 'pass'

    # Manager one-liner
    blocker_count = len(errors)
    warning_count = len(warnings)
    cat_count = len([c for c in by_category_err_warn if by_category_err_warn[c] > 0])
    blocked_stages = [s for s in STAGES if stage_readiness[s] == 'needs_work']

    if blocker_count == 0 and warning_count == 0:
        one_liner = 'No errors or warnings — all stages ready.'
    else:
        parts = []
        if blocker_count:
            parts.append(f'{blocker_count} error{"s" if blocker_count != 1 else ""}')
        if warning_count:
            parts.append(f'{warning_count} warning{"s" if warning_count != 1 else ""}')
        summary_str = ', '.join(parts)
        cat_str = f'across {cat_count} categor{"ies" if cat_count != 1 else "y"}' if cat_count else ''
        blocker_str = ''
        if blocked_stages:
            stage_names = ', '.join(s.replace('_', '-') for s in blocked_stages)
            blocker_str = f' {stage_names.capitalize()} stage{"s" if len(blocked_stages) != 1 else ""} {"have" if len(blocked_stages) != 1 else "has"} blockers.'
        one_liner = f'{summary_str}{" " + cat_str if cat_str else ""}.{blocker_str}'

    # ------------------------------------------------------------------
    # Risk level
    # ------------------------------------------------------------------
    if blocker_count >= 5:
        risk_level = 'high'
    elif blocker_count >= 1:
        risk_level = 'moderate'
    elif warning_count >= 10:
        risk_level = 'moderate'
    elif warning_count >= 1:
        risk_level = 'low'
    else:
        risk_level = 'none'

    # ------------------------------------------------------------------
    # Assemble
    # ------------------------------------------------------------------
    return {
        'designer': {
            'total_findings': len(findings),
            'by_severity': {
                'error': len(errors),
                'warning': len(warnings),
                'info': len(infos),
            },
            'by_category': dict(by_category),
            'top_issues': top_issues_full,
        },
        'reviewer': {
            'total_findings': len(errors) + len(warnings),
            'by_category': dict(by_category_err_warn),
            'top_issues': top_issues_reviewer,
        },
        'manager': {
            'risk_level': risk_level,
            'blocker_count': blocker_count,
            'warning_count': warning_count,
            'stage_readiness': stage_readiness,
            'one_liner': one_liner,
        },
    }


# ---------------------------------------------------------------------------
# Text formatting
# ---------------------------------------------------------------------------

def _group_by_category(findings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for f in findings:
        cat = f.get('category', 'uncategorized') or 'uncategorized'
        groups[cat].append(f)
    return dict(groups)


def _format_finding_designer(f: Dict[str, Any], idx: int) -> str:
    """Full detail for designer audience."""
    lines = []
    rule_id = f.get('rule_id', '')
    severity = f.get('severity', 'INFO').upper()
    summary = f.get('summary', f.get('message', '(no summary)'))
    lines.append(f'  [{idx}] {severity} {rule_id}: {summary}')

    detail = f.get('detail', f.get('description', ''))
    if detail:
        lines.append(f'      Detail: {detail}')

    recommendation = f.get('recommendation', f.get('fix', ''))
    if recommendation:
        lines.append(f'      Fix:    {recommendation}')

    component = f.get('component', f.get('ref', ''))
    if component:
        lines.append(f'      Component: {component}')

    stages = f.get('stages', [])
    if stages:
        lines.append(f'      Stages: {", ".join(stages)}')

    return '\n'.join(lines)


def _format_finding_reviewer(f: Dict[str, Any], idx: int) -> str:
    """Summary + recommendation only for reviewer audience."""
    rule_id = f.get('rule_id', '')
    severity = f.get('severity', 'INFO').upper()
    summary = f.get('summary', f.get('message', '(no summary)'))
    recommendation = f.get('recommendation', f.get('fix', ''))
    line = f'  [{idx}] {severity} {rule_id}: {summary}'
    if recommendation:
        line += f'\n      Rec: {recommendation}'
    return line


def _readiness_char(status: str) -> str:
    return {'pass': 'PASS', 'needs_review': 'REVIEW', 'needs_work': 'WORK'}.get(status, status.upper())


def format_text(
    findings: List[Dict[str, Any]],
    audience: str,
    stage: Optional[str] = None,
) -> str:
    """Render human-readable text output for --text mode.

    audience: 'designer' | 'reviewer' | 'manager'
    stage:    optional active stage name (used to filter text output)
    """
    audience = (audience or 'designer').lower()

    # When a stage is active, only show findings marked in_active_stage=True
    active_findings = [
        f for f in findings
        if f.get('in_active_stage', True)  # default True when no stage filter applied
    ]

    # ------------------------------------------------------------------
    # Manager view
    # ------------------------------------------------------------------
    if audience == 'manager':
        summary = build_audience_summary(active_findings)
        mgr = summary['manager']
        lines = [
            '=== Manager Summary ===',
            '',
            mgr['one_liner'],
            '',
            f'Risk level:    {mgr["risk_level"].upper()}',
            f'Blockers:      {mgr["blocker_count"]}',
            f'Warnings:      {mgr["warning_count"]}',
            '',
            'Stage Readiness:',
        ]
        readiness = mgr['stage_readiness']
        for s in STAGES:
            status = readiness.get(s, 'pass')
            lines.append(f'  {s:<12} {_readiness_char(status)}')

        # Blocker list
        blockers = [f for f in active_findings if _severity_bucket(f.get('severity', '')) == 'error']
        if blockers:
            lines += ['', 'Blockers:']
            for f in blockers:
                rule_id = f.get('rule_id', '')
                summary_txt = f.get('summary', f.get('message', ''))
                lines.append(f'  - {rule_id}: {summary_txt}')

        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Reviewer view
    # ------------------------------------------------------------------
    if audience == 'reviewer':
        # Errors and warnings only
        visible = [
            f for f in active_findings
            if _severity_bucket(f.get('severity', '')) in ('error', 'warning')
        ]
        if not visible:
            header = '=== Review Summary ==='
            suffix = ''
            if stage:
                suffix = f' (stage: {stage})'
            return f'{header}\nNo errors or warnings found{suffix}.'

        groups = _group_by_category(visible)
        stage_label = f' [stage: {stage}]' if stage else ''
        lines = [f'=== Review Summary{stage_label} ===', '']
        idx = 1
        for cat in sorted(groups):
            lines.append(f'--- {cat} ---')
            for f in groups[cat]:
                lines.append(_format_finding_reviewer(f, idx))
                idx += 1
            lines.append('')

        total = len(visible)
        err_count = sum(1 for f in visible if _severity_bucket(f.get('severity', '')) == 'error')
        warn_count = total - err_count
        lines.append(f'Total: {total} ({err_count} error{"s" if err_count != 1 else ""}, {warn_count} warning{"s" if warn_count != 1 else ""})')
        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Designer view (default)
    # ------------------------------------------------------------------
    if not active_findings:
        stage_label = f' [stage: {stage}]' if stage else ''
        return f'=== Design Analysis{stage_label} ===\nNo findings.'

    groups = _group_by_category(active_findings)
    stage_label = f' [stage: {stage}]' if stage else ''
    lines = [f'=== Design Analysis{stage_label} ===', '']
    idx = 1
    for cat in sorted(groups):
        lines.append(f'--- {cat} ---')
        for f in groups[cat]:
            lines.append(_format_finding_designer(f, idx))
            idx += 1
        lines.append('')

    err_count = sum(1 for f in active_findings if _severity_bucket(f.get('severity', '')) == 'error')
    warn_count = sum(1 for f in active_findings if _severity_bucket(f.get('severity', '')) == 'warning')
    info_count = len(active_findings) - err_count - warn_count
    lines.append(
        f'Total: {len(active_findings)} ({err_count} error{"s" if err_count != 1 else ""}, '
        f'{warn_count} warning{"s" if warn_count != 1 else ""}, '
        f'{info_count} info)'
    )
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Integration helper
# ---------------------------------------------------------------------------

def apply_output_filters(
    result: Dict[str, Any],
    stage: Optional[str] = None,
    audience: Optional[str] = None,
) -> None:
    """Apply stage/audience filtering to a result dict.  Mutates in place.

    Accesses result["findings"] directly (harmonized format from Batch 9).
    Safe to call when findings list is empty or missing.
    """
    findings = result.get('findings', [])
    if not findings:
        return

    assign_stages(findings)

    if stage:
        result['stage_filter'] = apply_stage_filter(findings, stage)

    result['audience_summary'] = build_audience_summary(findings)
