---
name: resolve-merge
description: "Use when the user asks to resolve merge conflicts, fix a failed merge, rebase conflict, or run /resolve-merge. Use when git status shows UU/AA/DD conflicts, when there are <<<<<<< conflict markers, when git merge or git pull failed with CONFLICT, or when numbered docs/plans need renumbering after merge. Triggers on: merge conflict, conflict markers, both modified, git merge failed, rebase conflict, resolve conflicts."
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Edit, Write, AskUserQuestion
---

# Resolve Merge Conflicts

Announce: "Using the resolve-merge skill."

1. Guard: run `git rev-parse MERGE_HEAD`; if no merge/rebase is in progress, stop with "No merge in progress."
2. Plan read-only — make no writes until the gate (step 5). Run `git status --short` and classify each conflicted file AUTO or JUDGMENT.
3. AUTO = resolution provably safe by a mechanical check; **default everything else to JUDGMENT**. AUTO cases:
   - Sides byte-identical (`git show :2:<f>` vs `:3:<f>`) or differing only in whitespace/EOL → take either.
   - DD, UD → `git rm`. UA, DU → `git checkout --theirs && git add`. AU → `git add`, but `git rm` if its slug already exists in theirs at another number (duplicate).
   - Lock file → never hand-merge: checkout one side, regenerate via the package manager.
   - `CHANGELOG.md` → merge unique entries, dedupe, keep category order.
4. Numbered docs (`docs/plans/NNNN__*`, `docs/chronicles/NNNN__*`): use THEIRS numbering as base, place each OURS-unique file at the next free number on collision, leave no gaps or duplicates; then fix internal refs so each plan's research ref and each chronicle's self-ref match its own number and every cross-ref resolves.
5. Present the full plan (every conflicted file, untruncated: file · code · action · AUTO/JUDGMENT) and gate once via `AskUserQuestion`: Approve / Modify / Abort. Abort leaves all files untouched.
6. Execute approved AUTO actions silently; report only counts and errors.
7. For each JUDGMENT file, show only the OURS hunk, the THEIRS hunk, and your proposed merge (those exact bytes, no outer fence, invent nothing); ask Approve / Edit / Skip. Skip leaves the conflict.
8. Any single failure (e.g. lock-file regen) → leave that file conflicted, continue, list it under `Skipped`. Never abort the run for one file.
9. Verify: no unresolved conflicts, no `<<<<<<<`/`=======`/`>>>>>>>` markers in tracked files, numbering and refs intact if docs changed, plus any known build/lint check.
10. Report a compact summary (`N resolved: X AUTO, Y JUDGMENT; Skipped: …`), then hand off to `/commit` — do not commit. If a check fails, report the failure and stop.

(Codex: replace each `AskUserQuestion` gate with a numbered list + STOP — see `../using-development-skills/references/codex-tools.md`.)
