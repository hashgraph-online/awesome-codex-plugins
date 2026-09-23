---
name: work
description: "Execute a work plan or specification systematically -- read the plan, set up a branch, implement tasks with continuous testing, commit incrementally, and ship a PR. Use when you have a plan file, spec, or task list ready to execute. --auto answers the routine gates (branch, final commit, PR handoff, workspace cleanup, third failed fix attempt) in advance and stops only for a blocker, a Critical finding, or a merge conflict."
argument-hint: "<plan file path or task description> [--auto]"
when-to-use: "user wants to execute a saved plan or implement tasks step by step -- '/work', '/work --auto', 'start implementation', 'execute the plan', 'work through these tasks', 'run the plan without stopping to ask'"
---

# Gather Context

```
!`git rev-parse --is-inside-work-tree 2>/dev/null || echo "NO_GIT"`
```

```
!`git branch --show-current 2>/dev/null || echo "NO_GIT"`
```

```
!`git log --oneline -5 2>/dev/null || echo "NO_GIT"`
```

```
!`git status --short 2>/dev/null || echo "NO_GIT"`
```

---

# Work

Execute a work plan, specification, or task list systematically. The focus is on shipping complete features by understanding requirements quickly, following existing patterns, and maintaining quality throughout.

**Announce:** "Using the work skill to execute the plan."

**Arguments.** `--auto` anywhere in `$ARGUMENTS` sets **auto mode** for this run. Strip it before Phase 1 reads the rest as a path or description. Auto mode pre-answers the routine gates and nothing else: the branch question in Phase 2 (continue on the current branch), the third failed fix attempt in Phase 3 and in the orchestrator's FAILED handling (accepted and listed; an orchestrated failure's dependents stay paused), the final commit in 5a (committed without the prompt), the handoff in 5b (no review, no PR -- the commands are printed as text), and the workspace in 5c-bis (kept). It answers no question whose answer changes what gets built or deletes something: a plan contradiction (1e), a blocker (Phase 3), an unaddressed Critical finding or unmet acceptance criterion (4c), and a merge conflict stop and ask exactly as they do without the flag. `/ship` passes it so a run that answered every question up front is not stopped for a routine one; a user can pass it directly for the same effect. Every `AskUserQuestion` site below names its auto-mode branch; a prompt added any other way stalls an auto run.

**Before starting Phase 1**, use the Glob tool to gather plan context silently (do not show results to the user):
1. `.claude/plans/*.md` -- existing plans
2. `**/plans/*.md` (max depth 4) -- plans in other locations

Treat empty Glob results as "no plans found". Proceed regardless.

**Use when:** a plan file exists, the user provides a spec or task list, or the user says "execute", "build this", "implement the plan". Use `/quiver:plan` first if no plan exists yet. Use `/quiver:review` for code review.

---

## Workflow

```
+----------+     +---------+     +---------+     +---------+     +--------+
| 1. LOAD  | --> | 2. SETUP| --> | 3. BUILD| --> | 4. CHECK| --> | 5. SHIP|
| Read plan|     | Branch  |     | Execute |     | Quality |     | PR     |
+----------+     +---------+     +---------+     +---------+     +--------+
```

### Phase 0: Git Availability

If any gather-context block above returned `NO_GIT`, this directory is not a git repository.
Print: `> No git repository detected -- skipping branch/commit context.`
Proceed to Phase 1. Treat all git-sourced fields (branch, log, diff, status) as empty. Skip branch creation in Phase 2, commit steps in Phase 3, and git-dependent actions in Phase 5.

### Phase 1: Load and Clarify

#### 1a -- Load the plan

**Case A: Path provided.** If `$ARGUMENTS` is a file path (ends in `.md` or contains `/`):
- Read that file as the work plan.
- Print: `> Executing plan: {plan filename} ({step count} steps) on branch {branch}`
- Proceed directly to Phase 1b. The user chose this plan explicitly -- no confirmation needed.

**Case B: No arguments.** If `$ARGUMENTS` is empty, collect all `.md` files from every `plans/` directory discovered by the Glob block above, plus the `.claude/plans/` listing.

- If exactly one plan exists across all directories, read it and use `AskUserQuestion`:
  > Found one plan: `{relative path}` (in `{directory}`)
  > **Goal:** {goal from plan}
  > **Steps:** {step count}
  Buttons: `["Execute this plan", "Other -- I'll provide a path or description"]`
- If multiple plans exist, present them via `AskUserQuestion` with full relative paths as buttons (most recent first), plus an `"Other -- I'll provide a path or description"` option. Show the directory in each label so the user can distinguish plans in different locations.
- If the user picks "Other", ask for a path or task description.

If no plans found:
> No plans found in any `plans/` directory. Usage:
> - `/work <path-to-plan.md>` -- execute a specific plan
> - `/work <plan-name>` -- search for a plan by name
> - `/work <task description>` -- work on a task directly
> - `/plan <task>` -- create a plan first

**Stop here.**

**Case C: Name or description provided.** If `$ARGUMENTS` is not a file path and is not empty:

1. **Discover plan files.** Read every `plans/` directory discovered by the Glob block. Combine with `.claude/plans/` listing.
2. **Match by filename.** Compare `$ARGUMENTS` against each plan file's stem (without `.md` extension):
   - **Exact match:** stem equals `$ARGUMENTS` (case-insensitive).
   - **Partial match:** stem contains `$ARGUMENTS` as a substring (case-insensitive).
3. **Rank and select.** Rank exact matches above partial matches.
   - **1 match** -- Read the plan file, print `> Executing plan: {filename} from {directory}`, proceed to Phase 1b. No confirmation needed.
   - **Multiple matches** -- Use `AskUserQuestion` to present candidates with full relative paths as button labels. Add a `"None of these -- treat as task description"` button.
   - **0 matches** -- Treat `$ARGUMENTS` as an inline task description. Print `> No matching plan found for "{$ARGUMENTS}". Treating as task description.` Proceed to Phase 1b with the description as the work specification.

#### 1b -- Review references

If the plan links to files, patterns, or prior research -- read those now. Understanding context before coding prevents rework.

If the plan carries a `## Global Constraints` section, read it as binding context for every task in this run, not as background prose -- it states what this work must not do.

#### 1c -- Detect review-fix plan

Check if this is a plan created to address review findings:
- **Primary**: Check plan YAML frontmatter for a `review_source` field (e.g., `review_source: .claude/reports/review-2026-03-10_14-30-00.md`).
- **Fallback**: Scan plan content for paths matching `.claude/reports/review-*.md` or `review-*_*-*-*.md`.
- If detected, read the review report file. If the file exists, note this as a **review-fix plan** and carry the parsed findings forward to Phase 4. If the file does not exist, warn: "Review report not found at {path}. Proceeding without review-aware verification."
- If no review reference detected, proceed normally.
- **Iteration tracking**: Read the plan's `review_iteration` frontmatter field (default: `1` if absent). If `review_iteration >= 2`, this is the **final iteration** -- Phase 4c verification is the only quality gate, and Phase 4d agent review is skipped unconditionally.

#### 1d -- Flag ambiguities

If the plan contains genuine contradictions (e.g., two steps that conflict, a referenced file that does not exist), note them. If the plan is clear, skip this step entirely -- do not invent ambiguities.

#### 1e -- Proceed or clarify

- **No plan found:** Ask the user what to work on.
- **Plan has contradictions** flagged in 1d: Ask about those specific contradictions only.
- **Plan is clear:** Move directly to Phase 2. Do NOT ask "should I proceed?", "are you sure?", "shall I start?", or any variation of confirmation. The user invoked `/work` with a plan -- that IS the approval. Summarizing the plan back and asking to continue is wasted time.

### Phase 2: Setup Environment

**If git is NOT available (Phase 0 detected `NO_GIT`):** Skip this phase entirely -- proceed to Phase 2.5.

**If already on a feature branch** (not main/master), use `AskUserQuestion`:
> You're on `{branch}`. Continue here or create a new branch?
Buttons: `["Continue on {branch}", "Create new branch"]`
If continuing, move to Phase 2.5. In auto mode, continue on the current branch without asking.

**If on the default branch**, create a new branch by default: `git checkout -b <meaningful-name>` using a descriptive name (e.g., `feat/user-auth`, `fix/email-validation`). Never commit to the default branch without explicit user confirmation.

### Phase 2.5: Orchestration Decision

Parse the plan and count top-level tasks (one deliverable = one task, regardless of markup format). Announce before proceeding:
```
Strategy: {sequential | parallel orchestration} ({N} tasks found)
Reason: {why}
```

#### Resolve the verification command

Read `skills/verification/SKILL.md` and follow its `## Command Resolution` section. This runs for every plan, sequential and orchestrated alike, once per run, before the strategy split below, so both paths carry the value. Print one line under the strategy line:

```
Verification: test <command | none (<reason>)>, build <command | none (<reason>)> (source: docs | stack | none)
```

The orchestrator copies the test value into every brief's `Test command:` line. `none` is printed as-is and carried forward -- it is never replaced by a guess.

Then split on the task count:

- **1-2 tasks:** Sequential. Proceed to Phase 3 with the verification command resolved above. The ledger below is orchestration-path-only; the sequential path keeps TodoWrite unchanged and writes nothing to disk.
- **3+ tasks:** Parallel orchestration. Resolve the workspace and check for a ledger (below), then follow `skills/work/orchestrator.md`. Skip Phase 3 entirely -- orchestration replaces it.

#### Resolve the workspace

`<plan-basename>` is the loaded plan file's name without `.md`. The workspace is `.claude/work/<plan-basename>/` and the ledger is `.claude/work/<plan-basename>/progress.md`.

Any path that reaches Phase 2.5 without a plan file has no plan basename -- Phase 1 Case B's "Other -- I'll provide a path or description" and Case C with 0 matches both do. Derive one instead of proceeding without it: slugify the task description to at most 40 characters and use `.claude/work/adhoc-<slug>/`. The workspace and ledger are otherwise identical, and the identity line names the task description in place of a plan file path. The orchestrator requires a workspace for every run -- every dispatch step writes to one. Name the derived workspace in the strategy line.

#### Check for a ledger

Read `.claude/work/<plan-basename>/progress.md`. Its first two lines are the identity header:

```
# work ledger -- plan: <full plan file path>
# run: <ISO-8601 start timestamp>
```

The `run:` line names the run that owns the workspace, and Phase 5c-bis checks it before deleting anything -- the plan path alone cannot separate this run from another session working the same plan.

Apply these rules, which restate `skills/work/orchestrator.md` Section 0:

| State | Action |
|-------|--------|
| No file, or a file whose first two lines are not a `# work ledger -- plan:` line followed by a `# run:` line | Fresh run. Create the directory if needed, overwrite the file with the identity header. Do not suffix -- a directory with no identity claims no plan. |
| First line names this plan file, and every completion line's task number and title match the plan | Resumable. Do not re-dispatch any task carrying a `Task <N> [<task title>]: complete (branch <branch>, commits <base7>..<head7>)` line. Merge a completed task's branch unless a `Task <N>: merged` line also exists for it -- a `complete` line records that the work was done, not that it landed. A complete line reading `commits none` has no branch to merge. Resume dispatch at the first task with no matching `complete` line. Overwrite the `# run:` line with this run's start timestamp and read it back -- the workspace now belongs to this run. |

For a ledger naming a different plan file, or a completion line whose title no longer matches the plan, `skills/work/orchestrator.md` Section 0 "Resume rules" is authoritative -- follow it there and print the line it requires.

#### Announce

When tasks are skipped:
> Resuming the previous run: skipping Task 1, Task 2 (already complete).

When the ledger is stale:
> Plan changed since the last run -- starting fresh.

When a suffixed workspace is used:
> Another plan's run already uses that folder name -- using .claude/work/<name>-2/ instead.

### Phase 3: Build

Break the plan into TodoWrite tasks (specific, dependency-ordered, with testing tasks included). For each task: mark `in_progress`, read referenced files, match existing patterns, then follow the cycle in `skills/tdd/SKILL.md`: write the test the task's test step names, run the resolved test command, and print its `red:` line (this run's exit code, the new test's name, its first error line); implement; run the resolved command again and print its pass line. Fix failures before moving on, within three runs after the implementation exists -- the red run is not one of them. A task still failing after the third run is a blocker under the rule below; in auto mode it is accepted instead: print `Task {N}: still failing after 3 attempts -- accepted`, list it in the 5d summary, and continue to the next task. The budget is never extended on its own. When the command resolved to `none`, print `skipped: test command none (<reason>)` once for the run and skip the red step on every task; when a task produces no testable behavior, print `skipped: no testable behavior (<what the change is>)` for that task. Then mark `completed` and update plan checkboxes if present.

Every task on this path is subject to the plan's `## Global Constraints` when the plan carries one: a task that cannot be completed without violating a constraint is a blocker, handled by the Blockers rule below.

**Commits:** After each logical unit, commit if the evidence line is a pass and the change is meaningful (`git add <specific files>` -- never `git add .`). Wait if tests fail or the message would say "WIP". Heuristic: "Can I write a message describing a complete, valuable change?"

**Blockers:** Stop immediately. Note in TodoWrite. Ask the user. Do not proceed until resolved.

### Phase 4: Quality Check

Before shipping, verify the work meets standards.

#### 4a -- Core checks (always run)

1. **Tests pass.** Run the test command resolved in Phase 2.5 and quote the evidence line from this run -- exit code and the runner's summary line, per the `## Evidence Rule` section of `skills/verification/SKILL.md`. A claim without that line is not a pass. When the command resolved to `none`, this item is a WARNING, not a block: print `Tests: skipped -- <reason>` here and again in the 5d summary.
2. **Linting passes.** Run the project's lint command if one exists.
3. **All TodoWrite tasks marked completed.** No tasks left in progress.
4. **Code follows existing patterns.** No new conventions introduced unless the plan explicitly called for them.
5. **No uncommitted changes** that belong to this work.
6. **Plan checkboxes updated** (if applicable).
7. **Post-merge test suite passes** (when orchestration was used), using the same resolved command and quoting its evidence line; all worktree branches merged with no unresolved conflicts.

**These are BLOCKING -- fix all before proceeding to Phase 5.**

#### 4b -- System-wide impact check

For non-trivial changes, pause and consider:

| Question | Action |
|----------|--------|
| What else fires when this runs? (callbacks, middleware, observers, hooks) | Trace two levels out from your change. Read the actual code. |
| Do tests exercise the real chain? | If every dependency is mocked, add at least one integration test using real objects. |
| Can failure leave orphaned state? | If state is persisted before an external call, test the failure path. |
| What other interfaces expose this? | Grep for the method/behavior in related classes. Add parity if needed. |

**Skip this check for:** leaf-node changes with no callbacks, no state persistence, no parallel interfaces. Purely additive changes (new helper, new partial) need only a quick scan.

**WARNING (review but do not block):** linting warnings present; no integration tests for changes touching callbacks or middleware; plan acceptance criteria not explicitly verified (NOTE: for review-fix plans, acceptance criteria are BLOCKING per Phase 4c step 6).

#### 4c -- Review finding verification (review-fix plans only)

If Phase 1 identified this as a review-fix plan and the review report was successfully loaded:

1. **Parse findings.** Extract all non-filtered findings from the review report, grouped by severity (Critical, High, Medium, Low). Skip the `## Filtered Findings` section entirely.

2. **Map findings to plan steps.** Match each finding to a plan task by file path or title/description. Findings with no matching plan step are marked "Not in scope."

3. **Check addressed status.** For each in-scope finding, verify the referenced file was modified (`git diff`) and the corresponding TodoWrite task is `completed`. Both conditions met = **Addressed**; otherwise = **Not addressed**.

4. **Cross-reference check.** Flag when a file modified to fix finding A is also referenced by finding B (potential regression area). Present these as notes, not blockers.

5. **Present verification summary** as a table with columns: ID, Severity, Finding, Status, Notes. Then apply gates:
   - **BLOCKING**: Any Critical finding marked "Not addressed." Use `AskUserQuestion`:
     > Critical review finding not addressed: {finding title}
     > Original finding: {finding text}
     Buttons: `["I've verified this is fixed", "Fix it now", "Skip -- not applicable"]`
   - **WARNING**: Any High/Medium/Low finding marked "Not addressed." List in summary but do not block.
   - **INFO**: Findings marked "Not in scope." Listed for awareness only.

6. **Acceptance criteria check.** If the plan has an `Acceptance Criteria` section, mark each criterion as **Met** or **Not met**. If any are **Not met**, use `AskUserQuestion`:
   > Acceptance criterion not met: {criterion text}
   Buttons: `["Fix it now", "Skip -- criterion is outdated", "Mark as met (I've verified manually)"]`
   All criteria must be **Met** to proceed to Phase 5.

7. **Convergence verdict.** If all in-scope findings are **Addressed** AND all acceptance criteria are **Met**, the review-fix cycle is **COMPLETE** -- proceed to Phase 5, do NOT trigger another review. If `review_iteration >= 2`, the cycle is **COMPLETE** regardless of remaining Low/Medium warnings; only unaddressed Critical findings can block. Print:
   ```
   Review-Fix Cycle Status: Iteration {review_iteration} | Findings {addressed}/{total_in_scope} | Criteria {met}/{total_criteria} | COMPLETE
   ```

<!-- SYNC: This verification parses the report format defined in skills/review/SKILL.md, section `### Synthesized report structure`. If the report structure changes, update the parsing logic here. New sections (What's Working Well, Recommended Fix Order, Senior Assessment) are additive and do not affect this parsing. -->

#### 4d -- Optional: Agent-assisted review

**SKIP this phase entirely if this is a review-fix plan.** The Phase 4c verification is the quality gate for review-fix work. Dispatching review agents on review-fix changes creates infinite loops -- the agents will always find new issues that weren't in the original scope.

For **non-review-fix plans** with large, risky, or security-sensitive changes, consider dispatching review agents. Discover available review agents by scanning `agents/review/*.md` and dispatch them in parallel -- one `Agent` call per agent, all in a single response, the way `skills/review/SKILL.md` Step 2 does it.

**Do not use review agents by default.** Tests + linting + pattern-following is sufficient for most work. Reserve agent reviews for:
- Large refactors (10+ files) that are NOT review-fix plans
- Security-sensitive changes (auth, permissions, data access)
- Complex business logic or algorithms

### Phase 5: Ship

**If git is NOT available (Phase 0 detected `NO_GIT`):** Skip commit and PR steps. Summarize what was completed and remaining follow-ups, then stop.

**CRITICAL: Every git action in this phase requires explicit user confirmation via `AskUserQuestion`. NEVER commit, push, or create a PR without asking first.** Auto mode is the one exception, for the commit alone: the caller's approval stands in for the 5a prompt. Push and PR are never automatic.

**NO ATTRIBUTION: Do not add `Co-Authored-By`, `Generated with Claude`, `Built with AI`, or any similar attribution lines to commit messages or PR descriptions. Only add attribution if the user explicitly requests it.**

#### 5a -- Final commit

If there are uncommitted changes after Phase 4, stage the relevant files (specific files only -- never `git add .`) then invoke the `commit` skill. If the user cancels, do not re-ask or proceed to 5b. In auto mode, commit directly with a Conventional Commits message -- the same rule Phase 3 commits under -- instead of delegating to the prompt.

#### 5b -- Create PR

After committing (or if all commits were already made during Phase 3), print the review command as text:
> Review before merging: /quiver:review --base <default branch>
Add `--plan <plan path>` to that line when the run had a plan file; `<default branch>` is `main` or `master`, whichever the repository has. `skills/review/SKILL.md` carries `disable-model-invocation: true`: the Skill tool blocks a `review` call from this skill and tells the model not to reproduce the review another way, so the review is the user's to run and never a button here. This is the whole review story for `/work`: the run itself dispatches no review agents, because `/quiver:review` on the finished branch sees every task's change together with the synthesis filters a per-task pass would not have.

Then use `AskUserQuestion`:
> All work is committed on `{branch_name}`. What would you like to do next?
Buttons: `["Create a pull request", "Done -- I'll review or handle the rest"]`

- **Create a pull request** -- invoke the `create-pr` skill.
- **Done** -- stop here. Move to 5c.

In auto mode, skip the question and act as **Done**: the review line is already printed; print `/create-pr` beside it, carry both as the last line of the 5d summary, and invoke neither.

`/create-pr` owns the pull request for the rest of the session, in both modes. When the user asks for one after the run -- 'push and open a PR', 'create the PR' -- invoke the `create-pr` skill; never run `gh pr create` from this skill or from the conversation it leaves behind. A description drafted during the run (a rationale document the user asked to put in the PR, a summary of the branch) is input to that skill, which reads it as something the user said in this conversation, not a substitute for it. Only an explicit instruction to skip the skill -- 'open it with gh directly', 'don't use create-pr' -- overrides this.

#### 5c -- Update plan status

If the work document has YAML frontmatter with a `status` field, update it:
```
status: active  -->  status: completed
```

#### 5c-bis -- Clean up the orchestration workspace

Runs only when orchestration was used, every task reached DONE, and Phase 4a check 7 passed. A run that ends blocked, failed, or cancelled skips this step entirely -- the surviving directory is what makes the retry cheap, and deleting it throws away the resume.

1. Resolve `<workspace-dir>` to the directory this run actually used -- the suffixed one (`-2`, `-3`) if the orchestrator's suffix-retry rule fired, otherwise `.claude/work/<plan-basename>/`. Confirm `<workspace-dir>` exists, that its `progress.md` first line names this plan file, and that its `# run:` line is this run's start timestamp. If any check fails, delete nothing and say so -- the directory belongs to a different run, and a `run:` line naming another run means a concurrent session owns it. Never re-derive the path from `<plan-basename>` after this step.
2. Name `<workspace-dir>` and its file count, then gate the delete on `AskUserQuestion`:
   > Orchestration finished and the work is committed. Delete the run workspace at `<workspace-dir>` ({N} files)?
   Buttons: `["Delete it", "Keep it"]`
   On "Keep it", print one line saying it was kept and continue to 5d. In auto mode, keep it without asking and print the same line.
3. On "Delete it", remove `<workspace-dir>` -- the exact path confirmed in step 1 and shown in step 2, no other -- then re-list `.claude/work/` to confirm it is gone, and name what was deleted in the 5d summary.

#### 5d -- Notify user

Summarize:
- What was completed
- Link to the PR (if one was created)
- Any follow-up work needed or remaining tasks, including every task accepted after three failed attempts and every discovered edit the group announcements printed (file and reason), so a change outside the plan's file lists is visible before the PR
- The test-first tally, one line: `TDD: <n> red-verified, <m> skipped (<distinct reasons>)`. The sequential path counts the lines Phase 3 printed; the orchestration path counts the `TDD` lines the group-completion announcements printed. Include this line whenever the run implemented anything.

This summary ends `/work`. It does not end the turn when another skill loaded `/work` through the Skill tool -- `/ship` does, and continues into its verification here -- because that skill's instructions are still in this conversation and its next step runs now. Before ending the turn on this summary, check whether a skill invoked `/work` and follow its continuation step.

---

## Anti-Patterns

- **Don't** skip Phase 1 clarification -- ask now, not after building the wrong thing.
- **Don't** ignore plan references -- the plan has file paths and pattern links for a reason.
- **Don't** save all testing for the end -- test continuously or suffer compounding failures.
- **Don't** use `git add .` -- stage specific files to avoid accidental inclusions.
- **Don't** commit with "WIP" messages -- wait until a logical unit is complete.
- **Don't** force through blockers -- stop, note the issue, ask the user.
- **Don't** over-review simple changes -- save agent reviews for genuinely complex or risky work.
- **Don't** leave TodoWrite tasks unfinished -- track progress or lose track of what is done.
- **Don't** move on at 80% -- finish the feature before starting something new.
- **Don't** commit directly to the default branch without explicit user permission.
- **Don't** commit, push, or create a PR without asking the user first via `AskUserQuestion` -- every git action in Phase 5 requires explicit confirmation.
- **Don't** add AI attribution to commits or PRs (`Co-Authored-By`, `Generated with Claude`, etc.) unless the user explicitly asks for it.
- **Don't** trigger another review cycle after completing a review-fix plan -- Phase 4c verification is the terminal quality gate. Dispatching review agents on review-fix work creates infinite loops.
- **Don't** spawn subagents for 1-2 task plans -- the overhead exceeds the benefit. Use sequential execution.
- **Don't** skip dependency resolution -- check both explicit `blockedBy` and file overlap before dispatching parallel agents; stop dispatching dependent tasks when a dependency fails.
- **Don't** attempt automatic merge conflict resolution -- report conflicts to the user and stop.
- **Don't** answer a blocker, a plan contradiction, a Critical finding, or a merge conflict on the user's behalf in auto mode -- auto covers the routine gates named at the top and nothing else.
- **Don't** extend the three-attempt fix budget on your own, in either mode. A loop that grants itself more attempts has no cap.
