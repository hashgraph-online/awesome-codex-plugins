---
name: resolve-merge
description: "Use when the user asks to resolve merge conflicts, fix a failed merge, rebase conflict, or run /resolve-merge. Use when git status shows UU/AA/DD conflicts, when there are <<<<<<< conflict markers, when git merge or git pull failed with CONFLICT, or when numbered docs/plans need renumbering after merge. Triggers on: merge conflict, conflict markers, both modified, git merge failed, rebase conflict, resolve conflicts."
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Edit, Write, AskUserQuestion
---

# Resolve Merge Conflicts

**Announce:** "I'm using the resolve-merge skill. Systematic merge conflict resolution."

## Prerequisites

Verify merge state:

```bash
git rev-parse MERGE_HEAD
```

If not in a merge, STOP with: "No merge in progress."

---

## Phase 1/3 — Plan + Gate

**This phase is read-only. Run no state-modifying commands until after the gate at the end of this phase.**

### Conflict type reference

| Code | Meaning |
|------|---------|
| DD | Both deleted |
| AU | Added by us (HEAD) |
| UA | Added by them (MERGE_HEAD) |
| UU | Both modified |
| DU | Deleted by us, modified by them |
| UD | Modified by us, deleted by them |
| AA | Both added same path |
| R | Renamed |

### Categorize

Run `git status --short` silently. **Numbered docs** are files matching `docs/plans/NNNN__*.md` and `docs/chronicles/NNNN__*.md`. Everything else is a **code file**. Do NOT display a separate categorization table — the per-file Resolution Plan below makes counts implicit.

Build the complete resolution plan before touching any file. Present every conflicted file as one row.

### AUTO vs JUDGMENT classification rules

**Default = JUDGMENT.** A file is AUTO **only** if it matches one of the explicit rows below. Anything else — including any UU/AA the agent is unsure about — is JUDGMENT.

**AUTO — execute after up-front plan approval (mechanical checks only):**

| Conflict code | Condition (must match exactly) | Action |
|---------------|--------------------------------|--------|
| DD | Both deleted | `git rm` |
| UA | Theirs added | `git checkout --theirs && git add` |
| DU | Deleted by us, modified by them | `git checkout --theirs && git add` |
| UD | Modified by us, deleted by them | `git rm` |
| AU | Ours added, slug exists in THEIRS at a different number | `git rm` (duplicate) |
| AU | Ours added, OURS-unique slug | `git add` |
| UU / AA | File is in `docs/plans/` or `docs/chronicles/` **AND** `git show :2:<file>` and `git show :3:<file>` are byte-identical (renumbering-only conflict, no body divergence) | `git checkout --theirs && git add` |
| UU / AA | `git show :2:<file>` and `git show :3:<file>` are byte-identical | take either side |
| UU / AA | Lock file (`package-lock.json`, `poetry.lock`, `yarn.lock`, `Cargo.lock`, etc.) **AND** the corresponding manifest (`package.json`, `pyproject.toml`, `Cargo.toml`) is unchanged on both sides OR already non-conflicted | checkout chosen side + regenerate via package manager |
| UU | `CHANGELOG.md` | combine unique entries, dedupe, keep sorted by category |
| UU / AA | Diff between OURS and THEIRS hunks is pure whitespace / EOL / indent only | take either side |

**JUDGMENT — DEFAULT for anything not in the AUTO table above. Examples that explicitly belong here:**

- UU/AA where one side is a "strict superset" of the other in line count (textual superset ≠ semantic superset — the additional lines may change behavior).
- UU/AA where the diff includes any non-whitespace change to import statements (a new import can be a side-effect import or change re-exports).
- UU/AA in lock files when the corresponding manifest is also conflicted on both sides (a deliberate dependency bump may be silently dropped by `--ours/--theirs` regen).
- UU/AA in `docs/plans/` or `docs/chronicles/` where body content differs between OURS and THEIRS (renumbering AUTO covers path-level conflicts only, not divergent prose).
- UU/AA in any code file where conflict markers (`<<<<<<<` / `=======` / `>>>>>>>`) remain after `git status` reports the conflict — these are by definition regions git could not auto-merge.

**Mechanical classification procedure (run silently for each conflicted file):**

1. If the file matches an AUTO row above with all conditions met, mark AUTO.
2. Otherwise, mark JUDGMENT.

The agent must not classify AUTO based on a semantic judgment of "this looks safe." If a rule's condition cannot be checked mechanically, the file is JUDGMENT.

**Notes on the byte-identity checks:**

- `git show :2:<file>` is the OURS version (HEAD); `git show :3:<file>` is the THEIRS version (MERGE_HEAD). Stage 1 (`:1:`, the merge base) does not need to be checked — if OURS and THEIRS resolve to identical content, taking either side is a no-op merge regardless of the base.
- `R` (renamed) is excluded from the AUTO table because git auto-resolves renames before `git status` reports a conflict; you will not see `R` in the conflict-state output. It appears only in the conflict-type reference (above) for completeness.

### Build the plan

For numbered docs, run the read-only inventories first (no state modification):

```bash
git ls-tree -r --name-only HEAD -- docs/plans/ docs/chronicles/ | sort
git ls-tree -r --name-only MERGE_HEAD -- docs/plans/ docs/chronicles/ | sort
```

Extract slugs. Identify shared slugs, OURS-only slugs, THEIRS-only slugs. Count duplicates and gaps on each side.

For code files, inspect each conflicted file to determine the conflict nature (`git diff`, `cat`, `git show HEAD:<path>`, `git show MERGE_HEAD:<path>`).

### Present the Resolution Plan table

Display the complete plan — every conflicted file must appear as a row. No "and others", no "etc.", no truncated paths. Render every filename in full.

```
## Phase 1/3 — Plan

Numbering analysis (numbered docs only):
  OURS:   N plans, M chronicles (X duplicates, Y gaps)
  THEIRS: N plans, M chronicles (X duplicates, Y gaps)
  Recommended base: THEIRS (fewer duplicates/gaps — prefer THEIRS by default)
  OURS-unique files to place: [slugs]

| # | File | Conflict | Action | Class | Reason |
|---|------|----------|--------|-------|--------|
| 1 | docs/plans/0007__2026-04-22__implementation_plan__cache-layer.md | UA | checkout --theirs + add | AUTO | new plan from feature branch |
| 2 | package-lock.json | UU | checkout --ours + npm install | AUTO | lock file, manifest unchanged on both sides |
| 3 | src/api/auth.ts | UU | edit (per-file gate) | JUDGMENT | conflict markers in login() body |

Total: N files — N AUTO + N JUDGMENT
```

The Class column already marks JUDGMENT rows — do NOT print a separate JUDGMENT files list under the table.

### Gate (up-front, once)

After displaying the table, gate via `AskUserQuestion`:
- Question: "Approve plan and execute?"
- Options: `"Approve (Recommended)"` / `"Modify plan"` / `"Abort"`

(Codex: numbered list + STOP — see `../using-development-skills/references/codex-tools.md`.)

- **Approve:** proceed to Phase 2/3.
- **Modify plan:** ask what to change. Allowed modifications: (a) re-classify a row AUTO ↔ JUDGMENT; (b) exclude a row from execution (leave the file conflicted, surface in summary); (c) change the action for a row to a different listed action (e.g., switch lock-file from `--ours` regen to `--theirs` regen). Any other modification (custom actions, re-orderings, or "auto-merge this JUDGMENT file without showing me") MUST be refused — point the user to the per-file JUDGMENT gate instead. Then update the plan table, re-display, re-gate.
- **Abort:** stop with "Merge resolution aborted. No files modified."

---

## Phase 2/3 — Execute

Run the approved actions in order. **All shell commands run silently** — do not echo command stdout to the user. Surface only: success/fail counts per category, any non-zero exit codes, any `ERESOLVE`/error text from package managers. Skip "running git status …", "executing …" narration.

### 2a: Numbered docs — apply renumbering

**Skip if no numbered doc conflicts exist.**

Process in this order:

1. **DD files** → `git rm`
2. **UA files** (theirs added) → `git checkout --theirs` + `git add`
3. **AU files** (ours added):
   - Slug exists in THEIRS at a different number → `git rm` (duplicate)
   - OURS-unique → `git add`
4. **DU files** → `git checkout --theirs` + `git add`
5. **UD files** → `git rm`
6. **UU / AA files** in docs **classified AUTO** (body byte-identical between OURS and THEIRS) → `git checkout --theirs` + `git add`. UU/AA in docs with body divergence are JUDGMENT (handled in 2d), not here.

**Place OURS-unique files:** For each OURS-only slug, check for number collisions with THEIRS files. If collision, rename to next available number. If not, keep as-is.

Verify: no gaps, no duplicate numbers.

### 2b: Fix internal references

**Skip if no numbered doc conflicts exist.**

After renumbering, internal cross-references may be stale. Fix silently; report counts.

**Research references in plan files** — each plan should reference its own number's research file (e.g., plan 0015 → `0015__research__cache-layer.md`). Handle all reference formats:

- `NNNN__research__{slug}.md`
- `NNNN__research.md` (legacy — rename to include slug)
- `NNNN**research**slug.md` (bold markdown)
- `NNNN\_\_research\_\_{slug}.md` (escaped underscores)

**Chronicle self-references** — each chronicle has a self-reference line like `> Chronicle: NNNN__...`. Verify the number matches the filename.

**Cross-plan and cross-chronicle references** — verify each referenced file exists. If not, find the correct file by slug and update.

**Leftover conflict markers in docs:**
```bash
grep -rn '<<<<<<< \|=======\|>>>>>>> ' docs/plans/ docs/chronicles/
```

Resolve any found by picking the correct side.

Stage all doc fixes:
```bash
git add docs/plans/ docs/chronicles/
```

### 2c: Code files — AUTO actions

Execute each AUTO code file action from the plan without further prompting.

**Lock files** — do NOT manually merge. Accept the chosen side, then regenerate:
```bash
# npm
git checkout --ours package-lock.json && npm install
# If ERESOLVE: git checkout --theirs package-lock.json && npm install

# pnpm
git checkout --ours pnpm-lock.yaml && pnpm install

# yarn
git checkout --ours yarn.lock && yarn install

# bun (lockfile is bun.lock or bun.lockb)
git checkout --ours bun.lock && bun install
```

If lock-file regeneration fails: leave the file in its conflicted state, do NOT abort the run, continue with the remaining AUTO and JUDGMENT files, and surface the failure in the Phase 3/3 final summary under a `Skipped (regen failed)` line.

**CHANGELOG.md** — combine unique entries from both sides, remove duplicates, keep sorted by category. Stage.

**Pure whitespace / EOL / indent-only conflicts** — take either side. Stage. (Import-block changes do NOT qualify as AUTO — they are JUDGMENT.)

**Byte-identical OURS and THEIRS** — take either side. Stage. ("Strict superset" cases are JUDGMENT, not AUTO — handle in 2d.)

Stage all auto-resolved code files:
```bash
git add [resolved files]
```

### 2d: Code files — JUDGMENT gates

For each file classified JUDGMENT:

1. **Read the file's live conflict markers** in the working tree. The OURS hunk = the bytes between `<<<<<<<` and `=======`. The THEIRS hunk = the bytes between `=======` and `>>>>>>>`. Render ONLY those bytes — do NOT include surrounding function bodies, lines above the `<<<<<<<` marker, or lines below the `>>>>>>>` marker. Hunk-only — never paraphrase.
2. **Compute the proposed resolution** from those exact bytes. Do not invent content not present in either side unless the user has explicitly asked for it.
3. **Output the gate as plain markdown.** The output has exactly THREE fenced code blocks (OURS, THEIRS, Resolved) and nothing else. **Do NOT wrap any part of the gate in an outer fence** — wrapping the whole gate in a fence causes the inner ``` delimiters to render as literal backticks in the user's terminal. The gate is markdown text emitted directly into the chat, not a code block containing markdown.

   Format (literal output the agent emits, in order):

   - heading line: `### JUDGMENT: <relative path>`
   - blank line
   - label line: `OURS:`
   - one fenced code block in the file's language, containing ONLY the OURS hunk (bytes between `<<<<<<<` and `=======`)
   - blank line
   - label line: `THEIRS:`
   - one fenced code block in the file's language, containing ONLY the THEIRS hunk (bytes between `=======` and `>>>>>>>`)
   - blank line
   - label line: `Resolved:`
   - one fenced code block in the file's language, containing the merged content
   - blank line
   - rationale line: `Why: <one short sentence>`

4. **Then ask via `AskUserQuestion`:**
   - Options: `"Approve (Recommended)"` / `"Edit and re-show"` / `"Skip this file (leave conflict)"`

(Codex: numbered list + STOP — see `../using-development-skills/references/codex-tools.md`.)

- **Approve:** apply the edit, stage the file.
- **Edit and re-show:** ask what to change, update the proposed resolution, re-display the gate.
- **Skip this file (leave conflict):** leave conflict markers in place; note in the final summary.

---

## Phase 3/3 — Verify

### 3a: No unresolved conflicts

```bash
git status --short | grep -E "^(UU|DD|AU|UA|DU|UD|AA)"
```

Must return empty.

### 3b: No conflict markers in tracked files

```bash
grep -rn '<<<<<<< \|=======\|>>>>>>> ' . --include="*.md" --include="*.ts" --include="*.tsx" --include="*.py" --include="*.json" --include="*.java" --include="*.swift" | grep -v node_modules | grep -v '.next' | grep -v __pycache__
```

Must return empty.

### 3c: Numbering integrity (if docs were resolved)

Verify plans and chronicles have sequential numbers with no gaps and no duplicates.

### 3d: Reference integrity (if docs were resolved)

Verify all research refs point to own number, chronicle self-refs match filename, cross-references are valid.

### 3e: Optional build/lint check

Run the project's standard verification commands if known (e.g., type checker, linter).

### 3f: Final summary

Display a compact summary. Render only the lines that apply.

```
## Phase 3/3 — Verify

All checks passed.

N conflicts resolved (X AUTO, Y JUDGMENT). Build/lint: PASS. Ready: /commit.
```

Append the following lines ONLY if non-empty (omit entirely otherwise — do NOT print "none"):

```
Skipped (conflict left): <files>
Skipped (regen failed): <files>
```

If a verification check (3a/3b/3c/3d) failed, replace the "All checks passed." line with the specific failure (e.g., "FAIL — conflict markers remain in: <files>") and stop without offering /commit.

Audit-trail detail (renumber counts, refs fixed, OURS/THEIRS unique slugs, numbering ranges) belongs in the commit message — `/commit` will collect it from the staged diff. Do NOT pre-emit it in this summary.

---

## Edge Cases

- **No numbered doc conflicts:** Skip phases 2a and 2b. Go straight to 2c/2d.
- **No code conflicts:** Skip phases 2c and 2d.
- **Only one side renumbered:** Use that side's numbering directly; no gap/duplicate analysis needed.
- **Conflicting unique files at the same number:** Shift the later-dated file to the next available number.
- **Research file missing for a plan:** Note in the final summary; do not create one.
- **Lock-file regeneration fails:** Leave the file in its conflicted (unstaged) state, continue with remaining files, surface under `Skipped (regen failed)` in the Phase 3/3 final summary; let the user decide whether to fix manually before committing.
