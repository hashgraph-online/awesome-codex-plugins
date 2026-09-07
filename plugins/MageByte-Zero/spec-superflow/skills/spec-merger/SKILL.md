---
name: spec-merger
description: Sync delta specs to main specs before closure. Invoke while an executing change has delta specs to merge into the main spec base, or when detecting spec drift across multiple changes.
---

# Spec Merger

Before the final `executing → closing` transition, delta specs (ADDED/MODIFIED/REMOVED/RENAMED) must be published into the main spec base. `changes/<change>/` remains the active workflow source; root `specs/` is only the published baseline. **Specs that aren't synced become lies.** A change already in `closing` must not be routed to `spec-merger`.

## Execution-State Guard

Before `ssf sync` or any other write, run
`ssf state get <change-dir> state`.
Continue only when the persisted state is exactly `executing`. If it is
`closing` → STOP: "Closing is terminal. Do not route this change to spec-merger;
synchronization belongs before the final executing → closing transition." For
any other state, or if the state cannot be read → STOP and route through
`workflow-start`; do not perform side effects.

## Pre-Flight Checks

### Conflict Detection
Run `ssf sync <change-dir>`. If conflicts are detected (same requirement modified by multiple changes), present the conflict list to the user for resolution order.

## Sync Process

### Step 1: Identify Deltas
Each `specs/<capability>/spec.md` under the change folder contains delta operations under `## ADDED/MODIFIED/REMOVED/RENAMED Requirements`.

`## Purpose` is an optional top-level delta extension. Use it only when creating a canonical main spec. When it is absent or empty, the sync result uses and reports a deterministic default Purpose so legacy delta specs remain usable. A delta Purpose must not overwrite an existing main spec Purpose.

### Step 2: Apply by Operation

**ADDED**: Append the requirement to the published baseline's `## Requirements`. Create a canonical main spec if it does not exist.

**MODIFIED**: Match on `### Requirement: <name>` and replace its description and scenarios. Flag if the requirement does not exist in the canonical baseline.

**REMOVED**: Remove the matched requirement from the published baseline. Flag if it does not exist.

**RENAMED**: Match the old name and change its header to the new name. Flag if the new name collides with an existing requirement.

### Step 3: Conflict Detection
Before executing, detect:
- Same requirement modified by multiple unsynced changes → manual resolution
- RENAMED target collides with existing requirement → manual resolution
- MODIFIED/REMOVED targeting nonexistent requirements → flag

### Step 4: Execute Merge
Validate every candidate main spec before writing any target. Apply only changed candidates. An operation that is already reflected in the baseline is an idempotent no-op and must report that it made no write. A missing operation target with a case- or whitespace-only near match is an error, not a no-op. Do NOT delete delta specs — they remain for traceability. The root baseline must contain `## Requirements`, never `## ADDED/MODIFIED/REMOVED/RENAMED Requirements` headers. Unsafe legacy delta-only baselines that cannot be interpreted are rejected instead of guessed.

### Step 5: Report
Output sync report table: Capability, ADDED/MODIFIED/REMOVED/RENAMED counts, Status (✓/⚠). Summary with totals and unresolved conflicts.

## Guardrails

- Do not delete delta spec files (historical record)
- Do not auto-resolve conflicts across changes
- Do not merge specs for unverified changes
- Validate every candidate main spec before publication; on validation failure, write no target
- Treat only semantically equivalent, already-applied operations as no-op; near-match requirement names must fail

## Post-Sync

1. Report results. If no conflicts → ready to archive. If conflicts → user resolves before archive.
2. Change folder (including deltas) remains for traceability.
3. `ssf sync` automatically writes a publication receipt to the active change state. Do **not** manually set `spec_merged`: that legacy marker is not closing evidence. The closing guard recomputes the delta and published-baseline hashes, so any later edit requires another sync.
4. If the change has no delta sections, no publication receipt is required.

## Exception Handling

- **Parse failures**: Report file and section. Do not attempt partial merges.
- **No deltas**: If change has no delta sections, report nothing to merge and exit cleanly.
- **User interruption**: On resume, check for merge conflict markers before proceeding.

## Standard User-Facing Handoff

End every user-facing phase report with this concise handoff. Only a successfully
persisted `closing` state and `abandoned` are terminal.

### Normal report

- Current stage: `<detected workflow stage>`.
- Completed / blocker: `<completed work>`.
- Next stage: `<next workflow stage or skill>`.
- Entry condition: `<what must be true to enter it>`.

### Blocked report

- Current stage: `<detected workflow stage>`.
- Completed / blocker: `<blocking fact or missing evidence>`.
- Next stage: `<stage that resumes after the blocker>`.
- Entry condition: `<the approval, artifact, validation, or fix required>`.

### Approval-wait report

- Current stage: `<detected workflow stage>`.
- Completed / blocker: `<work ready for the named decision>`.
- Next stage: `<stage that follows approval>`.
- Entry condition: `<explicit user approval or recorded decision>`.

### Closing-in-progress report

- Current stage: `executing`; release verification or archive work is still running.
- Completed / blocker: `<completed release work or remaining release blocker>`.
- Next stage: complete the remaining release or archive step, then transition to `closing` (not `none`).
- Entry condition: all release and archive work is complete and the transition succeeds.

### Successful terminal report

- Current stage: successfully persisted `closing` or `abandoned`.
- Completed / blocker: `<persisted terminal outcome>`.
- Next stage: `none`.
- Entry condition: no further transition exists.
