---
name: hypothesis-elimination
type: reference
parent_skill: is-is-not-scoping
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-06"
last_updated: "2026-06-06"
updated_by: RBraga01
reviewed_by: RBraga01
license: MIT
---

# Hypothesis Elimination — Is/Is-Not Reference

Structured logic for generating, testing, and eliminating hypotheses using the Is/Is-Not matrix.
Use alongside the [is-is-not-scoping](../SKILL.md) skill.

> **Scope:** This document covers the hypothesis tracking table template, elimination logic, a worked end-to-end example, how to write a verified problem statement after elimination, and how to transition from Is/Is-Not into 5-Why or Fishbone. For the Is/Is-Not matrix construction workflow and fact-gathering discipline, see [is-is-not-scoping SKILL.md](../SKILL.md).

---

## Hypothesis Tracking Table Template

Use one row per hypothesis. Complete the Outcome column only after testing against all five Is/Is-Not dimensions.

| # | Hypothesis | What | Which | Where | When | How many | Outcome | Eliminating entry |
|---|---|---|---|---|---|---|---|---|
| H1 | [Hypothesis statement] | Consistent / Contradicts / Unknown | Consistent / Contradicts / Unknown | Consistent / Contradicts / Unknown | Consistent / Contradicts / Unknown | Consistent / Contradicts / Unknown | ELIMINATED / SURVIVES / PARTIAL | [Dimension + specific entry that eliminates, if applicable] |
| H2 | | | | | | | | |
| H3 | | | | | | | | |

**Minimum three hypotheses required.** Fewer than three indicates premature narrowing — generate more before testing any.

**Column guidance:**

- **Consistent** — the hypothesis can explain this IS or IS-NOT observation without modification
- **Contradicts** — the hypothesis cannot explain this observation; it predicts a different result
- **Unknown** — data for this dimension is not yet available; mark the cell, do not leave it blank, and record what investigation is needed

A single "Contradicts" entry is sufficient to eliminate a hypothesis, unless the contradiction can be explained by a modifying condition (e.g., sampling limitation). Document any modifying conditions explicitly — do not use them to avoid elimination.

---

## Elimination Logic

### What a distinction is

A **distinction** is the specific IS/IS-NOT contrast that a hypothesis cannot explain. A valid distinction has two properties:

1. The hypothesis predicts a different result for this dimension than what the IS/IS-NOT matrix records
2. The distinction is based on a documented fact, not an assumption

**Examples of valid distinctions:**

- Hypothesis: "All material from supplier X is non-conforming." Distinction: "IS NOT — Batches from supplier X delivered before 2026-04-15 showed 0 defects in 1,200 parts inspected. If all material from supplier X were non-conforming, we would expect defects in those batches too."
- Hypothesis: "The inspection gauge is out of calibration." Distinction: "IS NOT — Defect was found at the customer's incoming inspection, not at our outgoing inspection. If our gauge were reading incorrectly, we would not have shipped 0 defectives in the previous 3 months of 100% outgoing inspection."
- Hypothesis: "Operator skill is the cause." Distinction: "IS — Defect is present across all three shifts, including automated operations. If this were operator-dependent, we would expect it to be absent during automated shift."

### What does NOT constitute a valid elimination

- "The team believes this cause is unlikely" — opinion without data
- "We have never seen this before" — absence of prior experience is not data
- "This would be expensive to investigate" — cost does not affect logical validity
- A contradiction based on an assumption in the IS column — if the IS entry is itself an assumption, the elimination is invalid

### Partial survival — when a hypothesis is not fully eliminated

A hypothesis **partially survives** when it is consistent with some dimensions but contradicts one or more others. Options:

1. **Modify the hypothesis** — narrow its scope to make it consistent with all dimensions (e.g., change "all supplier X material" to "supplier X material from the revised process introduced 2026-04-16")
2. **Hold for further data** — if the contradicting dimension has an Unknown entry, gather data before deciding
3. **Split the hypothesis** — if the original hypothesis actually contains two distinct claims, separate them and test each independently

---

## Worked Example: Is/Is-Not to Hypothesis Elimination

### Scenario

A Tier 1 automotive electronics supplier receives a customer complaint: bent connector pins on part number ECU-4472 rev C. The customer found 47 defective units in a delivery of 200 pieces.

### Completed Is/Is-Not Matrix (facts only)

| Dimension | IS | IS NOT |
|---|---|---|
| What | Connector pin bent (pin 3 only, lateral deflection 12–18°) | Other pins bent; housing cracked; solder joint failure; any electrical defect |
| Which | Part number ECU-4472 rev C; production batches W18 and W19 2026 | ECU-4472 rev B; ECU-4471 (same connector, different PCB); batches W16 and W17 |
| Where | Found at customer incoming inspection, Germany Plant | Found at our outgoing inspection (0 defectives in 100% inspection); at Plant B customer |
| When | First reported 2026-05-08 for batches shipped 2026-04-28 to 2026-05-02; all shifts | Before W18 production (zero complaints for ECU-4472 in prior 6 months) |
| How many | 47/200 (23.5%) in affected batches; consistent rate across W18 and W19 | Any defects in W16 or W17 (0/600 inspected by customer) |

**Key clue:** Rate is stable at ~23.5% across two batches; confined to pin 3 only; appeared at batch W18 onset; not detected at our 100% outgoing inspection.

### Hypotheses Generated

**H1:** The connector housing supplier changed the pin material or geometry in batch W18, causing pin 3 to be more susceptible to deflection during transit.

**H2:** A new packing configuration was introduced for the W18 shipment that allows pin 3 to contact the tray during vibration in transit.

**H3:** Our outgoing inspection gauge for this feature failed or is insufficiently sensitive to detect the 12–18° deflection.

**H4:** A process change at our assembly station (crimping jig or insertion force) was introduced between W17 and W18 that deforms pin 3 during assembly.

**H5:** The defect occurs at the customer's incoming unpacking process, not in our production or transit.

### Hypothesis Testing

| # | Hypothesis | What | Which | Where | When | How many | Outcome | Eliminating entry |
|---|---|---|---|---|---|---|---|---|
| H1 | Supplier material/geometry change at W18 | Consistent (pin 3 only could relate to positional characteristic) | Consistent (batch boundary matches W18) | Consistent | Consistent (onset at W18) | Consistent (~23.5% stable rate) | **SURVIVES** | — |
| H2 | New packing configuration causing transit damage | Consistent | Consistent (W18 boundary) | Consistent (found at customer) | Consistent | Partially — 23.5% is high for random transit damage | **PARTIAL** | How many: random transit contact would produce lower, variable rate |
| H3 | Outgoing inspection gauge failure | Consistent (defect escaped) | Consistent | **Contradicts** — if gauge failed, we'd expect escapes on other part numbers too; no other complaints received | Partially consistent | Consistent | **ELIMINATED** | Where: "IS NOT — found at our outgoing inspection" combined with 100% inspection means our gauge passed these parts; if gauge failed, rate would not be batch-specific |
| H4 | Assembly process change at W18 (crimping jig) | Consistent (pin 3 specific — jig feature) | Consistent (batch boundary W18) | **Partially** — consistent with escaping outgoing inspection if deformation is at or near limit | Consistent (onset W18) | Consistent (stable ~23.5%) | **SURVIVES** | — |
| H5 | Damage at customer unpacking | Consistent | **Contradicts** — damage would not be batch-specific; W16/W17 same unpacking process | Contradicts (would be found equally at all deliveries) | Contradicts (would not have a batch onset) | Contradicts (rate would vary by unpacking event) | **ELIMINATED** | Which: "IS NOT — W16 and W17 unaffected"; When: no onset pattern |

### Investigation Priority After Elimination

Surviving: H1 (supplier change), H4 (assembly jig change). Partial: H2 (packing — low priority).

**Next actions:**
1. Request supplier change notification log for W18 raw material
2. Review internal ECO log for assembly station changes between W17 and W18
3. Retrieve crimping jig maintenance and calibration records for the period
4. Retain sample parts from W18 for CMM measurement of pin 3 geometry

---

## Writing a Verified Problem Statement After Elimination

After elimination, surviving hypotheses must be distinguished from the problem statement. The problem statement describes what IS known from evidence. Surviving hypotheses are what will be investigated next.

### Formula

> "On [part number + revision], [defect description with measurement] was found [where] affecting [quantity/rate] of [which batches]. The defect first appeared [when]. Investigation has confirmed [any confirmed facts from elimination]. Hypotheses under active investigation: [H1 and H4]. The following have been eliminated with evidence: [H3 — gauge failure eliminated by X; H5 — unpacking damage eliminated by Y]."

### Worked example (from above)

> "On ECU-4472 rev C, connector pin 3 was found laterally deflected 12–18° at customer incoming inspection (Germany Plant), affecting 23.5% (47/200) of units in batches W18 and W19 shipped 2026-04-28 to 2026-05-02. No defects were found in batches W16 or W17 (0/600 units). The defect was not detected at our 100% outgoing inspection. Active hypotheses: (H1) supplier pin material or geometry change at W18; (H4) assembly crimping jig change between W17 and W18. Eliminated: (H3) outgoing gauge failure — contradicted by batch-specific escape pattern and no other part number complaints; (H5) customer unpacking damage — contradicted by batch onset and zero rate in W16/W17 under identical handling."

**Rules for the problem statement:**
- Contains only documented facts — no hypothesis language ("may have been," "probably," "we think")
- Eliminates ambiguity in quantity (specific count and rate, not "several" or "some")
- Names the active hypotheses explicitly so the next investigator knows where to focus
- Names the eliminated hypotheses with their contradiction so they are not re-opened without new evidence

---

## Transition from Is/Is-Not to 5-Why or Fishbone

### When to go to 5-Why directly

Use 5-Why directly when:
- Only one or two hypotheses survive and they are specific and mechanistic (e.g., "crimping jig worn")
- The surviving hypothesis has strong physical or data support (Confirmed in fishbone terms)
- The cause chain is likely short (3–4 levels) and within a single process domain

**5-Why entry point:** The surviving hypothesis becomes Why 1, stated as a confirmed or probable fact.

Example: "Why did pin 3 deflect laterally during assembly? — Because the crimping jig locating pocket for pin 3 shows 0.22 mm wear (limit: 0.05 mm), confirmed by CMM measurement."

### When to go to Fishbone first

Use Fishbone when:
- Multiple hypotheses survive and they span different 6M categories (Man, Machine, Material)
- The scope is broad and the team needs to ensure no cause category is missed
- The problem is complex and the investigation will involve multiple people across functions

**Fishbone entry point:** Map surviving hypotheses to their 6M category and use them as the starting point for structured brainstorming in those categories. Do not re-brainstorm eliminated categories — the Is/Is-Not work has already scoped them out.

Example handoff:
- H1 (supplier material change) → Material branch, starting cause: "Supplier changed pin geometry or material specification at W18"
- H4 (assembly jig change) → Machine branch, starting cause: "Crimping jig modified or degraded between W17 and W18"

**What Is/Is-Not feeds into the Fishbone:**
- IS NOT entries restrict which causes can survive evaluation — any fishbone cause that contradicts an IS NOT is Unlikely without further evidence
- The IS "When" and "Which" entries point directly to which sub-causes to confirm first (those that match the timing or batch boundary)

### Carrying the Is/Is-Not into NCR and 8D

The Is/Is-Not "What IS" entry is the non-conformance description for the NCR. The eliminated hypotheses belong in the 8D D2 (problem description) section, not the D4 (root cause) section. The surviving hypotheses are D4 inputs.

Auditors will look for consistency between the D2 problem description and the Is/Is-Not matrix. If they do not match, the 8D is internally inconsistent and will be rejected.
