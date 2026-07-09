---
name: dfmea-design
description: >-
  Build a design risk analysis, DFMEA worksheet, or interface analysis using the AIAG-VDA
  FMEA Handbook 2019. Covers design intent, interface failures, boundary diagram, and design
  robustness before manufacturing. Use during new product development, design changes, or
  when a field failure reveals a design weakness. Required for IATF 16949 §8.3 scope.
license: MIT
metadata:
  author: RBraga01
  version: "1.1"
  iso-9001: "8.3"
  iatf-16949: "8.3.3.3"
  aiag-reference: "AIAG-VDA FMEA Handbook 2019, DFMEA chapters"
  domain: quality-engineering
  subdomain: risk-analysis
  industries: automotive,electronics,aerospace,medical,general
  status: approved
  created: "2026-06-01"
  last_updated: "2026-06-06"
  updated_by: RBraga01
  reviewed_by: RBraga01
  standard_edition: "AIAG-VDA FMEA Handbook 2019"
---

# Design FMEA (DFMEA) — AIAG-VDA 2019

## Goal

Identify and mitigate design risks by analysing functions, interfaces, and failure modes — so that design weaknesses are resolved before release to manufacturing, and the results feed directly into the DVP, PFMEA, and Control Plan.

## Required Execution Checklist

- [ ] DFMEA scope defined: boundary diagram complete, inside/outside boundary identified
- [ ] Product hierarchy mapped: system → subsystem → component → interface (Step 2)
- [ ] All interfaces identified — internal (component-to-component), external (environment), and user/assembly
- [ ] All functions defined with Verb + Noun + Measurable Standard (Step 3)
- [ ] Each function has a measurable verification method confirmed in the DVP
- [ ] Failure chain complete: Effect → Mode → Cause for each function (Step 4)
- [ ] All Failure Causes validated using engineering analysis (FEA, calculation) or test evidence — not assumptions
- [ ] S/O/D ratings justified using analysis, test data, or design history
- [ ] All H-AP items have a defined action, named owner, and target date
- [ ] DFMEA → DVP, PFMEA, and drawing linkage verified before release to manufacturing

---

## When to use

- New product development (integrate into APQP Phase 2 — Product Design and Development)
- Design change or engineering change request (ECR)
- Field failure investigation revealing a design root cause
- Periodic design review
- Before handoff to manufacturing (DFMEA drives the PFMEA)

**Key difference from PFMEA:** DFMEA analyses the design intent and design robustness. PFMEA analyses the manufacturing process. DFMEA comes first — its failure effects and severity ratings inform the PFMEA.

## Prerequisites

- Product requirements / specification (engineering drawing, customer spec)
- System block diagram or product breakdown structure
- Interface matrix (if system-level analysis)
- Team: design engineer, systems engineer, quality engineer, reliability (if available)

## The 7-Step AIAG-VDA 2019 Approach for DFMEA

---

### Step 1 — Planning and Preparation

Define scope:
- **Analysis object:** component, subsystem, or system
- **Customer:** who is the next-level assembly? Who is the end user?
- **Boundary diagram:** what is inside and outside the DFMEA scope
- **Interface matrix:** what interacts with this component (mechanical, electrical, thermal, chemical)?

---

### Step 2 — Structure Analysis (Design Hierarchy)

Map the product hierarchy:

```
System (e.g., Steering Column)
└── Subsystem (e.g., Tilt Mechanism)
    └── Component (e.g., Pivot Pin)
        └── Interface (e.g., Pin-to-Bracket contact)
```

**Interface matrix:**
For each component, identify:
- Interfaces to other components (internal)
- Interfaces to the environment (external): heat, vibration, corrosion, electromagnetic
- Interfaces to the user or assembly process

Interfaces are where most design failures occur. Each interface must be analysed as a potential failure location in its own right — not just the components that share it. In practice, at least 50% of DFMEA effort should focus on interfaces and interactions; component-only analysis misses the most common field failure modes.

---

### Step 3 — Function Analysis

For each element in the structure, define its design function:

**Format:** Verb + Noun + Measurable Standard

Examples:
- Component function: "Transmit torque of 50 Nm ± 5 Nm without permanent deformation"
- Interface function: "Maintain sealing at pressure 2.5 bar across -40°C to +120°C"
- System function: "Provide steering angle feedback with latency < 50ms"

Identify **Special Characteristics** from the drawing — these get S = 9 or 10 in Step 5.

**Testability rule:** Every function must be measurable and verifiable — a test or analysis method must exist in the DVP. A function with no verification method cannot receive a credible D rating in Step 5.

---

### Step 4 — Failure Analysis

The failure chain for DFMEA: **Failure Effect → Failure Mode → Failure Cause**

**Failure Effect (FE):**
- End-user effect: safety hazard, loss of primary function, reduced performance
- Vehicle/system effect: damage to adjacent components, secondary failures
- Manufacturing effect (if component is not to spec): inability to assemble, rework

**Failure Mode (FM):**
How does this component fail to perform its design function?
- Fracture, wear, corrosion, deformation, signal loss, leakage, dimensional drift, electrical short/open

**Failure Cause (FC):**
What design parameter or design decision causes the failure mode?
- Insufficient material strength (wrong grade, wrong heat treat)
- Inadequate geometry (stress concentration, insufficient wall thickness)
- Thermal expansion mismatch
- Corrosion protection insufficient for environment
- Tolerance stack-up causing interference
- Interface design not accounting for assembly variation

**Failure Cause validation:** Failure Causes must be validated using engineering analysis (FEA, structural calculation, thermal simulation) or test evidence. Unverified assumptions — "probably," "likely," "may be" — are not acceptable as final Failure Causes. Use CAE (FEA, simulation), test data, and field return data to support both the failure modes identified and their causes. For post-field-failure DFMEA updates, the FC must match the validated root cause from the 8D or field investigation.

---

### Step 5 — Risk Analysis

Use the same S/O/D ratings and AP table as PFMEA (see [action-priority-ap](../action-priority-ap/) and [pfmea-process](../pfmea-process/) for the tables).

**Key DFMEA-specific notes:**

**Occurrence (O) in DFMEA** considers:
- Design maturity (new design = higher O)
- Similar design history (similar designs with this failure = higher O)
- Prevention controls: design reviews, CAE / FEA, DVP testing

**Detection (D) in DFMEA** considers:
- Design verification tests (DVP)
- Engineering analysis (FEA, simulation)
- Design reviews with checklists
- Prototype testing

D = 10 means no design verification for this failure mode. This is common for new features — it drives the DVP.

**Ratings justification:** All S/O/D ratings must be justified using analysis, test data, or design history. A rating without documented justification will not withstand OEM audit. Where design history exists from similar components, reference it explicitly. Where data is absent, mark O and D as preliminary and flag the DVP entry that will confirm them.

---

### Step 6 — Optimization

For H-AP items in DFMEA, actions typically fall into:

1. **Design change:** change geometry, material, tolerance, or coating
2. **Add design verification:** add DVP test entry to confirm the design meets the requirement
3. **Add prevention:** design guideline, DFM/DFA rule, standard reference
4. **Improve detection:** add inspection requirement to DVP or design review checklist

**DFMEA → DVP linkage:**
Every detection control (D rating improvement) must have a corresponding entry in the Design Verification Plan (DVP). If you improve D because "we will test it," the test must exist in the DVP.

**Action tracking:** All actions must be tracked to closure with objective evidence — test results, simulation output, or updated analysis. Actions marked "complete" without verification evidence are not acceptable. Open H-AP items past their target date must be escalated to the design review owner or programme manager, with a revised date and documented reason for delay.

---

### Step 7 — Results Documentation

DFMEA outputs that feed other APQP documents:
- **Special Characteristics** identified in DFMEA → transferred to Control Plan and PFMEA
- **Detection controls** → DVP entries
- **Interface failure modes** → PFMEA structure analysis inputs
- **Material / geometry requirements confirmed** → released drawing

## DFMEA → PFMEA handoff

The DFMEA and PFMEA are linked:

| DFMEA | → | PFMEA |
|-------|---|-------|
| Design Failure Effects (end-user impact) | → | Severity ratings in PFMEA |
| Special Characteristics | → | SC flagging in PFMEA process steps |
| Interface failure modes | → | PFMEA failure modes for assembly steps |
| Design intent (function) | → | Process step function requirements |

## Mandatory DFMEA review events (APQP / IATF 16949 §8.3)

| Trigger | Required action |
|---------|----------------|
| New product development | Start DFMEA at APQP Phase 2 — before design freeze. DFMEA initiated after freeze has no corrective value. |
| Engineering change request (ECR) | Review and update the DFMEA for all functions, failure modes, and interfaces affected by the change — before the change is released. |
| Design milestone / design review | Present DFMEA status: open H-AP items, actions, and revised ratings. DFMEA must be current at each gate. |
| Field failure with confirmed design root cause | Update FC, ratings, and actions to match validated root cause from 8D/field investigation. Update DVP to include the failure mode. |

A DFMEA that is not updated through the programme lifecycle is a design quality assurance gap — not a living document.

## Common mistakes

- **Starting DFMEA after design is frozen** — DFMEA has no value if no changes can be made
- **Only analysing the component, not the interfaces** — most design failures are interface failures
- **Improving D without adding DVP tests** — detection credit without actual testing
- **DFMEA and PFMEA teams working in silos** — they must share severity ratings and special characteristics

## Output Format

At the start of each use, ask the user:

> "How would you like to receive the output?
> **A** — Structured Markdown (formatted tables and sections, ready to copy)
> **B** — Plain tables (simplified structure for Excel or Word)
> **C** — Narrative report (flowing text for a formal document or email)
>
> Default: A."

Adapt all output sections to the chosen format. If the platform or session context already defines a format preference, skip this question.

## Reference files

- [Interface matrix construction guide](references/interface-matrix.md)

## Changelog

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-01 | @RBraga01 | Initial release |
| 1.1 | 2026-06-03 | @RBraga01 | Added interface matrix integration and DFMEA-to-PFMEA handoff workflow |
