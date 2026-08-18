# Unit Economics Framework

Every marketing strategy ultimately resolves to one question: does the revenue from a customer exceed the cost of acquiring them, by enough margin to sustain and grow the business?

If the answer is no, no amount of clever creative or sophisticated targeting will save the strategy. If the answer is yes, every channel decision becomes a question of how to scale efficiently.

This framework is the foundation. Every recommendation in this plugin — channel selection, budget allocation, campaign approval, scaling decisions — checks back to unit economics.

## The Core Metrics

### Customer Acquisition Cost (CAC)

```
CAC = Total marketing and sales cost / Number of new customers acquired
```

**What goes into Total marketing and sales cost:**

- Ad spend (Google, Meta, LinkedIn, TikTok, programmatic, etc.)
- Agency fees
- Marketing team salaries (loaded with benefits)
- Marketing software costs (CRM, CDP, MAP, analytics, design tools, etc.)
- Content creation costs (writers, designers, videographers, freelancers)
- Event costs (sponsorships, booths, hosted events)
- Sales team costs (for B2B, if marketing generates the leads sales convert)

**How to calculate CAC at multiple levels:**

- **Blended CAC:** total marketing+sales cost / total new customers. Headline number. Use for board reporting.
- **Channel CAC:** for each channel, what is the per-customer cost. Use for channel optimization.
- **Segment CAC:** for each customer segment, what is the per-customer cost. Use for segment prioritization.
- **Cohort CAC:** for each acquisition cohort (week or month), what was the CAC. Use for trend analysis.

Skills that recommend channel changes always cite Channel CAC, not Blended CAC.

### Lifetime Value (LTV)

```
LTV = Average revenue per customer × Average customer lifespan × Gross margin
```

**The gross margin is critical** — without it, LTV overstates the contribution to overheads and growth.

**Methods for calculating LTV:**

- **Cohort-based:** Take a cohort of customers acquired N months ago. Track their cumulative revenue. The longer N, the more accurate but the older the data.
- **Probabilistic:** Use survival analysis or BG/NBD models. Better for subscription businesses.
- **Predictive:** Use machine learning on customer attributes to predict LTV at acquisition. Useful for early-stage prediction.

For an early-stage business without historical data, **estimate LTV with explicit assumptions**:

> LTV estimate: ARPU INR 2,400 per month × estimated 14-month tenure × 65% gross margin = INR 21,840
> Assumption: 14-month tenure based on category benchmark; revisit when 12-month cohort data is available.

The estimate is acceptable as long as the assumptions are explicit and revisitable.

### LTV:CAC Ratio

```
LTV:CAC ratio = LTV / CAC
```

**Health thresholds (industry standard):**

| Ratio | Status | Implication |
|---|---|---|
| **≥ 3.0** | Healthy | Sustainable growth path. Scale with confidence. |
| **2.0–3.0** | Warning | Marginally profitable. Optimize CAC down or LTV up before scaling. |
| **< 2.0** | Critical | Marketing is destroying value. Stop scaling, fix unit economics first. |
| **> 5.0** | Investigate | Often signals under-investment in marketing — could grow faster with more spend. |

The 3.0 threshold is the **minimum** for sustainable business. Above 3.0 is healthy. Above 5.0 often signals under-investment — the business could grow faster by spending more.

### Payback Period

```
Payback Period = CAC / (Monthly contribution from average customer)
```

For subscription businesses, the payback period is critical. A long payback period means cash is tied up in customer acquisition; a short payback period means cash recycles quickly into more acquisition.

**Health benchmarks:**

| Period | Implication |
|---|---|
| < 12 months | Excellent for subscription business |
| 12–18 months | Healthy for B2B SaaS |
| 18–24 months | Manageable if LTV:CAC > 4 |
| > 24 months | Cash-strain risk; need strong balance sheet |

For non-subscription businesses (one-time purchase), payback is the contribution from the first purchase divided into CAC.

## Where these metrics live in the engagement

- **Core Doc 3.1 (Business & SBU Analysis), Step 4** — captures the unit economics for each SBU
- **Core Doc 3.4 (DMFlow), Step 5** — uses LTV:CAC to set channel budget allocation
- **Living Project Instruction File** — the current blended CAC, LTV, ratio, payback are visible in the "Currently True" section
- **Monthly performance report** — performance is reported by Channel CAC vs target, with trend
- **Quarterly strategy review** — full unit economics audit, adjustments to source docs if needed

## How recommendations check back to unit economics

Every channel recommendation, every budget allocation, every campaign approval should verify:

1. **Does this maintain LTV:CAC ≥ 3.0?** If not, recommendation must address why anyway (e.g., long-term brand investment with deferred ROI).
2. **Does this stay within payback tolerance?** If not, recommendation must address cash-flow impact.
3. **Is the LTV assumption still valid?** If channel mix shifts toward lower-LTV segments, blended LTV may decline — recalculate.

Skills that make recommendations without showing this check produce gut-feel suggestions that may destroy unit economics.

## Common mistakes

1. **CAC without sales-team cost (B2B).** If marketing generates the leads but sales closes them, sales cost is part of CAC. Excluding it makes marketing look more efficient than it is.

2. **LTV using gross revenue instead of margin-adjusted revenue.** A INR 10,000 sale at 30% gross margin contributes INR 3,000 to LTV — not INR 10,000. Margin matters.

3. **Calculating LTV from a single product purchase when the business depends on repeat.** For subscription / consumable businesses, LTV must include retention assumptions.

4. **Using industry-average LTV instead of brand-specific LTV.** Industry averages are starting points; brand-specific data always overrides.

5. **Not revisiting unit economics as the business scales.** CAC typically rises as you scale (audience saturation, more expensive bid environments). LTV may fall if scaling pulls in lower-quality customers. Recalculate quarterly.

6. **Ignoring payback in cash-constrained businesses.** A business with INR 3 crore in the bank and INR 50 lakh monthly burn cannot sustain a 24-month payback period regardless of how good the LTV:CAC looks.

## Tools the plugin uses

The plugin includes scripts that compute and track unit economics:

- `scripts/roi-calculator.py` — campaign-level ROI with attribution model selection
- `scripts/clv-calculator.py` — cohort-based and probabilistic LTV models
- `scripts/budget-optimizer.py` — channel budget reallocation honoring LTV:CAC constraints
- `scripts/revenue-forecaster.py` — revenue forecasting with seasonality
- `scripts/revenue-simulator.py` — Monte Carlo revenue simulation with scenarios
- `scripts/churn-predictor.py` — churn risk prediction informing LTV calculations

These scripts are called by skills as needed. They produce machine-readable output that Skills consume.

## Related references

- [four-core-documents-spec.md](four-core-documents-spec.md) — Core Doc 3.1 Step 4 (Unit Economics)
- [in-market-out-market.md](in-market-out-market.md) — budget split decisions
- [decision-framework.md](decision-framework.md) — multi-dimensional decision making
- [three-scenario-forecasting.md](three-scenario-forecasting.md) — projecting unit economics
