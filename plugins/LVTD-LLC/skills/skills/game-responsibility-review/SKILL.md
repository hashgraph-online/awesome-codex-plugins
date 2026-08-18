---
name: game-responsibility-review
description: Review a game for player impact, ethics, transformation, inclusion, monetization pressure, community risk, dark patterns, and hidden design agendas. Use before shipping manipulative loops, social systems, ads, monetization, retention mechanics, UGC, or player-generated communities.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Game Responsibility Review
  category: Game Development
  tags: game-design,ethics,safety,monetization,community
---

# Game Responsibility Review

Use this skill to evaluate what a game teaches, rewards, pressures, or normalizes. The goal is not to remove all friction or intensity; it is to make deliberate choices about player impact.

## Source Traceability

Primary source: *The Art of Game Design: A Book of Lenses, Third Edition* by Jesse Schell, especially chapters 33-35 on transformation, responsibility, and purpose. The workflow is transformed and paraphrased.

Supporting sources include accessibility guidance and community safety practice where relevant.

## Workflow

1. State the intended player transformation or after-effect.
2. Identify pressures created by rewards, scarcity, social comparison, streaks, ads, monetization, and notifications.
3. Review vulnerable player contexts: children, compulsive behavior, spending pressure, harassment, exclusion, and accessibility barriers.
4. Distinguish deliberate tension from accidental harm.
5. Recommend design changes, policy limits, instrumentation, and review gates.

## Required Output

- `Purpose Statement`: what the game should leave players with.
- `Impact Map`: beneficial, neutral, and risky effects.
- `Pressure Review`: retention, monetization, social, scarcity, and notification mechanics.
- `Risk Controls`: product changes, limits, disclosures, parental or accessibility options, moderation, and telemetry.
- `Ship Gate`: unresolved issues that should block release or require explicit owner approval.

## Local References

Before producing a responsibility review, read:

- `references/core/guide.md`
- `workflows/responsibility-audit.md`
