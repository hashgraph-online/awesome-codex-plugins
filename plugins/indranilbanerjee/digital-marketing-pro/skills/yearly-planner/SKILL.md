---
name: yearly-planner
description: "Produce the 12-month operational Yearly Planner — the calendar companion to the Growth Plan in Part 8. Translates strategy into month-by-month execution."
user-invocable: true
triggers:
  - produce the yearly planner
  - generate 12-month operational calendar
  - run part 8 yearly planner
  - month-by-month execution plan
  - quarterly themes and monthly initiatives
  - operational calendar for the year
allowed-tools: Read Write Edit Bash Glob Grep
engagement-part: "8"
view-preference: v2-primary
---

# /digital-marketing-pro:yearly-planner — Part 8 Operational Companion

The Yearly Planner complements the Growth Plan with a 12-month operational calendar that ties strategy to date-by-date execution. If the Growth Plan answers *"How will we grow this business?"*, the Yearly Planner answers *"What will we do, week by week, month by month?"*

**Specification:** [yearly-planner-template.md](../context-engine/yearly-planner-template.md) — the canonical structure.

## Pre-conditions

The Yearly Planner is produced **after** the Growth Plan. It operationalises the Growth Plan's strategic decisions.

Before producing, verify:

1. **Growth Plan completed** at `part-08-growth-plan/growth-plan.md`
2. **Part 7 preparation documents available** (campaign architecture, content pillars, KPI tree)
3. **Living Project Instruction File current**
4. **Brand profile** specifies geographic operations (so seasonal context can be applied)

## Structure (8 sections)

| # | Section | Source |
|---|---------|--------|
| 1 | Annual Themes | Synthesis of Growth Plan strategy across 4 quarters |
| 2 | Monthly Calendar | 12 monthly sub-sections; Growth Plan Section 8 expanded |
| 3 | Seasonal Strategy | Industry + cultural / festival seasonality (regional context) |
| 4 | Campaign Architecture | Part 7 campaign architecture detailed by quarter |
| 5 | Content Pillars Calendar | Core Doc 3.3 messaging pillars × Part 7 content pillars |
| 6 | Channel-Specific Cadence | One sub-section per active channel family |
| 7 | Resource & Budget Pacing | Quarterly budget pacing + resource plan |
| 8 | Quarterly Review Schedule | QBR dates + decision authority per [reporting-cadence.md](../context-engine/reporting-cadence.md) |

## Production process

### Step 1: Read sources

- Growth Plan (canonical version)
- Living Project Instruction File
- Part 7 preparation documents
- Brand profile (for geography → seasonality)
- For India-operating brands: [india-market-context.md](../context-engine/india-market-context.md)

### Step 2: Build the Annual Themes

Identify 4 quarterly themes that organise the year. Each theme is one sentence with strategic rationale and ladders into the overall positioning. Themes might be (this is one example pattern, customise per engagement):

- Q1: Foundation + initial demand capture
- Q2: Demand generation activation
- Q3: Account expansion + community
- Q4: Festive surge + awards / press push

### Step 3: Detail the Monthly Calendar

12 sub-sections, ~1 page each. For each month:

- **Theme** — one sentence summary
- **Major initiatives** — 2-4 specific initiatives with owner and deadline
- **Always-on activity** — what continues from the prior month (paid ads at fixed budget, organic posting cadence, email programme, SEO content production)
- **Key dates** — product launches, industry events, holidays / festivals relevant to the brand, planned PR moments
- **Content calendar overview** — themes per week, content pillars covered, target volume per channel
- **Budget** — monthly fixed spend by channel, variable budget reserve
- **KPI targets** — primary + 2-3 secondary KPIs for the month

### Step 4: Map Seasonal Strategy

For India-operating brands, reference the seasonality table from [india-market-context.md](../context-engine/india-market-context.md):

- Dussehra → Diwali (Sept-Nov) festive peak
- Wedding season (Nov-Feb)
- End of financial year (Jan-Mar) — B2B budget spend
- Back-to-school (Apr-Jun)
- Monsoon (Jun-Sep)
- Cricket / IPL season (Mar-May)

For other markets, apply equivalent seasonality. For B2B globally, fiscal year-end and major industry events are universal seasonality drivers.

### Step 5: Map Campaign Architecture

The Part 7 campaign architecture document defines the year's major campaigns. The Yearly Planner places each campaign in its calendar slot with:

- Campaign name + theme
- Target persona
- Primary channels
- Timing (start, peak, wind-down)
- KPIs
- Expected outcome

### Step 6: Map Content Pillars Calendar

The 3-5 content pillars from Core Doc 3.3 are scheduled across the year:

- Per-pillar production target for the year (volume per format)
- Quarterly distribution (how content mix shifts)
- Repurposing flow (long-form blog → social posts → video → email)

### Step 7: Map Channel-Specific Cadence

For each active channel family:

- Posting / sending / publishing cadence (e.g., LinkedIn: 4 posts/week; Email: 1 broadcast/week + lifecycle flows; SEO: 6 articles/month)
- Volume targets for the year
- Quarterly emphasis shifts
- Resource requirements (creative production, copywriting, design, video)

### Step 8: Produce companion files

The Yearly Planner is delivered as:

- **`yearly-planner.md`** (canonical)
- **`yearly-planner.pdf`** (client distribution via `pdf-generator.py`)
- **`yearly-planner.xlsx`** (calendar in spreadsheet form for ongoing operational use)

Save all to `engagements/{id}/part-08-growth-plan/`.

## Quality discipline

1. **Every initiative has an owner.** "Marketing team will do X" is not actionable.
2. **Every quarter has measurable KPI targets.** "Improve traffic" is not a target.
3. **Always-on activity distinguished from initiatives.** Always-on is the baseline; initiatives are time-bounded efforts on top.
4. **Realistic capacity respected.** Sequence prevents burnout.
5. **Living document.** Reviewed and adjusted at each Quarterly Business Review.
6. **Aligns with Growth Plan.** No contradictions between the two.

## After production

1. Save all formats to `part-08-growth-plan/`
2. Mark Part 8 fully completed via `engagement-state.py mark-part-completed --part 8`
3. Update LIF: Engagement phase = "Strategy approved; Channel Build (Part 9) ready to begin"
4. Brief: "Yearly Planner complete. Operational calendar covers 12 months with quarterly themes, monthly initiatives, and channel-specific cadence. Recommend reviewing with the client before kicking off Part 9 channel build. /digital-marketing-pro:engagement next to advance."

## Examples

### Example 1: Standard Yearly Planner production

```
User: Produce the Yearly Planner for Acme.

Skill response:
1. Verify Growth Plan exists ✓; Part 7 preparation docs available ✓
2. Read Growth Plan, Part 7 docs, brand profile (geography: India)
3. Apply India seasonality: Q3 includes Dussehra-Diwali surge planning; Q4 includes wedding season prep
4. Build 4 quarterly themes
5. Detail 12 monthly sections with initiatives, dates, budget, KPIs
6. Schedule 6 major campaigns across the year (Q1: launch; Q2: growth-acceleration; Q3: festive; Q4: awards-PR push)
7. Map content pillars: Pillar A 40%, B 25%, C 20%, D 15% of annual production
8. Generate markdown + PDF + XLSX
9. Mark Part 8 complete
10. Brief: "Yearly Planner complete. 12 months, 6 major campaigns, 48 content pieces planned, 4 quarterly review checkpoints. Festive season Q3 has 2x normal budget pacing per Diwali surge. /digital-marketing-pro:engagement next moves to Part 9."
```

## Related skills

- `growth-plan` — companion deliverable; produced first
- `engagement-workflow` — orchestrates Part 8

## Related references

- [yearly-planner-template.md](../context-engine/yearly-planner-template.md) — canonical structure
- [growth-plan-template.md](../context-engine/growth-plan-template.md) — companion deliverable
- [india-market-context.md](../context-engine/india-market-context.md) — seasonality
- [reporting-cadence.md](../context-engine/reporting-cadence.md) — Section 8 QBR cadence
- [fixed-vs-variable-budget.md](../context-engine/fixed-vs-variable-budget.md) — monthly budget structure
