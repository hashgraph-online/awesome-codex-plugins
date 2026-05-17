# Phase 4: REVIEW + FINALIZE — GATE

Combines staff review with finalization. The staff-reviewer agent is the workflow's only named subagent — independent context, scoped tools, fresh eyes on the diff.

Apply [Iron Rules](../iron-rules.md) throughout. Staff review enforces the diff-relevant pillars (Pillar 1 Simplicity, Pillar 2 Signal/zero noise, Pillar 3 No claim without evidence, Pillar 5 WHY comments, Pillar 6 Refactoring objective). Finalization applies Pillar 4 (document discoveries), Pillar 7 (keep project docs slim), and Pillar 8 (English + memory hygiene). Process Rule A (no commits without explicit user request) gates step 4d.

---

## 4a: Staff Engineer Review (MANDATORY)

**Cannot skip.** Do not rationalize *"simple changes"* or *"already verified."*

### Before spawning

1. Run `git diff` — if >500 lines, write to a temp file and pass the path.
2. Collect Phase 3 pass/fail summary (full details already in plan file — pass path, not content).
3. **If diff >2000 lines:** Split by component using `## Task Checklist` file list. Spawn separate reviews. All must pass.

### Spawn `staff-reviewer` via Task tool

Pass:

- **Task:** Original requirement.
- **Constraints:** From approved plan.
- **Git diff:** The changes (path if >500 lines).
- **Plan file path:** FULL path — reviewer reads `## Task Checklist` and `## Verification Results` directly from the file.
- **Patterns file path(s):** From language skill config.
- **Verification summary:** Phase 3 pass/fail.
- **Detected framework / additional context** from language skill.

Two-stage review: spec compliance → code quality. Returns `APPROVED`, `SPEC_ISSUES`, or `ISSUES` with file:line.

### Persist results to plan file

After each cycle, append `## Review Log`:

```markdown
## Review Log

### Review 1
- **Stage 1 (Spec):** PASS / SPEC_ISSUES
- **Stage 2 (Quality):** APPROVED / ISSUES
- **Issues:**
  1. [file:line] [SEVERITY] [description] → Fix: [action]
- **Action:** Applied fixes, re-verified, re-submitted

### Review 2
- **Result:** APPROVED
```

### Handling results

- **SPEC_ISSUES** → fix → re-verify (Phase 3 Step 4) → re-review.
- **ISSUES** → fix → re-verify → re-review.

Iterate until APPROVED.

**After fix-review cycle:** Run `/compact` before re-spawning.

**Gate:** State **"STAFF REVIEW: APPROVED"**

---

## 4b: Chronicle Finalization

1. **Chronicle created:** Read `## Implementation Log` for discoveries. Align with final code. Update Status to Completed. Identify insights for `AGENTS.md` (or `CLAUDE.md` if the project uses that as primary).
2. **Chronicle NOT NEEDED:** Check WORKFLOW STATE reason. If significant discoveries emerged (check Implementation Log), consider retroactive chronicle.
3. **Update `AGENTS.md`** (or `CLAUDE.md` if primary) with new patterns/rules/knowledge.
4. **Update WORKFLOW STATE:** `Status: Completed`, `Current Phase: 4 (Complete)`.

**Gate:** State **"CHRONICLE FINALIZED — [filename]"** (or confirm NOT NEEDED).

---

## 4c: Align Documentation

Invoke `development-skills:align-docs` via the Skill tool.

---

## 4d: Integration

**Default (changes on current branch):** Ask via `AskUserQuestion`:

- *"Implementation complete. Commit the changes now?"* — options: `"Yes, commit now"`, `"No, I'll handle it myself (Recommended)"`.

**STOP and wait.** Only commit if user picks `"Yes, commit now"`. Use `development-skills:commit` via the Skill tool.

**Unmerged worktree branch (rare):** Ask via `AskUserQuestion`:

- *"Implementation complete. How would you like to land the changes?"* — options: `"Merge to current branch locally"`, `"Push and create a Pull Request"`, `"Keep the branch as-is"`, `"Discard this work"`.

| Option | Actions |
|--------|---------|
| 1. Merge | checkout base → merge → test → delete branch → cleanup |
| 2. PR | push → `gh pr create` with plan summary → keep branch |
| 3. Keep | Report branch name and path |
| 4. Discard | Confirm with "discard" → checkout base → delete branch → cleanup |

---

## Expected Artifacts

- `## Review Log` in plan file
- Staff reviewer APPROVED
- Chronicle finalized (or confirmed NOT NEEDED)
- `AGENTS.md` (or `CLAUDE.md`) updated (if applicable)
- Documentation aligned
- Changes integrated per user's choice
- WORKFLOW STATE: `Status: Completed`, `Current Phase: 4 (Complete)`

State: **"WORKFLOW COMPLETE"**
