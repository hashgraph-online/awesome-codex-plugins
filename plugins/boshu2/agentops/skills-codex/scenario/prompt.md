Author and manage holdout scenarios for Stage 4 behavioral validation.

Scenarios are stored in `.agents/holdout/` where implementing agents cannot see them (enforced by holdout-isolation-gate hook). Evaluator agents validate code against scenarios during STEP 1.8 in `$validate`.

## Commands

```bash
ao scenario init      # Create .agents/holdout/ directory
ao scenario list      # List active scenarios
ao scenario validate  # Validate schema compliance
```

## Key Rules

- Scenarios use satisfaction scoring (0.0-1.0), not boolean pass/fail
- Never author scenarios as the implementing agent — only humans or evaluator agents
- Agent-built specs from `$implement` Step 5c use `auto-*` id prefix in `.agents/specs/`
