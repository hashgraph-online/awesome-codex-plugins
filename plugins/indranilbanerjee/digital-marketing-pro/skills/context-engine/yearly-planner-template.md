# Yearly Planner Template

The Yearly Planner is the second client-facing deliverable produced in Part 8 of the engagement methodology. It complements the Growth Plan with a 12-month operating calendar that ties strategy to date-by-date execution.

If the Growth Plan answers *"How will we grow this business?"*, the Yearly Planner answers *"What will we do, week by week, month by month?"*

## Structure

### Section 1: Annual Themes

**Length:** 1 page.

**Content:**

- The 4 quarterly themes (one per quarter) that organise the year's marketing work
- Each theme stated in 1–2 sentences with strategic rationale
- How themes ladder into the overall positioning (Core Doc 3.3)

Example:

> Q1: Founder-led category education (build authority with TOFU thought leadership before launching demand-gen at scale)
> Q2: Demand generation activation (launch full-funnel campaigns; ramp paid spend with proven creative)
> Q3: Account expansion + community (deepen relationships with acquired accounts; launch customer community)
> Q4: Awards + festive amplification (festive surge in B2C-adjacent segments; awards / press push to lift brand)

### Section 2: Monthly Calendar

**Length:** 12 monthly sub-sections, ~1 page each.

For each month:

- **Theme:** one-sentence summary of the month's focus
- **Major initiatives:** 2–4 specific initiatives with owner and deadline
- **Always-on activity:** what continues from the prior month (typically: paid ads at fixed budget, organic posting cadence, email programme, SEO content production)
- **Key dates:** product launches, industry events, holidays/festivals relevant to the brand, planned PR moments
- **Content calendar overview:** themes per week, content pillars covered, target volume per channel
- **Budget:** monthly fixed spend by channel, variable budget reserve
- **KPI targets:** primary + 2–3 secondary KPIs for the month

### Section 3: Seasonal Strategy

**Length:** 1–2 pages.

**Content:**

- Industry-specific seasonality (when demand peaks and dips for this brand's category)
- Cultural / festival seasonality (relevant to the brand's geography — for India see [india-market-context.md](india-market-context.md))
- Pre-peak preparation windows (when to start building creative for festive, etc.)
- Post-peak follow-up windows (when to nurture recently acquired customers)

### Section 4: Campaign Architecture

**Length:** 2–3 pages.

**Content:**

- The major campaigns planned for the year (typically 4–8 campaigns with explicit identities)
- For each campaign: name, theme, target persona, primary channels, timing, KPIs, expected outcome
- The campaign naming convention (see Part 9.2 Campaign Strategy)
- How campaigns relate to always-on activity

### Section 5: Content Pillars Calendar

**Length:** 1–2 pages.

**Content:**

- The 3–5 content pillars (from Core Doc 3.3)
- Per-pillar production target for the year (volume per format)
- Quarterly distribution across pillars (how content mix shifts)
- Repurposing flow (how a long-form blog becomes social posts, video, email, etc.)

### Section 6: Channel-Specific Cadence

**Length:** 2–3 pages, one per channel family in scope.

For each active channel family:

- Posting / sending / publishing cadence (e.g., LinkedIn: 4 posts/week; Email: 1 broadcast/week + lifecycle flows; SEO: 6 articles/month)
- Volume targets for the year
- Quarterly emphasis shifts
- Resource requirements (creative production, copywriting, design, video)

### Section 7: Resource & Budget Pacing

**Length:** 2 pages with tables.

**Content:**

- Quarterly budget pacing (does spend ramp linearly, or front-loaded for Q1, or back-loaded for festive Q3 / Q4?)
- Per-quarter resource requirements (FTE equivalents, creative production volume, vendor spend)
- Cash-flow implications (working capital needed for paid media, deferred revenue from subscriptions, etc.)

### Section 8: Quarterly Review Schedule

**Length:** 1 page.

**Content:**

- Quarterly Business Review dates (when the strategy gets re-evaluated)
- Pre-QBR data preparation timeline (when each report is due before the QBR)
- QBR participants and decision authority
- What can be revised at QBR (channel mix, budget reallocation, persona priority) vs what is locked for the year (positioning, brand identity, major campaigns)

## Format and Tools

The Yearly Planner is delivered as:

- **A markdown file** (canonical, lives in the engagement directory)
- **An exported PDF** (for client distribution)
- **An exported XLSX** (the calendar in spreadsheet form for ongoing operational use)
- **(Optional) A shared Google Calendar / Notion / Airtable view** if the client uses these tools

The skill that produces the Yearly Planner generates all formats from the markdown source.

## Production approach

The Yearly Planner is produced **after the Growth Plan** because it operationalises the Growth Plan's strategic decisions into calendar form.

Use:

```
/digital-marketing-pro:engagement yearly-planner
```

The output lands at `engagements/{engagement-id}/part-08-growth-plan/yearly-planner.md` (with PDF + XLSX exports alongside).

## Quality Discipline

- **Every initiative has an owner.** "Marketing team will do X" is not actionable. "Persona research lead [name / role] will do X by [date]" is.
- **Every quarter has measurable KPI targets.** "Improve traffic" is not a target. "20% MoM organic traffic growth" is.
- **Always-on activity is distinguished from initiatives.** Always-on is the baseline that runs every month. Initiatives are time-bounded efforts on top.
- **The calendar respects realistic capacity.** A small team cannot sustain 6 major initiatives simultaneously. Sequencing prevents burnout.
- **The Yearly Planner is a living document.** It is reviewed and adjusted at each QBR. The first version is the plan; the version at end-of-year is the actual.

## Related references

- [growth-plan-template.md](growth-plan-template.md) — companion deliverable
- [engagement-flow-methodology.md](engagement-flow-methodology.md) — Part 8 in context
- [india-market-context.md](india-market-context.md) — seasonality patterns for India-operating brands
- [monthly-report-template.md](monthly-report-template.md) — how the Yearly Planner gets reviewed monthly
