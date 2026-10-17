---
name: ship
description: Use when all plan tasks are done and green to review, archive planning artifacts, and ask how to finish.
---
# Ship

If `topology=multi-module` (triage announcement or coordinator spec/plan declaration), read `../references/multi-module.md`.

**Gates — if any fail, stop here:**

- Tests pass — or, for tasks with no automated test, their manual acceptance was performed.
- No `- [ ]` remains in any relevant plan.
- Staging spec reflects actual code behavior.
- README commands runnable; living docs honor North Star (atemporal ground truth, modular specs; see `../references/quality.md`).
- No incomplete tracked tasks in the harness task tracker (whatever the host calls it).
- For multi-module work: module plans and local acceptance are complete, and coordinator integration passes (or the change is reported as `partial-commit`).

1. `review` the whole diff.

2. **Update `docs/ROADMAP.md`** (if it exists):
   - Milestone completed? Mark `[x]`.
   - Scope changed? Adjust upcoming milestone descriptions.
   - Unrelated work (bugfix, refactor)? Roadmap unchanged.

3. `archive` — for multi-module work, archive module artifacts in their owning repositories first; archive the coordinator last.

4. If user-visible, add to CHANGELOG `Unreleased`. Releases move it to a version.

5. Ask disposition: **commit / merge / PR / keep / discard.**  
   For a linked multi-repository implementation whose approved plan already includes linked commits: run the commit protocol (non-coordinators in dependency order, record SHAs as the revision set, coordinator last, shared change-set ID in every commit) when the user chooses **commit** or previously approved that path — do not re-ask whether commits are in scope. Still never push or open a PR without explicit approval.

If a linked commit fails, report `partial-commit`, preserve all commits and working trees, and report the exact recovery point.

6. On merge or PR: clean up worktree, delete local branch.

7. Roadmap has unchecked milestones? → `plan` next.

No push or PR without explicit user approval.
