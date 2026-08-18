---
name: dvp-test-plan
description: >-
  Design Verification Plan and Report (DVP&R) — build or review a test plan that links each DFMEA
  failure mode to a specific test, pass/fail criterion, sample size, and timing. Use when creating
  a DVP for a new design, reviewing a supplier's DVP for completeness, or auditing whether all
  design risks are covered by validation testing. Covers IATF 16949 §8.3.4.3 and AIAG APQP Phase 2.
license: MIT
metadata:
  author: RBraga01
  version: "1.1"
  iso-9001: "8.3.4"
  iatf-16949: "8.3.4.3"
  domain: quality-engineering
  subdomain: planning
  industries: automotive,electronics,aerospace,medical,general
  status: approved
  created: "2026-06-06"
  last_updated: "2026-06-06"
  updated_by: migmcc
  reviewed_by: RBraga01
  standard_edition: "IATF 16949:2016 §8.3.4.3 / AIAG APQP 2nd Edition"
---

# Design Verification Plan and Report (DVP&R)

## When to use

Use this skill when:
- Creating a DVP for a new part design during APQP Phase 2
- Reviewing a supplier's DVP for completeness and DFMEA alignment
- Determining which tests are required for a specific failure mode or design characteristic
- Tracking test completion and recording results (the "R" in DVP&R)
- Assessing whether a design change requires additional validation testing

## Prerequisites

- DFMEA with all failure modes identified and AP ratings assigned
- Engineering drawing with all characteristics defined
- Customer design specifications and performance requirements
- List of applicable standards and test methods (customer spec, ISO, SAE, etc.)

## Workflow

### Step 1 — Understand the DVP structure

The DVP&R is a table with one row per test. Each test must address at least one failure mode or design characteristic from the DFMEA.

**The linkage rule:** Every H-AP (High Action Priority) failure mode in the DFMEA must have at least one corresponding test in the DVP. If a failure mode has no test, document why (e.g., analysis-only justification with sign-off).

### Step 2 — Build each DVP row

| Column | What to enter |
|--------|--------------|
| Test number | Sequential reference (e.g., DVP-001) |
| DFMEA reference | Failure mode number(s) this test addresses |
| Test name / description | Specific name of the test (not "durability test" — use "salt spray 240h per ASTM B117") |
| Test specification | Standard or specification number with version (e.g., ASTM B117-19, SAE J2530, customer spec DS-XYZ) |
| Pass/fail criteria | Exact acceptance criteria (e.g., "no rust after 240h", "burst pressure > 150 bar", "dimension within ±0.05 mm") |
| Sample size | Number of parts to test |
| Who performs | Internal lab, external accredited lab, customer lab |
| Phase | P = Prototype, PL = Pre-launch, PR = Production |
| Planned date | Date test is scheduled to complete |
| Actual date | Date test was completed |
| Result | Pass / Fail / In progress |
| Report reference | Lab report number or document reference |
| Comments | Failures, deviations, re-test requirements |

### Step 3 — Determine required tests

For each DFMEA failure mode, identify the test category:

**Functional / performance tests:**
- Tests that verify the product performs its intended function
- Examples: burst pressure, tensile strength, electrical resistance, flow rate
- Must demonstrate the product meets its design intent specifications

**Environmental / durability tests:**
- Tests that simulate the product's operating environment over its design life
- Examples: thermal cycling, salt spray, vibration, UV exposure, humidity
- Duration and cycles must represent the design life or accelerated equivalent

**Safety / regulatory tests:**
- Tests required by law, regulation, or homologation
- Examples: ECE R10 (EMC), FMVSS standards, ECE R94/R95 (crash), REACH, RoHS
- Must be performed by accredited lab; results must accompany PPAP

**Dimensional / material tests:**
- Verification that design dimensions and material properties are achieved
- Examples: 3D scan, CMM, tensile test, hardness test, chemical composition
- Must reference the specific drawing characteristic or material specification

**Reliability / life tests:**
- Tests that verify the product meets its reliability target (e.g., B10 life)
- Examples: fatigue testing, accelerated aging, wear testing
- Test plan must include correlation between accelerated test and field life

### Step 4 — Populate timing per APQP phase

| Phase | Tests due |
|-------|-----------|
| Prototype (P) | Tests on design concept — functional, dimensional, preliminary environmental |
| Pre-launch (PL) | Tests on tooled parts — full environmental, durability, all safety/regulatory |
| Production (PR) | Confirmation tests on production parts — dimensional, safety, any tests with production-specific requirements |

Not all tests need to run in all phases. Focus safety and regulatory tests on Pre-launch or Production parts.

### Step 5 — Track completion (the "R" in DVP&R)

Update the DVP after each test:
- Record actual completion date
- Record Pass/Fail result
- For any Fail: log a DFMEA action (or open an 8D if failure escapes to customer)
- Re-test after corrective action — reference the re-test as a new row with the original DVP number + suffix (e.g., DVP-012-R1)

At PPAP submission: all DVP tests must show "Pass" or have a documented customer-approved deviation. If a test is still in progress at PPAP submission (e.g., a long-duration life test), a formal customer deviation request must be submitted with: the test in progress, the expected completion date, the interim risk assessment, and the customer's written acceptance. The PPAP approval will be conditional until the test completes with a Pass result.

**Engineering changes:** If the DFMEA is updated during the design phase and adds new H-AP failure modes, the DVP must be updated to cover them before the next gate review. A DVP revision that is behind the current DFMEA revision is a gap — the DVP&R revision must match or exceed the DFMEA revision at PPAP submission.

### Step 6 — Audit an existing DVP

When reviewing a supplier's or internal DVP, check:

- [ ] Every H-AP DFMEA failure mode has at least one corresponding test
- [ ] Test specifications reference a specific standard or document (not "internal test")
- [ ] Pass/fail criteria are objective and measurable (not "acceptable appearance")
- [ ] Sample sizes are adequate (not "1 sample" for durability/life tests)
- [ ] Safety and regulatory tests are assigned to an accredited external lab
- [ ] All results show "Pass" (or documented deviations with customer approval)
- [ ] Failed tests have a corresponding DFMEA update or corrective action reference
- [ ] DVP revision is aligned with the current DFMEA revision

## Validation criteria

A complete DVP&R for PPAP submission must:
- Reference every H-AP failure mode from the DFMEA
- Have specific, standard-referenced test methods (not "per engineering judgement")
- Show Pass results for all tests (or customer-approved deviations)
- Have accredited lab reports for all safety/regulatory tests
- Be signed off by design engineering and quality

## Common mistakes

- DVP created with generic tests not linked to specific DFMEA failure modes
- Pass/fail criteria defined as "meets spec" without stating what the spec is
- All tests assigned to internal lab when regulatory tests require external accreditation
- DVP not updated when DFMEA adds new H-AP failure modes during design reviews
- Re-tests after failures not documented — original Fail result erased
- Sample size of 1 for durability or life tests (statistically meaningless)
- DVP not updated to "Report" status at PPAP — submitted as plan, not results

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
| 1.1 | 2026-06-06 | @migmcc | Added guidance for tests in-progress at PPAP submission (customer deviation process); added DVP revision synchronisation with DFMEA requirement |
