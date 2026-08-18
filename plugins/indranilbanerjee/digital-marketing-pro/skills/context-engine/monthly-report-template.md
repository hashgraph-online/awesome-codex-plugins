# Monthly Report Template

Monthly reports are the primary communication tool with the client between strategic reviews. A good monthly report drives decisions; a bad one is just a data dump that nobody reads.

This template enforces the discipline that makes monthly reports useful.

## Structure

### Section 1: Executive Summary

**Length:** 3–5 sentences. No more.

**Content:**

- What happened this month (1 sentence)
- Are we on track to monthly / quarterly KPIs (1 sentence)
- The single most important thing the client should know (1–3 sentences)

The CEO reads this and stops if everything looks fine. Make it possible to absorb in 15 seconds.

### Section 2: KPI Dashboard

**Length:** 1 page.

**Content:**

- Visual overview of all primary + secondary KPIs vs targets
- Green / Yellow / Red status indicators
- Trend arrow (↑ / → / ↓) vs prior month and vs same month prior year
- One-line context per KPI ("Traffic up 18% MoM driven primarily by new SEO content")

Use a table or visual dashboard. Not a wall of text.

### Section 3: Channel Performance

**Length:** 2–4 pages, one sub-section per active channel.

For each channel:

- Performance vs target (with the actual numbers and the target)
- Trend vs prior month
- **Why** the result is what it is (this is the critical part — not "CPA increased" but "CPA increased because [specific reason] and here is what we are doing about it")
- Key wins this month (1–2 bullets)
- Key concerns this month (1–2 bullets)
- Specific actions taken during the month (proactive management evidence)

### Section 4: Creative Performance

**Length:** 1–2 pages.

**Content:**

- Top-performing ads / posts / content pieces (with visual examples)
- Bottom-performing ads / posts / content pieces (with visual examples)
- What we learned about what is working
- Creative refresh schedule for next month

Visual evidence is critical here. Embed actual screenshots / thumbnails.

### Section 5: Insights & Learnings

**Length:** 1 page.

**Content:**

- 3–5 specific insights the team learned this month
- What surprised us (data that did not match expectations)
- Hypotheses to test next month based on these learnings

This section captures the institutional learning. Without it, every month is starting from scratch.

### Section 6: Compliance & Quality

**Length:** ½ page.

**Content:**

- Compliance violations detected and resolved (count + summary)
- Brand voice consistency score (if applicable, from semantic checking)
- Content quality scores (composite eval scores)
- Any approval bottlenecks experienced

Most months this is a brief "all clear" — but when issues exist, they get visibility.

### Section 7: Variable Budget Recommendation

**Length:** ½ to 1 page.

**Content:**

- Which campaigns are below target CPA (candidates for budget increase)
- Estimated additional revenue if budget +X%
- New channel opportunities identified through testing this month
- Specific recommendation (with the math)

This section turns the budget conversation from "can we spend more?" to "here is where additional spend generates proven returns." See [fixed-vs-variable-budget.md](fixed-vs-variable-budget.md).

### Section 8: Next Month Plan

**Length:** ½ page.

**Content:**

- New campaigns launching
- A/B tests planned
- Optimisations queued
- Risks being monitored

### Section 9: Asks of the Client

**Length:** ½ page.

**Content:**

- Specific approvals needed (with deadlines)
- Information / assets needed from client team
- Decisions awaiting client input

If there are no client asks, say so explicitly. If there are, list them clearly with deadlines.

## Total Length Target

A monthly report should be **8–12 pages**. Beyond 15 pages, clients stop reading. Below 8 pages, depth is usually insufficient.

If a particular month requires a deeper analysis (e.g., the post-mortem of a campaign), produce that as a separate deliverable rather than bloating the standard report.

## Writing Principles

### 1. Lead with insight, not data

**Weak:** "Conversion rate: 2.1% (was 2.5%)."

**Strong:** "Conversion rate dropped 15% this month because our top-performing landing page had a 48-hour outage. Page is restored; expect rebound next month. Specific actions: [what we did]."

### 2. Always explain why, not just what

Numbers without context are noise. Every notable change needs a "because" with evidence.

### 3. Be honest about underperformance

Clients respect honesty and lose trust when agencies hide bad news. Bad performance with a clear explanation and action plan is better than bad performance with excuses.

### 4. Include visual evidence

- Screenshots of top-performing ads
- Heatmap findings on landing pages
- GA4 trend charts
- Performance comparison tables

A monthly report is part-narrative, part-visual. Both matter.

### 5. Distinguish "what we did" from "what happened"

- **What we did** (proactive management): "We A/B tested two landing page variants; variant B won by 14%; deployed; expect to see lift in November."
- **What happened** (results in the world): "Organic traffic grew 18% MoM, driven primarily by [specific drivers]."

Both belong in the report, but mixing them causes confusion.

### 6. Keep the structure consistent month-to-month

Clients build a mental model of the report structure over time. Inconsistent structure forces them to re-orient every month.

### 7. Close every loop from the prior month

If last month's report said "we will test X next month," this month's report says what happened with X. No silent dropping of past commitments.

## Cadence-Specific Reports

The plugin supports differentiated reports by cadence (see [reporting-cadence.md](reporting-cadence.md) for the full cadence framework):

- **Daily reports:** spend pace, anomalies, delivery status. Internal only, very brief.
- **Weekly reports:** campaign-level performance, creative, search terms. Internal team operating doc.
- **Monthly reports:** the structure above. Client-facing, primary communication tool.
- **Quarterly reports:** strategy refresh, full retrospective, scenario re-forecast. Client-facing, decision document.
- **Annual reports:** full year retrospective, new Growth Plan input. Client-facing, strategic.

## Production

Use:

```
/digital-marketing-pro:performance-report --cadence monthly --period 2026-04
```

The skill reads:

- Performance data from the cached daily pulls (GA4, ad platforms, CRM)
- KPI targets from the Growth Plan and Yearly Planner
- The prior month's report (to close loops)
- The Living Project Instruction File (for current truth)

And produces the 9-section report. Output lands at `engagements/{engagement-id}/reports/monthly/{period}-monthly-report.md` with PDF export.

## Related references

- [growth-plan-template.md](growth-plan-template.md) — KPIs are set in Section 7 of Growth Plan
- [yearly-planner-template.md](yearly-planner-template.md) — monthly targets cascade from Yearly Planner
- [fixed-vs-variable-budget.md](fixed-vs-variable-budget.md) — Section 7 framework
- [three-scenario-forecasting.md](three-scenario-forecasting.md) — actuals vs scenarios
