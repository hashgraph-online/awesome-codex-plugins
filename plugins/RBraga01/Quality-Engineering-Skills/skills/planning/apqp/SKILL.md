---
name: apqp
description: >-
  Advanced Product Quality Planning (APQP) — plan and track a new product launch through all 5 phases,
  identify deliverables per phase, run gate reviews, and ensure quality outputs are complete before
  Start of Production (SOP). Use when launching a new part, managing an APQP project, or auditing
  APQP completeness. Covers AIAG APQP 2nd edition and IATF 16949 §8.3.
license: MIT
metadata:
  author: RBraga01
  version: "1.1"
  iso-9001: "8.3"
  iatf-16949: "8.3"
  aiag-reference: "AIAG APQP 2nd Edition"
  domain: quality-engineering
  subdomain: planning
  industries: automotive,electronics,aerospace,medical,general
  status: approved
  created: "2026-06-06"
  last_updated: "2026-06-06"
  updated_by: migmcc
  reviewed_by: RBraga01
  standard_edition: "AIAG APQP 2nd Edition (2008) / IATF 16949:2016 §8.3"
---

# Advanced Product Quality Planning (APQP)

## When to use

Use this skill when:
- A new product or part is being launched and a structured quality plan is needed
- Managing an APQP project and tracking deliverables across phases
- Conducting an APQP gate review to assess launch readiness
- A customer requests an APQP status report or phase completion confirmation
- Auditing whether a supplier's APQP process is adequate

## Prerequisites

- Customer requirements, specifications, and drawings (or RFQ package)
- Programme timing (SOP date, PPAP submission date, prototype gates)
- Nominated APQP team (cross-functional: engineering, quality, purchasing, manufacturing, logistics)
- Customer APQP template if OEM-specific format required

## Workflow

### Overview — The 5 APQP Phases

```
Phase 1          Phase 2          Phase 3          Phase 4          Phase 5
Plan & Define → Product Design → Process Design → Product & Process → Feedback &
                & Development   & Development      Validation         Corrective Action
     ↓               ↓               ↓                ↓                  ↓
  Program         Prototype       Pre-launch         PPAP              SOP +
  approval         build           build           submission          Production
```

All phases run with concurrent engineering — phases overlap and teams work in parallel.

---

### Phase 1 — Plan and Define Program

**Objective:** Understand customer requirements and define what the product must do.

**Key deliverables:**

| Deliverable | Description |
|-------------|-------------|
| Voice of the Customer (VOC) | Customer wants, needs, expectations — translated to measurable requirements |
| Design Goals | Product performance targets derived from VOC |
| Reliability and Quality Goals | Target failure rate, warranty targets, Cpk targets |
| Preliminary Bill of Materials | Draft BOM from design intent |
| Preliminary Process Flow | High-level process sequence |
| Preliminary Special Characteristics | Initial list of critical/significant characteristics |
| Product Assurance Plan | Quality plan for the programme |
| Management Support | Signed-off programme charter with resources and timing |

**Gate 1 pass criteria:**
- Customer requirements documented and agreed
- Feasibility confirmed (technical and commercial)
- Team chartered and timing plan approved
- Special characteristics list preliminary but complete

---

### Phase 2 — Product Design and Development

**Objective:** Translate customer requirements into a product design with verified characteristics.

**Key deliverables:**

| Deliverable | Description |
|-------------|-------------|
| DFMEA | Design FMEA — all failure modes analysed, H-AP items addressed |
| Design Verification Plan (DVP) | Test plan linked to DFMEA failure modes |
| Drawing and Specification Release | Fully released engineering drawings and 3D data |
| Material Specifications | Raw material specs, supplier approval plan |
| Drawing and Specification Changes | Change management process in place |
| New Equipment and Tooling | List of new equipment/tooling required |
| Special Product and Process Characteristics | Updated with design detail |
| Gauge Plan | MSA requirement list — which characteristics need MSA studies |
| Prototype Control Plan | Control plan for prototype builds |
| Prototype Build | Prototype parts manufactured and tested |
| Engineering Drawings | Released and approved |

**Gate 2 pass criteria:**
- DFMEA complete with all H-AP actions closed
- DVP complete and test execution started
- Prototype build results acceptable
- All special characteristics identified and confirmed
- No outstanding major design concerns

---

### Phase 3 — Process Design and Development

**Objective:** Design and verify the manufacturing process.

**Key deliverables:**

| Deliverable | Description |
|-------------|-------------|
| Packaging Standards | Packaging design, labelling, MMOG/LE if required |
| Product/Process Quality System Review | Internal quality system audit against customer requirements |
| Process Flow Chart | Detailed process flow for all operations |
| Floor Plan Layout | Manufacturing floor layout approved |
| Characteristics Matrix | Matrix linking process steps to product characteristics |
| PFMEA | Process FMEA — all failure modes, AP ratings, H-AP actions complete |
| Pre-Launch Control Plan | Control plan for pre-launch production |
| Process Instructions | Work instructions for all operations |
| MSA Plan | Gauge R&R plan for all measurement systems |
| Preliminary Process Capability Study Plan | Plan for capability studies on special characteristics |
| Packaging Specifications | Final packaging specs including OEM labelling |

**Gate 3 pass criteria:**
- PFMEA complete, H-AP actions closed or formally accepted
- Pre-launch Control Plan approved
- Process instructions complete for all operations
- Tooling and equipment installed and qualified
- No unresolved open issues blocking pre-launch build

---

### Phase 4 — Product and Process Validation

**Objective:** Validate the production process and prepare for PPAP submission.

**Key deliverables:**

| Deliverable | Description |
|-------------|-------------|
| Production Trial Run | Significant Production Run (minimum run to PPAP requirements) |
| MSA Studies | Gauge R&R completed for all special characteristics |
| Preliminary Process Capability | Cpk study on special characteristics (target ≥ 1.67) |
| Production Part Approval (PPAP) | All 18 PPAP elements complete and submitted |
| Production Validation Testing | Final validation tests on production parts |
| Packaging Evaluation | Production packaging validated |
| Production Control Plan | Final production control plan approved |
| Quality Planning Sign-Off | Customer approval of PPAP and APQP completion |
| Management Support Sign-Off | Internal management approval for SOP |

**Gate 4 pass criteria (= PPAP approval):**
- Significant production run completed (minimum 300 consecutive parts per AIAG PPAP 4th ed §4.0, unless the customer specifies otherwise in writing)
- Dimensional results 100% conforming
- Cpk ≥ 1.67 on all special characteristics (or customer-approved deviation)
- %GRR < 30% for all MSA studies
- PPAP submitted and customer approval received
- No open concerns from validation testing

---

### Phase 5 — Feedback, Assessment and Corrective Action

**Objective:** Continuous improvement after SOP — close the loop on any issues found in production.

**Key activities:**

| Activity | Description |
|----------|-------------|
| Reduced variation | Monitor process capability, reduce common-cause variation |
| Improved customer satisfaction | Track warranty, field returns, and customer scorecards |
| Improved delivery and service | Monitor OTD (on-time delivery) and logistics performance |
| Lessons learned | Document lessons learned for future programmes |
| Control Plan updates | Update based on production data and any quality escapes |
| PFMEA updates | Update based on field failures and warranty data |

**Phase 5 is ongoing.** There is no defined end gate — it runs for the life of the programme.

---

### APQP timing — rule of thumb

| Milestone | Typical timing before SOP |
|-----------|--------------------------|
| Programme approval / Phase 1 complete | 18–24 months |
| Design release / Phase 2 complete | 12–15 months |
| Process design complete / Phase 3 complete | 8–10 months |
| PPAP submission | 4–6 months |
| PPAP approval (customer) | 3–4 months |
| Pre-production builds | 2–3 months |
| SOP | 0 |

Automotive OEM programmes vary — always confirm with the customer's APQP coordinator.

## Validation criteria

At each gate review, verify:
- All deliverables for the phase are complete (not "in progress")
- No open H-AP items in DFMEA or PFMEA without approved actions
- No outstanding design or process concerns without a documented resolution plan
- Team sign-off obtained from all functions (quality, engineering, manufacturing, purchasing)
- Customer confirmation received before advancing to next phase

Gate reviews are STOP gates — do not advance until all criteria are met.

## Common mistakes

- Starting Phase 2 before customer requirements are fully understood and documented (Phase 1 incomplete)
- PFMEA created after process is already running — it must drive process design, not document it
- Production trial run shorter than 300 consecutive parts without written customer authorisation — the PPAP samples must come from this run; a shorter run requires an explicit customer waiver
- Capability studies run on off-tool or pre-production parts — must be from production tooling
- Prototype Control Plan used for PPAP submission — production control plan must be separate
- MSA studies done after PPAP submission — must be complete before PSW is signed
- Phase 5 never started — APQP is treated as "done" at SOP rather than as a continuous loop
- Lessons learned not captured — same problems recur on next programme

## Output Format

At the start of each use, ask the user:

> "How would you like to receive the output?
> **A** — Structured Markdown (formatted tables and sections, ready to copy)
> **B** — Plain tables (simplified structure for Excel or Word)
> **C** — Narrative report (flowing text for a formal document or email)
>
> Default: A."

Adapt all output sections to the chosen format. If the platform or session context already defines a format preference, skip this question.

## Changelog

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-06 | @RBraga01 | Initial release |
| 1.1 | 2026-06-06 | @migmcc | Added 300-part production trial run minimum to Gate 4 criteria and Common Mistakes |
