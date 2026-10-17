---
name: eighty-twenty-funnel-economics
description: Diagnose and prioritize sales funnel improvements by economics, conversion, split testing, and high-value customer potential. Use when optimizing funnels, deciding what to test, improving CAC or profit, evaluating upsells, or choosing the few metrics that matter now.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: 80/20 Funnel Economics
  category: Marketing
  tags: eighty-twenty,funnels,economics,experiments,marketing
---

# 80/20 Funnel Economics

Use this skill to find the few funnel improvements that multiply economic
results. It is based on 80/20 Sales and Marketing by Perry Marshall.

## Source Traceability

Primary source: 80/20 Sales and Marketing, chapters 6, 9, 12, and 22.

- Chapter 6 introduces traffic, conversion, economics as a linked system.
- Chapter 9 covers split testing and fixing funnels in pieces.
- Chapter 12 covers higher customer value and premium buying behavior.
- Chapter 22 covers identifying the few measurements that matter now.

## Workflow

### 1. Map The Funnel Economics

Capture each step:

- Traffic source.
- Lead capture.
- Qualification.
- Offer.
- Purchase.
- Upsell or expansion.
- Retention or repeat purchase.

For each step, capture volume, conversion rate, revenue, gross margin, and
customer quality where available.

### 2. Work Backwards From Economics

Before increasing traffic, answer:

- What customer value can the funnel support?
- What acquisition cost is acceptable?
- Which customers are worth much more than the median?
- Where is premium demand hidden?
- What offer or upsell could capture more value?

### 3. Find The Multiplying Constraint

Identify the smallest number of steps where improvement multiplies downstream
results.

Prefer tests that affect:

- Qualified conversion.
- Average order value or expansion.
- Gross margin.
- Sales cycle speed.
- High-value customer capture.

### 4. Design The Next Test

Choose one test at a time. Define:

- Hypothesis.
- Funnel step.
- Variant.
- Primary metric.
- Secondary guardrail.
- Run time or sample size.
- Decision rule.

## Output Format

```markdown
# Funnel Economics Diagnosis

## Funnel Map
| Step | Volume | Conversion | Revenue/Value | Constraint |
|------|--------|------------|---------------|------------|

## Economic Leverage
- Allowable CAC:
- Highest-value segment:
- Hidden premium opportunity:
- Main constraint:

## Test Priority
| Rank | Test | Step | Expected Economic Effect | Decision Rule |
|------|------|------|--------------------------|---------------|

## Recommendation
- Run next:
- Do not optimize yet:
- Data needed:
```

## Quality Bar

- Do not increase traffic before checking economics.
- Do not optimize vanity metrics.
- Do not run multiple ambiguous tests at once.
- Treat funnel improvements as multiplicative, not isolated.
- Include a decision rule before recommending a test.
