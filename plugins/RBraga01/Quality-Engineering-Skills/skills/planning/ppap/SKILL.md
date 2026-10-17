---
name: ppap
description: >-
  Production Part Approval Process (PPAP) — verify PPAP submission level, audit all 18 elements,
  check completeness for customer approval, prepare PSW. Use when a supplier needs to submit parts
  for approval, when reviewing a PPAP package, or when determining which PPAP level is required.
  Covers AIAG PPAP 4th edition with Ford, BMW, VW, and Stellantis OEM-specific requirements.
license: MIT
metadata:
  author: RBraga01
  version: "1.1"
  iso-9001: "8.4"
  iatf-16949: "8.3.4, 8.4.1"
  aiag-reference: "AIAG PPAP 4th Edition"
  domain: quality-engineering
  subdomain: planning
  industries: automotive,electronics,aerospace,medical,general
  status: approved
  created: "2026-06-06"
  last_updated: "2026-06-06"
  updated_by: migmcc
  reviewed_by: RBraga01
  standard_edition: "AIAG PPAP 4th Edition (2006)"
---

# Production Part Approval Process (PPAP)

## When to use

Use this skill when:
- A supplier must submit parts for customer approval before Start of Production (SOP)
- A design change, process change, or engineering change requires re-submission
- An OEM or Tier 1 customer requests a PPAP at a specific level
- Reviewing or auditing an incoming PPAP package from a supplier
- Determining what PPAP level is required for a given change

## Prerequisites

- Part number, revision level, and customer drawing
- Bill of Materials (BOM) if applicable
- Production process flow and manufacturing location confirmed
- Customer's PPAP level requirement (Level 1–5) or change category known

## Workflow

### Step 1 — Determine the PPAP Level

| Level | What must be submitted |
|-------|----------------------|
| 1 | Part Submission Warrant (PSW) only — no supporting documents unless requested |
| 2 | PSW + designated samples + limited supporting data |
| 3 | PSW + product samples + complete supporting data (default for new parts) |
| 4 | PSW + other requirements as defined by the customer |
| 5 | PSW + parts and complete supporting data — reviewed at the supplier's manufacturing location |

**Default:** Level 3 for new parts or significant changes. Always confirm with the customer before submitting.

### Step 2 — Identify the change category

PPAP re-submission is required for:
- New part or product
- Engineering change (design revision)
- Change of supplier (sub-supplier, raw material)
- Change of manufacturing location, process, or tooling
- Change that affects fit, form, or function
- Corrective action following a field failure or customer complaint
- Production interruption >12 months

### Step 3 — Prepare all 18 PPAP elements

**Production trial run minimum:** Unless otherwise specified in writing by the authorised customer representative, the production trial run must consist of a **minimum of 300 consecutive parts** produced at the production rate, using production tooling, production process, production operators, and production tooling (AIAG PPAP 4th ed §4.0). This run generates the PPAP samples (Element 14), dimensional results (Element 9), and capability data (Element 11). A run shorter than 300 consecutive parts requires explicit written customer authorisation before PSW can be signed.

Verify each element against the level requirement. For Level 3 (default):

**Element 1 — Design Records**
- Customer drawing (latest revision, stamped/approved)
- Math data if applicable (3D model)
- All referenced specifications

**Element 2 — Engineering Change Documents**
- Approved change documentation (ECN, SREA, or equivalent)
- Required only if an authorized engineering change is in process

**Element 3 — Customer Engineering Approval**
- Written approval from customer engineering (if design is customer-owned)
- Engineering sign-off or deviation/waiver reference number

**Element 4 — DFMEA**
- Customer-approved Design FMEA (if design is supplier-responsible)
- Review all H-AP items for completion before submission

**Element 5 — Process Flow Diagram**
- Sequence of all operations from incoming material to shipment
- Includes: incoming inspection, all process steps, sub-supplier operations, final inspection, packaging

**Element 6 — PFMEA**
- Process FMEA aligned to the Process Flow
- All H-AP items must have completed actions before PPAP
- Reviewed and signed off by responsible engineer

**Element 7 — Control Plan**
- Covers all phases: Prototype, Pre-launch, and Production
- Linked to PFMEA failure modes and controls
- Includes: characteristics, measurement method, sample size/frequency, reaction plan

**Element 8 — Measurement System Analysis (MSA)**
- Gauge R&R study for each measurement system used on special and significant characteristics
- Acceptance criteria: %GRR < 10% preferred, <30% conditional
- Number of distinct categories (ndc) ≥ 5

**Element 9 — Dimensional Results**
- Balloon drawing with all dimensions/tolerances numbered
- Measurement results for each ballooned characteristic
- Minimum 5 parts per cavity/spindle; identify each part
- All results must be within specification (100% conforming for PPAP)

**Element 10 — Material Performance Test Results**
- Functional and durability test results per customer/engineering specification
- Test reports from customer-approved laboratories
- All tests passed with certificate of conformance

**Element 11 — Initial Process Studies (Statistical)**
- Capability studies for all special characteristics (Sc, CC, SC)
- Minimum Cpk ≥ 1.67 preferred; ≥ 1.33 minimum acceptable
- If Cpk < 1.33: customer-approved control plan with 100% inspection required

**Element 12 — Qualified Laboratory Documentation**
- Test reports must be from accredited laboratories (ISO/IEC 17025 preferred)
- In-house labs: scope of accreditation must cover the tests performed

**Element 13 — Appearance Approval Report (AAR)**
- Required only for appearance-critical parts
- Customer sign-off on colour, grain, gloss, and appearance attributes

**Element 14 — Sample Production Parts**
- Minimum 1 sample part per cavity/spindle/die
- From the submission run (not prototype or off-tool samples unless Level 1 or 2)
- Labelled with part number, revision, and date

**Element 15 — Master Sample**
- One signed-off sample retained at the supplier as a reference standard
- Signed by supplier and customer (if required)

**Element 16 — Checking Aids**
- Gauges, fixtures, and check tools used for dimensional verification
- Calibration records for all checking aids
- MSA results for all variable gauges on special characteristics

**Element 17 — Customer-Specific Requirements**
- OEM-specific PPAP requirements (see OEM section below)
- CSR compliance checklist if required

**Element 18 — Part Submission Warrant (PSW)**
- One PSW per part number per submission
- Must be signed by the authorised quality manager
- Submission reason, specification level, and change description completed

### Step 4 — OEM-specific requirements

**Ford:**
- Ford-specific PSW form (not generic AIAG form)
- SREA (Supplier Request for Engineering Approval) for design changes
- ISIR (Initial Sample Inspection Report) may be required
- Ford CSR compliance statement on PSW

**BMW:**
- Form 1410 (Erstmusterprüfbericht / Initial Sample Inspection Report)
- VDA 6.3 process audit may be required before PPAP
- G8D report if PPAP follows a concern

**Volkswagen / Audi:**
- PPF (Produktionsprozess und Produktfreigabe) — VW's PPAP equivalent
- QMSS portal submission required
- Audit of production process mandatory for new parts

**Stellantis:**
- STELLANTIS PPAP requirements per CSR (Customer Specific Requirements)
- Supplier Quality Assurance (SQA) portal submission
- PFMEA must follow AIAG-VDA 2019 format

### Step 5 — PSW Completion and Submission

Complete the PSW accurately:
- Submission reason must match the change category
- Specification level (Level 1–5) confirmed with customer
- All 18 elements checked as complete (or N/A with justification)
- Signed by Quality Manager (not just coordinator)
- Submit through the customer's designated portal or APQP contact

## Validation criteria

Before submitting PPAP:
- All dimensional results 100% within specification
- Cpk ≥ 1.67 for all special characteristics (or documented deviation with customer approval)
- %GRR < 30% for all measurement systems on special characteristics
- All H-AP items in PFMEA have completed actions
- Control Plan covers all special and significant characteristics
- Test reports from accredited labs with pass status
- PSW signed by Quality Manager

## Common mistakes

- Submitting with any out-of-specification dimensional result (automatic rejection)
- Using prototype or pre-production samples for PPAP (must be from production tooling)
- Production trial run shorter than 300 consecutive parts without written customer authorisation — automatic rejection at many OEMs
- Cpk calculated on insufficient data (minimum 100 pieces for capability study)
- MSA not performed for all gauges used on special characteristics
- PFMEA not updated after process changes made during PPAP run
- PSW signed by someone without authority (Quality Manager signature required)
- Submitting Level 3 without retaining a master sample
- Generic AIAG PSW form submitted to Ford (requires Ford-specific form)

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
| 1.1 | 2026-06-06 | @migmcc | Added 300-part production trial run minimum (AIAG PPAP 4th ed §4.0); added to Common Mistakes |
