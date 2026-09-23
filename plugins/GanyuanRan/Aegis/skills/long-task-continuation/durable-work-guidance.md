# Durable Work Guidance

This reference preserves conditional durable-record detail. It does not own routing, inline-versus-durable selection, slice boundaries, drift decisions,
implementation authorization, or completion. Load it only through a trigger in
`SKILL.md` and use only the sections needed by the current lifecycle event.

## Contents

1. [Required Artifact Layout](#required-artifact-layout)
2. [Create A Durable Work Record](#create-a-durable-work-record)
3. [Update A Slice](#update-a-slice)
4. [Retry Convergence Detail](#retry-convergence-detail)
5. [Pause, Handoff, And Completion Bundle](#pause-handoff-and-completion-bundle)
6. [Expanded State Fields](#expanded-state-fields)

## Required Artifact Layout

Use one directory: `docs/aegis/work/YYYY-MM-DD-<slug>/`.

| Artifact view | File | Lifecycle point |
|---|---|---|
| TaskIntentDraft, BaselineReadSetHint, BaselineUsageDraft, ImpactStatementDraft | `10-intent.md`; optional `task-intent-draft.json`, `baseline-usage-draft.json` | workstream start or material baseline change |
| TodoCheckpointDraft, ResumeStateHint, DriftCheckDraft | `20-checkpoint.md`; optional `todo-checkpoint-draft.json`, `resume-state-hint.json`, `drift-check-draft.json` | checkpoint, pause, or handoff |
| EvidenceBundleDraft | `90-evidence.md`; optional `evidence-bundle-draft.json` | terminal slice evidence only |
| Reflection | `99-reflection.md` | completion candidate when reflection is useful |

Do not create every optional JSON file manually. Prefer the configured helper's
normal lifecycle and do not invent a parallel artifact family.

## Create A Durable Work Record

Initialize the external target project only when project authority permits it:

```bash
python <aegis-workspace-helper> init --root <target-project-root>
```

Create and index one workstream:

```bash
python <aegis-workspace-helper> new-work --root <target-project-root> --date YYYY-MM-DD --slug <slug> --title "<title>" --requested-outcome "<outcome>" --scope "<scope>" --change-kind <kind>
```

Populate intent from approved sources: outcome, scope/non-goals, parent plan or
goal, baseline refs/usage, compatibility and retirement boundaries, todo map,
branch/HEAD, and any execution-readiness locks. Do not copy full plans, raw
logs, or large diffs into the record.

## Update A Slice

For an existing helper-backed work record, update only the affected views:

```bash
python <aegis-workspace-helper> add-checkpoint --root <target-project-root> --work YYYY-MM-DD-<slug> ...
python <aegis-workspace-helper> add-baseline-usage --root <target-project-root> --work YYYY-MM-DD-<slug> ...
python <aegis-workspace-helper> add-evidence --root <target-project-root> --work YYYY-MM-DD-<slug> --slice-id <slice-id> --evidence-status <terminal-status> ...
python <aegis-workspace-helper> add-drift-check --root <target-project-root> --work YYYY-MM-DD-<slug> ...
```

Checkpoint state names current todo, completed todos, active slice, evidence
refs, blockers, next step, and resume order. Evidence stores bounded refs and
outcomes, not repeated raw output. Drift stores the advisory decision and its
falsifier.

## Retry Convergence Detail

Record a failed verification retry inside the current slice:

```bash
python <aegis-workspace-helper> add-attempt --root <target-project-root> --work YYYY-MM-DD-<slug> --slice-id <slice-id> --attempt-id <attempt-id> --attempt-status failed ...
```

Do not use `add-evidence` until the slice reaches `evidence-finalized`,
`blocked`, or `abandoned`. A failed attempt does not create another slice,
formal evidence sidecar, or process-only commit. A process-only diff under
`docs/aegis/` does not restart already completed business-code verification.

At `process-artifact-pressure`, stop automatic retry. Preserve only the bounded
direction state needed to avoid a repeated misfix: `PatchShape`,
`CanonicalOwner`, `UpwardDrillSignal`, decision, latest outcome, and one bounded
evidence ref. Route diagnosis or proof to the owning workflow.

## Pause, Handoff, And Completion Bundle

Before pause, handoff, or a completion candidate, assemble the structural
bundle and validate workspace shape:

```bash
python <aegis-workspace-helper> bundle --root <target-project-root> --work YYYY-MM-DD-<slug>
python <aegis-workspace-helper> check --root <target-project-root>
```

These commands validate structure, index coverage, and JSON sidecar shape only.
They do not decide evidence sufficiency, produce authoritative `GateDecision`,
or grant completion. A `GateInputPack` remains future-runtime input.

For durable architecture work, retain the record, proof bundle, drift checks,
evidence refs, alternatives, compatibility/retirement notes, baseline-sync
questions, and ADR signals for completion-time ADR Backfill Check.

## Expanded State Fields

Use these only when natural checkpoint prose would be ambiguous:

- `TaskIntentDraft`: outcome, scope, non-goals, risk, parent authority, success
  evidence, and stop states.
- `BaselineUsageDraft`: required, acknowledged, cited, and missing refs plus an
  advisory decision.
- `TodoCheckpointDraft`: current todo, completed todos, active slice, blockers,
  evidence refs, and `nextStep`.
- `ResumeStateHint`: exact read order, `mustReadBeforeContinuing`, branch/HEAD,
  worktree comparison, and first authorized action.
- `DriftCheckDraft`: intent, scope/acceptance, compatibility, new-surface,
  retirement, evidence, readiness-lock checks, falsifier, and allowed decision.
- `EvidenceBundleDraft`: terminal status, bounded command/file/log/manual refs,
  covered scope, uncovered scope, and residual risk.

Optional sidecars are projections of these semantic views, not independent
owners. Keep task IDs consistent across sidecars and reuse the same active slice
for retries.
