---
name: scenario
description: "Run scenario."
---
# Scenario Skill

Author and manage holdout scenarios for Stage 4 behavioral validation.

Scenarios are **holdout** — implementing agents cannot see them (enforced by hook).
Evaluator agents validate code against scenarios during STEP 1.8 in `$validate`.

## Execution Steps

### Step 1: Initialize

```bash
ao scenario init   # Creates .agents/holdout/ with README
```

### Step 2: Author Scenario

Write a scenario JSON to `.agents/holdout/<id>.json` following `schemas/scenario.v1.schema.json`:

```json
{
    "id": "s-2026-04-05-001",
    "version": 1,
    "date": "2026-04-05",
    "goal": "User can authenticate with valid credentials",
    "narrative": "A user visits login, enters valid credentials, expects dashboard redirect.",
    "expected_outcome": "Dashboard loads, session cookie is HttpOnly and Secure.",
    "acceptance_vectors": [
        {"dimension": "correctness", "threshold": 0.9, "check": "grep -q 'HttpOnly' headers"},
        {"dimension": "performance", "threshold": 0.7}
    ],
    "satisfaction_threshold": 0.8,
    "scope": {
        "files": ["src/auth/middleware.go"],
        "functions": ["Authenticate"],
        "behaviors": ["login flow"]
    },
    "source": "human",
    "status": "active"
}
```

### Step 3: Validate

```bash
ao scenario validate   # Checks all scenarios against schema
```

### Step 4: List

```bash
ao scenario list                  # All scenarios
ao scenario list --status active  # Active only
```

## Key Rules

- Scenarios use **satisfaction scoring** (0.0-1.0), not boolean pass/fail
- Scenarios should be written by humans or evaluator agents, NEVER by the implementing agent
- `source` field tracks provenance: `human`, `agent`, `prod-telemetry`
- Agent-built specs (from `$implement` Step 5c) use `auto-*` id prefix and live in `.agents/specs/`

## See Also

- `$validate` — STEP 1.8 consumes scenarios
- `$vibe` — Exposes satisfaction_score
- `$implement` — Step 5c generates agent-built specs
