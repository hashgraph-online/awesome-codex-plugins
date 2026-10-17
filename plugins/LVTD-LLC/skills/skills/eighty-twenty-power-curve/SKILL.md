---
name: eighty-twenty-power-curve
description: Apply 80/20 power-curve thinking to sales, marketing, customers, offers, traffic, time, and operations. Use when finding leverage, diagnosing uneven results, prioritizing high-upside segments, or replacing average-based reasoning with Pareto and power-law analysis.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: 80/20 Power Curve
  category: Marketing
  tags: eighty-twenty,pareto,sales,marketing,prioritization
---

# 80/20 Power Curve

Use this skill to find where a small minority of inputs creates most of the
value, cost, waste, demand, or opportunity. It is based on 80/20 Sales and
Marketing by Perry Marshall.

## Source Traceability

Primary source: 80/20 Sales and Marketing, chapters 1, 5, 14, and the appendix.

- Chapter 1 introduces compounding 80/20 behavior and warns against average
  thinking.
- Chapter 5 applies the power curve to business opportunity and resource shifts.
- Chapter 14 explains why positive feedback creates non-linear outcomes.
- The appendix gives the math-oriented version of the power curve.

## Workflow

### 1. Name The Population

Define the set being ranked:

- Customers, leads, products, pages, ads, keywords, salespeople, tasks, support
  issues, markets, partners, content assets, or campaigns.
- Time window.
- Outcome metric: revenue, profit, conversions, usage, retention, attention,
  qualified pipeline, cost, complaints, or effort.

If the user provides only averages, ask for raw counts or ranked items. If raw
data is unavailable, create an explicit estimate and label it.

### 2. Rank By The Outcome That Matters

Sort items from strongest to weakest. Prefer profit or qualified action over
surface volume.

Use these questions:

- Which few items create most of the upside?
- Which few items create most of the waste?
- What is the best item worth compared with the median?
- Where does the distribution drop sharply?
- What would change if resources moved from the weak tail to the strong head?

### 3. Look For Nested 80/20

After finding the top 20 percent, look inside that group for the top 20 percent
again. Stop when the data becomes too thin to interpret.

Useful nested cuts:

- Top customers inside the top customer segment.
- Best ads inside the best campaign.
- Highest-intent keywords inside the best keyword cluster.
- Best tasks inside the highest-value role.

### 4. Decide The Resource Shift

Recommend one of four moves:

- Double down on the strongest items.
- Split-test or refine the items near the threshold.
- Stop, delegate, or automate the weak tail.
- Gather better data before acting.

Do not recommend optimization of the average item unless it unlocks a stronger
power-curve move.

## Output Format

```markdown
# 80/20 Power Curve Analysis

## Population
- Items ranked:
- Time window:
- Outcome metric:
- Data quality:

## Power-Curve Findings
| Rank/Segment | Item Or Group | Outcome | Interpretation |
|--------------|---------------|---------|----------------|

## Nested 80/20
- Strongest sub-segment:
- Weak tail:
- Biggest surprise:

## Recommended Resource Shift
- Move resources from:
- Move resources to:
- Expected effect:
- Data still needed:
```

## Quality Bar

- Do not use averages as the main conclusion.
- Do not treat all customers, leads, channels, or tasks as equal.
- Separate upside concentration from waste concentration.
- Prefer profit, qualified action, or strategic value over raw volume.
- Label assumptions when exact ranked data is missing.
