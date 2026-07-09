# Growth Experimentation — Frameworks & Methodology Reference

## Experiment Prioritization Frameworks

### ICE Score (Impact, Confidence, Ease)

| Dimension | Scale | Definition |
|-----------|-------|-----------|
| Impact | 1-10 | How much will this move the target metric? |
| Confidence | 1-10 | How confident are you in the predicted impact? (based on data, research, or precedent) |
| Ease | 1-10 | How easy is this to implement? (time, resources, dependencies) |

```
ICE Score = (Impact + Confidence + Ease) / 3

Example:
Experiment: Change CTA button color from gray to green
- Impact: 3 (minor UX change)
- Confidence: 4 (no strong data suggesting impact)
- Ease: 10 (5-minute code change)
- ICE Score: (3 + 4 + 10) / 3 = 5.7

Experiment: Redesign pricing page with social proof and FAQ
- Impact: 9 (pricing page is highest-intent page)
- Confidence: 7 (competitor analysis + user research supports it)
- Ease: 4 (requires design, copy, dev work)
- ICE Score: (9 + 7 + 4) / 3 = 6.7  ← Prioritize this one
```

**Best for:** Small teams, fast-moving startups, early-stage experimentation programs. Quick to score, easy to debate.

### RICE Score (Reach, Impact, Confidence, Effort)

| Dimension | Scale | Definition |
|-----------|-------|-----------|
| Reach | # of users/month | How many people will this affect in a given time period? |
| Impact | 0.25 / 0.5 / 1 / 2 / 3 | Minimal / Low / Medium / High / Massive impact per person |
| Confidence | 50% / 80% / 100% | How certain are you? Low / Medium / High |
| Effort | Person-months | Total work required (design + dev + QA) |

```
RICE Score = (Reach x Impact x Confidence) / Effort

Example:
Experiment: Add exit-intent popup with email capture on blog
- Reach: 50,000 visitors/month
- Impact: 1 (medium — captures some emails)
- Confidence: 80%
- Effort: 0.5 person-months
- RICE Score: (50,000 x 1 x 0.8) / 0.5 = 80,000

Experiment: Rebuild checkout flow to reduce steps from 5 to 3
- Reach: 8,000 checkout initiators/month
- Impact: 3 (massive — directly affects revenue)
- Confidence: 80%
- Effort: 3 person-months
- RICE Score: (8,000 x 3 x 0.8) / 3 = 6,400
```

**Best for:** Product teams with clear user data, growth teams needing to justify investment to stakeholders.

### PIE Score (Potential, Importance, Ease)

| Dimension | Scale | Definition |
|-----------|-------|-----------|
| Potential | 1-10 | How much room for improvement exists? (based on current performance vs benchmarks) |
| Importance | 1-10 | How valuable is the traffic/audience affected? (high-value pages score higher) |
| Ease | 1-10 | How easy is the test to implement? |

```
PIE Score = (Potential + Importance + Ease) / 3
```

**Best for:** CRO teams focused on website optimization, where you're comparing pages/funnels against each other.

### When to Use Each Framework

| Framework | Best Scenario | Weakness |
|-----------|-------------|----------|
| ICE | Quick prioritization, small teams, many ideas | Subjective, no quantified reach |
| RICE | Data-rich environments, product teams | Requires user reach data, slower to calculate |
| PIE | CRO and website optimization | Limited to conversion optimization context |

---

## Hypothesis Format

Every experiment must start with a falsifiable hypothesis. A vague "let's try this" is not an experiment.

### Standard Hypothesis Template

```
If we [specific change],
then [target metric] will [direction: increase/decrease]
by [estimated magnitude: %, absolute number, or range]
because [reasoning based on data, research, or user insight].
```

### Examples of Strong Hypotheses

| Hypothesis | Strength |
|-----------|----------|
| "If we add customer testimonials to the pricing page, then the pricing-page-to-signup conversion rate will increase by 10-15% because user research shows that 68% of prospects cite 'lack of social proof' as their top hesitation." | Specific metric, grounded in research, realistic magnitude |
| "If we reduce the signup form from 7 fields to 3 (email, name, password), then the form completion rate will increase by 25-40% because our analytics show a 60% drop-off between fields 3 and 7." | Data-backed reasoning, clear change, measurable outcome |
| "If we send cart abandonment emails within 1 hour instead of 24 hours, then the cart recovery rate will increase by 15-20% because industry data shows email engagement drops 50% after the first hour." | Industry benchmark as reasoning, testable timing change |

### Common Hypothesis Mistakes

| Mistake | Example | Fix |
|---------|---------|-----|
| No specific metric | "Making the page better will improve performance" | Define which metric and by how much |
| No reasoning | "If we change the button to green, conversions will increase" | Add the "because" — what evidence supports this? |
| Untestable | "If we rebuild the entire product, users will be happier" | Scope to a testable, isolated change |
| No magnitude | "Conversion rate will increase" | Estimate a range: "by 5-10%" |
| Multiple changes | "If we change the headline, image, CTA, and layout..." | Test one variable at a time, or use multivariate design |

---

## Experiment Types

| Type | What It Is | When to Use | Complexity |
|------|-----------|-------------|-----------|
| A/B test | Two variants (control vs challenger) on the same page/element | Testing a single change with sufficient traffic | Low |
| A/B/n test | Multiple variants (3+) against a control | Testing several ideas for the same element | Medium |
| Multivariate (MVT) | Multiple elements changed simultaneously, all combinations tested | Understanding interaction effects between elements | High |
| Split URL test | Traffic split between entirely different page URLs | Testing fundamentally different page designs | Medium |
| Feature flag | New feature exposed to a percentage of users | Product changes, gradual rollouts | Medium |
| Holdout test | Suppress a feature/campaign from a control group | Measuring incremental impact of an existing feature | Low-Medium |
| Sequential test | Run variant A for a period, then variant B | When traffic is too low for simultaneous split | Low (but less reliable) |
| Bandit (explore/exploit) | Algorithm allocates traffic toward better-performing variant dynamically | When you want to minimize opportunity cost during the test | High |

### A/B Test Decision Criteria

```
Is your change a single, isolated variable?
├── Yes → A/B test
└── No → Multiple elements changing?
    ├── Yes, and I need to know interaction effects → Multivariate test
    ├── Yes, but they're part of a complete redesign → Split URL test
    └── No, it's a product feature → Feature flag with holdout
```

---

## Statistical Foundations

### Sample Size Calculation

Before running any test, calculate the required sample size to avoid inconclusive results.

| Input | Definition | How to Estimate |
|-------|-----------|----------------|
| Baseline conversion rate | Current conversion rate of the control | Use last 30-60 days of data |
| Minimum Detectable Effect (MDE) | Smallest improvement worth detecting | Typically 5-20% relative change |
| Statistical significance | Probability of avoiding false positives | Standard: 95% (alpha = 0.05) |
| Statistical power | Probability of detecting a true effect | Standard: 80% (beta = 0.20) |

### Sample Size Reference Table (95% significance, 80% power)

| Baseline CVR | 5% Relative MDE | 10% Relative MDE | 20% Relative MDE |
|-------------|-----------------|------------------|-------------------|
| 1% | 3,070,000 per variant | 770,000 per variant | 193,000 per variant |
| 2% | 1,500,000 | 376,000 | 94,500 |
| 5% | 580,000 | 146,000 | 36,700 |
| 10% | 275,000 | 69,400 | 17,500 |
| 20% | 125,000 | 31,500 | 8,000 |
| 50% | 38,000 | 9,600 | 2,500 |

> **Rule of thumb:** If your baseline CVR is low or your desired MDE is small, you need very large sample sizes. If you can't reach the required sample size within 4-6 weeks, either increase your MDE threshold or find a higher-traffic test location.

### Duration Estimation

```
Test Duration (days) = Required Sample Size per Variant x 2 / Daily Traffic to Page

Example:
- Baseline CVR: 5%
- MDE: 10% relative (5% → 5.5%)
- Required: 146,000 per variant = 292,000 total
- Daily traffic: 8,000 visitors/day
- Duration: 292,000 / 8,000 = 36.5 days → run for 5 weeks (include full weekday cycles)
```

### Avoiding Statistical Pitfalls

| Pitfall | What Happens | How to Avoid |
|---------|-------------|-------------|
| Peeking at results | Checking daily and stopping early when results look good inflates false positive rate to 20-30% | Pre-commit to sample size and duration; only evaluate at the end |
| Underpowered tests | Test ends with "no significant result" but sample was too small to detect real effect | Calculate sample size before starting; do not run tests you cannot power |
| Multiple comparisons | Testing 10 variants without adjustment means ~40% chance of false positive | Apply Bonferroni correction or use sequential testing methods |
| Novelty effect | New variant performs well initially because it is unfamiliar, then regresses | Run tests for at least 2 full weeks; monitor for regression in week 2-3 |
| Selection bias | Non-random traffic split (e.g., different time periods or geographies) | Use proper randomization; verify that control/treatment demographics match |
| Simpson's Paradox | Overall result is flat, but segments show opposite effects that cancel out | Always segment results by device, traffic source, new vs returning |

---

## Growth Experiment Categories (AARRR Framework)

### Acquisition Experiments

| Experiment | Metric | Example |
|-----------|--------|---------|
| Channel testing | CAC by new channel | Test Reddit ads for B2B audience vs LinkedIn |
| Landing page variants | Landing page CVR | Test long-form vs short-form landing page |
| Ad creative testing | CTR, CPA | Test benefit-focused vs pain-focused ad copy |
| Referral mechanics | Referral conversion rate | Test "Give $20, Get $20" vs "Give 1 month free, Get 1 month free" |
| SEO content format | Organic traffic, time on page | Test comprehensive guide vs comparison post for same keyword |
| Partnership channels | Qualified leads from partners | Test co-webinar vs guest blog vs integration marketplace listing |
| Outbound messaging | Reply rate | Test personalized video vs text-only cold email |

### Activation Experiments

| Experiment | Metric | Example |
|-----------|--------|---------|
| Onboarding flow | Activation rate (Day 7) | Test guided setup wizard vs self-serve with tooltips |
| First-value acceleration | Time-to-value | Test pre-populated templates vs empty state |
| Signup friction | Signup completion rate | Test social login vs email-only signup |
| Welcome email sequence | Day 7 engagement | Test 5-email sequence vs 3-email sequence |
| Personalized onboarding | Feature adoption rate | Test role-based onboarding paths vs generic |
| Empty state design | First-action completion | Test sample data vs "create your first [item]" prompt |

### Retention Experiments

| Experiment | Metric | Example |
|-----------|--------|---------|
| Engagement triggers | Weekly active user rate | Test push notification with insight vs generic reminder |
| Re-engagement campaigns | Reactivation rate | Test incentive email vs product update email for dormant users |
| Feature stickiness | Feature retention at Day 30 | Test in-app tip sequence vs video tutorial |
| Communication cadence | 30-day retention | Test weekly digest vs real-time notifications |
| Habit loop design | Session frequency | Test streak mechanics vs progress bar |
| Community features | 90-day retention | Test forum access vs peer group matching |

### Revenue Experiments

| Experiment | Metric | Example |
|-----------|--------|---------|
| Pricing page design | Pricing-page-to-purchase CVR | Test 3-tier vs 2-tier pricing layout |
| Upgrade triggers | Free-to-paid conversion | Test in-app usage limit popup vs email upgrade prompt |
| Upsell timing | Expansion revenue per account | Test upgrade prompt at feature limit vs after 30 days |
| Annual vs monthly framing | Annual plan selection rate | Test "Save 20%" vs "2 months free" messaging |
| Cross-sell placement | Add-on attach rate | Test post-purchase page vs in-cart recommendation |
| Price anchoring | AOV | Test showing enterprise tier first vs starter tier first |

### Referral Experiments

| Experiment | Metric | Example |
|-----------|--------|---------|
| Incentive structure | Referral send rate | Test double-sided vs single-sided reward |
| Referral placement | Referrals per user | Test post-purchase prompt vs account settings page |
| Social sharing | Share rate | Test pre-written social post vs custom message |
| Referral messaging | Referral conversion rate | Test "Share and save" vs "Give your friend a gift" |
| Timing of referral ask | Referrals per activated user | Test ask at activation vs ask after first value milestone |

---

## Experiment Tracking

### Experiment Log Template

| Field | Description | Example |
|-------|-----------|---------|
| Experiment ID | Unique identifier | EXP-2025-042 |
| Name | Descriptive experiment name | "Pricing page social proof test" |
| Owner | Person responsible | Sarah Chen |
| Hypothesis | Full hypothesis statement | "If we add 3 customer logos and review scores to the pricing page..." |
| Primary metric | The one metric this experiment targets | Pricing page → signup conversion rate |
| Secondary metrics | Additional metrics to monitor for side effects | Time on pricing page, support ticket volume |
| Guardrail metrics | Metrics that must NOT degrade | Overall site conversion rate, revenue per visitor |
| Variant description | What the challenger variant changes | Add logo bar + 3 review scores above pricing table |
| Traffic allocation | % of traffic to each variant | 50/50 control/variant |
| Required sample size | Pre-calculated sample per variant | 35,000 per variant |
| Start date | When the experiment goes live | 2025-03-01 |
| Planned end date | When sample size will be reached | 2025-03-28 |
| Actual end date | When the experiment was actually stopped | 2025-03-30 |
| Result | Won / Lost / Inconclusive | Won |
| Lift | Measured change in primary metric | +12.4% (95% CI: +6.1% to +18.7%) |
| Statistical significance | P-value or confidence level | p = 0.003 (99.7% confidence) |
| Decision | Ship / Iterate / Kill | Ship to 100% |
| Key learning | What was learned regardless of outcome | Social proof near pricing decisions significantly reduces hesitation |

### Experiment Status Board

| Status | Definition | Color |
|--------|-----------|-------|
| Backlog | Hypothesis written, not yet prioritized | Gray |
| Prioritized | Scored and scheduled for upcoming sprint | Blue |
| In Development | Being built/designed/configured | Yellow |
| Running | Live and collecting data | Green |
| Analysis | Data collection complete, being analyzed | Orange |
| Decided | Decision made (ship/kill/iterate) | Purple |
| Shipped | Winning variant rolled out to 100% | Dark Green |

---

## Experimentation Velocity

### Benchmark Velocity Targets

| Team Size | Target Experiments/Month | Notes |
|-----------|------------------------|-------|
| Solo growth marketer | 2-4 | Focus on high-impact, easy-to-implement tests |
| Growth team (2-3) | 4-8 | Mix of quick wins and deeper experiments |
| Growth team (4-6) | 8-15 | Run parallel experiments across funnel stages |
| Dedicated experimentation team | 15-30 | Full experimentation infrastructure and culture |

### How to Increase Velocity

| Lever | Implementation |
|-------|---------------|
| Reduce experiment scope | Test one variable, not redesigns; smaller scope = faster cycles |
| Pre-built test templates | Standardize experiment setup in your testing tool |
| Hypothesis backlog | Maintain a scored backlog so tests are ready when a slot opens |
| Parallel testing | Run experiments on different pages/funnels simultaneously (no overlap) |
| Automated analysis | Set up auto-reporting when experiments reach significance |
| Learning documentation | Avoid re-running failed experiments by documenting learnings |
| Reduce approval bottlenecks | Empower growth team to launch tests without executive approval |

---

## Learning from Failures

### Why Experiments Fail (and What to Learn)

| Failure Type | What Happened | What to Learn |
|-------------|-------------|--------------|
| Inconclusive (no winner) | Neither variant significantly outperformed | Your change was too small to matter, MDE was too tight, or the sample was too small |
| Negative result (variant lost) | Challenger performed worse than control | The hypothesis was wrong — but now you know. Document why and test a different approach |
| Execution failure | Test was misconfigured, traffic not split properly | Improve QA process for experiment setup |
| External contamination | Seasonal effect, site outage, or marketing campaign skewed results | Run tests for full weekly cycles; exclude known anomaly periods |
| Metric moved but business didn't | Primary metric improved but revenue/retention didn't follow | You optimized for the wrong metric — revisit metric selection |

### Post-Experiment Analysis Template

```
Experiment: [Name]
Result: [Won / Lost / Inconclusive]

1. What did we expect to happen?
   [Restate hypothesis]

2. What actually happened?
   [Primary metric result + confidence level + secondary metric results]

3. Why did it happen?
   [Analysis of user behavior, segment breakdowns, qualitative insights]

4. What did we learn?
   [Insight that applies beyond this single experiment]

5. What's the next experiment?
   [Follow-up test based on this learning, or new direction]

6. Should we update any existing assumptions or strategies?
   [Broader implications for growth model, personas, or messaging]
```

---

## Growth Model: Inputs to Compound Growth

### The Growth Equation

```
Growth = Acquisition x Activation x Retention x Revenue x Referral

Each factor is a multiplier. A 10% improvement in each:
1.1 x 1.1 x 1.1 x 1.1 x 1.1 = 1.61x total growth (61% improvement)

This is why experimentation compounds.
```

### Growth Model Template

| Stage | Input Metric | Current | Target | Lever | Experiment Ideas |
|-------|-------------|---------|--------|-------|-----------------|
| Acquisition | Monthly new signups | 2,000 | 2,500 | New channels, referrals | Reddit ads test, referral program launch |
| Activation | 7-day activation rate | 35% | 45% | Onboarding, first-value | Guided wizard, pre-built templates |
| Retention | 30-day retention | 60% | 70% | Engagement, habit loops | Weekly insight email, streak feature |
| Revenue | Free-to-paid conversion | 5% | 7% | Pricing, upgrade prompts | Pricing page redesign, in-app limits |
| Referral | Referrals per activated user | 0.3 | 0.5 | Incentives, sharing mechanics | Double-sided rewards, social sharing |

---

## Common Growth Experiments by Business Model

### SaaS

| Stage | High-Impact Experiment |
|-------|----------------------|
| Acquisition | Free tool or calculator that captures emails and demonstrates product value |
| Activation | Role-based onboarding flow that shows relevant features first |
| Retention | Weekly email with personalized usage insights and "try this feature" prompts |
| Revenue | In-app modal at usage limit showing upgrade value with social proof |
| Referral | "Invite your team" prompt after activation milestone with free seat for referrer |

### eCommerce

| Stage | High-Impact Experiment |
|-------|----------------------|
| Acquisition | Quiz/recommendation engine as top-of-funnel content play |
| Activation | First-purchase discount tied to email signup (10% off first order) |
| Retention | Post-purchase replenishment email timed to product consumption cycle |
| Revenue | Dynamic bundle recommendations on product pages ("Complete the look") |
| Referral | Post-purchase "give $15, get $15" referral card in shipping box |

### Marketplace

| Stage | High-Impact Experiment |
|-------|----------------------|
| Acquisition (supply) | Automated seller onboarding that imports listings from competitor platform |
| Acquisition (demand) | SEO-optimized category pages targeting "[product] near me" queries |
| Activation | First transaction incentive for both buyer and seller (subsidized) |
| Retention | Personalized weekly digest of new listings matching buyer's search history |
| Revenue | Tiered seller plans with premium placement and analytics |
| Referral | Seller referral program with reduced commission for referred sellers |

---

*Growth is not about one brilliant idea. It is about the velocity of learning. Every experiment, whether it wins or loses, makes the system smarter. The teams that grow fastest are not the ones with the best ideas. They are the ones that test the most ideas, learn the fastest, and compound those learnings over time.*
