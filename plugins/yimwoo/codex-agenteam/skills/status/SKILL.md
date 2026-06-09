---
name: status
description: Show the current state of a run — stages, roles, write locks, and gates.
---

# AgenTeam Status

Display the current state of the team's work.

## Process

### 1. Get Status

Use the `--progress` flag for a compact, human-friendly view:

```bash
python3 <runtime>/agenteam_rt.py status --progress
```

If the user specifically asks for raw JSON state, use without `--progress`:
```bash
python3 <runtime>/agenteam_rt.py status
```

### 2. Format Output

Display the progress view in a readable format:

```
AgenTeam Run: <run-id>
Task: <task description>
Profile: <profile or "full">
Status: <running|completed|failed|stopped>
Elapsed: <Nm Ss>

Stages:
  research   ✓ completed  (0m 45s)
  strategy   ✓ completed  (0m 30s)
  design     ✓ completed  (1m 02s)
  implement  → verifying   (1m 15s)  [verify attempt 2/3]
  test       · pending
  review     · pending

Active Lock: dev
Last Event: stage_verified (implement) — fail, attempt 2
```

The progress view includes elapsed times per stage, the current
verify attempt if applicable, and the most recent event for context.
When `governance.adoption` is present, include the high-signal governance
items in the readable status: open follow-ups/escalations, recorded tripwire
blocks or warnings, gate rejections, and criteria overrides. Do not ask the
user to inspect raw `.agenteam/governance` files for these summary facts.

### 3. No Active Run

If no run is found, show:
- Team config status (does `.agenteam/config.yaml` or legacy `agenteam.yaml` exist?)
- Available roles
- Suggestion: "Use `$ateam:run` to start a new task."

## Symbols

- `✓` — completed
- `→` — in progress
- `·` — pending
- `✗` — failed/blocked
