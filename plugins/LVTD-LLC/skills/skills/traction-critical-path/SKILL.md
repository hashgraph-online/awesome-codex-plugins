---
name: traction-critical-path
description: Set traction goals and identify the Critical Path from Traction so teams focus only on milestones needed for growth. Use when a startup has too many priorities, needs growth goals, is debating product versus marketing work, or wants to decide what not to do.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Traction Critical Path
  category: Marketing
  tags: traction,growth,strategy,startups,prioritization
---

# Traction Critical Path

Use this skill to convert an ambiguous growth objective into a measurable
traction goal, required milestones, and a disciplined "not now" list.

## Source Traceability

Primary source: Traction, chapters 2 and 5.

- Chapter 2 covers the 50 percent rule, moving the needle, growth phases, and
  bright spots. Authoring notes: converted lines 394-554.
- Chapter 5 defines traction goals, Critical Path milestones, reassessment, and
  channel bias. Authoring notes: converted lines 787-902.

## Workflow

### 1. Identify The Growth Stage

Classify the current stage:

| Stage | Main Question | Typical Goal |
|-------|---------------|--------------|
| Phase I | Can the product get real traction? | First engaged customers or proof of demand |
| Phase II | Can this become sustainable? | Enough customers or revenue to approach sustainability |
| Phase III | Can this scale profitably? | Larger growth, market position, or profit expansion |

If the product is early, keep tests small and feedback-rich. If it is later,
insist on goals large enough to move the business.

### 2. Define The Traction Goal

The traction goal should be quantitative, time-bound, and meaningful enough to
change the company's situation.

Good goals include:

- Reach 1,000 paying customers by a date.
- Add 100 qualified trials per week.
- Hit a break-even revenue number.
- Reach a market-share threshold that changes partnership or investor leverage.

Weak goals include:

- Get more awareness.
- Do marketing.
- Improve engagement without defining the metric.

### 3. Work Backward Into Necessary Milestones

List milestones that are absolutely necessary to hit the goal. Include product,
distribution, hiring, analytics, partnership, or operational milestones only if
they are required.

For each candidate milestone, ask:

- If this does not happen, can we still hit the traction goal?
- Is this a prerequisite or just attractive?
- What evidence supports this being necessary?
- What would make us remove or replace it?

### 4. Cut Off-Path Work

Create an explicit off-path list. This matters because founders often spend
scarce time on useful work that is not necessary for the current traction goal.

Off-path work can include:

- Feature requests that do not unlock the next growth stage.
- Marketing activities that cannot move the needle.
- Partnerships, events, or content that produce activity without traction.
- Infrastructure polish that does not affect the current bottleneck.

### 5. Reassess After Every Milestone

The Critical Path changes as evidence changes. After each milestone, update:

- Goal confidence.
- Bottleneck.
- Milestone order.
- Off-path list.
- Next test or build decision.

## Output Format

```markdown
# Critical Path Plan

## Traction Goal
- Metric:
- Target:
- Deadline:
- Why it matters:

## Stage
[Phase I, II, or III, with reasoning.]

## Critical Path
| Order | Milestone | Why Required | Evidence Needed | Owner/Deadline |
|-------|-----------|--------------|-----------------|----------------|

## Off-Path List
| Activity | Why It Is Off Path | Revisit Trigger |
|----------|--------------------|-----------------|

## Reassessment Cadence
- Review after:
- Metrics to inspect:
- Decision rules:
```

## Quality Bar

- Do not accept vague growth goals.
- Do not include milestones merely because they are valuable.
- Do not let product work crowd out traction work by default.
- Name bright spots when growth is weak but some users are highly engaged.
- Recommend a pivot only after checking engagement evidence and timing risk.
