# Test Plan -- /ship

**Trigger:** `/ship` and `/quiver:ship` (Q&A, then build, then verification); `/ship --execute` (hand a saved ship plan to `/work`); `/ship --verify` (verification only)

**Setup (Q&A):** A project description as $ARGUMENTS (e.g., "a Flutter to-do app with Firebase sync"). Optionally a `--seed <spec.md>` file with stack and acceptance criteria. Run from the default branch of a git repository; a non-git directory also works.

**Setup (`--execute`):** A ship plan at `.claude/plans/<date>-<project>-ship-plan.md` with three or more tasks and, for the resume case, a ledger at `.claude/work/<plan-basename>/progress.md` carrying at least one `complete` line.

**Setup (`--verify`):** A ship plan whose branch `/work` has finished, with `test_command` and `build_command` resolved and `run_command` set to a real launch command in one variant and `none` in another.

**Expected behavior:**
1. Shell blocks all exit 0 in both git and non-git directories.
2. Phase 0 reads $ARGUMENTS and presents a 1-2 sentence summary; no AskUserQuestion yet.
3. Phase 1 asks Q&A via AskUserQuestion until all 6 categories plus platform and deployment target are answered; category 6 records a run command or `none`.
4. Phase 2 presents the table with a `Blocked by` column; the approve question says the build stops only for a blocker or a merge conflict.
5. Phase 3 writes the plan in the `skills/plan/SKILL.md` Step 5 format, runs the Step 6 checks, reads the file back, and confirms `## Global Constraints` is present and `**Provides:**` lines are present exactly on the tasks another task names by symbol -- none when no symbol crosses tasks.
6. "Approve -- build it" flows Q&A -> plan -> `/work --auto` -> verification -> report in one invocation; no question is asked between approval and the report unless a task blocks or a merge conflicts.
7. "Approve the plan only" writes the plan, prints the `/ship --execute` command, and terminates without building.
8. Execution invokes `work` through the Skill tool with the plan path and `--auto`; ship creates no branch and calls no Agent.
9. `/ship --execute` on a plan with a ledger re-dispatches no task carrying a `complete` line; on a plan without one, `/work` starts from the first task.
10. A second bare `/ship` finds the plan and offers Resume / Start fresh / Inspect, with the state read from the `status` field first and the ledger second; a finished plan whose ledger survived auto mode reads as finished.
11. Verification Steps 1-2 quote an evidence line each, or a skipped reason; a zero-test run is `skipped`, never `pass`.
12. Verification invokes no `review` and no second `work`; the report's Review line and What's Next name `/quiver:review --base <default branch> --plan <plan path>` for the user to run.
13. Verification Step 3 launches the app only when `run_command` is not `none`; otherwise it prints `Smoke: skipped -- no run command`.
14. The report lands at `.claude/reports/ship-<project>-<timestamp>.md`; a second `--verify` adds a file and overwrites nothing.
15. A second "Start fresh" on the same day writes `<date>-<project>-ship-plan-2.md`; the first plan and its ledger are untouched, and the Step 1 Glob finds both.

**Verification checklist:**
- [ ] `/ship` and `/quiver:ship` both appear in the slash command menu after plugin reload.
- [ ] All five shell blocks exit 0 in a git repo; all five exit 0 (with NO_GIT output) in a non-git directory.
- [ ] No plain-text questions to the user -- every user prompt uses AskUserQuestion (R5).
- [ ] The plan frontmatter carries `stack`, `platform`, `deployment_target`, `test_command`, `build_command`, and `run_command`, none empty.
- [ ] Phase 1 category 3 lands in the plan: the tech-stack half in `stack`, the restrictions under `## Global Constraints`. A user who answered "no ORM, raw SQL only" can find that sentence in the plan.
- [ ] Every task carries `**Files:**`; every task another task names carries `**Provides:**`; no task carries a `none` placeholder.
- [ ] Plan read back after the write (L3); report read back after the write.
- [ ] Ship invokes `work` through the Skill tool, never invokes `review` (its `disable-model-invocation: true` refuses the call), and never calls the Agent tool itself.
- [ ] Ship never creates a branch, never commits, never pushes, and never opens a PR; `/work --auto` commits, and pushes or opens nothing.
- [ ] A PR asked for after the run is opened by the `create-pr` skill, not by a bare `gh pr create`, even when the run drafted a description.
- [ ] The `work` invocation carries `--auto`; a run with no blocker reaches the report with no question after Phase 2.
- [ ] `--execute` with no ship plan terminates with a message; no prompt.
- [ ] `--execute` + `--resume` together: `--resume` wins; the Step 1 Resume path runs.
- [ ] `--verify` + `--resume` together: `--resume` wins.
- [ ] `--verify` runs only the verification phase and changes no plan field.
- [ ] The report's Review line carries `--base` and `--plan`; ship prints the command and runs nothing.
- [ ] No `CLAUDE_PLUGIN_ROOT` references in this file (R4).
- [ ] No Unicode characters or emoji in this file (R8).
- [ ] No new inline `!` shell blocks beyond the five git blocks (R3).
- [ ] `when-to-use:` field is a single-line double-quoted string (R10).
- [ ] All `!` shell blocks use git commands only; no `||` with non-git commands (L1).
- [ ] This file names `skills/plan/SKILL.md`, `skills/verification/SKILL.md`, and `skills/tdd/SKILL.md` and restates none of them.

**Known gotchas:**
- Plugin auto-discovery requires a plugin reload after the skill is first installed. `/ship` will not appear in the slash menu until the plugin reloads.
- The Glob for `.claude/plans/*-ship-plan*.md` returns empty on the first run -- the skill must not abort on this empty result.
- `.claude/plans/` and `.claude/work/` are the same directories `/plan` and `/work` use, so a ship plan is visible to `/work` Case B's plan picker and resumes from the same ledger. That is the point: ship writes a plan, not a format of its own.
- Phase 2's approval is the run's last routine question because `/work --auto` answers the rest from it. The questions that survive -- a blocker, a merge conflict -- are the ones whose answer changes what gets built; ship must not answer those for the user, and must not add a flag that skips them.
- The three-attempt fix cap lives in `/work` (Phase 3 and the orchestrator prompt), not here. Ship adds no retry of its own; in auto mode both of `/work`'s paths accept a task that fails its third run -- the orchestrator's FAILED handling leaves its dependents paused and lists all of them -- and they show up in `/work`'s summary and again under the report's Open Items.
- Starting ship on a feature branch makes `/work --auto` continue on that branch. Start on the default branch when the build should land on a fresh one.
- The task format, its `**Provides:**` field, and the Step 6 plan checks live in `skills/plan/SKILL.md`; `tests/skills/test-task-interfaces-contract.sh` pins the `**Provides:**` label and the check count there, and this file carries no count of its own. Restating them here is the drift this rewrite removed.
- The verification and TDD subagent restatements are pasted only into `skills/work/orchestrator.md`. Ship dispatches no subagent, so it carries neither; the contract tests check the orchestrator's copy alone.
- The review is the user's, not ship's. `skills/review/SKILL.md` carries `disable-model-invocation: true`, so the Skill tool refuses a `review` call from ship -- an earlier draft made that call and could never have run. The report names the command with `--base` so `/quiver:review` does not prompt for the base branch on a feature branch, and `--plan` so its Step 1.8 finds the Global Constraints; dropping either makes the user's pass interactive or blind to the constraints.
- A `/work` run that ends blocked keeps its ledger on purpose; `/ship --execute` is the retry, and the ledger is what makes it cheap.
- The Skill tool does not return. Invoking `work` loads its file into the conversation and the run continues inline; the only end signal is `/work`'s Phase 5d summary. A 2026-09-16 run with several blocker stops ended the turn on that summary and never verified. The Continue step is keyed to the summary for that reason, and `/work` 5d names the caller's continuation; `/ship --verify` re-enters when a turn still ends there.
