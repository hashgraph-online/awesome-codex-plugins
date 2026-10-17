# Tuning Pass Workflow

## Procedure

1. Name the loop being tuned.
2. Define the intended player behavior.
3. Extract all numerical parameters into a table.
4. Mark each parameter as `feel`, `fairness`, `difficulty`, `economy`, `progression`, or `accessibility`.
5. Calculate obvious expected values for random rewards, combat outcomes, risk-reward offers, or loot tables.
6. Identify edge cases:
   - minimum skill player
   - high skill player
   - unlucky player
   - optimized player
   - player who misunderstands the system
7. Propose conservative changes first.
8. Specify telemetry that proves whether the change worked.

## Output Template

```markdown
## Balance Intent

## Economy Map

## Tuning Table
| Parameter | Current | Proposed | Safe Range | Purpose | Telemetry |

## Expected Value Checks

## Dominant Strategy Review

## Accessibility Options

## Playtest Plan
```
