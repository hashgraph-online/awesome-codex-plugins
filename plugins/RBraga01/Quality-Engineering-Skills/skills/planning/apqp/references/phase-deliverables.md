---
name: phase-deliverables
type: reference
parent_skill: apqp
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-06"
last_updated: "2026-06-06"
updated_by: migmcc
reviewed_by: RBraga01
license: MIT
---

# APQP Phase Deliverables — Complete Reference

Complete deliverables per phase with roles, timing, gate criteria, common gaps, and APQP-to-PPAP cross-reference.
Use alongside the [apqp](../SKILL.md) skill.

> **Scope:** This document covers the exhaustive deliverable list per APQP phase, responsible party, timing relative to SOP, gate review checklists, common deliverable gaps that cause PPAP failure, and the cross-reference mapping each APQP output to its corresponding PPAP element. For the phase-by-phase workflow and gate criteria, see [apqp SKILL.md](../SKILL.md).

---

## 1. Phase 1 — Plan and Define Program

**Timing:** Complete 18–24 months before SOP (programme kickoff to design release kickoff)

| Deliverable | Responsible | Customer / Supplier / Joint | Notes |
|-------------|-------------|----------------------------|-------|
| Voice of the Customer (VOC) | Customer + Supplier | Joint | Translated to measurable technical requirements; must cover QFD inputs if applicable |
| Design Goals | Supplier (design-responsible) / Customer | Joint | Performance targets, tolerance targets, Cpk goals — must be quantified |
| Reliability and Quality Goals | Supplier | Supplier | Warranty targets (e.g., B10 life), PPM goals, field failure rate target |
| Preliminary Bill of Materials (BOM) | Supplier | Supplier | Draft BOM from design intent; identifies sub-suppliers and commodity risks |
| Preliminary Process Flow | Supplier | Supplier | High-level sequence — not a detailed operation-by-operation flow |
| Preliminary Special Characteristics | Joint | Joint | Initial list of SC/CC/KPC — will be refined through Phases 2 and 3 |
| Product Assurance Plan | Supplier | Supplier | Programme quality plan: milestones, resources, risk register, test strategy |
| Programme Timing Plan | Joint | Joint | APQP milestone timeline tied to SOP; must include all PPAP milestones |
| Feasibility Commitment | Supplier | Supplier | Formal sign-off that the design is technically and commercially feasible |
| Management Support / Programme Charter | Joint | Joint | Executive sign-off on resources, budget, and programme scope |

**Gate 1 checklist:** See Section 3.

---

## 2. Phase 2 — Product Design and Development

**Timing:** 12–15 months before SOP (design release to process design kickoff)

| Deliverable | Responsible | Customer / Supplier / Joint | Notes |
|-------------|-------------|----------------------------|-------|
| Design FMEA (DFMEA) | Supplier (design-resp.) / Customer | Supplier or Joint | AIAG-VDA format preferred; all H-AP items addressed before gate |
| Design Verification Plan (DVP&R) | Supplier | Supplier | Linked to DFMEA failure modes; every H-AP must have a test |
| Engineering Drawings — Released | Customer / Supplier | Joint | Formally released drawings with tolerances; 3D model issued |
| Material Specifications | Supplier | Supplier | Raw material specs confirmed; sub-supplier list initiated |
| Prototype Control Plan | Supplier | Supplier | Describes controls for prototype builds — not reused for production |
| New Equipment and Tooling — Identified | Supplier | Supplier | Capital expenditure plan; long-lead items ordered |
| Updated Special Characteristics List | Joint | Joint | SC/CC/KPC confirmed from design detail; drawing symbols applied |
| Gauge Plan (MSA Requirement List) | Supplier | Supplier | Lists every characteristic requiring an MSA study and the gauge type |
| Prototype Build Completion | Supplier | Joint | Prototypes built, tested, results reviewed — DVP tests on prototypes executed |
| Prototype Test Results | Supplier | Joint | Pass/Fail results from prototype-phase DVP tests; failures trigger DFMEA updates |
| Engineering Drawing and Spec Changes | Joint | Joint | Change management process active; ECN/SREA log maintained |

**Gate 2 checklist:** See Section 3.

---

## 3. Phase 3 — Process Design and Development

**Timing:** 8–10 months before SOP (process design through tooling qualification)

| Deliverable | Responsible | Customer / Supplier / Joint | Notes |
|-------------|-------------|----------------------------|-------|
| Detailed Process Flow Chart | Supplier | Supplier | Operation-by-operation; includes inspection steps, rework paths; feeds PFMEA |
| Manufacturing Floor Plan Layout | Supplier | Supplier | Material flow, ergonomics, access confirmed; approved by plant management |
| Characteristics Matrix | Supplier | Supplier | Links each process step to the product characteristics it affects |
| Process FMEA (PFMEA) | Supplier | Supplier | AIAG-VDA format; all H-AP items closed before pre-launch; feeds Control Plan |
| Pre-Launch Control Plan | Supplier | Supplier | Stricter sample sizes than production CP; 100% inspection common at this stage |
| Process Instructions / Work Instructions | Supplier | Supplier | Step-by-step operator instructions for all operations; tied to Control Plan |
| MSA Plan | Supplier | Supplier | Identifies which gauges require GR&R; assigns responsibility and schedule |
| Preliminary Process Capability Study Plan | Supplier | Supplier | Documents how the Cpk study will be run: n, characteristics, method |
| Packaging Standards — Design | Supplier | Joint | Packaging design approved; MMOG/LE materials flow if required |
| Packaging Specifications | Joint | Joint | Final packaging specs including OEM-specific label requirements |
| Product / Process Quality System Review | Customer | Joint | Internal quality system audit against customer IATF/VDA requirements |
| Tooling and Equipment — Qualified | Supplier | Supplier | All production tooling installed and run-off at supplier; acceptance criteria met |

**Gate 3 checklist:** See Section 3.

---

## 4. Phase 4 — Product and Process Validation

**Timing:** 3–6 months before SOP (significant production run through PPAP approval)

| Deliverable | Responsible | Customer / Supplier / Joint | Notes |
|-------------|-------------|----------------------------|-------|
| Significant Production Run (Trial Run) | Supplier | Supplier | Minimum run size as agreed with customer; typically ≥ 300 pieces or customer-defined |
| MSA Studies (Gauge R&R) | Supplier | Supplier | GR&R completed for all SC/CC/KPC gauges; must meet %GRR < 30% |
| Process Capability Studies (Cpk) | Supplier | Supplier | From significant production run; Cpk ≥ 1.67 target for all SC/CC |
| Production Control Plan | Supplier | Joint | Final production CP; supersedes Pre-Launch CP; submitted as PPAP Element 7 |
| PPAP Package (all 18 elements) | Supplier | Supplier | Complete submission; see ppap SKILL.md for element details |
| Production Validation Testing (PVT) | Supplier / Customer | Joint | Final DVP tests on production parts; all tests must show Pass |
| Packaging Evaluation | Supplier | Supplier | Production packaging validated (drop test, transit test, OEM label verification) |
| Quality Planning Sign-Off | Joint | Joint | Customer PPAP approval; APQP completion confirmed |
| Management Support Sign-Off | Supplier | Supplier | Internal executive approval to begin SOP shipments |

**Gate 4 checklist (= PPAP approval criteria):** See Section 3.

---

## 5. Phase 5 — Feedback, Assessment and Corrective Action

**Timing:** SOP onward — no end gate; runs for the life of the programme

| Activity | Responsible | Frequency |
|----------|-------------|-----------|
| Process capability monitoring (SPC) | Supplier quality | Ongoing — per Control Plan frequency |
| Control Plan updates (post-SOP issues) | Supplier quality | After any quality escape, corrective action, or PFMEA update |
| PFMEA updates (warranty / field data) | Supplier engineering + quality | Quarterly review minimum; after any warranty claim |
| Customer scorecard review | Supplier quality | Monthly or per customer rhythm |
| Lessons learned capture | APQP team | At SOP and at programme end |
| Warranty and field return analysis | Supplier engineering | Per warranty cycle (monthly / quarterly) |
| OTD and logistics performance review | Supplier logistics | Monthly |

---

## 6. Gate Review Checklists

### Gate 1 — End of Phase 1

| Check | Pass Condition |
|-------|---------------|
| Customer requirements documented | VOC captured in measurable technical targets; signed off by both parties |
| Feasibility confirmed | Formal feasibility commitment signed by supplier; no open technical blockers |
| Preliminary BOM issued | All major components identified; sub-supplier strategy confirmed |
| Special characteristics — preliminary list | At least a draft list exists; all high-risk characteristics flagged |
| Programme timing plan | APQP milestone plan issued; PPAP submission date confirmed with customer |
| Management resources committed | People, equipment budget, and capital approved |
| No open feasibility blockers | No unresolved "cannot meet" items — all risks have mitigation plans |

### Gate 2 — End of Phase 2

| Check | Pass Condition |
|-------|---------------|
| DFMEA complete | All failure modes analysed; H-AP items have completed actions with evidence |
| DVP issued and execution started | All H-AP failure modes have at least one test; prototype-phase tests underway |
| Drawings released | Formal release; all referenced specs issued; revision-controlled |
| Special characteristics finalised | SC/CC/KPC confirmed and applied to drawing with correct symbols |
| Prototype build results acceptable | No unresolved failures from prototype DVP tests |
| Gauge plan complete | All characteristics requiring MSA identified; gauge procurement started |
| No blocking design concerns | No open DRB (Design Review Board) action items without an owner and due date |

### Gate 3 — End of Phase 3

| Check | Pass Condition |
|-------|---------------|
| Process Flow Chart complete | All operations documented; numbering matches PFMEA and CP |
| PFMEA complete | All operations covered; H-AP actions closed; reviewed and signed off |
| Pre-launch Control Plan approved | All SC/CC present; sample plan defined; reaction plans complete |
| Process instructions complete | Work instructions for every operation; linked to CP rows |
| MSA plan confirmed | Gauge R&R schedule locked; gauges procured or on order |
| Tooling and equipment qualified | All production tooling installed; first-off-tool parts approved |
| Packaging approved | Packaging design signed off; OEM label format confirmed |
| No open blocking issues | All action items from process FMEA review closed or formally accepted |

### Gate 4 — PPAP Approval (End of Phase 4)

| Check | Pass Condition |
|-------|---------------|
| Significant production run complete | Minimum agreed quantity produced from production tooling at production conditions |
| Dimensional results 100% conforming | Zero out-of-tolerance results across all ballooned dimensions, all sampled parts |
| Cpk ≥ 1.67 for all SC/CC | Or customer-approved formal deviation with agreed containment |
| MSA %GRR < 30% for all SC/CC gauges | Preferably < 10%; 10–30% requires customer concurrence |
| All DVP tests passed | Zero open failures; any failures resolved with DFMEA update and re-test |
| PPAP package complete | All 18 elements present, accepted, and documented |
| Customer PPAP approval received | Written approval (email, portal status, PSW stamp) — not verbal confirmation |
| No open customer concerns | No outstanding 8D, deviation, or corrective action from Phase 4 |

---

## 7. Common Deliverable Gaps That Cause PPAP Failure

| Gap | Phase where it originates | Effect at PPAP |
|-----|--------------------------|----------------|
| Special characteristics not identified in Phase 1/2 | Phase 1–2 | SC/CC missing from Control Plan and PFMEA — PPAP Elements 6 and 7 incomplete |
| DVP not aligned to DFMEA | Phase 2 | H-AP failure modes have no test coverage — PPAP Element 10 fails audit |
| PFMEA created after process is running | Phase 3 | PFMEA is documenting the process, not driving controls — detection controls in PFMEA do not match actual Control Plan |
| Pre-launch CP used as Production CP | Phase 4 | Control Plan submitted to PPAP is not the production-level document — rejected |
| MSA studies not completed before PPAP run | Phase 4 | Capability data (Cpk) is from an unvalidated measurement system — invalid |
| Capability study run on pre-production parts | Phase 3–4 | Cpk calculated from parts not produced at production tooling conditions — not valid for PPAP Element 11 |
| Lessons learned not captured (Phase 5 skipped) | Phase 5 | Same PPAP gaps repeat on subsequent programmes; no institutional memory |
| Prototype CP not replaced by Production CP | Phase 3–4 | PPAP Element 7 shows prototype-level controls only — missing production-specific controls and frequencies |
| Gauge plan not executed — MSA missing for some characteristics | Phase 2–3 | Some SC/CC have no MSA — PPAP Element 8 incomplete |
| Packaging specs not finalised before PPAP run | Phase 3–4 | Production parts shipped in uncertified packaging — PPAP package incomplete |

---

## 8. APQP Deliverable to PPAP Element Cross-Reference

| APQP Deliverable | APQP Phase | PPAP Element |
|------------------|-----------|-------------|
| Engineering Drawings — Released | 2 | Element 1 — Design Records |
| Engineering Change Documents | 2–3 | Element 2 — Engineering Change Documents |
| Customer Engineering Approval (design sign-off) | 2 | Element 3 — Customer Engineering Approval |
| DFMEA | 2 | Element 4 — DFMEA |
| Detailed Process Flow Chart | 3 | Element 5 — Process Flow Diagram |
| PFMEA | 3 | Element 6 — PFMEA |
| Production Control Plan | 4 | Element 7 — Control Plan |
| MSA Studies (Gauge R&R) | 4 | Element 8 — Measurement System Analysis |
| Dimensional Results (from PPAP run) | 4 | Element 9 — Dimensional Results |
| Production Validation Testing (DVP&R results) | 4 | Element 10 — Material / Performance Test Results |
| Process Capability Studies (Cpk from PPAP run) | 4 | Element 11 — Initial Process Studies |
| Lab Documentation (ISO/IEC 17025 certs) | 4 | Element 12 — Qualified Laboratory Documentation |
| Appearance Approval (customer AAR sign-off) | 2–4 | Element 13 — Appearance Approval Report |
| Significant Production Run — sample parts | 4 | Element 14 — Sample Production Parts |
| Master Sample retention | 4 | Element 15 — Master Sample |
| Gauge Plan → gauges procured and calibrated | 3–4 | Element 16 — Checking Aids |
| CSR Compliance / OEM-specific requirements | 1–4 | Element 17 — Customer-Specific Requirements |
| Quality Planning Sign-Off + Management Support Sign-Off | 4 | Element 18 — Part Submission Warrant (PSW) |

**Note:** Element 18 (PSW) is the culmination of the entire APQP programme — it can only be signed when all prior deliverables are complete and accepted. The PSW signature is the quality manager's attestation that the APQP process was followed.
