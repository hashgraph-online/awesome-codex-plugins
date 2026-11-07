"""Risk scoring and the top-risk summary for kicad-happy.

Scores findings from any analyzer into the respin, bring-up and
manufacturing risk buckets and picks the top few per bucket.

Zero external dependencies - stdlib only.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

# standalone load by file path (harness spec_from_file_location, docs)
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))
from kicad_core.render import normalize_severity


SEVERITY_WEIGHTS = {'error': 15, 'warning': 3, 'info': 0}

CONFIDENCE_WEIGHTS = {
    'deterministic': 1.0,
    'datasheet-backed': 0.9,
    'heuristic': 0.7,
}

# Category → risk bucket(s) with boost multiplier
RESPIN_CATEGORIES = {
    'ground_plane', 'stackup', 'diff_pair', 'board_edge',
    'pdn', 'via_stitching', 'return_path',
}
BRINGUP_CATEGORIES = {
    'thermal_safety', 'switching_emc', 'pdn', 'esd_path',
}
MANUFACTURING_CATEGORIES = {
    'dfm_violation', 'tombstoning', 'documentation', 'thermal_pad_vias',
}

BUCKET_BOOSTS = {
    'respin': 1.5,
    'bringup': 1.3,
    'manufacturing': 1.2,
}


def compute_finding_risk(finding: Dict[str, Any], bucket: str) -> float:
    """Compute risk score for a single finding in a specific bucket."""
    sev = SEVERITY_WEIGHTS.get(normalize_severity(finding.get('severity')), 0)
    conf_name = finding.get('confidence')
    conf = CONFIDENCE_WEIGHTS.get(conf_name, 0.7) if isinstance(conf_name, str) else 0.7
    boost = BUCKET_BOOSTS.get(bucket, 1.0)
    return sev * conf * boost


def classify_finding_buckets(finding: Dict[str, Any]) -> List[str]:
    """Return which risk buckets a finding belongs to."""
    cat = finding.get('category', '')
    buckets = []
    if cat in RESPIN_CATEGORIES:
        buckets.append('respin')
    if cat in BRINGUP_CATEGORIES:
        buckets.append('bringup')
    if cat in MANUFACTURING_CATEGORIES:
        buckets.append('manufacturing')
    return buckets


def compute_top_risks(all_findings: List[Dict[str, Any]],
                      top_n: int = 3,
                      ) -> Dict[str, List[Dict[str, Any]]]:
    """Compute top-N findings per risk bucket across all analyzers.

    Each finding in *all_findings* should have: severity, confidence,
    category, rule_id, title, source (analyzer name).

    Returns::

        {
            "respin": [top 3 findings],
            "bringup": [top 3 findings],
            "manufacturing": [top 3 findings],
        }

    Only includes active (non-suppressed) findings.
    """
    buckets: Dict[str, List[tuple]] = {
        'respin': [], 'bringup': [], 'manufacturing': [],
    }

    for f in all_findings:
        if f.get('suppressed'):
            continue
        for bucket in classify_finding_buckets(f):
            score = compute_finding_risk(f, bucket)
            if score > 0:
                buckets[bucket].append((score, f))

    result: Dict[str, List[Dict[str, Any]]] = {}
    for bucket, scored in buckets.items():
        scored.sort(key=lambda x: x[0], reverse=True)
        result[bucket] = [f for _, f in scored[:top_n]]

    return result
