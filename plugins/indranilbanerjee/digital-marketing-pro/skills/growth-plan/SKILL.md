---
name: growth-plan
description: "Produce the 11-section Growth Plan — the flagship Part 8 client-facing deliverable that synthesises the entire engagement into a single executable strategy."
user-invocable: true
triggers:
  - produce the growth plan
  - generate flagship client deliverable
  - run part 8 growth plan
  - synthesise the engagement into a growth plan
  - write the strategy document for the client
  - 11-section growth plan
allowed-tools: Read Write Edit Bash Glob Grep
engagement-part: "8"
view-preference: v2-primary
---

# /digital-marketing-pro:growth-plan — Part 8 Flagship Deliverable

The Growth Plan is the flagship client-facing deliverable. It synthesises every internal document produced in Parts 1–7 into a single 11-section narrative answering: *"How will we grow this business digitally, and what will it cost?"*

## Context efficiency

Heavy skill. **Grep before Read** any referenced file, then `Read` only matched ranges with `offset` + `limit`. List `${CLAUDE_PLUGIN_DATA}/<brand>/` before opening files. On re-invocation mid-session, skip files already in context.

**Specification:** [growth-plan-template.md](../context-engine/growth-plan-template.md) — the canonical 11-section structure.

## Pre-conditions

Before producing the Growth Plan, verify:

1. **Parts 1–7 completed** in the engagement
2. **Four Core Documents at canonical version** (v2 if re-runs happened, v1 otherwise)
3. **Living Project Instruction File current** — reflects the current strategic facts
4. **Part 7 Preparation Documents completed** — campaign architecture, naming conventions, KPI tree, content pillars, asset inventory, approval chains

If any pre-condition fails, do NOT produce. Instruct the user.

## The 11 Sections

| # | Section | Length | Source |
|---|---------|--------|--------|
| 1 | Executive Summary | 1 page | Synthesis |
| 2 | Business Context | 2-3 pages | Core Doc 3.1 + Part 4.4 + Part 4.2 |
| 3 | Target Audience | 2-3 pages | Core Doc 3.2 |
| 4 | Strategic Positioning | 2 pages | Core Doc 3.3 |
| 5 | Channel Strategy | 3-4 pages | Core Doc 3.4 + Part 9 channel docs |
| 6 | Budget & Media Plan | 2-3 pages | Core Doc 3.4 Step 5 + 9 |
| 7 | KPI Framework | 2 pages | Part 7 KPI tree |
| 8 | Implementation Timeline | 2-3 pages | Part 7 + 30/60/90 framework |
| 9 | Team & Resource Plan | 1-2 pages | Engagement context |
| 10 | Risk & Contingency | 1-2 pages | Core Doc 3.1 Step 16 |
| 11 | Expected Outcomes | 2 pages | Three-scenario forecasting |

Total target length: **20–30 pages**. Beyond 30, clients stop reading.

## Production process

### Step 1: Read source documents

Reading order (canonical version of each):

1. Living Project Instruction File (current truth)
2. Core Doc 3.1 Business & SBU Analysis
3. Core Doc 3.2 Segmentation Framework
4. Core Doc 3.3 Brand Positioning & Communications
5. Core Doc 3.4 DMFlow
6. Part 4 documents (4.1, 4.2, 4.3, 4.4)
7. Part 7 preparation documents (campaign architecture, KPI tree, content pillars)

### Step 2: Synthesise — do not re-state

The Growth Plan is **synthesis**, not concatenation. Do not copy paragraphs from the Core Docs verbatim. Re-write each section in client-facing narrative form, citing the source document for traceability.

### Step 3: Apply the three-scenario discipline

Section 11 (Expected Outcomes) presents Conservative / Moderate / Aggressive scenarios per [three-scenario-forecasting.md](../context-engine/three-scenario-forecasting.md).

Section 7 (KPI Framework) targets are also presented as three scenarios per KPI.

### Step 4: Apply the In-Market vs Out-Market split

Section 5 (Channel Strategy) and Section 6 (Budget & Media Plan) explicitly call out the In-Market vs Out-Market budget allocation per [in-market-out-market.md](../context-engine/in-market-out-market.md).

### Step 5: Apply the 30/60/90 framework

Section 8 (Implementation Timeline) uses the 30/60/90 phasing per [30-60-90-framework.md](../context-engine/30-60-90-framework.md) for the first quarter, then quarterly milestones thereafter.

### Step 6: Output

Save to `engagements/{id}/part-08-growth-plan/growth-plan.md`. Generate companion exports:

- PDF via the existing `pdf-generator.py` script
- DOCX via the existing document export utilities

## Section-by-section guidance

### Section 1: Executive Summary

The CEO reads this. Make it count.

- Key findings (3-5 bullets — most important things from analysis)
- Recommended strategy (1-2 sentences headline)
- Expected outcomes (moderate scenario, with conservative-aggressive band)
- Investment required (total budget; fixed + variable breakdown)
- Timeline (30/60/90 + quarterly milestones in one sentence)
- The single most important thing the client needs to know

### Section 2: Business Context

Set the stage for why the strategy is what it is.

- Summary of business analysis (Core Doc 3.1) — what the business is, how it makes money, key strengths and constraints
- Industry landscape — market size, growth trajectory, competitive intensity
- Competitive position — where the brand sits, key competitors, positioning today
- Critical assumptions — major Stone facts and validated Opinions

### Section 3: Target Audience

- Primary persona summary in actionable format (6 questions)
- Secondary persona if relevant
- Why these personas were chosen (tie back to TG scoring from 3.2)
- Anti-personas — who we explicitly do NOT target
- For B2B: Decision-Making Unit summary per persona

### Section 4: Strategic Positioning

- Positioning statement (the formal one-sentence)
- Brand promise + 3-5 supporting proof points
- The 3-5 messaging pillars
- Tone-of-voice profile with one on-tone vs off-tone example
- Don't-say rules

### Section 5: Channel Strategy

- Channel selection summary (in-scope vs deferred per [channel-families.md](../context-engine/channel-families.md))
- Per-channel role (which funnel stage)
- Channel sequencing logic (which feeds which)
- In-Market vs Out-Market split with rationale
- Media mix across paid / organic / earned / owned

### Section 6: Budget & Media Plan

- Total monthly fixed budget
- Variable budget envelope per [fixed-vs-variable-budget.md](../context-engine/fixed-vs-variable-budget.md)
- Per-channel allocation table with rationale
- Quarterly budget pacing
- Year-1 total investment
- Investment vs expected return (LTV:CAC math per [unit-economics-framework.md](../context-engine/unit-economics-framework.md))

### Section 7: KPI Framework

- Primary KPI (the one number that matters most for the period)
- Secondary KPIs (3-5)
- Per-channel KPIs
- KPI targets in three scenarios
- Reporting cadence per [reporting-cadence.md](../context-engine/reporting-cadence.md)
- Attribution model used
- Known measurement limitations

### Section 8: Implementation Timeline

30 / 60 / 90-day milestones for the first quarter. Quarterly milestones thereafter.

- Days 1-30 Foundation
- Days 31-60 Validation
- Days 61-90 Optimisation & Scale
- Q2 milestones
- Q3 milestones
- Year-end goals

### Section 9: Team & Resource Plan

- Agency / consulting team roles
- Client team roles (especially what client must own)
- External partners
- Approval workflows and SLAs
- Critical dependencies that could delay execution

### Section 10: Risk & Contingency

- Top 3-5 risks across market, competitive, regulatory, operational, execution dimensions
- Per risk: likelihood, impact, mitigation strategy, trigger conditions
- Contingency budget (typically 10-15% reserve)
- Decision-making authority for invoking contingency

### Section 11: Expected Outcomes

- Three-scenario forecast (Conservative / Moderate / Aggressive)
- Per-quarter forecast (Q1, Q2, Q3, Q4)
- Triggers that move us between scenarios
- What the team will track to know which scenario is unfolding
- Conditions under which the plan would be revised

## Quality discipline

1. **Every claim cites a source** — Core Doc reference with version number
2. **Every projection states assumptions** — no naked numbers
3. **Plain language** — the CEO is not a marketing specialist
4. **Visual evidence where it helps** — charts, scenario tables, timeline diagrams
5. **20-30 page target** — beyond 30, clients stop reading
6. **Consistency with Yearly Planner** — the operational calendar from `/digital-marketing-pro:yearly-planner` must align with this Growth Plan

## After production

1. Save markdown to `part-08-growth-plan/growth-plan.md`
2. Generate PDF + DOCX exports
3. Mark Part 8 sub-complete (Growth Plan); Yearly Planner completion finishes Part 8
4. Update LIF: Engagement phase = "Strategy approved; Channel Build pending"
5. Brief: "Growth Plan complete. {N} pages. Run /digital-marketing-pro:yearly-planner to produce the operational companion. After client approval, /digital-marketing-pro:engagement next advances to Part 9 Channel Strategy."

## Examples

### Example 1: First Growth Plan production

```
User: Produce the Growth Plan for Acme.

Skill response:
1. Verify pre-conditions: Parts 1-7 completed, Core Docs at v2 ✓
2. Pull from source docs ONE AT A TIME via targeted Read with offset+limit (grep first for the section you need, then Read just that range) — the full corpus is ~95K words, so bulk-reading every doc up front blows the per-skill 5K-token budget
3. Synthesise into 11 sections, ~24 pages
4. Apply three-scenario forecasting in Sections 7 + 11
5. Apply 30/60/90 phasing in Section 8
6. Save markdown + generate PDF + DOCX
7. Mark Growth Plan complete (Yearly Planner pending)
8. Brief: "Growth Plan v1.0 produced. 24 pages. Conservative Q1 forecast: INR 1.8 Cr new ARR; Moderate: INR 2.6 Cr; Aggressive: INR 3.4 Cr. Run /digital-marketing-pro:yearly-planner next."
```

## Related skills

- `engagement-workflow` — orchestrates Part 8
- `yearly-planner` — companion deliverable that completes Part 8
- `four-core-documents` — produces the canonical Core Docs that feed the Growth Plan

## Related references

- [growth-plan-template.md](../context-engine/growth-plan-template.md) — canonical 11-section structure
- [three-scenario-forecasting.md](../context-engine/three-scenario-forecasting.md) — Sections 7 + 11
- [in-market-out-market.md](../context-engine/in-market-out-market.md) — Sections 5 + 6
- [fixed-vs-variable-budget.md](../context-engine/fixed-vs-variable-budget.md) — Section 6
- [unit-economics-framework.md](../context-engine/unit-economics-framework.md) — Section 6
- [30-60-90-framework.md](../context-engine/30-60-90-framework.md) — Section 8
- [reporting-cadence.md](../context-engine/reporting-cadence.md) — Section 7
- [channel-families.md](../context-engine/channel-families.md) — Section 5
