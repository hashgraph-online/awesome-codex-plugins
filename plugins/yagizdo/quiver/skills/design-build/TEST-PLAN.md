# Test Plan -- /design-build

**Trigger:** `/design-build`, `/design-build .claude/plans/2026-08-16-wallet-design-plan.md`, `/design-build <plan> --auto`, `/quiver:design-build`

**Setup:**
- A design plan written by `/quiver:design` with at least two tasks, one node carrying a `Reconciliation:` line, and reference PNGs present under `screenshot_dir`.
- A second, legacy plan carrying neither `commit_strategy` nor `verify_gate`.
- A runnable project.

**Expected behavior:**
1. All three shell blocks exit 0 in a git repo and in a non-git directory.
2. With no design plan on disk, Phase 1 prints the `/quiver:design` pointer and stops.
3. A plan lacking `design_source: figma-bridge` or `### Node Specs` is rejected with a message; no code is written.
4. The legacy plan loads and builds on the documented defaults, committing nothing.
5. A node with a `Fit:` axis of `fill` is implemented with the framework's fill mechanism, not the `Box:` literal.
6. A node with a `Content:` line carrying an i18n key produces that key, never invented copy.
7. No capture, screenshot, or image-comparison command runs anywhere in the run, and no run session is opened.
8. Phase 4 prints `Design match: skipped -- nothing measured the built UI` exactly once, on every run, including a run in which every task cleared its gate.
8c. On the default branch with an existing `design/<slug>`, the run checks that branch out instead of failing at `git checkout -b`. With a dirty working tree it stays on the current branch and says so.
9. A node with a `Reconciliation:` line and a precedent `file:line` causes that file range to be read before the positioning code is written.
10. A node with a `Reconciliation:` line and `No precedent found` produces content constrained to the chrome-excluded region, with a comment naming what it centers within.
11. After three failed gate attempts on one task, `AskUserQuestion` appears with the four options. The loop never continues silently.
11b. In auto mode the same point accepts the failure, prints the one-line notice, and continues to 3d without asking. The 3-attempt budget is not extended.
12. "Try 3 more attempts" resets the counter; nothing else does.
13. `verify_gate: build` or `test` runs that command before the commit; a failure blocks the commit and re-enters 3c. The gate runs at most twice per task, and "Accept as-is" after a gate failure moves on instead of re-running it -- a permanently failing gate never loops. A gate whose command resolves to `none` records `failed` with the reason and never enters 3c.
14. `commit_strategy: none` or absent writes no commit and says so exactly once.
15. `commit_strategy: per-task` produces one commit per task, skipping any task whose gate verdict is `failed`; `single` produces exactly one commit after the last task, and none at all if any task's gate failed. The plan and `screenshot_dir` are never staged.
15b. "Skip this task" restores the modified files and deletes the created ones when git is available, and leaves them in place with a stated reason under `NO_GIT` or on files an earlier task also wrote.
16. Phase 4 prints the status table, the `Design match: skipped -- nothing measured the built UI` line, every accepted check failure, and ends with the four-button handoff.
17. `--auto` is stripped before a plan path is resolved, and `/design-build --auto` with several plans on disk takes the most recent and names the count instead of asking.
18. A full `/quiver:design --auto` run reaches no `AskUserQuestion` after `/quiver:design` Step 8, all the way to the Phase 4 summary.
19. The auto handoff prints the `/quiver:review`, `/commit`, and `/create-pr` commands as text and invokes none of them.
20. `--no-commit` against a plan carrying `commit_strategy: per-task` writes no commit, says so once, and leaves the plan file unchanged. Re-running the same plan without the flag commits normally.
21. `--no-commit` works with or without `--auto`, and `--auto` works without `--no-commit`.

**Verification checklist:**
- [ ] `/design-build` and `/quiver:design-build` both appear in the slash menu after plugin reload.
- [ ] All three `!` blocks exit 0 with `NO_GIT` output in a non-git directory.
- [ ] No figma-bridge tool is called anywhere in this skill.
- [ ] No capture command, tolerance value, or check order appears anywhere in this file.
- [ ] No screenshot binary or capture MCP server is named anywhere in this file.
- [ ] The plan frontmatter fence is not reproduced; only the fields this skill reads are listed, each with a default.
- [ ] The retry budget is capped at 3 and only the user can reset it.
- [ ] The gate runs at most twice per task and never re-runs after "Accept as-is".
- [ ] Phase 4 carries the `Design match: skipped -- nothing measured the built UI` line on every run.
- [ ] The bounded-retry prompt uses `AskUserQuestion`, not plain text -- and is unreachable in auto mode.
- [ ] Every `AskUserQuestion` site in this skill has an auto-mode branch ahead of it.
- [ ] The interactive handoff prints `/quiver:review` as text and offers no review button; `commit` and `create-pr` are invoked as skills.
- [ ] Auto mode changes no gate verdict and no commit rule.
- [ ] No commit is written when `commit_strategy` is absent.
- [ ] `--no-commit` overrides the plan for the run and never edits the plan file.
- [ ] Commits stage task files only; no `git add .`; plan and reference assets excluded.
- [ ] No AI attribution in any commit message.
- [ ] `when-to-use:` is a single-line double-quoted string.
- [ ] No `CLAUDE_PLUGIN_ROOT` reference anywhere in this file.
- [ ] No Unicode characters or emoji in this file.
- [ ] No `$()`, variable assignment, or `if/else` inside any `!` block.

**Known gotchas:**
- The retry budget is this skill's own state. It counts gate attempts per task and lives nowhere on disk, so a re-run of the same plan starts every task at attempt one.
- `Design match: skipped -- nothing measured the built UI` is a fixed string, not a computed result. A run that quietly drops it reports a build as if its fidelity had been checked.
- The plan's per-node measurement specs and reference images are still written and still read at 3a. They are the implementation's source of numbers; nothing measures the result against them.
- Reference images live under `.claude/plans/assets/<slug>/`. If `.claude/` is gitignored they stay local, which is intended -- never stage them.
- Undoing a skipped task's changes only removes what that task wrote, and only when git can restore them. A task whose files an earlier task also touched cannot be cleanly skipped; when that happens, say so rather than hand-unpicking interleaved edits.
- `commit_strategy: single` still has to skip when `NO_GIT`. The accumulate branch is easy to write as if git is always present.
