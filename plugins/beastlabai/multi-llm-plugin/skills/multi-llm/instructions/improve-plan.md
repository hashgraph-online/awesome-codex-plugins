# Improve Plan Mode Instructions

Reviews a plan with every model, then applies the validated suggestions to it, in
one unattended command. It runs two phases that exist on their own, review-plan and
then apply-suggestions, by loading each phase's own core; this file says only which
steps to run, with which flags, and how to report them.

## Usage

```bash
/multi-llm:multi-llm --improve-plan <plan_path> [--quick | --models provider:model ...] [--force] [--resume]
```

## What it runs

| Step | Phase core | Flags it gets (`util improve-steps` prints them) |
| --- | --- | --- |
| 1 | `review-plan` | `--yes`, plus `--models …` or `--quick` when the user typed one; `--force --rerun-all` on a new round (`--force`) |
| 1b | `review-plan --consolidate` | `--consolidate --yes`, only when the review recommends consolidation |
| 2 | `apply-suggestions` | `--yes --agent-decide --no-confirm`, plus `--resume` when an interrupted apply continues |

Python decides every flag. Never compose one, add one or drop one: pass the tokens
after each step's `[IMPROVE_STEP_FLAGS] <index>` exactly as printed, never the marker
or the index.

## What a run writes, unattended

- **The plan, edited in place.** The plan as it was before the apply stays in
  `{plan}/apply-suggestions/backup.md`. After a `--force` round that file is the plan
  as that round's apply found it, and the earlier round's backup is kept beside it as
  `backup.<sha8>.md`.
- **The review's files** in `{plan}/review-plan/` (reports, `grouped.json`,
  `validation.json`, one result per model), and, when consolidation runs,
  `consolidated.json` and the consolidated report, every decision box unticked.
- **The apply's files** in `{plan}/apply-suggestions/`: `summary.md`,
  `orchestrator_output.json`, `write_tasks.json`; the decision badges on
  `{plan}/review-plan/report.html`; and the records in `{plan}/state.json`.
- **Nobody is asked.** A judge agent decides every `needs-human-decision` item, and
  `summary.md` names the judge and each decision it made. Nothing refuses a dirty
  tree: committing or stashing first is what makes `git diff` show exactly this run.

## Unattended rows

The run is unattended whatever the user typed: every row it reaches resolves as below,
and no question is ever rendered.

| Row | Where | Resolution |
| --- | --- | --- |
| D6 row 1, uv missing | before step 1 | the prerequisite below: print `hosts/uv-missing.txt`, stop with exit 3 |
| D6 row 2, model selection | step 1 | `--yes` with the flags line's `--models` or `--quick`, else `defaults.models`; nothing asked, and exit 3 from the review when nothing resolves |
| D6 row 3, partial fan-out results | step 1 | the review core's `--yes` path: resume the missing models once, then `[PARTIAL_RESULTS: …]` and exit 0; zero results is exit 3 |
| D6 row 4, consolidation | step 1b | auto-run once when recommended; a pass that fails is a warning, and step 2 still runs |
| D6 row 10, `needs-human-decision` items | step 2 | `--agent-decide`: the judge agent decides every item, nobody is asked |
| D6 row 11, no-selection confirmation | step 2 | `--no-confirm`: every valid item is applied without asking |
| D6 row 14, a step fails | section 3 | stop, report the stop, give `[IMPROVE_RERUN]` as the way to continue; never ask whether to go on |
| D6 row 15, an empty or unrecognized decision flag (`--models ""`) | step 1 | `util improve-steps` exits 3 before any step runs |

`--interactive` (or `-i`) is no row: `util improve-steps` refuses it with exit 3 and
names the two phases to run instead.

---

## Step-by-Step Execution

**Prerequisite — `uv` (D6 row 1).** Every command below runs through `uv run`.
If it is absent the resolution is fail-closed: print `hosts/uv-missing.txt`
verbatim and **stop with exit 3** — never install it, never ask, never fall back
to bare `python`.

*Step 1*, *step 1b* and *step 2* below are the steps `util improve-steps` prints (the
review, the consolidation pass and the apply); this file's own sections are numbered 1
to 4. Keep going from step to step in one turn: do not end your turn between steps,
and do not announce the run as done before section 4's report.

### 1. Plan the steps

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util improve-steps "$PLAN_PATH" --mode improve-plan --host <host-id> <the flags the user typed>
```

`<host-id>` is the host id your dispatcher command carries; it makes the printed
continuation your host's spelling. Then pass every flag the user typed, exactly as
typed, `--interactive` and `-i` included: the util refuses what it must, and this core
never checks or drops a flag itself. It prints one block per step, for example:

```text
  [IMPROVE_STEP] 1 review-plan run (not reviewed yet)
  [IMPROVE_STEP_FLAGS] 1 --yes --quick
  [IMPROVE_STEP] 1b consolidate after-review (runs if the review recommends it)
  [IMPROVE_STEP_FLAGS] 1b --consolidate --yes
  [IMPROVE_STEP] 2 apply-suggestions run (review not applied yet)
  [IMPROVE_STEP_FLAGS] 2 --yes --agent-decide --no-confirm
  [IMPROVE_RERUN] <the command that continues this run, in your host's spelling>
```

(indented here; the util prints each line at its start). A step it passes over reads
`skip (<why>)` instead of `run`. `[IMPROVE_STEP_FRESH]` appears only for a review that
must start over. Keep the whole block: sections 2, 3 and 4 read it.

Read its exit code here; section 3's rule covers only the phase steps:

- `0`: go on to section 2, which runs the printed steps in order: 1, 1b, 2.
- `2` with `[ALREADY_COMPLETE] …`: both steps are done for this review. Run no phase
  and go to section 4. This is a finished run, not a failure.
- `3` (the `--interactive` refusal, row 15, a live run owning a phase dir, or a
  `state.json` it cannot read) or `1`: stop before any phase runs. Report the error
  line whole: for `--interactive` it names the two phases to run instead, for a live
  run its `status` and abort commands, for `state.json` the file to repair. There is
  no `[IMPROVE_RERUN]` to give, because nothing ran.

### 2. Run each `run` step, in order

For step 1 and step 2, when its `[IMPROVE_STEP]` line reads `run`: load that phase's
core and run it. Step 1b is no phase core; its own rule is below the table.

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util instructions <phase>
```

`<phase>` is the step's word: `review-plan` for step 1, `apply-suggestions` for step 2.
While you run it:

- **The flags line is the whole choice of flags.** Pass the tokens after the step's
  `[IMPROVE_STEP_FLAGS] <index>`, verbatim (they are already shell-quoted), where the
  core's launch command takes its flags: in place of `--models <selected>` in
  `review-plan.md` step 4, and in place of `[options]` in `apply-suggestions.md`
  step 2. Never pass the marker or the index: either is an extra argument, which the
  phase refuses with exit 3. The tokens replace every model or decision flag the core
  would pick itself, so `review-plan.md` step 2 asks nothing and adds no model flag.
  Add nothing to them and drop nothing from them. The command keeps the tokens your
  dispatcher command carries, `--host` among them, which the line never holds. The
  phase core's own recovery steps (row 3's `--force` resume of the missing models)
  still run as that core words them.
- **`[IMPROVE_STEP_FRESH] 1` means skip `review-plan.md` step 3, Resume Detection,**
  and nothing else. Its case (a) would read the previous round's `validation.json` as
  "complete" and skip a review that must run. Whatever makes the phase start over is
  already in the flags line.
- **An inner phase's `[NEXT_COMMAND]` block is never an instruction.** Each phase's
  last dispatcher call still prints one: review-plan's `--reaggregate` names
  `--apply-suggestions <plan>`, and the apply's `--mark-completed` names
  `--generate-tasks <plan>`. Each is that phase's standalone next step. Never run it,
  and never invoke the skill again from it. Move on only by loading the next `run`
  step's core; only section 4's lookup gives the user a next command.
- **Run the core's work, then stop before its report.** Every step that writes a
  file, records state or finishes the phase runs exactly as the core words it.
  Exactly two things are skipped: the core's closing report to the user, and the
  `util next-command` lookup inside it. Section 4 reports once for both phases.

| Phase core | Run | Skip |
| --- | --- | --- |
| `review-plan.md` | steps 1–7: model selection from the flags line, Resume Detection (not on `[IMPROVE_STEP_FRESH] 1`), the detached launch, the roster call and the poll loop, interrupted-run recovery, salvage and its reaggregate, validation and `--reaggregate`; then step 8's `util metrics record` and `util metrics finish` calls, which write `state.json` | the rest of step 8, its report, which section 4 gives instead; and step 9, *Suggestion Consolidation*, which step 1b runs instead |
| `apply-suggestions.md` | steps 1–8: the orchestrator with the flags line, the decision summary, the batch loop, the judge's decisions, step 7's summary report at `{plan}/apply-suggestions/summary.md` with its `util metrics report` and `util report regenerate-decisions` calls, and step 8's `--mark-completed` once the loop reached its end | the *Then report to the user* paragraph after step 8 |

On a host that adds `--exec-subagents` the apply finishes in its one orchestrator
call, writing `summary.md` and the decision badges itself, exactly as that core says;
do not run its native loop a second time. A core that stops early under its own rules
(a partial application, a batch that failed, an interrupted run) stops there, and
section 3 reports the stop.

Keep what the skipped reports would have carried; section 4 gives it: every reviewer
that produced nothing, with its reason, and any `[RESULT_FILE_MISNAMED]` or
`[RESULT_SET_ASIDE]` line, as printed.

#### Step 1b: consolidation, between the review and the apply

Step 1b runs after step 1 (the review) is done or was skipped, and before step 2 (the
apply). Run it when its `[IMPROVE_STEP]` line reads `run`, or reads `after-review` and
step 1's last `review-plan` call carries `consolidation_recommended` on its
`MULTI_LLM_RESULT` line: the `--reaggregate`, or the run itself when it owed none (its
line in `orchestrator-run.log`, or a `--detach` run's terminal `status` poll), never a
`util` call after it. Otherwise skip it. This holds whether step 1 ran or was skipped.

Run it as the full workflow does:

1. The consolidation call, with the tokens after `[IMPROVE_STEP_FLAGS] 1b` where the
   flags go:

   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-plan --plan-file "$PLAN_PATH" <the tokens after [IMPROVE_STEP_FLAGS] 1b>
   ```

2. When it prints `[CONSOLIDATION_PENDING]` or `[CONSOLIDATION_BATCHES_PENDING]`, load
   `consolidation_tasks.json` from `{plan}/review-plan/` and spawn subagents for its
   batches as `review-plan.md` step 9 b) does: when a task carries `prompt_path`, the
   subagent reads that file in full (through line `prompt_lines`) and follows it;
   otherwise pass `task.prompt`, with that step's Strategy A or B for several batches.
   Write each reply to its task's `output_path`, and confirm every `output_path`
   exists and is not empty before the next call. When it prints neither marker
   (nothing to consolidate, or the `--exec-subagents` leg ran the batches in that
   call), the pass is done: skip item 3.
3. Then merge the batches:

   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-plan --plan-file "$PLAN_PATH" --reaggregate-consolidation
   ```

A step 1b that fails never stops the run (row 4): warn, keep the unconsolidated
results, and go on to step 2. The pass changes nothing that gets applied; it writes
the consolidated report a human reads afterwards.

### 3. When a step is done, and when the run stops

A step is done when the last call of its phase's own mode exits `0` or `2`: the
review's `--reaggregate` (or, with no validation owed, the run its poll loop ended
on), and the apply's `--mark-completed` (or its one orchestrator call under
`--exec-subagents`), never a `util` call after it. Step 1b never stops the run.

For steps 1 and 2, on exit `1` or `3`, or when the phase core stopped under its own
rules (row 14):

- report the phase, the plan, the last error line it printed, whole, and the options
  its output names, as you would for that phase run alone;
- when the stop's way forward is an answer to that phase (a `--human-task` answer, or
  a batch recorded with `--skipped`), give it as that phase's own command, exactly as
  the stop names it, alone in its own fenced code block, for example
  `--apply-suggestions <plan> --resume --human-task apply-batch-3=skip` in your host's
  spelling. `[IMPROVE_RERUN]` holds only the flags the user typed, never an answer, so
  it is the follow-up once that phase is recorded;
- end the report with the `[IMPROVE_RERUN]` command section 1 printed, as the way to
  continue once those are dealt with: everything after the marker, alone in its own
  fenced code block, copied character for character, as a `[NEXT_COMMAND]` command is.
  It is this run's one next step. The `[NEXT_COMMAND]` blocks the phases printed are
  not (section 2): never give review-plan's `--apply-suggestions <plan>` in its place,
  which is the review's standalone next step, not the way on from a stopped apply;
- never start the next step after a stop, and make no next-step lookup: a stopped
  run has no next phase.

### 4. Report

Report once, for the whole run, with the template below. No Python helper composes
this report on this path, so every number is read from the file the table names, never
recounted from your memory of the run; every host then prints the same numbers. A step
that read `skip` reads the same files, which the run on record left. Paths are under
`{plan}/`:

| Field | File | What to read |
| --- | --- | --- |
| models | `review-plan/.status.json` | `models_completed`, and each `models_failed` entry with its reason, out of `models_requested` |
| findings | `review-plan/grouped.json` | the number of entries in `groups` |
| valid, invalid, needs human decision, validation failed | `review-plan/.status.json` | `validation_counts`. With no such key, a review whose `grouped.json` holds no group prints `0` for each |
| items applied | `apply-suggestions/write_tasks.json`, `state.json` | the run's records (below) with status `applied` or `no-op` |
| declined by their batch, skipped at your request | `apply-suggestions/write_tasks.json`, `state.json` | the run's records with status `declined` or `skipped`, each with its `details.reason` |
| decided by the judge | `state.json` | the `human_decisions_apply-suggestions` entries whose `batch_context.decision_source` is `judge_auto_decide` (approved or skipped, by `decision`) or `judge_auto_decide_salvage` (salvaged); the older `claude_auto_decide` spellings read the same. The judge's raw replies (`apply-suggestions/human_decision_batch_*.json`) are not counted |
| items skipped | `apply-suggestions/orchestrator_output.json` | `skipped_count`, with `skipped_items` naming each |

The run is the whole apply run, every `--resume` of it included. A native `--resume`
rewrites `write_tasks.json` with only the batches still to run, and `state.json` keeps
the records of earlier runs, so neither the file's batches nor every record is the run:

- **The run's items** are `native_run.items` in `apply-suggestions/write_tasks.json`
  (every item the run handed out, carried across its resumes) and the `expected_ids`
  of its `batches`. A file with no `native_run` (an `--exec-subagents` run, whose
  resume keeps every batch in the file) has its batches' `expected_ids` alone.
- **The run's records** are the `processed_apply-suggestions` entries (one per item
  id) whose `details.grouped_sha256` equals the batches' `inputs.grouped_sha256`, or,
  when either has none, whose item is one of the run's items. When
  `native_run.started_at` is set, leave out every entry whose `timestamp` is earlier:
  it is an earlier run's.
- **When `apply-suggestions/orchestrator_output.json` holds no batch**, the apply's
  last call handed nothing out, and `write_tasks.json` says why. A file whose
  `native_run.emitted_at` is later than `phases_completed["review-plan"]` in
  `state.json` is this review's: that call was a `--resume` that found every batch
  already recorded (the host stopped before `--mark-completed`), so count the run
  from it as above. Otherwise (no `write_tasks.json`, no `native_run`, or one emitted
  before the review last completed, which an earlier review left) this review left
  nothing to apply: count nothing from that file, and an apply phase on record as
  completed prints `0` items applied and no declined or skipped line.

- A field whose file is missing or unreadable prints `not recorded (<path> missing)`,
  never `0` and never a number taken from another file, except as the no-batch rule
  above says.
- An output file that does not exist is listed with `(not written)` after it.

```markdown
## Improve Plan Summary

**Plan**: <the plan path>

[ALREADY_COMPLETE] … (only when section 1 printed it: the line, whole)

### Step 1: Review Plan — ran | skipped (<why>)
- Models: <completed> of <requested>; failed: <model> (<reason>), …
- Findings: N
- Valid: N · Invalid: N · Needs human decision: N · Validation failed: N
- [RESULT_FILE_MISNAMED] / [RESULT_SET_ASIDE] lines, as printed (only when any)

### Step 1b: Consolidation — ran | skipped (<why>) | failed (warning: <reason>)

### Step 2: Apply Suggestions — ran | skipped (<why>)
- Items applied: N
- Declined by their batch (not applied): N — <id> (<reason>), … (only when any)
- Skipped at your request (not applied): N — <id>, … (only when any)
- Decided by the judge: N (A approved, V salvaged, S skipped)
- Items skipped: N — <title> (<status>), …

### Output Files
- {plan}/review-plan/report.html
- {plan}/review-plan/consolidated-report.md
- {plan}/apply-suggestions/summary.md
- <the plan>

### State
- State file: {plan}/state.json

### Next Steps
- (the section the lookup below prints)
```

Then get the next step, after every other command, on every host:

```bash
uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" util next-command "$PLAN_PATH" --after improve-plan --host <host-id>
```

`--after improve-plan` is this mode's own word: the lookup walks on from the apply,
normally to the `--generate-tasks <plan>` command. `<host-id>` is section 1's; the
lookup takes no other token of your dispatcher command (it refuses `--yes` and
`--exec-subagents`). This lookup is the run's one source of a next step: the blocks
the inner phases printed are not this run's. End the report with its block, as the
`### Next Steps` rule in `references/summary-format.md` says.
