# Review Commits Mode Instructions

Reviews a range of commits with every model: what was committed, not what is on
disk. It is review-code run on a **commit brief** instead of a plan. A front door
resolves the range, prints the commits it covers, writes the brief (the commit
messages are the stated intent) and runs review-code on it at the range's two
commits. This file says only how to start that front door and how to hand over to
review-code's own core, which does everything after the launch: the poll loop,
salvage, validation, `--reaggregate` and the report. The core ends with section 4.

## Usage

```bash
/multi-llm:multi-llm --review-commits [<range>] [--quick | --models provider:model ...] [--focus "<text>"] [--context-plan <path>] [--files <path> (repeatable) | --files-from <file>] [--force]
```

## The range

- **Optional.** No range means `HEAD`: the last commit on the current branch,
  against its first parent.
- **What it can be.** Git revision syntax (`abc123`, `HEAD~2`, a tag or branch,
  `A..B`, `A...B`) or one phrase: `last commit`, `last 2 commits`, `-2`,
  `last two days`, `today`, `yesterday`, `this week`, `since <rev>`,
  `since 2026-10-01`, `this branch`. A commit brief's path is a range too (the
  pinned follow-up of a range that starts at the root commit). Python resolves it;
  never interpret, translate, re-type or re-order the user's words.
- **Bare words are joined.** `--review-commits last 2 commits` needs no quotes:
  every bare word right after the mode word, a `-N` included, is one range. This
  differs from `--ask`, whose question must arrive as one quoted argument.
- **The range comes right after the mode word, before any flag.** A range word
  after a flag is refused with `[RANGE_AFTER_FLAGS]` (exit 3) and nothing is
  written; the message names the command with the words moved where they belong.
- **One range per run.** Two ranges typed together (`A..B C..D`, `HEAD~3 HEAD`)
  are refused with `[RANGE_UNRECOGNIZED] … one range per run`.
- **A plan is never the range.** There is no plan by default. To review the commits
  against a plan, keep the range and add `--context-plan <path>`; `--plan-file`,
  `--base-ref` and `--head-ref` are the front door's own and are refused with
  `[COMMIT_FLAG_CONFLICT]`.

## What the front door prints, and what you relay

Before any model runs it prints the **commit block**, one line per commit:

```text
[COMMIT_RANGE] a1b2c3d..e4f5a6b (3 commits, 14 files, +412 −88)
  e4f5a6b  2026-10-24  Wait for the clock to tick in the shared-ps-table row
  …
[COMMIT_RANGE_END]
```

The block may carry a `window:` line, `NOTE:` lines, `[RANGE_LARGE]` and
`[SCOPE_DRIFT]` (a reviewed file changed on disk since the range's last commit).
Then, outside the block, `[COMMIT_BRIEF] <path>`: the brief this review runs on.

- **Relay the commit block verbatim and once**, the whole block from
  `[COMMIT_RANGE]` to `[COMMIT_RANGE_END]`, as soon as you have read it. This is
  the one exception to the poll loop's "nothing else from the view is relayed".
- **`[COMMIT_BRIEF]` is read, not relayed.** Its path is the plan path of every
  command after the launch (section 3).
- **Notices for the report.** `[COMMIT_REVIEW_RESTARTED]` (a typed `--focus` or
  `--context-plan` changed the review's identity, so a new round starts),
  `[COMMIT_REVIEW_ARCHIVED]`, `[COMMIT_DECISIONS_DROPPED]` (report decisions of
  the round set aside, which are not carried over), `[CONTEXT_PLAN_CHANGED]` and
  `[COMMIT_REVIEWS_NOT_IGNORED]`: give each one the launch printed, whole, in
  section 4's report.

## Unattended rows

| Row | Where | Resolution |
| --- | --- | --- |
| D6 row 1, uv missing | before section 1 | the prerequisite below: print `hosts/uv-missing.txt`, stop with exit 3 |
| D6 row 2, model selection | section 1 | `--yes`, `--models` or `--quick` as typed; otherwise ask the user before the launch |
| D6 row 3, partial fan-out results | section 3 | review-code's own rule under `--yes`: resume the missing models once, then `[PARTIAL_RESULTS: …]` and exit 0 |

Code review has no consolidation pass, and `needs-human-decision` items are decided
later, by `--apply-commit-fixes`: never ask about them here.

---

## Step-by-Step Execution

**Prerequisite — `uv` (D6 row 1).** Every command below runs through `uv run`.
If it is absent the resolution is fail-closed: print `hosts/uv-missing.txt`
verbatim and **stop with exit 3** — never install it, never ask, never fall back
to bare `python`.

### 1. Run the front door

**Models first (D6 row 2).** When the user typed `--models`, `--quick` or `--yes`
(or your dispatcher command carries `--yes`), add no model flag: under `--yes` the
review resolves `defaults.models` itself, and exits 3 naming the flags when nothing
resolves. Otherwise **ask the user** which models to use (multi-select, from the
configured providers) and add `--models <selected>` after the user's tokens.

Then launch the mode with every token the user typed but the mode flag, exactly
as typed: the range words (the bare words right after the mode flag) first, then the
rest in the order typed. Then **run detached**:

```bash
PYTHONUNBUFFERED=1 uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-commits <the tokens the user typed> --host <host-id> [--models <selected>]
```

`<host-id>` and the other tokens your dispatcher command carries are added as
for any mode. *Run detached* takes one of two shapes; use exactly one:

- **With `--detach`:** add it. The call returns within seconds, and its own output
  holds the commit block, `[COMMIT_BRIEF] <path>` and the `status` command the
  launcher printed for the poll loop.
- **Through your host's own background mechanism:** launch the command through it
  as your host's *run detached* answer says, its timeout included, but give it
  **no redirect**. The phase dir a log would go in is
  `<brief folder>/code-review/`, which nothing names before this run prints
  `[COMMIT_BRIEF]`, so read the run's output where your mechanism keeps it. The
  commit block and `[COMMIT_BRIEF]` print within seconds, before any model runs:
  read that output until one of them, or the process's exit, is there. Wherever
  review-code's core reads `{plan}/code-review/orchestrator-run.log`, read this
  output instead.

**A run that prints no `[COMMIT_BRIEF]` stopped before writing anything:** exit 2
`[NOTHING_TO_REVIEW] …` (an empty range, or no commits yet), or exit 3 for a range
it cannot resolve (`[RANGE_UNRECOGNIZED]`, `[RANGE_DIVERGED]`, `[RANGE_SHALLOW]`,
`[RANGE_BAD_REF]`, `[RANGE_UNRESOLVED]`, `[COMMIT_REVIEW_NOT_FOUND]`), a flag in the
wrong place (`[RANGE_AFTER_FLAGS]`, `[COMMIT_FLAG_CONFLICT]`) or a live run that owns
the review. Report the error line whole, with the way forward it names, and stop:
nothing ran, so there is no poll, no report of findings and no next step.

### 2. Load review-code's core

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util instructions review-code
```

In it, `$PLAN_PATH` is the path `[COMMIT_BRIEF]` printed (copied, never
re-typed); `{plan}` is that path without its `.md`, the brief's output folder
(`plans/commit-reviews/<slug>.md` → `plans/commit-reviews/<slug>/`); and
`$STATE_FILE` is `{plan}/state.json`. The brief stands in for the plan everywhere
that core says "plan".

### 3. Continue from the step after its fan-out launch

Start in its step 5 right after the launch command, which section 1 already ran:
the one non-waiting roster call, the poll loop with its five rules, then step 6
(salvage and its `--reaggregate`) and step 7 (validation, `--reaggregate` and its
`util metrics finish`), each exactly as that core words it, with `$PLAN_PATH`
the brief, except that its follow-up commands are the ones the run prints
(below). Skip its steps 1 to 4 and the launch itself: the front door wrote the
brief, section 1 settled the models, the front door hands review-code the range's
two commits (never `head_at_start` or `HEAD~1`), and review-code's own guards
cover resume. Its step 8 and the fix half of its *Post-Fix Workflow* run only
under `--apply-fixes`, which this mode does not use; fixes are applied by
`--apply-commit-fixes`. That workflow's step 6, the report, is section 4 below.

- **An exit 2 from the launch** with `[COMMIT_BRIEF]` printed means the review on
  record is complete for this brief: there is nothing to poll, so go to section 4.
  An exit `1` or `3` after `[COMMIT_BRIEF]` is review-code's own (a partial round
  on disk, no model resolved): stop and report it as that core says.
- **Follow-ups run as printed.** On a brief, review-code prints its follow-ups as
  this mode with the pinned range: `review-commits <base12>..<head12> … --reaggregate`
  (its `next` after validation, `[REAGGREGATE_AFTER_SALVAGE]` after salvage), and
  the `--force` retry a zero-result exit names, with the brief path in the range's
  place on a root range. Wherever that core runs or offers one of them, it spells or
  rebuilds its own `review-code --plan-file "$PLAN_PATH"` form: use the printed line
  instead, verbatim. The pinned range takes it back through the front door to this
  brief and its round, and the commit block that pass prints is not relayed a
  second time. Never put the words the user typed there instead: a phrase is
  resolved afresh, and once the branch moves it names another range. The phase
  after the reaggregate, the `--apply-commit-fixes …` it prints as its next step,
  is the user's to type, and section 4's lookup gives it; never run it. Every
  `status` and `util` call takes the brief as its plan path, as that core spells
  them.
- **A relaunch nothing printed** (the `--force` resume or the `--reaggregate` your
  host's *run detached* answer offers after a stopped run) is section 1's command
  with the brief path `[COMMIT_BRIEF]` printed in place of the range words, a range
  in its own right, then that verb.

### 4. Report

Report as review-code's core words its report (its *Post-Fix Workflow* step 6,
with no fix tasks): the files in `{plan}/code-review/`, the verdict counts, every
reviewer that produced nothing with its reason, and any `[RESULT_FILE_MISNAMED]`
or `[RESULT_SET_ASIDE]` line as printed. Also:

- name the commit brief (`$PLAN_PATH`) and both reports, `{plan}/code-review/report.md`
  and `{plan}/code-review/report.html`: the user reads them, and can mark skips,
  overrides and edited descriptions in either, before applying the fixes;
- give each notice listed under *What the front door prints*, whole, when the
  launch printed one;
- never relay the commit block a second time.

Then get the next step, after every other command, on every host:

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util next-command "$PLAN_PATH" --after review-code --host <host-id>
```

The plan path is the brief, and `--after review-code` is the phase this mode
fronts: the lookup spells its answer as the commit mode with the pinned range
(`--apply-commit-fixes <base12>..<head12>`), never as `apply-code-fixes` and never
with the phrase the user typed. End the report with its block, as the
`### Next Steps` rule in `references/summary-format.md` says.
