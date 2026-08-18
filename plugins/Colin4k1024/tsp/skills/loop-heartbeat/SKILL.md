---
name: loop-heartbeat
description: "Scheduled discovery automation that runs scans on a heartbeat interval, classifies findings, and routes them to goals or triage inbox."
origin: ECC
---

# Loop Heartbeat

Scheduled discovery automation that runs scans, finds issues, and routes findings
to goals or triage. The heartbeat is what makes a loop a loop — not a one-shot run.

Based on Addy Osmani's Loop Engineering: "Automations are the thing that makes
a loop an actual loop. Run prompts on a schedule. Findings go to a triage inbox;
empty runs archive themselves."

## When to Activate

- User invokes `/heartbeat start` to begin scheduled scans
- User invokes `/heartbeat run` for a one-shot scan
- A goal converges and follow-up scanning is needed
- Project onboarding includes quality monitoring setup

## Core Concept

The heartbeat is the "discovery layer" of a loop. It answers: "What's broken right
now?" on a recurring basis without human prompting.

```
Every 30 minutes:
  ┌─ Run test suite ─── PASS → skip
  ├─ Run linter ─────── FAIL → create goal (auto-fix)
  ├─ Audit deps ─────── FAIL → triage inbox (human decision)
  └─ Type check ─────── PASS → skip
```

## Configuration

Create `.claude/heartbeat.yaml` in the project root:

```yaml
heartbeat:
  interval: "30m"
  scans:
    - name: "test-health"
      command: "npm test 2>&1 | tail -10"
      onFailure: "auto-goal"
      description: "Test suite health"
    - name: "lint-drift"
      command: "npm run lint -- --quiet 2>&1 | wc -l"
      threshold: 0
      onFailure: "triage"
      description: "Lint error count"
    - name: "type-check"
      command: "npx tsc --noEmit 2>&1; echo EXIT:$?"
      onFailure: "auto-goal"
      description: "TypeScript type errors"
  budget:
    maxDollarsPerHour: 2.0
    pauseOnExhaust: true
```

## Scan Result Classification

| onFailure | Behavior | Use When |
|-----------|----------|----------|
| `auto-goal` | Creates `/goal` automatically | Machine can fix it (tests, lint, types) |
| `triage` | Adds to `/triage` inbox | Human judgment needed (deps, security) |
| `notify` | Desktop notification only | Informational, no action required |
| `ignore` | Log silently | Monitoring only, aggregate later |

## Budget Controls

- `maxDollarsPerHour`: Pause heartbeat if scanning costs exceed this
- `pauseOnExhaust`: If true, pause (resumable); if false, stop entirely
- Goal creation inherits the default goal budget from `/goal` settings

## Empty Run Handling

When all scans pass:
- No goals or triage items are created
- Run is logged to `~/.claude/heartbeat-last-run.json`
- Next run proceeds on schedule
- This is the "archive themselves silently" behavior

## Integration Points

- **`/goal`**: `auto-goal` failures create goals via completion-oracle.js
- **`/triage`**: `triage` failures append to `~/.claude/triage/inbox.jsonl`
- **CronCreate**: Scheduling uses the Claude Code CronCreate primitive
- **ScheduleWakeup**: Alternative for dynamic-interval loops
- **Hooks**: Runs as a scheduled task, not a synchronous hook

## Hard Bans

- Heartbeat MUST NOT modify code (it's discovery-only)
- Heartbeat MUST NOT create goals without a stopping condition
- Budget limits MUST be enforced (no unbounded scan spending)
- Failed scans MUST be classified (no silent failures)
- Empty runs MUST NOT create noise (pass = skip)

## Example Session

```
User: /heartbeat start

System:
  Loaded .claude/heartbeat.yaml (3 scans configured)
  Registered CronCreate: every 30m
  Next run: 30m from now
  Budget: $2.00/hour

[30 minutes later, heartbeat fires]

Scan results:
  ✓ test-health: all tests pass
  ✗ lint-drift: 4 lint errors found → created goal-a1b2c3d4
  ✓ type-check: no type errors

Summary: 2/3 scans passed, 1 goal created
```
