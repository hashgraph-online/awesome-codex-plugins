# Caveman-internal Budget Thresholds

Session budget is the cumulative token count across all iterations of a
Cavekit loop. Read it from `.cavekit/token-ledger.json` (`session_used` /
`session_budget`). Per-task budget lives in the same ledger under
`tasks.<id>.used` / `tasks.<id>.budget`.

## Decision table

| Session pressure | Task pressure | Task depth | Chosen intensity |
|------------------|---------------|------------|------------------|
| < 50 %           | < 50 %        | any        | lite             |
| < 50 %           | ≥ 50 %        | any        | full             |
| 50 – 80 %        | < 80 %        | quick      | full             |
| 50 – 80 %        | < 80 %        | standard   | full             |
| 50 – 80 %        | < 80 %        | thorough   | lite             |
| 50 – 80 %        | ≥ 80 %        | any        | ultra            |
| ≥ 80 %           | any           | thorough   | lite (clamped)   |
| ≥ 80 %           | any           | other      | ultra            |

## Clamping rules

- `depth = thorough` and `phase = inspecting` clamp to **lite** regardless of
  pressure. Accuracy dominates cost.
- Security-sensitive artifacts (auth, secrets, permissions, crypto) clamp to
  **lite**.
- If three consecutive fallbacks hit, clamp the affected category to **lite**
  for the rest of the session.

## Artifact-category overrides

| Category                 | Baseline |
|--------------------------|----------|
| handoff-memo             | full     |
| context-bundle           | full     |
| artifact-summary         | full     |
| review-notes (non-user)  | lite     |
| status-block (dashboard) | lite     |
| loop-log entry           | ultra    |
| state.md notes           | full     |

Baselines apply when pressure is low. When pressure rises, escalate in
ultra direction by one step.
