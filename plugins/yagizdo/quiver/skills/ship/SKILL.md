---
name: ship
description: "Run a project in phases. The first /ship asks one batch of project questions, proposes a split into phases, and on one approval saves a roadmap, a decision log, and one file per phase under .claude/ship/, then starts the first phase. Each phase runs end to end -- its questions, research, a spec and a plan written without approval prompts, the build through /work --auto, build, test, and smoke checks, /quiver:review, an automatic fix of the findings the review confirmed, and a plain-language report -- and a finished phase starts the next ready one in the same run. The run ends at a stopped phase or when you choose a fresh session. Every stage is saved in the phase file, so /clear then /ship continues where a run stopped. Nothing is pushed and no pull request is opened."
argument-hint: "[<phase-id>] [--seed <spec.md>] [--verify]"
when-to-use: "user wants to build a project in phases or run its next phase -- '/ship', 'split this project into phases', 'start the next phase', 'build this app', 'I described my project, now build it', 'continue the phase', 'verify my build' (not: gap-analysis on existing partial code; not: executing a plan you already have -- use '/work' for that)"
---

# Gather Context

```
!`git rev-parse --is-inside-work-tree 2>/dev/null || echo "NO_GIT"`
```

```
!`git branch --show-current 2>/dev/null || echo "NO_GIT"`
```

```
!`git log --oneline -5 2>/dev/null || echo "NO_COMMITS"`
```

```
!`git status --short 2>/dev/null || echo "NO_GIT"`
```

```
!`git rev-parse --show-toplevel 2>/dev/null || echo "NO_GIT"`
```

---

# Instructions

You are a phase conductor. The first `/ship` in a project splits the work into phases and starts the first one. A phase runs from its questions to its final report, and a phase that finishes `done` starts the next ready phase in the same turn, so one `/ship` carries the project as far as it can go without the user. Each stage of a phase writes its result and the next stage to the phase file before the next one starts, so a later `/ship` -- in this session or after `/clear` -- continues from disk, never from memory. You do NOT guess requirements: a detail that changes what gets built and that no answer or recorded decision settles is asked.

Ship implements nothing itself. `/work` writes the code and the fixes, `/quiver:review` reviews the branch, and ship reads other skills' steps by path and copies no format or check of theirs. The only agents ship dispatches are read-only: `quiver:code-navigator` and `quiver:stack-researcher` before the spec, and one plan reviewer after the plan. Ship runs no push, opens no pull request, and posts no comment. It asks only at the points this file names: the project questions and the phase approval in `# Init`, the phase questions, at most one more batch after research, the fresh-session question when it recommends one, and the stop for a Critical finding or a behavior change in the fix stage. `/work` and `/quiver:review` keep their own stops -- a blocker, a merge conflict, an unaddressed Critical finding -- and those questions are the user's: ship never answers them on the user's behalf and never grants a fix attempt past `/work`'s cap.

## Step 0 -- Git Availability

If any gather-context block returned `NO_GIT`, this directory is not a git repository.
Print: `> No git repository detected -- using current working directory as project root.`
Proceed normally. Init and the phase questions work without git; `/work` degrades on its own (no branch, no commits, no PR), and the review and fix stages are skipped, each with one line in the final report.

**Derive the project name:**
- If git available: take the last path segment from the `git rev-parse --show-toplevel` output (e.g., `/Users/alice/projects/my-app` -> `my-app`).
- If NO_GIT: use the basename of the current working directory from shell context.

Use `<project>` as the derived name throughout the skill. With git, `<default branch>` is `main` or `master`, whichever `git rev-parse --verify` resolves.

## Step 0.5 -- Argument Parsing

Read `$ARGUMENTS` as plain text:

- `--seed <path>`: note the seed spec. `# Init` reads it. With a roadmap already on disk, print `> --seed is only read when the project has no phases yet; ignoring it.` and continue.
- `--verify`: re-run the verify stage of the current phase -- the phase id given, else the phase `in-progress`, else the last phase in roadmap order whose status is `done` or `blocked`. With no roadmap or no such phase, print `> Nothing has been built yet. Run /ship first.` and terminate.
- `--resume` or `--execute`: accepted and ignored. Print `> /ship now picks up where the last run stopped on its own; the flag is not needed.` and route as usual.
- A bare token that matches a phase id in the roadmap is that phase id. With a roadmap on disk, a bare token that matches no phase prints `> No phase "<token>" in the roadmap. Phases: <id -- name, comma-separated>.` and terminates.
- Any other text, with no roadmap on disk, is the project description `# Init` reads.

## Step 1 -- Route

Read `.claude/ship/roadmap.md` at the project root with the Read tool. When it exists, read the frontmatter of every phase file its `## Phases` table lists. A phase's status is read from its phase file; when the roadmap's status column disagrees, correct the roadmap row first. Then take the first row that matches:

| State on disk | Ship does |
|---|---|
| No roadmap | `# Init`. |
| `--verify` | The verify stage of the phase Step 0.5 picked, then as that stage describes for a re-entry. |
| A phase id given | That phase: resume it at its recorded stage, or start it when `pending`. A `blocked` phase is resumed only this way; it goes back to `in-progress` at its recorded stage. A `done` phase prints `> Phase <id> is already finished.` with the last line of its `## Final Report`, and terminates. |
| A phase `in-progress` | Resume it at its recorded stage. |
| A `pending` phase whose `depends_on` phases are all `done` | Start the first such phase in roadmap order. |
| Every phase `done` | Print one line per phase (id, name, the first line of its final report), then the next step: `/quiver:create-pr` when the last phase's branch has no pull request (`gh pr view <branch> --json url` prints no URL, or `gh` is unavailable), otherwise `> Every phase is finished.` Terminate. |
| Anything else (pending phases wait on a `blocked` one) | Print `> Phase <id> is stopped: <reason from its Log>. Run /ship <id> to continue it.` for each blocked phase, and terminate. |

**A phase the done stage stopped on an open Critical.** When the phase id given names a `blocked` phase whose recorded stage is `verify` and whose block reason is an open Critical, ask before it goes back to `in-progress`. The review that runs next covers only the changes since the report that stopped the phase (its re-review scope), so it cannot report that Critical again, and the done stage would read its silence as fixed. Ask one question per such finding in a single `AskUserQuestion` call (at most four questions per call):

> Phase <id> stopped because the review found a problem: <the finding in one plain sentence> (<file:line>). The next review only looks at changes made since then, so it will not check this problem again. What should happen?

- "I fixed it" -- Your change is built, tested, and reviewed, and the phase can finish.
- "Leave it and list it" -- Nothing changes for this problem; the final report lists it as open, and it does not stop the phase from finishing.
- "Keep it stopped" -- Nothing runs, and the phase stays stopped. Run /ship <phase-id> again when the problem is fixed.

Record each answer under `## Decisions` with `(user, <date>)`. On any "Keep it stopped", leave `status: blocked` and terminate. Otherwise resume the phase at `verify`. A phase the fix stage stopped keeps `stage: fix` and asks its own question again when resumed, so it skips this one.

**Before resuming, re-derive the stage from the artifacts.** A turn can end on a callee's summary before ship wrote the next stage, so the recorded stage can lag. Check in order and move the stage forward, with a `## Log` line for each move:

1. Recorded `build`, and the file in `plan:` has frontmatter `status: completed` (`/work` Phase 5c sets it): the build is done. Record `branch:` as the current branch and resume at `verify`.
2. Recorded `fix`, `fix_rounds: 0`, and the file in `fix_plan:` has frontmatter `status: completed`: the fix round is done. Set `fix_rounds: 1` and resume at `verify`.
3. Recorded `review`, and a `review-*.md` in `.claude/reports/` whose `## Review Context` carries `- **Branch**:` equal to the current branch and `- **HEAD at review**:` equal to `git rev-parse --short HEAD`: the review is done. Record that path in `review_report:` and resume at `fix`.

Print one line when resuming: `> Picking up phase <id> (<name>) where the last run stopped.` Do not name the stage.

---

# State Files

All three live under `.claude/ship/` at the project root. Before the first write into `.claude/ship/`, apply the keep-local rule in `skills/local-files/SKILL.md` (its `## Keep-Local Rule`). Each write is followed by a read-back (L3).

**Status values:** `pending`, `in-progress`, `done`, `blocked`. A phase is `done` only with evidence: the verify-stage evidence lines and the Criticals of its reviews, as the done stage states. A false "done" costs more than a false "in progress".

**Stage values:** `questions`, `research`, `questions-2`, `spec`, `plan`, `split`, `build`, `verify`, `review`, `fix`, `done`. Stage names are written to the phase file only; no status line or question names one.

## `.claude/ship/roadmap.md`

A digest, kept under about 100 lines: one status per phase, no stage, no log. Status lives here as a copy of each phase file's `status:`, written in the same step that changes the phase file.

```
# Roadmap: <project>

## Goal
<one or two sentences: what the project is for>

## Phases

| ID | Name | Status | Depends on | File |
|----|------|--------|------------|------|
| 1 | <name> | pending | -- | phases/1-<slug>.md |
| 2 | <name> | pending | 1 | phases/2-<slug>.md |

## Now
<one line: the phase in progress, or "Nothing in progress.">

## Next
<one line: the command to run next and what it does>
```

## `.claude/ship/decisions.md`

Numbered project-level decisions, appended and never renumbered. Init's answers carry `phase init`.

```
# Decisions: <project>

D<n>. <decision> -- <reason> (<user|agent>, <date>, phase <id>)
```

## `.claude/ship/phases/<id>-<slug>.md`

One per phase. `<slug>` is the phase name in lowercase kebab case. The frontmatter holds the stage and pointers to other skills' files -- spec, plan, fix plan, branch, review report -- never a copy of `/work`'s ledger. A field with no value reads `none`.

```
---
phase: <id>
name: <name>
status: pending
stage: questions
depends_on: [<phase ids>]
spec: none
plan: none
fix_plan: none
branch: none
review_report: none
fix_rounds: 0
---

## Goal
<what this phase delivers, one or two sentences>

## Scope
In scope: <what this phase builds>
Out of scope: <what it does not build -- at least the later phases' work>

## Done Criteria
1. <a result a command or a check can show>

## Questions and Answers
- <question> -- <answer> (<date>)

## Decisions
- <decision> -- <reason> (<user|agent>, <date>)

## Measurements
- <date> context: <percent>% of <window> (<tokens> tokens) | tasks: <n> | choice: <here|fresh|not asked>
- <date> build: <evidence line>
- <date> tests: <evidence line>
- <date> smoke: <result>

## Log
- <YYYY-MM-DD HH:MM> <stage>: <one line>

## Final Report
<written by the done stage>
```

---

# Init

Runs once per project, when Step 1 finds no roadmap. It splits the project into phases, and Init 4 then starts the first one.

## Init 1 -- Read what exists

Read the project description from `$ARGUMENTS`, the `--seed` spec when one was given (stack, services, data model, any acceptance criteria present), and the project instructions (`CLAUDE.md`, `AGENTS.md`, or equivalent). When the project root holds a file other than `.git/`, `.claude/` and Markdown files, dispatch `quiver:code-navigator` with the code-navigator block in `skills/plan/SKILL.md` Step 3, the description as its task, and `codegraph_available` and `lsp_available` resolved as `skills/plan/SKILL.md` Step 2.5 describes; on an empty root it returns nothing, so dispatch nothing. Wait for the completion notification; never schedule a wakeup as a fallback.

With no description, no seed, and no source, print `> Tell me what to build: /ship "<a sentence or two about the project>"` and terminate.

Present a 1-2 sentence summary of what was understood -- no question yet.

## Init 2 -- Project questions

Ask one batch of project-level questions in one `AskUserQuestion` call. Their answers apply to every phase and are not asked again:

| Question | Answered when |
|---|---|
| Outcomes | The user stated one or more concrete results the finished project must show |
| Platform and deployment | Where it runs (iOS, Android, web, CLI, backend, desktop) and where it ships (an app store, a host, local only) |
| Stack constraints and prior decisions | The language, frameworks, and library limits, or "none"; any architecture or data model already fixed, or "starting fresh" |
| Testing and launching | The command that runs the tests or a manual check, and whether a command launches the app |

Leave out a question the description, the seed, or the code already answers. Put the recommended option first, and give every option a one-line description of what picking it means for the project. When an answer comes back partial ("not sure about tests"), ask that one question once more before going on.

The testing-and-launching answer resolves `test_command` and `build_command`: read `skills/verification/SKILL.md` and follow its `## Command Resolution`, with the answer as rule 1 when it names a command. Each holds the command string or `none (<reason>)`, never an empty value. `run_command` holds the launch command the answer named, or `none`.

## Init 3 -- Propose the phases

Present the split as a table:

```
| ID | Phase | Goal | Done when | Depends on |
|----|-------|------|-----------|------------|
| 1  | ...   | ...  | ...       | --         |
| 2  | ...   | ...  | ...       | 1          |
```

Each phase has 2-5 done criteria that a command or a check can show, and an out-of-scope line that names at least the later phases' work -- with one phase, at least one thing the project does not build. A small project gets one phase. Then ask one `AskUserQuestion`:

> Here is how I would split the project. Approving saves the phases and starts the first one.

Options:
- "Approve -- save the phases" -- Saves the roadmap and one file per phase, and starts the first phase now.
- "Change something" -- You say what to change; I redraw the table and ask again.
- "Start over" -- Drops this split and asks the project questions again.

On "Change something": ask what to change, update the table, ask again. On "Start over": return to Init 2.

## Init 4 -- Save

Get the date with the Bash tool (`date '+%Y-%m-%d'`). Before the first write into `.claude/ship/`, apply the keep-local rule in `skills/local-files/SKILL.md`. Then write, in the formats `# State Files` defines:

- `.claude/ship/roadmap.md`, every phase `pending`.
- `.claude/ship/decisions.md`, each project-level answer as one `D<n>` entry with `(user, <date>, phase init)`, the resolved `test_command`, `build_command`, and `run_command` among them.
- One `.claude/ship/phases/<id>-<slug>.md` per phase, with `status: pending` and `stage: questions`, its goal, scope, and done criteria from the approved table.

Read each file back (L3). Print `> Saved <N> phases under .claude/ship/. Starting phase <id> -- <name>.` and continue in the same turn with `## Step 1 -- Route` as a bare `/ship` -- the description is not a phase id -- which picks that phase. The approval is the consent `/ship` would otherwise give for the first phase.

---

# Phase Run

Runs one phase, the one Step 1 picked, from the stage its file records.

Every stage ends by writing the next `stage:` value and one `## Log` line (`- <YYYY-MM-DD HH:MM> <stage>: <one line>`) to the phase file, then starts the next stage in the same turn. The stage names are for the file: no status line and no question names a stage. Every phase-file write is read back (L3).

**Starting a phase.** When the phase is `pending`, set `status: in-progress` in its file and in the roadmap row, and set the roadmap's `## Now` line. When a phase in `depends_on` has a `branch:` that is not merged into `<default branch>` (`git branch --merged <default branch>` does not list it), print `> Phase <dep id> is not merged yet, so this phase continues on the current branch, <branch>.` Ship never merges or rebases.

**What starting a phase authorizes.** Approving the phases, or running `/ship` on an approved roadmap, is the consent for every phase the run starts: the spec and plan writes, the build through `/work --auto` with its per-task commits, the checks, the review, and the fix round. It does not authorize a push, a pull request, or a comment -- none of those is automatic -- and it does not stand in for a blocker: `/work` still asks when a task cannot proceed or a merge conflicts.

## Stage: questions

Read `.claude/ship/decisions.md`, this phase's file, and the `## Decisions` of the phases in `depends_on`. Earlier decisions are inputs, not questions.

Ask, in one `AskUserQuestion` call, every question about this phase whose answer changes what gets built, touches something outward-facing or destructive (a published name, a paid service, data that gets deleted), or picks between options the user can weigh. Put the recommended option first, with a one-line plain description per option. A technical detail the user would not weigh -- a file layout, a helper name, a test structure -- is your call: record it under `## Decisions` with `(agent, <date>)` and do not ask. When no question qualifies, ask nothing and print nothing.

Record each answer under `## Questions and Answers`.

## Stage: research

**What to look up.** List every fact this phase's spec or plan depends on that the answers, the decisions, and the seed do not state: a library or tool choice left open, a default or limit an output depends on, what a platform command returns, version compatibility. Write each as `<question> -- settled by: <what answer would settle it>`. With no such fact, print `> Nothing to look up -- every technical choice is already set.`, dispatch nothing, and go to the next stage.

**Dispatch, in one response.** Read `agents/research/stack-researcher.md` and dispatch `quiver:stack-researcher` with the input block its `## Input` section defines: the objective from this phase's goal; the stack and versions from the project decisions; the environment from the platform and deployment decision, including whether the target device, service or runtime is attached to this machine; the project root and whether it holds source; the constraints from the phase scope and the project decisions; the numbered questions; and a `search_language:` line only when the user named a search language. With more than six questions, split them into at most three non-overlapping groups and dispatch one agent per group. Dispatch `quiver:code-navigator` alongside it only when the project root holds a file other than `.git/`, `.claude/` and Markdown files -- on an empty root it returns nothing. Use the code-navigator block in `skills/plan/SKILL.md` Step 3, with this phase's goal as its task, and `codegraph_available` and `lsp_available` resolved as `skills/plan/SKILL.md` Step 2.5 describes. Wait for the completion notifications; never schedule a wakeup as a fallback.

**Use the answers.** Each question comes back under a `### Q<n> -- <status>` heading, as the agent's `## Output Format` defines. Route on the status:

- `answered` -- the question is not asked. The fact goes under `## Decisions` with its evidence line and into the spec and plan.
- `narrowed` -- ask it in the follow-up batch, with the recommended option first and the fact that decides between the options in each option's description.
- `open` -- ask it in the follow-up batch the way the phase questions ask any choice the user has not made.
- `needs-measurement` -- put "measure <what> on the target first" at the start of the plan task that depends on it.
- `premise-false` -- say what was wrong in the follow-up batch.

A limit a task could violate becomes a constraint candidate. Ask all of them in the follow-up batch as one multi-select question, each option's description naming the source the limit came from; the ones the user selects join the phase's decisions. code-navigator's report supplies the file paths and current patterns for the plan's tasks.

Print one status line: `> Looked up <N> questions -- <a> answered from sources, <b> need your pick, <c> still open, <d> need a measurement on the target, <e> rested on a wrong assumption.` Leave out any part whose count is zero.

## Stage: questions-2

Only when research returned a `narrowed`, `open`, or `premise-false` item whose answer changes what gets built, or a constraint candidate: ask one more `AskUserQuestion` batch holding exactly those, as the research stage describes. Record the answers under `## Questions and Answers`. Otherwise skip this stage silently. There is no third batch.

## Stage: spec

Get the date with the Bash tool (`date '+%Y-%m-%d'`). Write the phase spec to `.claude/specs/<date>-<project>-<phase-id>-<slug>.md`, creating `.claude/specs/` when it does not exist. Before the first write, apply the keep-local rule in `skills/local-files/SKILL.md` -- a project where `/brainstorm` never ran has not excluded the directory yet. The spec is in the format `skills/brainstorm/SKILL.md` Step 5 defines -- read that section before writing, including its read-back and self-review, and stop there: that skill's later review gate does not apply. Its header block reads `- **Status:** Approved in advance by the phase questions (<date>)` in place of `Draft`; there is no approval question. The executive summary, design, and success criteria come from the phase goal, scope, done criteria, answers, decisions, and research.

Record the path in `spec:`.

## Stage: plan

Write `.claude/plans/<date>-<project>-<phase-id>-plan.md`, creating `.claude/plans/` if it does not exist. Before the first write, apply the keep-local rule in `skills/local-files/SKILL.md`. When that path already exists, write `<date>-<project>-<phase-id>-plan-2.md`, then `-3`, and so on -- the first free name. An existing plan is never overwritten: its basename keys its `/work` ledger at `.claude/work/<plan-basename>/`, and a rewrite under the same name would resume that ledger's `complete` lines against tasks it never built. The file is a plan in the format `skills/plan/SKILL.md` Step 5 defines -- read that section before writing, and do not improvise a format of your own. `/work` reads this file exactly as it reads a `/plan` output; the format has one home, and this skill does not restate it.

What the phase becomes:

- **Frontmatter:** `name: <project>-<phase-id>-plan`, `status: active`, `created: <date>`, `spec_source: <spec path>`, then `stack`, `platform`, and `deployment_target` from the project decisions, then `test_command`, `build_command`, and `run_command` from the project decisions. When a recorded command is `none` and this phase is what creates the project's manifest, resolve `test_command` and `build_command` again by `skills/verification/SKILL.md` `## Command Resolution` after the stack is fixed; each still holds the command string or `none (<reason>)`, never an empty field.
- **Goal:** the phase goal, as the plan's opening section.
- **`## Global Constraints`:** the section Step 5 defines, holding the stack constraints and stated limits from the project and phase decisions -- one imperative sentence per numbered entry -- and the phase's out-of-scope line as "Do not build ..." entries, which is how `skills/plan/SKILL.md` Step 4.5 treats out-of-scope items. `/work` copies this section verbatim into every task brief and `/quiver:review --plan` binds its findings to it, so a constraint the plan does not record is one no implementer can honor.
- **Context:** when research ran, the Context section `skills/plan/SKILL.md` Step 5 defines, holding each finding with its evidence line and its attribution -- "(from stack-researcher)", "(from code-navigator)". Without research the section carries only a `### Plan Guard Notes` subsection when the Step 6 checks or the plan reviewer leave notes, and is omitted when there are none.
- **Tasks:** derived from the spec, in the task format Step 5 defines, each with its `**Files:**` line, its `**Provides:**` line where another task names what it creates, and an acceptance criterion. A dependency is written as a `blockedBy: [<task numbers>]` line under the task's `**Files:**` line -- the explicit-dependency field `skills/work/orchestrator.md` Section 1 reads; a task with none carries no line. When `test_command` is not `none`, order each task's steps test-first as Step 5 describes, naming `skills/tdd/SKILL.md`; `/work` follows that cycle when it builds.
- **Acceptance Criteria:** the phase's done criteria, as the plan's closing section.

Then run the checks of `skills/plan/SKILL.md` Step 6 by reading that section. The phase spec is the source specification Check 3 reads. Apply its action routing; do not present the checks to the user.

Then dispatch the plan reviewer once, as `skills/plan/SKILL.md` Step 6.5 describes -- read that section. Its two skip conditions do not apply: ship assesses no complexity, and this plan is not a review-fix plan. The phase spec is the source specification its prompt carries. Wait for the completion notification, then apply items 1-4 of that step's post-agent flow and come back here where they say to proceed: ship never continues to `skills/plan/SKILL.md` Step 7, which is a question to the user, and the phase questions already asked the last one. When the reviewer added or reordered a task, print one line naming the change: `> A second look changed the task list: <each added or moved task, one clause each>.`

After writing: read the plan back and confirm the `## Global Constraints` heading is present -- the out-of-scope line always names something not being built, so it always is -- and that every task another task names by symbol carries a `**Provides:**` line. A plan whose tasks share no symbol carries none, and that is correct: Check 8 is a no-op there, not a miss.

Record the path in `plan:` and print `> Wrote <N> tasks to <plan path>.`

## Stage: split

Decide whether the build runs in this session or in a fresh one. This is the only point where a phase moves to a fresh session: the phase file already holds everything the build needs, and a fresh session carries no research or question turns into it.

1. **Measure the context in use.** With the Bash tool, find this session's transcript: `find ~/.claude/projects -maxdepth 2 -name "${CLAUDE_SESSION_ID}.jsonl"`. Print its last usage entry: `grep '"usage"' <transcript path> | tail -1`. From that line's `usage` object, add `input_tokens`, `cache_creation_input_tokens`, and `cache_read_input_tokens` yourself: the sum is the context in use. The window is 1M tokens for Opus 4.7 and later, Sonnet 5 and later, Haiku 5.5, and Fable, and 200K for any other model. The transcript format is undocumented and written asynchronously: when the file is not found or the line carries no `usage` object, the context in use is unknown.
   <!-- ponytail: the window sizes are the 2026-10-16 defaults and the 30% and 8-task thresholds are unmeasured guesses; revisit both after five recorded phases, or when a model family changes its default window. -->
2. **Count the plan's tasks** (`### Task` headings in the file in `plan:`).
3. **Recommend a fresh session** when the context in use is at least 30% of the window, or the plan has at least 8 tasks. When the context in use is unknown, decide on the task count alone and print `> Could not read how much of this session is in use; deciding on the task count alone.`
4. **Ask only when recommending.** One `AskUserQuestion`:

   > This phase has <N> tasks and this session is <P>% full (or: this phase has <N> tasks). Writing the code in a fresh session leaves it more room. How do you want to go on?

   Options:
   - "Stop and continue in a fresh session" -- Everything so far is saved. Type /clear, set the effort to high for the coding (it is ${CLAUDE_EFFORT} now), then type /ship and it picks up where this stopped.
   - "Continue here" -- Starts writing the code in this session now. Coding runs best at high effort; this session is at ${CLAUDE_EFFORT}.

5. **Record** one line under `## Measurements`: `- <date> context: <P>% of <window> (<tokens> tokens) | tasks: <N> | choice: <here|fresh|not asked>`, with `context: unknown (<reason>)` when the transcript could not be read. The line is how the thresholds get tuned, so it is written on every run, asked or not.
6. On "Stop and continue in a fresh session": set `stage: build`, add the `## Log` line, print `> Saved. Next: /clear, then /ship.` and terminate. Otherwise set `stage: build` and continue.

## Stage: build

Ship implements nothing here: it hands the plan to `/work`.

**Stay on the branch ship started on.** Ship creates no branch. Started on `main` or `master`, `/work` Phase 2 creates the feature branch itself; started on a feature branch, its auto mode continues there. Do not switch branches to pre-empt either case.

**Hand off.** Print `> Writing the code now. This runs until every task is done or one needs you.` Invoke the `work` skill through the Skill tool with the plan path and `--auto` as its arguments (`/work <plan path> --auto`). The Skill tool does not run `/work` and come back: it loads `skills/work/SKILL.md` into this conversation as a message, the run continues here under `/work`'s instructions, and nothing signals its end -- `/work` ends at its Phase 5d summary. `/work` loads the file as a plan (its Case A path), resolves the verification command per `skills/verification/SKILL.md`, follows `skills/tdd/SKILL.md` on every task under its three-attempt fix cap, lets a subagent make the small wiring edits a task needs outside its file list and report them as discovered, commits per task, and in auto mode answers its routine gates: it continues on the current branch, commits the final leftovers, prints `/quiver:review` and `/create-pr` as text instead of running them, and keeps its workspace. It still stops for a blocker or a merge conflict; when it does, that question is the user's, not ship's -- never answer it for them. A task still failing after its third run is accepted and listed, on both of `/work`'s paths, never retried by ship.

**Continue.** The moment `/work`'s Phase 5d summary is printed, record `branch:` as the current branch, write `stage: verify` and its `## Log` line, print `> The code is written. Checking that it builds, passes its tests, and starts.`, and continue into the verify stage in the same turn -- before the turn ends, before any other question, and however long the run was. A run that stopped for a blocker and resumed on the user's answer is still this run, and its 5d summary is the same signal. A `/work` run that stopped on a blocker or a merge conflict has said so; still continue -- the final report is where the remaining work is listed. A turn that ended on the summary is recovered by the next `/ship` from the plan's `status: completed`, as Step 1 describes.

**Re-entry.** A phase resumed at this stage invokes `/work` with the same plan path and `--auto`. For a plan of 3+ tasks `/work` resumes from its ledger at `.claude/work/<plan-basename>/progress.md` and re-dispatches no task carrying a `complete` line. A 1-2 task plan, or a plan started in a repository with no commit yet, has no ledger; `/work` runs it from the top on the branch that carries the earlier commits.

## Stage: verify

This stage checks what `/work` built. It runs the build, runs the tests, and smoke-launches the app when the plan carries a run command. It changes no plan field. `--verify` re-enters here: when the phase's recorded stage is `verify` and its status is `in-progress`, the run continues to the review stage as usual; otherwise it prints the three lines, records them, and terminates without changing `stage` or `status`.

Read `test_command`, `build_command`, and `run_command` from the frontmatter of the file in `plan:`. A field that is absent resolves to `none (field missing)`; do not write it back. Verification runs on the branch `/work` left the session on.

### Build

When `build_command` is `none`: print `Build: skipped -- <reason>`.

Otherwise run it via the Bash tool and quote one evidence line per the Evidence Rule in `skills/verification/SKILL.md`: `pass: <command> -> exit 0: <summary line>` or `fail: <command> -> exit <code>: <first error line>`.

### Tests

When `test_command` is `none`: print `Tests: skipped -- <reason>`.

Otherwise run it via the Bash tool and quote one evidence line per the same Evidence Rule. A run whose summary line shows zero tests executed is `skipped: <reason>`, never `pass` -- cross-cutting rule 1 of that file.

### Smoke

When `run_command` is `none`: print `Smoke: skipped -- no run command`.

Otherwise launch the app with the run command via the Bash tool with `run_in_background`, then wait on a cheap readiness condition -- a port answering, a "Ready" log line, a booted simulator -- inside an `until` loop with a deadline of at most 120 seconds and a failure check on the log (a crash line, `Error:`, `EADDRINUSE`). Run the wait itself with `run_in_background` too, or with the `Monitor` tool where the session has it: a foreground `sleep` is blocked by the harness, so an `until ... sleep 1; done` issued inline is rejected before it polls once. Never poll by re-running the launch command. When a screenshot tool is available in the session (an iOS simulator or browser MCP), capture the first screen and flag placeholder text, a blank screen, or a visible error. Stop the process when done.

Record `Smoke: pass`, `Smoke: fail -- <first error line>`, or `Smoke: timeout -- <condition> not met in <N>s`.

### Record

Write the three lines under `## Measurements` (`- <date> build: ...`, `- <date> tests: ...`, `- <date> smoke: ...`), then `stage: review` and its `## Log` line.

## Stage: review

Without git, or when neither `main` nor `master` resolves (the user told `/work` to create no main branch in a repository with no commit), skip this stage and the fix stage: write `stage: done` with a `## Log` line saying the branch could not be reviewed and why, and go to the done stage.

Before the review writes its report, apply the keep-local rule in `skills/local-files/SKILL.md` to `.claude/reports/`: the review applies it only to its own default location, and ship names the directory explicitly below.

Print `> Reviewing the branch. Each problem the review finds is checked against the code before anything is fixed.` Invoke the `quiver:review` skill through the Skill tool with `--base <default branch> --run-checks --plan <plan path> --output .claude/reports` as its arguments, where `<plan path>` is the file in `plan:`. Use the qualified name: a bare `/review` is a bundled command's alias.

- `--base` puts the review in branch-diff mode and keeps it from asking for a base branch (`skills/review/SKILL.md` Step 1 Mode 2).
- `--run-checks` is required. Without it a branch review checks findings read-only, behavior findings come back unverified, and the fix stage sees fewer confirmed findings. This branch is the phase's own work, which is the case the flag is for.
- `--plan` binds the findings to the plan's `## Global Constraints`.
- `--output .claude/reports` fixes where the report lands for this run (`skills/review/SKILL.md` Step 4a item 3), so a saved report location cannot move the file Step 1 and the fix stage look for.

A second review on the same branch -- the one after the fix round -- finds the first report in `.claude/reports/` and reviews only the changes since it (its re-review detection). A saved report location points that detection elsewhere; the second review then covers the whole branch again, which costs more and changes nothing else here.

**Continue.** The review ends at its Step 4b summary, which names the saved report path. The moment that summary is printed, record the path in `review_report:`, write `stage: fix` and its `## Log` line, and continue into the fix stage in the same turn. A turn that ended on the summary is recovered by the next `/ship` from the report's `Branch` and `HEAD at review` lines, as Step 1 describes.

## Stage: fix

Read the report in `review_report:`. A confirmed finding is one in `## Findings` that carries a `Verification: confirmed` line. Findings marked `Verification: unverified`, and the ones listed as `refuted-by-verification` under `## Filtered Findings`, are not fixed: the final report lists them.

**When `fix_rounds` is already 1,** this report came from the review after the fix round. Fix nothing: write `stage: done` and go to the done stage, which lists its confirmed findings as open. One fix round per phase.

**Re-entry.** When `fix_plan:` is not `none`, an earlier run already asked the questions below and wrote the fix plan. Ask nothing, write no plan, and go to the hand-off with the plan in `fix_plan:`. For a plan of 3+ tasks `/work` resumes from its ledger and re-dispatches no task carrying a `complete` line, as the build stage's re-entry describes; a new plan name would key a new ledger and run the committed tasks again.

**With no confirmed finding,** write `stage: done` and go to the done stage.

**Stop for the user only here.** When a confirmed finding is Critical, or its fix would change behavior the phase spec defines, ask one question per such finding in a single `AskUserQuestion` call (at most four questions per call; ask any beyond four in a second call):

> The review found a problem it confirmed against the code: <the finding in one plain sentence> (<file:line>). What should happen?

Options, in this order for a Critical finding; for a behavior change, put "Leave it and list it" first:
- "Fix it" -- The next round of code changes fixes it, and the branch is built, tested, and reviewed once more afterwards.
- "Leave it and list it" -- Nothing changes for this problem; the final report lists it as open, and it does not stop the phase from finishing.
- "Stop this phase here" -- Nothing else runs; the phase is saved as stopped with this problem as the reason. Run /ship <phase-id> later to continue it.

Record each answer under `## Decisions` with `(user, <date>)`. On any "Stop this phase here": set `status: blocked` in the phase file and the roadmap row with the finding as the reason, write the final report as the done stage describes, and terminate.

**Write the fix plan** at `.claude/plans/<date>-<project>-<phase-id>-fix-plan.md` (the first free `-2`, `-3` name when taken), in the format `skills/plan/SKILL.md` Step 5 defines with its review-fix frontmatter: `review_source: <review_report path>` and `review_iteration: 1`, plus `status: active` and the `test_command`, `build_command`, and `run_command` of the phase plan. It holds only the confirmed findings to fix -- not the ones the user chose to leave -- one task per finding, each task naming the finding's report ID and title so `/work` matches it to the finding, and one acceptance criterion per finding as that step requires. Read it back (L3) and record the path in `fix_plan:`.

**Hand off.** Print `> Fixing <N> confirmed problems.` Invoke the `work` skill through the Skill tool with `<fix plan path> --auto` as its arguments. `/work` detects the review-fix plan by its `review_source` frontmatter and checks each finding against the report before it finishes; it keeps its own stops, and those questions are the user's. The moment `/work`'s Phase 5d summary is printed, write the `## Log` line `fix: not fixed: <the fix-plan task numbers the summary lists as accepted after three failed attempts, blocked, failed, or not run, or none>`, set `fix_rounds: 1`, write `stage: verify` and its `## Log` line, and run the verify stage once more in the same turn; it continues to the review. The done stage reads the check lines of the last verify, so the fix commits are built and tested before the phase can be `done` -- a fix task `/work` accepted after three failed attempts leaves a failing test line there.

## Stage: done

**Set the status from evidence.** Set `status: done` only when every verify line under `## Measurements` from this phase's last check is a pass or a skip, and no Critical finding is open. Otherwise set `status: blocked` with the reason (the failing check line, or the open Critical).

A Critical is one in the `## Findings` of the last review or, when `fix_plan:` is not `none`, of the first review: the report named by `review_source:` in the file at `fix_plan:`. Read both. The review after the fix round covers only the changes since the first report, so a Critical the fix round did not really fix is not in the last one. A Critical is open unless the user chose "Leave it and list it" or "I fixed it" for it under `## Decisions`. A Critical of the first review is also closed when a fix-plan task names it and the fix stage's `fix: not fixed:` line under `## Log` does not list that task; a Critical of the last review never is, since report IDs restart in every report and the review after the fix can report an incomplete fix under the same ID and title. With no such line -- the turn ended on `/work`'s summary and the next `/ship` resumed from the fix plan's status -- the Critical stays open, and the question in Step 1 settles it.

Without git, the review did not run; the phase can still be `done` on its check lines, and the final report says it was not reviewed.

Update the roadmap: the phase's row in `## Phases`, the `## Now` line, and the `## Next` line (the next `pending` phase whose dependencies are now `done`, or the pull request). Append to `decisions.md` every decision from this phase that applies beyond it, as `D<n>` entries with `phase <id>`. Write `stage: done` and its `## Log` line when the status is `done`. When it is `blocked`, write `stage: verify` instead, so `/ship <id>` checks the branch again and reviews the changes made since the phase stopped rather than re-reading the results that stopped it.

**Final report.** Write it under `## Final Report` in the phase file and print it. Write it in the user's language and in plain words, for a reader who has not read the code or this file:

1. What the phase now does, in two or three sentences.
2. Each decision you made on your own (the `(agent, ...)` entries under `## Decisions`), one line each.
3. The build, test, and smoke lines, as recorded.
4. The commits: `git log --oneline <default branch>..HEAD`.
5. Problems the review found: the ones fixed; the ones ruled out, with one evidence line each; the ones that could not be checked, with what was tried; and any left open, with the reason. When the review did not run, say so and name the command: `/quiver:review --base <default branch> --run-checks --plan <plan path>`.
6. What was not done or not measured: tasks `/work` reported blocked, failed, or accepted after three attempts, smoke flags, and anything the done criteria name that no check showed.
7. That nothing was pushed and no pull request was opened.
8. The next command: `/quiver:create-pr` to open the pull request for this branch. When the phase is `blocked`, `/ship <phase-id>` continues it. When the next phase starts in this run, say so instead of naming `/ship`.

`/create-pr` owns the pull request for the rest of the session. When the user asks for one after the run -- 'push and open a PR', 'create the PR' -- invoke the `create-pr` skill; never run `gh pr create` from this skill or from the conversation it leaves behind. The final report is input to that skill, which reads it as something said in this conversation, not a body to hand to `gh pr create`.

Read the phase file and the roadmap back (L3). **Go on to the next phase.** When the status is `done` and the roadmap has a `pending` phase whose `depends_on` phases are all `done`, print `> Phase <id> is done. Starting phase <next id> -- <name>.` and continue in the same turn with `## Step 1 -- Route` as a bare `/ship`, with no phase id or flag from this run's arguments, which picks it. Its stages measure this session again at the split, so a session that has grown full is offered a fresh one there. Otherwise terminate.
