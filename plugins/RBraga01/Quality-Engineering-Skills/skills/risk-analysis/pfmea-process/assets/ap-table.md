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
---

# AIAG-VDA Action Priority (AP) Table

Reference: AIAG-VDA FMEA Handbook 2019, Step 5, Table 5-3

## How to read the table

1. Find the Severity (S) row
2. Find the Occurrence (O) column range
3. Find the Detection (D) range
4. Read the Action Priority: **H** (High), **M** (Medium), **L** (Low)

## Absolute rules (override the table)

| Condition | AP |
|-----------|-----|
| S = 9 or 10 | Always **H** — regardless of O and D |
| S = 8, O = 4–10 | **H** if D ≥ 5; **M** if D ≤ 4 |

## AP Table (AIAG-VDA 2019 summary)

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
