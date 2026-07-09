---
name: player-experience-modeling
description: Model target players, motivations, emotions, pleasures, needs, flow, novelty, judgment, and interest curves. Use when defining who a game is for, shaping retention, diagnosing boredom or confusion, designing progression, or aligning gameplay with a desired emotional arc.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Player Experience Modeling
  category: Game Development
  tags: game-design,player-research,motivation,flow,interest-curve
---

# Player Experience Modeling

Use this skill to define the experience the game is trying to create before implementing systems. It gives an AI game-building agent a target for taste, pacing, onboarding, and progression decisions.

## Source Traceability

Primary source: *The Art of Game Design: A Book of Lenses, Third Edition* by Jesse Schell, especially chapters 2, 9-11, and 16 on experience, players, pleasure, flow, motivation, novelty, judgment, and interest curves. The workflow is transformed and paraphrased.

Supporting source: Self-Determination Theory for autonomy, competence, and relatedness as durable motivation lenses.

## Workflow

1. Define the target player by behavior and context, not demographic shorthand.
2. Identify the desired emotional and motivational promise.
3. Map pleasures, needs, novelty, mastery, and social drivers.
4. Shape the interest curve across first minute, first session, midpoint, climax, and return session.
5. Translate experience goals into implementation constraints and telemetry.

## Required Output

- `Player Model`: target player, context, skills, anxieties, and motivations.
- `Experience Promise`: what the game should make the player feel and do.
- `Motivation Map`: autonomy, competence, relatedness, novelty, mastery, expression, and reward drivers.
- `Interest Curve`: beats, intensity, variety, and recovery.
- `Build Implications`: onboarding, feedback, difficulty, pacing, progression, and content priorities.

## Local References

Before producing an experience model, read:

- `references/core/guide.md`
- `workflows/experience-brief.md`
