---
name: four-core-documents
description: "Produce the Four Core Documents at strategic depth (61 total steps): Business & SBU Analysis, Segmentation Framework, Brand Positioning, DMFlow. Use when running Part 3 of the engagement methodology."
user-invocable: true
triggers:
  - produce the four core documents
  - run part 3 of the engagement
  - generate the strategic spine
  - business and SBU analysis
  - segmentation framework
  - brand positioning document
  - DMFlow document
  - re-run a core document as v2
allowed-tools: Read Write Edit Bash Glob Grep
engagement-part: "3"
view-preference: v2-primary
---

# /digital-marketing-pro:four-core-documents — The Strategic Spine (61 Steps)

This skill produces Part 3 of the engagement methodology: the four documents that together define the brand at strategic depth. Every channel strategy, every creative brief, every piece of copy reads back to these.

## Context efficiency

Heavy skill. **Grep before Read** any referenced file, then `Read` only matched ranges with `offset` + `limit`. List `${CLAUDE_PLUGIN_DATA}/<brand>/` before opening files. On re-invocation mid-session, skip files already in context.

**Specification:** [four-core-documents-spec.md](../context-engine/four-core-documents-spec.md) — the exact 61 steps across the four documents.

**Engagement context:** [engagement-flow-methodology.md](../context-engine/engagement-flow-methodology.md) — where Part 3 fits in the 12-Part flow.

## Pre-conditions

Before running this skill, verify:

1. **Brand profile exists** at `~/.claude-marketing/brands/{brand-slug}/profile.json`. If not, run `/digital-marketing-pro:brand-setup` first.
2. **Engagement is initialised** with state file `_engagement.json` present. If not, run `/digital-marketing-pro:engagement start` first.
3. **Part 1 (Client Inputs) is completed**. Stone facts and Opinion hypotheses must be captured before Part 3 can begin.
4. **Part 2 (External Research) is at least started**. Some Part 2 research may continue in parallel with Part 3, but the kickoff must have happened.

If any pre-condition fails, do NOT produce output. Instead, instruct the user on what to run first.

## Subcommands

### Produce all four documents

```
/digital-marketing-pro:four-core-documents <brand-slug> <engagement-id>
```

Produces 3.1, 3.2, 3.3, 3.4 in sequence. Total time: 30–90 minutes depending on engagement complexity.

### Produce a single document

```
/digital-marketing-pro:four-core-documents <brand-slug> <engagement-id> --doc 3.1
```

Produces just the specified document. Useful for re-runs (Part 6) or when one doc needs to be redone independently.

### Produce v2 re-runs

```
/digital-marketing-pro:four-core-documents <brand-slug> <engagement-id> --view v2 --docs "3.1,3.3"
```

Produces v2 versions of the specified documents. Used during Part 6 after the Decision Matrix has triggered re-runs.

### Produce the Combined Core Document (3.C)

```
/digital-marketing-pro:four-core-documents <brand-slug> <engagement-id> --combined
```

Stitches all four canonical core documents (latest version of each) into a single executive-reference file with master TOC, master assumptions table, and master source index. Produced only when an executive audience needs a single-file read.

## Production Order

The four documents are produced in sequence because each builds on the prior:

1. **3.1 Business & SBU Analysis** (18 steps) — foundational. Establishes the business reality.
2. **3.2 Segmentation Framework** (15 steps) — depends on 3.1's SBU and customer data.
3. **3.3 Brand Positioning & Communications** (19 steps) — depends on 3.2's personas.
4. **3.4 DMFlow** (9 steps) — depends on 3.1, 3.2, and 3.3 to make channel decisions.

When running re-runs, only the affected documents are regenerated. Other documents remain at their current version.

## Per-Document Production

### 3.1 — Business & SBU Analysis (18 steps)

Read the spec section for 3.1 in [four-core-documents-spec.md](../context-engine/four-core-documents-spec.md). The 18 steps are:

1. SBU identification
2. SBU separation rationale
3. Revenue streams per SBU
4. Unit economics per SBU
5. Value chain mapping
6. Offering portfolio at task-level granularity
7. Pricing architecture
8. Organisational and go-to-market model
9. Sales and distribution architecture
10. Full SWOT with evidence
11. Growth levers
12. Constraints
13. Customer acquisition economics
14. Customer retention economics
15. Partnership and channel dependencies
16. Risk profile
17. Strategic implications for the engagement
18. Open questions

**Inputs:**

- `part-01-client-inputs/stone-facts.json` — ground-truth facts
- `part-02-external-research/` — unbiased external research (industry data, market context)
- Brand profile at `~/.claude-marketing/brands/{slug}/profile.json`
- (Do NOT use Opinion hypotheses as ground truth — those are research questions, not facts)

**Output:**

`engagements/{id}/part-03-four-core-documents/v1/3.1-business-and-sbu-analysis.md`

(For v2 re-runs: same path but in `v2/` instead of `v1/`)

**Output structure:**

```markdown
---
document: 3.1-business-and-sbu-analysis
version: v1.0
engagement: {engagement-id}
brand: {brand-slug}
produced: {iso-timestamp}
view: v1   # or v2 for re-runs
---

# 3.1 Business & SBU Analysis

## Step 1: SBU Identification

[Content for step 1]

## Step 2: SBU Separation Rationale

[Content for step 2]

... (all 18 steps, in order)

## Sources

[Numbered list of every cited source: client docs, public sources, industry reports, Stone facts referenced]

## Open Questions

[Anything that could not be answered with available info]

## Change Log

### v1.0 — {date}
- Initial unbiased research version produced from Part 2 + Stone facts.
```

### 3.2 — Segmentation Framework (15 steps)

The 15 steps:

1. Target Group identification
2. TG scoring across criteria
3. TG prioritisation
4. Sub-TG breakdown
5. Persona development per primary TG (using [actionable-persona-format.md](../context-engine/actionable-persona-format.md))
6. Behavioural attributes per persona
7. Psychographic attributes per persona
8. Need-state mapping
9. Geographic distribution
10. (B2B only) Multi-stakeholder Decision Unit per persona (using [b2b-decision-making-unit.md](../context-engine/b2b-decision-making-unit.md))
11. (B2B only) MQL definition
12. (B2B only) SQL definition
13. (B2B only) Pipeline logic
14. Anti-personas
15. Activation guidance

Steps 10–13 are skipped for B2C engagements. The skill detects B2B vs B2C from the brand profile's `business_model.type` field.

**Inputs:**

- 3.1 (just produced) for SBU + customer baseline
- `part-04-competitive-customer-market/v1/4.3-customer-analysis.md` if available (for unbiased customer research)
- Brand profile

**Output:**

`engagements/{id}/part-03-four-core-documents/v1/3.2-segmentation-framework.md`

### 3.3 — Brand Positioning & Communications (19 steps)

The 19 steps:

1. Positioning options considered
2. Per-option rationale
3. Per-option trade-offs
4. Chosen positioning with defence argument
5. Positioning statement (formal one-sentence)
6. Trade-offs explicit
7. Brand promise
8. Proof points for the brand promise
9. Primary message architecture
10. Messaging pillars (3–5)
11. Proof points per pillar
12. Segment-level messaging variations
13. Full-funnel communication framework (TOFU/MOFU/BOFU/retention/advocacy)
14. Tone-of-voice principles
15. Explicit don't-say rules
16. Sensitive-topic handling
17. Crisis-communication posture
18. Application guidance across channels
19. Open positioning questions

**Inputs:**

- 3.1 + 3.2 (just produced)
- `part-04-competitive-customer-market/v1/4.2-competitor-positioning.md` if available
- Brand profile (for current brand voice signals)

**Output:**

`engagements/{id}/part-03-four-core-documents/v1/3.3-brand-positioning-and-communications.md`

### 3.4 — DMFlow (9 steps)

The 9 steps:

1. Channel universe considered (using [five-digital-markets.md](../context-engine/five-digital-markets.md))
2. Channel selection with rationale per channel
3. Funnel architecture per channel
4. Media mix logic across paid/organic/earned/owned
5. Budget allocation logic at business level (with In-Market vs Out-Market split per [in-market-out-market.md](../context-engine/in-market-out-market.md))
6. Channel interdependencies and sequencing
7. Conversion framework
8. Measurement approach
9. Strategic implications and track weightages

**Inputs:**

- 3.1 + 3.2 + 3.3 (just produced)
- Brand profile (for current channels, budget envelope)
- [channel-families.md](../context-engine/channel-families.md) for the 7-family / 17-channel taxonomy

**Output:**

`engagements/{id}/part-03-four-core-documents/v1/3.4-dmflow.md`

## Quality Discipline (Apply to All Four Documents)

1. **Every claim cites a source.** No "we think" — only "the evidence shows" with cited source.
2. **Every assumption is explicit.** When estimating CAC, LTV, market size, etc., state the methodology and inputs.
3. **Every recommendation flows from analysis.** No conclusions the body does not support.
4. **No generic statements.** "Strong brand" is generic. "92% brand recall in target segment per [source]" is specific.
5. **All four documents reference each other consistently.** A persona defined in 3.2 must be the same persona referenced in 3.3 messaging variations and 3.4 channel selection.
6. **Open questions are documented**, not hidden.
7. **Stone facts are facts; Opinion hypotheses are questions.** Don't elevate Opinion to fact in the document.
8. **Multi-Dimensional Decision Framework** (see [decision-framework.md](../context-engine/decision-framework.md)) is used for any choice (channel selection, persona prioritisation, positioning trade-offs).

## Single-File Discipline

Each document is produced as a single file containing all its steps. If a document cannot be completed in one turn due to output limits:

1. Save the partial document so far
2. Continue the same file from where it left off in the next turn (NEVER start a new file)
3. The file is considered complete only when all steps are present

The skill uses an internal continuation mechanism — if it hits a limit, it logs the cut-off step and resumes from there.

## After Production

Once all four documents are produced (or after each individually):

1. Update the Living Project Instruction File:
   - Strategic Facts section: extract positioning statement, primary persona summary, channel selections, unit economics
   - Version History section: add the new v1.0 entries
2. Mark Part 3 (or the specific sub-document) as completed in `_engagement.json`
3. Notify the user that Part 4 is the natural next step

## v2 Re-runs

When invoked with `--view v2`, the skill:

1. Reads the v1 version of the requested doc
2. Reads the Part 5 Client Validation Document (the changes the client requested)
3. Reads the relevant subset of changes that apply to this doc
4. Produces v2 with a header section listing what changed vs v1:

```markdown
## v1 → v2 Changes

- Section X (Step N): {what changed} — driven by {client validation finding ID}
- Section Y: ...
```

5. Saves to `v2/{doc-name}.md` (the v1 file remains untouched)
6. Bumps the version in `_engagement.json` via `engagement-state.py bump-version`
7. Updates the LIF with the changed strategic facts

## Examples

### Example 1: First-time production of all four documents

```
User: Produce the four core documents for the Acme engagement.

Skill response:
1. Verify pre-conditions: brand profile ✓, engagement initialised ✓, Part 1 complete ✓, Part 2 in progress ✓
2. Begin 3.1 Business & SBU Analysis. Read Stone facts, Part 2 research, brand profile. Walk all 18 steps. Cite sources throughout. Save to v1/3.1-business-and-sbu-analysis.md.
3. Begin 3.2 Segmentation Framework. Read 3.1, Part 4.3 if available. Detect business model = B2B from profile, so include steps 10-13. Walk 15 steps. Save to v1/3.2-segmentation-framework.md.
4. Begin 3.3 Brand Positioning. Read 3.1, 3.2, Part 4.2 if available. Walk 19 steps. Save to v1/3.3-brand-positioning-and-communications.md.
5. Begin 3.4 DMFlow. Read 3.1, 3.2, 3.3. Apply 5 Digital Markets taxonomy. Walk 9 steps. Save to v1/3.4-dmflow.md.
6. Update LIF: positioning statement, primary persona, channel selections, blended CAC estimate.
7. Mark Part 3 completed.
8. Brief: "Part 3 complete. 4 documents, 61 steps. Total ~12,000 words across all four. Recommend reviewing 3.3 (positioning) carefully — the chosen positioning has notable trade-offs documented in step 6."
```

### Example 2: v2 re-run after Part 5

```
User: Re-run 3.3 and 3.4 as v2 — client rejected the positioning and we need to redo the channel mix as a result.

Skill response:
1. Verify Part 5 Client Validation Document exists with positioning rejection captured ✓
2. Begin 3.3 v2. Read 3.3 v1 + Client Validation Document. Re-do positioning per client direction. Add v1→v2 changes header. Save to v2/3.3-brand-positioning-and-communications.md.
3. Begin 3.4 v2. Read 3.4 v1 + (now updated) 3.3 v2. Re-do channel mix to align with new positioning. Add v1→v2 changes header. Save to v2/3.4-dmflow.md.
4. Bump versions: engagement-state.py bump-version --doc 3.3 + --doc 3.4
5. Update LIF: new positioning statement, new channel selections, version history.
6. Brief: "v2 re-runs complete. 3.1 and 3.2 unchanged (still v1.0). 3.3 and 3.4 now at v2.0. Both views remain available. Operating decisions should reference v2 docs."
```

### Example 3: Producing the Combined Core Document for executive review

```
User: Produce the Combined Core Document for the executive presentation next week.

Skill response:
1. Verify all four core documents exist (latest version of each) ✓
2. Read 3.1 v1.0, 3.2 v1.0, 3.3 v2.0, 3.4 v2.0
3. Synthesise into single document with:
   - Master TOC at top
   - Each document as a major section
   - Master Assumptions Table (extract every "Assumption" call-out from all four docs)
   - Master Source Index (de-duplicated list of every source cited)
4. Save to part-03-four-core-documents/3.C-combined-core-document.md
5. Brief: "3.C produced. 60+ pages. Includes master TOC + assumptions table + source index. Recommended exports: PDF for the executive deck, DOCX if they want to annotate."
```

## Related skills

- `engagement-workflow` — orchestrates the 12-Part flow that contains Part 3
- `client-validation-document` — Part 5 deliverable that triggers v2 re-runs
- Existing skills consumed by this one: `audience-intelligence`, `competitive-intel`, `market-intelligence`, `brand-guardian`

## Related references

- [four-core-documents-spec.md](../context-engine/four-core-documents-spec.md) — the canonical 61-step specification
- [actionable-persona-format.md](../context-engine/actionable-persona-format.md) — Step 5 of 3.2
- [b2b-decision-making-unit.md](../context-engine/b2b-decision-making-unit.md) — Steps 10-13 of 3.2 (B2B)
- [five-digital-markets.md](../context-engine/five-digital-markets.md) — Step 1 of 3.4
- [in-market-out-market.md](../context-engine/in-market-out-market.md) — Step 5 of 3.4
- [channel-families.md](../context-engine/channel-families.md) — Step 2 of 3.4
- [decision-framework.md](../context-engine/decision-framework.md) — used throughout for choice-making
- [unit-economics-framework.md](../context-engine/unit-economics-framework.md) — Step 4 of 3.1
