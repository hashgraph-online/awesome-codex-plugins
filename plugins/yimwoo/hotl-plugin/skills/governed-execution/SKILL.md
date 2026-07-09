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
4. If preflight resolves fallback, follow the chosen existing execution skill with the generic driver. If it resolves native, obtain `envelope` and use only supported native features; the host sandbox and approvals remain authoritative. Native goals, automations, background sessions, handoffs, and hooks provide scheduling and liveness only. They never replace HOTL ownership, verification, state, or receipts. Preview and experimental continuation features remain explicit opt-ins.
5. Launch new driver-managed runs with `--require-owner`. Immediately run `owner claim --owner <stable-controller-id> --lease-seconds <bounded-lease> --run-id <run-id>`, retain the returned token only in the controller, export it as `HOTL_OWNER_TOKEN`, and run `owner heartbeat` before and after long actions and at safe transition boundaries. Every later mutation must carry that token. Use explicit `owner handoff`, `owner release`, or reviewed `owner takeover`; never infer ownership from age alone.
6. Persist every step, verification, gate, action decision, effect outcome, budget observation, finalize, and finish transition through the selected driver. Host UI or chat text is never state.
7. Before claiming success, require `receipt <run-id>` to return `sufficiency.sufficient: true`. A successful `finalize` only moves the run to `ready_to_finish`; `finish` records the explicit disposition and moves it to `completed`. If interrupted, run `reconcile <run-id>` and follow `resuming` verify-first behavior.

## Long-running controller contract

- The controller, not the host session UI or a delegated worker, owns `HOTL_OWNER_TOKEN`, gates, verification, budgets, and stop conditions.
- Before a sensitive external effect, run `action request` with a stable idempotency key, obtain the required human `action decide`, and then persist `action begin` before performing the effect. Persist the observed result with `action complete`; after an interrupted or uncertain result, inspect the target and use `action reconcile` instead of replaying it.
- Treat `in_progress` or `uncertain` effect state as a reconciliation stop. Approval authorizes one bounded attempt; it is not evidence that the effect succeeded.
- Keep the lease renewable during long work. If the controller cannot heartbeat safely, stop at a durable boundary and hand off or release ownership.

## Compatibility profiles

- `loop-execution`: canonical autonomous state machine and reporting contract.
- `executing-plans`: explicit human checkpoints.
- `subagent-execution`: delegated workers; controller retains gates and verification.
- `resuming`: interrupted-run recovery.
- `finishing-a-development-branch`: explicit finish disposition.

These names remain supported. Do not rewrite an accepted workflow merely to use this router.

## Safety invariants

- Native mode is opt-in; executable presence alone does not prove capability.
- `external_write`, `production_change`, and `secret_access` require the `action request` → human `action decide` → `action begin` → effect → `action complete` lifecycle. Interrupted effects use `action reconcile`, never blind replay.
- Unknown budget telemetry stays unknown.
- Never auto-write project memory. `scripts/hotl-memory-proposal.sh` only creates a proposal for human review.
