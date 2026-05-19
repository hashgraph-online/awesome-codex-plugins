---
name: long-task-continuation
description: Use when a task is multi-step, may span context resets or sessions, uses subagents, or risks losing state before completion.
---

# Long Task Continuation

## Overview

Use this skill to keep long tasks checkpointed, resumable, drift-aware, and evidence-gated.

This is a protocol skill. It does not execute plans, dispatch subagents, run tests, or grant completion authority.

## Authority Boundary

Current owner:

- Method Pack protocol discipline

Not owned here:

- plan execution
- subagent dispatch
- host daemon / watchdog / automatic retry
- authoritative `GateDecision`
- evidence sufficiency final judgment
- completion authority

## When To Use

Use this skill when any of these are true:

- the task has multiple phases or more than one meaningful work slice
- the task may be interrupted, compacted, resumed, or handed off
- the task uses subagents
- the user explicitly asks for long-task continuity, resume safety, or avoiding drift
- the task changes architecture, contracts, shared workflows, or verification gates

For short direct answers or one-command checks, do not force this protocol.

## Required Artifacts

Maintain artifacts under `docs/aegis/work/YYYY-MM-DD-<slug>/`:

| Artifact | File | When |
|----------|------|------|
| TaskIntentDraft | `10-intent.md` and optional `task-intent-draft.json` | Start protocol |
| BaselineReadSetHint | `10-intent.md` (inline) | Start protocol |
| ImpactStatementDraft | `10-intent.md` (inline) | Start protocol |
| TodoCheckpointDraft | `20-checkpoint.md` and optional `todo-checkpoint-draft.json` | Each checkpoint |
| ResumeStateHint | `20-checkpoint.md` (inline) | Each pause/handoff |
| DriftCheckDraft | `20-checkpoint.md` (inline) and optional `drift-check-draft.json` | Per-slice protocol |
| EvidenceBundleDraft | `90-evidence.md` and optional `evidence-bundle-draft.json` | Per-slice protocol |
| Reflection | `99-reflection.md` | Completion candidate |

For medium+ complexity tasks only. Low-complexity tasks skip work/.

When durable architecture decisions are in scope, these work records are the
preferred ADR Auto Backfill source. Preserve ADR signals, source refs,
alternatives, compatibility boundaries, drift checks, retirement notes, and
baseline-sync questions in the work record instead of relying on memory at
completion time.

These are draft / hint / projection inputs. They are not authoritative runtime records.

## Workspace Helper Protocol

When configured Aegis workspace support or installed Aegis workspace support is
available, use it for the target project workspace and lifecycle records:

1. Initialize before writing work records:

   ```bash
   python <aegis-workspace-helper> init --root <target-project-root>
   ```

2. For a new medium+ task process trail, prefer helper-backed lifecycle
   creation over hand-created files:

   ```bash
   python <aegis-workspace-helper> new-work --root <target-project-root> --date YYYY-MM-DD --slug <slug> --title "<title>" --requested-outcome "<outcome>" --scope "<scope>" --change-kind <kind>
   ```

3. After each slice, update checkpoint, evidence, and drift through the helper:

   ```bash
   python <aegis-workspace-helper> add-checkpoint --root <target-project-root> --work YYYY-MM-DD-<slug> ...
   python <aegis-workspace-helper> add-evidence --root <target-project-root> --work YYYY-MM-DD-<slug> ...
   python <aegis-workspace-helper> add-drift-check --root <target-project-root> --work YYYY-MM-DD-<slug> ...
   ```

4. Before pause, handoff, or completion candidate, assemble a structural proof
   bundle and check the workspace:

   ```bash
   python <aegis-workspace-helper> bundle --root <target-project-root> --work YYYY-MM-DD-<slug>
   python <aegis-workspace-helper> check --root <target-project-root>
   ```

These helper checks validate workspace structure, index coverage, and JSON
sidecar shape only. They do not determine evidence sufficiency, do not produce
authoritative `GateDecision`, and do not grant completion authority.

## Start Protocol

Before long-task execution:

1. State the requested outcome, scope, non-goals, and risk hints.
2. If goal framing exists, restate goal, success evidence, stop condition, and
   non-goals. Stop condition must allow done, blocked, needs-verification, and
   scope-exceeded outcomes.
3. Identify baseline refs that must be read before changing files.
4. Create or update the todo map.
5. Create the first checkpoint:
   - current todo
   - active slice
   - completed todos
   - evidence refs
   - blocked-on items
   - next step
6. If baseline refs are missing, pause in `needs-baseline-readback`.
7. If the workspace helper is available, use `aegis-workspace.py new-work` to
   create/index the first `docs/aegis/work/` files and run `check --root
   <target-project-root>` before continuing.

## Per-Slice Protocol

Before each work slice, restate:

1. current goal
2. current todo
3. intended edits
4. explicit non-edits
5. verification command or manual check

After each work slice, update:

1. completed todos
2. evidence refs
3. blockers
4. next step
5. drift check
6. helper-backed JSON sidecars through `aegis-workspace.py add-checkpoint`,
   `aegis-workspace.py add-evidence`, and `aegis-workspace.py add-drift-check`
   when available

If no fresh evidence exists, the state is `needs-verification` or `partial`.

## Resume Protocol

When resuming:

1. Read latest checkpoint.
2. Read latest resume hint if present.
3. Re-read original task intent.
4. Re-read required baseline refs.
5. Compare current worktree state with checkpoint claims.
6. If checkpoint, baseline, and worktree disagree, pause and ask for direction.

Never resume from memory alone.

## Drift Check

Answer these after each slice:

- Does the current work still serve the original task intent?
- Does the current work still serve the goal and stop condition?
- Did the slice stay inside the compatibility boundary?
- Did any new owner, fallback, adapter, or branch appear?
- Is the retirement track still explicit?
- Did the evidence bundle grow enough to support the next claim?

Allowed decisions:

- `continue`
- `pause-for-user`
- `needs-baseline-readback`
- `needs-verification`
- `blocked`

Forbidden decisions:

- `gate-passed`
- `completion-granted`
- `authoritatively-safe`

## Completion Candidate Protocol

Before saying work is complete:

1. Use aegis:verification-before-completion.
2. Confirm every todo has a status.
3. Confirm blockers are resolved or externalized.
4. Confirm evidence refs cover the acceptance criteria.
5. Confirm drift check has no blocking state.
6. Run `python <aegis-workspace-helper> bundle --root <target-project-root>
   --work YYYY-MM-DD-<slug>` if the helper is available and a work record
   exists.
7. Run `python <aegis-workspace-helper> check --root <target-project-root>`
   if the helper is available and the task wrote `docs/aegis/` records.
8. Treat the generated `GateInputPack` as future-runtime input only.
9. If durable architecture decisions were in scope, pass the work record,
   proof bundle, drift checks, evidence refs, and ADR signals into
   aegis:verification-before-completion for ADR Backfill Check.

Method Pack output is verified evidence and advisory judgment only. It is not authoritative completion.

## Minimal Reporting Shape

Use this shape for long-task updates:

- `TodoCheckpointDraft`: current todo, completed todos, active slice, next step
- `Evidence`: commands, files, logs, or manual checks
- `DriftCheckDraft`: scope, compatibility, retirement, decision
- `Risk / Unknown`: unresolved blockers or missing evidence
- `Next`: the next smallest safe action
