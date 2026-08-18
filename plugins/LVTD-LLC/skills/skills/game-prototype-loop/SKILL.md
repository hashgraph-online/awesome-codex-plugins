---
name: game-prototype-loop
description: Turn a game idea into a focused design problem, risk-first prototype plan, and iteration loop. Use when starting a game, choosing what to build first, scoping an MVP, defining design questions, planning prototypes, or deciding whether an idea is ready for production.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Game Prototype Loop
  category: Game Development
  tags: game-design,prototyping,iteration,mvp,risk
---

# Game Prototype Loop

Use this skill to convert vague game intent into buildable experiments. The default stance is risk-first: identify what must be true for the game to work, then build the cheapest prototype that can answer that question.

## Source Traceability

Primary source: *The Art of Game Design: A Book of Lenses, Third Edition* by Jesse Schell, especially chapters 7-8 on idea generation, problem statements, filters, risk, prototyping, and iteration. The workflow is transformed and paraphrased from those ideas rather than copied.

Supporting source: Hunicke, LeBlanc, and Zubek's MDA framework for separating mechanics, dynamics, and aesthetics during prototype evaluation.

## Workflow

1. State the target player experience in one sentence.
2. Reframe the idea as a design problem with constraints, not as a feature list.
3. List the riskiest assumptions: fun, clarity, feasibility, controls, production cost, content burden, performance, market fit, and multiplayer or systems complexity.
4. Choose one prototype per major risk. Prefer paper, spreadsheet, greybox, or throwaway code before production code.
5. Define the prototype's success signal before building it.
6. Run the build-play-observe-decide loop until the risk is retired, reframed, or accepted.
7. Convert learning into a next action: cut, keep, change, defer, or productionize.

## Required Output

When invoked, produce:

- `Design Problem`: the player-facing experience and constraints.
- `Assumption Map`: ranked risks with why each matters.
- `Prototype Plan`: prototype type, scope, build time, success signal, and kill/change criteria.
- `Iteration Loop`: cadence, test method, evidence to collect, and next decision.
- `Build Notes`: exact implementation guidance for the coding agent.

## Local References

Before producing a full plan, read:

- `references/core/guide.md`
- `workflows/risk-first-prototype.md`
