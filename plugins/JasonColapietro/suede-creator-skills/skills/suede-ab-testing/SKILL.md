---
name: suede-ab-testing
description: "Suede AI A/B Testing Skills. Use when asked to \"design an A/B test\", compare variants, assess reliability, or build an experiment backlog: hypothesis, power, duration, guardrails and a predeclared decision rule. NOT FOR: instrumentation (suede-analytics), funnel diagnosis (suede-site-alchemy), variant copy (suede-copy), or channel incrementality (suede-attribution)."
metadata:
  display-name: "Suede AI A/B Testing Skills"
  version: 2.1.0
---

# Suede AI A/B Testing Skills

Read [the worked delivery contract](references/worked-contract.md) for a concrete
input, expected artifact, failure response and validation example.

## Compatibility

Works from supplied experiment data and product context; file access for saved plans and a calculator/code runtime for power or statistical calculations. Analytics access is optional when exports are provided.

Use this experimentation playbook to design tests that produce statistically valid, actionable results.

## The Iron Law

```
Predeclare three things before a test launches: sample per variant,
minimum duration, and the decision rule: and read the result only once
all three are satisfied. A result read before then is preliminary.
Never a winner.
```

- **Sample per variant**: the Sample Size table below, or a calculator run on your actual baseline.
- **Minimum duration**: 1 full week (day-of-week variation), 2 business cycles (B2B), through paydays (e-commerce): see the "Minimum Duration Rules" section of [references/sample-size-guide.md](references/sample-size-guide.md).
- **Decision rule**: which metric, at which threshold, decides the call: written down before launch, not after.

Two carve-outs, and only these two:

- A **predeclared sequential or always-valid design** may look early under its own stopping rule (see "Sequential Testing" in the sample-size guide). Declaring it sequential after the peek does not count.
- A **guardrail-triggered stop for harm** is a stop, not a winner call. Kill the variant, report no result.

## Initial Assessment

Check for `.agents/product-marketing.md` (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md`) and read it if present, baseline conversion rate, traffic volume, and available tooling decide whether a test is even powerable, and they are usually already written down there.

Then work the intake list under Task-Specific Questions below; ask only what the context file did not already answer.

---

## Hypothesis Framework

### Structure

```
Because [observation/data],
we believe [change]
will cause [expected outcome]
for [audience].
We'll know this is true when [metrics].
```

### Example

**Weak**: "Changing the button color might increase clicks."

**Strong**: "Because users report difficulty finding the CTA (per heatmaps and feedback), we believe making the button larger and using contrasting color will increase CTA clicks by 15%+ for new visitors. We'll measure click-through rate from page view to signup start."

---

## Test Types

| Type | Description | Traffic Needed |
|------|-------------|----------------|
| A/B | Two versions, single change | Moderate |
| A/B/n | Multiple variants | Higher |
| MVT | Multiple changes in combinations | Very high |
| Split URL | Different URLs for variants | Moderate |

---

## Sample Size

### Quick Reference

| Baseline | 10% Lift | 20% Lift | 50% Lift |
|----------|----------|----------|----------|
| 1% | 170,000/variant | 43,000/variant | 7,800/variant |
| 3% | 54,000/variant | 14,000/variant | 2,600/variant |
| 5% | 32,000/variant | 8,200/variant | 1,500/variant |
| 10% | 15,000/variant | 3,900/variant | 690/variant |

Two-sided, 95% significance, 80% power, relative lift, rounded up.

**Calculators:**
- Two-proportion sample size calculator: https://www.evanmiller.org/ab-testing/sample-size.html
- Optimizely sample size calculator: https://www.optimizely.com/sample-size-calculator/

**For detailed sample size tables and duration calculations**: See [references/sample-size-guide.md](references/sample-size-guide.md)

---

## Metrics Selection

### Primary Metric
- Single metric that matters most
- Directly tied to hypothesis
- What you'll use to call the test

### Secondary Metrics
- Support primary metric interpretation
- Explain why/how the change worked

### Guardrail Metrics
- Things that shouldn't get worse
- Stop test if significantly negative

### Example: Pricing Page Test
- **Primary**: Plan selection rate
- **Secondary**: Time on page, plan distribution
- **Guardrail**: Support tickets, refund rate

---

## Designing Variants

### What to Vary

| Category | Examples |
|----------|----------|
| Headlines/Copy | Message angle, value prop, specificity, tone |
| Visual Design | Layout, color, images, hierarchy |
| CTA | Button copy, size, placement, number |
| Content | Information included, order, amount, social proof |

### Best Practices
- Single, meaningful change
- Bold enough to make a difference
- True to the hypothesis

---

## Traffic Allocation

| Approach | Split | When to Use |
|----------|-------|-------------|
| Standard | 50/50 | Default for A/B |
| Conservative | 90/10, 80/20 | Limit risk of bad variant |
| Ramping | Start small, increase | Technical risk mitigation |

**Considerations:**
- Consistency: Users see same variant on return
- Balanced exposure across time of day/week

---

## Implementation

### Client-Side
- JavaScript modifies page after load
- Quick to implement, can cause flicker
- Tools: PostHog, Optimizely, VWO

### Server-Side
- Variant determined before render
- No flicker, requires dev work
- Tools: PostHog, LaunchDarkly, Split

---

## Running the Test

### Pre-Launch Checklist

Each box names the artifact that closes it. An unchecked box means the test is
running unvalidated: any result it produces is reportable only as unverified,
and a silently broken variant invalidates the entire run's traffic.

- [ ] **Hypothesis documented**: written in the framework structure above, saved with the test record
- [ ] **Primary metric defined**: the metric name plus the predeclared decision rule
- [ ] **Sample size calculated**: n per variant and the projected end date, from the table or a calculator
- [ ] **Variants implemented correctly**: a screenshot or recording of each variant exactly as served
- [ ] **Tracking verified**: a fired-event readback showing the exposure and conversion events with correct properties (use `suede-analytics` for the instrumentation and the readback)
- [ ] **QA completed on all variants**: a pass on every browser and device class the test will serve

### During the Test

**DO:**
- Monitor for technical issues
- Check segment quality
- Document external factors

**Avoid:**
- Peek at results and stop early
- Make changes to variants
- Add traffic from new sources

### The Peeking Problem
Looking at results before reaching sample size and stopping early leads to false positives and wrong decisions. Pre-commit to sample size and trust the process.

---

## Analyzing Results

### Statistical Significance
- 95% confidence = p-value < 0.05
- Means <5% chance result is random
- Not a guarantee: just a threshold

### Analysis Checklist

1. **Reach sample size?** If not, result is preliminary
2. **Statistically significant?** Check confidence intervals
3. **Effect size meaningful?** Compare to MDE, project impact
4. **Secondary metrics consistent?** Support the primary?
5. **Guardrail concerns?** Anything get worse?
6. **Segment differences?** Mobile vs. desktop? New vs. returning?

### Interpreting Results

| Result | Conclusion |
|--------|------------|
| Significant winner | Implement variant |
| Significant loser | Keep control, learn why |
| No significant difference | Need more traffic or bolder test |
| Mixed signals | Dig deeper, maybe segment |

---

## Documentation

Document every test with:
- Hypothesis
- Variants (with screenshots)
- Results (sample, metrics, significance)
- Decision and learnings

**For templates**: See [references/test-templates.md](references/test-templates.md)

---

## Growth Experimentation Program

Individual tests are valuable. A continuous experimentation program is a compounding asset. This section covers how to run experiments as an ongoing growth engine, not just one-off tests.

### The Experiment Loop

```
1. Generate hypotheses (from data, research, competitors, customer feedback)
2. Prioritize with ICE scoring
3. Design and run the test
4. Analyze results with statistical rigor
5. Promote winners to a playbook
6. Generate new hypotheses from learnings
→ Repeat
```

### Hypothesis Generation

Feed your experiment backlog from multiple sources:

| Source | What to Look For |
|--------|-----------------|
| Analytics | Drop-off points, low-converting pages, underperforming segments |
| Customer research | Pain points, confusion, unmet expectations: use `suede-customer-research` to produce these |
| Competitor analysis | Features, messaging, or UX patterns they use that you don't: use `suede-competitor-profiling` to produce these |
| Support tickets | Recurring questions or complaints about conversion flows |
| Heatmaps/recordings | Where users hesitate, rage-click, or abandon |
| Past experiments | "Significant loser" tests often reveal new angles to try |

### ICE Prioritization

Score each hypothesis 1-10 on three dimensions:

| Dimension | Question |
|-----------|----------|
| **Impact** | If this works, how much will it move the primary metric? |
| **Confidence** | How sure are we this will work? (Based on data, not gut.) |
| **Ease** | How fast and cheap can we ship and measure this? |

**ICE Score** = (Impact + Confidence + Ease) / 3

Run highest-scoring experiments first. Re-score monthly as context changes.

### Experiment Velocity

Track your experimentation rate as a leading indicator of growth:

| Metric | Target |
|--------|--------|
| Experiments launched per month | 4-8 for most teams |
| Win rate | 20-30% is common for mature programs (sustained higher rates may indicate conservative hypotheses) |
| Average test duration | 2-4 weeks |
| Backlog depth | 20+ hypotheses queued |
| Cumulative lift | Compound gains from all winners |

### The Experiment Playbook

When a test wins, don't just implement it, document the pattern:

```
## [Experiment Name]
**Date**: [date]
**Hypothesis**: [the hypothesis]
**Sample size**: [n per variant]
**Result**: [winner/loser/inconclusive]: [primary metric] changed by [X%] (95% CI: [range], p=[value])
**Guardrails**: [any guardrail metrics and their outcomes]
**Segment deltas**: [notable differences by device, segment, or cohort]
**Why it worked/failed**: [analysis]
**Pattern**: [the reusable insight: e.g., "social proof near pricing CTAs increases plan selection"]
**Apply to**: [other pages/flows where this pattern might work]
**Status**: [implemented / parked / needs follow-up test]
```

Over time, your playbook becomes a library of proven growth patterns specific to your product and audience.

### Experiment Cadence

**Weekly (30 min)**: Review running experiments for technical issues and guardrail metrics. Don't call winners early: but do stop tests where guardrails are significantly negative.

**Bi-weekly**: Conclude completed experiments. Analyze results, update playbook, launch next experiment from backlog.

**Monthly (1 hour)**: Review experiment velocity, win rate, cumulative lift. Replenish hypothesis backlog. Re-prioritize with ICE.

**Quarterly**: Audit the playbook. Which patterns have been applied broadly? Which winning patterns haven't been scaled yet? What areas of the funnel are under-tested?

---

## Rationalizations

The failure this skill exists to prevent is calling a result early under
pressure. When one of these lines shows up, from a stakeholder or from you,
the answer is already in this file.

| Excuse | Reality |
|--------|---------|
| "It's already significant at 95%" | 95% is a threshold, not a guarantee. Significance checked before the predeclared sample is a peek, and peeking inflates false positives. Analysis Checklist item 1 still stands: preliminary. |
| "We've been running it two weeks" | Duration is one of three conditions, not the condition. Check n per variant against the sample-size table before reading anything. |
| "The trend is obvious" | Early trends reverse routinely: that is exactly what The Peeking Problem describes. An obvious trend at 30% of sample is a reason to wait, not to stop. |
| "Leadership needs an answer Friday" | Then report it as preliminary, with the sample reached and the stopped-early status disclosed (Boundaries). A stopped-early result sold as a winner is what costs credibility two quarters from now. |
| "The losing variant is clearly bad, why keep serving it" | Stopping for a significantly negative guardrail is legitimate (Experiment Cadence). But a stop for harm is a stop, not a winner call for the control. |
| "The mobile segment won" | A segment that was not predeclared is a hypothesis for the next test, not a result. Post-hoc segment selection manufactures significance out of noise. |
| "The numbers look fine, no need to re-check the build" | A variant can break silently mid-flight: a script fails, a flag flips, an event stops firing. Re-verify firing and variant rendering before reading the result, not only before launch. |
| "It didn't win, but the secondary metrics did" | Inconclusive is a result. Over-interpreting a null test is how a playbook fills with patterns that never replicate. |
| "Let's fold a few more changes into this one" | Multiple simultaneous changes cannot be isolated, and splitting traffic further pushes every arm below its required sample (see Designing Variants). |

---

## Task-Specific Questions

1. What's your current conversion rate?
2. How much traffic does this page get?
3. What change are you considering and why?
4. What's the smallest improvement worth detecting?
5. What tools do you have for testing?
6. Have you tested this area before?

---

## Boundaries

- Do not claim a winner before the predeclared sample, duration, and decision rule are satisfied.
- Do not alter production traffic allocation, experiment settings, or analytics without explicit authorization and a rollback path.
- Do not publish results without reporting uncertainty, guardrail movement, exclusions, and stopped-early status.
- Do not decide that statistical significance equals business value; compare the effect with the minimum useful lift.

## Routing

- Need event or conversion instrumentation -> use `suede-analytics`.
- Need page-level diagnosis or test ideas -> use `suede-site-alchemy`.
- Need variant copy -> use `suede-copy`.
- Result inconclusive and the question is whether the change moved anything at all -> use `suede-attribution` for incrementality and geo-holdout designs.
- From those skills, route hypothesis design, power checks, and experiment readouts back to `suede-ab-testing`.
