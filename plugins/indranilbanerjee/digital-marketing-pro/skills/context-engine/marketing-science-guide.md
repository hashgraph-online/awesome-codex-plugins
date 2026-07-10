# Marketing Science Guide

Reference knowledge for marketing science, causal inference, predictive modeling, and experimentation rigor. Use this to ground recommendations in statistical methods rather than gut feel.

---

## 1. Bayesian Marketing Mix Modeling (MMM)

### What It Is
A statistical model that decomposes revenue (or conversions) into contributions from each marketing channel plus external factors. Unlike attribution models that assign credit to touchpoints, MMM works with aggregate data and captures offline + online effects together.

### Why Bayesian Over Frequentist
- **Uncertainty quantification**: Produces credible intervals, not point estimates — "TV drives $120K-$180K/month" is more useful than "TV drives $150K"
- **Works with limited data**: Bayesian priors compensate when you have fewer than 3 years of data
- **Incorporates domain knowledge**: Set priors from industry benchmarks (e.g., "TV adstock half-life is typically 3-6 weeks") to regularize estimates
- **Handles collinearity better**: Channels that always spend together (common in marketing) cause instability in frequentist models; priors stabilize Bayesian estimates
- **Iterative updating**: As new data arrives, update the posterior without rebuilding from scratch

### Key Components
- **Adstock transformation**: Models the carryover effect of advertising — a TV ad seen today still influences purchases next week. Parameterized by decay rate (how fast the effect fades) and optionally lag (delay before peak effect). Geometric adstock: `adstock_t = spend_t + decay * adstock_{t-1}`. Typical decay rates: TV 0.7-0.9, digital display 0.3-0.5, search 0.1-0.2, social 0.3-0.6
- **Saturation curves**: Model diminishing returns — the first $10K on Facebook drives more incrementals than the tenth $10K. Hill function: `response = max_response * (spend^slope) / (half_saturation^slope + spend^slope)`. The half-saturation parameter (K) represents the spend level at which you get 50% of maximum response
- **Time-varying coefficients**: Seasonality, trend, and regime changes. December TV effectiveness differs from March. Use Fourier terms or hierarchical time effects
- **Control variables**: Price changes, promotions, competitor activity, weather, holidays, macroeconomic shifts, COVID impacts, product launches

### Data Requirements
- **Minimum**: 2 years of weekly data (104 observations). 3+ years preferred
- **Channel data**: Weekly spend per channel (not impressions — spend is the decision variable)
- **Response variable**: Weekly revenue, conversions, or leads
- **External factors**: Weather indices, holiday flags, competitor spend (if available), economic indicators
- **Granularity**: Weekly is standard. Daily adds noise without improving signal for most channels. Monthly loses too much information

### Interpreting Results
- **Channel contribution %**: What fraction of total revenue each channel drives (including baseline/organic)
- **ROI per channel**: Revenue generated per dollar spent, with credible intervals
- **Marginal ROI**: The return on the NEXT dollar spent (more useful than average ROI for budget decisions)
- **Optimal budget allocation**: Shift budget from channels with low marginal ROI to channels with high marginal ROI until marginal ROIs equalize
- **Saturation points**: Where each channel hits diminishing returns — the spend level beyond which marginal ROI drops below your threshold (typically 1.0x or your cost of capital)

---

## 2. Incrementality Testing

### Geo-Lift Tests
Split geographic markets into test and control groups. Run the campaign only in test markets. Measure the lift in test vs control after accounting for pre-existing differences.
- **Design**: Minimum 10 geographic units (DMA, state, city). Randomize or match on pre-period performance. Run for minimum 4 weeks (8+ preferred for brand campaigns)
- **Power**: Need sufficient volume per geo. Rule of thumb — each geo needs 100+ conversions/week for conversion-based measurement
- **Analysis**: Difference-in-differences with geo fixed effects. Report lift %, confidence interval, and cost-per-incremental-conversion
- **Pitfalls**: Spillover between adjacent geos (use buffer zones), seasonal effects (ensure test period is representative), small sample sizes (geos are the unit, not users)

### Holdout Analysis
Withhold the campaign from a random 10-20% of the eligible audience. Compare conversion rates between exposed and holdout groups.
- **Advantage**: User-level randomization is cleaner than geo-level
- **Disadvantage**: Opportunity cost of not serving 10-20% of audience; contamination if holdout users see ads through other paths
- **Best for**: Retargeting campaigns, email campaigns, CRM audiences where you control the user list

### Synthetic Control Method
When you cannot randomize, construct a statistical counterfactual from a weighted combination of control units that matches the pre-period behavior of the treated unit.
- **Use case**: "We launched in a new market — what would have happened without marketing?"
- **Method**: Find weights for control markets such that the weighted combination closely matches the treated market's pre-period outcome trajectory
- **Advantage**: Works with as few as 1 treated unit (single market launch)
- **Limitation**: Requires a sufficient pool of untreated control units with similar characteristics

### Ghost Ads / PSA Methodology
In programmatic environments, show a PSA (public service announcement) to the control group in the same auction. Both groups win the same auctions, but control sees a non-commercial ad.
- **Cleanest digital incrementality method**: Controls for selection bias in ad targeting
- **Measures**: True incremental lift of the creative/message, not just the targeting

### Matched Market Testing
Pair similar markets based on historical performance, demographics, and market characteristics. Assign one market in each pair to treatment, the other to control. Alternating treatment across pairs improves balance.

---

## 3. Causal Inference for Marketers

### Why Correlation Does Not Equal Causation
Spending more on branded search correlates with higher revenue — but branded search captures existing demand rather than creating it. Cutting branded search might lose very little incremental revenue. Without causal methods, you over-credit channels that harvest demand and under-credit channels that create it.

### Difference-in-Differences (DiD)
Compare the change in outcomes (pre vs post) between a treated group and a control group. The "difference in differences" removes time-invariant confounders.
- **Requirements**: Parallel trends assumption — treated and control groups must have similar outcome trajectories before the intervention
- **Application**: "We launched a new campaign in Region A on March 1. Compare Region A's pre/post change to Region B's pre/post change"

### Regression Discontinuity Design (RDD)
Exploit a threshold or cutoff to identify causal effects. Units just above and just below the threshold are nearly identical, creating a quasi-experiment.
- **Application**: "Users who scored 81+ on lead score got a sales call. Compare conversion rates of users scoring 79-80 vs 81-82"
- **Requirement**: The running variable (lead score) must not be manipulable near the cutoff

### Instrumental Variables (IV)
Find an external factor (instrument) that affects the treatment (marketing spend) but does not directly affect the outcome (sales) except through the treatment.
- **Example**: Weather as an instrument for in-store foot traffic campaigns — bad weather reduces campaign exposure but does not directly affect online purchase intent
- **Hard to find**: Valid instruments are rare in marketing; use with caution

### Propensity Score Matching (PSM)
When you cannot randomize, estimate the probability of treatment assignment (propensity score) based on observable characteristics. Match treated and untreated units with similar propensity scores.
- **Application**: Compare customers who received a promotional email vs those who did not, matching on purchase history, engagement, and demographics
- **Limitation**: Only controls for observed confounders — unobserved differences remain

---

## 4. Saturation Curves and Budget Optimization

### What Saturation Means in Practice
At some spend level, each additional dollar produces less incremental return. The first $1K on TikTok Ads might generate $5K in revenue. The 100th $1K might generate only $200. Knowing where you sit on the curve is critical for budget allocation.

### Hill Function (Standard Model)
`response = max_response * (spend^slope) / (K^slope + spend^slope)`
- **max_response**: Theoretical maximum revenue if spend were infinite
- **K (half-saturation)**: Spend level at which response reaches 50% of max. Lower K = faster saturation
- **slope**: Steepness of the curve. slope > 1 = S-curve (slow start, fast middle, slow end). slope < 1 = concave (fast start, diminishing returns immediately)

### Practical Optimization
1. Estimate the saturation curve per channel from MMM or historical data
2. Calculate marginal ROI at current spend level: derivative of the response function
3. Rank channels by marginal ROI
4. Shift budget from lowest marginal ROI channels to highest until marginal ROIs equalize across channels (or hit minimum spend constraints)
5. Set an ROI floor — do not spend beyond the point where marginal ROI drops below 1.0x (or your target ROAS)

---

## 5. Channel Interaction Models

### Complementarity (Synergy)
Channels that amplify each other when active simultaneously. TV + paid search: TV creates awareness, search captures the demand spike. Social + email: social warms the audience, email converts. Quantify synergy by adding interaction terms to MMM: `revenue ~ TV + search + TV*search`. A positive interaction coefficient means the combined effect exceeds the sum of individual effects.

### Cannibalization
Channels that steal conversions from each other. Branded search vs organic: both capture the same intent. Retargeting vs email: both target existing customers with similar offers. Negative interaction coefficient in MMM signals cannibalization.

### Synergy Quantification
Report the percentage of revenue attributable to channel interactions versus individual channel effects. Typical range: 5-20% of total marketing-driven revenue comes from synergies. High-synergy brands (those with strong cross-channel strategies) can reach 25-30%.

---

## 6. Revenue Simulation (Monte Carlo)

### Methodology
1. Define probability distributions for each input: channel ROI (normal distribution with mean and standard deviation from MMM posteriors), budget scenarios (fixed or range), seasonal multipliers (historical), competitive factors (scenario-based)
2. Draw random samples from each distribution
3. Calculate revenue for each draw: `revenue = sum(channel_spend_i * channel_ROI_i * seasonal_multiplier * competitive_factor) + baseline`
4. Repeat 10,000+ times
5. Analyze the distribution of simulated revenues

### Output Interpretation
- **Expected revenue**: Mean of all simulations
- **Confidence range**: 10th percentile (downside), 50th (median), 90th (upside)
- **Probability of hitting target**: Percentage of simulations that exceed the revenue goal
- **Sensitivity analysis**: Which input parameters have the largest impact on revenue variance (run simulations with each parameter fixed to see which one, when fixed, reduces variance the most)

---

## 7. Churn Prediction and Intervention

### Behavioral Signals
- Login frequency decline (>30% drop over 4 weeks)
- Feature usage narrowing (using fewer product features)
- Support ticket volume increase (frustration signal)
- Payment failures or downgrades
- Session duration shortening

### Engagement Signals
- Email open rate declining over 3+ consecutive sends
- Click-through rate dropping below 50% of cohort average
- Unsubscribing from content categories
- Reduced app/site visit frequency
- No engagement with new features or announcements

### Transactional Signals
- Purchase frequency decline (>40% drop vs prior period)
- Average order value decrease
- Category narrowing (buying from fewer categories)
- Coupon/discount dependency increasing
- Cart abandonment rate rising

### Risk Score Tiers and Intervention Playbook
| Score | Tier | Intervention |
|-------|------|-------------|
| 0-30 | Low risk | Nurture sequences, value reinforcement content, product education |
| 30-60 | Medium risk | Personalized offer, success manager outreach, feature adoption campaign |
| 60-80 | High risk | Retention offer (discount/upgrade), executive outreach, win-back sequence |
| 80-100 | Critical | Urgent save offer, proactive cancellation intercept, 1:1 outreach |

---

## 8. Experimentation Rigor

### Sample Size and Runtime
Use power analysis before launching any test. Inputs: minimum detectable effect (MDE), significance level (typically 0.05), statistical power (typically 0.80), baseline conversion rate. Tools: `sample-size-calculator.py` and `significance-tester.py`. Runtime = required sample size / daily traffic. Never stop a test early based on "peeking" at results unless using sequential testing methods.

### Multiple Testing Correction
Running 5 variants? The probability of at least one false positive at alpha=0.05 rises to 23%. Apply Bonferroni correction (alpha / number of tests) for simplicity, or Holm-Bonferroni for more power. For related metrics, consider False Discovery Rate (FDR) control instead.

### Sequential Testing
Group sequential methods allow for planned interim analyses with early stopping boundaries. Spending functions (O'Brien-Fleming, Pocock) control overall Type I error while allowing early stopping for very large effects. Define stopping boundaries before the test starts — not during.

### Guardrail Metrics
Metrics that must NOT degrade while you optimize the primary metric. Examples: revenue per user (guardrail) while testing for higher signup rate (primary); page load speed (guardrail) while testing new page layout (primary); customer satisfaction (guardrail) while testing for higher upsell rate (primary). If a guardrail degrades beyond a pre-set threshold, stop the test regardless of primary metric improvement.
