---
name: traction-review
description: Review traction experiment results and recommend whether to double down, iterate, repeat Bullseye, or pivot. Use when analyzing growth test data, comparing channel performance, deciding if a channel moved the needle, or reassessing startup traction strategy.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Traction Review
  category: Marketing
  tags: traction,growth,experiments,analytics,strategy
---

# Traction Review

Use this skill after traction tests have run. The goal is to turn results into a
decision: focus, iterate, repeat Bullseye, or reconsider the product or market.

## Source Traceability

Primary source: Traction, chapters 2-5. Authoring notes: converted lines
394-902.

## Review Workflow

1. Restate the traction goal and current growth stage.
2. Compare results against the prewritten success and kill thresholds.
3. Evaluate customer quality, not only volume.
4. Decide whether the result moved the needle for the current stage.
5. Identify bright spots: small customer groups with unusually strong
   engagement, conversion, retention, or willingness to pay.
6. Recommend one decision:
   - double down on the core channel,
   - run inner-ring optimization,
   - run another middle-ring test,
   - repeat Bullseye with new information,
   - revisit product, market, or positioning.

## Output Format

```markdown
# Traction Review

## Goal And Context
- Goal:
- Stage:
- Test period:

## Results
| Channel/Strategy | Cost | Reach | Conversion | Customer Fit | Notes |
|------------------|------|-------|------------|--------------|-------|

## Decision
[Double down, iterate, repeat Bullseye, or revisit product/market.]

## Reasoning
- What moved the needle:
- What failed:
- Bright spots:
- Risks:

## Next Actions
1. [Action]
2. [Action]
3. [Action]
```

## Quality Bar

- Do not declare success from vanity metrics.
- Do not pivot before checking bright spots and engagement evidence.
- Do not keep secondary channels alive just because they somewhat worked.
- Reassess the Critical Path after meaningful evidence.
