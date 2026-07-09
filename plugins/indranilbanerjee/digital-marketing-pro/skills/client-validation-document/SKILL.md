---
name: client-validation-document
description: "Produce the Part 5 Client Validation Document — the one true stop where unbiased v1 findings meet the client. Each finding gets ACCEPT/REJECT/EDIT/DEFER decision."
user-invocable: true
triggers:
  - produce client validation document
  - run part 5 client validation
  - prepare findings for client review
  - client validation deliverable
  - the one true stop
  - prepare v1 findings for client
allowed-tools: Read Write Edit Bash Glob Grep
engagement-part: "5"
view-preference: v1-only
---

# /digital-marketing-pro:client-validation-document — Part 5: The One True Stop

This skill produces the Part 5 deliverable: the Client Validation Document. It is the only point in the engagement where unbiased v1 findings are formally presented to the client for accept/reject/edit decisions.

## Context efficiency

Heavy skill. **Grep before Read** any referenced file, then `Read` only matched ranges with `offset` + `limit`. List `${CLAUDE_PLUGIN_DATA}/<brand>/` before opening files. On re-invocation mid-session, skip files already in context.

This is the **one true stop** in the 12-Part flow. Nothing in Parts 6+ proceeds until this is signed off.

## What this document is

The Client Validation Document compiles the most strategically consequential findings from Parts 2, 3, and 4 (the unbiased research and the four core documents) into a structured review document. For each finding:

- The finding itself
- Evidence / sources
- Proposed implication if accepted
- Three response options for the client: ACCEPT / REJECT / EDIT / DEFER
- (For REJECT or EDIT) — the client provides their corrected version and the rationale

The client's responses then feed the Decision Matrix in Part 6 to determine which v2 re-runs are needed.

## What this document is NOT

- **Not a Growth Plan.** This is research findings, not strategic recommendations dressed up. The Growth Plan is Part 8.
- **Not exhaustive.** It includes only findings that have material strategic implications. Detail belongs in the source documents.
- **Not a slide deck.** It is a written document the client reads carefully and responds to. Slides do not capture the rigor required.
- **Not optional.** Every engagement runs Part 5. No shortcut to Part 6 without it.

## Pre-conditions

Before running this skill:

1. Parts 2, 3, 4 must be completed (or substantially complete with explicit acknowledgment that some research continues)
2. The engagement state file `_engagement.json` must show Parts 3 and 4 as `completed`
3. The Living Project Instruction File should be up to date with the v1 strategic facts

If pre-conditions fail, do NOT produce output. Instruct the user on what is missing.

## Document Structure

The Client Validation Document is organised by category of finding. Each category has 3–8 findings; total document is typically 12–25 findings across categories.

### Section 1: Executive Briefing

**Length:** 1 page.

**Content:**

- Purpose of this document
- How to read it (the ACCEPT / REJECT / EDIT / DEFER framework)
- What happens after the client responds (Part 6 v2 re-runs governed by the Decision Matrix)
- Decision deadline (typically 7–14 days)

### Section 2: Findings — by category

Each category contains its findings as structured blocks. Categories:

#### A. Business & SBU Findings (from 3.1)

Findings about the business reality — SBU separation, unit economics, value chain, growth levers, constraints, risks. Typically 3–5 findings.

#### B. Audience & Segmentation Findings (from 3.2 + 4.3)

Findings about target groups, persona priority, decision-making units, MQL/SQL definitions. Typically 3–5 findings.

#### C. Positioning & Communications Findings (from 3.3)

The chosen positioning, messaging pillars, tone-of-voice, don't-say rules, sensitive-topic handling. Typically 3–5 findings.

#### D. Channel & Budget Findings (from 3.4)

Channel selections, in-market vs out-market split, budget allocation, channel sequencing. Typically 2–4 findings.

#### E. Competitive Findings (from 4.1 + 4.2)

Competitor list, competitive positioning, Three-Question outputs (do well / do poorly / not doing). Typically 2–4 findings.

#### F. Market & Customer Findings (from 4.3 + 4.4)

Market sizing, customer behaviour patterns, demand signals. Typically 2–4 findings.

### Section 3: Open Questions

Questions that the unbiased research could not resolve and need client input. The client provides answers here.

### Section 4: Response Mechanism

How the client returns their responses (typically a structured response file or a meeting walkthrough).

## Finding Block Format

Each finding follows this exact structure:

```markdown
### Finding {ID}: {Short title}

**Category:** {A/B/C/D/E/F}
**Source:** {Document and step references — e.g., "3.1 Step 4, 4.1 Three-Question Output"}
**Materiality:** {High / Medium / Low}

**Finding:**
{2–4 sentences stating the finding from the unbiased research}

**Evidence:**
- {Cited source 1 with specific data point}
- {Cited source 2}
- {Cited source 3}

**Proposed implication if accepted:**
{1–3 sentences on what this means for the strategy if the client accepts}

**Client response:**

- [ ] ACCEPT — finding is correct as stated
- [ ] REJECT — finding is wrong; correction below
- [ ] EDIT — finding is partially correct; amended version below
- [ ] DEFER — needs further investigation; reason below

**If REJECT or EDIT, client correction:**
{Client fills in: what the correct finding is, with their evidence}

**If DEFER, reason and follow-up plan:**
{Client fills in: what additional research / data is needed, who is accountable, deadline}
```

## Materiality Classification

Each finding gets a Materiality rating that indicates how consequential the response is:

- **High** — accepting vs rejecting would meaningfully change the channel mix, budget, positioning, or audience priority. Triggers v2 re-runs per Decision Matrix.
- **Medium** — accepting vs rejecting would change tactical execution but not strategic direction. May or may not trigger re-runs.
- **Low** — accepting vs rejecting changes phrasing or examples but not substance. No re-run triggered.

The client should focus most attention on High materiality findings; Medium and Low are still presented for completeness.

## Response Categorisation for the Decision Matrix

After the client provides responses, the responses are categorised into Decision Matrix triggers:

| Client decision pattern | Decision Matrix trigger |
|---|---|
| Any competitor finding REJECTED or EDITED with new competitors | `competitors_changed` |
| Any market sizing finding REJECTED or EDITED | `target_market_changed` |
| Any segmentation finding REJECTED or EDITED with persona changes | `audiences_changed` |
| Any positioning finding REJECTED or EDITED | `positioning_changed` |
| Any budget / scope finding REJECTED or EDITED | `budget_or_scope_changed` |
| Any pricing or offering finding REJECTED or EDITED | `pricing_or_offering_changed` |
| Any unit economics finding REJECTED or EDITED | `unit_economics_changed` |
| Only Low-materiality EDITs / minor wording corrections | `minor_corrections_only` |

The skill compiles the trigger list and runs:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/engagement-state.py decision-matrix \
  --brand {slug} --id {id} \
  --triggers "{comma-separated-trigger-list}"
```

The output then feeds the Part 6 v2 re-run plan.

## Production Steps

1. **Verify pre-conditions** — Parts 2, 3, 4 completed.

2. **Read the v1 source documents:**
   - `part-03-four-core-documents/v1/3.1-business-and-sbu-analysis.md`
   - `part-03-four-core-documents/v1/3.2-segmentation-framework.md`
   - `part-03-four-core-documents/v1/3.3-brand-positioning-and-communications.md`
   - `part-03-four-core-documents/v1/3.4-dmflow.md`
   - `part-04-competitive-customer-market/v1/4.1-competitor-ad-analysis.md`
   - `part-04-competitive-customer-market/v1/4.2-competitor-positioning.md`
   - `part-04-competitive-customer-market/v1/4.3-customer-analysis.md`
   - `part-04-competitive-customer-market/v1/4.4-market-analysis.md`

3. **Extract material findings.** For each source document, identify the 2–5 most strategically consequential findings. Materiality rating: prefer High and Medium; include Low only if the client specifically benefits from confirming.

4. **Synthesise findings into the structured format.** Use plain client-facing language, not internal jargon. Each finding stands alone — do not require the client to read the source documents.

5. **Add Open Questions section** drawn from the "Open questions" sections of each source document.

6. **Add response mechanism section** — instruct the client how to return responses (recommended: produce a paired `client-validation-responses.json` file alongside the document).

7. **Save the document** to:
   ```
   engagements/{id}/part-05-client-validation/client-validation-document.md
   ```

8. **Generate the response template:**
   ```
   engagements/{id}/part-05-client-validation/client-validation-responses.template.json
   ```
   Containing one entry per finding with empty decision/correction fields.

9. **Mark Part 5 as `awaiting_input`** in `_engagement.json` (not `completed` — Part 5 is only complete when the client responses are recorded).

10. **Brief the user** on the document, the response mechanism, and the typical 7–14 day decision window.

## Recording Client Responses

When the client returns responses (filled-in JSON file or verbal walkthrough captured in a meeting):

1. Save the populated response file to:
   ```
   engagements/{id}/part-05-client-validation/client-validation-responses.json
   ```

2. Run `engagement-state.py decision-matrix --validation-file <path>` to determine the v2 re-run plan.

3. Mark Part 5 as `completed`.

4. Advance to Part 6 (v2 re-runs).

## Quality Discipline

1. **Plain client language.** No "MQL/SQL pipeline funnel architecture" jargon. Translate to "the way leads move from interested to ready-to-buy."
2. **Each finding stands alone.** Client should not need to consult the source docs to understand the finding.
3. **Evidence is cited explicitly.** Vague claims ("market data shows...") are unacceptable. Cite the specific source with the data point.
4. **Materiality is honest.** Don't downgrade an uncomfortable finding to "Low" to make it easier to accept.
5. **Open Questions are real questions.** Don't fabricate questions for the sake of having an Open Questions section.
6. **The response mechanism is structured.** Free-form client emails are hard to translate into Decision Matrix triggers; the JSON response template makes the pattern unambiguous.

## Examples

### Example 1: Producing the document

```
User: We've completed Parts 2, 3, 4 for Acme. Time to prepare the Client Validation Document.

Skill response:
1. Verify pre-conditions ✓
2. Pull findings from the 8 source documents (4 from Part 3 + 4 from Part 4) using grep first to locate each category's section, then targeted Read with offset+limit — avoid bulk-Read on all 8 files up front or you'll blow the per-skill 5K-token budget
3. Extract 18 material findings across categories A–F:
   - 4 in Business & SBU
   - 3 in Audience & Segmentation
   - 4 in Positioning & Communications
   - 3 in Channel & Budget
   - 2 in Competitive
   - 2 in Market & Customer
4. 12 are High materiality, 5 Medium, 1 Low
5. 4 Open Questions identified from source docs
6. Save document at engagements/2026-q2/part-05-client-validation/client-validation-document.md (~22 pages)
7. Save response template at engagements/2026-q2/part-05-client-validation/client-validation-responses.template.json
8. Mark Part 5 as awaiting_input
9. Brief: "Document ready. 18 findings, 4 open questions. Recommend client meeting in 5–7 days for live walk-through, with responses returned within 2 weeks."
```

### Example 2: Recording client responses

```
User: Acme client returned responses. They accepted most but rejected the positioning finding (they want to keep their existing positioning) and added 2 new competitors we missed.

Skill response:
1. Read the populated client-validation-responses.json
2. Categorise responses: 16 ACCEPT, 1 REJECT (positioning), 1 EDIT (competitor list)
3. Determine triggers: positioning_changed + competitors_changed
4. Run engagement-state.py decision-matrix --triggers "positioning_changed,competitors_changed"
5. Output: triggered re-runs = 3.1, 3.2, 3.3, 3.4, 4.1, 4.2 (the union of both triggers' re-run sets)
6. Estimate cost: ~85K tokens
7. Mark Part 5 completed
8. Brief: "Part 5 closed. 6 v2 re-runs triggered. Recommend reviewing the re-run plan and approving before invoking four-core-documents and competitor-analysis with view=v2."
```

## Related skills

- `engagement-workflow` — orchestrates the 12-Part flow
- `four-core-documents` — produced the v1 docs being validated; will produce v2 re-runs after Part 5
- Existing `competitor-analysis`, `audience-intelligence`, `market-intelligence` skills produced the Part 4 docs

## Related references

- [engagement-flow-methodology.md](../context-engine/engagement-flow-methodology.md) — Part 5 in context
- [decision-matrix-rerun.md](../context-engine/decision-matrix-rerun.md) — how responses translate to re-runs
- [two-views-model.md](../context-engine/two-views-model.md) — v1 + v2 architecture
- [stone-vs-opinion.md](../context-engine/stone-vs-opinion.md) — confidence tagging context
