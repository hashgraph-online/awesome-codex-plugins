---
name: spec-merger
description: Sync delta specs to main specs before closure. Invoke while an executing change has delta specs to merge into the main spec base, or when detecting spec drift across multiple changes.
---

# Spec Merger

Before the final `executing → closing` transition, delta specs (ADDED/MODIFIED/REMOVED/RENAMED) must be merged into the main spec base. **Specs that aren't synced become lies.** A change already in `closing` must not be routed to `spec-merger`.

## Execution-State Guard

Before `ssf sync` or any other write, run
`npx --yes --package spec-superflow@0.10.0 ssf state get <change-dir> state`.
Continue only when the persisted state is exactly `executing`. If it is
`closing` → STOP: "Closing is terminal. Do not route this change to spec-merger;
synchronization belongs before the final executing → closing transition." For
any other state, or if the state cannot be read → STOP and route through
`workflow-start`; do not perform side effects.

## Pre-Flight Checks

### Conflict Detection
Run `npx --yes --package spec-superflow@0.10.0 ssf sync <change-dir>`. If conflicts are detected (same requirement modified by multiple changes), present the conflict list to the user for resolution order.

## Sync Process

### Step 1: Identify Deltas
Each `specs/<capability>/spec.md` under the change folder contains delta operations under `## ADDED/MODIFIED/REMOVED/RENAMED Requirements`.

### Step 2: Apply by Operation

**ADDED**: Append to `specs/<capability>/spec.md`. Create the main spec if it doesn't exist. Insert before any REMOVED section.

**MODIFIED**: Match on `### Requirement: <name>`. Replace description and scenarios. Preserve original in a `### Previous version` subsection. Flag if requirement doesn't exist in main spec.

**REMOVED**: Move to `## Removed` section with deprecation note: reason, migration, and change name. Flag if requirement doesn't exist.

**RENAMED**: Match old name, change header to new name, add `_Renamed from <old> in <change>_`. Flag if new name collides with existing.

### Step 3: Conflict Detection
Before executing, detect:
- Same requirement modified by multiple unsynced changes → manual resolution
- RENAMED target collides with existing requirement → manual resolution
- MODIFIED/REMOVED targeting nonexistent requirements → flag

### Step 4: Execute Merge
Apply changes. Do NOT delete delta specs — they remain for traceability. After merge, validate: no duplicate requirement names, no orphaned references, REMOVED section clearly separated.

### Step 5: Report
Output sync report table: Capability, ADDED/MODIFIED/REMOVED/RENAMED counts, Status (✓/⚠). Summary with totals and unresolved conflicts.

## Guardrails

- Do not delete delta spec files (historical record)
- Do not auto-resolve conflicts across changes
- Do not merge specs for unverified changes
- Validate main spec consistency after each capability merge

## Post-Sync

1. Report results. If no conflicts → ready to archive. If conflicts → user resolves before archive.
2. Change folder (including deltas) remains for traceability.
3. Record that merging is complete so the `executing → closing` guard allows closure:
   ```bash
   npx --yes --package spec-superflow@0.10.0 ssf state set <change-dir> spec_merged true
   ```
   (If the change had no delta sections, still set `spec_merged true` — there was nothing to merge.)

## Exception Handling

- **Parse failures**: Report file and section. Do not attempt partial merges.
- **No deltas**: If change has no delta sections, report nothing to merge and exit cleanly.
- **User interruption**: On resume, check for merge conflict markers before proceeding.
