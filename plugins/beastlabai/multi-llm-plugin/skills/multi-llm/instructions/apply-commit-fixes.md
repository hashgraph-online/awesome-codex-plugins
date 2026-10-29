# Apply Commit Fixes Mode Instructions

Applies a commit review's validated fixes to the code as uncommitted edits: the
commit-range counterpart of apply-code-fixes, run on the review's **commit brief**.
A front door finds the review, prints the commits it covers and runs apply-code-fixes
on the brief, whose guard first compares every fix file with the reviewed commit and
skips the fixes to files changed since. This file says only how to start that front
door and how to hand over to apply-code-fixes' own core, which does everything after
its orchestrator call: the decisions, the batch loop, verification, the summary and
the phase's completion. Nothing is committed. The core ends with section 4.

## Usage

```bash
/multi-llm:multi-llm --apply-commit-fixes [<range>] [options]
```

The options are apply-code-fixes' own (`--agent-decide`, `--no-confirm`, `--resume`,
`--dry-run`, `--min-priority`, …); `--plan-file`, `--base-ref` and `--head-ref` are
the front door's and are refused with `[COMMIT_FLAG_CONFLICT]`.

## Which review it applies

- **A range** opens that range's review. The range is read as `--review-commits`
  reads it: optional, bare words joined into one range with no quotes needed
  (unlike `--ask`'s question), right after the mode word before any flag
  (`[RANGE_AFTER_FLAGS]` otherwise, exit 3), and one range per run. A phrase is
  resolved again now, so `last 2 commits` typed after a new commit names another
  range: the pinned `<base12>..<head12>` (or brief path) the review printed is the
  spelling that always names the reviewed range. A range with no completed review
  exits 3 with `[COMMIT_REVIEW_NOT_FOUND]`, naming `--review-commits <range>`.
- **No range** applies the newest completed commit review whose last commit is
  `HEAD` or in its history. The commit block says which, on its
  `[COMMIT_REVIEW_SELECTED]` line. With none, the exit-3 `[COMMIT_REVIEW_NOT_FOUND]`
  listing names each candidate with the command that applies it.
- **The review on record is applied as it is.** A typed `--focus` or
  `--context-plan` that differs from it changes nothing here: the front door prints
  `[COMMIT_REVIEW_KEPT]`, naming the commands that review with it.
- **The user's decisions count.** Skips, overrides and edited descriptions marked in
  the review's `report.md`, or exported from its `report.html` as
  `user_selections.json`, are honoured as for any apply. With none anywhere, D6
  row 11 asks before every valid fix is applied, unless `--no-confirm` (or `--yes`)
  was given.

## What it prints, and what you relay

- **The commit block**, `[COMMIT_RANGE] …` to `[COMMIT_RANGE_END]`, printed before
  anything is read or written, one line per commit.
- **`[COMMIT_BRIEF] <path>`**, outside the block: read, not relayed. Its path is the
  plan path of every command after section 1.
- **The fixes block**, `[COMMIT_FIXES] …` to `[COMMIT_FIXES_END]`, printed by the
  apply phase once its guard has decided, before any batch: the fixes to apply per
  commit, the unattributed ones, and the ones skipped because a file changed since
  the reviewed commit or because the review's context plan is read-only.

**Relay each of the two blocks verbatim and once**, the whole block from its opening
marker to its end marker, the first time it prints. This is the one exception to
"nothing else is relayed" mid-run. `[COMMIT_REVIEW_KEPT]` and
`[COMMIT_REVIEWS_NOT_IGNORED]` are notices: give each one printed, whole, in
section 4's report.

## Unattended rows

| Row | Where | Resolution |
| --- | --- | --- |
| D6 row 1, uv missing | before section 1 | the prerequisite below: print `hosts/uv-missing.txt`, stop with exit 3 |
| D6 row 10, `needs-human-decision` items | section 3 | apply-code-fixes' own rule: `--agent-decide` (which `--yes` sets) lets the judge agent decide; otherwise ask the user |
| D6 row 11, no-selection confirmation | section 3 | apply-code-fixes' step 2a: `--no-confirm` or `--yes` applies every valid fix without asking |

---

## Step-by-Step Execution

**Prerequisite — `uv` (D6 row 1).** Every command below runs through `uv run`.
If it is absent the resolution is fail-closed: print `hosts/uv-missing.txt`
verbatim and **stop with exit 3** — never install it, never ask, never fall back
to bare `python`.

### 1. Run the front door

Run the mode with every token the user typed but the mode flag, exactly as typed:
the range words (the bare words right after the mode flag) first, then the rest in
the order typed. Run it **in the foreground**:

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-commit-fixes <the tokens the user typed> --host <host-id>
```

`<host-id>` and the other tokens your dispatcher command carries are added as for any
mode. This call is apply-code-fixes' orchestrator call (its step 2), so run it as
that core runs its own: it only prepares the batches, and returns quickly. On a host
that adds `--exec-subagents` the whole apply runs in this one call, and that core's
notes on the executor leg apply to it unchanged.

**A run that prints no `[COMMIT_BRIEF]` stopped before writing anything:** exit 2
`[NOTHING_TO_REVIEW]` (no commits yet), or exit 3 for a review it cannot find
(`[COMMIT_REVIEW_NOT_FOUND]` and its listing), a range it cannot resolve
(`[RANGE_UNRECOGNIZED]`, `[RANGE_DIVERGED]`, `[RANGE_SHALLOW]`, `[RANGE_BAD_REF]`,
`[RANGE_UNRESOLVED]`), a flag in the wrong place (`[RANGE_AFTER_FLAGS]`,
`[COMMIT_FLAG_CONFLICT]`) or a live run that owns the apply. Report the error line
whole, with every way forward it names, and stop: nothing was applied, and there is
no next step.

Everything the call prints after `[COMMIT_BRIEF]` is apply-code-fixes' own output,
the `[COMMIT_FIXES]` block included, and its exit code is that phase's.

### 2. Load apply-code-fixes' core

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util instructions apply-code-fixes
```

In it, `$PLAN_PATH` is the path `[COMMIT_BRIEF]` printed (copied, never re-typed);
`{plan}` is that path without its `.md`, the brief's output folder; and
`$STATE_FILE` is `{plan}/state.json`. The brief stands in for the plan everywhere
that core says "plan".

### 3. Continue from its step 2a

Skip its step 1 (the front door already refused a range with no completed review)
and its step 2 (section 1 was that orchestrator call). From step 2a on, run every
step exactly as that core words it, with these additions:

- **Step 2a's re-run** is section 1's command with `--no-confirm` appended, never a
  re-typed `apply-code-fixes` command. It prints the commit block again: relay no
  block a second time.
- **`[COMMIT_FIXES_STALE] <task id>: <files> changed since reviewed commit <head7>`**,
  printed by `util write-prompt` in place of `[WRITE_PROMPT]`, means that batch's
  files changed after the guard decided: no prompt was written, so spawn no
  subagent for it and record nothing for it (its groups are already recorded as
  skipped or held back), and go on to the next batch. The loop still reaches its
  end. Give the line, whole, in section 4's report.
- **`[COMMIT_PROTECTED_WRITE] <task id>: <paths>`**, `util batch-done`'s exit 3,
  means the batch wrote a file that changed since the reviewed commit and was
  protected from every batch. Stop the loop as for a partial application: the batch
  is not recorded as done, the phase stays incomplete, and the line names the way
  back for each path: the copy under `{plan}/apply-fixes/protected/` when it holds
  what the file had before the batch, else putting the file back by hand. Report it
  whole.
- **Step 8's summary names the brief as the commit brief.** Its template's
  `**Plan**: /path/to/plan.md` line is `**Commit brief**: $PLAN_PATH`, as the
  `--exec-subagents` leg writes it: no line a user reads calls the brief a plan.
- **Step 9's section goes in the brief, below its closing marker.** Append
  `## Code Fixes Applied` after the brief's `<!-- /multi-llm:commit-brief -->`
  line, never above it: the header above that line is the plugin's, and it is
  rewritten when the review restarts, while everything below it is kept.
- **Step 10's `--mark-completed`** takes the brief as its plan path, as that core
  spells it, and runs only when the batch loop reached its end.

### 4. Report

Report as apply-code-fixes' core says after its step 10 (or, when the loop stopped,
as its stop says), naming `{plan}/apply-fixes/summary.md` and every other file the
phase wrote. Also:

- name the commit brief (`$PLAN_PATH`), and for every fix the guard skipped, the
  changed file that caused it, as the `[COMMIT_FIXES]` block named it;
- give each notice and each `[COMMIT_FIXES_STALE]` line, whole, when one printed;
- never relay a block a second time.

After a run that exits `0` or `2` with `next` `null`, get the next step, after every
other command, on every host:

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util next-command "$PLAN_PATH" --after apply-code-fixes --host <host-id>
```

The plan path is the brief, and `--after apply-code-fixes` is the phase this mode
fronts, so the lookup walks on from the apply: normally to "Workflow complete.". After
`1` or `3` there is no next step, and the stop's own output only says to re-invoke
with `--resume`, without the command. Get it from the same lookup with
`--blocked apply-commit-fixes` in place of `--after apply-code-fixes`: its
`[RESUME_COMMAND]` line is the command that continues the run
(`--apply-commit-fixes <base12>..<head12> --resume`, the brief path on a root
range, in your host's spelling). End the report with the lookup's block, as the
`### Next Steps` rule in `references/summary-format.md` says.
