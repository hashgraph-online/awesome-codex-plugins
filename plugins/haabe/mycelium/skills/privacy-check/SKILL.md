---
name: privacy-check
description: "Use to assess Privacy by Design compliance and GDPR/data protection alignment for a feature or system."
metadata:
  instruction_budget: "37"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Privacy Check Skill

Privacy by Design assessment.

## Workflow

### 7 Foundational Principles (Cavoukian)

1. **Proactive not Reactive**: Are privacy measures built in from the start?
   - [ ] Privacy considered in design phase, not bolted on
   - [ ] Risks identified before implementation

2. **Privacy as Default**: Is the most private option the default?
   - [ ] Data collection opt-in, not opt-out
   - [ ] Minimum data collected by default
   - [ ] Sharing disabled by default

3. **Privacy Embedded in Design**: Is privacy integral to the system?
   - [ ] Privacy controls are core features, not add-ons
   - [ ] Architecture supports data minimization

4. **Positive-Sum, not Zero-Sum** (originally "Full Functionality"): Privacy without trade-offs?
   - [ ] Privacy features don't degrade user experience
   - [ ] Not a false choice between privacy and functionality
   - [ ] Avoid false dichotomies: privacy vs. security, privacy vs. business value

5. **End-to-End Security**: Data protected throughout its lifecycle?
   - [ ] Stored and sent the way the data needs: encryption where personal data is stored or sent electronically; for paper or in-person handling, who holds it and where (v0.271.0)
   - [ ] Secure deletion when no longer needed
   - [ ] Access controls throughout the data lifecycle

6. **Visibility and Transparency**: Is data processing transparent?
   - [ ] Users know what data is collected and why
   - [ ] Processing purposes documented and communicated
   - [ ] Third-party sharing disclosed

7. **Respect for User Privacy**: Are user interests centered?
   - [ ] Users can access their data
   - [ ] Users can correct their data
   - [ ] Users can delete their data
   - [ ] Consent is informed, specific, and revocable

### Data Protection Assessment

**If the product holds no personal data, say so in the data inventory, with how you know** (a
page that stores nothing, a book): the principles above then need only a line each confirming
nothing is collected. Controls are proportional to what is held; none are defaults (v0.271.0).

- **What data is collected?** List all personal data fields.
- **Why?** Lawful basis for each data element.
- **How long?** Retention period for each data type.
- **Who accesses it?** List all parties with access.
- **Where is it stored?** Data residency and cross-border transfers.
- **How is it protected?** Encryption, access control, monitoring.
- **What if breached?** Incident response plan exists?

### Output

```
## Privacy Assessment: [Feature/System]

### PbD Principles
| Principle | Status | Notes |
|-----------|--------|-------|
| Proactive | Pass/Fail | ... |
| Default privacy | Pass/Fail | ... |
| Embedded | Pass/Fail | ... |
| Full functionality | Pass/Fail | ... |
| End-to-end security | Pass/Fail | ... |
| Transparency | Pass/Fail | ... |
| User respect | Pass/Fail | ... |

### Data Inventory
| Data | Purpose | Basis | Retention | Protection |
|------|---------|-------|-----------|-----------|
| ... | ... | ... | ... | ... |

### Risks and Recommendations
1. [risk and recommended action]
```

## Canvas (MANDATORY — the source of truth, do this FIRST)

`.claude/canvas/privacy-assessment.yml` is the canonical record. The decision log is provenance; the
canvas is what the framework READS. Write the canvas before the decision log — if only one of the two
lands, it must be this one.

**WHY THIS SECTION EXISTS (v0.170.0).** On the dogfood project this file carried
`last_assessed: 2026-05-04` while **all seven** Privacy-by-Design principles read
`assessment: not-assessed` with empty `evidence`, and `data_inventory` was empty. **A date asserting
an assessment that never landed is worse than an empty file**: a reader checking freshness sees an
assessed record, and the `Privacy` theory gate — Required at L2-L4 — reads it. Never stamp
`last_assessed` in a run that does not also fill the principles.

**Since v0.331.0 the gate checks this itself.** The scale-lock gate and the release gate count Privacy
as passed only when `last_assessed`, a `data_inventory` (or `data_minimization_check`) and all seven
principles judged with `evidence` are on the record (`scripts/_assessment_lib.py`). A principle left
at `not-assessed`, or judged with no `evidence`, holds the gate and is named in what it reports. At an
L3's `commit_to_build` the principles are judged on the design; nothing built is needed. Until
0.331.0 the gate read the date and the inventory only, so the record this section warns about passed.

**UPDATE each of the seven keys in `principles`** (`proactive_not_reactive`, `privacy_as_default`,
`privacy_embedded`, `full_functionality`, `end_to_end_security`, `visibility_transparency`,
`respect_for_users`):

```yaml
  <principle_key>:
    assessment: pass|partial|fail|not-assessed
    evidence: "<what was observed, and where>"
```

**Then:** `data_inventory` (what personal data the product actually touches — an empty list is a
CLAIM that it touches none, so make it deliberately), `processors` (every party outside the product
that receives or stores that data, with `role`, `data_types`, `location`, `retention_period` and
`agreement`: the answers to "Who accesses it?" and "Where is it stored?" above), `dpia_required` +
`dpia_rationale`, and `last_assessed`.

**A reassessment updates these same fields; it does not add a new block.** What changed, and why,
goes in the decision-log entry below. The schema rejects any root key it does not name, and from
v0.250.0 the write is checked as it lands.

**`last_assessed` IS A CLAIM ABOUT THE PRINCIPLES BELOW IT.** Set it only when they were filled in
the same run. If the assessment is partial, say which keys were judged in `dpia_rationale` rather
than dating the whole file.

## Postflight: Verify-After-Write (write-narration-verification discipline)

**Hard rule** (per the operating contract's Communication Rules, anti-pattern #7 Stage 2 graduation). Before any
user-facing summary claims the assessment was recorded, use the **Read tool** on the canvas file and
confirm the VALUE fields above actually changed — not just `_meta.last_validated`. A stamp moving
while the assessed fields stay at their defaults is the exact failure this skill shipped with: the
file reads fresh and holds nothing. Preflight protects what gets written; Postflight protects what
gets claimed about what was written.

## Decision Log (MANDATORY per G-P4)
**APPEND** a `### Privacy Assessment` entry to `.claude/harness/decision-log.md` with: principles assessed, data flows identified, risks found, GDPR compliance status.

## Theory Citations
- Cavoukian: Privacy by Design (7 principles)
- GDPR: Data protection regulation
