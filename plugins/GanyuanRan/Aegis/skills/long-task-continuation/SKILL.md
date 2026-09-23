---
name: long-task-continuation
description: "Use when a task is multi-step, may span context resets or sessions, uses subagents, or risks losing state before completion."
---

# Long Task Continuation

## Overview

Keep long work checkpointed, resumable, drift-aware, and evidence-gated. This
protocol does not execute plans, dispatch subagents, run tests, or grant
completion authority.

## Authority Boundary

The Method Pack owns continuation discipline only. It does not own the parent
plan, host retry/watchdog behavior, authoritative `GateDecision`, evidence
sufficiency, requirement acceptance, or completion.

## When To Use

Use this skill when the work has meaningful phases, may be compacted/resumed or
handed off, uses subagents, or explicitly needs continuity and drift control.
Architecture, contract, shared-workflow, and verification-gate changes also
benefit from it. Do not force it onto a short answer or one-command check.

Choose exactly one state carrier:

- use a durable `work/` record for medium+ work that actually crosses sessions,
  needs handoff, or requires resumable state;
- otherwise keep one inline checkpoint.

Multi-step, todo-driven, possible-compaction, and subagent use do not force
durable records by themselves. Do not create both carriers or a record per
slice.

## Required Artifacts

A durable task has one process trail under
`docs/aegis/work/YYYY-MM-DD-<slug>/`. It keeps logical intent/baseline state,
the latest todo/checkpoint/resume state, terminal evidence/drift state, and a
completion reflection when warranted. These are
`TaskIntentDraft`, `BaselineReadSetHint`, `BaselineUsageDraft`,
`ImpactStatementDraft`, `TodoCheckpointDraft`, `ResumeStateHint`,
`DriftCheckDraft`, and `EvidenceBundleDraft` views—not authoritative runtime
records or separate plan owners.

Read only the lifecycle-matched section of `durable-work-guidance.md`:

- `## Required Artifact Layout` and `## Create A Durable Work Record` for a new durable work record;
- `## Update A Slice` when an existing helper-backed record needs sidecar updates;
- `## Retry Convergence Detail` for retry/attempt bookkeeping;
- `## Pause, Handoff, And Completion Bundle` when preparing a pause, handoff, or completion bundle; and
- `## Expanded State Fields` only when natural checkpoint prose is ambiguous.

The reference owns artifact layout and `<aegis-workspace-helper>` command
detail; this file owns carrier selection, resume order, drift decisions, and
stop conditions.

An `Execution Readiness View` may be kept in the intent or active checkpoint
for medium/high, handoff-prone, long-running, subagent-driven, architecture,
contract, compatibility, or retirement-sensitive work. It renders existing
intent, scope, baseline, owner, test, review, and drift constraints; it is not a
new JSON artifact or completion authority.

Planless Slice Lane:

- When an existing parent plan/spec owns a bounded task, reuse it and the
  current checkpoint. For a no-parent direct bounded request with no new
  durable or unclear verification boundary, use an inline checkpoint.
- State one compact `Slice Card`: Goal, `Parent plan/spec` (or
  `none — direct bounded request`), Files, Boundary, Verification, and Stop.
- The slice goal closes only that slice. Final completion returns to the parent
  or direct bounded request through `verification-before-completion`.
- Do not create a plan/spec merely to give a micro-slice a parent, and do not
  create per-slice plans/specs or work records.
- Escalate when a new owner, contract, schema, public API, architecture,
  migration, persistence, security/permission, distribution/release surface,
  unclear verification boundary, or mismatch with parent scope or acceptance
  appears.

When durable architecture decisions are in scope, these work records are the
preferred ADR Auto Backfill source. Preserve decision signals, source refs,
alternatives, compatibility, retirement, drift, and baseline-sync questions.

## Start Protocol

Before execution:

1. Capture requested outcome, scope, non-goals, risks, parent plan/goal, success
   evidence, and stop states (`done | blocked | needs-verification |
   scope-exceeded`).
2. Identify required baseline refs and record acknowledged, cited, and missing
   refs. Missing authority pauses in `needs-baseline-readback`.
3. Choose inline or durable state once, then record the todo map, active slice,
   completed slices/evidence, blockers, next step, and current branch/HEAD.
4. When an `Execution Readiness View` exists, retain its intent lock, scope
   fence, baseline lock, compatibility/retirement boundary, tests, reviews,
   evidence, and rewind rules.
5. For a new helper-backed record, use `durable-work-guidance.md` to create and
   structurally check it before implementation.

## Retry Convergence Protocol

A failed verification is another attempt in the current slice, not a new
slice. Keep failed-attempt telemetry out of terminal evidence and normal
commits. Only `evidence-finalized`, `blocked`, or `abandoned` is terminal.
When retry state reaches `process-artifact-pressure`, stop auto-retry and route
to `systematic-debugging` or `verification-before-completion`. Load the durable
reference only when the attempt/evidence commands or sidecar rules are needed.

## Per-Slice Protocol

Before each slice, state the current goal/todo, intended edits, explicit
non-edits, verification, and readiness alignment. A bounded parent-plan or
no-parent slice uses the compact Slice Card rather than a new plan/spec.

After each slice, update completed todos, evidence refs, newly used baseline
refs, blockers, next step, and drift decision. When an active helper-backed work record exists, read `durable-work-guidance.md` and update that same record;
never create another workstream for bookkeeping.

When patch-shape/ripple triage, an H-class finding, or a bounded compatibility
mitigation fired, a locally green result does not clear the direction. Retain
`PatchShape`, `CanonicalOwner`, `UpwardDrillSignal`, latest outcome, and one
bounded evidence ref; do not copy raw logs or full diffs. If no fresh evidence
exists, the state is `needs-verification` or `partial`.

## Resume Protocol

Resume in this order:

1. Read original intent, parent plan/goal, latest checkpoint and resume hint.
2. Re-read required baseline refs and relevant active `CONTEXT.md` language.
3. Read the `Execution Readiness View` when present.
4. Compare checkpoint branch/HEAD, completed commits, evidence refs, and claims
   with the current worktree.
5. Compare the active slice against intent lock, scope fence, baseline lock,
   compatibility/retirement boundary, tests, reviews, and non-goals.
6. Re-run the drift decision, then name the next smallest authorized action.

Any disagreement among plan, checkpoint, baseline, context, readiness view, or
worktree pauses execution. A semantic conflict routes to
`establishing-project-context`; an unplanned repair re-reads the retained
invariant, owner seam, patch shape, and causal topology, then route comparison to
`systematic-debugging`. A new carrier name alone does not prove a new direction. Never resume from memory alone.

## Drift Check

Check original intent and stop condition, parent scope/acceptance, compatibility,
new owners/fallbacks/adapters/branches, retirement, evidence freshness, and any
readiness locks. Allowed decisions are `continue`, `pause-for-user`,
`needs-baseline-readback`, `needs-verification`, and `blocked`.

Never emit `gate-passed`, `completion-granted`, or `authoritatively-safe`.

## Completion Candidate Protocol

Before a completion claim:

1. Use `aegis:verification-before-completion`.
2. Confirm every todo has status, blockers are resolved/externalized, evidence
   covers acceptance, and drift has no blocking state.
3. If a durable record exists, load `durable-work-guidance.md` for the completion
   bundle and structural workspace check.
4. For durable architecture work, pass the work record, proof bundle and ADR signals
   to verification for ADR Backfill Check.

Generated packs are future-runtime inputs only. Method Pack output remains
verified evidence and advisory judgment, not authoritative completion.

## Minimal Reporting Shape

Report naturally and omit empty structures. Keep these semantic slots visible:
`Aegis Visibility`; current todo/active/completed/next; baseline usage decision;
readiness state when present; fresh evidence; retry/convergence state when
relevant; drift decision; risk/unknown; and the next smallest safe action.
