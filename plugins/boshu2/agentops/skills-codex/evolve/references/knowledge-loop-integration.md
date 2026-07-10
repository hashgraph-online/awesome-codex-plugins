# Knowledge Loop Integration

## Compile Warmup (--compile only)

Skip if `--compile` was not passed or if `--dry-run`.

Run the mechanical half of the Compile cycle to surface fresh signal before the first evolve cycle:

```bash
mkdir -p .agents/mine .agents/defrag
echo "Compile warmup: mining signal..."
ao mine --since 26h --quiet 2>/dev/null || echo "(ao mine unavailable — skipping)"

echo "Compile warmup: defrag sweep..."
ao defrag --prune --dedup --quiet 2>/dev/null || echo "(ao defrag unavailable — skipping)"
```

Then read `.agents/mine/latest.json` and `.agents/defrag/latest.json` and note (in 1-2 sentences each):
- Any **orphaned research** files that look relevant to current goals
- Any **code hotspots** (high-CC functions with recent edits) that may be the root cause of failing goals
- Any **duplicate learnings** merged by defrag — context on what's been cleaned up

These notes inform work selection throughout the evolve session. Store them in a session variable (in-memory), not a file.

## Harvested Work Selection (Step 3.1)

Read `.agents/rpi/next-work.jsonl` and pick the highest-value unconsumed item for this repo. Prefer:
- exact repo match before `*`, then legacy unscoped entries
- already-harvested concrete implementation work before process work
- higher severity before lower severity

When evolve picks a queue item, **claim it first**:
- set `claim_status: "in_progress"`
- set `claimed_by: "evolve:cycle-N"`
- set `claimed_at: "<timestamp>"`
- keep `consumed: false` until the `/rpi` cycle and regression gate both succeed

If the cycle fails, regresses, or is interrupted before success, release the claim and leave the item available for the next cycle.

## Queue Finalization After Regression Gate

- **success:** finalize any claimed queue item with `consumed: true`, `consumed_by`, and `consumed_at`; clear transient claim fields
- **failure/regression:** clear `claim_status`, `claimed_by`, and `claimed_at`; keep `consumed: false`; record the release in `session-state.json`

After the cycle's `/post-mortem` finishes, immediately re-read `.agents/rpi/next-work.jsonl` before selecting the next item. Never assume the queue state from before the cycle.

## Teardown Learning Extraction

1. Commit any staged but uncommitted `cycle-history.jsonl`:
```bash
if git diff --cached --name-only | grep -q cycle-history.jsonl; then
  git commit -m "evolve: session teardown -- artifact-only cycles logged"
fi
```

2. Run `/post-mortem "evolve session: ${CYCLE} cycles"` to harvest learnings.

3. Push only if unpushed commits exist:
```bash
UNPUSHED=$(git log origin/main..HEAD --oneline 2>/dev/null | wc -l)
[ "$UNPUSHED" -gt 0 ] && git push
```

4. Report summary: cycles, productive/regressed/idle counts, stop reason. Quality mode adds quality score + remaining findings.
