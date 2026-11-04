# Measurement Framework: KPIs, North Stars, Cadence

Every plan needs a measurement section that tells the team how to know if the plan is working. This doc is the source for Section 13's measurement subsection.

**Related docs:**
- `growth-patterns.md`: linear, step-function, and layered-curve scenarios
- `budget-planning.md`: blended-CAC evidence and low/base/high scenario limits

## The north-star principle

A north star is one metric that captures the business-model thesis at the highest level. It should:
- Be derivable from the funnel + revenue model
- Move slowly enough to be a strategic compass (not whipsawed by weekly noise)
- Trade off correctly against other metrics: improving the north star should generally improve the business

Don't default to "ARR" or "MRR" alone. Those are outcomes, not norths. Pick something that captures the business model.

## North-star patterns by business model

### B2B SaaS (subscription)
- **Net Revenue Retention (NRR)**: keeps existing customers + expansion in focus
- Alternative: "Logo retention × expansion ARR"
- Why: ARR alone hides churn / lets gross-add growth mask product fit problems

### D2C consumer app (subscription)
- **Blended LTV / blended CAC**: keeps unit economics honest as paid layer scales
- Alternative: "Day-35 paid users from cohort × LTV"
- Why: monthly subscription metrics are volatile; cohort × LTV smooths it

### Hybrid hardware + software (e.g., Quietude)
- **Blended LTV / blended CAC across hardware + software**: captures the wedge thesis
- Alternative: "Hardware-buyers-to-subscriber conversion × blended margin"
- Why: hardware revenue isn't free (cost to make); subscription revenue isn't expensive to acquire if hardware funds it

### Marketplace (two-sided)
- **Liquidity ratio × take-rate**: captures both sides + monetization
- Alternative: "Monthly transacting users × take-rate × repeat frequency"
- Why: GMV alone doesn't capture whether the marketplace is becoming a habit

### Developer tool / open source
- **Weekly active developers × paid-conversion**: captures both adoption and monetization
- Alternative: "Weekly active orgs × seats per org × ARPU"

### Content / media business
- **Daily active readers / listeners × ad revenue per session**: captures both reach and monetization
- Alternative: "Subscriber count × retention × ARPU"

### Commerce (DTC, non-subscription)
- **Repeat purchase rate × AOV × frequency**: captures monetization layered on quality of customer
- Alternative: "Customer LTV / CAC × payback period"

## Leading indicators by AARRR stage

After the north star, every plan needs leading indicators per AARRR stage. These move faster than the north star and trigger investigations.

### Acquisition leading indicators
- Organic visits/month, total + per pillar (SEO health)
- App Store / Play Store visit-to-install rate (ASO health)
- Founder-led social channel growth → email subscriber conversion (LinkedIn / X / Substack funnels)
- Event-to-app conversion rate (event ROI)
- Ambassador-attributed visits (referral funnel)
- Paid CAC by channel (when paid is firing)

### Activation leading indicators
- Day 1 / Day 7 / Day 35 → paid conversion rate
- Onboarding session-completion rate
- First key-action completion (post-signup activation event)
- App Store conversion rate (install → trial → paid)
- Trial → paid conversion rate

### Retention leading indicators
- Day 30 / Day 60 / Day 90 retention
- Monthly churn rate (gross + net)
- Lifecycle email engagement (open / click / unsubscribe by flow)
- Hardware → app activation rate (for hybrid businesses)
- Win-back / reactivation rate

### Referral leading indicators
- Ambassador-attributed new subs (via Dub or similar)
- Share-after-value moment rate (% of users sharing)
- Two-sided referral completion rate
- Guides program referrals (when live)
- NPS score (if surveyed)

### Revenue leading indicators
- ARPU by cohort
- Annual plan adoption %
- Cohort LTV by source
- Plan mix shifts
- Eye-mask / hardware attach rate (for hybrid)
- Expansion revenue (B2B)

## Review cadence

The plan should specify decision rhythms that match data latency, operational
capacity, and the accountable owner's needs. Weekly, monthly, and quarterly are
labels for consideration, not mandatory frequencies.

### Operational sync
- **Who:** named workflow owners and decision maker
- **When:** chosen from execution cadence and signal latency
- **Format:** source-backed AARRR changes, shipped artifacts, blockers, and
  decisions due
- **Output:** owner-assigned actions and recorded decisions

### Metrics review
- **Who:** accountable business owner plus only the required operators/reviewers
- **When:** chosen from cohort maturity and reporting latency
- **Format:** full metric definitions, source/as-of dates, scenario comparison,
  qualitative evidence, and option reprioritization
- **Output:** documented continue/adjust/pause decisions, including unresolved
  capacity questions rather than assumed hiring

### Plan recalibration
- **Who:** named plan owner, executive decision maker, and required reviewers
- **When:** the chosen planning interval or an explicit trigger fires
- **Format:** plan review against evidence ranges and decision rules,
  channel-level analysis, resource/approval changes, and next-interval scenarios
- **Output:** versioned plan decision with owners and review dates

## KPI target setting

For each planning interval in Section 10, include 3–5 source-backed KPI decision
rules only when a baseline exists. These should be:
- **Specific**: name metric definition, cohort, baseline, source, and as-of date
- **Measurable**: pull from a wired data source
- **Scenario-bounded**: show low/base/high cases from historical patterns or
  label assumptions unverified
- **Decision-triggering**: name owner, review date, and hit/miss action

### KPI target patterns by decision state

- **Repair:** verify a known defect is removed using a dated baseline, acceptance
  readback, owner, and regression guard.
- **Instrument:** ship the measurement path and prove event/count reconciliation
  before setting a performance target.
- **Validate:** compare a new cohort or bounded test with its pre-registered
  baseline and decision rule.
- **Expand:** increase exposure only within an approved ceiling while the
  measured guardrails hold.
- **Compound:** test whether multiple channels or loops add incremental value;
  do not infer attribution from correlated movement.

Any of these states may occur in any quarter. Calendar position, company stage,
or a financing event does not choose the state or target.

## Selecting a Growth Scenario

Do not impose a stage-based growth multiple. Build low/base/high scenarios from
the client's dated retention, margin, capacity, pipeline, and cash evidence.
External benchmarks may be shown only with a current source, cohort definition,
and explicit note that they are context rather than a target.

## Forecasting reality check

A plan derives a budget and an annual goal. It does not produce a 12-month month-by-month forecast that's reliably accurate to the dollar.

Forecast confidence depends on the model, data history, input stability, and
operating process: not listing status or ARR. Label every projection with its
source dates, assumptions, range, limitations, owner, and recalibration rule.
Treat unsupported point estimates as illustrative scenarios.

What the plan commits to honestly:
- The annual goal is a defensible direction-of-travel
- The budget is the resource commitment that makes the goal plausible
- The 90-day roadmap (Section 9) is what's actionable now
- Month-to-month projection is illustrative, not promised

Founders who over-engineer the forecast end up explaining variance every month instead of executing. The plan should resist this, name the annual target, the quarterly KPIs, and the kill criteria. Don't promise the month.

Full context in `budget-planning.md`.

## Kill criteria

For every channel or initiative, the plan should specify when to stop. Often missing from plans, kill criteria force discipline.

Template:

> If `{metric, definition, cohort}` crosses `{threshold approved by owner}` after
> `{minimum evidence window/sample/exposure}`, `{named owner}` pauses or changes
> `{scope}` on `{review date}`. Source: `{artifact and as-of date}`.

Thresholds must come from the client's baseline, economics, safety boundary, or
a current cited comparator with a matched cohort. If evidence is insufficient,
the rule is an instrumentation or evidence-collection checkpoint, not a
fabricated performance cutoff.

## Guardrail metrics

Some metrics get a hard guardrail (cannot drop below threshold). Useful for protecting brand or unit economics during aggressive growth.

Record guardrails in this auditable form:

| Metric definition | Threshold/range | Source and as-of | Owner | Minimum evidence | Triggered action | Review |
|---|---|---|---|---|---|---|

The accountable owner approves every threshold and action before launch.
Platform ratings, complaint rates, CAC, and similar metrics have no universal
cutoff in this skill.

## Data sources mapping

The plan should name where each metric comes from. This makes it auditable.

| Metric | Source |
|---|---|
| Organic traffic | GA4 / Ahrefs |
| App Store conversion | App Store Connect |
| Funnel conversion (Day N → paid) | Internal analytics (Mixpanel / Amplitude) or App Store Connect cohort export |
| Retention | Customer.io segments + product analytics |
| MRR / ARR | Stripe (via MCP if wired) |
| Plan mix | Stripe |
| Lifecycle email metrics | Customer.io |
| Ambassador attribution | Dub.co |
| Hardware → app activation | Shopify + App Store + internal join |
| NPS | Survey tool (Customer.io / Typeform / SurveyMonkey) |

## When data isn't wired

If a metric can't currently be measured, flag it in Section 13's open decisions. Example:

> "Hardware → app activation rate not currently visible in the App Store dashboard. Requires Shopify ↔ App Store Connect join. Q1 work item."

A plan with un-measurable goals is a plan that can't be validated. Surface the instrumentation work explicitly.

## Reporting cadence + automation

Where possible, discover currently callable, authorized data sources and
automate a review only after confirming schemas, owners, and data boundaries.
Otherwise produce a manual Markdown review from user-supplied exports. Choose an
email, sheet, or dashboard from audience, decision cadence, maintenance
capacity, and approved tooling: not from funding stage.
