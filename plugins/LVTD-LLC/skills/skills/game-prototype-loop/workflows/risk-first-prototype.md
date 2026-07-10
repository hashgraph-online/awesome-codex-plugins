# Risk-First Prototype Workflow

## Input Contract

Ask for or infer:

- Game concept
- Target platform
- Target player
- Available build time
- Engine or tech stack
- Non-negotiable constraints

## Procedure

1. Write the design problem as: "Create a game where [target player] can [core activity] and feels [experience] under [constraints]."
2. List 5-12 assumptions and mark each as `fatal`, `major`, or `minor`.
3. Pick the top 1-3 assumptions by uncertainty multiplied by consequence.
4. For each chosen assumption, choose the cheapest prototype type.
5. Define a measurable or observable success signal.
6. Tell the coding agent exactly what to build and what not to build.
7. After the test, classify the result:
   - `Retire`: risk is sufficiently answered.
   - `Refine`: risk needs a narrower prototype.
   - `Pivot`: the concept must change.
   - `Stop`: the idea no longer justifies build effort.

## Output Template

```markdown
## Design Problem

## Top Risks
| Rank | Risk | Severity | Unknown | Why It Matters |

## Prototype Backlog
| Prototype | Tests | Build Scope | Exclusions | Success Signal | Decision Rule |

## First Build Instructions

## Evidence To Capture

## Next Decision
```
