---
name: eighty-twenty-customer-value-rfm
description: Segment customers and lists by 80/20 value, responsiveness, recency, frequency, and money. Use when identifying best customers, prioritizing follow-up, finding high-value buyers, pruning low-value accounts, or deciding what customer data to measure.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: 80/20 Customer Value RFM
  category: Marketing
  tags: eighty-twenty,rfm,segmentation,customers,analytics
---

# 80/20 Customer Value RFM

Use this skill to find the customers, buyers, leads, or accounts that deserve
disproportionate attention. It is based on 80/20 Sales and Marketing by Perry
Marshall.

## Source Traceability

Primary source: 80/20 Sales and Marketing, chapters 12, 19, 22, and 23.

- Chapter 12 covers premium buyer behavior and hidden customer value.
- Chapter 19 covers removing problem customers and weak performers.
- Chapter 22 covers choosing the few measurements that matter.
- Chapter 23 covers recency, frequency, money, and customer-value measurement.

## Workflow

### 1. Define The Customer Set

Capture:

- Customer or lead population.
- Time window.
- Revenue, profit, or strategic value metric.
- Available behavioral data.
- Follow-up capacity.

If the data is weak, create a practical scoring plan instead of pretending the
segmentation is precise.

### 2. Score RFM And Responsiveness

Score each customer or segment:

- Recency: how recently they acted or bought.
- Frequency: how often they act or buy.
- Money: how much they spend or can spend.
- Responsiveness: how quickly and strongly they respond.
- Fit: whether they match the desired customer profile.

### 3. Segment The List

Use these groups:

- Best buyers: high recent value, repeat behavior, strong fit.
- Expansion candidates: good fit with evidence of premium potential.
- Nurture: fit is plausible but timing or proof is weaker.
- Low-value tail: low fit, low value, high effort, or high support burden.
- Problem customers: negative margin, toxic behavior, or strategic drag.

### 4. Decide Treatment By Segment

Recommend different action by segment:

- Personal outreach.
- Premium offer.
- Referral request.
- Automated nurture.
- Requalification.
- Sunset, prune, or fire.

## Output Format

```markdown
# Customer Value Segmentation

## Data Available
- Population:
- Time window:
- Fields available:
- Data gaps:

## RFM Segments
| Segment | Recency | Frequency | Money | Responsiveness | Action |
|---------|---------|-----------|-------|----------------|--------|

## 80/20 Findings
- Top customers:
- Hidden expansion group:
- Low-value tail:
- Problem customers:

## Recommended Actions
1. [Action]
2. [Action]
3. [Action]
```

## Quality Bar

- Do not treat all customers as equally valuable.
- Do not use revenue without considering effort, margin, or fit.
- Do not recommend firing customers without a clear reason.
- Separate premium potential from current spend.
- State what data would improve the segmentation.
