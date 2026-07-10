# Plan Skill Examples

Detailed examples of `$plan` usage scenarios.

---

## Example 1: Plan from Research

**User says:** `$plan "add user authentication"`

**What happens:**
1. Agent reads recent research from `.agents/research/2026-02-13-authentication-system.md`
2. Explores codebase to identify integration points
3. Decomposes into 5 issues: middleware, session store, token validation, tests, docs
4. Creates epic `ag-5k2` with 5 child issues in 2 waves
5. Output written to `.agents/plans/2026-02-13-add-user-authentication.md`

**Result:** Epic with dependency graph, conformance checks, and wave structure for parallel execution.

## Example 2: Plan with Auto Mode

**User says:** `$plan --auto "refactor payment module"`

**What happens:**
1. Agent skips human approval gates
2. Searches knowledge base for refactoring patterns
3. Creates epic and child issues automatically
4. Records ratchet progress

**Result:** Fully autonomous plan creation with 3 waves, 8 issues, ready for `$crank`.

## Example 3: Plan Cleanup Epic with Audit

**User says:** `$plan "remove dead code"`

**What happens:**
1. Agent runs quantitative audit: 3,003 LOC across 3 packages
2. Creates issues grounded in audit numbers (not vague "cleanup")
3. Each issue specifies exact files and line count reduction
4. Output includes deletion verification checks

**Result:** Scoped cleanup plan with measurable completion criteria (e.g., "Delete 1,500 LOC from pkg/legacy").

## Example 4: Plan with Implementation Detail (Symbol-Level)

**User says:** `$plan "add stale run detection to RPI status"` (external operator loop surface)

**What happens:**
1. Agent explores codebase, finds `classifyRunStatus` at `rpi_status.go:850`, `phasedState` at `rpi_phased.go:100`
2. Produces file inventory: 4 files to modify, 2 new files
3. Each implementation section names exact functions, parameters, struct fields with JSON tags
4. Tests section lists `TestClassifyRunStatus_StaleWorktree`, `TestDetermineRunLiveness_MissingWorktree` with descriptions
5. Verification section provides manual simulation: create fake stale run, check the external RPI status surface output

**Result:** Implementer can execute the plan in a single pass without rediscovering any symbol names, reducing implementation time by ~50% and eliminating spec-divergence rework.

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ao beads exec create` fails | Beads not initialized in repo | Initialize the tracker first (e.g. `br init --prefix <prefix>`) |
| Dependencies not created | Issues created without explicit `ao beads exec dep add` calls | Verify plan output includes dependency commands. Re-run to regenerate |
| Plan too large | Research scope was too broad, resulting in >20 issues | Narrow the goal or split into multiple epics |
| Wave structure incorrect | False dependencies declared (logical ordering, not file conflicts) | Review dependency necessity: does blocked issue modify blocker's files? |
| Conformance checks missing | Acceptance criteria not mechanically verifiable | Add `files_exist`, `content_check`, `tests`, or `command` checks per validation-contract.md |
| Epic has no children | Plan created but tracker commands failed silently | Check `ao beads exec list --type epic` output; re-run plan with the tracker available |
