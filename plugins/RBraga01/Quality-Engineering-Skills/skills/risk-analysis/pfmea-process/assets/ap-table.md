---
name: ap-table
type: asset
parent_skill: pfmea-process
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-01"
last_updated: "2026-06-03"
updated_by: RBraga01
reviewed_by: RBraga01
license: MIT
license-note: >-
  MIT covers the original expression in this file. It does not extend to the
  AIAG-VDA FMEA Handbook, which is a separately licensed third-party work.
  See THIRD_PARTY_CONTENT.md.
---

# Action Priority (AP) Determination Rules

**What this file is.** An independent restatement of the Action Priority decision
logic used in the AIAG-VDA FMEA methodology (2019 joint edition), expressed as
banded rules. It is **not** a reproduction of the handbook's Action Priority
table, and it does not replace it.

**What this file is not.** The authoritative AP table enumerates every S/O/D
combination and comes with the rating criteria tables that define what each S, O
and D value means. Those criteria are what make a rating defensible in an audit,
and they are not in this file. For formal PPAP submissions, customer-facing FMEA
work, or any disputed rating, use your own licensed copy of the handbook.

AIAG and VDA are trademarks of their respective owners. This project is not
affiliated with, endorsed by, or certified by either organisation.

## How to apply the rules

1. Find the Severity (S) row
2. Find the Occurrence (O) band
3. Find the Detection (D) band
4. Read the Action Priority: **H** (High), **M** (Medium), **L** (Low)

## Absolute rules (override the table)

| Condition | AP |
|-----------|-----|
| S = 9 or 10 | Always **H** — regardless of O and D |
| S = 8, O = 4–10 | **H** if D ≥ 5; **M** if D ≤ 4 |

## AP decision rules (banded)

| S | O | D | AP |
|---|---|---|----|
| 10 | Any | Any | **H** |
| 9 | Any | Any | **H** |
| 8 | 6–10 | Any | **H** |
| 8 | 4–5 | 6–10 | **H** |
| 8 | 4–5 | 1–5 | **M** |
| 8 | 1–3 | Any | **M** |
| 7 | 6–10 | 7–10 | **H** |
| 7 | 6–10 | 4–6 | **M** |
| 7 | 6–10 | 1–3 | **M** |
| 7 | 4–5 | 7–10 | **M** |
| 7 | 4–5 | 4–6 | **M** |
| 7 | 4–5 | 1–3 | **L** |
| 7 | 1–3 | Any | **L** |
| 6 | 8–10 | 7–10 | **H** |
| 6 | 8–10 | 4–6 | **M** |
| 6 | 8–10 | 1–3 | **M** |
| 6 | 5–7 | 7–10 | **M** |
| 6 | 5–7 | 1–6 | **L** |
| 6 | 1–4 | Any | **L** |
| 1–5 | Any | Any | **L** |

## Action requirements by AP

| AP | Required Action |
|----|----------------|
| **H** | Must assign a responsible person and a target date. If no action is possible, document why and escalate to management. |
| **M** | Team should evaluate whether a reduction is beneficial. Recommended to act. Document decision. |
| **L** | No action required. Document rationale. |

## Why AP replaces RPN

The legacy Risk Priority Number (RPN = S × O × D) was unreliable because:
- Same RPN could represent very different risk profiles: S=6, O=6, D=6 (RPN=216) vs S=9, O=8, D=3 (RPN=216) — the second is far more dangerous
- Teams "gamed" RPN by improving detection (cheapest change) without addressing safety risk
- No mandatory action threshold for high-severity items

The AP table ensures:
- S=9/10 always gets action regardless of O and D
- Actions address severity + occurrence priority, not just the cheapest detection improvement
