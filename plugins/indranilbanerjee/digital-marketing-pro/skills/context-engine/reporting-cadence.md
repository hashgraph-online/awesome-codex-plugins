# Reporting Cadence

Different metrics need different review frequencies. Checking everything daily produces noise-driven overreaction. Checking everything monthly produces slow response to issues. The cadence framework matches review frequency to decision velocity.

## The Five Cadences

| Cadence | Audience | What gets reviewed | Action threshold |
|---------|----------|---------------------|-------------------|
| **Daily** | Internal team | Spend pace, major anomalies, delivery status | Investigate if spend ±20% of daily target; check tracking if conversions = 0 |
| **Weekly** | Internal team | Campaign-level: CPC, CTR, CPA, ROAS by campaign; keyword performance; creative performance; search terms | Restructure if a campaign's CPA is 50%+ above target for 2 consecutive weeks; pause consistently underperforming keywords / creatives |
| **Monthly** | Client | Overall digital performance: blended CAC, total conversions, ROAS, traffic trends, SEO rankings | Present performance vs targets; identify top 3 wins, top 3 concerns; specific actions for next month; Variable budget recommendations |
| **Quarterly** | Client | Strategic metrics: market share indicators, brand search volume, LTV:CAC ratio, competitive position, strategy alignment | Full strategy review; adjust positioning if needed; reallocate budgets based on 3-month trends; update Yearly Planner |
| **Annually** | Client + Leadership | Full year review: revenue contribution, annual ROAS, market changes, competitive landscape shift, strategy refresh | New Growth Plan for next year; updated analysis; refreshed targeting; new creative direction |

## Daily — What and Why

**What gets reviewed:**

- Ad spend pacing (are we on monthly budget pace?)
- Major anomalies (unexpected spend spike, conversion drop to zero, ad disapproval, account suspension)
- Campaign delivery status (campaigns paused unexpectedly, creative rejected, tracking errors)

**Who reviews:** Internal media buyer / performance team. Not client-facing.

**Format:** Slack digest or dashboard. Text-light, signal-heavy.

**Action threshold:** If spend is more than 20% above or below daily target → investigate. If conversions drop to zero for any campaign → check tracking immediately.

**Common pitfall:** Treating daily noise as signal. A campaign with 30% above-target CPA on a single day is not failing — it is one data point. Wait for the weekly trend before action.

## Weekly — What and Why

**What gets reviewed:**

- Each campaign's performance vs target (CPC, CTR, CPA, ROAS)
- Keyword-level performance (Google Ads, SEO)
- Search terms report (queries triggering ads)
- Creative performance (which ads / posts are working)
- Audience performance (which audiences are converting)
- Landing page conversion rates
- Email programme performance (if active)

**Who reviews:** Internal performance team + agency PM. Not client-facing as a formal report (though insights surface in monthly).

**Format:** Internal review meeting + spreadsheet / dashboard.

**Action threshold:**

- Campaign with CPA 50%+ above target for 2 consecutive weeks → restructure
- Keyword with CTR below category benchmark consistently → pause or revise
- Creative with frequency above 3.5 (Meta) → refresh
- Landing page conversion below benchmark → add to CRO test queue

**Common pitfall:** Acting on insufficient sample size. A keyword with 50 impressions and 0 conversions is not "failing" — it is "unproven." Wait for meaningful volume before pausing.

## Monthly — What and Why

**What gets reviewed:**

- Blended CAC vs target
- Total conversions / leads / pipeline / revenue (depending on KPI)
- Channel-level ROAS
- Website traffic trends (organic, direct, referral, paid)
- SEO ranking changes (top keywords)
- Email programme performance
- Top-performing and bottom-performing creative
- Compliance and brand voice scores
- Variable budget recommendations

**Who reviews:** Client (primary recipient) + agency.

**Format:** Structured monthly report (see [monthly-report-template.md](monthly-report-template.md)).

**Action threshold:**

- Any KPI in red zone → escalation discussion at the next strategy session
- Top wins → consider scaling investment
- Top concerns → specific next-month actions
- Variable budget recommendations → client decision

**Common pitfall:** Reporting numbers without "why." A monthly report is not a data dump — it is a decision document. Lead with insight; back with data.

## Quarterly — What and Why

**What gets reviewed:**

- Strategic position changes (have we moved up or down vs competitors on key dimensions?)
- Market share / share-of-voice trends
- Brand search volume and direct traffic trends
- LTV:CAC ratio actuals vs assumed
- Cohort performance over the quarter
- Channel mix performance — should mix shift?
- Customer feedback themes
- Major competitor moves
- Strategy alignment — is what we are executing still what we should be executing?

**Who reviews:** Client leadership + agency leadership.

**Format:** Quarterly Business Review (QBR) — typically 1.5–2 hour meeting with structured pre-read deck.

**Action threshold:**

- Strategic drift detected → adjust Yearly Planner
- Major competitor shift → trigger v2 re-runs per [decision-matrix-rerun.md](decision-matrix-rerun.md)
- Channel mix should shift → revise Core Doc 3.4 (DMFlow) as v2.x
- KPI targets need recalibration → update Growth Plan Section 7

**Common pitfall:** Treating quarterly as a "bigger monthly." Quarterly is for strategic decisions, not tactical optimisation. Tactical issues belong in monthly.

## Annually — What and Why

**What gets reviewed:**

- Year-over-year revenue contribution from marketing
- Annual blended ROAS
- Market changes (category dynamics, regulation, technology shifts)
- Competitive landscape shift
- Brand health (recall, association, sentiment)
- Strategic refresh — what has fundamentally changed?
- Team and resource adequacy for next year's plan

**Who reviews:** Client leadership + agency leadership + (if relevant) board / investors.

**Format:** Annual review document + new Growth Plan + new Yearly Planner.

**Action threshold:**

- Always produces a new Growth Plan + Yearly Planner for the coming year
- May trigger major strategic shifts (new segments, new channels, new positioning) — if so, this is effectively a re-engagement and Parts 1–8 may be re-run
- Always recalibrates LTV / CAC / payback assumptions with full-year data

## Cadence collisions

Cadences nest:

- The week of the monthly report includes a weekly review (don't skip — they serve different purposes)
- The month of the quarterly review includes a monthly report (the monthly is the "data update"; the quarterly is the "strategic discussion")
- The quarter of the annual review includes a quarterly review (the quarterly is the data; the annual is the strategic refresh)

Each cadence stays focused on its own purpose. Don't compress quarterly thinking into a monthly report or expand monthly tactical detail into a quarterly review.

## Skipping cadences

Skipping a cadence is allowed only with explicit reason:

- **Skip a daily check:** acceptable if the team is on a planned offday and an automated alerting system covers anomalies
- **Skip a weekly review:** rarely acceptable; if needed, the next weekly should cover two weeks of data
- **Skip a monthly report:** never acceptable for active engagements; if absolutely necessary, an abbreviated update must still be sent
- **Skip a quarterly review:** never acceptable; a missed quarterly compounds into strategic drift
- **Skip an annual review:** never acceptable; engagement enters auto-renewal mode for another year of stale strategy

## How the plugin enforces cadence

The `/digital-marketing-pro:performance-report --cadence {daily|weekly|monthly|quarterly|annually}` command produces the appropriate report for each cadence.

Background scheduled tasks (when configured) automatically:

- Pull daily performance data (GA4, ad platforms)
- Generate daily anomaly digest
- Produce weekly performance summary
- Schedule monthly report production for the first business day after month-end
- Schedule quarterly review pre-read 5 business days before the QBR
- Schedule annual review prep 30 days before the year-end review

## Related references

- [monthly-report-template.md](monthly-report-template.md) — monthly report structure
- [growth-plan-template.md](growth-plan-template.md) — Section 7 KPI Framework defines what gets reviewed
- [yearly-planner-template.md](yearly-planner-template.md) — Section 8 quarterly review schedule
- [decision-matrix-rerun.md](decision-matrix-rerun.md) — quarterly strategic drift triggers
