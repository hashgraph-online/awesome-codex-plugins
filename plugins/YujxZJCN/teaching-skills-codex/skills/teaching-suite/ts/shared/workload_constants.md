# Workload & threshold constants

Single source of truth for the numeric constants used by the Alignment Gate's workload
and assessment-structure checks. `ts/scripts/check_alignment_gate.py` imports these via its
module constants; `ts/shared/alignment_gate_protocol.md` and
`ts/assessment-architect/templates/test_blueprint_template.md` cite this file rather than
restating the numbers, so there is one place to adjust them.

These are evidence-informed defaults, not law — a professor's discipline norms or an
institution's credit-hour policy override them. When overridden, record the change in
`workload_audit.constants_used`.

## Workload estimation (D1 / D2)

| Constant | Default | Source / rationale |
|----------|---------|--------------------|
| Out-of-class hours per contact hour | 2.0 | US credit-hour convention; adjust per `institution_constraints` |
| Workload tolerance band (D2) | ±25% | flag only outside this around the credit-hour target |
| Reading rate (dense technical) | ~100 wpm | Rice course-workload-estimator range (67–500 wpm by density/purpose) |
| Problem-set multiplier (novice) | ×3 | professor's own solve-time × 3 for novices |
| Writing | 0.5–5 hrs/page | by genre; reflective < analytical < research |

## Assessment-structure thresholds (C2 / C3 / D3)

| Constant | Default | Check |
|----------|---------|-------|
| Single-assessment weight cap | 40% | C2 — flag any one assessment above this |
| Low-stakes ceiling | ≤10% | C3 — counts as low-stakes for early-calibration |
| High-stakes floor | ≥20% | C3 — a low-stakes item should precede the first of these |
| Major-deliverable floor | ≥15% | D3 — two of these due the same week is a collision |

## Outcome-count guidance (B4)

3–8 outcomes typical; >12 flagged (usually topics restated as outcomes).
