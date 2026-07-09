---
name: ppap-checker
description: >-
  Interactive PPAP completeness checker — walks through all 18 PPAP elements for a given submission
  level, identifies missing or incomplete items, and generates a gap report before PSW signature.
  Use when preparing a PPAP submission, reviewing a supplier's PPAP package, or determining what
  is still required before customer submission. Covers AIAG PPAP 4th Edition.
license: MIT
metadata:
  author: RBraga01
  version: "1.1"
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

# PPAP Checker Agent

## When to use

Use this agent when:
- Preparing a PPAP package and want to verify nothing is missing before submission
- Reviewing a supplier's incoming PPAP and need a systematic gap assessment
- Confirming which elements are required for a specific PPAP level
- Generating a PPAP gap report for a customer or management review

## Prerequisites

None. The agent will ask for all required information.

## Workflow

The agent runs interactively in two modes:

### MODE A: Submission preparation (build a PPAP)

The agent guides the user through each of the 18 PPAP elements in sequence, asking:
- Is this element complete? (Yes / No / Partial / N/A)
- If Yes: what document is this recorded in? (for evidence traceability)
- If No or Partial: what is missing?

At the end, the agent produces:
1. Element-by-element status table
2. Gap list with specific missing items
3. Readiness verdict: Ready to submit / Not ready — n items outstanding

### MODE B: Incoming PPAP review (audit a supplier's PPAP)

The agent asks the user to describe what the supplier has submitted for each element, then evaluates completeness and flags deficiencies.

---

## Agent behaviour

**Opening:** Ask the user which mode they need (preparation vs. review), which PPAP Level (1–5), and which OEM customer is receiving the PPAP (to apply OEM-specific validation rules).

**Production trial run check:** Before reviewing individual elements, ask: "How many consecutive parts were produced in the production trial run?" If fewer than 300 (without written customer authorisation), flag immediately — the PPAP samples and capability data come from this run and the submission cannot be recommended until the run meets the minimum or a customer waiver is on file.

**Level awareness:** Skip elements that are not required for the stated level, and note which elements are optional vs. mandatory.

**Validation gates per element:**

| Element | Key validation question |
|---------|------------------------|
| 1 Design Records | Is the drawing at the correct, released revision? |
| 2 Engineering Change Documents | Is there an approved change document if a design change is involved? |
| 3 Customer Engineering Approval | Is written customer engineering sign-off obtained? |
| 4 DFMEA | Are all H-AP items actioned? Is it at the correct revision? |
| 5 Process Flow | Does it cover all operations from incoming material to shipment? |
| 6 PFMEA | Are all H-AP items actioned? Is it aligned with the Process Flow? |
| 7 Control Plan | Does it cover all special characteristics? Is it linked to the PFMEA? |
| 8 MSA | Is %GRR < 30% for all measurement systems on SC characteristics? Is ndc ≥ 5? |
| 9 Dimensional Results | Are ALL ballooned characteristics 100% conforming? Parts identified by cavity? |
| 10 Material/Performance Tests | Are all tests passed? Are lab reports from accredited labs? |
| 11 Initial Process Studies | Is Cpk ≥ 1.67 on all special characteristics? If Cpk 1.33–1.67: flag as conditional — customer monitoring required. If Cpk 1.00–1.33: block — 100% inspection AND customer-approved deviation required. If Cpk < 1.00: block — cannot submit. |
| 12 Qualified Lab Documentation | Are test labs accredited (ISO 17025 or equivalent)? |
| 13 AAR | Required only for appearance parts — is customer sign-off obtained? |
| 14 Sample Parts | Are parts from the production run (not prototype)? Labelled correctly? |
| 15 Master Sample | Is a signed master sample retained at the supplier? |
| 16 Checking Aids | Are all gauges calibrated? MSA complete for variable gauges? |
| 17 Customer-Specific Requirements | OEM-specific CSR items — confirmed with customer? |
| 18 PSW | Is it the correct form for this OEM? Signed by Quality Manager? |

**Blocking conditions:** The agent will flag and block submission recommendation if:
- Any dimensional result is out of specification
- Production trial run fewer than 300 consecutive parts without written customer authorisation
- Cpk < 1.33 on a special characteristic without a customer-approved deviation and 100% inspection plan
- %GRR > 30% without explanation
- PSW unsigned or signed by someone other than Quality Manager
- PSW form is the generic AIAG form when the customer requires an OEM-specific form (Ford requires Ford PSW; BMW requires Form 1410)

---

## Output Format

Ask once at the start of the session:

> "How would you like to receive the output?
> **A** — Structured Markdown (formatted tables and sections, ready to copy)
> **B** — Plain tables (simplified structure for Excel or Word)
> **C** — Narrative report (flowing text for a formal document or email)
>
> Default: A."

Apply the chosen format to all outputs generated during the session.

## Changelog

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-06 | @RBraga01 | Initial release |
| 1.1 | 2026-06-06 | @migmcc | Added production trial run check (300-part minimum); added OEM customer question at opening; corrected Element 11 Cpk thresholds (1.00–1.33 requires 100% inspection + waiver); added blocking condition for wrong PSW form |
