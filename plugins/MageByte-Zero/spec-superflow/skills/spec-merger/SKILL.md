---
name: spec-merger
description: Sync delta specs to main specs before closure. Invoke while an executing change has delta specs to merge into the main spec base, or when detecting spec drift across multiple changes.
---

# Spec Merger

## Bundled runtime

Before executing a CLI line below, replace its leading `SSF` with `node "<plugin-root>/scripts/spec-superflow.mjs"`; `<plugin-root>` is the absolute directory two levels above this file. Never run `SSF` literally or call an `ssf` from `PATH`.

Before the final `executing → closing` transition, delta specs (ADDED/MODIFIED/REMOVED/RENAMED) must be published into the main spec base. `changes/<change>/` remains the active workflow source; root `specs/` is only the published baseline. **Specs that aren't synced become lies.** A change already in `closing` must not be routed to `spec-merger`.

## Execution-State Guard

Before `SSF sync` or any other write, run
`SSF state get <change-dir> state`.
Continue only when the persisted state is exactly `executing`. If it is
`closing` → STOP: "Closing is terminal. Do not route this change to spec-merger;
synchronization belongs before the final executing → closing transition." For
any other state, or if the state cannot be read → STOP and route through
`workflow-start`; do not perform side effects.

## Pre-Flight Checks

### Conflict Detection
Run `SSF sync <change-dir>`. If conflicts are detected (same requirement modified by multiple changes), present the conflict list to the user for resolution order.

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
3. `SSF sync` automatically writes a publication receipt to the active change state. Do **not** manually set `spec_merged`: that legacy marker is not closing evidence. The closing guard recomputes the delta and published-baseline hashes, so any later edit requires another sync.
4. If the change has no delta sections, no publication receipt is required.

## Exception Handling

- **Parse failures**: Report file and section. Do not attempt partial merges.
- **No deltas**: If change has no delta sections, report nothing to merge and exit cleanly.
- **User interruption**: On resume, check for merge conflict markers before proceeding.
