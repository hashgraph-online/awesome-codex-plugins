---
name: refocus
description: Audits an existing Clean Room run and steers it back to missed gates without expanding declared scope.
argument-hint: [existing task-manifest.json or artifact roots]
disable-model-invocation: true
---

# Clean Room Refocus

Refocus realigns the current run to the declared scope, controller policy, artifact schemas, and clean-room boundary.

Refocus does not optimize, expand, or reinterpret the task. It does not invent new requirements or add behavior beyond `preflight-goal.json`, `task-manifest.json`, `clean-run-context.json`, ledgers, implementation plan/report, QC, and abstract delta tickets.

Use the canonical `clean-room` skill workflow and references in this plugin. Preserve the same clean-room boundary, role separation, artifact schemas, leakage rules, implementation-root rules, and hook expectations.

## Audit

Compare current artifacts to the canonical gate checklist:

- Scope gate recorded authorization, roots, boundaries, prohibited actions, evidence handling, selected target profile, Agent 0-4 pipeline, and Agent 1.5 sanitizer role for new runs.
- Preflight goal exists for new runs, validates against `preflight-goal.schema.json`, and is referenced by `task-manifest.json` with `preflight_goal_ref` and `preflight_goal_sha256`.
- Task manifest records the required `handoff_sequence` and does not skip Stage 0.
- Initialization snapshot exists when init preferences were used, and reusable `init-config.json` drift is reported instead of silently applied.
- `clean-run-context.json` exists before clean roles run and excludes source roots, visual roots, contaminated roots, source index refs, visual index refs, and ledger paths.
- `clean-run-context.json` records artifact-only coordination: Agent 0 does not directly steer Agent 2, Agent 3, or Agent 4, and clean implementation/polish roles report to Agent 0 only at terminal status.
- When context management is enabled, the next role launch can be driven by a fresh `role-session-brief.json` inside the recorded budgets. `controller-status.json` remains contaminated-side only.
- Implementation roots are recorded, separated, and not source-derived.
- Source index or visual-index fallback preflight exists when required and remains contaminated-only.
- Decomposition produced neutral `task-manifest.json` units.
- Contaminated analysis wrote draft behavior specs without implementation code.
- Agent 1.5 sanitization ran before handoff, or older artifacts clearly predate the Agent 1.5 gate and require review before reuse.
- Handoff package excludes full `task-manifest.json`, `source-index.json`, `visual-index.json`, raw screenshots, source or visual paths, raw diffs, copied comments, copied visible words, private identifiers, exact UI palettes/layouts/iconography, source-shaped pseudocode, and contaminated ledgers.
- Agent 2 produced clean-only `implementation-plan.json` when the run reached that gate.
- Agent 3 produced `implementation-report.json` when the run reached implementation.
- Non-terminal Agent 3 implementation reports were not used as Agent 0 feedback or guidance.
- QC produced `qc-report.json` with schema, leakage, coverage, and abstract delta ticket status when the run reached that gate.
- Agent 4 produced `polish-report.json` when the run reached final polish review.
- Contaminated verification returned only abstract delta tickets.

Validate schemas and handoff hashes before trusting the artifacts. Use `source-index.json` or `visual-index.json` only on the contaminated side and only when referenced by the task manifest.

## Findings

Emit missed-gate findings only:

- Missing required artifact.
- Invalid schema.
- Failed or missing leakage review.
- Invalid or stale handoff hash.
- Boundary violation or unproven root separation.
- Stale handoff compared with latest QC or ledger state.
- Stale implementation plan compared with latest clean handoff.
- Stale implementation report compared with latest implementation plan.
- Controller policy not preserved.
- Missing, invalid, or drifted preflight goal.
- Noncanonical manifests, reports, ledgers, or manual result summaries used as completion evidence. Mark these `not verified` unless `clean-room-skill run --dry-run` (or `npx clean-room-skill@latest run --dry-run` if the binary is not available) succeeds against the canonical `task-manifest.json`.
- Missing public-surface inventory parity: required public commands, APIs, config keys, protocol entries, or user-visible behaviors listed in approved specs are not mapped through behavior spec tests, implementation-plan `public_contract_refs`, terminal implementation reports, and coverage-ledger `public_surface_coverage`.

Do not suggest speculative improvements. Do not change source scope, target profile, public API, or implementation plan.
If the user asks to add scope, stop and route to a new scope gate instead of silently expanding the run.

## Output

Return a bounded next-action plan containing:

- Current verified gate.
- Missed gate findings.
- One to three process corrections, ordered by safety.
- The single next action the controller should take.

If root separation, authorization, or clean/contaminated boundary cannot be proven, the single next action is to stop and repair that gate.
