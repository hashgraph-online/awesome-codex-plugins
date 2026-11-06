# Sample Size Guide

Reference for calculating sample sizes and test duration.

## Contents
- Sample Size Fundamentals (required inputs, what these mean)
- Sample Size Quick Reference Tables
- Duration Calculator (formula, examples, minimum duration rules, maximum duration guidelines)
- Online Calculators
- Adjusting for Multiple Variants
- Common Sample Size Mistakes
- When Sample Size Requirements Are Too High
- Sequential Testing
- Quick Decision Framework

## Sample Size Fundamentals

### Required Inputs

1. **Baseline conversion rate**: Your current rate
2. **Minimum detectable effect (MDE)**: Smallest change worth detecting
3. **Statistical significance level**: Usually 95% (α = 0.05)
4. **Statistical power**: Usually 80% (β = 0.20)

### What These Mean

**Baseline conversion rate**: If your page converts at 5%, that's your baseline.

**MDE (Minimum Detectable Effect)**: The smallest improvement you care about detecting. Set this based on:
- Business impact (is a 5% lift meaningful?)
- Implementation cost (worth the effort?)
- Realistic expectations (what have past tests shown?)

**Statistical significance (95%)**: Means there's less than 5% chance the observed difference is due to random chance.

**Statistical power (80%)**: Means if there's a real effect of size MDE, you have 80% chance of detecting it.

---

## Sample Size Quick Reference Tables

Two-sided test, 95% significance (alpha 0.05), 80% power, equal split, relative
lift. Values are rounded up. Recompute with a calculator for any other setting.

### Conversion Rate: 1%

| Lift to Detect | Sample per Variant | Total Sample |
|----------------|-------------------|--------------|
| 5% (1% → 1.05%) | 640,000 | 1,280,000 |
| 10% (1% → 1.1%) | 170,000 | 340,000 |
| 20% (1% → 1.2%) | 43,000 | 86,000 |
| 50% (1% → 1.5%) | 7,800 | 15,600 |
| 100% (1% → 2%) | 2,400 | 4,800 |

### Conversion Rate: 3%

| Lift to Detect | Sample per Variant | Total Sample |
|----------------|-------------------|--------------|
| 5% (3% → 3.15%) | 210,000 | 420,000 |
| 10% (3% → 3.3%) | 54,000 | 108,000 |
| 20% (3% → 3.6%) | 14,000 | 28,000 |
| 50% (3% → 4.5%) | 2,600 | 5,200 |
| 100% (3% → 6%) | 750 | 1,500 |

### Conversion Rate: 5%

| Lift to Detect | Sample per Variant | Total Sample |
|----------------|-------------------|--------------|
| 5% (5% → 5.25%) | 130,000 | 260,000 |
| 10% (5% → 5.5%) | 32,000 | 64,000 |
| 20% (5% → 6%) | 8,200 | 16,400 |
| 50% (5% → 7.5%) | 1,500 | 3,000 |
| 100% (5% → 10%) | 440 | 880 |

### Conversion Rate: 10%

| Lift to Detect | Sample per Variant | Total Sample |
|----------------|-------------------|--------------|
| 5% (10% → 10.5%) | 58,000 | 116,000 |
| 10% (10% → 11%) | 15,000 | 30,000 |
| 20% (10% → 12%) | 3,900 | 7,800 |
| 50% (10% → 15%) | 690 | 1,380 |
| 100% (10% → 20%) | 200 | 400 |

### Conversion Rate: 20%

| Lift to Detect | Sample per Variant | Total Sample |
|----------------|-------------------|--------------|
| 5% (20% → 21%) | 26,000 | 52,000 |
| 10% (20% → 22%) | 6,600 | 13,200 |
| 20% (20% → 24%) | 1,700 | 3,400 |
| 50% (20% → 30%) | 300 | 600 |
| 100% (20% → 40%) | 90 | 180 |

---

## Duration Calculator

### Formula

```
Duration (days) = (Sample per variant × Number of variants) / (Daily traffic × % exposed)
```

### Examples

**Scenario 1: High-traffic page**
- Need: 10,000 per variant (2 variants = 20,000 total)
- Daily traffic: 5,000 visitors
- 100% exposed to test
- Duration: 20,000 / 5,000 = **4 days**

**Scenario 2: Medium-traffic page**
- Need: 30,000 per variant (60,000 total)
- Daily traffic: 2,000 visitors
- 100% exposed
- Duration: 60,000 / 2,000 = **30 days**

**Scenario 3: Low-traffic with partial exposure**
- Need: 15,000 per variant (30,000 total)
- Daily traffic: 500 visitors
- 50% exposed to test
- Effective daily: 250
- Duration: 30,000 / 250 = **120 days** (too long!)

### Minimum Duration Rules

Even with sufficient sample size, run tests for at least:
- **1 full week**: To capture day-of-week variation
- **2 business cycles**: If B2B (weekday vs. weekend patterns)
- **Through paydays**: If e-commerce (beginning/end of month)

### Maximum Duration Guidelines

Avoid running tests longer than 4-8 weeks:
- Novelty effects wear off
- External factors intervene
- Opportunity cost of other tests

---

## Online Calculators

### Recommended Tools

**Two-proportion calculator (evanmiller.org)**
https://www.evanmiller.org/ab-testing/sample-size.html
- Simple interface
- Bookmark-worthy

**Optimizely sample size calculator**
https://www.optimizely.com/sample-size-calculator/
- Business-friendly language
- Duration estimates

**AB Test Guide Calculator**
https://www.abtestguide.com/calc/
- Includes Bayesian option
- Multiple test types

**VWO Duration Calculator**
https://vwo.com/tools/ab-test-duration-calculator/
- Duration-focused
- Good for planning

---

## Adjusting for Multiple Variants

With more than 2 variants (A/B/n tests), you need more sample:

| Variants | Multiplier |
|----------|------------|
| 2 (A/B) | 1x |
| 3 (A/B/C) | ~1.5x |
| 4 (A/B/C/D) | ~2x |
| 5+ | Consider reducing variants |

**Why?** More comparisons increase chance of false positives. You're comparing:
- A vs B
- A vs C
- B vs C (sometimes)

Apply Bonferroni correction or use tools that handle this automatically.

---

## Common Sample Size Mistakes

### 1. Underpowered tests
**Problem**: Not enough sample to detect realistic effects
**Fix**: Be realistic about MDE, get more traffic, or don't test

### 2. Overpowered tests
**Problem**: Waiting for sample size when you already have significance
**Fix**: This is actually fine: you committed to sample size, honor it

### 3. Wrong baseline rate
**Problem**: Using wrong conversion rate for calculation
**Fix**: Use the specific metric and page, not site-wide averages

### 4. Ignoring segments
**Problem**: Calculating for full traffic, then analyzing segments
**Fix**: If you plan segment analysis, calculate sample for smallest segment

### 5. Testing too many things
**Problem**: Dividing traffic too many ways
**Fix**: Prioritize ruthlessly, run fewer concurrent tests

---

## When Sample Size Requirements Are Too High

Options when you can't get enough traffic:

1. **Increase MDE**: Accept only detecting larger effects (20%+ lift)
2. **Lower confidence**: Use 90% instead of 95% (risky, document it)
3. **Reduce variants**: Test only the most promising variant
4. **Combine traffic**: Test across multiple similar pages
5. **Test upstream**: Test earlier in funnel where traffic is higher
6. **Don't test**: Make decision based on qualitative data instead
7. **Longer test**: Accept longer duration (weeks/months)

---

## Sequential Testing

If you must check results before reaching sample size:

### What is it?
Statistical method that adjusts for multiple looks at data.

### When to use
- High-risk changes
- Need to stop bad variants early
- Time-sensitive decisions

### Tools that support it
- Optimizely (Stats Accelerator)
- VWO (SmartStats)
- PostHog (Bayesian approach)

### Tradeoff
- More flexibility to stop early
- Slightly larger sample size requirement
- More complex analysis

---

## Quick Decision Framework

### Can I run this test?

```
Daily traffic to page: _____
Baseline conversion rate: _____
MDE I care about: _____

Sample needed per variant: _____ (from tables above)
Days to run: Sample / Daily traffic = _____

If days > 60: Consider alternatives
If days > 30: Acceptable for high-impact tests
If days < 14: Likely feasible
If days < 7: Easy to run, consider running longer anyway
```
