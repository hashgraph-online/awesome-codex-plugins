---
name: supplier-scar
description: >-
  Supplier Corrective Action Request (SCAR) — escalate a supplier non-conformance to a formal
  corrective action request, define response requirements, evaluate the supplier's 8D response,
  and verify effectiveness. Use when an NCR escalates to a SCAR, when a supplier delivers
  repeated non-conformances, or when a field failure is traced to a supplier. Covers ISO 9001 §8.4
  and IATF 16949 §8.4.1.
license: MIT
metadata:
  author: RBraga01
  version: "1.1"
  iso-9001: "8.4, 10.2"
  iatf-16949: "8.4.1, 10.2.3"
  domain: quality-engineering
  subdomain: supplier-quality
  industries: automotive,electronics,aerospace,medical,general
  status: approved
  created: "2026-06-06"
  last_updated: "2026-06-06"
  updated_by: migmcc
  reviewed_by: RBraga01
  standard_edition: "ISO 9001:2015 §8.4 / IATF 16949:2016 §8.4.1"
---

# Supplier Corrective Action Request (SCAR)

## When to use

Use this skill when:
- A supplier NCR requires a formal corrective action (beyond simple return/replacement)
- A supplier has delivered the same non-conformance twice or more
- A non-conformance has caused a production line stoppage, customer complaint, or field failure
- A supplier's quality performance score falls below the defined threshold
- An OEM customer issues a concern that is traced to a sub-supplier
- Preparing a SCAR, evaluating a supplier's 8D response, or conducting an effectiveness review

## Prerequisites

- Non-conformance documented (NCR or equivalent) with: part number, description, quantity, measured evidence
- Supplier code, contact name, and corrective action coordinator identified
- SCAR response timeline agreed (typically 24h for D3, 30 days for full 8D)
- Historical data: previous SCARs, PPM trend, quality score for this supplier

## Workflow

### Step 1 — Escalation criteria: when does an NCR become a SCAR?

Issue a SCAR when any of the following conditions are met:

| Trigger | Description |
|---------|-------------|
| Severity — Critical | Non-conformance affects safety, regulatory compliance, or field function |
| Severity — Customer impact | Non-conformance reached the end customer or caused a production line stop |
| Recurrence | Same defect or same part rejected for the second time within 12 months |
| Volume | Rejection of an entire lot or >5% of a delivery |
| Systemic risk | Evidence that the supplier's process or system is inadequate (missing controls, no inspection, operator error on SC characteristic) |
| Customer escalation | An OEM customer has issued a concern traceable to this supplier |

Do NOT issue a SCAR for every NCR — use NCR + return for minor first-occurrence issues and reserve SCAR for systemic or high-risk situations.

---

### Step 2 — Write the SCAR

The SCAR document must contain:

**Header:**
- SCAR number (unique, traceable)
- Date issued
- Supplier name, supplier code, contact person
- Issued by (supplier quality engineer name)

**Non-conformance description:**
- Part number and revision
- Delivery reference (PO number, lot number, delivery note)
- Quantity delivered / quantity non-conforming / % affected
- Defect description in objective-evidence language (measured values vs. specification — not opinions)
- Customer impact (if applicable): production stop, customer complaint, field return
- Reference to the NCR (attach or link)

**Response requirements:**
Specify exactly what the supplier must provide and by when:

| Deliverable | Typical deadline |
|-------------|-----------------|
| D3 Immediate Containment Action (ICA) | 24–48 hours |
| D4 Root Cause (occurrence AND escape) | 7–14 days |
| D5–D6 Permanent Corrective Actions with evidence | 30 days |
| D7 Systemic prevention (PFMEA, CP, WI updates) | 30 days |
| Full 8D report | 30 days |

Always require TWO root causes: why the defect was produced (occurrence) AND why it was not detected (escape).

**Containment verification:**
State that the supplier must confirm:
- All suspect stock at their facility has been identified and quarantined
- All stock in transit has been recalled or placed on hold
- All stock at your facility has been segregated (include quantity)
- A containment verification plan is in place before any further shipments are accepted

---

### Step 3 — Evaluate the supplier's 8D response

Use the 8D Evaluator methodology (skill: `8d-problem-solving`) to review the supplier's response. Focus on the most common SCAR-specific failures:

**D3 — Containment:**
- Is the containment in PAST TENSE? (If it says "we will inspect going forward" — reject)
- Does it cover all locations (supplier, transit, your facility, customer)?
- Is there a verification result (quantity sorted, quantity rejected, quantity cleared)?

**D4 — Root cause:**
- Are BOTH causes identified: occurrence (why produced) AND escape (why not caught)?
- Is the root cause supported by evidence, or is it opinion?
- Reject: "human error", "operator oversight", "customer changed specs" — always ask why it was possible
- Verify: if the supplier claims "operator error", ask why the error was not detected by the control plan

**D5 — Permanent corrective action:**
- Does the PCA directly address the confirmed root cause?
- Is "retrain the operator" the only action? If so, reject — training is not a systemic fix
- Is there a poka-yoke or process change that makes the defect impossible or immediately detectable?

**D7 — Systemic prevention:**
- Has the PFMEA been updated to reflect the failure mode and new controls?
- Has the Action Priority (AP) been revised in the PFMEA after verified corrective action? The revised AP must be lower than the original or documented with justification — AP revision is only valid after D6 effectiveness is confirmed, not at planning stage.
- Has the Control Plan been updated?
- Have Work Instructions been updated?
- Has horizontal deployment been considered (same process at other lines/plants)?

**D6 — Verification:**
- Is there production data showing the PCA is effective?
- What quantity was run? Over what period?
- What is the measured improvement (before/after comparison)?

---

### Step 4 — Issue a SCAR response rejection

If the supplier's 8D response does not meet the gate criteria, reject it formally:

**Rejection notice must specify:**
- Which discipline(s) failed and why (specific, not generic)
- What is required in the revised response
- Revised deadline for resubmission

Do not accept a response that:
- Has no evidence of D3 completion (only a plan)
- States "human error" as the final root cause without systemic analysis
- Lists only training as the PCA
- Has no PFMEA or CP update in D7
- Shows no production data in D6

---

### Step 5 — Effectiveness verification

30–90 days after PCA implementation, verify that the corrective action is effective:

**Methods:**
- Monitor incoming quality data: zero recurrence of the same defect in the next X deliveries
- Review updated PFMEA and Control Plan (request current revision, verify D4 failure mode is addressed)
- On-site verification: audit the specific process step where the defect occurred (use VDA 6.3 P6 questions for that step)
- Request production data showing Cpk improvement on the relevant characteristic

**Close the SCAR when:**
- Zero recurrence of the same non-conformance for the agreed monitoring period (typically 3–6 months)
- Updated PFMEA, CP, and WI documents received and verified
- Effectiveness data reviewed and accepted

**If recurrence occurs during monitoring:**
- Escalate to supplier management (not just quality coordinator)
- Consider: production stop, new supplier qualification, customer notification
- Issue a new SCAR referencing the previous one as evidence of systemic failure

---

### Step 6 — Supplier performance tracking

Link every SCAR to the supplier's quality performance record:
- PPM trend (Parts Per Million non-conforming)
- SCAR open count and average response time
- Closure rate (closed on time vs. overdue)
- Recurrence rate (same defect within 12 months of a previous SCAR)

Suppliers with repeated SCARs or recurrences should be placed on:
- **Controlled shipping** — every delivery inspected before acceptance (in automotive: CS1 = supplier-managed 100% sort; CS2 = customer-managed sort at supplier's cost)
- **Supplier improvement plan** — formal APQP-style corrective programme
- **Qualification review** — potential re-qualification or replacement

**Warranty cost recovery / debit note risk:** In automotive OEM supply chains, SCARs that result in field failures or warranty claims can trigger financial recovery. The OEM issues a warranty debit note to the Tier 1, who cascades it to the responsible sub-supplier via SCAR. Each SCAR must therefore document whether the non-conformance caused any field or warranty cost — this determines whether cost recovery applies. A SCAR without this assessment is incomplete for OEM reporting purposes. If warranty cost recovery is raised, escalate immediately to commercial and legal before responding to the OEM.

---

## Validation criteria

A SCAR is closed when:
- Full 8D submitted with both root causes confirmed (occurrence AND escape)
- Permanent corrective action verified with production data (D6)
- PFMEA, Control Plan, and Work Instructions updated and received (D7)
- No recurrence of the same non-conformance during the agreed monitoring period
- Closure signed off by Supplier Quality Engineer and documented in the supplier record

## Common mistakes

- Issuing a SCAR for every NCR — dilutes the severity signal; suppliers stop taking SCARs seriously
- Accepting a D3 response that is a plan ("we will inspect") rather than a completed action
- Closing the SCAR when the 8D is submitted rather than when effectiveness is verified
- Accepting "human error" or "operator training" without requiring a systemic root cause
- Not updating the supplier performance record — next engineer doesn't know the history
- Allowing the SCAR to stay open indefinitely with no escalation — sets the precedent that deadlines are negotiable

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
| 1.1 | 2026-06-06 | @migmcc | Added AP revision check in D7 evaluation; added warranty cost recovery / debit note risk in Step 6; added CS1/CS2 controlled shipping reference |
