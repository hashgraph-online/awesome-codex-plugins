---
name: game-mechanics-design
description: Design, inspect, or repair game mechanics, core loops, rules, goals, actions, state, chance, secrets, skills, and emergent dynamics. Use when building gameplay systems, combat, puzzles, progression, simulations, board/card mechanics, or any feature where rules create player behavior.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Game Mechanics Design
  category: Game Development
  tags: game-design,mechanics,systems,core-loop,emergence
---

# Game Mechanics Design

Use this skill to make gameplay systems explicit enough for an AI coding agent to implement, test, and tune. The mechanic spec should separate rule structure from presentation so the same idea can be prototyped cheaply before polish.

## Source Traceability

Primary source: *The Art of Game Design: A Book of Lenses, Third Edition* by Jesse Schell, especially chapters 12-14 on mechanics, balance, and puzzles. The workflow is transformed and paraphrased.

Supporting source: MDA, which helps distinguish coded mechanics from the player-visible dynamics and aesthetic experience they produce.

## Workflow

1. Identify the core loop: player input, system response, feedback, reward or consequence, and next decision.
2. Specify mechanics across space, time, objects, attributes, state, actions, rules, goals, skill, chance, and information visibility.
3. Predict dynamics: dominant strategies, degenerate loops, emergent interactions, pacing, and failure states.
4. Define player mastery: what starts simple, what becomes expressive, and how players improve.
5. Produce implementation-ready rules with test cases and tuning parameters.

## Required Output

- `Mechanic Brief`: player promise, core loop, and intended dynamics.
- `Rules Model`: state, objects, actions, rules, goals, and information.
- `Implementation Notes`: data structures, tunable constants, edge cases, and instrumentation.
- `Failure Modes`: exploits, dead ends, unreadable outcomes, and boring optimal play.
- `Test Scenarios`: deterministic cases the agent can implement.

## Local References

Before producing a mechanic spec, read:

- `references/core/guide.md`
- `workflows/mechanic-spec.md`
