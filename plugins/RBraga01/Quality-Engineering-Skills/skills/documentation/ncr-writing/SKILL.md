---
name: ncr-writing
description: >-
  Write a non-conformance report, NCR, reject a supplier, or document a defect with
  objective-evidence language and correct severity grading (Critical/Major/Minor). Covers
  disposition recommendations and segregation requirements for incoming inspection failures,
  in-process defects, customer returns, and audit findings.
license: MIT
metadata:
  author: RBraga01
  version: "1.1"
  iso-9001: "8.7"
  iatf-16949: "8.7.1"
  domain: quality-engineering
  subdomain: documentation
  industries: automotive,electronics,aerospace,medical,general
  status: approved
  created: "2026-06-01"
  last_updated: "2026-06-03"
  updated_by: migmcc
  reviewed_by: RBraga01
  standard_edition: "ISO 9001:2015"
---

# Non-Conformance Report (NCR) Writing

## When to use

Write an NCR whenever a product, material, or service does not conform to a specified requirement:

- Incoming inspection failure
- In-process defect found at any production step
- Final inspection rejection
- Customer return or field complaint
- Audit finding on a product characteristic

## The non-negotiable rule

**An NCR describes WHAT is wrong, not WHY.**

Root cause belongs in the CAPA / 8D. The NCR is the factual record of the non-conformance itself. Mixing root cause speculation into the NCR contaminates the record.

An NCR is a controlled quality record and may be used in audits, customer reviews, and legal contexts. All content must be objective and defensible.

## Required NCR Checklist

☐ Requirement clearly referenced (drawing/specification number and revision)
☐ Actual value or observed defect recorded with quantified measurement
☐ Gap between required and actual explicitly defined
☐ Evidence attached or referenced and traceable to this NCR
☐ Severity correctly classified — grade higher when in doubt
☐ Affected quantity and population at risk identified
☐ Material physically segregated and identified before NCR is closed
☐ Detection point reflects where the defect was found, not where it originated
☐ Disposition defined and approved by authorised personnel
☐ Containment actions documented with timestamps (if applicable)
☐ Language is objective — no subjective terms, no root cause, no opinion
☐ NCR traceable to production records, batch records, and inspection logs

---

## NCR structure

### 1. Header

| Field | Content |
|-------|---------|
| NCR number | Sequential, traceable |
| Date | Date of detection |
| Part number | Exact part number + revision |
| Part description | Name |
| Supplier / source | Supplier name + supplier code (for incoming) or line/station (for in-process) |
| Batch / lot | Traceability reference |
| Quantity affected | Non-conforming qty / total inspected |
| Detected by | Name + function |
| Detection point | Incoming / in-process station / outgoing / customer |

### 2. Non-conformance description

**Write like a measurement report, not a complaint.**

Required elements:

- What is the specified requirement? (drawing dimension, specification, standard)
- What was actually observed or measured? (actual value, description)
- What is the gap? (difference between required and actual)

Every NCR description must be independently understandable without additional explanation. Do not rely on attachments to complete the description.

**Good NCR description:**
> "Connector housing flange thickness measured at 1.8 mm ± 0.05 mm on 3 of 5 sampled units. Drawing specification: 2.2 mm ± 0.1 mm (ref. DWG-12345 rev B, detail B-3). Non-conformance: measured values 0.35–0.42 mm below lower specification limit."

**Bad NCR description (do not write):**
> "Parts are out of spec. The housing looks too thin and won't fit properly."

**Rules for the description:**

- Use numbers: actual value, specification value, tolerance, quantity
- Reference the requirement: drawing number + revision, specification number, purchase order
- Describe the physical observation: measured value, visual characteristic (location, extent, appearance)
- Avoid subjective language ("poor quality", "bad parts", "looks wrong") — use measurable and observable facts only
- Do NOT include hypotheses ("probably because…"), root cause, or blame

### 3. Objective evidence

List what evidence exists:

- Measurement records (gauge reading, CMM report, test result) — all evidence must be traceable to this NCR by ID or reference
- Photos (reference photo numbers or attach)
- Sample availability (samples retained: Yes/No, location)
- Batch / lot traceability (delivery note, batch record)

### 4. Severity classification

| Grade | Definition | Examples |
|-------|-----------|---------|
| **Critical** | Affects safety, regulatory compliance, or potential field failure that cannot be contained internally | Safety-related dimension OOS, regulatory label missing, electrical isolation failure, risk of harm to end user |
| **Major** | Affects form, fit, or function — customer will likely detect | Dimension preventing assembly, performance parameter below specification, missing required feature |
| **Minor** | Does not affect form, fit, or function — cosmetic or documentation | Surface scratch within defined limits, label position deviation, minor visual blemish |
| **OFI** | Observation for improvement — technically conforming but below best practice | (Used in audit context only, not for product NCRs) |

**When in doubt, grade higher.** It is easier to downgrade after review than to explain why a major issue was graded minor.

### 5. Affected quantity and segregation status

- How many units are affected? (inspected quantity, non-conforming quantity, population at risk)
- Where is the suspect material now? (on-hold location: shelf, bin, quarantine area)
- Has it been segregated? (Yes / No / In progress)
- Has it been identified? (red tag, quarantine label, system flag)

**Segregation must occur immediately upon detection, before NCR documentation is completed.**

**Any non-conforming material must be physically identified and segregated before the NCR is closed.**

### 6. Disposition

| Disposition | When to use |
|------------|-------------|
| **Use As Is (UAI)** | Non-conformance does not affect form, fit, function or safety — requires engineering approval with documented rationale |
| **Rework** | Non-conformance can be corrected to bring part into specification — specify rework method and re-inspection required |
| **Repair** | Non-conformance can be corrected, but result will not meet original specification — requires customer deviation approval if shipping to customer |
| **Return to Supplier (RTS)** | Incoming material non-conformance — returned with copy of NCR |
| **Scrap** | Cannot be reworked or repaired — irreversible disposal |

UAI requires documented approval with technical justification. Never approve UAI verbally.

Disposition must be approved by authorised personnel per the defined approval matrix.

### 7. Immediate containment (if applicable)

If suspect material may have already passed to a downstream process or customer:

- List containment actions taken (sort, inspection, ship-hold) — all actions must be time-stamped and traceable
- Reference the 8D / CAPA initiated (if applicable)

---

## Output format — example NCR

```
NCR-2026-0047
Date: 2026-05-28 | Part: 12345-B | Lot: 2026-05-12-A | Qty: 47/200 = 23.5%
Detection: Incoming inspection | Supplier: ABC Electronics

NON-CONFORMANCE:
Connector pin insertion depth measured at 3.8–4.1 mm on 47 of 200 sampled units.
Specification: 5.0 ± 0.3 mm (DWG-12345 rev B, detail C-1).
Non-conformance: 0.6–1.5 mm below lower limit on 23.5% of sampled parts.

EVIDENCE:
Measurement records: Sheet INS-2026-0047 (caliper, calibration cert. 2026-03-01)
Photos: NCR-2026-0047-Photo-01 to 05
Samples retained: 5 units, quarantine bin QA-07

SEVERITY: Major — connector will not achieve full mating depth, risking intermittent
electrical contact failure at the assembly stage.

SEGREGATION: 200 sampled units on hold, quarantine bin QA-07.
Remaining units in delivery note 55512 (1,500 units) on ship-hold pending 100% sort.

DISPOSITION: Return to Supplier pending investigation.
Immediate containment: 100% incoming inspection of remaining 1,500 units.
```

## Common mistakes

- **"Parts are bad"** — too vague; always give measured values vs. specification
- **Root cause in the description** — "caused by incorrect tooling setting" → remove from NCR, goes in 8D D4
- **Missing traceability** — no batch or lot number makes containment impossible
- **Incorrect severity grade** — failing to grade Critical when safety is at risk
- **UAI without engineering approval** — verbal approval is not acceptable
- **Not segregating before writing the NCR** — segregation must happen immediately, before the paperwork
- **Subjective language** — "poor quality", "bad supplier", "looks wrong" — use objective, measurable facts

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

- [NCR template](assets/ncr-template.md)

## Changelog

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-01 | @RBraga01 | Initial release |
| 1.1 | 2026-06-03 | @migmcc | Expanded severity classification criteria and disposition guidance |
