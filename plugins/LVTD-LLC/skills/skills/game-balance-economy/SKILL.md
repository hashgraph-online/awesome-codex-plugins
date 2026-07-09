---
name: game-balance-economy
description: Balance game difficulty, resources, rewards, probability, progression, economies, and dominant strategies. Use when tuning combat, loot, upgrades, scoring, level curves, AI difficulty, risk-reward choices, or any system where numbers shape player decisions.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Game Balance Economy
  category: Game Development
  tags: game-design,balance,economy,progression,probability
---

# Game Balance Economy

Use this skill when a game system needs numerical tuning. Balance is not just fairness; it is the shape of player decisions over time. A good balance pass names the intended experience before changing numbers.

## Source Traceability

Primary source: *The Art of Game Design: A Book of Lenses, Third Edition* by Jesse Schell, especially chapters 12-13 on chance, expected value, fairness, challenge, meaningful choices, rewards, punishment, and economies. The workflow is transformed and paraphrased.

Supporting sources include MDA for reasoning from mechanics to dynamics and accessibility guidance for difficulty options that preserve player agency.

## Workflow

1. Define the target experience: tense, generous, punishing, expressive, strategic, chaotic, readable, or mastery-driven.
2. Map resources, sinks, sources, rewards, costs, probabilities, time, and failure penalties.
3. Find dominant strategies, dead choices, runaway feedback, grind, scarcity collapse, and opaque randomness.
4. Use expected value and simulation where useful, but validate with playtests.
5. Produce a tuning table with ranges, defaults, rationale, and telemetry.

## Required Output

- `Balance Intent`: what the numbers should make players feel and do.
- `Economy Map`: sources, sinks, currencies, rewards, gates, and conversion rates.
- `Tuning Table`: parameters, default values, safe ranges, and intended effects.
- `Risk Review`: dominant strategies, exploits, fairness issues, and accessibility concerns.
- `Validation Plan`: spreadsheet checks, script checks, playtest tasks, and telemetry.

## Helper Script

Use `scripts/expected_value.py` for quick expected value checks:

```bash
python3 path/to/game-balance-economy/scripts/expected_value.py --outcome 0:0.5 --outcome 10:0.5
```

## Local References

Before producing a tuning plan, read:

- `references/core/guide.md`
- `workflows/tuning-pass.md`
