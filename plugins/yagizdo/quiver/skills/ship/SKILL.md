---
name: ship
description: "Take a project from description to working app in one run -- conduct a deep planning Q&A session (outcomes, scope, constraints, prior decisions, task breakdown, verification criteria), write the answers as a plan at .claude/plans/<date>-<project>-ship-plan.md in the format /plan produces, hand that plan to /work --auto for a build that stops only for a genuine blocker, then verify the result with the build command, the test suite, and a smoke launch when the plan carries a run command, and name the /review command to run before merging. /ship --execute and /ship --verify re-enter a run that was paused or deferred."
argument-hint: "[<project-path>] [--seed <brainstorm-spec.md>] [--resume] [--execute] [--verify]"
when-to-use: "user wants to build a project from scratch or description -- '/ship', 'build this app', 'I described my project, now build it', 'start from description and ship', 'autonomous build', 'I want to walk away and come back to a finished app', 'verify my build' (not: gap-analysis on existing partial code; not: executing a plan you already have -- use '/work' for that; '/ship --execute' hands a saved ship plan to /work, '/ship --verify' checks a finished build)"
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

```
!`git rev-parse --show-toplevel 2>/dev/null || echo "NO_GIT"`
```

---

# Instructions

You are a build orchestrator. Your job is to conduct a deep planning Q&A session with the user -- covering every detail needed to build the project without further human input -- write the answers as a plan `/work` can execute, hand that plan to `/work`, and verify what it built. The user answers questions once, approves once, and comes back to a built and verified project -- never to a mid-run prompt. The one command the report leaves to them is `/quiver:review`, which ship cannot invoke. You do NOT guess requirements. If a detail is not provided and it affects what gets built, you ask.

Ship runs no task and dispatches no subagent. `/work` executes the plan and `skills/work/orchestrator.md` is the only orchestrator. The questions are front-loaded: Phase 1 asks everything the build could otherwise stop to ask, and `/work` runs in its auto mode, which answers the routine gates -- branch, final commit, PR handoff, workspace, third failed fix attempt -- from the approval already given. A blocker or a merge conflict -- anything whose answer changes what gets built or deletes something -- still stops and asks. Ship never decides those on the user's behalf, and never grants a fix attempt past `/work`'s cap.

## Step 0 -- Git Availability

If any gather-context block returned `NO_GIT`, this directory is not a git repository.
Print: `> No git repository detected -- using current working directory as project root.`
Proceed normally. The Q&A works without git; `/work` degrades on its own (no branch, no commits, no PR).

**Derive the project name:**
- If git available: take the last path segment from the `git rev-parse --show-toplevel` output (e.g., `/Users/alice/projects/my-app` -> `my-app`).
- If NO_GIT: use the basename of the current working directory from shell context.

Use `<project>` as the derived name throughout the skill.

## Step 0.5 -- Argument Parsing

Read `$ARGUMENTS` as plain text:

- If it contains `--execute`: set execution intent; skip interactive State Detection entirely and enter `# Execution`. Do not continue into Step 1.
- If it contains `--verify`: set verification intent; skip interactive State Detection entirely and enter `# Verification`. Do not continue into Step 1.
- If it contains `--resume`: jump directly to the Step 1 Resume path (act as if exactly one ship plan was found -- the most recently modified when several exist -- and the user picked "Resume").
- **Precedence:** `--resume` > `--verify` > `--execute`. If `--resume` is present, clear all other intents and follow the Resume path. If `--verify` is present without `--resume`, clear execution intent and enter `# Verification`.
- If it contains `--seed <path>`: note the seed path. Read the spec file in Phase 0 and extract all context: stack, services, data model, any acceptance criteria present.
- If it contains a path that is not a flag (e.g., `/path/to/project`): treat it as the project root for all Glob and Read operations in this run. Derive `<project>` from this path's basename instead.
- If it is empty or contains only flags: proceed normally using the current directory.

## Step 1 -- State Detection

**Mode routing guard (check first, before any Glob):**
- If execution intent was set in Step 0.5 (`--execute`), do not run State Detection. Go directly to `# Execution`.
- If verification intent was set in Step 0.5 (`--verify`), do not run State Detection. Go directly to `# Verification`.

**The flags are entry points for an interrupted or deferred run, not the normal path.** A run started from Q&A reaches execution and verification on its own. `--execute` is for resuming after an interruption or for a plan approved with "plan only"; `--verify` is for re-verifying a finished build.

### Locating the ship plan

Used here and by both re-entry modes. Use the Glob tool: `.claude/plans/*-ship-plan*.md` -- the pattern also matches the `-2`, `-3` suffixes Phase 3 adds when a day's path is taken.

A ship plan's state is read from disk, never remembered:

- **finished** -- the plan's frontmatter reads `status: completed`; `/work` Phase 5c sets it when its run completes. Check this first: it wins over the ledger below.
- **in progress** -- not finished, and its work ledger exists at `.claude/work/<plan-basename>/progress.md`, where `<plan-basename>` is the plan filename without `.md`. `/work` writes the ledger for plans of 3+ tasks and, in auto mode, keeps it after a finished run as well as after an interrupted one -- the ledger alone does not separate the two, the `status` field does.
- **not started** -- neither of the above.

**Zero plans (first run):** proceed to Phase 0.

**One plan found:** read it, then use `AskUserQuestion`:
> Found an existing ship plan: `<path>` (<not started | in progress | finished>). How would you like to proceed?

Buttons: `["Resume -- hand the plan to /work", "Start fresh -- run a new Q&A", "Inspect -- show me the plan"]`

- **Resume:** for a not-started or in-progress plan, enter `# Execution` with this plan path. For a finished plan there is nothing left to build -- enter `# Verification` instead.
- **Start fresh:** proceed to Phase 0. The existing plan stays on disk and is never overwritten; Phase 3 writes the new one at today's path, suffixed when that path is taken.
- **Inspect:** print the full plan contents. Then use `AskUserQuestion`:
  > What would you like to do next?
  Buttons: `["Resume", "Start fresh", "Cancel"]`
  - Cancel: stop immediately. Do nothing.
  - Resume and Start fresh: as above.

**Multiple plans found (multi-project workspace):**
Use `AskUserQuestion`:
> Multiple ship plans found. Which one would you like to work on?

List each plan filename with its state as a button label (up to 4; show the 4 most recently modified if more exist). Add a final button: `"Start a new project"`.

- Selecting an existing plan: same routing as "One plan found" above.
- Selecting "Start a new project": proceed to Phase 0.

## Phase 0: Project Intake

Read `$ARGUMENTS` as the initial project description (may be long). If `--seed <path>` was provided, read the file and extract all context: stack, services, data model, any acceptance criteria present. Present a 1-2 sentence summary of what was understood -- no AskUserQuestion yet.

## Phase 1: Mandatory Q&A

Ask questions via AskUserQuestion until all 6 categories plus platform/deployment are answered:

| # | Category | Answered when |
|---|----------|---------------|
| 1 | Outcomes | User stated 1+ concrete acceptance criteria |
| 2 | Scope boundaries | User named at least one thing NOT being built |
| 3 | Constraints | User stated tech stack, library restrictions, or "none" |
| 4 | Prior decisions | User described locked architecture/data model, or "starting fresh" |
| 5 | Task breakdown | AI proposes a task list, user approves or adjusts; dependencies noted per task |
| 6 | Verification criteria | User named a test command or described a manual acceptance check, and said whether a command launches the app (recorded as the run command, or none) |
| + | Platform | iOS, Android, web, CLI, backend, desktop |
| + | Deployment target | App Store, Google Play, Vercel, self-hosted, local only |

Batching rules:
- Ask outcomes first (standalone).
- Batch platform + deployment together (independent questions).
- Batch constraints + prior decisions together if neither depends on the other's answer.
- Ask task breakdown after outcomes and scope are known (it depends on them).
- Ask verification after task breakdown (user knows what tasks to verify).

Q&A runs until all categories are answered. If the user answers partially (e.g., "not sure about verification"), prompt once more for that category before proceeding.

Ask here anything that would otherwise become a question during the build: a service or library choice the task list leaves open, a data shape two tasks share, a name the user cares about, an environment the tests need. Ten questions up front cost less than one interruption mid-run. After Phase 2 the only questions left are `/work`'s blocker gates.

## Phase 2: Plan Summary + Approval

Present a build plan table:

```
| ID | Task | Blocked by | Acceptance Criterion |
|----|------|------------|----------------------|
| 1  | ...  | --         | ...                  |
| 2  | ...  | 1          | ...                  |
| 3  | ...  | 1          | ...                  |
```

`Blocked by` carries the dependencies from Q&A category 5. `/work` builds its execution groups from these and from file overlap (`skills/work/orchestrator.md` Section 1): tasks with no unmet dependency run in parallel, the rest wait.

Use AskUserQuestion:
> Does this plan cover everything you need? Approving starts the build -- I write the plan, hand it to /work, then verify the result. Nothing stops to ask again unless a task blocks or a merge conflicts.

Options: "Approve -- build it", "Approve the plan only -- do not build yet", "Add or change something", "Start over"

On "Add or change something": ask what to change, update the table, re-present. On "Start over": return to Phase 0.

**"Approve -- build it" is the run's single consent point (R6).** It authorizes the plan write, the handoff to `/work --auto`, every per-task commit, and the verification pass. Proceed to Phase 3 and do not stop between phases. It does not authorize a push, a pull request, or a review -- none of those is automatic -- and it does not stand in for a blocker: `/work` still asks when a task cannot proceed or a merge conflicts. When the user asks for the pull request after the run, `/create-pr` opens it -- `/work` Phase 5b states that rule, and a description the run drafted is that skill's input, not a body to hand to `gh pr create`.

**"Approve the plan only"** writes the plan and stops there, for a user who wants to read or edit it first. Print the plan path and the `/ship --execute` command, then terminate.

## Phase 3: Plan Write

Get the date via the Bash tool (`date '+%Y-%m-%d'`) and write `.claude/plans/<date>-<project>-ship-plan.md`, creating `.claude/plans/` if it does not exist. When that path already exists, write `<date>-<project>-ship-plan-2.md`, then `-3`, and so on -- the first free name. An existing plan is never overwritten: its basename keys its `/work` ledger at `.claude/work/<plan-basename>/`, and a rewrite under the same name would resume that ledger's `complete` lines against tasks it never built. The file is a plan in the format `skills/plan/SKILL.md` Step 5 defines -- read that section before writing, and do not improvise a format of your own. `/work` reads this file exactly as it reads a `/plan` output; the format has one home, and this skill does not restate it.

What the Q&A answers become:

- **Frontmatter:** `name: <project>-ship-plan`, `status: active`, `created: <date>`, then `stack`, `platform`, and `deployment_target` from the Phase 1 answers, then `test_command`, `build_command`, and `run_command`. `stack` carries the tech-stack half of the category 3 answer. `test_command` and `build_command` are resolved once, here, by reading `skills/verification/SKILL.md` and following its Command Resolution, with the Phase 1 category 6 answer as rule 1 when it names a command. Each holds the command string or `none (<reason>)`, never an empty field. `run_command` holds the launch command category 6 named, or `none`.
- **Goal:** the category 1 outcomes, as the plan's opening section.
- **`## Global Constraints`:** the section Step 5 defines, holding the category 3 answer -- the library restrictions and stated limits, one imperative sentence per numbered entry -- and the category 2 scope boundaries as "Do not build ..." entries, which is how Step 4.5 treats out-of-scope items. `/work` copies this section verbatim into every task brief and `/quiver:review --plan` binds its findings to it, so a constraint the plan does not record is one no implementer can honor.
- **Tasks:** one per row of the approved Phase 2 table, in the task format Step 5 defines, each with its `**Files:**` line, its `**Provides:**` line where another task names what it creates, and its acceptance criterion from the table. A dependency from the `Blocked by` column is written as a `blockedBy: [<task numbers>]` line under the task's `**Files:**` line -- the explicit-dependency field `skills/work/orchestrator.md` Section 1 reads; a task with none carries no line. When `test_command` is not `none`, order each task's steps test-first as Step 5 describes, naming `skills/tdd/SKILL.md`; `/work` follows that cycle when it builds.
- **Acceptance Criteria:** the category 1 outcomes and the category 6 check, as the plan's closing section.

Then run the checks of `skills/plan/SKILL.md` Step 6 by reading that section. The Q&A answers (and the `--seed` spec, when given) are the source specification Check 3 reads. Apply its action routing; do not present the checks to the user.

After writing: read the plan back and confirm the `## Global Constraints` heading is present -- category 2 always names something not being built, so it always is -- and that every task another task names by symbol carries a `**Provides:**` line. A plan whose tasks share no symbol carries none, and that is correct: Check 8 is a no-op there, not a miss.

Print: `> Plan complete: <N> tasks. Saved to <plan path>.`

Then route on the Phase 2 answer:

- **"Approve -- build it":** print `> Building.` and continue straight into `# Execution`. Do not ask again, do not print a command for the user to run, and do not wait for a reply.
- **"Approve the plan only":** print `> Plan saved. Run /ship --execute when you want the build.` and terminate.

---

# Execution

Consent for this phase was given at Phase 2's "Approve -- build it", or by the `/ship --execute` invocation. Ship implements nothing here: it hands the plan to `/work` and waits.

**Locate the plan.** When entered from Phase 3, the plan is the file just written. On `--execute` re-entry, locate it as Step 1 describes; with no ship plan, print `> No ship plan found. Run /ship first.` and terminate; with several, ask which one with `AskUserQuestion` (up to 4, most recent first).

**Stay on the branch ship started on.** Ship creates no branch. Started on `main` or `master`, `/work` Phase 2 creates the feature branch itself; started on a feature branch, its auto mode continues there. Do not switch branches to pre-empt either case.

**Hand off.** Invoke the `work` skill through the Skill tool with the plan path and `--auto` as its arguments (`/work <plan path> --auto`). The Skill tool does not run `/work` and come back: it loads `skills/work/SKILL.md` into this conversation as a message, the run continues here under `/work`'s instructions, and nothing signals its end -- `/work` ends at its Phase 5d summary. `/work` loads the file as a plan (its Case A path), resolves the verification command per `skills/verification/SKILL.md`, follows `skills/tdd/SKILL.md` on every task under its three-attempt fix cap, lets a subagent make the small wiring edits a task needs outside its file list and report them as discovered, commits per task, and in auto mode answers its routine gates from the Phase 2 approval: it continues on the current branch, commits the final leftovers, prints `/quiver:review` and `/create-pr` as text instead of running them, and keeps its workspace. It still stops for a blocker or a merge conflict; when it does, that question is the user's, not ship's -- never answer it for them. A task still failing after its third run is accepted and listed, on both of `/work`'s paths, never retried by ship.

**Continue.** The moment `/work`'s Phase 5d summary is printed, print `> Build finished. Verifying.` and continue into `# Verification` in the same turn -- before the turn ends, before any other question, and however long the run was. A run that stopped for a blocker and resumed on the user's answer is still this run, and its 5d summary is the same signal. A `/work` run that stopped on a blocker or a merge conflict has said so; still run verification -- its report is where the remaining work is listed. A turn that ended on the summary with no report is the case `/ship --verify` re-enters.

**Re-entry.** `/ship --execute` invokes `/work` with the same plan path and `--auto`. For a plan of 3+ tasks `/work` resumes from its ledger at `.claude/work/<plan-basename>/progress.md` and re-dispatches no task carrying a `complete` line. A 1-2 task plan has no ledger; `/work` runs it from the top on the branch that carries the earlier commits.

---

# Verification

This phase checks what `/work` built. It runs the build, runs the tests, smoke-launches the app when the plan carries a run command, and writes a report. It changes no plan field. It runs no review: `skills/review/SKILL.md` carries `disable-model-invocation: true`, so a Skill-tool call to `review` from here is refused, and an unattended review is the case that flag exists to stop. The report names the `/quiver:review` command instead, and the user runs it.

## Entry

**Triggers:** `--verify` (set in Step 0.5), or continuation from `# Execution`.

1. Locate the ship plan as Step 1 describes. With no ship plan, print `> No ship plan found. Run /ship first.` and terminate. With several, ask which one with `AskUserQuestion`.
2. Read `test_command`, `build_command`, and `run_command` from the plan frontmatter. A field that is absent resolves to `none (field missing)`; do not write it back.
3. Note the current branch from the gather-context output. Verification runs on the branch `/work` left the session on.

## Step 1 -- Build

When `build_command` is `none`: print `Build: skipped -- <reason>`.

Otherwise run it via the Bash tool and quote one evidence line per the Evidence Rule in `skills/verification/SKILL.md`: `pass: <command> -> exit 0: <summary line>` or `fail: <command> -> exit <code>: <first error line>`.

## Step 2 -- Tests

When `test_command` is `none`: print `Tests: skipped -- <reason>`.

Otherwise run it via the Bash tool and quote one evidence line per the same Evidence Rule. A run whose summary line shows zero tests executed is `skipped: <reason>`, never `pass` -- cross-cutting rule 1 of that file.

## Step 3 -- Smoke

When `run_command` is `none`: print `Smoke: skipped -- no run command`.

Otherwise launch the app with the run command via the Bash tool with `run_in_background`, then wait on a cheap readiness condition -- a port answering, a "Ready" log line, a booted simulator -- inside an `until` loop with a deadline of at most 120 seconds and a failure check on the log (a crash line, `Error:`, `EADDRINUSE`). Run the wait itself with `run_in_background` too, or with the `Monitor` tool where the session has it: a foreground `sleep` is blocked by the harness, so an `until ... sleep 1; done` issued inline is rejected before it polls once. Never poll by re-running the launch command. When a screenshot tool is available in the session (an iOS simulator or browser MCP), capture the first screen and flag placeholder text, a blank screen, or a visible error. Stop the process when done.

Record `Smoke: pass`, `Smoke: fail -- <first error line>`, or `Smoke: timeout -- <condition> not met in <N>s`.

## Step 4 -- Report

Get a timestamp via the Bash tool (`date '+%Y-%m-%d_%H-%M-%S'`) and write `.claude/reports/ship-<project>-<timestamp>.md`, creating the directory if needed:

```
# Ship Report: <project>

- **Plan:** <ship plan path>
- **Branch:** <branch>
- **Build:** <evidence line or skipped reason>
- **Tests:** <evidence line or skipped reason>
- **Smoke:** <result>
- **Review:** not run -- `/quiver:review --base <default branch> --plan <ship plan path>`

## Open Items

<numbered list: every task /work reported blocked, failed, or accepted after three attempts, every smoke flag. "None." when empty.>

## What's Next

<1-3 sentences. When every line above is a pass or a skip and Open Items is empty, say the project appears complete, name the branch to merge, and name the `/quiver:review` command above as the step before merging. `<default branch>` is `main` or `master`, whichever the repository has -- `--base` keeps `/quiver:review` from asking for it, and `--plan` lets its Step 1.8 bind the findings to the plan's Global Constraints.>
```

Read the report back to confirm it was written (L3). Print `> Verification complete. Report: <path>. <count> open items. Next: /quiver:review --base <default branch> --plan <plan path>` and terminate.

A second `/ship --verify` writes a new timestamped report; earlier ones are never overwritten.
