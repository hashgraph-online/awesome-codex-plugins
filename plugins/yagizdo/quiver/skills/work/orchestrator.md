# Orchestrator Reference

This document defines the subagent orchestration logic used by the work skill when a plan has 3+ tasks. It is NOT a standalone skill — it is referenced by `skills/work/SKILL.md` Phase 2.5.

> **Scope:** This document is the reference for subagent orchestration in Quiver -- dependency resolution, worktree isolation, task briefs, and the merge procedure. Any skill that dispatches implementation subagents reads it here.

---

## 0. Workspace and Ledger

Orchestration keeps its state on disk, not in the session. A run that is compacted, interrupted, or resumed reads that state back rather than remembering it.

### Workspace layout

```
.claude/work/<plan-basename>/
  progress.md          -- the ledger
  task-<N>-brief.md    -- one task's requirements, extracted from the plan
  task-<N>-report.md   -- that task's full report, written by the subagent
```

`<plan-basename>` is the loaded plan file's name without `.md`. `skills/work/SKILL.md` Phase 2.5 resolves the workspace before handing off. A run with no plan file takes `adhoc-<slug>` as its basename, slugified from the task description -- every run has a workspace and a ledger, because every dispatch step below requires one.

### Identity header

The first two lines of `progress.md`, in this order:

```
# work ledger -- plan: <full plan file path>
# run: <ISO-8601 start timestamp>
```

When the run has no plan file, the task description takes the place of the path on the first line. The timestamp is taken once, when orchestration begins: `date -u '+%Y-%m-%dT%H:%M:%SZ'`.

The `run:` line names the run that currently owns the workspace. Two sessions working the same plan in the same repo both resolve the same directory and both read an identity line naming their own plan, so the plan path alone cannot tell them apart. The `run:` line can, and `skills/work/SKILL.md` Phase 5c-bis checks it before deleting anything.

### Ledger grammar

Every line after the identity header is one of exactly these seven forms:

```
Group <G>: dispatched (<task numbers>)
Task <N> [<task title>]: complete (branch <branch>, commits <base7>..<head7>)
Task <N> [<task title>]: blocked -- <one-line reason>
Task <N> [<task title>]: failed -- <one-line reason>
Task <N>: merged
Group <G>: merged (<task numbers>, no conflicts)
Group <G>: merge stopped -- conflict in <file list>
```

`Task <N>: merged` records one branch landing. `Group <G>: merged (...)` summarizes the whole group and is written only after every branch in it has landed, so it cannot stand in for the per-task line.

This section is the single source of truth for the grammar. Section 2 and Section 3 append these lines; they do not redefine them.

### Resume rules

At the start of orchestration, read `.claude/work/<plan-basename>/progress.md`:

| State | Action |
|-------|--------|
| No file, or a file whose first two lines are not a `# work ledger -- plan:` line followed by a `# run:` line | Fresh run. Create the directory if needed, overwrite the file with the identity header. Do not suffix -- a directory with no identity claims no plan. |
| First line names this plan file, and every completion line's task number and title match the plan | Resumable. Do not re-dispatch any task carrying a `complete` line. Merge a completed task's branch unless a `Task <N>: merged` line also exists for it -- a `complete` line records that the work was done, not that it landed. A complete line reading `commits none` has no branch to merge. Resume dispatch at the first task with no matching `complete` line. Overwrite the `# run:` line with this run's start timestamp and read it back -- the workspace now belongs to this run. If it named a different run, say so in one line before continuing. |
| First line names a different plan file | Leave that directory untouched. Retry at `.claude/work/<plan-basename>-2/`, then `-3`, and so on, until a directory is found that either does not exist or whose identity line names this plan file. Use that one for the whole run. Print one line naming the directory actually used and why. |
| First line matches this plan file, but a completion line's task title does not match the plan's task at that number, or names a task number the plan does not have | The plan changed mid-run. Warn the user, treat the ledger as stale, and start fresh in the same directory. |

### Cleanup

The workspace is deleted by `skills/work/SKILL.md` Phase 5 after a successful run, never by the orchestrator. A run that ends blocked, failed, or cancelled leaves the directory in place -- that is what makes the next invocation resumable.

### Write discipline

Every ledger append is followed by reading the file back to confirm the line landed (skill rule L3). A ledger write that cannot be verified is reported to the user and orchestration stops -- an unverifiable ledger makes resume unsound.

---

## 1. Dependency Resolution

Dependency resolution determines the order in which tasks execute. It runs three steps, then builds execution groups.

### Step 1 — Explicit Dependencies

Read each task's `blockedBy` field from the plan. This field lists task numbers that must complete before this task can start.

Example plan fragment:

```yaml
- id: 1
  title: Create database schema
  blockedBy: []

- id: 2
  title: Build API endpoints
  blockedBy: [1]

- id: 3
  title: Add input validation
  blockedBy: [1]

- id: 4
  title: Write integration tests
  blockedBy: [2, 3]
```

Here, Tasks 2 and 3 both wait for Task 1. Task 4 waits for both 2 and 3.

### Step 2 — File Overlap Detection

Compare each pair of tasks' file lists to detect implicit dependencies. If two tasks modify the same file, the later task (by plan order) implicitly depends on the earlier one.

**Algorithm:**

1. Extract file paths from each task's `Files:` section — include all lines under `Create:`, `Modify:`, and `Test:`.
2. For each pair `(i, j)` where `i < j`:
   - Compute the intersection: `intersection(files[i], files[j])`
   - If the intersection is non-empty AND task `j` does not already depend on task `i` (directly or transitively), add `i` to task `j`'s `blockedBy`.
3. Transitive check: task `j` already depends on task `i` transitively if there is any chain `j → ... → i` in the existing dependency graph. Do not add redundant edges.

**Example:**

```
Task 1 — Files: src/models/user.ts, src/db/schema.ts
Task 2 — Files: src/api/users.ts, src/middleware/auth.ts
Task 3 — Files: src/api/users.ts, src/api/admin.ts
```

Tasks 2 and 3 both touch `src/api/users.ts`. Since 2 < 3, Task 3 gets an implicit `blockedBy: [2]`. Tasks 1 and 2 share no files, so no implicit dependency is added between them.

The graph is built from the plan's file lists only. An edit a subagent reports on a `DISCOVERED` line (Section 2) is outside it by construction -- the file was not known when the groups were formed -- so two parallel tasks can discover the same file. That case is caught at the merge, not here.

### Step 3 — Build Execution Groups

After resolving all dependencies (explicit + implicit), partition tasks into execution groups:

- **Group 0:** Tasks with no `blockedBy` — these start immediately, in parallel.
- **Group 1:** Tasks whose `blockedBy` entries are all in Group 0.
- **Group N:** Tasks whose `blockedBy` entries are all in Groups 0 through N-1.

Tasks within the same group run in parallel. Groups execute sequentially (Group 0 completes before Group 1 starts).

### Reporting the Graph

Before dispatching, print the execution plan so the user can see what will happen:

```
Dependency Graph:
  Group 0 (parallel): Task 1 [Create database schema]
  Group 1 (parallel): Task 2 [Build API endpoints], Task 3 [Add input validation]
  Group 2 (parallel): Task 4 [Write integration tests]

Dependencies:
  Task 2 → blocked by Task 1 (explicit)
  Task 3 → blocked by Task 1 (explicit)
  Task 4 → blocked by Task 2, Task 3 (explicit)

Dispatching Group 0...
```

---

## 2. Subagent Dispatch

### Prompt Template

The dispatch is a file handoff, not a paste. The task's requirements go to disk as a brief; the prompt carries the path.

**Part 1 -- the brief.** Before dispatching task N:

1. Write `.claude/work/<plan-basename>/task-<N>-brief.md` with the Write tool. It carries, in this order:
   1. **The task's own text**, extracted from the plan -- title, description, acceptance criteria, and file list (Create / Modify / Test, exact paths) -- plus the plan header's architecture context. When the run has no plan file, the brief carries that task's slice of the task description and the file list resolved for it. Either way the brief is the subagent's only source of requirements.
   2. **The line `Test command: <command | none (<reason>)>`**, written after the file list, copying the test value `skills/work/SKILL.md` Phase 2.5 resolved under `#### Resolve the verification command`. The line is always present -- `none` with its reason is a value, and a brief with no such line tells the subagent nothing.
   3. **A `## Interfaces` heading, when any task in the loaded plan carries a `**Provides:**` line.** Reproduce the union of every such line from every task in the plan -- including this task's own -- under that heading, placed after the task's file list and before the `## Global Constraints` heading, each entry prefixed with its owning task number. The copy is unfiltered and does not consult the dependency graph: two tasks that agree on a signature in advance can be built simultaneously in separate worktrees and merge cleanly, so filtering the block by dependency would withhold the signature from exactly the pair that needs it while still parallel.
   4. **No such line anywhere in the plan, or an ad-hoc run with no plan file.** The brief omits the `## Interfaces` heading entirely -- an empty heading reads as "this task has no collaborators" rather than "this plan declared none".
   5. **A `## Global Constraints` heading, when the loaded plan carries that section.** Reproduce the section verbatim under its own `## Global Constraints` heading, placed after the task's file list.
   6. **No such section, or an ad-hoc run with no plan file.** The brief omits the heading entirely -- an empty heading is worse than no heading because it reads as "no constraints were derived" rather than "this run has none".

   Read the file back to confirm it was written (skill rule L3). The resolution and evidence rules are in `skills/verification/SKILL.md`; this file copies only the restatement. The test-first cycle and the red-step evidence form the `TDD` line carries are in `skills/tdd/SKILL.md`, read the same way.
2. Delete any existing `task-<N>-report.md` for this task number, then confirm it is gone (L3). The report path is fixed per task, so on a resumed or retried run a report from the previous attempt is already there; leaving it would let the orchestrator read a stale report as if the new subagent had written it. The delete is the entire mitigation for that hazard, so an unverified delete reintroduces the defect it exists to close.

**Part 2 -- the dispatch prompt.** The prompt carries no plan prose. Its context section is exactly three items -- the plan preamble, other tasks' text, and summaries of completed tasks are all excluded:

```
Task {N} of {total}, execution group {G}.

Your requirements are in .claude/work/<plan-basename>/task-{N}-brief.md. Read it first.
It lists the files you may create, modify, and test.

Write your full account to .claude/work/<plan-basename>/task-{N}-report.md.

## Instructions
1. Sync your worktree before reading anything else: run `git reset --hard {working branch}`, then confirm with `git log --oneline -3` that the commits from earlier execution groups are present. Your worktree is cut from the default branch, so until you do this every file you are about to read is missing the changes this run has already merged. If `{working branch}` does not resolve, report BLOCKED rather than working from the default branch.
2. Read all files listed in the brief to understand current state and existing patterns.
3. Follow the test-first cycle: write the test for the behavior the brief describes, run the test command named on the brief's Test command line exactly as written, and record the red line -- this run's exit code, the new test's name, and its first error line. When that line reads none, skip the red step and report TDD | skipped: test command none (<the reason on that line>); when the brief describes no behavior a test can assert, report TDD | skipped: no testable behavior (<what the change is>).
4. Implement the changes described, following the codebase's existing conventions, then run the test command again exactly as written. When the Test command line reads none, run nothing and report TESTS | skipped: <the reason on that line>. On a failure, fix and run again, at most three runs after the implementation exists -- the red run in instruction 3 is not one of the three attempts. When the third run still fails, stop, report STATUS | FAILED, and put the first failing test and its first error line on REASON. Never grant yourself more attempts.
5. Self-review your changes: check for missing edge cases, naming consistency, and adherence to acceptance criteria.
6. Commit each logical unit on your worktree branch, then report every commit on a COMMITS line. If the tree already matched the spec and there was nothing to commit, return no COMMITS line.

## Constraints
- Modify the files listed in the brief. When the task cannot work without a change in a file the brief does not list -- an import, a registration, a route entry, a config key, an export the brief's file needs -- make that change, keep it as small and additive as you can, and report it on a DISCOVERED line. A change that is a deliverable of its own -- a new module, a feature the brief does not describe, a rewrite of a file another task owns -- is not discovered work: report BLOCKED naming it.
- Follow existing code patterns (naming, structure, error handling).
- Do not add AI attribution comments or generated-by markers.
- The brief's Global Constraints bind every change you make. A change you cannot make without violating one is a BLOCKER, not a judgment call.
- A signature listed under `## Interfaces` in the brief is fixed. If your implementation needs it to differ, report BLOCKED naming the signature -- do not change it and do not work around it.
- If you encounter an ambiguity or need a decision from the user, report BLOCKED status with a clear description of what you need.
- Run the test command you were given exactly as written, and report a pass only by quoting this run's exit code and the runner's summary line -- a run that executed zero tests, a command that has not returned, or a result remembered from an earlier run is not a pass. On failure, quote the first failing test name and the first error line.
- Write the test for the behavior before the implementation and run the test command you were given exactly as written, then report the red step by quoting that run's exit code, the new test's name, and its first error line -- a test that was never seen failing, or a red line naming a test you did not write in this task, is not red evidence; when no test can be written, report skipped with the reason.
```

**Return contract.** The agent's final text is data, not prose. It writes its full account -- what it implemented, what it tested, files changed, self-review findings, concerns -- to the report path, and returns only these lines, in this order:

```
STATUS | DONE | BLOCKED | FAILED
BRANCH | <branch name>
BASE | <short sha of the branch point, after the instruction 1 sync>
COMMITS | <short sha> <subject>                 (zero or more lines, one per commit)
TESTS | <command> -> exit <code>: <summary line>
TESTS | skipped: <reason>                       (the alternate form; exactly one TESTS line is returned)
TDD | red: <command> -> exit <code>: <failing test> -- <first error line>
TDD | skipped: <reason>                         (the alternate form; exactly one TDD line is returned)
DISCOVERED | <repo-relative path> | <one line: what changed and why the task needed it>   (zero or more lines)
REASON | <one line, only when STATUS is not DONE>
REPORT | <path to task-<N>-report.md>
```

`COMMITS` is one line per commit rather than a pipe-delimited list, because a commit subject can contain `|` and the field separator would then be ambiguous. `<base7>` in Section 0's `complete` line is the `BASE` value; `<head7>` is the short sha on the last `COMMITS` line. When there is no `COMMITS` line the task changed nothing to commit -- write `commits none` in place of `commits <base7>..<head7>` and merge no branch for that task. The summary line on `TESTS` is the runner's own (`47 passed, 0 failed`, `Tests: 12 passed, 12 total`); a `TESTS` line that is not in the `skipped:` form and carries no exit code or no summary is treated as `skipped: no evidence returned`. The `TDD` line carries the red step: `red:` quotes the run made after the test was written and before the implementation and names the test the task wrote; `skipped:` carries the reason. A return with no `TDD` line is read as `TDD | skipped: no red evidence`. It never changes the task's status and never blocks the merge -- it is a fact about how the task was built, not about whether it landed -- and the ledger grammar in Section 0 does not carry it; the report file and the group-completion announcement do.

A `DISCOVERED` line records an edit outside the brief's file list, one line per file. It never changes the task's status and the ledger grammar in Section 0 does not carry it; the group-completion announcement prints it and the report file holds the detail. The bound on discovered edits is the merge, not a prompt: a file two tasks both discovered conflicts at Section 3's Per-Branch Merge and stops the run there, which is the one case that earns a question. Keeping the edit small and additive is what makes that case rare.

Anything beyond these lines is ignored. The detail belongs in the report file, which the orchestrator reads only when it needs it -- that is what keeps a run's controller context a function of the number of tasks rather than the size of the work each task did.

### Dispatch Mechanics

For each execution group, in order:

1. **Write the briefs:** For each task in the group, write its `task-<N>-brief.md` and delete any stale `task-<N>-report.md`, per Prompt Template Part 1. Both writes are read back before the group dispatches.
2. **Create tracking entries:** Call `TaskCreate` for each task in the group, recording task title, status `IN_PROGRESS`, and assigned group number.
3. **Spawn agents:** For each task, spawn one Agent with:
   - `subagent_type="general-purpose"`
   - `isolation="worktree"` (each agent works in its own git worktree)
   - `run_in_background=true`
   - The filled-in prompt template as the agent's instructions, with `{working branch}` set to the branch `skills/work/SKILL.md` Phase 2 put this run on.

   `isolation="worktree"` cuts the worktree from the repository's default branch, not from the branch this run is working on. Measured on Claude Code 2.1.233: with the working branch four commits ahead of `master`, a freshly spawned agent's worktree `HEAD` was `master`. Every ref is still readable from inside the worktree because the object store is shared, so the sync in the prompt template's instruction 1 is what puts the agent on the right base. Without it a Group 1 agent reads the pre-run state of every file Group 0 wrote -- it will not fail, it will silently build against stale content and report commits on a base the orchestrator never merges from.
4. **Record the dispatch:** Append `Group <G>: dispatched (<task numbers>)` to the ledger and read the file back to confirm the line landed. `TaskCreate` remains the live in-session view and the ledger is the durable record; the two are complementary, not redundant, and neither replaces the other.
5. **Wait for group completion:** Wait for all agents in the current group to finish. Never call `ScheduleWakeup` as a fallback in case a notification is missed -- the harness always notifies on completion, and a fallback wakeup past the 5-minute prompt-cache TTL forces a full-context reprocess for no benefit.
6. **Process results:** Collect each agent's output and determine status (see Result Collection below).
7. **Update tracking:** Call `TaskUpdate` for each task with its final status.
8. **Merge, then proceed to next group:** Run Section 3's Per-Branch Merge for this group's branches now, not at the end of the run -- the next group's agents sync onto the working branch and can only see what has landed on it. Then, if all tasks in the current group are DONE or if independent tasks in the next group are unblocked, move to the next group.

### Result Collection

Status is read from the return contract's `STATUS` line, not from the prose of a summary. Every ledger append below is verified by reading the file back.

| Status | Detection | Action |
|--------|-----------|--------|
| **DONE** | `STATUS \| DONE` | Append `Task <N> [<task title>]: complete (branch <branch>, commits <base7>..<head7>)`, taking `<branch>` from `BRANCH`, `<base7>` from `BASE`, and `<head7>` from the short sha on the last `COMMITS` line. With no `COMMITS` line, write `commits none` and queue no branch. Otherwise queue the branch for merge. Do not read the report file. |
| **BLOCKED** | `STATUS \| BLOCKED` | Append `Task <N> [<task title>]: blocked -- <one-line reason>`, taking the reason from `REASON`. Read the report file at `REPORT` for the detail. Pause dependents, report to the user. |
| **FAILED** | `STATUS \| FAILED` | Append `Task <N> [<task title>]: failed -- <one-line reason>`, taking the reason from `REASON`. Read the report file at `REPORT` for the detail. Pause dependents, report to the user. |

An agent that returns nothing -- killed on a terminal error, or skipped -- is neither blocked nor complete. Append no ledger line for it. The absent `complete` line is what makes the next invocation re-dispatch it cleanly.

**When a report file is read.** The orchestrator reads a `task-<N>-report.md` only on a BLOCKED or FAILED status, or when post-merge validation points at that task. A DONE task's report is written and never opened.

**Handling BLOCKED/FAILED tasks:**

- All tasks that have a direct or transitive dependency on a BLOCKED/FAILED task are paused — they do not dispatch.
- Tasks in the same or later groups that are independent of the failed task continue normally.
- The orchestrator reports the situation to the user and waits for guidance before retrying paused tasks.
- In auto mode (`skills/work/SKILL.md` Arguments), a FAILED task is not waited on: print `Task <N>: still failing after 3 attempts -- accepted`, keep its dependents paused, let independent tasks continue, and carry on to Post-Merge Validation and Phase 4 with the failed task and every paused dependent listed for the 5d summary. The ledger line stays the `failed` form -- accepted is a routing decision, not a status. BLOCKED waits in auto mode too: a blocker's answer changes what gets built, and auto mode answers no such question.

---

## 3. Merge Procedure

### Merge Order

A group's branches merge as soon as that group completes, before the next group dispatches. This is what makes the branch-point sync in Section 2 worth anything: the sync can only deliver what the working branch already carries, so deferring every merge to the end leaves each later group resetting onto a branch that is missing its own dependencies.

Within that, merge in topological order -- a task's branch merges only after all of its dependencies have merged -- and within the same execution group, merge in plan order (lower task ID first).

Merging per group also keeps conflicts small and attributable. Two tasks in consecutive groups that touch the same file conflict against one already-merged commit at a known point in the run, rather than against a pile of parallel branches all resolved at the end, where the conflict names no group and the run has nothing left to roll back to.

### Per-Branch Merge

For each completed task branch, in topological order:

1. Run `git merge <worktree-branch> --no-edit` into the working branch.
2. **Auto-merge succeeds:** Append `Task <N>: merged` to the ledger and read it back, before moving on -- a branch that landed must be recorded at the moment it lands, not once its group finishes. Continue to the next branch. Clean up the worktree. Once the whole group's branches have merged, append `Group <G>: merged (<task numbers>, no conflicts)` to the ledger and read it back.
3. **Conflict detected:** Stop the merge sequence immediately. Append `Group <G>: merge stopped -- conflict in <file list>` to the ledger, then report to the user with:
   - The conflicting file list (from `git diff --name-only --diff-filter=U`)
   - Which task branches have merged so far
   - Which task branches remain unmerged

Each branch that landed carries its own `Task <N>: merged` line, so the "which task branches have merged so far" item is read from the ledger rather than from memory -- including after a compaction, when memory is gone and the group line has not been written.

Do not attempt automatic conflict resolution. The user must resolve conflicts before the merge sequence continues.

### Post-Merge Validation

After the final group's branches have merged successfully -- once per run, not once per group:

1. Run the test command Phase 2.5 resolved, on the merged result, and record the evidence line; when it resolved to none, record skipped with the reason and report that the merged result is unverified.
2. If tests pass, report success.
3. If tests fail, report the failures with:
   - Which tests failed
   - Likely responsible task (based on which files the failing tests cover)
   - Suggestion: re-run the responsible task's agent with the test failure as context.

   Read that task's `task-<N>-report.md` for the detail before reporting. This is the third and last case where a report file is read.

---

## 4. Progress Reporting

The printed tables are a view, not the state. After a context compaction the ledger at `.claude/work/<plan-basename>/progress.md` is the authority for what has been dispatched, completed, and merged; rebuild the table from it rather than from anything remembered.

### At Start

When orchestration begins, report:

```
Orchestrating {N} tasks across {M} execution groups.
```

Print the dependency graph using the format shown in "Reporting the Graph" above, then announce dispatching the first group.

### During Execution

Use `TaskCreate` and `TaskUpdate` calls to maintain real-time status. Each task transitions through:

```
PENDING → IN_PROGRESS → DONE | BLOCKED | FAILED
```

When a group completes, announce it before dispatching the next:

```
Group 0 complete. All tasks DONE.
  Task 1: npm test -> exit 0: Tests: 47 passed, 47 total
          red: npm test -> exit 1: parses a manifest -- ReferenceError: parseManifest is not defined
  Task 2: go test ./... -> exit 0: ok  example.com/m/pkg  0.41s
          skipped: no testable behavior (README section)
          discovered: src/router.ts -- registered the /users route the handler needs
Dispatching Group 1 (2 tasks in parallel)...
```

Print each task's `TESTS` line, its `TDD` line, and every `DISCOVERED` line from the return contract in the group-completion announcement. That announcement is the one place these lines are consumed, which is why the fields are in the contract; `skills/work/SKILL.md` 5d counts the `TDD` lines and lists the discovered edits from these announcements.

### At End — Success

When all tasks complete successfully and merge cleanly:

```
All tasks complete.

| Task | Title                    | Status | Branch                    |
|------|--------------------------|--------|---------------------------|
| 1    | Create database schema   | DONE   | work/1-database-schema    |
| 2    | Build API endpoints      | DONE   | work/2-api-endpoints      |
| 3    | Add input validation     | DONE   | work/3-input-validation   |
| 4    | Write integration tests  | DONE   | work/4-integration-tests  |

Merge: All 4 branches merged successfully.
Tests: 47 passed, 0 failed.
```

### At End — Partial Failure

When some tasks fail or are blocked:

```
Orchestration paused — 1 task blocked, 1 task not started.

| Task | Title                    | Status      | Branch                    |
|------|--------------------------|-------------|---------------------------|
| 1    | Create database schema   | DONE        | work/1-database-schema    |
| 2    | Build API endpoints      | DONE        | work/2-api-endpoints      |
| 3    | Add input validation     | BLOCKED     | work/3-input-validation   |
| 4    | Write integration tests  | NOT STARTED | —                         |

Blocker (Task 3): "Validation rules not specified in plan — need user input on email format requirements."

Merged so far: Task 1, Task 2.
Awaiting: Resolve Task 3 blocker, then Task 3 and Task 4 can proceed.
```

In auto mode a FAILED task prints the same table with `FAILED (accepted)` in its Status cell and `Awaiting:` replaced by the list of paused dependents; the run then continues to Post-Merge Validation instead of pausing. A BLOCKED task pauses the run in auto mode as well.
