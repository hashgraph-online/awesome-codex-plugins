---
name: control-plan-template
type: reference
parent_skill: control-plan
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-06"
last_updated: "2026-06-06"
updated_by: RBraga01
reviewed_by: RBraga01
license: MIT
---

# Control Plan — Template and Column Reference

Blank Control Plan template with column-by-column guidance, sampling selection criteria, reaction plan matrix, and PFMEA-to-CP column mapping.
Use alongside the [control-plan](../SKILL.md) skill.

> **Scope:** This document covers the blank CP template structure, detailed column instructions with common mistakes, a sample plan selection guide, the reaction plan severity matrix, and the PFMEA column-to-CP column mapping. For the workflow (how to build, populate, and audit a CP), see [control-plan SKILL.md](../SKILL.md).

---

## 1. Control Plan Header — Blank Template

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│  CONTROL PLAN                                    □ Prototype  □ Pre-Launch  □ Production          │
├──────────────────────────┬───────────────────────┬──────────────────────────────────────────────┤
│  Control Plan Number:    │                       │  Date (original):                             │
│  Part Number / Latest    │                       │  Date (revised):                              │
│  Change Level:           │                       │                                               │
├──────────────────────────┼───────────────────────┼──────────────────────────────────────────────┤
│  Part Name / Description:│                       │  Core Team:                                   │
├──────────────────────────┼───────────────────────┼──────────────────────────────────────────────┤
│  Supplier / Plant:       │                       │  Supplier Code:                               │
├──────────────────────────┼───────────────────────┼──────────────────────────────────────────────┤
│  Supplier / Plant        │                       │  Key Contact / Phone:                         │
│  Approval / Date:        │                       │                                               │
├──────────────────────────┼───────────────────────┼──────────────────────────────────────────────┤
│  Customer Engineering    │                       │  Customer Quality                             │
│  Approval / Date:        │                       │  Approval / Date:                             │
│  (if required)           │                       │  (if required)                                │
└──────────────────────────┴───────────────────────┴──────────────────────────────────────────────┘
```

---

## 2. Control Plan Detail — 13-Column Row Structure

Each row in the Control Plan body represents one controlled characteristic at one process step. The 13 standard columns are:

```
Col 1        Col 2                   Col 3                    Col 4    Col 5              Col 6
Part /    |  Process Name /       |  Machine / Device /    |  No.  |  Product          |  Process
Process   |  Operation            |  Jig / Tools for       |       |  Characteristic   |  Characteristic
Number    |  Description          |  Mfg.                  |       |                   |

Col 7              Col 8                          Col 9           Col 10     Col 11      Col 12        Col 13
Special        |  Product / Process            |  Evaluation / |  Sample |  Sample  |  Control    |  Reaction
Characteristic |  Specification /             |  Measurement  |  Size   |  Freq.   |  Method     |  Plan
Classification |  Tolerance                   |  Technique    |         |          |             |
```

---

## 3. Column-by-Column Guidance

### Column 1 — Part / Process Number

**What to enter:** The operation number from the Process Flow Diagram. Use the same numbering system as the Process Flow and PFMEA (e.g., OP-010, OP-020, or 10, 20, 30).

**Common mistakes:**
- Using free-form descriptions instead of a consistent operation number — breaks the PFMEA-CP traceability link
- Skipping operations present in the Process Flow — every operation must appear
- Using a different numbering convention than the PFMEA

---

### Column 2 — Process Name / Operation Description

**What to enter:** Short descriptive name of the operation (e.g., "Injection Moulding", "Heat Treatment 180°C", "Torque Tightening M8 Bolts", "Final Inspection"). Must match the operation name in the Process Flow.

**Common mistakes:**
- Overly generic names ("Operation 1", "Process Step") — not auditable
- Name does not match the Process Flow — auditor cannot trace the row back to the flow

---

### Column 3 — Machine / Device / Jig / Tools for Manufacturing

**What to enter:** Specific equipment identifier. For machinery: machine name + asset number (e.g., "Injection Moulding Press P-12"). For inspection steps: the gauge or fixture name and ID. For assembly: jig or torque tool ID.

**Common mistakes:**
- Listing the equipment type only ("injection press") without an identifier — impossible to verify calibration
- Leaving blank for manual operations — manual operations still require a tool or method description
- Not updating when equipment is changed (new machine installed post-PPAP)

---

### Column 4 — No. (Characteristic Number)

**What to enter:** The balloon number from the dimensioned drawing, or an internal reference number linking this CP row to a specific PFMEA failure mode or drawing characteristic. Each row has a unique number.

**Common mistakes:**
- Numbering does not match the ballooned drawing — auditor cannot verify the tolerance is correct
- Process characteristics (temperature, torque, speed) have no balloon number but still need an internal reference — use "P-001" convention or similar

---

### Column 5 — Product Characteristic

**What to enter:** The physical or functional attribute of the product being measured at this step (e.g., "Outer Diameter", "Tensile Strength", "Surface Roughness Ra", "Weld Penetration Depth"). This is a product measurement — what the part looks like or does.

Leave blank if this row controls a process parameter only (Column 6 carries the characteristic).

**Common mistakes:**
- Mixing product and process characteristics in the same column — use Column 5 for product and Column 6 for process; some rows will have both
- Writing a vague characteristic like "appearance" — must name the specific attribute (e.g., "surface gloss level 60°")

---

### Column 6 — Process Characteristic

**What to enter:** The process parameter being controlled at this step, where controlling the process parameter ensures the product characteristic. Examples: "Mould Temperature (°C)", "Injection Pressure (bar)", "Torque Setting (N·m)", "Cure Time (min)".

Leave blank if this row controls a product output only (Column 5 carries the characteristic).

**Common mistakes:**
- Control Plan covers only product characteristics and omits process parameters — this is one of the most common audit findings
- Process characteristic specified without a tolerance (Column 8 must have the process setpoint and control limits)

---

### Column 7 — Special Characteristic Classification

**What to enter:** The OEM classification symbol for safety-critical, significant, or key characteristics. Leave blank for standard (non-classified) characteristics.

| Symbol | Classification | Used by |
|--------|---------------|---------|
| SC | Safety Characteristic | Ford, GM |
| CC | Critical Characteristic | Ford |
| ★ | Safety / Critical | AIAG generic |
| ◆ | Safety / Critical | VDA / BMW |
| KPC | Key Product Characteristic | Ford, GM, Stellantis |
| KCC | Key Control Characteristic | Ford, GM |
| ▲ | Significant Characteristic | GM |
| (none) | Standard characteristic | All |

**Common mistakes:**
- Incorrect symbol for the OEM — Ford uses SC/CC/KPC; BMW uses ◆; using the wrong symbol is a direct audit nonconformance
- SC/CC rows missing entirely — auditor cross-checks against the PFMEA and drawing
- Standard characteristic rows incorrectly flagged as SC — creates unnecessary inspection burden

---

### Column 8 — Product / Process Specification / Tolerance

**What to enter:** The nominal value and tolerance (e.g., "25.00 ± 0.05 mm", "180°C ± 5°C", "Torque 22 N·m min / 28 N·m max"). For attribute characteristics: the acceptance criterion (e.g., "No visible porosity").

**Common mistakes:**
- Copying the drawing tolerance without updating when the drawing is revised
- Writing "per drawing" or "per spec" without stating the actual value — the CP must be self-sufficient for an operator on the floor
- Tolerance range wider than the drawing tolerance — the CP tolerance must be equal to or tighter than the drawing

---

### Column 9 — Evaluation / Measurement Technique

**What to enter:** The specific gauge or measurement method (e.g., "Vernier calliper 0.02 mm resolution", "CMM – Zeiss Contura", "Torque wrench TW-04", "Attribute go/no-go gauge G-021", "Visual per WI-057").

**Common mistakes:**
- Entering "measure" or "check" without specifying the tool — not a valid inspection method
- Specifying a gauge type without an asset ID — cannot verify calibration status
- "Visual inspection" on an SC/CC characteristic — visual is not adequate for a classified characteristic unless backed by a verified visual standard with a defined accept/reject limit

---

### Column 10 — Sample Size

**What to enter:** A specific number (e.g., 5, 10, 1 per pallet). For 100% inspection, enter "100%". Do not write "as required", "as needed", or "n/a".

**Common mistakes:**
- "As required" — not a sample plan; customer will reject
- Sample size of 1 for a critical characteristic — statistically meaningless for detecting process shifts
- No differentiation between sample size for setup verification vs. running production (if both are done, document separately)

---

### Column 11 — Frequency

**What to enter:** Specific interval or trigger (e.g., "Every 2 hours", "First-off and last-off per shift", "Every 50 pcs", "Every lot", "100% — all pieces"). For event-triggered checks, specify the trigger (e.g., "After each tool change").

**Common mistakes:**
- "As required" or "as needed" — rejected; must be a defined interval
- Frequency not tied to the process control strategy (e.g., high-Cpk process with 100% inspection — wasteful; low-Cpk process with once-per-shift — dangerous)
- No mention of startup checks — many defects occur at shift start or after a tool change

---

### Column 12 — Control Method

**What to enter:** How the process is controlled to maintain the characteristic within specification. Specify the control type:
- **SPC:** "X-bar R chart, 5 pcs every 2h, action rules: 1 point beyond UCL/LCL, 8 consecutive points one side of mean"
- **100% inspection:** "100% visual per WI-057 / 100% dimensional with go/no-go gauge G-021"
- **Poka-yoke / error-proofing:** "Torque controller with pass/fail signal; part does not release if out of range"
- **Setup check:** "First-off approval by QC before production run starts"
- **Lot testing:** "AQL 0.65 per MIL-STD-1916 table"

**Common mistakes:**
- "SPC" written without specifying which chart, sample size, frequency, or action rules
- "Inspect per WI" without naming which WI
- Control method not commensurate with the severity of the characteristic (e.g., visual-only on an SC)

---

### Column 13 — Reaction Plan

**What to enter:** Specific actions to take when the characteristic is out of control or out of specification. Must answer:
1. **What** — immediate containment action (stop production, segregate parts, 100% sort)
2. **Who** — responsible person or role (not "contact supervisor" — name the role explicitly)
3. **What next** — disposition of suspect parts (scrap, rework per WI-XXX, customer notification)
4. **When to restart** — condition that must be met before production resumes (corrective action verified, re-measurement confirms conformance)
5. **Escalation** — if the issue is not resolved within a defined time, who is notified next

**Common mistakes:**
- "Notify supervisor" — this is not a reaction plan; it is step zero of one
- No disposition instruction for non-conforming parts
- No restart condition — production can restart without verification
- Reaction plan is identical for every row regardless of severity — demonstrates it was not tailored

---

## 4. Sample Plan Selection Guide

### When to Use Each Approach

| Method | When to use | Typical application |
|--------|------------|---------------------|
| **100% Inspection** | Cpk < 1.33; Safety/regulatory characteristics (SC, CC); poka-yoke not available; new process with unstable history | All safety welds, safety-critical fastener torques, regulatory functional tests |
| **Statistical Process Control (SPC)** | Cpk ≥ 1.33 and process is stable; variable characteristics where trends are detectable; high-volume repetitive processes | Dimensional characteristics on injection moulded or stamped parts; process parameters (temperature, pressure) |
| **AQL-based lot sampling** | Lot sizes well-defined; inspection cost prohibitive at 100%; characteristic is not SC/CC; traceability exists to separate lots | Incoming inspection of purchased components; final inspection of low-volume machined parts |
| **First-off + Last-off per shift** | Characteristics affected by tool wear, thermal expansion, or setup variation; medium volume; Cpk ≥ 1.67 | Machining operations where tool wear drifts dimensions within the shift |
| **Fixed frequency (time-based)** | Continuous process (extrusion, casting, plating); Cpk ≥ 1.33; no discrete lot structure | Plating thickness, coating weight, extrusion diameter |
| **Event-triggered (setup/changeover)** | Characteristic affected primarily by setup, not by in-run variation; Cpk ≥ 1.67 between setups | Tooling changeover in stamping; first-off after mould cleaning |

### AQL Selection Reference

| AQL Level | Use when | Risk |
|-----------|----------|------|
| 0.065 | Safety or regulatory; SC/CC on non-100% process | Highest detection sensitivity |
| 0.10 | Fit/form/function characteristics with high severity | Very high detection |
| 0.25 | Functional characteristics; customer-visible | High detection |
| 0.65 | Standard dimensional or cosmetic | Standard |
| 1.0 | Cosmetic only; low customer impact | Lower detection |
| 2.5 | Internal characteristics; fully contained failure modes | Lowest practical detection |

**Never use AQL sampling for SC/CC characteristics unless the customer has formally approved the AQL plan and the characteristic has Cpk ≥ 1.67.**

---

## 5. Reaction Plan Requirement Matrix

Required stringency of the reaction plan based on characteristic severity and control method.

| Characteristic | Cpk / Process State | Minimum Control Method | Reaction Plan Required Elements |
|----------------|--------------------|-----------------------|--------------------------------|
| SC / CC (Safety, Regulatory) | Any | 100% inspection OR Cpk ≥ 1.67 + SPC | Stop production immediately; segregate and contain all parts since last confirmed good; do not release any parts until 100% verification; escalate to customer within 24h; PFMEA and CP update required before restart |
| SC / CC (Safety, Regulatory) | Cpk < 1.33 | 100% inspection mandatory | As above — plus formal customer deviation required; do not ship any parts without customer approval |
| KPC / KCC (Significant) | Cpk ≥ 1.33 | SPC or fixed-frequency | Stop line on OOC signal; hold parts produced since last conforming sample; 100% sort of suspect lot; notify quality lead; record on SPC chart and investigate assignable cause; restart after assignable cause confirmed resolved |
| Standard (non-classified) | Cpk ≥ 1.33 | Periodic sampling or SPC | Hold suspect parts; notify operator and shift supervisor; sort per defined AQL or 100%; identify and tag conforming lot; document in quality log; restart after confirmation |
| Standard (non-classified) | Cpk < 1.33 | 100% inspection | Same as above + open corrective action (8D or equivalent); notify quality manager; escalate to engineering for root cause if recurrent within 5 days |
| Process characteristic (KCC) | Process parameter OOC | Poka-yoke preferred; SPC acceptable | Stop process; adjust process to setpoint; verify product produced during OOC condition; do not advance to next operation until process confirmed stable; document deviation |

---

## 6. PFMEA-to-Control Plan Column Mapping

How each PFMEA column informs the corresponding Control Plan column.

| PFMEA Column | PFMEA Content | Maps to CP Column | CP Usage |
|--------------|--------------|-------------------|----------|
| Function (PFMEA Step 2) | What the process step is supposed to do | Col 2 — Process Name / Operation Description | Confirms the CP row exists for this process step |
| Failure Mode (PFMEA Step 3) | What goes wrong | Col 5 or Col 6 — Product or Process Characteristic | The characteristic being controlled is the feature that, if not controlled, leads to the failure mode |
| Failure Effect (PFMEA Step 3) | What the customer experiences | Informs Col 7 classification | High-severity effects (S ≥ 8) drive SC/CC classification in the CP |
| Severity (S) rating | How bad is the effect | Col 7 — Classification; Col 13 — Reaction Plan stringency | S ≥ 9: SC/CC required in Col 7; stringent reaction plan in Col 13 |
| Current Prevention Control | How we prevent the failure mode from occurring | Col 6 — Process Characteristic; Col 12 — Control Method (prevention side) | Process parameters being controlled (process characteristic) and the control method used to maintain them |
| Current Detection Control | How we detect the failure mode if it occurs | Col 9 — Measurement Technique; Col 12 — Control Method (detection side) | The gauge or inspection method; detection frequency drives Col 10 and Col 11 |
| Detection (D) rating | How well we detect the failure if it occurs | Col 10/11 — Sample size and frequency | High D rating (poor detection) → increase sample size or move to 100%; low D rating (good detection) may allow frequency reduction |
| Action Priority (AP) / RPN | Overall risk level | Col 7, Col 12, Col 13 | H-AP or high-RPN → SC/CC in Col 7; highest-stringency control in Col 12; most explicit reaction plan in Col 13 |
| Recommended Action (completed) | Improvement action taken | Col 12 — Control Method (updated) | Completed actions that improved controls must be reflected in the CP; CP revision date ≥ PFMEA recommended action completion date |
| Responsibility / Target Date | Owner of the corrective action | Not directly on CP | Confirms the CP is updated after PFMEA actions close — if PFMEA action date is more recent than CP revision, CP is out of date |

### Key Alignment Rules

1. Every PFMEA row with Severity ≥ 8 must have a corresponding CP row — no exceptions.
2. Every PFMEA "Current Detection Control" must appear in CP Column 9 (Measurement Technique) or Column 12 (Control Method).
3. Every completed PFMEA "Recommended Action" that changes a control must be reflected in the CP before the CP is submitted for PPAP.
4. The CP revision date must be ≥ the PFMEA date of last update. If the PFMEA was updated (e.g., after a corrective action or process change) and the CP was not, the CP is out of revision.
5. Process characteristics (KCC) in the PFMEA "Current Prevention Controls" must appear in CP Column 6 — if the PFMEA says "controlled mould temperature" but the CP has no row for mould temperature, there is a gap.
