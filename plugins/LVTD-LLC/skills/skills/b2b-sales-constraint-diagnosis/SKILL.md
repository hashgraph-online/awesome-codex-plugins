---
name: b2b-sales-constraint-diagnosis
description: Diagnose the single B2B sales constraint currently limiting pipeline or revenue and route to the right repair workflow. Use when sales feels stuck, pipeline is weak, leads ghost, outbound is not working, conversion is unclear, or the team is debating whether to fix reach, messaging, follow-up timing, or trust.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: B2B Sales Constraint Diagnosis
  category: Marketing
  tags: b2b-sales,sales,pipeline,diagnosis,constraints
---

# B2B Sales Constraint Diagnosis

Use this skill to find the sales bottleneck before recommending tactics. The
goal is to identify the one constraint that is throttling the current sales
system, then route work to the most relevant repair skill.

## Source Traceability

Primary source: Unf*ck Your Sales by Jakob Greenfeld. Authoring notes used the
sections "Our Map, Lens, and Compass", "The One Sentence Sales Course",
"Invert, Always Invert!", "The Theory of Constraints", and "Putting It
Together".

## Constraint Model

Diagnose in this order:

1. **Reach** - the right people do not know the company exists.
2. **Resonance** - the right people see the company but do not connect it to a
   painful problem, concrete outcome, and credible mechanism.
3. **Timing** - buyers know and understand the company, but the company is not
   present when pain becomes urgent.
4. **Trust** - qualified buyers engage but do not feel enough certainty or risk
   reduction to take action.

Only one constraint should be treated as primary at a time. Everything else is
secondary until the primary constraint is fixed or disproven.

## Diagnostic Workflow

1. Restate the current sales symptom and stage:
   - No awareness or no replies.
   - Replies but poor recall or weak understanding.
   - Interest but no urgency or inconsistent timing.
   - Qualified calls, proposals, or trials that stall or ghost.
2. Check for basic evidence before diagnosing:
   - Target segment or account list.
   - Recent outreach or visibility activity.
   - Message or offer being used.
   - Lead, meeting, close, and ghosting data.
3. Run the constraint checks:
   - **Reach**: Have enough named buyers in the target market been reached at
     least once?
   - **Resonance**: Can target buyers explain what the company does, who it is
     for, and what problem it solves?
   - **Timing**: Has every viable buyer seen or heard from the company in the
     last 4-6 weeks?
   - **Trust**: Do qualified buyers close at an acceptable rate once they engage?
4. Pick the weakest proven constraint. If evidence is missing, recommend the
   smallest diagnostic test rather than guessing.
5. Route next work:
   - Reach problem: use `b2b-reach-engineering`.
   - Resonance problem: use `b2b-resonance-audit`.
   - Timing problem: use `b2b-timing-engine`.
   - Trust problem: use `b2b-trust-engineering`.

## Output Format

```markdown
# B2B Sales Constraint Diagnosis

## Current Symptom
- Segment:
- Offer:
- Sales motion:
- Evidence reviewed:

## Constraint Assessment
| Constraint | Evidence | Pass/Concern | Confidence |
|------------|----------|--------------|------------|
| Reach | | | |
| Resonance | | | |
| Timing | | | |
| Trust | | | |

## Primary Constraint
[Name the one constraint and why it is most likely throttling growth.]

## Next Diagnostic Or Repair
- Use skill:
- First action:
- Success signal:
- Do not optimize yet:
```

## Quality Bar

- Do not prescribe tactics before naming the constraint.
- Do not optimize messaging, follow-up, funnels, or close tactics if the market
  has not actually been reached.
- Do not diagnose rejection when the market may simply be unaware.
- Do not work on multiple bottlenecks at once unless the user explicitly wants a
  broad audit.
- Treat missing evidence as a diagnostic task, not permission to guess.
