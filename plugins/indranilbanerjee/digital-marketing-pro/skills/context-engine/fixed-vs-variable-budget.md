# Fixed vs Variable Budget

Every monthly budget conversation should distinguish between Fixed and Variable budget. This separation turns budget management from a "can we spend more?" negotiation into a data-backed "here is where additional spend pays off" recommendation.

## The Two Buckets

### Fixed Budget

**Definition:** The committed monthly spend the client has agreed to. Covers always-on activity.

**What it covers:**

- Always-on paid campaigns (brand search, retargeting, baseline social ads)
- Always-on creative production (the steady cadence of new ads / content)
- Always-on infrastructure (martech subscriptions, agency retainer, content management)
- Baseline organic activity (SEO content production, organic social posting)

**Characteristics:**

- Predictable month to month
- Locked at the start of the period (typically annual)
- Adjusted only at quarterly or annual reviews
- Funds the engagement's core operating tempo

### Variable Budget

**Definition:** Additional budget that can be deployed when performance warrants. Held in reserve, deployed selectively.

**What it covers:**

- Scaling spend on campaigns delivering below target CPA
- Capturing spike opportunities (a piece of content goes viral, a competitor goes dark, a category trend hits)
- Funding A/B tests on new channels or creative concepts
- Responding to seasonal opportunities (festive surge, industry event, product launch)

**Characteristics:**

- Held at agency / marketing-team level
- Deployed via monthly recommendation conversation with client
- Authorised on case-by-case basis with data-backed justification
- Typically 15–30% of fixed budget held as Variable reserve

## The Monthly Variable Budget Conversation

This is the most consequential recurring conversation in the engagement. Every monthly report includes a Variable Budget Recommendation section that frames the conversation:

### Format

```markdown
## Variable Budget Recommendation — {Month}

### Available reserve: INR {X}

### Recommended deployment:

#### Opportunity 1: {Channel} — Scale below-target CPA campaigns
- Current performance: CPA INR {actual} vs target INR {target} ({% below target})
- Opportunity: increase budget by INR {amount} across [list of campaigns]
- Estimated additional outcome: {leads / customers / revenue}
- Estimated CPA at scale: INR {projected CPA} (still below target)
- Risk: scaling may push CPA up; suggested approach is graduated 15–20% increases per week

#### Opportunity 2: {Channel} — Test new audience / creative
- Current observation: [what we have learned that suggests the test would pay off]
- Test budget: INR {amount}
- Hypothesis: {what we expect to learn}
- Decision rule: [what would make us scale this further vs kill it]

#### Total recommended Variable deployment: INR {sum}
#### Variable reserve remaining: INR {residual}
```

### Approval flow

- The client reviews the recommendation
- Client approves all, some, or none of the recommendations
- Approved Variable spend is added to the month's deployment
- Performance of Variable-funded activity is reported separately the following month

## Why this discipline matters

Without the Fixed / Variable separation, marketing budget conversations devolve into one of two patterns:

**Pattern A — "Stay within budget":**

The agency hits a Fixed budget target every month and never asks for more, even when below-target CPA campaigns could scale profitably. Money sits in the client's account that should be working in the market.

**Pattern B — "Always ask for more":**

The agency asks for budget increases without specific data backing. The client reflexively says no. Trust degrades. Even legitimate scaling opportunities get rejected.

The Fixed / Variable framework solves both problems:

- Fixed budget is locked and predictable — the client knows what they are committing
- Variable budget creates a pre-authorised mechanism for scaling — the conversation is "should we deploy reserve toward this specific opportunity?" with data, not "give us more money"
- Both sides have skin in the game — the agency must justify Variable deployment with data; the client retains decision authority

## Sizing the Variable reserve

Recommended Variable reserve as % of Fixed budget by business stage:

| Stage | Variable reserve |
|---|---|
| Early-stage / proving channel | 10–15% (conservative — limited proven scaling opportunities yet) |
| Growth-stage with proven channels | 20–30% (substantial reserve to capture scaling opportunities) |
| Mature business optimising | 15–20% (smaller reserve; most opportunities already captured) |

The reserve sits in the marketing budget but is not committed. If unused at month-end, it rolls into the following month's reserve (does not become part of the next month's Fixed).

## What does NOT belong in Variable

- **Adding new channels** that were not in the strategic plan — that is a strategy change, not a Variable budget decision. Belongs in quarterly review.
- **Routine creative refreshes** — that is part of Fixed always-on production.
- **Emergency firefighting** that should have been planned for — re-examine the Fixed budget if this is recurring.
- **Vague "more spend would help"** without specific opportunity and outcome estimate.

## Variable spend reporting

The next month's report includes a Variable spend reckoning:

```markdown
## Prior Month Variable Spend Reckoning

| Variable spend | Approved | Outcome | Status |
|----------------|----------|---------|--------|
| Scale Google Search Brand campaign | INR 1.5L | +47 customers at INR 3,200 CPA (target was INR 3,500) | Approved as ongoing in Fixed for next month |
| Test LinkedIn Document Ads | INR 75K | 12 leads at CPL INR 6,250 (above INR 4,000 target) | Killed; learnings recorded |
| Capture Diwali surge | INR 2L | +ROAS 4.2 vs typical 2.8 | Surge ended; back to baseline |
```

The reckoning closes the loop and builds institutional knowledge about what kinds of Variable deployment work best for this brand.

## Where Fixed / Variable lives in the engagement

- **Growth Plan (Section 6 — Budget & Media Plan):** sets the year's Fixed budget by channel + the Variable reserve sizing
- **Yearly Planner:** distributes Fixed budget by month + flags expected Variable deployment windows (festive, product launches)
- **Monthly performance report (Section 7):** the Variable Budget Recommendation
- **Living Project Instruction File:** current month's Fixed spend, current Variable reserve remaining

## Related references

- [growth-plan-template.md](growth-plan-template.md) — Section 6
- [monthly-report-template.md](monthly-report-template.md) — Section 7 Variable Budget Recommendation
- [unit-economics-framework.md](unit-economics-framework.md) — LTV:CAC math that gates scaling decisions
- [in-market-out-market.md](in-market-out-market.md) — split logic that influences Fixed allocation
