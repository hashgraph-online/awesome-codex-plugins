# Rust Game Slice Planning Reference

Use this file when turning a game idea into a sequence of safe coding tasks for
an AI agent.

## Short Design Brief

Create a small design record before coding:

```markdown
# Game Brief

## Working Title
[Name]

## Short Description
[One paragraph. Include player fantasy, viewpoint, and genre.]

## Core Loop
1. [Start state]
2. [Player action]
3. [Game response]
4. [Reward, risk, or progression]
5. [Repeat or exit condition]

## MVP
- [ ] [One required mechanic]
- [ ] [One required screen/state]
- [ ] [One required win/loss/progression condition]

## Stretch Goals
- [ ] [Optional after MVP]

## Constraints
- Engine/framework:
- Target platform:
- Art style:
- Input:
```

## Slice Rules

- Each slice must leave the project compiling and runnable.
- Each slice should add one visible behavior, not a whole subsystem family.
- Put optional content in stretch goals until the MVP loop exists.
- Prefer a plain implementation over a generic framework until two real use
  cases need the abstraction.
- Record acceptance checks before coding the slice.
- Stop a slice when its checks pass; move polish to a separate slice.

## Recommended Slice Order

| Slice | Goal | Acceptance checks |
|---|---|---|
| Project boot | Window, loop, blank scene | `cargo run` opens the game and exits cleanly |
| Input and player | Player can perform one core action | Input visibly changes game state |
| World surface | Minimal map, arena, or level exists | Player is constrained by world rules |
| Core obstacle | One enemy, hazard, puzzle, or timer | Player can fail or be blocked |
| Resolution | Win, loss, score, or level transition | Player can complete a full loop |
| Feedback | HUD, messages, audio, or visual cues | Player can understand state changes |
| Content | More maps, enemies, items, or balance | Content uses existing systems |
| Packaging | Release build and resource check | Release build runs with assets |

## AI Agent Guardrails

Ask these before adding code:

1. Does this belong to the current slice or a later stretch goal?
2. Can this be represented with concrete types for now?
3. Can the mechanic be verified without playing for several minutes?
4. Is the code path reachable from the current game loop?
5. Is there a smaller version that proves the idea?

## Red Flags

- Building save/load before the first playable loop.
- Adding multiple enemy types before one enemy works.
- Creating an editor or content pipeline before hand-authored content works.
- Introducing a plugin system for one implementation.
- Balancing numbers before the mechanics are observable.
- Treating "make it fun" as a task without measurable checks.

## Sprint Template

```markdown
## Slice: [Name]

Goal:

In scope:
- 

Out of scope:
- 

Implementation steps:
1. 
2. 
3. 

Acceptance checks:
- [ ] `cargo fmt`
- [ ] `cargo clippy` or project lint command
- [ ] `cargo test` if tests exist
- [ ] Manual smoke check:
```
