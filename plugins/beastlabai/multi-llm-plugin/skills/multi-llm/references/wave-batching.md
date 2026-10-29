# Wave-Based Parallel Spawning

When there are more than 4 batches, spawn them in waves to control context growth.

## Strategy Selection

- **≤ 4 batches (Strategy A)**: **Spawn subagents** for every batch at once, in one parallel group.
- **> 4 batches (Strategy B)**: Use wave-based spawning (below).

## Wave-Based Spawning (Strategy B)

1. Split batches into waves of up to 4 batches each, except the last wave may include up to 6 batches (absorbing any small remainder to avoid an unnecessary extra round — e.g., 5 batches = one wave of 5, 9 batches = wave of 4 + wave of 5, 8 batches = two waves of 4)
2. For each wave:
   - **Spawn subagents** for every batch in the wave at once, in one parallel group
   - Run each batch's task exactly as the calling instruction's contract says (the sidecar at `prompt_path`, or `task.prompt`), writing the reply to its `output_path`
   - A validation batch whose context was too big to inline is `context_mode: workspace-read`: its prompt holds an excerpt and names a snapshot of the full plan (and, for review-tasks, of the task list) by path. Run it where the subagent can read that path, and never treat the excerpt as the whole document
   - Wait for all agents in the wave to complete
   - **Confirm every batch in the wave wrote its `output_path`** — the file is there and is not empty — before moving on. A missing file is not a batch that failed; it is a batch whose reply never reached you, and nothing else will write it
3. Proceed to the next wave
4. After ALL waves complete, and only once every task's `output_path` is on disk, continue to the next step (reaggregation, etc.)

## Error Handling

- Per-subagent timeout: 60 seconds. If a subagent times out, mark that batch as `validation_failed`.
- If a subagent returns malformed output or fails validation, retry it once (max 1 retry per batch). `util check-reply` is the test of "malformed" — run it after writing each reply, never on a batch whose subagent has not returned (its `[REPLY_MISSING]` is a reply not written yet, not a malformed one) — and the retry is a fresh reply from the subagent, never a repair of the bad one. If still failing, mark it as `validation_failed` and move on.
- A missing `output_path` spends that same one retry: re-dispatch the batch and write the reply yourself. Only a batch that comes back empty-handed a second time is `validation_failed`. A batch you never re-dispatched is not a failed batch and must not be reported as one — it is a batch the run dropped, and the merge cannot tell the two apart.
- If any batch in a wave fails (after retry), log the failed batch index and continue to the next wave -- do NOT abort the workflow.
- After ALL waves complete, report which batches failed (e.g., "Completed {success}/{total} batches. Failed: batch {indices}.").
- Proceed to the next step regardless of partial failures -- `merge_batched_validation_results` already handles missing batch files gracefully, so partial results are merged automatically. That grace is for batches the verification above has already re-dispatched and given up on: it means the merge does not crash on a missing file, never that the batch's findings survive it.

## Important Notes

- Do NOT run these batches detached. Spawn them as ordinary parallel subagents so their results return inline.
- **Do not end your turn while a dispatched batch is outstanding.** Stay in the turn until the last `output_path` above is on disk. A reply that arrives after the turn ends arrives after a one-shot headless run has ended, and the batch dies with it — unwritten, unreported, and indistinguishable afterwards from a batch that was never dispatched. Saying what you are waiting for is not waiting for it.
- Context growth per wave is approximately 30-50 lines (4 subagent spawns with their parameters plus responses), so for 5 waves (~20 batches) expect ~150-250 lines of context growth — still manageable within typical context budgets.

## ETA Reporting

When the calling instruction file wraps the wave loop with `util metrics start ... finish`, each per-batch `util metrics record --batch-index {N} --total-batches {total}` prints an `[ETA]` line to stderr. In wave-parallel runs, summing per-subagent durations would overstate wall-clock time by a factor of ~wave-width, so the ETA helper reports both signals (`per-item` and `wall-clock`) and the predicted-remaining segment uses `min(per_item, wall_clock)` — wall-clock dominates here. Pass the **cumulative** `--batch-index` (1..N across all completed waves), not the within-wave index.

## Design Rationale

**Why wave size 4 (with flexible last wave)?** The base wave size of 4 balances parallelism against context growth and typical API concurrency limits. The last wave absorbs remaining batches (up to 6 total) to avoid unnecessary serialization at the boundary — the extra context from 1-2 additional parallel subagents is negligible compared to the cost of an entire extra sequential round.

**Trade-off: wave-level synchronization.** Wave-based spawning waits for all subagents in a wave to complete before starting the next wave. If one subagent is slow, the other completed results sit idle until the wave finishes. This is simpler and more predictable than the coordinator approach, but does sacrifice some throughput.
