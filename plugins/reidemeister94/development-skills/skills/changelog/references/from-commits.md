# changelog · from-commits

Derive `[Unreleased]` entries from Conventional Commits. Load `writing-guidelines.md` (mapping + filter + aggregation). Pre-flight + insertion: `SKILL.md` Steps 2–3.

## 1 — Range

```bash
git tag --sort=-version:refname 2>/dev/null | head -5
```

- ≥1 tag → `<latest-tag>..HEAD`.
- No tag but a prior `## [X.Y.Z]` section → `git log --grep="release.*X\.Y\.Z" -iE -1 --format=%H`; ≥1 hit → lower bound; 0 hits → next branch (do NOT default to all commits).
- No baseline → `git rev-list --count HEAD`, print N, `AskUserQuestion`: `all N | last 30 | last 100 | other (SHA/tag/count)`. No silent default.

## 2 — Gather

`git log --oneline <range>`, then `git log --pretty=format:"%h %s%n%b%n---" <range>` (BREAKING footers live in bodies).

## 3 — Classify → filter → aggregate → normalize

Apply `writing-guidelines.md`. De-duplicate against entries already in `[Unreleased]`.

## 4 — Propose & confirm

Show entries grouped by category, plus what was skipped and what was aggregated (with one-line reasons). Ask in plain text: *"Approve, edit, or drop any? Reply with edits or 'all good'."* Wait for approval; re-print on changes.

## 5 — Insert & confirm

Apply `SKILL.md` Step 3 per approved entry (preserve existing `[Unreleased]` entries). Print: path, final `[Unreleased]`, tally (N scanned / M proposed / K skipped / J aggregated). Hint: `/changelog release`.
