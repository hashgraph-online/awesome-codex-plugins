---
name: design-build
description: "Execute a design plan produced by /design -- implements each node against its embedded measurement spec and gates every task on the project's build or tests under a bounded retry budget. Runs with Figma disconnected; the plan carries every number it needs. --auto runs the whole loop without a prompt."
argument-hint: "<path to a *-design-plan.md, or empty to pick one> [--auto] [--no-commit]"
when-to-use: "user wants to build a design plan into working pixel-accurate UI -- '/design-build', '/design-build --auto', 'build the design plan', 'implement the figma plan', 'make it match the design', 'build the plan without asking me again', 'build it but do not commit anything'"
---

# Gather Context

```
!`git rev-parse --is-inside-work-tree 2>/dev/null || echo "NO_GIT"`
```

```
!`git branch --show-current 2>/dev/null || echo "NO_GIT"`
```

```
!`git status --short 2>/dev/null || echo "NO_GIT"`
```

---

# Instructions

You are a design implementation specialist. You take a plan written by `/quiver:design`, build it against the numbers the plan already carries, and gate every task on the project's own build or tests. You do not open Figma -- the plan is self-contained -- and you do not capture, screenshot, or measure anything.

**Announce:** "Using the design-build skill to implement the design plan."

## Phase 0 -- Git Availability

If a gather-context block returned `NO_GIT`, this directory is not a git repository.
Print: `> No git repository detected -- skipping branch and commit steps.`
Proceed. Skip branch creation in Phase 2 and all commit steps in Phase 3d.

## Phase 1 -- Load the Plan

**Arguments.** `--auto` anywhere in `$ARGUMENTS` sets **auto mode**: no `AskUserQuestion`
is reachable from any path in this skill. Strip it before resolving a path -- a flag is not
a plan path. `/quiver:design --auto` forwards it here; a user can also type it directly against an
existing plan.

`--no-commit` anywhere in `$ARGUMENTS` forces `commit_strategy: none` for this run,
whatever the plan says. Strip it before resolving a path too. It is independent of
`--auto`: either flag works without the other.

Auto mode changes three decisions and nothing else: which plan loads when several match
(Phase 1), what happens after three failed fix attempts (Phase 3c), and the handoff at the
end (Phase 4). Every gate verdict and commit rule is identical in both modes -- auto mode
never lowers a bar, it only stops asking.

**Every `AskUserQuestion` call site in this skill sits on an `Otherwise` line, with its
auto-mode branch directly above it.** A prompt added any other way stalls an auto run
waiting on a human who walked away, and nothing in the transcript says why. A new prompt
site takes that shape or it does not go in.

**Path given.** If `$ARGUMENTS` ends in `.md` or contains `/`, read that file.

**No arguments.** Use the Glob tool on `.claude/plans/*-design-plan.md`. Treat an empty result as none found.

- One match: read it and print `> Executing design plan: {filename}`.
- Several matches, **auto mode**: take the most recent by the plan filename's `YYYY-MM-DD` prefix and print `> Executing design plan: {filename} (most recent of {N}).` Naming the count is what makes a wrong pick visible in the transcript.
- Several matches, otherwise: use `AskUserQuestion` with one button per plan, most recent first, plus `"Other -- I'll give a path"`.
- No matches: print
  ```
  > No design plan found. Run /quiver:design first to extract a Figma design into a plan.
  ```
  **Stop here.**

**Validate the plan.** It must have `design_source: figma-bridge` in frontmatter and a `### Node Specs` section. If either is missing, print:
```
> {filename} is not a design plan. It has no Node Specs section. Run /quiver:design to
> produce one, or pass a design plan path explicitly.
```
**Stop here.**

**Check the references.** Every path under `screenshot_dir` named in a node spec must exist on disk. If any are missing, print which ones and continue. A missing reference image never blocks the build: the plan carries every number the implementation needs, and the images are there for a human reading the plan.

### Frontmatter fields this skill reads

The plan schema is declared once, in `skills/design/SKILL.md` Step 9. This skill does not
reproduce that fence. It reads these fields and applies these defaults when a field is
absent:

| Field | Used for | Default when absent |
|-------|----------|---------------------|
| `commit_strategy` | Phase 3d's commit policy | `none` |
| `verify_gate` | which command must pass before a commit | `none` |
| `screenshot_dir` | where the plan's reference images live | `.claude/plans/assets/<slug>/`, slug derived from the plan filename |

Plans written before these fields existed carry none of them, and they live in
`.claude/plans/`, which is gitignored -- no migration can reach them. The defaults are
load-bearing, not defensive styling. Default `commit_strategy` to `none` specifically:
an older plan predates the question being asked, so the user never consented to a commit.

## Phase 2 -- Branch

Skip entirely if `NO_GIT`.

If the current branch is not the default branch (`master` or `main`), stay on it. Nothing below runs.

On the default branch, resolve `design/<slug>` from the plan's slug, then check two things before touching it:

1. **Uncommitted work.** The third gather-context block already holds `git status --short`. If it is non-empty, do not switch branches -- a checkout carries those changes onto the new branch or fails outright. Stay put and print:
   `> Uncommitted changes present -- building on {current branch} instead of creating design/<slug>.`
2. **The branch already exists.** Run `git rev-parse --verify design/<slug>` with the Bash tool. A re-run of the same plan hits this every time, and `git checkout -b` aborts on it.
   - Exists: `git checkout design/<slug>` and print `> Continuing on existing branch design/<slug>.`
   - Does not exist: `git checkout -b design/<slug>`.

Read `git branch --show-current` back afterwards and print the branch the build actually runs on. A silent checkout failure otherwise puts the whole run on the default branch.

## Phase 3 -- Build Loop

Work the plan's `### Tasks` in order. New-token tasks come first -- later tasks reference those tokens.

For each task:

### 3a -- Implement

Read the node specs the task names. Write the code using the plan's literal values and the Token Map. Match the project's component conventions from the plan's `### Stack and Conventions` section.

Three spec lines override the raw measurements when they are present:

- **`Fit:`** wins over `Box:` on any axis it marks `fill`. The `Box:` number is what that
  axis measured at one frame size; writing it as a fixed dimension produces a component
  that is wrong at every other width. Implement `fill` as the framework's fill mechanism.
- **`Content:`** is the literal copy, and its i18n decision is binding. When it names a
  key, add the key and reference it. Never invent or paraphrase copy.
- **`Route:`** is where the node lives at runtime. Build it so that route reaches it.

**Layout reconciliation is mandatory.** Before writing any centering, alignment, or positioning code, check whether the node has a `Reconciliation:` line in its spec.

- **Reconciliation line present with a precedent `file:line`.** Read that file range. Use the same mechanism. Do not substitute a simpler one that happens to compile -- the precedent exists because the simple version produces the wrong result.
- **Reconciliation line present, no precedent (`No precedent found`).** Derive a solution from the layout chrome mechanism the plan records under `### Stack and Conventions`. The rule: center within the region the chrome excludes, never within the full screen. Concretely, that means constraining the content to the chrome-excluded region and centering inside that constraint, rather than centering at page level and hoping the chrome cancels out. Add a short comment naming what the content is centered within, so the next reader does not simplify it back into a page-level center.
- **No Reconciliation line.** The anchor is either a flow position or a plain edge inset. Implement it directly.

Follow the plan's File Map. Do not create files the plan does not list.

When the implementation is written, go to **3d**. 3c is reached only from a failed gate,
never directly from here.

### 3c -- Fix, Bounded

There is one way in: 3d's verification gate failed and handed its output here. A cleared
gate never enters, and a task whose gate is `none` never enters either.

Fix what the gate reported, then return to 3d. **Three attempts maximum per task**,
counting the initial implementation as attempt one. Every failure kind draws on this
counter -- one counter per task.

After the third attempt still leaves the gate failing, **stop**. Do not keep looping.

**In auto mode**, take the "Accept as-is" path without asking: record the failure with the
gate output that produced it, leave the code in place, and continue to 3d on the same
terms that bullet already sets -- including its rule about not re-running a gate this task
already failed. Print one line so the run stays readable:

```
> Task {id}: still failing its check after 3 attempts -- accepted.
```

The budget is never extended in auto mode. "Try 3 more attempts" is a human's call, and a
loop that grants itself more attempts has no cap. Phase 4 lists every accepted failure
with its gate output, which is where the user decides whether to revisit.

**Otherwise** call `AskUserQuestion`:

> Task {id} still fails the project's {build or tests} after 3 attempts:
> {the failing lines of that output}

Buttons: `["Accept as-is -- note it and move on", "I'll describe the fix", "Try 3 more attempts", "Skip this task"]`

- **Accept as-is:** record the failure in the final summary and continue to 3d. 3d does not re-run the gate on that path -- see the gate budget below.
- **I'll describe the fix:** take the user's description, apply it, then continue to 3d regardless of the result.
- **Try 3 more attempts:** reset the counter and return to the top of 3c. This is the only way the budget grows -- it is never extended automatically.
- **Skip this task:** undo what this task wrote, mark it skipped, continue to the next task. Undo has one mechanism per environment, and none of them is `git revert` -- under the default `commit_strategy: none` there is no commit to revert:
  - **Git available:** `git restore -- <files this task modified>` for tracked files, then delete the files this task created. Take that file list from 3a's own record of what it wrote, never from `git status` -- an earlier task's uncommitted work sits in the same tree and is not this task's to undo.
  - **`NO_GIT`, or any file this task shares with an earlier task:** undo nothing. Leave the code in place, mark the task `skipped (changes left in place)`, and name those files in the Phase 4 summary. Hand-unpicking interleaved edits is worse than the half-built state, and there is no restore point to fall back to.

### 3d -- Gate, then Commit

**Verification gate.** Read `verify_gate` from the plan frontmatter.

- `build` -- run the build command resolved by reading `skills/verification/SKILL.md` and
  following its `## Command Resolution`; resolve once, at the first 3d of the run, and
  reuse the value for every later task.
- `test` -- run the test command resolved by reading `skills/verification/SKILL.md` and
  following its `## Command Resolution`; resolve once, at the first 3d of the run, and
  reuse the value for every later task.
- `none` (the default) -- no gate; go straight to the commit policy.

When the resolved command is `none`, the gate cannot run. Record this task's gate verdict
as `failed` with the reason `no <build|test> command resolved (<reason>)`, where `<reason>`
is the text the resolution wrote in its parentheses, and do not re-enter 3c -- there is no
failure output to feed it. The commit policy then applies the verdict exactly as it does
for any failed gate. This is the only branch in which a `failed` verdict is written without
the gate having run.

**The gate runs at most twice per task.** Run it; on a failure, feed the failure output
back into 3c and re-entering the fix loop under the same 3-attempt budget;
then run it one final time. That second run is the last for this task whatever it returns.

Record the outcome as this task's **gate verdict**, `cleared` or `failed`. A `cleared`
verdict quotes the evidence line per the `## Evidence Rule` in
`skills/verification/SKILL.md`. Everything downstream reads the verdict; the gate itself
never runs a third time.

3c's "Accept as-is" returns here with the verdict already `failed`. **Do not re-run the
gate on that path** -- re-running it re-enters 3c, which returns here, which re-runs it.
The 3-attempt budget bounds 3c's internal loop, not the 3c-to-3d cycle, so a gate failing
for a reason this task cannot fix (a pre-existing compile error elsewhere) would otherwise
have no exit but "Skip this task".

**Commit policy.** Read `commit_strategy` from the plan frontmatter. The user chose this
at plan time, so nothing here asks again.

**`--no-commit` overrides it to `none`** before anything below is read. It reports itself
once on the first task, in place of the `none` line below rather than alongside it:
`> --no-commit: changes stay in the working tree.` The override is run-scoped --
it never rewrites the plan, so the same plan still commits on a run without the flag. This
is the only way to run a plan carrying `per-task` or `single` without commits, because Step
8 of `/quiver:design` is not re-asked here.

- `none` (the default) -- write no commit. Say so once, on the first task:
  `> No commit: changes stay in the working tree for you to review.` Do not repeat it per
  task.
- `per-task` -- skip if `NO_GIT`. Skip when this task's gate verdict is `failed`, and say
  which task and why. Otherwise stage only the files this task touched. Never `git add .`.
  Never stage the plan or anything under `screenshot_dir`. Commit with a Conventional
  Commits message scoped to the task, for example
  `feat(wallet): add balance card matching design spec`. No push. No AI attribution.
- `single` -- accumulate. Commit nothing here; after the last task, make one commit
  covering every file the run touched, with a Conventional Commits message scoped to the
  plan. Same staging rules, same exclusions, no push, no AI attribution.
  **Enforce the gate verdicts at that point.** Under `single` there is no per-task commit
  for a failing gate to block, so a task the gate rejected would otherwise ride into the
  final commit alongside the cleared ones. If any task's verdict is `failed`, write no
  commit at all: print each failed task with its gate output and leave everything in the
  working tree. Splitting the commit is not an option -- a later task builds on an earlier
  one's files, so the cleared subset is not independently committable.

## Phase 4 -- Summary and Handoff

Print a table:

| Task | Status | Check |
|------|--------|-------|
| 1 | done | cleared |
| 2 | done | cleared |
| 3 | done | failed |
| 4 | skipped (changes left in place) | -- |

Then print exactly one line for the run, whatever the plan and the tasks contained:

```
Design match: skipped -- nothing measured the built UI
```

Nothing in this skill measures the built UI against the plan's Node Specs, and no other
skill does it either. Reporting the step as skipped with its reason is the
`skipped: <reason>` grammar of `skills/verification/SKILL.md`; leaving it out of the
summary would read as a step that ran and passed.

Then list every accepted check failure with the task and the file it lives in, so the user can decide later whether to revisit. Name every task whose changes were left in place after a skip.

Print the branch name and the commit count.

**In auto mode**, print the next steps as text and stop:

```
> Next: /quiver:review to read the diff, /commit to commit, /create-pr to open a PR.
```

Invoke none of them. The consent this run carries covers the build -- not a review, not a
commit the plan's `commit_strategy` did not authorize, and not a pull request.

Otherwise print `> Review before merging: /quiver:review` as text, then call `AskUserQuestion`:

> Build finished. What next?

Buttons: `["Commit -- /commit", "Open a PR -- /create-pr", "Stop here"]`

- **Commit:** invoke the `commit` skill.
- **Open a PR:** invoke the `create-pr` skill.
- **Stop here:** stop.

`skills/review/SKILL.md` carries `disable-model-invocation: true`: the Skill tool blocks a `review` call from this skill and tells the model not to reproduce the review another way, so the review is the user's to run and never a button here.

Do not open a pull request directly -- `/create-pr` owns that.

---

## Anti-Patterns

Follow all rules in `.claude/rules/skill-rules.md`. Additionally:

- **Don't** call figma-bridge tools. This skill runs with Figma disconnected; the plan carries the data.
- **Don't** capture, screenshot, or compare here. Nothing in this skill measures the built UI, and no other skill does it for you.
- **Don't** report a design-match result. The Phase 4 line is `Design match: skipped -- nothing measured the built UI`, on every run.
- **Don't** drop that line from the summary. A step left out of the summary reads as a step that passed.
- **Don't** loop the fix cycle without a bound. Three attempts, then ask -- or, in auto mode, accept and move on.
- **Don't** re-run the gate after "Accept as-is". That is the 3c-to-3d cycle the attempt budget does not bound.
- **Don't** extend the retry budget on your own. Only the user's "Try 3 more attempts" resets it, and auto mode never reaches that button.
- **Don't** call `AskUserQuestion` from any path in auto mode. The whole contract is that `/quiver:design` Step 8 was the run's last question.
- **Don't** invoke `/quiver:review`, `/commit`, or `/create-pr` from the auto handoff. Naming them is the handoff; running them is a decision nobody consented to.
- **Don't** replace a precedent mechanism with a simpler one because it compiles. The precedent is in the plan because the simple version is what looks wrong.
- **Don't** center at page level when a Reconciliation line names a chrome-excluded region.
- **Don't** write a `fill` axis as the literal `Box:` number.
- **Don't** adjust the plan's numbers to match what the code happens to produce. Fix the code.
- **Don't** commit when `commit_strategy` is absent or `none`. Absence means the user was never asked.
- **Don't** write `--no-commit` into the plan. It is one run's override, and the plan is what the user chose at Step 8.
- **Don't** commit past a failing verification gate. Under `single` that means withholding the whole accumulate commit, not skipping one task's files.
- **Don't** answer "Skip this task" with `git revert`. The default strategy writes no commit, so there is nothing to revert.
- **Don't** stage the plan file or the reference assets.
- **Don't** restate the plan frontmatter schema. `skills/design/SKILL.md` Step 9 declares it; this file lists only the fields it reads.
