# Suggestion Consolidation (review-plan, optional)

Read this only when the review-plan core's step 9 sends you here, in one of two
cases:
- **Starting a recommended pass:** the log `{plan}/review-plan/orchestrator-run.log`
  carries `[CONSOLIDATION_RECOMMENDED]`, or `MULTI_LLM_RESULT.consolidation_recommended`
  is set. Start at *Decide whether it runs*.
- **Continuing a requested or pending pass:** the user typed `--consolidate`, or
  a review-plan run printed `[CONSOLIDATION_PENDING]` or
  `[CONSOLIDATION_BATCHES_PENDING]`. That pass is already decided, below the
  recommendation threshold too: it passes no recommendation check and asks no
  question. Start at section a) when that `--consolidate` has not run yet, or at
  section b) for the batches a pending marker names.

A run with no `[CONSOLIDATION_RECOMMENDED]` line, no `consolidation_recommended`
field, no `--consolidate` from the user and no `[CONSOLIDATION_PENDING]` or
`[CONSOLIDATION_BATCHES_PENDING]` line skips consolidation entirely.

**Commands.** This file is read as it is, so its commands are spelled from the
mode word on: `<prefix>` stands for the dispatcher prefix every command in the
core starts with (`uv run … --project "<skill dir>" -- python "<skill dir>/multi_llm.py"`,
flags and paths exactly as the core prints them). Copy it from any command in
the core, unchanged, and run each command bare, as the core runs its own.

## Decide whether it runs

The orchestrator emits the marker only at `CONSOLIDATION_RECOMMENDED_THRESHOLD`
(15 valid groups, tunable with `--consolidation-threshold`), so the marker's
presence *is* the decision; there is no second threshold to apply. Report the
recommendation from `MULTI_LLM_RESULT.consolidation_recommended`
(`{valid_groups, threshold, command}`, carried by `status --view run` too) rather
than inferring it from the marker's absence.

- With `--yes` (or `--non-interactive`): **auto-run consolidation once, no
  prompt** (D6 row 4). If consolidation itself fails, keep the unconsolidated
  results, warn, and continue: a failed optional pass is not a failed phase.
- Without `--yes`: tell the user the group count and **ask the user** whether to
  run consolidation. If the user declines, stop here.

## a) Run the consolidation orchestrator

```bash
<prefix> review-plan --plan-file "$PLAN_PATH" --consolidate
```

## b) Run the consolidation batches as subagents

The orchestrator output carries `[CONSOLIDATION_PENDING]` (one batch) or
`[CONSOLIDATION_BATCHES_PENDING]` (several). Then:

1. Load `consolidation_tasks.index.json` from the phase directory (`{plan}/review-plan/`),
   or `consolidation_tasks.json` when there is no index: the same `batches` without
   their prompts. Every task in the full file carries a complete `prompt`, and
   `prompt_path` (`consolidation_batch_N.prompt.txt` in the same directory, exactly
   the bytes of `prompt`) with its line count `prompt_lines`.
2. Count the batches as `{total_batches}` and mark the consolidation phase start:
   ```bash
   <prefix> util metrics start --state-file "$STATE_FILE" --phase "review-plan-consolidation" --total-batches {total_batches}
   ```
3. For each task, run a subagent the way the core's validation contract says: when
   the task carries `prompt_path`, the subagent reads that file in full (through
   line `prompt_lines`) and follows it; otherwise, or if the file is absent, pass
   that task's `prompt` from `consolidation_tasks.json`. The filled
   `consolidate_suggestions.txt` template and that batch's group records are
   already inside it, so write no prompt file of your own.
4. Write the JSON each subagent returns to that task's `output_path`
   (`consolidation_batch_N.json` in the phase directory).
5. After each batch completes, record metrics with a cumulative `--batch-index`:
   ```bash
   <prefix> util metrics record --state-file "$STATE_FILE" --phase "review-plan-consolidation" --label "Consolidation batch {N}" --subagent-type "general-purpose" --tokens {token_count} --tool-uses {tool_uses} --duration-ms {duration_ms} --total-batches {total_batches} --batch-index {N}
   ```
   `token_count`, `tool_uses` and `duration_ms` come from whatever your subagent
   mechanism reports. Omit any flag it does not report. Never pass `0` for an
   unknown value; omit the flag: a made-up zero is averaged into the phase totals
   as a real measurement.

**Strategy A (≤ 4 batches):** run all batch subagents from the main agent in
parallel (one message with several subagent calls).

**Strategy B (> 4 batches):** split the batches into waves of up to 4 (the last
wave may absorb the remainder, up to 6). For each wave, run all its subagents in
parallel, wait for them, then start the next wave.

**Before you continue: verify every batch wrote its file, and do not end your
turn before it has.** Confirm that each task's `output_path`
(`consolidation_batch_N.json`) exists and is not empty, and re-dispatch any task
whose file is missing before reaggregating. **You** write these files, and a host
that runs one headless turn has no second turn in which to write them.

## c) Reaggregate after all batches complete

```bash
<prefix> review-plan --plan-file "$PLAN_PATH" --reaggregate-consolidation
```

Then mark the consolidation phase finish:

```bash
<prefix> util metrics finish --state-file "$STATE_FILE" --phase "review-plan-consolidation"
```

**CRITICAL**: do NOT report consolidation results until reaggregation is complete.

## d) Report every consolidation output path

- `consolidated.json`: consolidated suggestion groups
- `consolidated-report.md`: human-readable consolidation report
- `consolidated-report.html`: HTML version of the consolidation report

That completes the core's step 9.
