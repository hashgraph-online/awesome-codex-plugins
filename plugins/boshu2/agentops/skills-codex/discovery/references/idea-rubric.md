# Idea Evaluation Rubric

> The ten-dimension rubric for scoring and winnowing ideas in ideation mode
> (`ideation-mode.md`). Adapted for AgentOps — tracking is `br` with `bv` triage.

Ideas are evaluated on: **robust, reliable, performant, intuitive, user-friendly,
ergonomic, useful, compelling, accretive, pragmatic.** A good idea makes the
project obviously better while staying obviously accretive and pragmatic.

## Quick Score Card

Rate each idea 1-5 on each criterion:

| Criterion | 1 (Poor) | 3 (Acceptable) | 5 (Excellent) |
|-----------|----------|----------------|---------------|
| **Robust** | Breaks on edge cases | Handles common cases | Handles all cases gracefully |
| **Reliable** | Intermittent failures | Usually works | Always works |
| **Performant** | Noticeably slow | Acceptable speed | Imperceptibly fast |
| **Intuitive** | Confusing UX | Learnable | Obvious immediately |
| **User-friendly** | Frustrating | Neutral | Delightful |
| **Ergonomic** | Adds friction | No change | Reduces friction |
| **Useful** | Solves nothing | Solves minor pain | Solves major pain |
| **Compelling** | Nobody wants | Nice to have | Must have |
| **Accretive** | Negative value | Marginal value | Clear value |
| **Pragmatic** | Impossible | Difficult | Straightforward |

**Threshold:** Ideas scoring <3 average should be cut.

## Detailed Criteria

### Robust
Does it handle empty input, malformed input, unicode, concurrent access? Does it
fail gracefully?

### Reliable
Does it work the first time and the 1000th time? Under load? Offline? Does it
recover from errors?

### Performant
Is latency acceptable (<100ms for interactive)? Is throughput sufficient? Does it
scale with data size and use resources efficiently?

### Intuitive
Can users predict behavior? Are defaults sensible? Is naming clear? Do errors
explain themselves?

### User-friendly
Is the happy path smooth? Are error messages helpful? Is recovery easy? Is help
accessible?

### Ergonomic
How many steps to accomplish the goal? How much typing? Are shortcuts available?
Does it reduce cognitive load?

### Useful
What problem does it solve? How often does the problem occur and how painful is
it? Does it create new problems?

### Compelling
Would users request it, switch for it, recommend it, miss it?

### Accretive
Does it add capability, reduce complexity, improve existing features, open new
possibilities? Is the value measurable?

### Pragmatic
Is the technology mature? Is the scope clear? Are dependencies manageable? Is the
timeline reasonable?

## Winnowing Process (30 → 5)

### Round 1: Hard Cuts
Remove any idea that scores 1 on ANY criterion.

### Round 2: Threshold
Remove any idea scoring <3 average.

### Round 3: Ranking
Sort remaining by weighted average:

- Useful: 2x weight
- Pragmatic: 2x weight
- Accretive: 1.5x weight
- Others: 1x weight

### Round 4: Synergy
Consider which ideas complement each other. A weaker idea that enables a stronger
idea may be worth keeping in the expanded 15.

## Red Flags (immediate disqualification)

- "Users will figure it out"
- "We'll document it later"
- "It's technically correct"
- "Nobody does it differently"
- "We've always done it this way"

## Relationship to the red-team checklist

The rubric scores how GOOD an idea is. The `red-team-checklist.md` stress-tests
how an idea BREAKS. Run both: rubric for ranking, red team for risk
classification. An idea that scores high on the rubric but fails 2+ red-team
questions is HIGH RISK and needs a mitigation plan before it survives the winnow.
