---
name: goal-convergence
description: "Goal-oriented autonomous loop with external completion oracle. Keeps iterating until verifiable stopping conditions are met, checked by a separate model."
origin: ECC
---

# Goal Convergence

Goal-oriented autonomous loop with external completion oracle.
Based on Addy Osmani's Loop Engineering principle: "Keep going until a verifiable
stopping condition holds, with a separate small model checking completion."

## When to Activate

- User invokes `/goal` command
- Heartbeat auto-creates a goal from scan failures
- Triage item is promoted to a goal via `/triage act <id> goal`
- Session resumes with an active goal state file

## Core Concept: Maker-Oracle Separation

The model that wrote the code is too nice grading its own homework.
A second model (the oracle) with different instructions and READ-ONLY tools
catches what the first talked itself into.

```
Maker (primary model, full tools)
  │
  ▼ produces iteration output
  │
Oracle (different model, read-only)
  │
  ├─ ALL conditions pass → CONVERGE (goal done)
  ├─ Some fail + budget remains → nextHint → LOOP (maker iterates)
  └─ Budget exhausted → ESCALATE (triage inbox)
```

## Goal Lifecycle

```
CREATE → ACTIVE → [iterate] → CONVERGED
                       │
                       ├──── PAUSED (manual /goal pause)
                       └──── ESCALATED (budget exhausted or repeated failure)
```

States:
- `active`: Maker-oracle loop is running
- `paused`: Manually paused, resumes with `/goal resume`
- `converged`: All stopping conditions met, goal complete
- `escalated`: Cannot converge within budget, needs human triage
- `failed`: Explicitly abandoned

## Stopping Conditions

Each goal has one or more stopping conditions. ALL must pass for convergence.

| Type | Command Pattern | Example |
|------|----------------|---------|
| `test_pass` | Test runner exits 0 | `npm test` |
| `lint_clean` | Linter exits 0 | `npm run lint -- --quiet` |
| `coverage_threshold` | Coverage >= N% | `npm test -- --coverage` |
| `build_pass` | Build succeeds | `npm run build` |
| `custom_command` | Any command exits 0 | `grep -r "TODO" src/ \| wc -l` |

## Oracle Protocol

The oracle receives:
1. The goal objective (natural language)
2. All stopping condition commands and their latest output
3. The maker's iteration summary
4. Previous iteration history (last 3)

The oracle returns:
```json
{
  "converged": false,
  "conditionResults": [
    {"type": "test_pass", "passed": false, "output": "2 tests failing"},
    {"type": "lint_clean", "passed": true, "output": ""}
  ],
  "reasons": ["2 tests still failing in auth module"],
  "nextHint": "Focus on src/auth/refresh.test.ts — the token expiry mock is stale",
  "confidence": 0.85
}
```

## Budget Management

Three budget dimensions, any exhaustion triggers escalation:

| Dimension | Default | Rationale |
|-----------|---------|-----------|
| Iterations | 15 | Prevents infinite loops |
| Wall time | 2h | Bounds real-world duration |
| Cost (USD) | $10 | Prevents runaway API spend |

On escalation, the goal:
1. Persists full state to `~/.claude/goals/{goalId}.json`
2. Creates a triage inbox item with context
3. Marks state as `escalated`
4. Reports final status to user

## Inter-Session Persistence

Goals survive session restarts:
1. `SessionEnd` hook serializes active goals
2. `SessionStart` hook detects active goals and notifies user
3. `/goal resume` re-enters the loop with oracle's last `nextHint`

State file: `~/.claude/goals/{goalId}.json` (follows `schemas/goal.schema.json`)

## Integration Points

- **`/heartbeat`**: Auto-creates goals from scan failures
- **`/triage`**: Escalated goals land in triage; triage items can become goals
- **`/checkpoint`**: Each iteration implicitly checkpoints
- **`/verify`**: Oracle internally uses verification patterns
- **`wave-execution`**: Multiple goals can run in parallel waves
- **`rework-loop`**: Failed iterations trigger blame-attributed rework

## Hard Bans

- Oracle MUST be a different model than maker (eliminates self-grading bias)
- Oracle MUST NOT have write tools (prevents it from "helping" fix issues)
- Goals MUST have at least one stopping condition (no open-ended loops)
- Budget MUST have at least one limit set (no unbounded execution)
- State MUST persist to disk (no goals lost on crash)

## Example

```
User: /goal "make all tests pass"

System infers:
  objective: "make all tests pass"
  stoppingConditions: [{type: "test_pass", command: "npm test"}]
  budget: {maxIterations: 15, maxDuration: "2h", maxDollars: 10}
  oracle: {model: "haiku"}

Iteration 1:
  Maker: reads test output, fixes obvious import error in auth.ts
  Oracle: runs `npm test` → 1 test still failing → {converged: false, nextHint: "..."}

Iteration 2:
  Maker: fixes token refresh logic based on oracle hint
  Oracle: runs `npm test` → all pass → {converged: true}

Result: CONVERGED in 2 iterations, $0.45 spent
```
