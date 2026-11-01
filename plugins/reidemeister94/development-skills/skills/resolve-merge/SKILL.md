---
name: resolve-merge
description: "Resolve an active merge or rebase conflict, including plans and chronicles with colliding names."
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Edit, Write, AskUserQuestion
---

# Resolve Merge Conflicts

1. Verify `MERGE_HEAD` or `REBASE_HEAD`; otherwise stop with `No merge in progress.`
2. Before any write, list conflicts and classify each as AUTO or JUDGMENT.
3. AUTO requires mechanical proof; default to JUDGMENT. AUTO cases:
   - Sides byte-identical (`git show :2:<f>` vs `:3:<f>`) or differing only in whitespace/EOL → take either.
   - AU → `git add`, but `git rm` if its slug already exists in theirs under another name (duplicate).
   - Lock file → checkout one side, regenerate via the package manager.
   - `CHANGELOG.md` → merge unique entries, dedupe, keep category order.
4. When an OURS-only `NNNN__` plan or chronicle collides with a THEIRS number, keep THEIRS. Rename OURS to `YYYY-MM-DD__<slug>.md` with its own date and slug. Repair paired records, research, and cross-references. When date names collide, reconcile the same task or give different tasks distinct slugs.
5. Show every conflict with file, code, action, and classification. Ask once: Approve / Modify / Abort. Abort writes nothing.
6. Apply approved AUTO actions; report only counts and failures.
7. For each JUDGMENT file, show exact OURS and THEIRS hunks plus the proposed merge. Ask Approve / Edit / Skip; Skip leaves it conflicted.
8. A file failure stays conflicted and goes under `Skipped`; continue with others.
9. Verify no tracked conflict markers, valid file names and references when relevant, and known build/lint checks.
10. Report `N resolved: X AUTO, Y JUDGMENT; Skipped: …`, then hand off to `/commit` without committing. Stop on failed checks.

On Codex, translate gates with [codex-tools.md](../using-development-skills/references/codex-tools.md).
