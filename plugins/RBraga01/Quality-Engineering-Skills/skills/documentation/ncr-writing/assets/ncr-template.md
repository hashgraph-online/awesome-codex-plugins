---
name: ncr-template
type: asset
parent_skill: ncr-writing
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-01"
last_updated: "2026-06-03"
updated_by: migmcc
reviewed_by: RBraga01
license: MIT
---

# NCR Template — Non-Conformance Report

**Instructions:** Fill every mandatory field. Leave no field blank — write "N/A" with a reason
if a field genuinely does not apply. NCR language must be objective: what is measured, what the
specification requires, and what the deviation is. Do not include root cause, opinion, or hypothesis.

This document is a controlled quality record and must be completed with accurate, traceable, and auditable information. It may be reviewed by customers, auditors, or in legal proceedings.

**Template version:** v1.1

---

## NCR Completion Checklist

☐ All header fields completed (no blanks)
☐ Requirement, actual value, and deviation clearly defined in the description
☐ Description is independently understandable without relying on attachments
☐ Evidence attached and traceable to this NCR
☐ Severity selected and justified with one sentence
☐ All affected material identified and physically segregated before continuing
☐ Stock status fully defined — including shipped and in-transit quantities
☐ Disposition defined and approved by authorised personnel
☐ CAPA/8D triggered if severity = Critical or Major
☐ NCR reviewed and approved before closure
☐ All entries traceable to production, inspection, and logistics records

---

## HEADER

| Field | Value |
|-------|-------|
| **NCR Number** | (assigned by quality system) |
| **Date issued** | YYYY-MM-DD |
| **Issued by** | Name, function |
| **Part number** | — |
| **Part name / description** | — |
| **Revision / drawing number** | — |
| **Supplier / source** | (supplier name and code, or internal department) |
| **Customer (if applicable)** | — |
| **Plant / site** | — |
| **Purchase order / job number** | — |
| **Batch / lot number** | — |
| **Serial numbers** | (if serialised — list or range) |
| **Delivery date** | YYYY-MM-DD |
| **Detection point** | ☐ Incoming inspection ☐ In-process ☐ Final inspection ☐ Customer |
| **Quantity received** | — |
| **Quantity inspected** | — |
| **Quantity non-conforming** | — |
| **Non-conformance rate** | — % |

---

## NON-CONFORMANCE DESCRIPTION

**State WHAT is wrong. Use measured values and specification references. No root cause, no opinion.**

The description must be understandable without reviewing attachments. Include all critical data inline.

### Defect description

_Template:_
> "[Feature / characteristic] measured [measured value] [unit] on [sample reference].
> Specification requires [specification value ± tolerance] [unit] per [drawing / standard reference].
> Deviation: [deviation amount] [unit] [over/under] the [upper/lower] limit."

_Example:_
> "Pin insertion force measured at 48 N (sample 12 of 50). Work instruction WI-047 Rev C requires
> insertion force of 22–30 N. Deviation: 18 N over the upper limit."

**Description:**

[Write here]

---

### Photographic evidence

| Reference | Description |
|-----------|------------|
| Photo 1 | |
| Photo 2 | |
| Measurement record | |
| Other | |

---

### Specification reference

| Document | Revision | Clause / dimension |
|----------|----------|-------------------|
| Drawing | | |
| Work instruction | | |
| Customer specification | | |
| Standard | | |

---

### Measurement equipment

| Equipment | Calibration status | Calibration certificate ref |
|-----------|-------------------|-----------------------------|
| | | |

---

## SEVERITY CLASSIFICATION

Select one:

| Severity | Criteria | Selected |
|----------|---------|---------|
| **Critical** | Safety hazard, regulatory non-compliance, or potential field failure that cannot be contained internally | ☐ |
| **Major** | Customer (external or internal) will detect — functional failure, dimensional out of spec | ☐ |
| **Minor** | Customer may detect — cosmetic, workmanship, not affecting function | ☐ |
| **OFI** | Observation for improvement — no non-conformance, audit finding only | ☐ |

**Severity justification:**
[One sentence explaining why this severity level was chosen]

**If Critical is selected:** Immediately escalate to quality management. Do not wait for NCR completion before escalating.

---

## IMMEDIATE SEGREGATION

**Mandatory before continuing.**

| Action | Completed | Date | Time (HH:MM) | By whom |
|--------|-----------|------|--------------|---------|
| Non-conforming stock physically segregated | ☐ | | | |
| Red tag / hold label applied | ☐ | | | |
| System hold placed (ERP / WMS) | ☐ | | | |
| Shipment blocked (if applicable) | ☐ | | | |
| Customer notified (if escaped) | ☐ | | | |

**Location of segregated stock:**
[Building / area / rack / bin / system hold reference]

---

## STOCK STATUS

| Category | Quantity | Location |
|----------|----------|---------|
| Confirmed non-conforming | | |
| Under investigation (suspect) | | |
| Confirmed conforming | | |
| Already shipped to customer | | |
| In transit | | |
| **Total population at risk** | | |

---

## PROPOSED DISPOSITION

Select and complete the applicable disposition. Each requires specific approvals.

**Disposition approval authority:** [Reference to approval matrix or name the authorised function]

### Use As Is

- Requires: written technical justification + quality manager approval + customer approval (if SC affected)
- Justification: [why the non-conformance does not affect form, fit, or function]

### Rework

- Requires: rework method documented, re-inspection criteria defined
- Rework method: [specific steps — not "fix it"]
- Re-inspection method: [what, how many, acceptance criteria]
- Responsible: [name + function]
- Target completion: YYYY-MM-DD

### Repair

- Requires: customer deviation / concession approved before repair begins
- Deviation reference: [customer approval number / date]
- Repair method: [specific steps]

### Return to Supplier

- Requires: supplier notification, RMA number
- RMA reference: [number]
- Return shipping date: YYYY-MM-DD

### Scrap

- Requires: quality manager approval; confirmation of destruction
- Scrapping method: [shredding / crushing / marked and binned]
- Destruction confirmed by: [name + date]

**Selected disposition:** [Use As Is / Rework / Repair / Return / Scrap]

---

## CUSTOMER IMPACT

| Field | Value |
|-------|-------|
| Customer impact known | ☐ Yes ☐ No ☐ Under investigation |
| Customer impact description | |
| Customer notified | ☐ Yes ☐ No ☐ N/A |
| Notification date / reference | |

---

## APPROVALS

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Quality engineer (issuer) | | | |
| Quality manager | | | |
| Production manager (if applicable) | | | |
| Customer representative (if applicable) | | | |

Electronic approval allowed: ☐ Yes ☐ No (system reference: _____________)

---

## ESCALATION TO CAPA / 8D

**If severity = Critical or Major, a Corrective Action (CAPA) or 8D is required.**

| Field | Value |
|-------|-------|
| CAPA / 8D required | ☐ Yes ☐ No |
| If No — reason why not required | |
| CAPA / 8D reference number | |
| Assigned to | |
| Target closure date | YYYY-MM-DD |

---

## CLOSURE

| Field | Value |
|-------|-------|
| Disposition completed | ☐ Yes |
| Re-inspection passed | ☐ Yes ☐ N/A |
| Re-inspection record reference | |
| Verification of effectiveness | ☐ Yes ☐ N/A (reference: _____________) |
| NCR closed by | |
| Closure date | YYYY-MM-DD |

---

## LANGUAGE GUIDE — DO / DO NOT

| Write this | Not this |
|-----------|---------|
| "Dimension X measured 23.5 mm; specification 25.0 ± 0.5 mm" | "Part is out of spec" |
| "47 of 200 parts inspected were non-conforming (23.5%)" | "Several parts were rejected" |
| "Non-conformance detected at incoming inspection on 2026-05-14" | "Quality is bad" |
| "Connector pin 3 bent 15° from nominal" | "Part looks wrong" |
| "Batch 2026-05-10 to 2026-05-15 suspect" | "Some batches" |
| **DO NOT include:** root cause, hypothesis, opinion, who is to blame | |
| **DO NOT include:** future actions (those go in CAPA/8D) | |
| **DO NOT use:** "poor quality", "bad supplier", "unacceptable" — use measured facts | |
