# A/B Testing — Methodology & Pitfalls

A rigorous framework for designing, executing, and interpreting conversion experiments. This guide covers the full lifecycle from hypothesis formation through analysis, with emphasis on the statistical and operational pitfalls that invalidate most tests.

---

## Test Design Framework

Every valid A/B test follows this sequence. Skipping any step introduces bias or renders results uninterpretable.

### Step 1: Hypothesis

**Format:** "If we [change], then [metric] will [improve/decrease] by [estimated amount], because [rationale]."

| Component | Purpose | Example |
|---|---|---|
| Change | What you are modifying | Replace generic hero image with product screenshot showing dashboard |
| Metric | Primary KPI you will measure | Free trial signup rate |
| Direction & magnitude | Expected effect and estimated size | Increase by 10–15% |
| Rationale | Why you believe this will work | Heatmap data shows visitors ignore the current stock image; customer interviews reveal the dashboard is the primary buying trigger |

**Hypothesis quality checklist:**
- [ ] Based on data (analytics, heatmaps, user research, support tickets), not opinion
- [ ] Specifies a single, measurable primary metric
- [ ] Includes a falsifiable prediction — you can prove it wrong
- [ ] Tied to a documented user problem or friction point
- [ ] Estimated impact is realistic given historical test results

### Step 2: Variable Selection

| Variable Type | Description | Example |
|---|---|---|
| Single variable | One element changed | Button color, headline text, image |
| Compound variable | Multiple related elements changed together | Full hero section redesign (headline + image + CTA) |
| Page-level | Entirely different page design | Current page vs. long-form vs. video-led variant |

**Rule of thumb:** Test single variables when diagnosing. Test compound variables when you have a strong hypothesis about a section. Test page-level when you have enough traffic and need step-change improvement.

### Step 3: Primary Metric

Choose exactly one primary metric. Track secondary metrics for context but do not use them to declare a winner.

| Metric Type | When to Use | Watch Out For |
|---|---|---|
| Conversion rate | Most A/B tests on landing pages | Can be gamed by attracting lower-quality leads |
| Revenue per visitor | E-commerce, pricing tests | Requires longer test duration due to variance |
| Activation rate | Free trial and onboarding tests | Requires tracking beyond the initial conversion |
| Lead quality score | Lead gen where volume alone is misleading | Needs CRM integration and sufficient time for leads to mature |

### Step 4: Duration & Calendar

| Factor | Guideline |
|---|---|
| Minimum duration | 2 full business cycles (typically 2 weeks minimum) |
| Maximum duration | 8 weeks — beyond this, external factors contaminate results |
| Calendar awareness | Must capture all days of the week; avoid launching mid-week |
| Exclusion periods | Black Friday, product launches, PR events, major outages |
| Holiday overlap | If a test runs through a holiday, extend it to include equivalent non-holiday period |

### Step 5: Sample Size Calculation

Determine required sample size **before** launching the test. Never start a test without knowing when to stop.

**Inputs required:**
- Baseline conversion rate (current control performance)
- Minimum Detectable Effect (MDE) — the smallest improvement worth detecting
- Statistical significance level (typically 95%, or alpha = 0.05)
- Statistical power (typically 80%, or beta = 0.20)

---

## Sample Size Reference Table

*Two-tailed test, 95% significance, 80% power. Figures show visitors needed PER VARIATION.*

| Baseline CVR | MDE: 5% relative | MDE: 10% relative | MDE: 15% relative | MDE: 20% relative | MDE: 25% relative |
|---|---|---|---|---|---|
| 1% | 3,067,000 | 779,000 | 350,000 | 199,000 | 128,000 |
| 2% | 1,504,000 | 383,000 | 172,000 | 98,000 | 63,000 |
| 3% | 984,000 | 252,000 | 113,000 | 64,000 | 42,000 |
| 5% | 570,000 | 147,000 | 66,000 | 38,000 | 25,000 |
| 8% | 338,000 | 87,000 | 40,000 | 23,000 | 15,000 |
| 10% | 263,000 | 68,000 | 31,000 | 18,000 | 12,000 |
| 15% | 165,000 | 43,000 | 20,000 | 12,000 | 8,000 |
| 20% | 116,000 | 30,000 | 14,000 | 8,200 | 5,400 |
| 30% | 68,000 | 18,000 | 8,400 | 4,900 | 3,200 |

*Key insight: Low-conversion pages need massive traffic to detect small effects. If your page converts at 2% and you want to detect a 10% relative lift (2.0% to 2.2%), you need ~383,000 visitors per variation.*

---

## Statistical Significance — What It Actually Means

### P-Value

The p-value is the probability of observing results as extreme as (or more extreme than) what you measured, assuming the null hypothesis is true (i.e., assuming there is no real difference between variations).

- **p < 0.05** means there is less than a 5% chance the observed difference is due to random noise
- It does NOT mean there is a 95% chance the variant is better
- It does NOT tell you the magnitude of the effect — only that an effect likely exists

### Confidence Intervals

A 95% confidence interval gives the range within which the true conversion rate difference likely falls.

| Scenario | Confidence Interval | Interpretation |
|---|---|---|
| Clear winner | +1.2% to +3.8% | Variant is better; effect is between 1.2% and 3.8% absolute lift |
| Inconclusive | -0.5% to +2.1% | Interval includes zero; cannot confidently declare a winner |
| Clear loser | -3.0% to -0.8% | Variant is worse; the control should be kept |

**Always report confidence intervals, not just p-values.** A statistically significant result with a tiny confidence interval around a negligible effect is not worth implementing.

### Minimum Detectable Effect (MDE)

The MDE is the smallest effect size your test is powered to detect. Setting this requires a business judgment:

- What is the smallest improvement that would justify the implementation cost?
- What lift would meaningfully change downstream revenue?

**Common mistake:** Setting MDE too low (trying to detect tiny effects) leads to impractically large sample sizes. Setting it too high (only detecting huge effects) means you miss real but moderate improvements.

---

## Common Pitfalls

### 1. Peeking (Repeated Significance Testing)

**What happens:** You check results daily and stop the test the moment you see p < 0.05.

**Why it's wrong:** Statistical significance fluctuates. If you check a test 10 times during its run, the false positive rate inflates from 5% to approximately 26%. You will declare winners that are not actually better.

**Fix:** Pre-commit to a sample size and run duration. Do not stop early. If you must monitor, use sequential testing methods (e.g., always-valid p-values, Bayesian approaches) that account for multiple looks.

### 2. Seasonal & Cyclical Bias

**What happens:** You run a test that starts on a Monday and ends on a Thursday, or runs through a promotional period.

**Why it's wrong:** Conversion rates vary by day of week, time of month, pay cycles, and seasonal patterns. Partial-cycle data skews results.

**Fix:** Always run tests for complete business cycles (full weeks minimum). Document any external events that occur during the test period.

### 3. Novelty Effect

**What happens:** A new design element performs well initially, but the lift fades as returning visitors become accustomed to it.

**Why it's wrong:** You implement the change expecting permanent lift, but it reverts to baseline within weeks.

**Fix:** Segment results by new vs. returning visitors. Run the test long enough (3–4 weeks) for the novelty to fade. Monitor post-implementation performance for 4–6 weeks.

### 4. Simpson's Paradox

**What happens:** Variant B wins overall, but when you segment by device type or traffic source, Variant A wins in every segment.

**Why it's wrong:** Uneven traffic allocation across segments creates misleading aggregate results. The "winner" is an artifact of traffic mix, not page performance.

**Fix:** Check results across major segments (device, source, new/returning). If the direction of effect reverses in segments, investigate the traffic split before declaring a winner.

### 5. Underpowered Tests

**What happens:** You run a test with insufficient traffic and declare "no significant difference" as proof that the variant has no effect.

**Why it's wrong:** Absence of evidence is not evidence of absence. A test with 500 visitors per variation cannot detect a 10% relative lift on a 3% conversion rate — it simply did not have enough data.

**Fix:** Calculate required sample size before launching. If you cannot reach it within 8 weeks, increase the MDE, test a higher-traffic page, or combine the test with other traffic sources.

### 6. Multiple Comparison Problem

**What happens:** You test 5 variations against a control and celebrate when one of them shows p < 0.05.

**Why it's wrong:** With 5 comparisons, the probability of at least one false positive is ~23% (not 5%). You are likely celebrating noise.

**Fix:** Apply a correction (Bonferroni: divide alpha by number of comparisons) or use a structured multivariate testing approach. Better yet, test fewer variations with stronger hypotheses.

### 7. Survivor Bias in Funnel Tests

**What happens:** You test a change on step 2 of a funnel and see higher conversion to step 3. But total funnel completion drops because the change also caused more drop-off between steps 1 and 2.

**Why it's wrong:** Optimizing one step in isolation can harm the overall funnel.

**Fix:** Track macro-conversion (final funnel outcome), not just micro-conversion at the tested step.

---

## ICE Prioritization Framework

Score each test idea on three dimensions (1–10 scale) and multiply to get a composite score.

| Dimension | Question | Scoring Guide |
|---|---|---|
| **Impact** | How large will the effect be if the hypothesis is correct? | 1–3: Minor lift. 4–6: Moderate improvement. 7–10: Transformative change. |
| **Confidence** | How certain are you this will produce a positive result? | 1–3: Gut feel only. 4–6: Supported by indirect data. 7–10: Strong evidence from research, past tests, or competitor analysis. |
| **Ease** | How simple is it to implement and launch? | 1–3: Major dev work, multiple teams. 4–6: Moderate effort, one sprint. 7–10: Copy/image change, launchable in hours. |

| Test Idea | Impact | Confidence | Ease | ICE Score | Priority |
|---|---|---|---|---|---|
| Rewrite headline to match top-performing ad copy | 7 | 8 | 9 | 504 | P1 |
| Reduce form from 8 fields to 4 | 8 | 7 | 7 | 392 | P1 |
| Add video testimonial above fold | 6 | 5 | 4 | 120 | P2 |
| Redesign full page layout | 9 | 4 | 2 | 72 | P3 |

---

## Multivariate Testing (MVT) Guidelines

| Criterion | A/B Test | Multivariate Test |
|---|---|---|
| Traffic required | Moderate | High (multiplied by number of combinations) |
| Best for | Validating a single hypothesis | Understanding interaction effects between elements |
| Complexity | Low | High — requires careful factorial design |
| Analysis | Simple comparison | Main effects + interaction effects |
| When to use | Default choice for most teams | When you have >100K monthly visitors AND need to test element interactions |

**MVT sample size rule:** Multiply the A/B sample size requirement by the number of combinations. A 2x2 MVT (two elements, two levels each = 4 combinations) needs roughly 4x the traffic of a simple A/B test.

---

## Test Documentation Template

Complete this for every test. Store in a shared test repository so the team builds institutional knowledge.

```
TEST ID: [Sequential number]
TEST NAME: [Descriptive name]
DATE: [Start] — [End]
PAGE: [URL tested]
TRAFFIC: [Source/segment targeted]

HYPOTHESIS:
If we [change], then [metric] will [direction] by [amount],
because [evidence-based rationale].

VARIATIONS:
- Control: [Description + screenshot link]
- Variant A: [Description + screenshot link]
- Variant B: [Description + screenshot link, if applicable]

PRIMARY METRIC: [Single metric]
SECONDARY METRICS: [List]
GUARDRAIL METRICS: [Metrics that must not degrade]

SAMPLE SIZE REQUIRED: [Per variation]
MDE: [Minimum detectable effect]
SIGNIFICANCE LEVEL: [Usually 95%]
POWER: [Usually 80%]

RESULTS:
- Control CVR: [X%]
- Variant A CVR: [X%] (p = [X], CI: [X% to X%])
- Winner: [Control / Variant / Inconclusive]

SEGMENTS CHECKED:
- Device: [Desktop / Mobile / Tablet]
- Traffic Source: [Paid / Organic / Direct / Email]
- New vs Returning: [Results by segment]

DECISION: [Implement / Iterate / Archive]
IMPLEMENTATION DATE: [When the winner was deployed]

LEARNINGS:
[What did this test teach us? What should we test next?]
```

---

## Test Velocity Benchmarks

| Company Stage | Tests per Month | Focus |
|---|---|---|
| Early-stage (low traffic) | 1–2 | High-impact, page-level tests with large MDE |
| Growth-stage | 4–8 | Section-level tests across key pages |
| Mature / High-traffic | 10–20+ | Element-level tests with rigorous methodology |

**The compounding effect:** A team running 8 tests/month with a 30% win rate and an average 5% lift per winning test achieves ~14% cumulative conversion improvement per quarter. Over a year, that compounds to 60%+ total lift — far exceeding what any single redesign delivers.
