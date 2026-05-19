---
name: ship
description: Use when all plan tasks are done and green to review, archive planning artifacts, and ask how to finish.
---
# Ship

**Gates — if any fail, stop here:**

- Tests pass.
- No `- [ ]` in `docs/staging/plans/YYYY-MM-DD-<topic>.md`.
- Staging spec reflects actual code behavior.
- No incomplete TodoWrite tasks.

1. `review` the whole diff.
2. `archive` — merge spec into living document, delete staging spec and plan.
3. If user-visible, add to CHANGELOG `Unreleased`. Releases move it to a version.
4. Ask: **merge / PR / keep / discard.**
5. On merge or PR: clean up worktree, delete local branch.

No push or PR without explicit user approval.
