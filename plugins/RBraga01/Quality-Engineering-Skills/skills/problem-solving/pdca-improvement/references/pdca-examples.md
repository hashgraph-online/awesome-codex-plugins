---
name: pdca-examples
type: reference
parent_skill: pdca-improvement
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-06"
last_updated: "2026-06-06"
updated_by: migmcc
reviewed_by: RBraga01
license: MIT
---

# PDCA Worked Examples and Gate Criteria Reference

Three complete PDCA worked examples with gate criteria, failure modes, and methodology selection guidance.
Use alongside the [pdca-improvement](../SKILL.md) skill.

> **Scope:** This document covers worked examples, phase gate checklists, a PDCA vs 8D vs DMAIC selection decision table, and common failure patterns by phase. For the PDCA workflow steps, pilot volume guidance, and required documentation list, see [pdca-improvement SKILL.md](../SKILL.md).

---

## Worked Example 1 — Manufacturing Process Improvement

**Context:** An automotive connector assembly line produces a solder joint defect (cold joint) on terminal type T-4 at a rate of 4,800 PPM over the last three months. The process engineer wants to reduce this to below 500 PPM without a full line redesign.

---

### PLAN

**Current situation:**
- Defect: Cold solder joint on T-4 terminals, identified at automated optical inspection (AOI)
- Baseline: 4,800 PPM over 13 weeks of production data (n = 62,000 units)
- Target: ≤ 500 PPM sustained for 8 consecutive weeks
- Owner: Process Engineer — Maria Santos
- Timeline: 12 weeks total cycle

**Root cause analysis:**
- Fishbone identified three Confirmed causes:
  - Machine: Reflow oven zone 3 temperature drifting 8–12°C low during high ambient temperature periods (confirmed by 6-week data log review)
  - Method: Solder paste volume specification not updated after component change in ECO-2025-144 — T-4 pads now require 15% more paste volume; current WI specifies the old volume
  - Method: No incoming solder paste viscosity check — paste at viscosity limits passes IQC but produces voids
- 5-Why on zone 3 drift: Thermocouple calibrated annually; calibration interval too long for this drift rate → root cause: no periodic drift verification between calibrations

**Improvement plan:**
| Action | Owner | Due | Target metric |
|---|---|---|---|
| Update oven zone 3 thermocouple calibration interval from annual to quarterly | Maintenance | Week 2 | Calibration record |
| Add in-shift temperature verification: operator records zone 3 reading at shift start | Quality | Week 2 | Updated WI + control plan |
| Update solder paste volume specification in WI rev 7 per ECO-2025-144 | Engineering | Week 3 | WI rev 7 approved |
| Add incoming paste viscosity check to IQC procedure | Quality | Week 3 | IQC procedure updated |

**Pilot scope:** Line 2, T-4 terminals only. Minimum pilot: 6,000 units (to detect 500 PPM with statistical confidence; at baseline 4,800 PPM, 6,000 units expected 29 defects under old conditions; 500 PPM target = 3 expected — clearly distinguishable). Duration: minimum 4 weeks.

**Plan gate — passed:** Root cause confirmed with data; pilot scope defined with explicit volume and duration minimum; target is SMART.

---

### DO

- WI rev 7 published to line 2 workstations in Week 3
- Zone 3 thermocouple recalibrated in Week 2; reading confirmed 6°C low — adjusted
- In-shift temperature verification log started Week 2
- Incoming paste viscosity check added to IQC from Week 3 receipt
- Pilot started Week 4 after all changes in place
- Deviation noted: solder paste supplier delivery delay — pilot started 4 days late; minimum duration and volume targets unchanged

**Do gate — passed:** All planned changes implemented; pilot started; data collection running per plan; deviation documented.

---

### CHECK

**Results at Week 8 (pilot Week 4 complete):**

| Metric | Baseline | Target | Pilot result | Gap closed? |
|---|---|---|---|---|
| Solder cold joint PPM — T-4 | 4,800 | ≤ 500 | 380 PPM (n = 7,200 units, 2.7 defects) | Yes |
| Zone 3 temperature deviation | ±10°C drift observed | ±2°C | ±1.8°C over pilot period | Yes |
| Paste volume conformance | Not measured (old WI) | 100% within spec | 98.4% in spec | Yes (marginal) |

**Unexpected effect:** AOI false reject rate increased 0.6% due to changed paste volume — solder fillet profile different from programmed reference. AOI programme update required before full deployment.

**Check gate — passed with condition:** Target PPM achieved; improvement is sustained over 4 weeks; unexpected AOI programme effect noted and must be resolved before full deployment.

---

### ACT

- WI rev 7 deployed to lines 1, 3, 4 after AOI programme update confirmed in Week 9
- PFMEA updated: zone 3 temperature drift added as new failure mode; in-shift verification listed as prevention control; S/O/D revised
- Control plan updated: in-shift zone 3 verification added; paste viscosity check added at IQC
- Training records completed for all operators on lines 1–4 and IQC technicians
- Horizontal deployment: T-3 and T-5 terminal variants reviewed — same oven, same paste volume change required; ECO confirmed both affected; WI updated for both
- Result at Week 16 (8 weeks post-deployment): 290 PPM across all lines — target sustained
- Lessons learned: ECO implementation must include a mandatory review of affected WI parameters, not just a document number update

**Act gate — closed:** Target sustained for 8 weeks; all documents updated; horizontal deployment completed and confirmed; lessons learned recorded.

---

## Worked Example 2 — Supplier Quality Issue

**Context:** A supplier (SubCo) for aluminium housings has a repeat non-conformance: surface roughness Ra exceeding 1.6 µm (limit) at the sealing face. Three 8D corrective actions have been issued in 18 months with no sustained improvement. PDCA opened as a proactive improvement with SubCo's quality manager.

---

### PLAN

**Current situation:**
- Defect: Ra > 1.6 µm at sealing face (specification limit); measured at our incoming inspection
- Baseline: 3.2% non-conformance rate over 18 months (n = 8,400 units inspected); three previous 8D actions did not sustain improvement beyond 60 days
- Target: ≤ 0.3% sustained for 12 weeks (to match IATF 16949 zero-defect incoming requirement at this volume)
- Owner: Supplier Quality Engineer — James Okafor (with SubCo QM as co-owner)
- Timeline: 16 weeks

**Root cause analysis — with SubCo team:**
- Previous 8D actions addressed: cutting insert type (replaced twice), coolant flow rate (increased), and operator training. None sustained.
- This PDCA used multi-vari study (positional vs cyclical vs temporal) — identified temporal pattern: Ra non-conformance rate doubles in the first 20 parts after a tool change, then stabilises
- Root cause confirmed: new inserts are not run-in before production; the cutting edge requires 15–20 cuts to reach stable geometry; parts produced during this run-in window exceed Ra limit
- Why was this not caught before: SubCo's SPC chart does not differentiate first-off-after-tool-change from steady-state production; the non-conforming parts blend into the chart and the pattern was invisible

**Improvement plan:**
| Action | Owner | Due |
|---|---|---|
| Implement tool change run-in protocol: first 20 parts after tool change segregated and scrapped | SubCo Process Engineer | Week 3 |
| Update SubCo control plan to flag tool change events and apply 100% inspection for next 25 parts | SubCo Quality Manager | Week 3 |
| Add tool change event marker to SPC chart to enable temporal analysis | SubCo Quality Manager | Week 4 |
| Update PPAP process flow to include run-in protocol | SubCo Engineering | Week 5 |

**Pilot scope:** One CNC machine (machine 3) processing housing variant HX-200. Minimum pilot: 3 complete tool life cycles (each cycle ~400 parts) = 1,200 parts minimum, 6 weeks minimum.

**Plan gate — passed:** Root cause confirmed with multi-vari data; pilot scope defined with explicit cycle and volume minimum; target measurable.

---

### DO

- Run-in protocol implemented on machine 3 Week 3; first tool change conducted under new protocol observed by SQE
- 100% inspection of first 25 parts after tool change started Week 3
- SPC chart updated with tool change markers Week 4
- Run-in parts from three tool changes: 20 parts + 20 parts + 20 parts scrapped (first 20 were Ra > 1.6 µm in all three cases — confirming the cause mechanism)

**Do gate — passed:** Protocol implemented; run-in confirmation data collected; scrap documented and accepted by SubCo as cost of validation.

---

### CHECK

| Metric | Baseline | Target | Pilot result (1,200 parts, 3 tool cycles) |
|---|---|---|---|
| Ra non-conformance rate — steady state | 3.2% | ≤ 0.3% | 0.0% (0/1,140 steady-state parts) |
| Ra non-conformance — run-in parts (scrapped) | Part of 3.2% | Scrapped | 100% of run-in parts exceeded Ra limit — confirms mechanism |
| Scrap increase | Not tracked separately | Quantified | +20 parts per tool change (run-in protocol); tool life = ~400 parts → +5.0% scrap rate on machine 3 |

**Check gate — passed with cost note:** PPM target met for steady-state production. Run-in scrap rate (+5.0%) is a trade-off and was accepted in the Plan — business case confirmed it is preferable to non-conformance at the customer. Financial impact to be reviewed quarterly.

---

### ACT

- Run-in protocol deployed to all 6 CNC machines at SubCo processing this housing variant
- PPAP updated to include run-in protocol and 100% first-25 inspection after tool change
- SubCo PFMEA updated: "tool change without run-in" added as failure mode
- Annual supplier audit checklist updated to verify run-in protocol compliance
- 12-week monitoring period: 0 Ra non-conformances at incoming inspection (n = 6,800 units)
- Lessons learned: SPC charts without event markers mask temporal patterns; SPC chart design must include process event logging for tool changes, material changes, operator changes

**Act gate — closed:** Target sustained 12 weeks; PPAP and PFMEA updated; supplier audit checklist updated; lessons learned recorded.

---

## Worked Example 3 — Internal Audit Finding

**Context:** An internal audit (ISO 9001 §8.4 — external providers) found that 6 of 12 active suppliers do not have current approved supplier agreements (ASAs). Finding classified as Major Non-Conformance. PDCA opened to close the systemic gap.

---

### PLAN

**Current situation:**
- Finding: 50% of active suppliers (6/12) have expired or missing Approved Supplier Agreements
- Baseline: 6 ASAs expired or missing; renewal process is manual and tracked in a spreadsheet that is not monitored for expiry dates
- Target: 100% of active suppliers with current ASAs; automated expiry monitoring in place; sustained for two subsequent internal audit cycles
- Owner: Supplier Quality Manager — Ana Ferreira
- Timeline: 10 weeks

**Root cause analysis (5-Why):**
1. Why are 6 ASAs expired or missing? — No system alerts when an ASA is approaching expiry
2. Why is there no system alert? — ASAs are tracked in a spreadsheet without conditional formatting or calendar integration
3. Why was the spreadsheet not designed with alerts? — When the ASA process was established (2019), the QMS did not have a digital workflow tool; the spreadsheet was a temporary solution that became permanent
4. Why was the temporary solution not replaced? — No one was assigned ownership of the ASA renewal process; document control and supplier quality each assumed the other was responsible
5. Root cause: No defined process owner for ASA renewals; no system-based monitoring of expiry dates

**Improvement plan:**
| Action | Owner | Due |
|---|---|---|
| Assign ASA renewal process owner role (SQE with monthly review obligation) | Supplier Quality Manager | Week 1 |
| Renew all 6 expired ASAs — contact supplier, update terms, obtain signatures | SQE (Ana Ferreira) | Week 6 |
| Migrate ASA tracking to QMS module with automated 90-day and 30-day expiry alerts | IT/Quality Systems | Week 8 |
| Add ASA expiry check to monthly supplier scorecard review agenda | Supplier Quality Manager | Week 2 |
| Update internal audit checklist: ASA coverage is now a mandatory check with count of active vs valid | Quality Manager | Week 3 |

**Pilot scope (not applicable):** This is a compliance and systemic process improvement, not a production process change requiring a pilot. The "pilot" is the implementation itself, validated by the following internal audit. Success criterion: next internal audit (scheduled Week 24) finds 0 expired ASAs.

**Plan gate — passed:** Root cause confirmed (no process owner, no system monitoring); target measurable; timeline defined.

---

### DO

- Process owner assigned in Week 1; responsibility documented in job description
- All 6 expired ASAs contacted in Week 2; 4 renewed by Week 4, 2 outstanding (supplier review cycles)
- QMS module configuration started Week 3; 90-day and 30-day alerts configured and tested Week 7
- ASA expiry added to monthly scorecard review agenda Week 2
- Internal audit checklist updated Week 3

**Do gate — passed:** All planned actions implemented within timeline; 2 renewals pending supplier response (tracked, not blocked).

---

### CHECK

| Metric | Baseline | Target | Result at Week 10 |
|---|---|---|---|
| ASAs current | 6/12 (50%) | 12/12 (100%) | 11/12 (91.7%) — 1 supplier renewal still pending legal review |
| System-based expiry monitoring | None | Automated 90 + 30 day alerts | Active and tested; 2 alerts triggered as expected |
| Process owner assigned | None | Defined and documented | Confirmed |

**Check gate — conditional pass:** 11/12 achieved; 1 pending due to supplier legal process outside our control. QMS alerts functioning. Condition: final ASA to be obtained within 4 weeks; escalation plan in place (supplier on watch status).

---

### ACT

- 12th ASA obtained Week 13 — 100% achieved
- QMS module live for all ASAs; expiry alerts functioning
- Lessons learned: temporary tracking solutions (spreadsheets) should have a defined review date and replacement plan; QMS module should have been used from process establishment
- Finding closed with documented evidence: all 12 ASAs current, system monitoring active, process owner documented
- Next internal audit (Week 24): 0 expired ASAs found; finding closed

**Act gate — closed:** 100% target achieved and sustained through next audit cycle; systemic controls in place; lessons learned recorded.

---

## Gate Criteria Checklist by Phase

### PLAN Gate

| Criterion | Check |
|---|---|
| Problem statement is specific, measurable, and time-bounded | ☐ |
| Baseline data collected from a reliable source with date range and sample size | ☐ |
| Target is SMART: includes specific value, measurement method, and due date | ☐ |
| Root cause analysis completed using Fishbone and/or 5-Why | ☐ |
| Root cause supported by data — not assumed or based on team opinion | ☐ |
| Improvement actions mapped to specific root causes (not generic) | ☐ |
| Pilot scope defined with explicit minimum volume and/or duration | ☐ |
| Success criteria defined before pilot starts (not after seeing results) | ☐ |
| PFMEA reviewed for impact of proposed change | ☐ |

### DO Gate

| Criterion | Check |
|---|---|
| All planned changes implemented as defined in the Plan | ☐ |
| Training completed for all personnel involved in the pilot | ☐ |
| Data collection running per plan (measurement method, frequency, responsible person) | ☐ |
| Deviations from the plan documented (deviations are data — do not hide them) | ☐ |
| Minimum pilot volume or duration not yet reached (if still in DO) | ☐ |

### CHECK Gate

| Criterion | Check |
|---|---|
| Pilot volume or duration minimum has been met | ☐ |
| Before/after comparison table completed with actual data (not estimated) | ☐ |
| Target metric evaluated: met / partially met / not met | ☐ |
| Unexpected effects (positive or negative) documented | ☐ |
| Improvement is stable over time (not a one-time spike) | ☐ |
| Pilot conditions were representative (same operators, materials, environment as production) | ☐ |
| Decision made: proceed to Act / revise Plan / restart — with supporting rationale | ☐ |

### ACT Gate

| Criterion | Check |
|---|---|
| Work Instructions updated (revision number and approval date confirmed) | ☐ |
| Control Plan updated (new controls, frequencies, reaction plans) | ☐ |
| PFMEA updated (new failure modes, updated S/O/D, new controls) | ☐ |
| Training records completed for all affected personnel | ☐ |
| Horizontal deployment assessed: list of similar processes/products reviewed | ☐ |
| Horizontal deployment actions documented and completed (or N/A with justification) | ☐ |
| Ongoing monitoring established (KPI owner, frequency, review mechanism) | ☐ |
| Lessons learned registered | ☐ |
| If PDCA was triggered by audit finding or CAR: CAR closure evidence attached | ☐ |

---

## PDCA vs 8D vs DMAIC Decision Table

| Factor | PDCA | 8D | DMAIC |
|---|---|---|---|
| **Primary trigger** | Proactive improvement opportunity; audit finding; quality objective | Customer complaint; field escape; specific defect event | Chronic recurring defect; capability gap; statistical investigation needed |
| **Root cause known?** | Partially or not yet | No | No — must be statistically confirmed |
| **Containment required?** | No | Yes (D3 — immediate action to stop escapes) | No — no active escape |
| **Timeline** | Weeks to months | Days to weeks | Weeks to months |
| **Statistical depth** | Data-supported; basic SPC and trend analysis | Data-informed; qualitative tools acceptable | Full hypothesis testing; DOE; capability studies |
| **Output** | Standardised improved process; updated documents | Specific corrective action; PFMEA/CP update; 8D report | Optimised process capability; sustained Cpk improvement |
| **When to use** | Process optimisation; lessons learned; audit NC | Single complaint; escape; containment needed | Cpk improvement needed; repeated 8D or PDCA failures |
| **ISO 9001 reference** | §10.3 | §10.2 | §10.3 |
| **IATF 16949 reference** | §10.3.1 | §10.2.3 | §10.1 |
| **Can convert to another?** | If defect is active → open 8D first; run PDCA in parallel | If root cause proves systemic → escalate to DMAIC | If single event → close DMAIC, open 8D for immediate action |

**Decision guidance:**
- Customer complaint with containment needed → 8D
- Same 8D root cause recurs after three corrective actions → DMAIC
- Proactive improvement with known or suspected root cause → PDCA
- Capability below Cpk 1.33 with unknown cause → DMAIC
- Audit finding with systemic process gap → PDCA (with CAR for ISO 9001 compliance)
- Improvement from lessons learned with agreed approach → PDCA

---

## Common PDCA Failures by Phase

### PLAN failures

| Failure | Consequence | Prevention |
|---|---|---|
| Root cause not confirmed before defining actions | Actions address symptoms; problem recurs | Require data or physical evidence before classifying a cause as Confirmed |
| Pilot scope undefined or left to "whatever we can get" | Inconclusive results; cannot distinguish signal from noise | Define minimum volume and duration in writing before starting |
| Target defined as a direction ("reduce defects") not a value ("reduce from 3.2% to 0.3%") | No objective CHECK gate possible | Require a specific numeric target and measurement method in Plan |
| PFMEA not reviewed | Change introduces new risks not captured in the risk register | Mandatory PFMEA review step before Plan gate sign-off |

### DO failures

| Failure | Consequence | Prevention |
|---|---|---|
| Partial implementation — some changes made, others deferred | Results reflect a mixed state; impossible to attribute improvement to specific changes | Require all Plan changes to be in place before starting data collection |
| Pilot conditions not representative | CHECK results don't transfer to full production | Explicitly verify pilot conditions match production (operators, materials, shifts) |
| Data not collected during pilot | Nothing to CHECK | Assign a data collection owner in the Plan; verify at start of DO |

### CHECK failures

| Failure | Consequence | Prevention |
|---|---|---|
| Declaring success before minimum volume reached | Appears to work based on noise, not signal | Enforce minimum volume/duration as a hard gate |
| Ignoring negative side effects | Improvement in Y causes degradation in X; overall result is neutral or worse | Measure at least two KPIs: the target metric and one downstream process indicator |
| Treating "better than before" as "target met" | Insufficient improvement is standardised | Compare to the specific target, not just to baseline |

### ACT failures

| Failure | Consequence | Prevention |
|---|---|---|
| Documents updated in name only (revision number changed, content unchanged) | Process reverts within months; auditors find inconsistency | Verify document content matches new process during Act gate review |
| Horizontal deployment not assessed | Same root cause exists in adjacent lines/products; recurrence elsewhere | Require a horizontal deployment log listing every similar process and the action taken or N/A justification |
| PDCA closed at implementation, not at sustained performance | Improvement not confirmed as durable | Schedule a follow-up data review 4–8 weeks after Act; close only after sustained result confirmed |
| Lessons learned skipped under time pressure | Same failure recurs on the next project | Lessons learned is a mandatory ACT gate criterion — not optional |
