---
name: ship
description: Use when all plan tasks are done and green to review, archive planning artifacts, and ask how to finish.
---
# Ship

**Gates — if any fail, stop here:**

- Tests pass — or, for tasks with no automated test, their manual acceptance was performed.
- No `- [ ]` in `docs/staging/plans/YYYY-MM-DD-<topic>.md`.
- Staging spec reflects actual code behavior.
- No incomplete TodoWrite tasks.

1. `review` the whole diff.

2. **Update `docs/ROADMAP.md`** (if it exists):
   - Milestone completed? Mark `[x]`.
   - Scope changed? Adjust upcoming milestone descriptions.
   - Unrelated work (bugfix, refactor)? Roadmap unchanged.

3. `archive` — merge spec into living document (except roadmap), delete staging spec and plan.

4. If user-visible, add to CHANGELOG `Unreleased`. Releases move it to a version.

5. Ask: **commit / merge / PR / keep / discard.**

6. On merge or PR: clean up worktree, delete local branch.

7. Roadmap has unchecked milestones? → `plan` next.

No push or PR without explicit user approval.
