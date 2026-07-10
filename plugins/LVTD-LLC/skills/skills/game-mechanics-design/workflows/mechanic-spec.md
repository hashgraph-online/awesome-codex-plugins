# Mechanic Spec Workflow

## Procedure

1. Name the mechanic using a player-facing verb phrase.
2. Define the player promise in one sentence.
3. Write the core loop in 4-7 steps.
4. Build the rules model:
   - entities
   - attributes
   - states
   - actions
   - legal transitions
   - win, loss, reward, and fail conditions
5. Mark every parameter that should be tunable.
6. Predict 3 desired dynamics and 3 unwanted dynamics.
7. Create a first implementation slice with no polish dependencies.
8. Add test scenarios and debug instrumentation.

## Output Template

```markdown
## Mechanic Brief

## Core Loop

## Rules Model
| Element | Definition | Tunable? | Notes |

## Desired Dynamics

## Failure Modes

## Implementation Plan

## Test Scenarios
```
