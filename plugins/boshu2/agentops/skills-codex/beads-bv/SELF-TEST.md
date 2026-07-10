# Self-Test: beads-bv

## Purpose

Validate that `bv` robot mode works and returns machine-readable JSON.

## Quick Validation

Run these from a project that has a `.beads/` workspace (any repo using br/bd):

```bash
which bv

# Robot help exists (no TUI)
bv --robot-help >/dev/null

# Core robot commands return JSON
bv --robot-plan | jq -e '.plan.tracks | type == "array"' >/dev/null
bv --robot-priority | jq -e '.recommendations | type == "array"' >/dev/null
bv --robot-triage | jq -e '.recommendations | type == "array"' >/dev/null
bv --robot-next | jq -e '.id and .claim_command' >/dev/null
```

