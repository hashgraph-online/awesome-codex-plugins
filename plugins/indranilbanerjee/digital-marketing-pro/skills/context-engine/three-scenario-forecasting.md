# Three-Scenario Forecasting

Every projection in this plugin — revenue forecast, campaign outcome, channel performance, growth trajectory — is presented as three scenarios, never as a single number.

A single number forecast destroys client trust the first time it is missed (which it will be). Three scenarios with explicit assumptions create a band of expectation that is honest about uncertainty and resilient to outcomes within the band.

## The Three Scenarios

### Conservative

**Definition:** What results look like if conditions are tough — competition increases, market softens, some campaigns underperform, execution delays occur.

**This is the floor.** The minimum the client should expect. If results fall below this, something fundamental went wrong and triggers an emergency review.

**Assumptions to use for Conservative:**

- Take the moderate baseline and reduce key inputs by 20–30%
- Assume one major channel underperforms by 30–50%
- Assume one major risk materialises (e.g., key competitor doubles ad spend, regulatory change, seasonality miss)
- Assume team / approval delays push some initiatives back by a month
- Apply the lower bound of conversion rate ranges, the upper bound of CAC ranges

### Moderate

**Definition:** What results look like under normal conditions with solid execution.

**This is the most likely scenario** and should be the planning baseline. Most decisions (budget, hiring, expectations setting) should reference this.

**Assumptions to use for Moderate:**

- Use historical performance benchmarks (yours if available, category benchmarks if not)
- Assume execution runs at typical agency / team competence (not exceptional, not poor)
- Assume no major external disruption
- Apply the midpoint of conversion rate ranges and CAC ranges
- Assume normal seasonality

### Aggressive

**Definition:** What results look like if everything goes well — campaigns outperform, market conditions favour the brand, scaling opportunities materialise faster than expected, no significant execution friction.

**This is the ceiling.** The upside the client should be aware of but not plan around.

**Assumptions to use for Aggressive:**

- Take the moderate baseline and increase key inputs by 20–30%
- Assume one or two campaigns produce outsized results (e.g., a content piece goes viral, a campaign concept resonates more than expected)
- Assume favourable market conditions (e.g., favourable regulatory change, competitor weakness, category tailwind)
- Apply the upper bound of conversion rate ranges, the lower bound of CAC ranges
- Assume capacity to capture upside (team is ready to scale fast)

## How to present three scenarios

Every forecast presented to the client must include all three scenarios with the assumptions for each.

### Format

```markdown
## Forecast — {Period} {Outcome}

| Scenario | Outcome | Key Assumptions |
|----------|---------|-----------------|
| **Conservative** | {value or range} | {2–3 key assumptions} |
| **Moderate** | {value or range} | {2–3 key assumptions} |
| **Aggressive** | {value or range} | {2–3 key assumptions} |

### Triggers that move us between scenarios

- We move toward Aggressive if: {specific signal 1}, {specific signal 2}
- We move toward Conservative if: {specific signal 1}, {specific signal 2}

### What we are watching

- {Metric or indicator 1 — what we will track to know which scenario is unfolding}
- {Metric or indicator 2}
```

## Worked example — Q1 Revenue Forecast for a B2B SaaS engagement

```markdown
## Forecast — Q1 2026 New ARR from Marketing-Sourced Pipeline

| Scenario | New ARR | Key Assumptions |
|----------|---------|-----------------|
| **Conservative** | INR 1.8 Crore | Google Ads CPL stays at INR 1,800 (current); LinkedIn Ads CPL rises 20% due to Q1 budget influx in category; close rate stays at current 18%; one large enterprise deal slips into Q2. |
| **Moderate** | INR 2.6 Crore | CPLs stay flat across channels; close rate improves to 22% as sales team adopts new lead-scoring; large enterprise deal closes in Q1 as forecast. |
| **Aggressive** | INR 3.4 Crore | Q1 industry conference produces 40+ qualified leads (vs typical 25); a planned product release closes the most-objected-to feature gap and lifts close rate to 27%; large enterprise deal closes plus one upsell. |

### Triggers that move us between scenarios

- Toward Aggressive: Industry conference attendance > 200, ad CPL drops 15%+, close rate above 25% by week 6
- Toward Conservative: Industry conference cancelled or under-attended, ad costs rise 25%+, sales team capacity drops below planned

### What we are watching

- Weekly: pipeline-generated, MQL-to-SQL conversion, ad CPL trend
- Monthly: close rate, enterprise deal stage progression, channel mix actuals vs plan
```

## Why three scenarios matter

1. **They prevent over-promising.** A single number is interpreted as a commitment. A range with assumptions is interpreted as honest forecasting.

2. **They make assumptions visible.** When the moderate scenario assumes a 22% close rate but the actual is 17%, the conversation is "the close-rate assumption was wrong, here is why" — not "your forecast was wrong, you under-delivered."

3. **They invite collaboration.** The client can challenge assumptions. "Why do you assume CPLs will stay flat? We are launching a new product that should pull bidders into the category." This produces a better forecast collaboratively.

4. **They define triggers for action.** If we hit Conservative-level signals by mid-quarter, the team knows to pivot. If we hit Aggressive-level signals, the team knows to scale.

5. **They protect against attribution disputes.** When results land in the Conservative-to-Aggressive band, the conversation is about which assumptions held vs not — not about whether the forecast was wrong.

## What three scenarios are NOT

- **Not "low / medium / high estimate" with no rigor.** Each scenario must have explicit assumptions.
- **Not a way to hide uncertainty by giving a wide band.** If Conservative is 30% of Moderate, the model is too uncertain — refine it before presenting.
- **Not a ceiling on accountability.** Aggressive is what is achievable with great execution; the team is still accountable to Moderate as the planning baseline.
- **Not a substitute for tracking.** The point of triggers and "what we are watching" is to know early which scenario is unfolding so the team can react.

## When to update scenarios

- **Monthly:** at the monthly performance review, scenarios for the remainder of the quarter are recalibrated based on actual data
- **At major events:** product launches, competitor moves, market shifts, regulatory changes
- **At quarterly strategy refresh:** full re-forecast for the next quarter with new scenarios

## Where forecasts live in the engagement

- **Core Doc 3.4 (DMFlow), Step 9:** strategic implications include forecast directionally
- **Growth Plan (Part 8):** Expected Outcomes section presents the three scenarios formally
- **Yearly Planner (Part 8):** annual forecast as three scenarios per quarter
- **Monthly performance reports:** actuals vs scenarios + recalibrated forward forecasts
- **Quarterly strategy refresh:** full re-forecast for the next quarter

## Related references

- [growth-plan-template.md](growth-plan-template.md) — Expected Outcomes section uses three scenarios
- [unit-economics-framework.md](unit-economics-framework.md) — CAC / LTV inputs to forecasts
- [monthly-report-template.md](monthly-report-template.md) — actuals vs scenarios reporting
