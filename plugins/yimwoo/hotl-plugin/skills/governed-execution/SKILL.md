---
name: governed-execution
description: Use when executing an accepted HOTL workflow through the best available host or fallback driver.
---

# HOTL Governed Execution

This is the preferred execution entry point for new HOTL runs. It selects a host driver and an execution profile while preserving the canonical state machine in `loop-execution`.

## Required behavior

1. Resolve and lint the workflow using `loop-execution` rules.
2. Select the profile from user intent: `loop` for autonomous sequential work, `manual` for explicit checkpoints, or `delegated` for eligible independent steps. Never select delegated execution when the user prohibited subagents.
3. Locate the router in the active HOTL installation, then run `runtime/drivers/route.sh preflight <workflow>` before initialization. Supported roots include the current repository, `~/.codex/hotl`, `~/.codex/plugins/hotl-source`, the active Codex plugin cache, the Claude plugin root, and `~/.cline/hotl`. Use `--host` only when the user or trusted host context identifies one.
4. If preflight resolves fallback, follow the chosen existing execution skill with the generic driver. If it resolves native, obtain `envelope` and use only supported native features; the host sandbox and approvals remain authoritative.
5. Persist every step, verification, gate, action decision, budget observation, finalize, and finish transition through the selected driver. Host UI or chat text is never state.
6. Before claiming success, require `receipt <run-id>` to return `sufficiency.sufficient: true`. If interrupted, run `reconcile <run-id>` and follow `resuming` verify-first behavior.

## Compatibility profiles

- `loop-execution`: canonical autonomous state machine and reporting contract.
- `executing-plans`: explicit human checkpoints.
- `subagent-execution`: delegated workers; controller retains gates and verification.
- `resuming`: interrupted-run recovery.
- `finishing-a-development-branch`: explicit finish disposition.

These names remain supported. Do not rewrite an accepted workflow merely to use this router.

## Safety invariants

- Native mode is opt-in; executable presence alone does not prove capability.
- `external_write`, `production_change`, and `secret_access` require `hotl-rt action` human approval before the host performs them.
- Unknown budget telemetry stays unknown.
- Never auto-write project memory. `scripts/hotl-memory-proposal.sh` only creates a proposal for human review.
