# Incrementality Testing — Experiment Design

## Why Incrementality Testing Matters

Attribution models tell you which channels touched a conversion. Incrementality tests tell you which channels **caused** a conversion. The difference is critical: a channel can receive attribution credit for conversions that would have happened anyway (organic demand captured by paid). Incrementality testing isolates the true causal lift by comparing a treatment group (exposed to marketing) against a control group (not exposed).

---

## When to Use Each Measurement Approach

| Question | Best Method | Why |
|----------|-------------|-----|
| "How should I allocate budget across channels?" | MMM | Looks at all channels simultaneously with historical data |
| "Which touchpoints contribute to the customer journey?" | Multi-Touch Attribution | Maps user-level paths to conversion |
| "Does this specific channel actually drive incremental revenue?" | Incrementality Test | Isolates causal impact with controlled experiment |
| "Is my brand campaign actually generating demand?" | Incrementality Test (geo-lift) | Brand effects are hard to attribute; experiments measure true lift |
| "Should I increase spend on Facebook by 30%?" | Incrementality Test | Tests the marginal return of spend changes |
| "What is the long-term halo effect of TV on search?" | MMM | Captures cross-channel effects over time |

---

## Experiment Design Templates

### 1. Geo-Lift Test

**Purpose:** Measure the incremental impact of a channel or campaign by comparing treated geographies to control geographies.

**Best for:** Channels where user-level holdout is difficult (TV, radio, OOH, YouTube) or when platform-level conversion lift is unavailable.

| Design Element | Specification |
|---------------|---------------|
| **Test unit** | Geographic region (DMA, state, city, zip code cluster) |
| **Treatment group** | Geos where marketing activity is present (or increased) |
| **Control group** | Matched geos where marketing activity is withheld (or maintained at baseline) |
| **Matching method** | Synthetic control, propensity score matching, or manual matching on key variables |
| **Key matching variables** | Baseline revenue, population, seasonality pattern, historical growth rate |
| **Test duration** | 4-8 weeks (depends on conversion cycle and required power) |
| **Cooldown period** | 1-2 weeks post-test to capture delayed conversions |
| **Primary metric** | Incremental revenue (or conversions) in treatment vs control |
| **Secondary metrics** | iROAS, CPA, brand search lift, new customer % |

**Step-by-step guide:**

1. **Define the hypothesis** — "Increasing Facebook spend by 50% in treatment geos will generate incremental revenue with an iROAS > 2.0"
2. **Select geos** — Pull 12-24 months of historical weekly revenue by geo. Identify 4-10 treatment geos and 10-20 potential control geos.
3. **Match geos** — Use synthetic control methods (CausalImpact in R, GeoLift by Meta) to find the control group that best replicates treatment group's pre-test behavior.
4. **Validate the match** — Run a pre-test "placebo" period. The synthetic control should track the treatment group within 2-3% during the pre-test period.
5. **Run the test** — Implement the treatment (increase/decrease spend) only in treatment geos. Change nothing in control geos.
6. **Monitor weekly** — Track for data quality issues but avoid making mid-test changes.
7. **Analyze results** — Compare actual treatment performance vs synthetic control prediction. Calculate lift, confidence interval, and iROAS.
8. **Validate** — Check that the lift is statistically significant (p < 0.10 for marketing tests) and economically meaningful.

### 2. User-Level Holdout Test

**Purpose:** Randomly withhold marketing from a subset of users to measure incremental lift.

**Best for:** Email, push notifications, retargeting, CRM campaigns.

| Design Element | Specification |
|---------------|---------------|
| **Test unit** | Individual user (cookie, email, device ID) |
| **Treatment group** | Users who receive the marketing activity |
| **Control group** | Randomly held-out users who do NOT receive the activity |
| **Randomization** | True random assignment at user level (not session level) |
| **Control size** | 10-20% of eligible audience (balance power vs revenue risk) |
| **Test duration** | 2-4 weeks (or 1 full conversion cycle, whichever is longer) |
| **Primary metric** | Conversion rate or revenue per user (treatment vs control) |

**Key considerations:**
- Control group must be truly held out — no ad exposure, no email, no retargeting
- Ensure randomization is at the user level, not the session level (prevents contamination)
- Track both groups for the same duration, including post-exposure conversion window

### 3. Platform Conversion Lift Tests

These are built-in incrementality tools provided by ad platforms.

**Meta Conversion Lift:**

| Element | Detail |
|---------|--------|
| **How it works** | Meta randomly splits your target audience into test (sees ads) and control (does not). Measures conversion lift. |
| **Setup** | Through Meta Experiments in Ads Manager or via API |
| **Minimum requirements** | ~$10K+ spend during test, sufficient conversion volume (~100+ conversions in control) |
| **Duration** | 2-4 weeks recommended |
| **Outputs** | Incremental conversions, incremental revenue, cost per incremental conversion, lift % |
| **Limitation** | Only measures Meta's own impact; control group may still see competitor ads |

**Google Conversion Lift:**

| Element | Detail |
|---------|--------|
| **How it works** | Google uses geo-based or user-based experiments to measure incremental conversions from Google Ads |
| **Setup** | Through Google Ads Experiments (requires Google rep for geo-based) |
| **Types** | Brand Lift (surveys), Search Lift (incremental searches), Conversion Lift (incremental conversions) |
| **Minimum requirements** | Significant spend (typically $50K+ for reliable results) |
| **Duration** | 2-6 weeks |
| **Outputs** | Incremental conversions, relative lift, cost per incremental conversion |

---

## Statistical Power Calculations

### Why Power Matters

A test without sufficient statistical power will produce inconclusive results. Running an underpowered test wastes time and budget. Calculate power **before** starting.

### Key Parameters

| Parameter | Definition | Typical Value |
|-----------|-----------|---------------|
| **Significance level (alpha)** | Probability of false positive (Type I error) | 0.10 for marketing (0.05 for strict) |
| **Power (1 - beta)** | Probability of detecting a true effect | 0.80 (80%) minimum |
| **Minimum Detectable Effect (MDE)** | Smallest lift you need to detect | Depends on business context (typically 5-20%) |
| **Baseline conversion rate** | Current conversion rate without treatment | From historical data |
| **Sample size / test duration** | Number of users or geo-weeks needed | Calculated from above parameters |

### Power Calculation Rules of Thumb

| Baseline CVR | MDE (Relative) | Approximate Sample Size per Group |
|-------------|----------------|----------------------------------|
| 1% | 20% | ~80,000 |
| 1% | 10% | ~320,000 |
| 3% | 20% | ~25,000 |
| 3% | 10% | ~100,000 |
| 5% | 20% | ~15,000 |
| 5% | 10% | ~60,000 |
| 10% | 20% | ~7,000 |
| 10% | 10% | ~28,000 |

*Based on two-sided test, alpha=0.05, power=0.80. For alpha=0.10 (common in marketing), sample sizes are ~20% lower.*

### Duration Calculation

```
Test Duration (weeks) = Required Sample Size / Weekly Eligible Users
```

If the required duration exceeds 8 weeks, you have three options:
1. Increase the MDE (accept you can only detect larger effects)
2. Relax alpha to 0.10
3. Increase test group size (reduce control holdout percentage)

---

## Result Analysis Framework

### Calculating Incremental ROAS (iROAS)

```
iROAS = (Revenue_treatment - Revenue_control_projected) / Incremental_Spend
```

Where:
- **Revenue_treatment** = Actual revenue in treatment group/geos
- **Revenue_control_projected** = Control group revenue scaled to treatment group size (or synthetic control prediction)
- **Incremental_Spend** = Additional spend in treatment vs what control would have received

### Interpreting Results

| Result | iROAS | Interpretation | Action |
|--------|-------|---------------|--------|
| Strong positive | > 3.0 | Channel is highly incremental | Scale spend (test at higher level) |
| Moderate positive | 1.5 - 3.0 | Channel is incremental but efficiency varies | Maintain spend; optimize targeting/creative |
| Marginal positive | 1.0 - 1.5 | Channel is barely incremental | Investigate segments; may be worth it for specific audiences only |
| Break-even | ~1.0 | Incremental revenue equals spend | Not profitable on a direct-response basis; evaluate brand value |
| Negative | < 1.0 | Channel is not generating sufficient incremental return | Reduce spend; reallocate budget |
| No significant lift | CI includes 0 | Cannot confirm channel has incremental impact | Test was underpowered or channel is truly not incremental; redesign test |

### Confidence Interval Interpretation

Always report confidence intervals, not just point estimates.

| Scenario | 90% CI for Lift | Interpretation |
|----------|----------------|---------------|
| Significant positive | [5%, 15%] | Confident lift is real; point estimate ~10% |
| Significant positive (wide) | [2%, 30%] | Lift is real but uncertain in magnitude; larger test needed for precision |
| Not significant | [-3%, 12%] | Cannot conclude lift is different from zero; underpowered or no effect |
| Significant negative | [-15%, -3%] | Marketing may have negative impact (rare; investigate data quality) |

---

## Common Pitfalls

### Design Pitfalls

| Pitfall | Problem | Prevention |
|---------|---------|------------|
| **Contamination** | Control group is exposed to treatment through spillover | Use geo-level tests for broad-reach channels; ensure user-level holdouts are truly held out |
| **Selection bias** | Treatment and control groups differ at baseline | Validate match quality in pre-test period; use randomization where possible |
| **Insufficient power** | Test ends without statistically significant result | Run power calculations before testing; extend duration if needed |
| **Too short duration** | Test ends before full conversion cycle completes | Test duration should be at least 1.5x the average conversion cycle |
| **Seasonality confound** | Test runs during an atypical period (Black Friday, summer lull) | Avoid major seasonal events or account for them in analysis |

### Analysis Pitfalls

| Pitfall | Problem | Prevention |
|---------|---------|------------|
| **Peeking** | Checking results before test completes and stopping early | Pre-commit to test duration; use sequential testing methods if early stopping is needed |
| **Multiple comparisons** | Testing many segments inflates false positive rate | Pre-specify primary metric; use Bonferroni correction for secondary analyses |
| **Ignoring novelty** | Initial lift from a new tactic fades as novelty wears off | Extend test duration or run a follow-up test 3 months later |
| **Extrapolation** | Assuming results from one test level apply at all spend levels | iROAS at $50K/week does not equal iROAS at $200K/week (diminishing returns) |
| **Platform bias** | Trusting platform-run lift tests without scrutiny | Cross-validate with independent geo-lift tests |

---

## Incrementality Testing Roadmap

### Prioritization Framework

| Channel | Current Spend | Attribution ROAS | Confidence in Attribution | Incrementality Test Priority |
|---------|-------------|-----------------|--------------------------|----------------------------|
| Branded Search | High | Very High | Low (would convert anyway) | **High** — likely over-attributed |
| Retargeting | Medium | High | Low (selection bias) | **High** — targeting converters, not causing conversions |
| Prospecting Social | High | Medium | Medium | **Medium** — test to calibrate |
| Non-Brand Search | Medium | Medium | Medium-High | **Low** — likely fairly attributed |
| TV / Video | High | Low/None | Very Low | **High** — no attribution data; MMM + geo-lift needed |
| Email Flows | Low | High | Medium | **Medium** — holdout test is easy |

### Annual Testing Calendar Template

| Quarter | Test | Channel | Design | Objective |
|---------|------|---------|--------|-----------|
| Q1 | Branded Search Holdout | Google Ads | Geo-lift (pause brand in test geos) | Determine how much brand search is truly incremental |
| Q1 | Retargeting Holdout | Meta | User-level holdout (10% control) | Measure true retargeting lift vs organic return |
| Q2 | Prospecting Scale Test | Meta | Geo-lift (+50% spend in test geos) | Determine iROAS at higher spend level |
| Q2 | Email Flow Holdout | Email | User-level holdout (15% control) | Measure incremental revenue from automated flows |
| Q3 | TV / YouTube Geo-Lift | YouTube/TV | Geo-lift (introduce in new geos) | Measure upper-funnel incremental impact |
| Q3 | Non-Brand Search Scale | Google Ads | Geo-lift (+30% budget in test geos) | Validate MMM-recommended budget increase |
| Q4 | Peak Season Holdout | Meta + Google | Reduced test activity during Q4 | Measure whether peak-season spending is incremental or capturing organic demand |

---

## Implementation Checklist

- [ ] Identified top 3 channels to test based on spend and attribution confidence gap
- [ ] Defined hypothesis, primary metric, and success criteria for each test
- [ ] Completed power calculations and confirmed sufficient sample size
- [ ] Selected test design (geo-lift, user holdout, platform conversion lift)
- [ ] Matched treatment and control groups with validated pre-test alignment
- [ ] Documented the test plan including start date, end date, and analysis method
- [ ] Configured monitoring to detect data quality issues during the test
- [ ] Committed to no changes in treatment or control during the test period
- [ ] Analyzed results with confidence intervals, not just point estimates
- [ ] Shared findings with stakeholders and documented in a test log
- [ ] Used results to calibrate MMM or update budget allocation
- [ ] Scheduled the next round of tests based on the annual roadmap
