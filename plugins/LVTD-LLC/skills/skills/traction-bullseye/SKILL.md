---
name: traction-bullseye
description: Apply the Bullseye framework from Traction to brainstorm, rank, test, and focus startup traction channels. Use when choosing growth channels, overcoming channel bias, prioritizing marketing experiments, or deciding which acquisition channel deserves focused effort.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Traction Bullseye
  category: Marketing
  tags: traction,growth,marketing,startups,prioritization
---

# Traction Bullseye

Use this skill to turn vague growth ideas into a ranked set of traction channel
tests and one focused core channel. It is based on the Bullseye framework from
Traction by Gabriel Weinberg and Justin Mares.

## Source Traceability

Primary source: Traction, chapters 1, 3, and 5.

- Chapter 1 introduces the 19 traction channels and warns against dismissing
  unfamiliar channels too early. Authoring notes: converted lines 238-393.
- Chapter 3 defines Bullseye: outer ring, middle ring, inner ring, and focus on
  one core channel. Authoring notes: converted lines 555-674.
- Chapter 5 covers channel bias and the 19-channel review. Authoring notes:
  converted lines 787-902.

See [source-map.md](references/source-map.md) for the channel list and line
references used while authoring this skill.

## Workflow

### 1. Define The Current Traction Goal

Start with the measurable outcome the company needs next. A channel cannot be
ranked well until the goal is explicit.

Capture:

- Stage: phase I, phase II, or phase III.
- Target metric: users, revenue, customers, usage, qualified leads, market
  share, or another growth metric.
- Deadline.
- Required volume.
- Constraint: budget, team capacity, geography, product readiness, sales cycle,
  or regulatory constraint.

If the user has no goal, ask for one or propose a provisional goal and label it
as an assumption.

### 2. Fill The Outer Ring

Generate at least one plausible strategy for each traction channel before
ranking anything. This counters default bias toward familiar channels.

Use this full channel list:

1. Targeting blogs
2. Publicity
3. Unconventional PR
4. Search engine marketing
5. Social and display ads
6. Offline ads
7. Search engine optimization
8. Content marketing
9. Email marketing
10. Viral marketing
11. Engineering as marketing
12. Business development
13. Sales
14. Affiliate programs
15. Existing platforms
16. Trade shows
17. Offline events
18. Speaking engagements
19. Community building

For each channel, write:

- One specific strategy.
- Why it might work for this product.
- What evidence would make it more promising.
- What assumption would kill it.

Do not discard a channel because it feels unfashionable, manual, or outside the
team's comfort zone. Mark concerns, then continue.

### 3. Promote The Middle Ring

Choose roughly three promising channels for cheap tests. Prefer channels that:

- Could plausibly move the traction goal.
- Have reachable customers now.
- Can be tested cheaply within the current stage.
- Produce interpretable data quickly.
- Are underused by competitors or unusually well-matched to the product.

When the ranking is uncertain, use the stronger testability criterion: pick the
channel where a small test would teach the most.

### 4. Define Tests

For each middle-ring channel, design one cheap test that answers:

1. How much could it cost to acquire a customer?
2. How many relevant customers may be reachable?
3. Are these the right customers right now?

Keep phase I tests small. The point is signal, not scale.

### 5. Pick Or Defer The Inner Ring

Recommend an inner-ring core channel only if one test result is meaningfully
stronger than the others. If no channel has enough evidence, recommend another
Bullseye pass using what was learned.

Once a core channel is chosen, focus. Other channels may support it, but should
not become parallel growth strategies unless the core channel stops moving the
needle.

## Output Format

Use this structure:

```markdown
# Bullseye Recommendation

## Traction Goal
- Goal:
- Deadline:
- Stage:
- Constraints:

## Outer Ring
| Channel | Strategy | Why It Could Work | Evidence Needed | Key Assumption |
|---------|----------|-------------------|-----------------|----------------|

## Middle Ring
| Rank | Channel | Test | Budget/Time | Success Signal |
|------|---------|------|-------------|----------------|

## Inner Ring Decision
[Choose core channel, defer decision, or repeat Bullseye.]

## Next Actions
1. [Action]
2. [Action]
3. [Action]
```

## Quality Bar

- Do not recommend a channel just because it is popular.
- Do not skip channels without naming the bias or constraint.
- Do not optimize tactics before choosing a promising strategy.
- Use numbers whenever possible, even if they are explicit estimates.
- Preserve losing channel ideas for later Bullseye rounds.
