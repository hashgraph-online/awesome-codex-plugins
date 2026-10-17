# Controller Loop Contract

## Purpose

The Clean Room controller uses nested loops.

The outer loop evolves specs. The inner clean-room loop completes one approved spec slice from sanitized handoff through implementation, QC, optional final clean polish review, and contaminated-side coverage verification, then returns a terminal result to the outer loop.

## Outer Loop: Spec Development

The outer loop owns product intent and spec state:

- Define or refine source scope.
- Create and approve the foundation unit first for code-development runs. Do not approve behavior units until the foundation unit is covered.
- Draft and review behavior specs.
- Select one approved spec slice.
- Invoke the inner clean-room loop.
- Consume the inner loop terminal result.
- Apply abstract delta tickets back to spec artifacts.
- Mark the slice complete or select the next slice.

Outer loop states:

- `SPEC_DISCOVERY`
- `SPEC_DRAFT`
- `SPEC_REVIEW`
- `SPEC_SLICE_READY`
- `CLEAN_ROOM_RUNNING`
- `CLEAN_ROOM_RETURNED`
- `SPEC_DELTA_APPLY`
- `SPEC_COMPLETE`

Only the outer loop may expand scope, alter acceptance criteria, change user stories, update OpenSpec/Kiro/Spec Kit/GSD artifacts, or decide that a blocked clean-room result needs a spec update.

## Inner Loop: Clean Room

The inner loop owns one approved spec slice:

- Reload durable artifacts each iteration.
- Validate the trust boundary and schemas.
- Refresh contaminated-side controller status when needed.
- Select at most one pending or gap unit inside the approved slice.
- Create one low-context role session brief for each role launch when context management is enabled.
- Run contaminated analysis.
- Run source-denied handoff sanitization.
- Run clean planning.
- Run clean implementation and QC.
- Run final clean polish review when configured.
- Run contaminated-side coverage verification.
- Return only a terminal clean-room result.

Inner loop states:

- `LOAD_ARTIFACTS`
- `VALIDATE_BOUNDARY`
- `SELECT_UNIT`
- `CONTAMINATED_ANALYSIS`
- `SANITIZE_HANDOFF`
- `CLEAN_PLAN`
- `CLEAN_IMPLEMENT`
- `CLEAN_QC`
- `CLEAN_POLISH_REVIEW`
- `CONTAMINATED_COVERAGE_VERIFY`
- `RETURN_TERMINAL_RESULT`

The inner loop must not expand scope. If it finds missing behavior, ambiguity, parity gaps, test gaps, or a plan that exceeds the selected slice, it emits abstract delta tickets and returns to the outer loop.

Unresolved high-priority `coverage-ledger.json` `discovery_leads` are treated as incomplete contaminated discovery, not clean implementation work. The inner loop may not mark the affected unit covered or send it to handoff until the lead is resolved by an authorized follow-up unit or the outer loop changes scope.

## Return Contract

The inner loop returns only after Agent 0 has consumed the terminal Agent 3 report, any configured Agent 4 `polish-report.json`, and verified coverage from the contaminated side. An Agent 3 terminal `implementation-report.json` alone is not a clean-room return.

Valid return results:

- `spec-slice-complete`
- `spec-slice-blocked`
- `spec-delta-required`
- `contamination-suspected`
- `iteration-limit-reached`
- `no-progress-detected`

The return artifact is `clean-room-result.json`. It contains the result, selected spec slice ref, coverage state, terminal implementation report ref, QC report ref, optional polish report ref, abstract delta tickets, and return timestamp. It must not contain source excerpts, raw diffs, source paths, private identifiers, or source-shaped pseudocode.

## Progress Contract

A controller iteration may advance only when at least one expected durable artifact changes and validates. Chat output alone is never progress.

Expected durable artifacts include:

- `coverage-ledger.json`
- `evidence-ledger.json`
- `handoff-package.json`
- behavior specs
- `implementation-plan.json`
- `implementation-report.json`
- `qc-report.json`
- `polish-report.json`
- abstract delta ticket artifacts
- `clean-room-result.json`

The runner records controller state in contaminated-side `controller-run-ledger.json`. That ledger is controller memory, not clean input.

`controller-status.json` is compact Agent 0 resume state, not workflow progress by itself. Status-only updates must not keep an unattended loop alive. `role-session-brief.json` is the launch packet for one fresh role context; it should contain refs and hashes, not copied artifact contents.

`coverage-ledger.json` `discovery_leads` are contaminated-only coverage metadata. They may name neutral source or visual refs for Agent 0 tracking, but clean roles receive only abstract deltas or sanitized behavior specs.

## Unit Sizing

Each unit must fit one fresh role session for the selected spec slice. Split a unit when it requires broad refactoring, multiple subsystems, multiple verification domains, or more than one fresh clean implementation context.

In unattended mode, `max_units_per_iteration` is always `1`. Agent 3 may execute only work items for the selected spec slice and current unit.
