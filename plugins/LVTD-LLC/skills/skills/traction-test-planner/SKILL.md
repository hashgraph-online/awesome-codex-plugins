---
name: traction-test-planner
description: Design cheap, measurable traction tests from Traction for startup growth channels. Use when planning marketing experiments, middle-ring tests, A/B tests, acquisition test spreadsheets, channel validation, or growth experiment success criteria.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Traction Test Planner
  category: Marketing
  tags: traction,growth,experiments,marketing,analytics
---

# Traction Test Planner

Use this skill to design traction tests that create decision-quality evidence.
It turns a candidate channel strategy into a scoped experiment with assumptions,
metrics, budget, duration, and next-step rules.

## Source Traceability

Primary source: Traction, chapters 3 and 4, plus the appendix.

- Chapter 3 defines the three core test questions for middle-ring channels.
  Authoring notes: converted lines 585-606.
- Chapter 4 distinguishes cheap channel tests from optimization and explains
  inner-ring testing. Authoring notes: converted lines 675-786.
- The appendix lists phase I test prompts for the 19 traction channels.
  Authoring notes: converted lines 3323-3372.

See [middle-ring-test-prompts.md](references/middle-ring-test-prompts.md) for
paraphrased starter tests by channel.

## Test Types

### Middle-Ring Test

Use when validating whether a channel strategy could become the core channel.
Keep it cheap, fast, and strategy-level.

Answer:

1. Acquisition cost: what would it cost to acquire a customer?
2. Reach: how many relevant customers may be available?
3. Fit: are these customers desirable right now?

### Inner-Ring Test

Use after a core channel is chosen. Inner-ring tests optimize the winning
strategy or search for a better strategy inside the same channel.

Examples:

- Test a new audience, keyword group, offer, landing page, creative angle, or
  partner segment.
- Run A/B tests where traffic and measurement are already in place.
- Use other channels only as support for the core channel, not as competing
  strategies.

## Workflow

### 1. State The Decision

Write the decision the test must enable. Good tests decide something specific:

- Continue, kill, or revise this channel strategy.
- Promote this channel into the inner ring.
- Scale spend, hold spend, or change audience.
- Choose between two channel strategies.

### 2. Write Assumptions

List the assumptions that must be true for the strategy to work.

Use this structure:

| Assumption | How Test Measures It | Kill Threshold |
|------------|----------------------|----------------|

### 3. Set Metrics

At minimum, include:

- Reach available.
- Conversion rate.
- Cost to acquire a customer.
- Customer quality or intent.
- Lifetime value estimate, if available.

If the user lacks analytics, include a setup step before the test. A test
without tracking creates anecdotes, not evidence.

### 4. Bound Budget And Time

For early-stage tests, prefer less than one month and a small budget. If the
user proposes a large test before there is evidence, reduce scope.

### 5. Define Outcomes Before Running

Every test needs decision rules:

- **Double down** when results beat the success threshold and customer quality is
  acceptable.
- **Iterate** when one metric fails but the channel shows a fixable signal.
- **Kill** when reach, cost, or customer fit cannot plausibly move the traction
  goal.

## Output Format

```markdown
# Traction Test Plan

## Decision
[What this test will decide.]

## Channel Strategy
- Channel:
- Strategy:
- Target customer:
- Stage:

## Assumptions
| Assumption | Measurement | Threshold |
|------------|-------------|-----------|

## Experiment Design
- Setup:
- Audience/source:
- Offer/message:
- Landing or conversion path:
- Budget:
- Duration:

## Metrics
| Metric | Target | Tracking Method |
|--------|--------|-----------------|

## Decision Rules
- Double down if:
- Iterate if:
- Kill if:

## Next Step After Test
[What to do for each likely outcome.]
```

## Quality Bar

- Do not design tests that only measure vanity traffic.
- Do not optimize multiple variables before validating strategy-level promise.
- Make tracking explicit before the test starts.
- Prefer comparable metrics across channels.
- Call out when the test cannot plausibly move the user's traction goal.
