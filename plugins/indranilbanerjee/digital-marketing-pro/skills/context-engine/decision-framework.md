# Multi-Dimensional Decision Framework

Every meaningful marketing decision involves multiple dimensions. Most decisions are made by considering only one or two dimensions and ignoring the rest. This produces gut-feel decisions that occasionally land well but often miss obvious tradeoffs.

The Multi-Dimensional Decision Framework forces every dimension to be named, weighted, and scored.

## When to use this framework

Use it for any decision where the wrong choice would cost meaningful budget, time, or strategic position:

- Channel selection (which channels to invest in)
- Platform selection (Google Ads vs Meta vs LinkedIn for a given campaign)
- Audience targeting (which segment to prioritise)
- Budget allocation (how to split across channels)
- Creative direction (which concept to develop)
- Tool / vendor selection (which platform / agency / partner to use)
- Pricing decisions
- Go-to-market sequence (which market to enter first)

Do **not** use it for:
- Trivial decisions (which colour for the button)
- Decisions where data is fully sufficient (a/b test winner is clear)
- Decisions where a constraint forces the answer (only one channel is allowed by compliance)

## The four steps

### Step 1: Identify ALL dimensions that matter

Force yourself to list every dimension, even ones that seem obvious. Common dimensions for marketing decisions:

- Audience presence (does the target audience use this channel/option?)
- Intent match (does the user mode match the option?)
- Conversion potential (likelihood of producing the desired outcome)
- Cost per outcome (CAC, CPC, CPL, CPA)
- Volume potential (can this scale to meet the goal?)
- Competitive density (how crowded is the option?)
- Brand safety (risk of unsafe placements / negative associations)
- Resource requirement (team time, creative production load)
- Time-to-results (immediate vs long-term)
- Measurability (can we attribute outcomes?)
- Strategic fit (does this align with the brand's positioning?)
- Reversibility (can we change course if it does not work?)

For a TikTok decision, the dimensions might be: audience presence (30%), content creation cost (20%), conversion potential (25%), brand safety risk (15%), resource requirement (10%).

### Step 2: Assign weightages

Weights must sum to 100%. Higher weight = more important to this specific decision.

Weights are not universal — they vary by business context. A startup might weight conversion potential highest. An established brand defending share might weight brand safety highest. A budget-constrained team might weight cost highest.

The weights themselves are a strategic decision. Document the rationale.

### Step 3: Score each option

For each option being considered, score 1–10 across every dimension.

Be ruthless about scoring. Avoid the temptation to score everything 7 or 8 (the "everything is fine" trap). Use the full 1–10 range.

If you cannot confidently score a dimension, that is a research gap — note it and decide whether to research before scoring or proceed with a confidence range.

### Step 4: Compute weighted total

For each option:

```
weighted_score = Σ (dimension_score × dimension_weight)
```

The option with the highest weighted score is the recommended choice. Document the math and the rationale.

## Worked example — "Should we add TikTok to our channel mix?"

**Context:** B2B SaaS company, mid-market target, considering TikTok addition.

**Dimensions and weights:**

| Dimension | Weight | Why |
|---|---|---|
| Audience presence | 30% | If the audience is not on TikTok, nothing else matters |
| Conversion potential | 25% | Need to show measurable pipeline impact |
| Content creation cost | 20% | Resource-constrained team |
| Brand safety risk | 15% | B2B audience is less tolerant of brand risk |
| Resource requirement | 10% | Ongoing maintenance load |

**Scores for TikTok:**

| Dimension | Score | Reasoning |
|---|---|---|
| Audience presence | 3 | Mid-market B2B decision-makers (CTOs, VPs of Engineering) are minimally present on TikTok |
| Conversion potential | 2 | Even if reached, the platform is poor for B2B consideration content |
| Content creation cost | 4 | Vertical short-form video requires dedicated production |
| Brand safety risk | 5 | Algorithmic feed adjacency risk |
| Resource requirement | 3 | Daily posting commitment for algorithmic favour |

**Weighted total for TikTok:**
```
(3 × 0.30) + (2 × 0.25) + (4 × 0.20) + (5 × 0.15) + (3 × 0.10)
= 0.9 + 0.5 + 0.8 + 0.75 + 0.3
= 3.25 / 10
```

**Scores for an alternative — "Add LinkedIn Document Ads to existing LinkedIn presence":**

| Dimension | Score |
|---|---|
| Audience presence | 9 |
| Conversion potential | 7 |
| Content creation cost | 7 |
| Brand safety risk | 8 |
| Resource requirement | 7 |

**Weighted total:**
```
(9 × 0.30) + (7 × 0.25) + (7 × 0.20) + (8 × 0.15) + (7 × 0.10)
= 2.7 + 1.75 + 1.4 + 1.2 + 0.7
= 7.75 / 10
```

**Conclusion:** LinkedIn Document Ads (7.75) significantly outscores TikTok (3.25) for this brand. The decision is to deprioritise TikTok and double down on LinkedIn Document Ads.

The conversation with the client is no longer "should we do TikTok?" — it is "we evaluated TikTok across five dimensions weighted by relevance to the business; TikTok scores 3.25 vs LinkedIn at 7.75; here is the math." Defensible.

## How skills use this framework

Skills that produce strategic recommendations (channel selection, platform choice, budget allocation, creative direction) follow this framework explicitly:

1. The skill output names the dimensions considered
2. Names the weights and the rationale
3. Names each option scored
4. Shows the math
5. Recommends the highest-scoring option

Skills that fail to apply this framework produce gut-feel recommendations that are harder to defend and easier to challenge.

## When the framework points to a non-obvious answer

The framework's most valuable use is when the weighted analysis points to an option the team would not have chosen by gut feel.

Example: the team intuitively favours Option A. The weighted analysis ranks Option B higher. This is the moment to:

- Re-examine the dimension weights (are we weighting correctly?)
- Re-examine the scores (are we biased in our scoring?)
- Re-examine the dimensions (is there a missing dimension that would tip back to A?)

If after this re-examination the framework still favours B, choose B and document why the gut-feel A was the wrong call. If after re-examination the team still believes A is right, document the override and the reasoning — this is institutional learning about when the framework misses something.

## What this framework does NOT do

The framework does not:

- **Make decisions for you.** It structures decisions; humans still decide.
- **Eliminate uncertainty.** Scores are best-effort estimates. Confidence intervals matter.
- **Replace judgment.** Some dimensions defy precise scoring. Note them, score honestly, and let weighted totals guide rather than dictate.
- **Work without good data.** If scores are guesses without basis, the framework just structures bad guesses into a polished output. Garbage in, garbage out.

## Related references

- [unit-economics-framework.md](unit-economics-framework.md) — adds CAC/LTV constraints to decision-making
- [in-market-out-market.md](in-market-out-market.md) — adds budget split constraints
- [four-core-documents-spec.md](four-core-documents-spec.md) — Core Doc 3.4 DMFlow uses this framework for channel selection
