---
name: 6m-category-guide
type: reference
parent_skill: fishbone-analysis
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-06"
last_updated: "2026-06-06"
updated_by: RBraga01
reviewed_by: RBraga01
license: MIT
---

# 6M Category Guide — Fishbone Analysis Reference

Deep reference for populating and validating each 6M branch of an Ishikawa diagram.
Use alongside the [fishbone-analysis](../SKILL.md) skill.

> **Scope:** This document covers category definitions, manufacturing examples, question banks, common mistakes per category, and how to link confirmed branches to 5-Why chains. For the step-by-step brainstorming and evaluation workflow, see [fishbone-analysis SKILL.md](../SKILL.md).

---

## Category Definitions and Manufacturing Examples

### 1. Man — Human Factors

**Definition:** Any cause attributable to a person's action, omission, decision, or physical capability. Includes skill, knowledge, attention, and physical condition. Does NOT include the process or procedure itself (that is Method).

| Sub-category | Manufacturing examples |
|---|---|
| Training / competency gap | Operator qualified for station A performs station B without cross-training; certification expired; OJT not completed |
| Work instruction deviation | Operator applies torque by feel instead of using torque wrench; skips visual check step |
| Distraction / fatigue | End-of-shift production rush; multi-tasking on rework and new production simultaneously |
| Shift handover failure | Outgoing operator does not communicate in-process issue; setup parameters not verified by incoming operator |
| Ergonomic constraint | Part orientation forces operator into awkward grip, causing inconsistent force application |
| New / unfamiliar operator | First week on the job; returned from leave with process changes made in the interim |
| Deliberate workaround | Operator bypasses safety interlock or skip-step to maintain throughput |

**Question bank — Man branch:**

- Who performed this operation when the defect occurred? Same operator every time or different?
- Is the operator trained and qualified for this specific task, with current documentation?
- Is this defect concentrated in one shift, one line, or one operator group? (If yes → strong Man indicator)
- How long has the operator been performing this task? Was a change made recently?
- Is there a documented work instruction, and was it at the workstation and in use?
- Is the task cognitively complex or physically difficult to perform consistently?
- What does the operator say happened? Have you observed the task being performed?
- Does the defect correlate with any change in headcount, overtime, or temporary labour?

**Common mistakes on this branch:**

- Stopping at "operator error" without asking what made the error possible or likely — this is a symptom, not a root cause
- Confusing Man with Method: if the error occurs because there is no procedure, the root cause is in Method, not Man
- Ignoring shift and time-of-day correlation data — this is often the fastest clue for Man causes
- Classifying as Man without interviewing the operator or observing the task

---

### 2. Machine — Equipment and Tooling

**Definition:** Any cause attributable to equipment, tooling, fixtures, jigs, or automated systems. Includes condition, calibration, capability, and maintenance status.

| Sub-category | Manufacturing examples |
|---|---|
| Calibration out of interval | Torque wrench last calibrated 14 months ago against a 12-month interval |
| Worn tooling | Drill bit at end of life producing oversized holes; punch worn beyond replacement limit |
| Fixture / jig degradation | Locating pin worn 0.15 mm — part sits proud of nominal, affecting downstream press-fit |
| Maintenance overdue | Preventive maintenance skipped during production crunch; lubrication interval exceeded |
| Machine drift | Press force decreasing over a shift due to hydraulic fluid temperature rise |
| Equipment capability | Cpk = 0.82 for the critical feature — machine not inherently capable for this tolerance |
| Setup error | Die not fully seated; incorrect programme loaded for variant; offset not reset after tool change |
| Ancillary equipment | Conveyor belt worn causing part misalignment at station entry; sensor drift on reject chute |

**Question bank — Machine branch:**

- What is the last calibration date of all measurement equipment used on this process? Are all within interval?
- What is the Cpk of the machine for this feature? Has it been measured recently?
- When was preventive maintenance last performed? Is there a PM record for the period of the defect?
- Is there evidence of wear, play, vibration, or thermal drift in the relevant equipment?
- Has any tooling been changed near the time of defect onset? Confirm change records.
- Is the defect intermittent (suggesting drift or wear) or constant (suggesting setup or capability)?
- Have other parts run on this machine without issue? (If yes → machine is not the sole cause; something changed)
- Is the same defect found on parts from other machines? (If no → machine-specific)

**Common mistakes on this branch:**

- Checking calibration status without checking whether calibration interval is appropriate for the drift rate
- Confirming "machine is calibrated" and closing the branch — calibration confirmation is not a capability confirmation
- Ignoring tooling life tracking; verifying the spindle but not the insert or punch
- Not checking whether the defect correlates with tool change cycles or PM intervals

---

### 3. Method — Process and Procedure

**Definition:** Any cause attributable to how the work is defined, documented, or controlled. Includes process parameters, work instructions, control plan entries, and process sequence.

| Sub-category | Manufacturing examples |
|---|---|
| Missing work instruction | No documented method for this operation; verbal-only instruction |
| Outdated work instruction | WI shows rev 3; engineering change was implemented at rev 4; rev 4 never published to floor |
| Process parameter out of spec | Cure temperature set at 140°C; specification requires 155°C ± 5°C |
| No parameter verification | Oven temperature set by operator without post-setup verification reading |
| Incorrect process sequence | Primer applied after adhesive — instruction requires primer first |
| Control plan gap | This operation has no control plan entry; no frequency, method, or reaction plan defined |
| No operator self-check | Process step has no built-in self-verification; defect passes to next operation unchecked |
| Ambiguous instruction | WI says "tighten to specification" without specifying the torque value |

**Question bank — Method branch:**

- Is there a documented work instruction for this specific operation? Is it at revision level with the current engineering standard?
- Are process parameters (temperature, pressure, speed, torque, time) written down and controlled?
- Is there a control plan entry for this step? What is the required monitoring frequency and reaction plan?
- Is the method consistent across all operators and shifts? Ask each shift how they perform the task.
- Has the process sequence changed recently? Verify against the approved process flow diagram.
- Is the work instruction specific enough to be performed without interpretation?
- Is there a self-check or in-process inspection built into the method?
- If the method is followed exactly, can the defect still occur? (If yes → the method is the problem, not the operator)

**Common mistakes on this branch:**

- Treating work instruction absence as a Man problem (the operator "should have known") — if there is no WI, the system failed, not the operator
- Confirming the WI exists without verifying it is current, correct, and accessible at the workstation
- Ignoring process parameter drift: the parameter may be in spec at setup but drift during the shift
- Not examining the control plan — a missing control plan entry means there is no system to detect deviation

---

### 4. Material — Input Material and Components

**Definition:** Any cause attributable to the physical characteristics of incoming material, components, or sub-assemblies. Includes raw material, purchased components, packaging, and storage conditions.

| Sub-category | Manufacturing examples |
|---|---|
| Incoming material OOS | Substrate hardness out of spec; connector pin plating thickness below minimum |
| Batch / lot variation | Problem confined to a single supplier lot; correlates with lot change date |
| Supplier process change | Supplier changed sub-supplier for raw material without notification; changed plating chemistry |
| Storage / handling damage | Moisture-sensitive components exposed beyond floor life; ESD-sensitive parts stored without protection |
| FIFO not maintained | Oldest stock not consumed first; material stored beyond shelf life used in production |
| Incorrect material used | Similar-looking part from adjacent bin used; labelling error at incoming |
| Traceability gap | Cannot identify which lot was used for the defective production; traceability link broken |

**Question bank — Material branch:**

- Does the defect onset correlate with a specific material lot, batch, or delivery?
- What do incoming inspection records show for the affected batches? Were any marginal results accepted under concession?
- Has the supplier notified any process or sub-supplier changes in the relevant period?
- Are storage conditions controlled and recorded (temperature, humidity, ESD, shelf life)?
- Is FIFO enforced and verifiable? Check the actual stock rotation against records.
- Can you trace every defective part back to its material lot? If not, why not?
- Does the defect appear across multiple material lots or only one? (Single lot → material cause; multiple lots → look elsewhere)
- Has incoming inspection sampling frequency been adequate to detect this type of variation?

**Common mistakes on this branch:**

- Assuming incoming inspection passed = material is not the cause; incoming inspection has sampling limitations and does not test every characteristic
- Not requesting the supplier's Certificate of Conformance and comparing against actual measurement data
- Overlooking storage and handling — moisture absorption, ESD damage, and exceeded shelf life are invisible at incoming inspection
- Failing to check supplier change notifications — many material causes trace to undisclosed supplier changes

---

### 5. Measurement — Measurement System

**Definition:** Any cause attributable to how the product is measured or inspected, including gauge capability, calibration, method standardisation, and interpretation.

| Sub-category | Manufacturing examples |
|---|---|
| Gauge R&R inadequate | %GRR = 42% — more than 30% of observed variation is measurement noise |
| Gauge out of calibration | Micrometer calibrated 18 months ago; interval is 12 months |
| Non-standardised method | Three operators measure the same feature with different fixture orientations; results differ by 0.12 mm |
| Measurement location inconsistency | Dimension measured at different positions along the feature by different operators |
| False acceptance | Gauge resolution too coarse to detect out-of-spec condition; defects pass undetected |
| Attribute gauge ambiguity | Go/No-Go gauge worn — marginal parts pass that should not |
| Environmental influence on measurement | Dimensional measurement performed immediately after part comes out of 180°C oven; thermally expanded |

**Question bank — Measurement branch:**

- Has a Gauge R&R been performed for the CTQ / measurement in question? What was the result (%GRR)?
- Is the gauge calibrated and within its calibration interval?
- Is the measurement method fully standardised: same fixture, same contact points, same operator technique, same temperature conditions?
- Could parts that are actually non-conforming be passing measurement? (False acceptance)
- Could parts that are actually conforming be failing measurement? (False rejection causing artificial scrap)
- Are measurement results consistent between operators and between shifts?
- Is there evidence that the defect rate changes when a different gauge or operator measures?

**Common mistakes on this branch:**

- Confirming calibration and assuming the measurement system is acceptable — calibration confirms the gauge reads correctly at known reference values; it does not confirm repeatability and reproducibility in production conditions
- Not performing MSA before drawing capability conclusions — Cpk calculated on a poor measurement system is meaningless
- Ignoring attribute gauges in the MSA requirement — Go/No-Go gauges wear and can drift
- Assuming measurement error cannot be the "root cause" — if the problem is false escapes due to measurement noise, measurement IS the root cause

---

### 6. Mother Nature — Environment

**Definition:** Any cause attributable to the physical environment in which the process operates. Includes temperature, humidity, contamination, lighting, vibration, and seasonal effects.

| Sub-category | Manufacturing examples |
|---|---|
| Temperature variation | Adhesive cure profile affected by ambient temperature drop in winter months |
| Humidity | Moisture-sensitive components absorbing humidity during high-humidity season; condensation on cold parts |
| Contamination | Cutting fluid mist contaminating adhesive bonding area; particulates on optical surfaces |
| Vibration / noise | Nearby press causing micro-vibrations affecting a precision measurement station |
| Lighting | Insufficient lux for visual inspection station; glare causing false pass at outgoing |
| ESD environment | Ioniser not functioning; ESD-sensitive components damaged at assembly station |
| Cleanroom class deviation | ISO Class 7 requirement; actual class drifted to Class 8 due to gowning non-compliance |
| Seasonal / time-of-day pattern | Defect rate increases in afternoon when building temperature peaks; correlates with HVAC cycle |

**Question bank — Mother Nature branch:**

- Does the defect rate correlate with time of year, time of day, or weather conditions?
- Are ambient temperature and humidity monitored and recorded in the process area? Is the data reviewed?
- Are ESD controls (wrist straps, ionisers, flooring) verified regularly? What does the log show?
- Is the area free from contamination sources (oils, dust, cutting fluid, particulates) relevant to this defect?
- Is lighting at the inspection station adequate and consistent? Has lux been measured?
- Is the cleanroom or controlled environment in compliance? Review particle count records.
- Are parts or materials exposed to environment changes (e.g., thermal cycling, moisture cycles) between process steps?

**Common mistakes on this branch:**

- Dismissing this category as irrelevant without reviewing environmental data — many intermittent defects have environmental drivers
- Not reviewing environmental monitoring logs for the defect period — verbal confirmation that "conditions are fine" is not evidence
- Overlooking micro-environments: the main area may be controlled but a specific station or storage rack may not be
- Treating ESD and cleanroom compliance as administrative rather than technical — contamination and ESD damage are physical causes

---

## Linking Fishbone Branches to 5-Why Chains

The fishbone produces **candidate causes** classified as Confirmed or Probable. Each one becomes the starting point (Why 1) of an independent 5-Why chain.

**How to connect:**

| Fishbone output | 5-Why input |
|---|---|
| Confirmed: "Jig locating pin worn — measured 0.15 mm beyond limit" | Why 1: The jig locating pin was worn beyond its replacement limit |
| Probable: "Operator not following current work instruction rev 4" | Why 1: The operator was following work instruction rev 3, not the current rev 4 |
| Confirmed: "Material lot 2026-05-12 had incoming hardness at lower specification limit" | Why 1: Material in lot 2026-05-12 was at the lower specification limit for hardness |

**Rules for the handoff:**

1. The 5-Why starting statement must be factual and specific — match the evidence from the fishbone evaluation, not the general category label.
2. One Confirmed/Probable cause = one 5-Why chain. Do not merge causes into a single chain.
3. If a 5-Why chain on a Probable cause reaches a Why that cannot be answered with data, stop and gather evidence before continuing. Do not invent Whys.
4. If two separate 5-Why chains converge on the same systemic root cause (e.g., both trace back to "no preventive maintenance schedule for tooling"), this convergence is significant — it reveals a systemic gap.

---

## Prioritising Branches for Investigation

Not all confirmed or probable causes can be investigated simultaneously. Use this prioritisation logic:

### Priority tier 1 — Investigate immediately

Causes where:
- Physical evidence already exists (e.g., wear measurement, calibration record gap, lot correlation)
- Investigation can be completed in hours (records review, quick measurement)
- The cause directly explains the full IS pattern (quantity, location, timing all fit)

### Priority tier 2 — Investigate in parallel

Causes where:
- Investigation requires production time (reproduction test, extended data collection)
- Cause is Probable but not yet Confirmed — needs a verification test
- The cause explains part of the IS pattern but not all dimensions

### Priority tier 3 — Hold pending tier 1 and 2 results

Causes where:
- Investigation is resource-intensive (full MSA, DOE, supplier audit)
- The cause is inconsistent with at least one IS/IS-NOT dimension — marginal
- The same systemic fix (if found in tier 1 or 2) would likely also address this cause

### Decision criteria table

| Factor | Weight toward higher priority |
|---|---|
| Physical evidence already available | High |
| Cause consistent with ALL IS/IS-NOT dimensions | High |
| Single operator, shift, or batch affected | Medium (concentrate investigation there) |
| Reversible to test (e.g., swap jig and rerun) | High |
| Investigation disrupts production | Lower (schedule, do not skip) |
| No physical evidence yet — theory only | Lower (gather data first) |

**Rule:** Never eliminate a branch from investigation based on team opinion alone. A branch is eliminated only when data contradicts it. If data is not available, the branch stays open until data is obtained.
