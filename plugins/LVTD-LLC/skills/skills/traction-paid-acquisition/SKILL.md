---
name: traction-paid-acquisition
description: Plan paid acquisition tests from Traction across SEM, social/display ads, and offline ads. Use when designing ad experiments, keyword tests, audience tests, paid channel budgets, or deciding whether a paid channel can acquire the right customers profitably.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Traction Paid Acquisition
  category: Marketing
  tags: traction,ads,sem,paid-acquisition,marketing
---

# Traction Paid Acquisition

Use this skill to design paid acquisition experiments that validate customer
quality and economics before scaling spend.

## Source Traceability

Primary source: Traction, chapters 9-11 and the appendix. Authoring notes:
converted lines 1233-1627 and 3335-3340.

## Channels

- **SEM**: test high-intent search demand and conversion economics.
- **Social and display ads**: test targeted audiences, creative, and offer
  resonance.
- **Offline ads**: test channels that competitors may ignore, especially niche
  podcasts, local media, or audience-specific placements.

## Workflow

1. State the buying intent or audience hypothesis.
2. Select one paid channel strategy, not a broad paid marketing mix.
3. Define the conversion event that matters.
4. Set a small budget and time box.
5. Create a minimal landing path with tracking.
6. Estimate break-even CAC from price, margin, and LTV.
7. Run the test and compare CAC, conversion quality, and reachable volume.

## Output Format

```markdown
# Paid Acquisition Test

## Hypothesis
[Audience/intent + offer + expected conversion.]

## Channel Strategy
- Channel:
- Audience or keywords:
- Offer:
- Budget:
- Duration:

## Economics
| Metric | Estimate |
|--------|----------|
| Price/LTV | |
| Gross margin | |
| Break-even CAC | |
| Target CAC for test | |

## Creative/Copy
- Ad angle 1:
- Ad angle 2:
- Landing page promise:

## Tracking
- Conversion event:
- Attribution method:
- Customer quality check:

## Decision Rules
- Double down:
- Iterate:
- Kill:
```

## Quality Bar

- Track conversions, not only clicks.
- Compare CAC against LTV or expected customer value.
- Keep early tests narrow enough to interpret.
- Avoid large budgets before one strategy has signal.
