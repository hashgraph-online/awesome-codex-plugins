# AI Design Slop Cleanup Result

## Processing summary

- Target: `<path or surface>`
- Mode: `design | restyle | mockup | audit | clean | verify`
- Design brief: `.hyper/design/<slug>/brief.md | not applicable`
- Detector: `v2 | unavailable (reason)`
- Engines run: `text | css | markup | context | dom | visual`
- Baseline delta: `not used | only-new | unavailable (reason)`
- Generic-output risk: `low | medium | high | unassessed`
- Render verification: `complete | static_only | unavailable`
- Edit passes: `0 | 1 | 2 | 3`
- Craft-floor check: `pass | fail (items) | static_only`
- Independent review: `subagent | self (degraded) | user | not run (reason)`
- Delivery gate: `pass | fail (lines) | not run (reason)`
- Final status: `pass | review_required | blocked`

## WCAG 2.2

| Criterion | Result | Reason | Evidence |
|---|---|---|---|
| 1.4.3 Contrast (Minimum) | `PASS / FAIL / N/A` | reason | evidence |
| 1.4.11 Non-text Contrast | `PASS / FAIL / N/A` | reason | evidence |
| 2.4.7 Focus Visible | `PASS / FAIL / N/A` | reason | evidence |
| 2.4.11 Focus Not Obscured (Minimum) | `PASS / FAIL / N/A` | reason | evidence |
| 2.5.8 Target Size (Minimum) | `PASS / FAIL / N/A` | reason | evidence |
| 2.1.1 Keyboard | `PASS / FAIL / N/A` | reason | evidence |
| 2.1.2 No Keyboard Trap | `PASS / FAIL / N/A` | reason | evidence |
| 1.4.10 Reflow | `PASS / FAIL / N/A` | reason | evidence |
| 1.4.12 Text Spacing | `PASS / FAIL / N/A` | reason | evidence |
| 2.5.7 Dragging Movements | `PASS / FAIL / N/A` | reason | evidence |
| 3.3.8 Accessible Authentication (Minimum) | `PASS / FAIL / N/A` | reason | evidence |
| 3.2.6 Consistent Help | `PASS / FAIL / N/A` | reason | evidence |
| 3.3.7 Redundant Entry | `PASS / FAIL / N/A` | reason | evidence |

## Brief inference

- Page type:
- Visitor mode:
- Audience:
- Primary task:
- Identity to preserve:
- Required data/state/cardinality:
- Scope for this run:
- Unknowns:

## Findings

| # | ID | Class | Severity | Detection / remediation confidence | Engine / evidence | Exception | Action | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | `rule.id` | `default-risk` | `P2` | `high / low` | `text / static-source` at `file:line` | `not-checked` | `review` | `open` |

## Applied changes

- Files:
- Change:
- Preserved contracts:
- Candidate or persisted waivers: `없음 | rule, narrow scope, reason, source`

## Verification

- Detector/baseline:
- Build/typecheck/lint/test:
- Rendered evidence: viewport/state/locator facts, or `static_only` / `unavailable` reason
- Desktop/mobile render:
- Accessibility:
- Reduced motion:
- Behavior regression:
- Report validator:

| Gate line | Result | Evidence |
|---|---|---|
| H1 to H11, craft floor, P1 to P13, L1 to L7 | `PASS / FAIL / n/a / not run` | file:line, command output, capture, or click-through |

## Residual risk

- Unrendered items:
- Review-only/context-dependent findings:
- User decisions:
- Evidence boundaries: screenshots do not prove keyboard, semantics, accessibility, or end-to-end behavior.
- Other caveats:
