# Test Plan -- /work

**Trigger:** `/work [plan-path | plan-name | task description] [--auto]` (and `/quiver:work` should also work)

**Setup:** Git repo with at least one plan in `.claude/plans/` or a `plans/` directory. For the review-fix path: a plan with `review_source` frontmatter pointing at an existing `.claude/reports/review-*.md` file.

**Expected behavior:**
1. Skill runs four git shell blocks plus the silent Glob over `.claude/plans/` and `**/plans/*.md`.
2. Phase 1 loads the plan via Case A/B/C, printing the executing-plan banner before proceeding.
3. Phase 0 NO_GIT handling skips branch creation, commits, and PR steps cleanly.
4. Phase 2.5 announces the strategy (sequential or parallel) and task count before continuing.
5. For review-fix plans, Phase 4c parses findings, applies BLOCKING/WARNING gates, and prints the convergence verdict; Phase 4d is skipped automatically.
6. Phase 5 invokes the `commit` and `create-pr` skills, gating each action with `AskUserQuestion`. 5b prints the `/quiver:review --base <default branch>` command as text before its question and never invokes it -- `review` carries `disable-model-invocation: true`, so the Skill tool blocks the call -- and the question offers only the PR button and Done.
7. A 3+ task plan creates `.claude/work/<plan-basename>/progress.md` with the identity line before the first group dispatches; a successful run through Phase 5 offers to delete it.
8. Phase 2.5 prints a `Verification:` line naming the resolved test and build commands or `none` with a reason, before any code changes.
9. Phase 3 prints a `red:` line naming the new test before each task's implementation edit, then a pass line; a `none` resolution prints one `skipped:` line for the run and no `red:` line.
10. A task whose tests still fail after three runs past the implementation stops as a blocker; in auto mode it prints the accepted notice and the run continues.
11. `/work <plan> --auto` on the default branch reaches no `AskUserQuestion` from load to summary when no task blocks: the branch is created, every commit lands, 5b prints the `/quiver:review` and `/create-pr` commands as text, the 5d summary ends on them, and the workspace is kept.
12. `--auto` is stripped before the path is read, so `/work .claude/plans/x.md --auto` loads `x.md` through Case A.
13. A PR requested later in the same session, after either an interactive or an auto run, goes through the `create-pr` skill even when a description was drafted during the run; no bare `gh pr create`.

**Verification checklist:**
- [ ] Slash menu shows `/work`; plan banner printed before code changes.
- [ ] Orchestration decision line appears for every plan (including 1-2 task plans).
- [ ] Non-git directory: plan loads and Phases 3-4 run; Phase 5 exits without commit/PR.
- [ ] Review-fix plans: verification table and convergence verdict shown; non-review-fix plans skip Phase 4c.
- [ ] Commit and PR steps both go through `AskUserQuestion`; skill never auto-pushes.
- [ ] Interrupting a run after Group 0 and re-invoking /work on the same plan re-dispatches no task carrying a complete line, and prints which tasks it skipped.
- [ ] A ledger whose identity line names a different plan file is left untouched and a suffixed workspace is used instead.
- [ ] Workspace deletion goes through AskUserQuestion and is verified by a re-list.
- [ ] Phase 4a item 1 output quotes an exit code and a summary line, never a bare "tests pass"
- [ ] A project with no resolvable test command reaches Phase 5 with `Tests: skipped -- <reason>` in the summary and no pass claim
- [ ] The 5d summary carries one `TDD:` line with a red-verified count and a skipped count.
- [ ] Every `AskUserQuestion` site has an auto-mode branch ahead of it, and no auto-mode branch answers a blocker, a contradiction, a Critical finding, or a merge conflict.
- [ ] Auto mode never pushes and never opens a PR.
- [ ] No `gh pr create` is run by /work or by the session it leaves behind; the `create-pr` skill is invoked instead, with any description drafted during the run as its input.

**Known gotchas:**
- Phase 4c parses the synthesized report format from the review skill; the SYNC comment must stay paired with the matching marker in `skills/review/SKILL.md`.
- For 3+ task plans the orchestrator (`skills/work/orchestrator.md`) replaces Phase 3; do not run Phase 3's TodoWrite loop alongside it.
- `git add .` is banned; always stage explicit file paths.
- The orchestration workspace survives a blocked, failed, or cancelled run on purpose -- that is what makes the next invocation resumable.
- The ledger, not the printed progress table, is the authority after a compaction.
- The resolution table lives in `skills/verification/SKILL.md`; this file names it and never restates it.
- The cycle and the `red:` evidence form live in `skills/tdd/SKILL.md`; this file names it and never restates it.
