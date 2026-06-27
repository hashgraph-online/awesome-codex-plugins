---
name: orchestrate
description: Out-of-session orchestration instrument
---
# Orchestrate — Out-of-Session Instrument Lane

When work escalates **outside** the in-session loop, start with deterministic
instruments — not a parallel spawn manual.

## Procedure

1. **Route** — `ao orchestrate route --json` (or `--writers N --models opus,codex,agy`)
2. **Preflight** — `ao orchestrate preflight --profile <name> --json`
3. **Spawn** — follow the profile in `docs/contracts/orchestration-profiles.yaml` using raw `atm` (human procedure; see `using-atm` / `dual-pane-atm`)
4. **Verify** — `ao orchestrate verify --session <name> --profile <name> --json`

Profiles contract is SOT; skills are drift-gated procedure, not CLI replacements.

## Commands

| Command | Role |
|---------|------|
| `ao orchestrate route` | Posture → profile recommendation |
| `ao orchestrate preflight` | Admission gate before spawn |
| `ao orchestrate verify` | Post-spawn windshield |
| `ao orchestrate tools` | Tool matrix probe |
| `ao orchestrate status` | Active ATM sessions |
| `ao orchestrate shape` | Stamp execution-packet shape |
| `ao orchestrate select` | Backend ladder (existing) |

## Non-goals

- Does not replace `atm spawn` in Phase 1 (earn-it wrappers deferred)
- Does not mandate orchestrate via hook on day one

## References

- Acceptance: `references/orchestrate.feature`
- Contract: `docs/contracts/orchestration-profiles.yaml`
- Playbook: `skills/dual-pane-atm/`
- Substrate: `skills/using-atm/`
