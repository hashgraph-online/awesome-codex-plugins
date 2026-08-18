# Marketing Mix Modeling — Framework & Implementation

## What is Marketing Mix Modeling?

Marketing Mix Modeling (MMM) is a statistical technique that quantifies the impact of each marketing channel (and external factors) on business outcomes — typically revenue or conversions. Unlike multi-touch attribution, MMM uses aggregate data (not user-level tracking), making it privacy-compliant by design and capable of measuring offline and non-clickable channels.

### When MMM is the Right Approach

| Use MMM When | Do Not Use MMM When |
|-------------|-------------------|
| You spend across 5+ channels and need to optimize allocation | You only use 1-2 channels (insufficient variance) |
| You need to measure TV, radio, OOH, or other offline channels | You need real-time, campaign-level optimization |
| Privacy restrictions limit user-level tracking | You have < 2 years of historical data |
| You want to quantify the impact of seasonality, promotions, or external factors | Your weekly spend per channel is < $1,000 (insufficient signal) |
| You need a strategic budget allocation framework | You need to attribute individual conversions to touchpoints |

---

## MMM vs Attribution vs Incrementality

| Dimension | MMM | Multi-Touch Attribution (MTA) | Incrementality Testing |
|-----------|-----|-------------------------------|----------------------|
| **Data level** | Aggregate (weekly/geo) | User-level | User or geo-level |
| **Privacy impact** | None (no user data) | High (requires tracking) | Low to moderate |
| **Channels covered** | All (including offline) | Digital clickable only | One channel at a time |
| **Time horizon** | Historical (2+ years ideal) | Real-time / recent | Point-in-time experiment |
| **Granularity** | Channel / tactic level | Touchpoint / campaign level | Single variable tested |
| **Latency** | Weeks to build model | Real-time | 2-8 weeks per test |
| **Best for** | Budget allocation across channels | Journey mapping, campaign optimization | Validating true lift of a specific tactic |
| **Limitation** | Cannot optimize within a channel | Biased by click-centric attribution | Only tests one thing at a time |
| **Recommended use** | Annual/quarterly budget planning | Daily/weekly campaign management | Validating MMM outputs |

**Use together:** MMM sets the strategic budget allocation. Attribution optimizes within channels. Incrementality tests validate both.

---

## Data Requirements Checklist

### Minimum Data Requirements

- [ ] **Time period:** 2+ years of weekly data (104+ data points minimum)
- [ ] **Dependent variable:** Weekly revenue, conversions, or other KPI
- [ ] **Marketing spend:** Weekly spend by channel (at minimum: Paid Search, Paid Social, Display, Email, TV, Radio, OOH, Affiliate — as applicable)
- [ ] **Impression / GRP data:** For channels where spend alone does not capture delivery (especially TV)
- [ ] **Pricing data:** Average selling price or discount depth per week
- [ ] **Promotion calendar:** Dates and types of all promotions (sale events, coupons, bundles)
- [ ] **Distribution changes:** Store openings/closings, new retail partners, website availability changes

### Recommended Additional Variables

- [ ] **Seasonality indicators:** Week of year, holiday flags, back-to-school, etc.
- [ ] **Macroeconomic data:** Consumer confidence index, unemployment rate, category trends
- [ ] **Competitive activity:** Competitor spend estimates (SimilarWeb/Pathmatics), competitor promotion flags
- [ ] **Weather data:** Temperature, precipitation (for relevant categories like beverages, apparel, travel)
- [ ] **PR / earned media:** Media mentions, share of voice, viral event flags
- [ ] **Product launches:** Dates of new product introductions
- [ ] **Platform changes:** iOS updates, algorithm changes, cookie deprecation milestones

### Data Quality Standards

| Requirement | Standard | Why It Matters |
|-------------|----------|---------------|
| Granularity | Weekly (not monthly) | Monthly data has too few observations and masks within-month variation |
| Consistency | Same definition applied across all weeks | Changing how a metric is calculated mid-dataset introduces bias |
| Completeness | No gaps in any time series | Missing weeks create errors in adstock calculations |
| Spend alignment | Spend recorded in the week the media ran, not when invoiced | Misaligned timing distorts cause-and-effect relationships |
| Currency consistency | All values in same currency, inflation-adjusted if > 3 years | Currency mixing distorts coefficient interpretation |

---

## Model Design Guidance

### Adstock Transformation

Advertising has a carryover effect — an ad seen this week still influences behavior next week. Adstock models this decay.

**Geometric adstock formula:**
```
Adstock_t = Spend_t + decay_rate * Adstock_(t-1)
```

| Channel | Typical Decay Rate | Half-Life (weeks) | Rationale |
|---------|-------------------|-------------------|-----------|
| TV | 0.70 - 0.85 | 2-4 | Brand awareness persists |
| Radio | 0.50 - 0.70 | 1-2 | Shorter memory than TV |
| OOH | 0.60 - 0.80 | 1.5-3 | Location-based reinforcement |
| Paid Search | 0.10 - 0.30 | < 1 | Intent-based, near-immediate response |
| Paid Social | 0.30 - 0.50 | 0.5-1 | Short carryover, frequent exposure |
| Display / Programmatic | 0.40 - 0.60 | 1-1.5 | Awareness lingers but fades |
| Email | 0.10 - 0.20 | < 0.5 | Near-immediate action |
| Content / SEO | 0.80 - 0.95 | 3-10+ | Compounding, long-lived asset |

### Diminishing Returns (Saturation)

Each additional dollar spent yields less incremental return. Model this with a Hill function or log transformation.

**Hill function:**
```
Response = Spend^alpha / (Spend^alpha + K^alpha)
```

Where:
- **alpha** controls the shape of the curve (steepness)
- **K** is the half-saturation point (spend level at which response reaches 50% of maximum)

**Interpretation guide:**

| Saturation Level | What It Means | Action |
|-----------------|---------------|--------|
| Well below saturation point | Incremental spend is highly efficient | Increase investment |
| Near saturation point | Diminishing returns beginning | Maintain or test small increases |
| Above saturation point | Additional spend has minimal incremental effect | Reallocate to under-saturated channels |

---

## Result Interpretation Guide

### Key Outputs from an MMM

| Output | Definition | How to Use It |
|--------|-----------|---------------|
| **Contribution %** | Share of total outcome (revenue) explained by each channel | Understand which channels drive the most volume |
| **ROI / ROAS** | Revenue generated per dollar spent on each channel | Identify most efficient channels |
| **Marginal ROI** | Revenue generated by the next dollar spent (at current spend level) | Optimize budget allocation (equalize marginal ROI across channels) |
| **Saturation curve** | Spend-response curve for each channel | Identify underspent and overspent channels |
| **Baseline** | Revenue that would occur without any marketing | Understand organic demand strength |
| **Adstock parameters** | Decay rate and peak lag for each channel | Understand carryover and timing effects |

### Interpreting the Budget Optimizer

The optimization should equalize **marginal ROI** across channels. The optimal allocation is where:
- Marginal ROI of Channel A = Marginal ROI of Channel B = ... = Marginal ROI of Channel N

**Reallocation decision framework:**

| Scenario | Current Marginal ROI | Optimal Action |
|----------|---------------------|---------------|
| Channel is under-saturated | High marginal ROI (> average) | Increase spend; expect incremental lift |
| Channel is over-saturated | Low marginal ROI (< average) | Decrease spend; reallocate to higher-ROI channels |
| Channel is near-optimal | Marginal ROI close to average | Maintain current spend |

### Red Flags in MMM Results

- [ ] A channel with known poor performance shows high ROI (possible confounding)
- [ ] Baseline is > 80% of total (marketing appears to have almost no impact — likely a model issue)
- [ ] Recommended reallocation suggests cutting a channel by > 50% (validate with incrementality test first)
- [ ] Adstock decay rates seem unreasonable (e.g., paid search decay > 0.8)
- [ ] Model R-squared is < 0.8 (significant unexplained variance)
- [ ] Out-of-sample MAPE (Mean Absolute Percentage Error) is > 15%

---

## Budget Optimization Using MMM

### Step-by-Step Process

1. **Run the model** with current data to establish baseline contribution and ROI by channel
2. **Generate saturation curves** for every channel to visualize diminishing returns
3. **Calculate marginal ROI** at current spend levels for every channel
4. **Run the optimizer** with total budget held constant to find the allocation that maximizes total revenue
5. **Apply business constraints** (minimum brand spend, contractual obligations, channel minimums)
6. **Generate scenarios** — Optimize at current budget, +10%, +20%, -10%, -20%
7. **Validate key recommendations** with incrementality tests before making large shifts
8. **Implement gradually** — Shift budgets 10-20% per quarter, not all at once
9. **Re-run the model** after 1-2 quarters with new data to assess impact

### Scenario Planning Template

| Scenario | Total Budget | Channel A | Channel B | Channel C | Channel D | Predicted Revenue | Predicted ROAS |
|----------|-------------|-----------|-----------|-----------|-----------|-------------------|---------------|
| Current allocation | $X | $X | $X | $X | $X | $X | X.Xx |
| MMM-optimized (same budget) | $X | $X | $X | $X | $X | $X | X.Xx |
| MMM-optimized (+10% budget) | $X | $X | $X | $X | $X | $X | X.Xx |
| MMM-optimized (+20% budget) | $X | $X | $X | $X | $X | $X | X.Xx |
| MMM-optimized (-10% budget) | $X | $X | $X | $X | $X | $X | X.Xx |

---

## Implementation Options

### Open-Source Frameworks

| Framework | Developer | Language | Strengths | Limitations |
|-----------|-----------|---------|-----------|-------------|
| **Robyn** | Meta | R (with Python wrapper) | Automated hyperparameter tuning via Nevergrad, built-in budget optimizer, strong community | Requires R environment, steep learning curve |
| **Meridian** | Google | Python | Bayesian approach, integrates with Google data, well-documented | Newer, smaller community |
| **LightweightMMM** | Google (predecessor to Meridian) | Python (JAX) | Bayesian, flexible priors, proven methodology | Being superseded by Meridian |
| **PyMC-Marketing** | PyMC Labs | Python | Fully Bayesian, highly customizable, strong statistical foundations | Requires Bayesian modeling expertise |

### Build vs Buy Decision

| Factor | Open-Source (Build) | Vendor Solution (Buy) |
|--------|-------------------|---------------------|
| Cost | Free software; internal team time | $50K-$300K+/year |
| Time to first model | 4-8 weeks (with experienced team) | 6-12 weeks (vendor onboarding) |
| Customization | Full control | Limited to vendor framework |
| Team required | Data scientist with marketing domain knowledge | Marketing analyst (vendor handles modeling) |
| Maintenance | Internal responsibility | Vendor-managed |
| Transparency | Full model visibility | Often black-box |
| Best for | Teams with data science capability and desire for control | Teams without data science resources |

---

## Validation Methodology

### In-Sample Validation

- **R-squared (adjusted):** Should be > 0.85 for a well-fitted model
- **Residual analysis:** Residuals should be normally distributed with no systematic pattern
- **Coefficient signs:** All channel coefficients should be positive (marketing should increase revenue)
- **VIF (Variance Inflation Factor):** Check for multicollinearity; VIF > 5 warrants investigation

### Out-of-Sample Validation

- **Holdout period:** Reserve the most recent 10-15% of data for validation
- **MAPE (Mean Absolute Percentage Error):** Target < 10%, acceptable < 15%
- **Prediction interval coverage:** Actual values should fall within the 90% prediction interval ~90% of the time

### External Validation

- **Incrementality test calibration:** Run a geo-lift or holdout test on a key channel and compare the measured lift to the MMM's predicted contribution. If they diverge by > 30%, recalibrate the model.
- **Business sense check:** Share results with channel managers. If anyone says "this doesn't match what I see operationally," investigate before publishing.
- **Cross-model comparison:** If possible, run a second modeling approach (e.g., Bayesian + Frequentist) and compare. Convergence increases confidence.

### Validation Checklist

- [ ] R-squared > 0.85
- [ ] MAPE < 15% on holdout data
- [ ] All channel coefficients have correct sign (positive)
- [ ] No multicollinearity issues (VIF < 5)
- [ ] Residuals show no systematic pattern
- [ ] Adstock parameters fall within reasonable ranges
- [ ] At least one incrementality test corroborates a key MMM finding
- [ ] Channel managers have reviewed and stress-tested results
- [ ] Saturation curves align with operational intuition
- [ ] Budget optimizer recommendations are directionally sensible

---

## MMM Program Maintenance

| Activity | Cadence | Owner |
|----------|---------|-------|
| Full model refresh (re-estimate all parameters) | Quarterly | Data Science |
| Data pipeline validation | Monthly | Analytics Engineering |
| New variable testing (add/remove controls) | Quarterly | Data Science + Marketing |
| Budget optimization scenario generation | Quarterly (before budget planning) | Data Science + Marketing Ops |
| Incrementality test for validation | 1-2 per quarter | Marketing + Data Science |
| Stakeholder results review | Quarterly | Marketing Leadership |
| Model documentation update | With each refresh | Data Science |
